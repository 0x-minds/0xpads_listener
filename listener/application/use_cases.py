"""
🎯 Application Use Cases
Business logic و use cases
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import asyncio
from loguru import logger

from ..domain.entities import TradeEvent, OHLCVCandle, BondingCurve, MarketData, ChartData
from ..domain.value_objects import (
    TokenAddress, TimeInterval, Price, Volume, 
    TradeDirection, PriceRange, VolumeData, BlockInfo, TransactionHash
)
from ..domain.events import (
    TradeExecuted, CandleUpdated, NewCandleCreated, 
    MarketDataUpdated, LargeTrade, VolumeSpike, event_bus
)
from .interfaces import (
    ITradeRepository, ICandleRepository, IBondingCurveRepository,
    IMarketDataRepository, ICacheService, IWebSocketService,
    IChartDataService, IEventProcessingService, IAlertService
)
from ..infrastructure.redis.redis_service import RedisService


class ProcessTradeEventUseCase:
    """Use case برای پردازش trade event"""
    
    def __init__(
        self,
        trade_repo: ITradeRepository,
        candle_repo: ICandleRepository,
        curve_repo: IBondingCurveRepository,
        market_data_repo: IMarketDataRepository,
        cache_service: ICacheService,
        websocket_service: IWebSocketService,
        alert_service: IAlertService,
        redis_service: RedisService
    ):
        self.trade_repo = trade_repo
        self.candle_repo = candle_repo
        self.curve_repo = curve_repo
        self.market_data_repo = market_data_repo
        self.cache_service = cache_service
        self.websocket_service = websocket_service
        self.alert_service = alert_service
        self.redis_service = redis_service
    
    async def execute(self, raw_event: Dict[str, Any]) -> TradeEvent:
        """پردازش اصلی trade event"""
        logger.info(f"🔥 Processing trade event for {raw_event.get('token_address', 'unknown')[:8]}...")
        
        # 1. Convert raw event to domain entity
        trade = await self._create_trade_from_raw_event(raw_event)
        
        # 2. Save trade
        await self.trade_repo.save_trade(trade)
        
        # 3. Update all candles asynchronously
        candle_tasks = [
            self._update_candle_for_interval(trade, TimeInterval(interval=interval))
            for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]
        ]
        await asyncio.gather(*candle_tasks, return_exceptions=True)
        
        # 4. Update bonding curve info
        await self._update_bonding_curve(trade)
        
        # 5. Update market data
        market_data = await self._update_market_data(trade)
        
        # 6. Check alerts
        await self._check_and_send_alerts(trade, market_data)
        
        # 7. Cache real-time data
        await self._cache_real_time_data(trade, market_data)
        
        # 8. Broadcast to WebSocket clients
        await self._broadcast_trade_update(trade, market_data)
        
        # 9. Send to backend via WebSocket (if connected)
        await self._send_to_backend(trade, market_data)
        
        # 10. Send to Redis stream for backend consumption
        await self._send_to_redis_stream(trade, market_data)
        
        # 11. Publish domain event
        await event_bus.publish(TradeExecuted(trade))
        
        logger.info(f"✅ Trade processed: {trade.direction.direction_str} {trade.token_amount.value} tokens")
        
        return trade
    
    async def _create_trade_from_raw_event(self, raw_event: Dict[str, Any]) -> TradeEvent:
        """تبدیل raw event به TradeEvent"""
        return TradeEvent(
            token_address=TokenAddress(raw_event['token_address']),
            curve_address=TokenAddress(raw_event['curve_address']),
            user_address=TokenAddress(raw_event['user_address']),
            direction=TradeDirection(is_buy=raw_event['is_buy']),
            token_amount=Volume.from_wei(raw_event['token_amount']),
            eth_amount=Volume.from_wei(raw_event['eth_amount']),
            price_before=Price.from_wei(raw_event['price_before']),
            price_after=Price.from_wei(raw_event['price_after']),
            total_supply=Volume.from_wei(raw_event['total_supply']),
            block_info=BlockInfo(
                number=raw_event['block_number'],
                timestamp=raw_event['block_timestamp'],
                hash=raw_event['block_hash']
            ),
            tx_hash=TransactionHash(raw_event['tx_hash']),
            timestamp=datetime.fromtimestamp(raw_event['timestamp'], tz=timezone.utc)
        )
    
    async def _update_candle_for_interval(self, trade: TradeEvent, interval: TimeInterval) -> None:
        """به‌روزرسانی candle برای interval مشخص"""
        try:
            # Get candle start timestamp
            candle_timestamp = interval.floor_timestamp(int(trade.timestamp.timestamp()))
            
            # Get existing candle or create new one
            existing_candle = await self.candle_repo.get_latest_candle(
                trade.token_address, interval
            )
            
            if existing_candle and existing_candle.timestamp == candle_timestamp:
                # Update existing candle
                existing_candle.update_with_trade(trade)
                await self.candle_repo.update_candle(existing_candle)
                await event_bus.publish(CandleUpdated(existing_candle))
            else:
                # Create new candle
                new_candle = OHLCVCandle.create_empty(
                    trade.token_address, interval, candle_timestamp, trade.price_before
                )
                new_candle.update_with_trade(trade)
                await self.candle_repo.save_candle(new_candle)
                await event_bus.publish(NewCandleCreated(new_candle))
            
        except Exception as e:
            logger.error(f"Error updating candle for {interval.interval}: {e}")
    
    async def _update_bonding_curve(self, trade: TradeEvent) -> None:
        """به‌روزرسانی bonding curve"""
        try:
            curve = await self.curve_repo.get_curve_by_token(trade.token_address)
            if curve:
                curve.update_from_trade(trade)
                await self.curve_repo.update_curve(curve)
        except Exception as e:
            logger.error(f"Error updating bonding curve: {e}")
    
    async def _update_market_data(self, trade: TradeEvent) -> MarketData:
        """محاسبه و به‌روزرسانی market data"""
        try:
            # Get 24h stats
            stats_24h = await self._calculate_24h_stats(trade.token_address)
            
            market_data = MarketData(
                token_address=trade.token_address,
                current_price=trade.price_after,
                price_change_24h=stats_24h['price_change'],
                price_change_percent_24h=stats_24h['price_change_percent'],
                volume_24h=stats_24h['volume'],
                volume_eth_24h=stats_24h['volume_eth'],
                trades_24h=stats_24h['trades'],
                market_cap=Volume(trade.total_supply.value * trade.price_after.value)
            )
            
            await self.market_data_repo.save_market_data(market_data)
            await event_bus.publish(MarketDataUpdated(market_data))
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
            # Return basic market data
            return MarketData(
                token_address=trade.token_address,
                current_price=trade.price_after,
                price_change_24h=Price(Decimal('0')),
                price_change_percent_24h=Decimal('0'),
                volume_24h=Volume(Decimal('0')),
                volume_eth_24h=Volume(Decimal('0')),
                trades_24h=0,
                market_cap=Volume(trade.total_supply.value * trade.price_after.value)
            )
    
    async def _calculate_24h_stats(self, token_address: TokenAddress) -> Dict[str, Any]:
        """محاسبه آمار 24 ساعته"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        trades_24h = await self.trade_repo.get_trades_in_timerange(
            token_address, start_time, end_time
        )
        
        if not trades_24h:
            return {
                'price_change': Price(Decimal('0')),
                'price_change_percent': Decimal('0'),
                'volume': Volume(Decimal('0')),
                'volume_eth': Volume(Decimal('0')),
                'trades': 0
            }
        
        # Sort by timestamp
        trades_24h.sort(key=lambda t: t.timestamp)
        
        first_trade = trades_24h[0]
        last_trade = trades_24h[-1]
        
        price_change = Price(last_trade.price_after.value - first_trade.price_before.value)
        price_change_percent = first_trade.price_before.percentage_change(last_trade.price_after)
        
        total_volume = sum(trade.token_amount.value for trade in trades_24h)
        total_volume_eth = sum(trade.eth_amount.value for trade in trades_24h)
        
        return {
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'volume': Volume(total_volume),
            'volume_eth': Volume(total_volume_eth),
            'trades': len(trades_24h)
        }
    
    async def _check_and_send_alerts(self, trade: TradeEvent, market_data: MarketData) -> None:
        """بررسی و ارسال alerts"""
        try:
            # Check for large trade
            if trade.is_large_trade():
                await event_bus.publish(LargeTrade(trade, Volume(Decimal('1.0'))))
                await self.alert_service.send_alert('large_trade', {
                    'token_address': str(trade.token_address),
                    'amount_eth': str(trade.eth_amount.value),
                    'direction': trade.direction.direction_str
                })
            
            # Check price alerts
            await self.alert_service.check_price_alerts(market_data)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _cache_real_time_data(self, trade: TradeEvent, market_data: MarketData) -> None:
        """Cache کردن real-time data"""
        try:
            # Cache latest trade
            await self.cache_service.set_json(
                f"trade:latest:{trade.token_address}",
                {
                    'price': str(trade.price_after.value),
                    'volume': str(trade.token_amount.value),
                    'direction': trade.direction.direction_str,
                    'timestamp': trade.timestamp.isoformat()
                },
                ttl=300  # 5 minutes
            )
            
            # Cache market data
            await self.cache_service.set_json(
                f"market:{trade.token_address}",
                {
                    'current_price': str(market_data.current_price.value),
                    'price_change_24h': str(market_data.price_change_24h.value),
                    'price_change_percent_24h': str(market_data.price_change_percent_24h),
                    'volume_24h': str(market_data.volume_eth_24h.value),
                    'trades_24h': market_data.trades_24h,
                    'market_cap': str(market_data.market_cap.value),
                    'last_updated': market_data.last_updated.isoformat()
                },
                ttl=60  # 1 minute
            )
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
    
    async def _broadcast_trade_update(self, trade: TradeEvent, market_data: MarketData) -> None:
        """Broadcast به WebSocket clients"""
        try:
            # Send to token-specific room
            await self.websocket_service.send_to_room(
                f"token:{trade.token_address}",
                {
                    'type': 'trade',
                    'data': {
                        'token_address': str(trade.token_address),
                        'price': str(trade.price_after.value),
                        'volume': str(trade.token_amount.value),
                        'direction': trade.direction.direction_str,
                        'timestamp': trade.timestamp.isoformat(),
                        'market_data': {
                            'current_price': str(market_data.current_price.value),
                            'price_change_24h': str(market_data.price_change_percent_24h),
                            'volume_24h': str(market_data.volume_eth_24h.value)
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting: {e}")
    
    async def _send_to_redis_stream(self, trade: TradeEvent, market_data: MarketData) -> None:
        """Send trade to Redis stream for backend consumption"""
        try:
            event_data = {
                'token_address': str(trade.token_address),
                'curve_address': str(trade.curve_address),
                'user_address': str(trade.user_address),
                'direction': trade.direction.direction_str,
                'token_amount': str(trade.token_amount.value),
                'eth_amount': str(trade.eth_amount.value),
                'price_before': str(trade.price_before.value),
                'price_after': str(trade.price_after.value),
                'tx_hash': str(trade.tx_hash),
                'timestamp': trade.timestamp.isoformat(),
                'market_data': {
                    'market_cap': str(market_data.market_cap.value),
                    'volume_24h': str(market_data.volume_24h.value),
                    'volume_eth_24h': str(market_data.volume_eth_24h.value),
                    'trades_24h': market_data.trades_24h,
                    'price_change_24h': str(market_data.price_change_24h.value),
                    'price_change_percent_24h': str(market_data.price_change_percent_24h)
                }
            }
            
            # Send to Redis stream  
            message_id = await self.redis_service.send_event_to_stream('Trade', event_data)
            logger.info(f"📡 Trade sent to Redis stream: {message_id}")
            
        except Exception as e:
            logger.error(f"Error sending to Redis stream: {e}")
    
    async def _send_to_backend(self, trade: TradeEvent, market_data: MarketData) -> None:
        """ارسال به Node.js backend via WebSocket"""
        try:
            await self.websocket_service.send_to_backend('trade_update', {
                'token_address': str(trade.token_address),
                'trade': {
                    'user_address': str(trade.user_address),
                    'direction': trade.direction.direction_str,
                    'token_amount': str(trade.token_amount.value),
                    'eth_amount': str(trade.eth_amount.value),
                    'price': str(trade.price_after.value),
                    'tx_hash': str(trade.tx_hash),
                    'timestamp': trade.timestamp.isoformat()
                },
                'market_data': {
                    'current_price': str(market_data.current_price.value),
                    'price_change_24h': str(market_data.price_change_percent_24h),
                    'volume_24h': str(market_data.volume_eth_24h.value),
                    'trades_24h': market_data.trades_24h,
                    'market_cap': str(market_data.market_cap.value)
                }
            })
            
        except Exception as e:
            logger.error(f"Error sending to backend: {e}")


class GetChartDataUseCase:
    """Use case برای دریافت chart data"""
    
    def __init__(
        self,
        candle_repo: ICandleRepository,
        market_data_repo: IMarketDataRepository,
        cache_service: ICacheService
    ):
        self.candle_repo = candle_repo
        self.market_data_repo = market_data_repo
        self.cache_service = cache_service
    
    async def execute(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        limit: int = 100
    ) -> ChartData:
        """دریافت chart data"""
        logger.info(f"📊 Getting chart data for {token_address.short_address()} - {interval.interval}")
        
        # Check cache first
        cache_key = f"chart:{token_address}:{interval.interval}:{limit}"
        cached_data = await self.cache_service.get_json(cache_key)
        
        if cached_data:
            logger.info("📦 Returning cached chart data")
            return self._deserialize_chart_data(cached_data)
        
        # Get candles
        candles = await self.candle_repo.get_candles(token_address, interval, limit)
        
        # Get market data
        market_data = await self.market_data_repo.get_market_data(token_address)
        
        if not market_data:
            # Create basic market data if not exists
            market_data = MarketData(
                token_address=token_address,
                current_price=Price(Decimal('0')),
                price_change_24h=Price(Decimal('0')),
                price_change_percent_24h=Decimal('0'),
                volume_24h=Volume(Decimal('0')),
                volume_eth_24h=Volume(Decimal('0')),
                trades_24h=0,
                market_cap=Volume(Decimal('0'))
            )
        
        chart_data = ChartData(
            token_address=token_address,
            interval=interval,
            candles=candles,
            market_data=market_data
        )
        
        # Cache the result
        await self.cache_service.set_json(
            cache_key,
            self._serialize_chart_data(chart_data),
            ttl=60  # 1 minute cache
        )
        
        logger.info(f"📊 Chart data ready: {len(candles)} candles")
        return chart_data
    
    def _serialize_chart_data(self, chart_data: ChartData) -> Dict[str, Any]:
        """Serialize chart data برای cache"""
        return {
            'token_address': str(chart_data.token_address),
            'interval': chart_data.interval.interval,
            'candles': [
                {
                    'timestamp': candle.timestamp,
                    'open': str(candle.price_range.open.value),
                    'high': str(candle.price_range.high.value),
                    'low': str(candle.price_range.low.value),
                    'close': str(candle.price_range.close.value),
                    'volume': str(candle.volume_data.total_volume.value),
                    'volume_eth': str(candle.volume_eth.value),
                    'trades': candle.volume_data.trade_count
                }
                for candle in chart_data.candles
            ],
            'market_data': {
                'current_price': str(chart_data.market_data.current_price.value),
                'price_change_24h': str(chart_data.market_data.price_change_24h.value),
                'price_change_percent_24h': str(chart_data.market_data.price_change_percent_24h),
                'volume_24h': str(chart_data.market_data.volume_24h.value),
                'volume_eth_24h': str(chart_data.market_data.volume_eth_24h.value),
                'trades_24h': chart_data.market_data.trades_24h,
                'market_cap': str(chart_data.market_data.market_cap.value)
            },
            'last_update': chart_data.last_update.isoformat()
        }
    
    def _deserialize_chart_data(self, data: Dict[str, Any]) -> ChartData:
        """Deserialize chart data از cache"""
        # Implementation would reconstruct ChartData from dict
        # برای سادگی فعلاً skip می‌کنم
        pass


class ManageBondingCurvesUseCase:
    """Use case برای مدیریت bonding curves"""
    
    def __init__(
        self,
        curve_repo: IBondingCurveRepository,
        cache_service: ICacheService,
        websocket_service: IWebSocketService
    ):
        self.curve_repo = curve_repo
        self.cache_service = cache_service
        self.websocket_service = websocket_service
    
    async def add_new_curve(self, curve_data: Dict[str, Any]) -> BondingCurve:
        """اضافه کردن bonding curve جدید"""
        logger.info(f"➕ Adding new bonding curve: {curve_data.get('name', 'unknown')}")
        
        curve = BondingCurve(
            token_address=TokenAddress(curve_data['token_address']),
            curve_address=TokenAddress(curve_data['curve_address']),
            creator_address=TokenAddress(curve_data['creator_address']),
            name=curve_data['name'],
            symbol=curve_data['symbol'],
            total_supply=Volume.from_wei(curve_data['total_supply']),
            current_supply=Volume.from_wei(curve_data['current_supply']),
            current_price=Price.from_wei(curve_data['current_price']),
            reserve_balance=Volume.from_wei(curve_data['reserve_balance']),
            deployed_at=datetime.now(timezone.utc)
        )
        
        await self.curve_repo.save_curve(curve)
        
        # Cache the new curve
        await self.cache_service.set_json(
            f"curve:{curve.token_address}",
            {
                'token_address': str(curve.token_address),
                'curve_address': str(curve.curve_address),
                'name': curve.name,
                'symbol': curve.symbol,
                'current_price': str(curve.current_price.value),
                'market_cap': str(curve.market_cap.value),
                'is_active': curve.is_active
            },
            ttl=3600  # 1 hour
        )
        
        # Notify WebSocket clients
        await self.websocket_service.broadcast({
            'type': 'new_curve',
            'data': {
                'token_address': str(curve.token_address),
                'name': curve.name,
                'symbol': curve.symbol,
                'current_price': str(curve.current_price.value)
            }
        })
        
        # Send to Redis stream for backend consumption
        await self._send_to_redis_stream(curve, curve_data)
        
        return curve
    
    async def get_all_active_curves(self) -> List[BondingCurve]:
        return await self.curve_repo.get_all_active_curves()
    
    async def _send_to_redis_stream(self, curve: BondingCurve, curve_data: Dict[str, Any]) -> None:
        """Send new curve event to Redis stream for backend consumption"""
        try:
            event_data = {
                'token_address': str(curve.token_address),
                'curve_address': str(curve.curve_address),
                'creator_address': str(curve.creator_address),
                'name': curve.name,
                'symbol': curve.symbol,
                'total_supply': str(curve.total_supply.value),
                'current_supply': str(curve.current_supply.value),
                'current_price': str(curve.current_price.value),
                'reserve_balance': str(curve.reserve_balance.value),
                'deployed_at': curve.deployed_at.isoformat(),
                'is_active': curve.is_active,
                'block_number': curve_data.get('block_number'),
                'block_timestamp': curve_data.get('block_timestamp'),
                'tx_hash': curve_data.get('tx_hash'),
                'log_index': curve_data.get('log_index'),
                'timestamp': curve_data.get('timestamp')
            }
            
            # Send to Redis stream  
            message_id = await self.cache_service.send_event_to_stream('BondingCurveDeployed', event_data)
            logger.info(f"📡 New curve sent to Redis stream: {message_id}")
            
        except Exception as e:
            logger.error(f"Error sending curve to Redis stream: {e}")
