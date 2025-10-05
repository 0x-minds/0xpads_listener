"""
🎪 Domain Events
Events that occur in the domain
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
import uuid

from .entities import TradeEvent, OHLCVCandle, BondingCurve, MarketData
from .value_objects import TokenAddress, Price, Volume


class DomainEvent(ABC):
    """Base class for all domain events"""
    
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.now(timezone.utc)
        self.version = 1
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        pass


@dataclass
class TradeExecuted(DomainEvent):
    """Trade execution event"""
    trade: TradeEvent
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'TradeExecuted',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.trade.token_address),
                'curve_address': str(self.trade.curve_address),
                'user_address': str(self.trade.user_address),
                'is_buy': self.trade.direction.is_buy,
                'token_amount': str(self.trade.token_amount.value),
                'eth_amount': str(self.trade.eth_amount.value),
                'price_before': str(self.trade.price_before.value),
                'price_after': str(self.trade.price_after.value),
                'total_supply': str(self.trade.total_supply.value),
                'block_number': self.trade.block_info.number,
                'tx_hash': str(self.trade.tx_hash),
                'timestamp': self.trade.timestamp.isoformat(),
                'price_impact': str(self.trade.price_impact),
                'effective_price': str(self.trade.effective_price.value)
            }
        }


@dataclass
class CandleUpdated(DomainEvent):
    """Candle update event"""
    candle: OHLCVCandle
    previous_candle: Optional[OHLCVCandle] = None
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'CandleUpdated',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.candle.token_address),
                'interval': self.candle.interval.interval,
                'timestamp': self.candle.timestamp,
                'open': str(self.candle.price_range.open.value),
                'high': str(self.candle.price_range.high.value),
                'low': str(self.candle.price_range.low.value),
                'close': str(self.candle.price_range.close.value),
                'volume': str(self.candle.volume_data.total_volume.value),
                'volume_eth': str(self.candle.volume_eth.value),
                'trades': self.candle.volume_data.trade_count,
                'buy_volume': str(self.candle.volume_data.buy_volume.value),
                'sell_volume': str(self.candle.volume_data.sell_volume.value)
            }
        }


@dataclass
class NewCandleCreated(DomainEvent):
    """New candle creation event"""
    candle: OHLCVCandle
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'NewCandleCreated',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.candle.token_address),
                'interval': self.candle.interval.interval,
                'timestamp': self.candle.timestamp,
                'initial_price': str(self.candle.price_range.open.value)
            }
        }


@dataclass
class BondingCurveDeployed(DomainEvent):
    """New bonding curve deployment event"""
    curve: BondingCurve
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'BondingCurveDeployed', 
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.curve.token_address),
                'curve_address': str(self.curve.curve_address),
                'creator_address': str(self.curve.creator_address),
                'name': self.curve.name,
                'symbol': self.curve.symbol,
                'total_supply': str(self.curve.total_supply.value),
                'created_at': self.curve.created_at.isoformat()
            }
        }


@dataclass
class MarketDataUpdated(DomainEvent):
    """Market data update event"""
    market_data: MarketData
    previous_price: Optional[Price] = None
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'MarketDataUpdated',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.market_data.token_address),
                'current_price': str(self.market_data.current_price.value),
                'price_change_24h': str(self.market_data.price_change_24h.value),
                'price_change_percent_24h': str(self.market_data.price_change_percent_24h),
                'volume_24h': str(self.market_data.volume_24h.value),
                'volume_eth_24h': str(self.market_data.volume_eth_24h.value),
                'trades_24h': self.market_data.trades_24h,
                'market_cap': str(self.market_data.market_cap.value),
                'last_updated': self.market_data.last_updated.isoformat(),
                'previous_price': str(self.previous_price.value) if self.previous_price else None
            }
        }


@dataclass
class PriceAlert(DomainEvent):
    """Price alert event"""
    token_address: TokenAddress
    current_price: Price
    threshold_price: Price
    alert_type: str  # 'above', 'below', 'change_percent'
    user_id: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'PriceAlert',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.token_address),
                'current_price': str(self.current_price.value),
                'threshold_price': str(self.threshold_price.value),
                'alert_type': self.alert_type,
                'user_id': self.user_id
            }
        }


@dataclass
class LargeTrade(DomainEvent):
    """Large trade event"""
    trade: TradeEvent
    threshold_eth: Volume
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'LargeTrade',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.trade.token_address),
                'user_address': str(self.trade.user_address),
                'is_buy': self.trade.direction.is_buy,
                'eth_amount': str(self.trade.eth_amount.value),
                'token_amount': str(self.trade.token_amount.value),
                'threshold_eth': str(self.threshold_eth.value),
                'price_impact': str(self.trade.price_impact),
                'tx_hash': str(self.trade.tx_hash)
            }
        }


@dataclass
class MilestoneReached(DomainEvent):
    """Milestone reached event"""
    curve: BondingCurve
    milestone_level: int
    reserve_eth: Volume
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'MilestoneReached',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.curve.token_address),
                'curve_address': str(self.curve.curve_address),
                'milestone_level': self.milestone_level,
                'reserve_eth': str(self.reserve_eth.value),
                'current_price': str(self.curve.current_price.value),
                'market_cap': str(self.curve.market_cap.value)
            }
        }


@dataclass
class VolumeSpike(DomainEvent):
    """Volume spike event"""
    token_address: TokenAddress
    current_volume: Volume
    average_volume: Volume
    spike_multiplier: float
    time_window_minutes: int
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'VolumeSpike',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'token_address': str(self.token_address),
                'current_volume': str(self.current_volume.value),
                'average_volume': str(self.average_volume.value),
                'spike_multiplier': self.spike_multiplier,
                'time_window_minutes': self.time_window_minutes
            }
        }


@dataclass
class RegularCreatorApproved(DomainEvent):
    """Regular token creator approved event"""
    creator_address: TokenAddress
    timestamp: int
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'RegularCreatorApproved',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'creator_address': str(self.creator_address),
                'timestamp': self.timestamp
            }
        }


@dataclass
class RegularCreatorRevoked(DomainEvent):
    """Regular token creator revoked event"""
    creator_address: TokenAddress
    timestamp: int
    
    def __post_init__(self):
        super().__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': 'RegularCreatorRevoked',
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': {
                'creator_address': str(self.creator_address),
                'timestamp': self.timestamp
            }
        }


class EventBus:
    """Event Bus for managing and dispatching events"""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = {}
        self._event_history: List[DomainEvent] = []
    
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers"""
        self._event_history.append(event)
        
        event_type = type(event).__name__
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    if callable(handler):
                        await handler(event) if hasattr(handler, '__await__') else handler(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    print(f"Error in event handler for {event_type}: {e}")
    
    def get_event_history(self, limit: int = 100) -> List[DomainEvent]:
        """Get recent event history"""
        return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()


# Global event bus instance
event_bus = EventBus()
