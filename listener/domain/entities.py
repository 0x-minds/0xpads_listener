"""
🏛️ Domain Entities
Core business entities
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List
from decimal import Decimal

from .value_objects import (
    TokenAddress, Price, Volume, TimeInterval, BlockInfo,
    TransactionHash, TradeDirection, PriceRange, VolumeData
)


@dataclass
class TradeEvent:
    """Trade event - main entity for charting"""
    token_address: TokenAddress
    curve_address: TokenAddress
    user_address: TokenAddress
    direction: TradeDirection
    token_amount: Volume
    eth_amount: Volume
    price_before: Price
    price_after: Price
    total_supply: Volume
    block_info: BlockInfo
    tx_hash: TransactionHash
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def price_impact(self) -> Decimal:
        """Calculate price impact"""
        if self.price_before.value == 0:
            return Decimal('0')
        return abs(self.price_after.value - self.price_before.value) / self.price_before.value * Decimal('100')
    
    @property
    def effective_price(self) -> Price:
        """Effective trade price"""
        if self.token_amount.value == 0:
            return self.price_after
        return Price(self.eth_amount.value / self.token_amount.value)
    
    def is_large_trade(self, threshold_eth: Decimal = Decimal('1.0')) -> bool:
        """Whether the trade is large"""
        return self.eth_amount.value >= threshold_eth


@dataclass 
class OHLCVCandle:
    """OHLCV candle for charting"""
    token_address: TokenAddress
    interval: TimeInterval
    timestamp: int  # Unix timestamp (start of interval)
    price_range: PriceRange
    volume_data: VolumeData
    volume_eth: Volume
    
    @classmethod
    def create_empty(
        cls,
        token_address: TokenAddress,
        interval: TimeInterval,
        timestamp: int,
        initial_price: Price
    ) -> 'OHLCVCandle':
        """Create empty candle"""
        price_range = PriceRange(
            open=initial_price,
            high=initial_price,
            low=initial_price,
            close=initial_price
        )
        volume_data = VolumeData(
            total_volume=Volume(Decimal('0')),
            buy_volume=Volume(Decimal('0')),
            sell_volume=Volume(Decimal('0')),
            trade_count=0
        )
        return cls(
            token_address=token_address,
            interval=interval,
            timestamp=timestamp,
            price_range=price_range,
            volume_data=volume_data,
            volume_eth=Volume(Decimal('0'))
        )
    
    def update_with_trade(self, trade: TradeEvent) -> None:
        """Update candle with new trade"""
        # Update price range
        new_high = Price(max(self.price_range.high.value, trade.price_after.value))
        new_low = Price(min(self.price_range.low.value, trade.price_after.value))
        
        self.price_range = PriceRange(
            open=self.price_range.open,
            high=new_high,
            low=new_low,
            close=trade.price_after
        )
        
        # Update volumes
        new_total = Volume(self.volume_data.total_volume.value + trade.token_amount.value)
        new_eth_volume = Volume(self.volume_eth.value + trade.eth_amount.value)
        
        if trade.direction.is_buy:
            new_buy = Volume(self.volume_data.buy_volume.value + trade.token_amount.value)
            new_sell = self.volume_data.sell_volume
        else:
            new_buy = self.volume_data.buy_volume
            new_sell = Volume(self.volume_data.sell_volume.value + trade.token_amount.value)
        
        self.volume_data = VolumeData(
            total_volume=new_total,
            buy_volume=new_buy,
            sell_volume=new_sell,
            trade_count=self.volume_data.trade_count + 1
        )
        
        self.volume_eth = new_eth_volume


@dataclass
class BondingCurve:
    """Bonding Curve Entity"""
    token_address: TokenAddress
    curve_address: TokenAddress
    creator_address: TokenAddress
    name: str
    symbol: str
    total_supply: Volume
    current_supply: Volume
    current_price: Price
    reserve_balance: Volume
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deployed_at: Optional[datetime] = None
    migrated_at: Optional[datetime] = None
    
    # Trading statistics
    total_trades: int = 0
    total_volume_eth: Volume = field(default_factory=lambda: Volume(Decimal('0')))
    unique_traders: int = 0
    
    # Milestones
    current_milestone: int = 0
    is_ready_for_dex: bool = False
    is_migrated: bool = False
    
    @property
    def market_cap(self) -> Volume:
        """Calculate market cap"""
        return Volume(self.current_supply.value * self.current_price.value)
    
    @property
    def circulating_supply_percentage(self) -> Decimal:
        """Percentage of tokens in circulation"""
        if self.total_supply.value == 0:
            return Decimal('0')
        return (self.current_supply.value / self.total_supply.value) * Decimal('100')
    
    def update_from_trade(self, trade: TradeEvent) -> None:
        """Update from trade"""
        self.current_price = trade.price_after
        self.current_supply = trade.total_supply
        self.total_trades += 1
        self.total_volume_eth = Volume(self.total_volume_eth.value + trade.eth_amount.value)


@dataclass
class TradingSession:
    """Trading session for a token"""
    token_address: TokenAddress
    session_start: datetime
    session_end: Optional[datetime] = None
    trades: List[TradeEvent] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Session duration in minutes"""
        if not self.session_end:
            end_time = datetime.now(timezone.utc)
        else:
            end_time = self.session_end
        
        duration = end_time - self.session_start
        return duration.total_seconds() / 60
    
    @property
    def total_volume_eth(self) -> Volume:
        """Total ETH volume in session"""
        total = sum(trade.eth_amount.value for trade in self.trades)
        return Volume(total)
    
    @property
    def unique_traders(self) -> int:
        """Number of unique traders"""
        return len(set(trade.user_address.value for trade in self.trades))
    
    @property
    def price_change_session(self) -> Optional[Price]:
        """Price change in session"""
        if not self.trades:
            return None
        first_trade = self.trades[0]
        last_trade = self.trades[-1]
        return Price(last_trade.price_after.value - first_trade.price_before.value)
    
    def add_trade(self, trade: TradeEvent) -> None:
        """Add trade to session"""
        self.trades.append(trade)
    
    def close_session(self) -> None:
        """Close session"""
        self.session_end = datetime.now(timezone.utc)


