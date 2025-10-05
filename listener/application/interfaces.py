"""
🔌 Application Interfaces
Repository patterns and service interfaces
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime
from decimal import Decimal

from ..domain.entities import (
    TradeEvent, OHLCVCandle, BondingCurve, MarketData, ChartData
)
from ..domain.value_objects import TokenAddress, TimeInterval, Price, Volume
from ..domain.events import DomainEvent


class ITradeRepository(ABC):
    """Repository for trades"""
    
    @abstractmethod
    async def save_trade(self, trade: TradeEvent) -> None:
        """Save trade"""
        pass
    
    @abstractmethod
    async def get_trades_by_token(
        self, 
        token_address: TokenAddress, 
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[TradeEvent]:
        """Get trades for a token"""
        pass
    
    @abstractmethod
    async def get_trades_in_timerange(
        self,
        token_address: TokenAddress,
        start_time: datetime,
        end_time: datetime
    ) -> List[TradeEvent]:
        """Get trades in time range"""
        pass
    
    @abstractmethod
    async def get_trade_count_24h(self, token_address: TokenAddress) -> int:
        """Get trade count for last 24 hours"""
        pass


class ICandleRepository(ABC):
    """Repository for OHLCV candles"""
    
    @abstractmethod
    async def save_candle(self, candle: OHLCVCandle) -> None:
        """Save candle"""
        pass
    
    @abstractmethod
    async def get_candles(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        limit: int = 100,
        after_timestamp: Optional[int] = None
    ) -> List[OHLCVCandle]:
        """Get candles"""
        pass
    
    @abstractmethod
    async def get_latest_candle(
        self,
        token_address: TokenAddress,
        interval: TimeInterval
    ) -> Optional[OHLCVCandle]:
        """Get latest candle"""
        pass
    
    @abstractmethod
    async def update_candle(self, candle: OHLCVCandle) -> None:
        """Update existing candle"""
        pass
    
    @abstractmethod
    async def delete_old_candles(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        older_than: datetime
    ) -> int:
        """Delete old candles"""
        pass


class IBondingCurveRepository(ABC):
    """Repository for bonding curves"""
    
    @abstractmethod
    async def save_curve(self, curve: BondingCurve) -> None:
        """Save bonding curve"""
        pass
    
    @abstractmethod
    async def get_curve_by_token(self, token_address: TokenAddress) -> Optional[BondingCurve]:
        """Get curve by token address"""
        pass
    
    @abstractmethod
    async def get_curve_by_address(self, curve_address: TokenAddress) -> Optional[BondingCurve]:
        """Get curve by curve address"""
        pass
    
    @abstractmethod
    async def get_all_active_curves(self) -> List[BondingCurve]:
        """Get all active curves"""
        pass
    
    @abstractmethod
    async def update_curve(self, curve: BondingCurve) -> None:
        """Update curve"""
        pass
    
    @abstractmethod
    async def get_curve_count(self) -> int:
        """Get total curves count"""
        pass


class IMarketDataRepository(ABC):
    """Repository for market data"""
    
    @abstractmethod
    async def save_market_data(self, market_data: MarketData) -> None:
        """Save market data"""
        pass
    
    @abstractmethod
    async def get_market_data(self, token_address: TokenAddress) -> Optional[MarketData]:
        """Get market data"""
        pass
    
    @abstractmethod
    async def get_all_market_data(self) -> List[MarketData]:
        """Get all market data"""
        pass
    
    @abstractmethod
    async def update_market_data(self, market_data: MarketData) -> None:
        """Update market data"""
        pass


class IBurnEventRepository(ABC):
    """Repository for burn events"""
    
    @abstractmethod
    async def save_burn_event(self, burn_event: Dict[str, Any]) -> None:
        """Save burn event"""
        pass
    
    @abstractmethod
    async def get_burn_events_by_token(
        self, 
        token_address: TokenAddress, 
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get burn events for a token"""
        pass
    
    @abstractmethod
    async def get_burn_events_by_burner(
        self,
        burner_address: TokenAddress,
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get burn events for a burner"""
        pass
    
    @abstractmethod
    async def get_recent_burn_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent burn events"""
        pass


class IEventRepository(ABC):
    """Repository for domain events"""
    
    @abstractmethod
    async def save_event(self, event: DomainEvent) -> None:
        """Save domain event"""
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Get events by type"""
        pass
    
    @abstractmethod
    async def get_recent_events(self, limit: int = 100) -> List[DomainEvent]:
        """Get recent events"""
        pass


class IBlockchainService(ABC):
    """Service for blockchain communication"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to blockchain"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Connection status"""
        pass
    
    @abstractmethod
    async def get_latest_block(self) -> int:
        """Get latest block"""
        pass
    
    @abstractmethod
    async def subscribe_to_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to events"""
        pass
    
    @abstractmethod
    async def get_contract_info(self, address: TokenAddress) -> Dict[str, Any]:
        """Get contract info"""
        pass


class ICacheService(ABC):
    """Service for caching (Redis)"""
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value"""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete cache key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set JSON value"""
        pass
    
    @abstractmethod
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value"""
        pass
    
    @abstractmethod
    async def publish(self, channel: str, message: Any) -> None:
        """Publish to pub/sub channel"""
        pass
    
    @abstractmethod
    async def subscribe(self, channel: str) -> AsyncIterator[Any]:
        """Subscribe to pub/sub channel"""
        pass
    
    @abstractmethod
    async def zadd(self, key: str, mapping: Dict[str, float]) -> None:
        """Add to sorted set"""
        pass
    
    @abstractmethod
    async def zrange(
        self, 
        key: str, 
        start: int = 0, 
        end: int = -1,
        with_scores: bool = False
    ) -> List[Any]:
        """Get range from sorted set"""
        pass


class IWebSocketService(ABC):
    """Service for WebSocket communication"""
    
    @abstractmethod
    async def start_server(self) -> None:
        """Start WebSocket server"""
        pass
    
    @abstractmethod
    async def stop_server(self) -> None:
        """Stop WebSocket server"""
        pass
    
    @abstractmethod
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all clients"""
        pass
    
    @abstractmethod
    async def send_to_room(self, room: str, message: Dict[str, Any]) -> None:
        """Send message to specific room"""
        pass
    
    @abstractmethod
    async def connect_to_backend(self) -> None:
        """Connect to Node.js backend"""
        pass
    
    @abstractmethod
    async def send_to_backend(self, event: str, data: Dict[str, Any]) -> None:
        """Send data to backend"""
        pass
    
    @abstractmethod
    async def get_active_connections(self) -> int:
        """Get active connections count"""
        pass


class IChartDataService(ABC):
    """Service for chart data management"""
    
    @abstractmethod
    async def get_chart_data(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        limit: int = 100
    ) -> ChartData:
        """Get chart data"""
        pass
    
    @abstractmethod
    async def get_real_time_data(self, token_address: TokenAddress) -> MarketData:
        """Get real-time data"""
        pass
    
    @abstractmethod
    async def get_supported_tokens(self) -> List[BondingCurve]:
        """Get list of supported tokens"""
        pass
    
    @abstractmethod
    async def update_chart_data(self, trade: TradeEvent) -> None:
        """Update chart data with new trade"""
        pass


class IEventProcessingService(ABC):
    """Service for processing events"""
    
    @abstractmethod
    async def process_trade_event(self, raw_event: Dict[str, Any]) -> TradeEvent:
        """Process raw trade event"""
        pass
    
    @abstractmethod
    async def process_batch_events(self, raw_events: List[Dict[str, Any]]) -> List[TradeEvent]:
        """Process batch events"""
        pass
    
    @abstractmethod
    async def validate_event(self, raw_event: Dict[str, Any]) -> bool:
        """Validate event"""
        pass
    
    @abstractmethod
    async def enrich_event_data(self, trade: TradeEvent) -> TradeEvent:
        """Enrich event data"""
        pass


class IAlertService(ABC):
    """Service for alerts and notifications"""
    
    @abstractmethod
    async def check_price_alerts(self, market_data: MarketData) -> None:
        """Check price alerts"""
        pass
    
    @abstractmethod
    async def check_volume_alerts(self, candle: OHLCVCandle) -> None:
        """Check volume alerts"""
        pass
    
    @abstractmethod
    async def send_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Send alert"""
        pass
    
    @abstractmethod
    async def register_alert(
        self,
        user_id: str,
        token_address: TokenAddress,
        alert_type: str,
        threshold: Decimal
    ) -> str:
        """Register new alert"""
        pass


class IMetricsService(ABC):
    """Service for performance metrics"""
    
    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record metric"""
        pass
    
    @abstractmethod
    async def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter"""
        pass
    
    @abstractmethod
    async def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timer"""
        pass
    
    @abstractmethod
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system status"""
        pass
