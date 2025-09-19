"""
🏛️ Domain Value Objects
Core value objects for domain entities
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union
from web3 import Web3
from pydantic import BaseModel, Field, validator


@dataclass(frozen=True)
class TokenAddress:
    """Token address with validation"""
    value: str
    
    def __post_init__(self):
        if not Web3.is_address(self.value):
            raise ValueError(f"Invalid token address: {self.value}")
        # Convert to checksum address
        object.__setattr__(self, 'value', Web3.to_checksum_address(self.value))
    
    def short_address(self) -> str:
        """Short display of address"""
        return f"{self.value[:6]}...{self.value[-4:]}"
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Price:
    """Price with appropriate precision"""
    value: Decimal
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Price cannot be negative")
        # Round to 18 decimal places (Wei precision)
        rounded_value = self.value.quantize(
            Decimal('0.000000000000000001'), 
            rounding=ROUND_HALF_UP
        )
        object.__setattr__(self, 'value', rounded_value)
    
    @classmethod
    def from_wei(cls, wei_value: Union[int, str]) -> 'Price':
        """Convert from Wei to ETH"""
        eth_value = Decimal(str(wei_value)) / Decimal('1000000000000000000')
        return cls(eth_value)
    
    @classmethod
    def from_string(cls, price_str: str) -> 'Price':
        """Convert from string"""
        return cls(Decimal(price_str))
    
    def to_wei(self) -> int:
        """Convert to Wei"""
        return int(self.value * Decimal('1000000000000000000'))
    
    def percentage_change(self, other: 'Price') -> Decimal:
        """Calculate percentage change"""
        if other.value == 0:
            return Decimal('0')
        return ((self.value - other.value) / other.value) * Decimal('100')
    
    def __add__(self, other: 'Price') -> 'Price':
        return Price(self.value + other.value)
    
    def __sub__(self, other: 'Price') -> 'Price':
        return Price(self.value - other.value)
    
    def __mul__(self, multiplier: Union[Decimal, int, float]) -> 'Price':
        return Price(self.value * Decimal(str(multiplier)))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Volume:
    """Trading volume"""
    value: Decimal
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Volume cannot be negative")
    
    @classmethod
    def from_wei(cls, wei_value: Union[int, str]) -> 'Volume':
        """Convert from Wei"""
        token_value = Decimal(str(wei_value)) / Decimal('1000000000000000000')
        return cls(token_value)
    
    def __add__(self, other: 'Volume') -> 'Volume':
        return Volume(self.value + other.value)
    
    def __str__(self) -> str:
        return str(self.value)


class TimeInterval(BaseModel):
    """Time interval for candlestick"""
    interval: str = Field(..., pattern=r'^(1m|5m|15m|1h|4h|1d)$')
    
    @property
    def seconds(self) -> int:
        """Convert to seconds"""
        mapping = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return mapping[self.interval]
    
    def floor_timestamp(self, timestamp: int) -> int:
        """Round timestamp to interval start"""
        return (timestamp // self.seconds) * self.seconds


@dataclass(frozen=True)
class BlockInfo:
    """Block information"""
    number: int
    timestamp: int
    hash: str
    
    def __post_init__(self):
        if self.number < 0:
            raise ValueError("Block number cannot be negative")
        if self.timestamp < 0:
            raise ValueError("Timestamp cannot be negative")


@dataclass(frozen=True)
class TransactionHash:
    """Transaction hash"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 66:
            raise ValueError(f"Invalid transaction hash: {self.value}")
    
    def short_hash(self) -> str:
        """Short display of hash"""
        return f"{self.value[:10]}...{self.value[-8:]}"
    
    def __str__(self) -> str:
        return self.value


class TradeDirection(BaseModel):
    """جهت معامله"""
    is_buy: bool
    
    @property
    def direction_str(self) -> str:
        return "BUY" if self.is_buy else "SELL"
    
    @property
    def emoji(self) -> str:
        return "🟢" if self.is_buy else "🔴"


@dataclass(frozen=True)
class PriceRange:
    """محدوده قیمت برای OHLCV"""
    open: Price
    high: Price
    low: Price
    close: Price
    
    def __post_init__(self):
        if self.high.value < max(self.open.value, self.close.value):
            raise ValueError("High price must be >= open and close prices")
        if self.low.value > min(self.open.value, self.close.value):
            raise ValueError("Low price must be <= open and close prices")
    
    @property
    def price_change(self) -> Price:
        """تغییر قیمت از open به close"""
        return Price(self.close.value - self.open.value)
    
    @property
    def price_change_percent(self) -> Decimal:
        """درصد تغییر قیمت"""
        if self.open.value == 0:
            return Decimal('0')
        return (self.price_change.value / self.open.value) * Decimal('100')
    
    @property
    def is_bullish(self) -> bool:
        """آیا candle صعودی است"""
        return self.close.value > self.open.value


@dataclass(frozen=True)
class VolumeData:
    """اطلاعات حجم معاملات"""
    total_volume: Volume
    buy_volume: Volume
    sell_volume: Volume
    trade_count: int
    
    def __post_init__(self):
        if self.trade_count < 0:
            raise ValueError("Trade count cannot be negative")
        # Validate volumes
        expected_total = Volume(self.buy_volume.value + self.sell_volume.value)
        if abs(self.total_volume.value - expected_total.value) > Decimal('0.000001'):
            raise ValueError("Total volume must equal buy_volume + sell_volume")
    
    @property
    def buy_sell_ratio(self) -> Optional[Decimal]:
        """نسبت خرید به فروش"""
        if self.sell_volume.value == 0:
            return None
        return self.buy_volume.value / self.sell_volume.value
    
    @property
    def average_trade_size(self) -> Volume:
        """میانگین اندازه معامله"""
        if self.trade_count == 0:
            return Volume(Decimal('0'))
        return Volume(self.total_volume.value / Decimal(str(self.trade_count)))