@dataclass
class MarketData:
    """Real-time market data"""
    token_address: TokenAddress
    current_price: Price
    price_change_24h: Price
    price_change_percent_24h: Decimal
    volume_24h: Volume
    volume_eth_24h: Volume
    trades_24h: int
    market_cap: Volume
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Technical indicators (optional)
    rsi: Optional[Decimal] = None
    moving_avg_24h: Optional[Price] = None
    volatility_24h: Optional[Decimal] = None
    
    @property
    def is_bullish_24h(self) -> bool:
        """Whether it has been bullish in the last 24 hours"""
        return self.price_change_24h.value > 0
    
    @property
    def volume_trend(self) -> str:
        """Trading volume trend"""
        # This should be compared with previous data
        return "neutral"  # placeholder


@dataclass
class ChartData:
    """Complete chart data"""
    token_address: TokenAddress
    interval: TimeInterval
    candles: List[OHLCVCandle]
    market_data: MarketData
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def latest_candle(self) -> Optional[OHLCVCandle]:
        """Latest candle"""
        return self.candles[-1] if self.candles else None
    
    @property
    def price_trend(self) -> str:
        """Overall price trend"""
        if len(self.candles) < 2:
            return "neutral"
        
        first_candle = self.candles[0]
        last_candle = self.candles[-1]
        
        if last_candle.price_range.close.value > first_candle.price_range.open.value:
            return "bullish"
        elif last_candle.price_range.close.value < first_candle.price_range.open.value:
            return "bearish"
        else:
            return "neutral"
    
    def get_candles_for_period(self, hours: int) -> List[OHLCVCandle]:
        """Get candles for a time period"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        return [c for c in self.candles if c.timestamp >= cutoff_time]
