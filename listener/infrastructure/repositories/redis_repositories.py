"""
🗄️ Redis Repository Implementations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from loguru import logger

from ...application.interfaces import (
    ITradeRepository, ICandleRepository, IBondingCurveRepository, IMarketDataRepository, IBurnEventRepository
)
from ...domain.entities import TradeEvent, OHLCVCandle, BondingCurve, MarketData
from ...domain.value_objects import TokenAddress, TimeInterval
from ..redis.redis_service import RedisService


class RedisTradeRepository(ITradeRepository):
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def save_trade(self, trade: TradeEvent) -> None:
        # Implementation placeholder
        pass

    async def get_trades_by_token(self, token_address: TokenAddress, limit: int = 100, after_timestamp: Optional[datetime] = None) -> List[TradeEvent]:
        # Implementation placeholder
        return []

    async def get_trades_in_timerange(self, token_address: TokenAddress, start_time: datetime, end_time: datetime) -> List[TradeEvent]:
        # Implementation placeholder
        return []

    async def get_trade_count_24h(self, token_address: TokenAddress) -> int:
        # Implementation placeholder
        return 0


class RedisCandleRepository(ICandleRepository):
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def save_candle(self, candle: OHLCVCandle) -> None:
        # Implementation placeholder
        pass

    async def get_candles(self, token_address: TokenAddress, interval: TimeInterval, limit: int = 100, after_timestamp: Optional[int] = None) -> List[OHLCVCandle]:
        # Implementation placeholder
        return []

    async def get_latest_candle(self, token_address: TokenAddress, interval: TimeInterval) -> Optional[OHLCVCandle]:
        # Implementation placeholder
        return None

    async def update_candle(self, candle: OHLCVCandle) -> None:
        # Implementation placeholder
        pass

    async def delete_old_candles(self, token_address: TokenAddress, interval: TimeInterval, older_than: datetime) -> int:
        # Implementation placeholder
        return 0


class RedisBondingCurveRepository(IBondingCurveRepository):
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def save_curve(self, curve: BondingCurve) -> None:
        # Implementation placeholder
        pass

    async def get_curve_by_token(self, token_address: TokenAddress) -> Optional[BondingCurve]:
        # Implementation placeholder
        return None

    async def get_curve_by_address(self, curve_address: TokenAddress) -> Optional[BondingCurve]:
        # Implementation placeholder
        return None

    async def get_all_active_curves(self) -> List[BondingCurve]:
        # Implementation placeholder
        return []

    async def update_curve(self, curve: BondingCurve) -> None:
        # Implementation placeholder
        pass

    async def get_curve_count(self) -> int:
        # Implementation placeholder
        return 0


class RedisMarketDataRepository(IMarketDataRepository):
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def save_market_data(self, market_data: MarketData) -> None:
        # Implementation placeholder
        pass

    async def get_market_data(self, token_address: TokenAddress) -> Optional[MarketData]:
        # Implementation placeholder
        return None

    async def get_all_market_data(self) -> List[MarketData]:
        # Implementation placeholder
        return []

    async def update_market_data(self, market_data: MarketData) -> None:
        # Implementation placeholder
        pass


class RedisBurnEventRepository(IBurnEventRepository):
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    async def save_burn_event(self, burn_event: Dict[str, Any]) -> None:
        """Save burn event to Redis"""
        try:
            token_address = burn_event.get('token_address', '').lower()
            burner_address = burn_event.get('burner_address', '').lower()
            timestamp = burn_event.get('timestamp', datetime.now().timestamp())
            
            # Store in multiple Redis structures for different query patterns
            burn_data = {
                'token_address': token_address,
                'burner_address': burner_address,
                'amount': str(burn_event.get('amount', '0')),
                'total_burned': str(burn_event.get('total_burned', '0')),
                'reason': burn_event.get('reason', ''),
                'timestamp': timestamp,
                'block_number': burn_event.get('block_number', 0),
                'transaction_hash': burn_event.get('transaction_hash', ''),
                'log_index': burn_event.get('log_index', 0)
            }
            
            # Store in time-ordered sets for querying
            await self.redis.zadd(f"burn_events:all", {json.dumps(burn_data): timestamp})
            await self.redis.zadd(f"burn_events:token:{token_address}", {json.dumps(burn_data): timestamp})
            await self.redis.zadd(f"burn_events:burner:{burner_address}", {json.dumps(burn_data): timestamp})
            
            # Store individual event for quick lookup
            event_key = f"burn_event:{burn_event.get('transaction_hash', '')}:{burn_event.get('log_index', 0)}"
            await self.redis.set_json(event_key, burn_data, ttl=86400 * 30)  # 30 days
            
            # Publish to Redis pub/sub for real-time updates
            await self.redis.publish("burn_events", json.dumps({
                'type': 'burn_event',
                'data': burn_data
            }))
            
            logger.info(f"💥 Saved burn event: {burn_event.get('amount', '0')} tokens burned by {burner_address[:8]}...")
            
        except Exception as e:
            logger.error(f"Error saving burn event: {e}")
            raise

    async def get_burn_events_by_token(
        self, 
        token_address: TokenAddress, 
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get burn events for a specific token"""
        try:
            key = f"burn_events:token:{token_address.value.lower()}"
            start_score = after_timestamp.timestamp() if after_timestamp else 0
            
            # Get events from Redis sorted set (newest first)
            raw_events = await self.redis.zrange(
                key, 
                start=0, 
                end=limit-1, 
                with_scores=False,
                rev=True  # Newest first
            )
            
            events = []
            for raw_event in raw_events:
                try:
                    event_data = json.loads(raw_event)
                    if event_data.get('timestamp', 0) > start_score:
                        events.append(event_data)
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return events
            
        except Exception as e:
            logger.error(f"Error getting burn events by token: {e}")
            return []

    async def get_burn_events_by_burner(
        self,
        burner_address: TokenAddress,
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get burn events for a specific burner"""
        try:
            key = f"burn_events:burner:{burner_address.value.lower()}"
            start_score = after_timestamp.timestamp() if after_timestamp else 0
            
            # Get events from Redis sorted set (newest first)
            raw_events = await self.redis.zrange(
                key, 
                start=0, 
                end=limit-1, 
                with_scores=False,
                rev=True  # Newest first
            )
            
            events = []
            for raw_event in raw_events:
                try:
                    event_data = json.loads(raw_event)
                    if event_data.get('timestamp', 0) > start_score:
                        events.append(event_data)
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return events
            
        except Exception as e:
            logger.error(f"Error getting burn events by burner: {e}")
            return []

    async def get_recent_burn_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent burn events across all tokens"""
        try:
            # Get events from global sorted set (newest first)
            raw_events = await self.redis.zrange(
                "burn_events:all", 
                start=0, 
                end=limit-1, 
                with_scores=False,
                rev=True  # Newest first
            )
            
            events = []
            for raw_event in raw_events:
                try:
                    event_data = json.loads(raw_event)
                    events.append(event_data)
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent burn events: {e}")
            return []
