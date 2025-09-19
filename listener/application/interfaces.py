"""
🔌 Application Interfaces
Repository patterns و service interfaces
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
    """Repository برای trades"""
    
    @abstractmethod
    async def save_trade(self, trade: TradeEvent) -> None:
        """ذخیره معامله"""
        pass
    
    @abstractmethod
    async def get_trades_by_token(
        self, 
        token_address: TokenAddress, 
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[TradeEvent]:
        """دریافت معاملات یک توکن"""
        pass
    
    @abstractmethod
    async def get_trades_in_timerange(
        self,
        token_address: TokenAddress,
        start_time: datetime,
        end_time: datetime
    ) -> List[TradeEvent]:
        """دریافت معاملات در یک بازه زمانی"""
        pass
    
    @abstractmethod
    async def get_trade_count_24h(self, token_address: TokenAddress) -> int:
        """تعداد معاملات 24 ساعت گذشته"""
        pass


class ICandleRepository(ABC):
    """Repository برای OHLCV candles"""
    
    @abstractmethod
    async def save_candle(self, candle: OHLCVCandle) -> None:
        """ذخیره candle"""
        pass
    
    @abstractmethod
    async def get_candles(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        limit: int = 100,
        after_timestamp: Optional[int] = None
    ) -> List[OHLCVCandle]:
        """دریافت candles"""
        pass
    
    @abstractmethod
    async def get_latest_candle(
        self,
        token_address: TokenAddress,
        interval: TimeInterval
    ) -> Optional[OHLCVCandle]:
        """دریافت آخرین candle"""
        pass
    
    @abstractmethod
    async def update_candle(self, candle: OHLCVCandle) -> None:
        """به‌روزرسانی candle موجود"""
        pass
    
    @abstractmethod
    async def delete_old_candles(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        older_than: datetime
    ) -> int:
        """حذف candles قدیمی"""
        pass


class IBondingCurveRepository(ABC):
    """Repository برای bonding curves"""
    
    @abstractmethod
    async def save_curve(self, curve: BondingCurve) -> None:
        """ذخیره bonding curve"""
        pass
    
    @abstractmethod
    async def get_curve_by_token(self, token_address: TokenAddress) -> Optional[BondingCurve]:
        """دریافت curve بر اساس token address"""
        pass
    
    @abstractmethod
    async def get_curve_by_address(self, curve_address: TokenAddress) -> Optional[BondingCurve]:
        """دریافت curve بر اساس curve address"""
        pass
    
    @abstractmethod
    async def get_all_active_curves(self) -> List[BondingCurve]:
        """دریافت همه curves فعال"""
        pass
    
    @abstractmethod
    async def update_curve(self, curve: BondingCurve) -> None:
        """به‌روزرسانی curve"""
        pass
    
    @abstractmethod
    async def get_curve_count(self) -> int:
        """تعداد کل curves"""
        pass


class IMarketDataRepository(ABC):
    """Repository برای market data"""
    
    @abstractmethod
    async def save_market_data(self, market_data: MarketData) -> None:
        """ذخیره market data"""
        pass
    
    @abstractmethod
    async def get_market_data(self, token_address: TokenAddress) -> Optional[MarketData]:
        """دریافت market data"""
        pass
    
    @abstractmethod
    async def get_all_market_data(self) -> List[MarketData]:
        """دریافت همه market data"""
        pass
    
    @abstractmethod
    async def update_market_data(self, market_data: MarketData) -> None:
        """به‌روزرسانی market data"""
        pass


class IEventRepository(ABC):
    """Repository برای domain events"""
    
    @abstractmethod
    async def save_event(self, event: DomainEvent) -> None:
        """ذخیره domain event"""
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
        after_timestamp: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """دریافت events بر اساس نوع"""
        pass
    
    @abstractmethod
    async def get_recent_events(self, limit: int = 100) -> List[DomainEvent]:
        """دریافت events اخیر"""
        pass


class IBlockchainService(ABC):
    """Service برای ارتباط با blockchain"""
    
    @abstractmethod
    async def connect(self) -> None:
        """اتصال به blockchain"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """قطع اتصال"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """وضعیت اتصال"""
        pass
    
    @abstractmethod
    async def get_latest_block(self) -> int:
        """دریافت آخرین block"""
        pass
    
    @abstractmethod
    async def subscribe_to_events(self) -> AsyncIterator[Dict[str, Any]]:
        """subscribe به events"""
        pass
    
    @abstractmethod
    async def get_contract_info(self, address: TokenAddress) -> Dict[str, Any]:
        """دریافت اطلاعات contract"""
        pass


class ICacheService(ABC):
    """Service برای caching (Redis)"""
    
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
    """Service برای WebSocket communication"""
    
    @abstractmethod
    async def start_server(self) -> None:
        """شروع WebSocket server"""
        pass
    
    @abstractmethod
    async def stop_server(self) -> None:
        """توقف WebSocket server"""
        pass
    
    @abstractmethod
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast پیام به همه clients"""
        pass
    
    @abstractmethod
    async def send_to_room(self, room: str, message: Dict[str, Any]) -> None:
        """ارسال پیام به room مشخص"""
        pass
    
    @abstractmethod
    async def connect_to_backend(self) -> None:
        """اتصال به Node.js backend"""
        pass
    
    @abstractmethod
    async def send_to_backend(self, event: str, data: Dict[str, Any]) -> None:
        """ارسال data به backend"""
        pass
    
    @abstractmethod
    async def get_active_connections(self) -> int:
        """تعداد اتصالات فعال"""
        pass


class IChartDataService(ABC):
    """Service برای chart data management"""
    
    @abstractmethod
    async def get_chart_data(
        self,
        token_address: TokenAddress,
        interval: TimeInterval,
        limit: int = 100
    ) -> ChartData:
        """دریافت chart data"""
        pass
    
    @abstractmethod
    async def get_real_time_data(self, token_address: TokenAddress) -> MarketData:
        """دریافت real-time data"""
        pass
    
    @abstractmethod
    async def get_supported_tokens(self) -> List[BondingCurve]:
        """دریافت لیست tokens پشتیبانی شده"""
        pass
    
    @abstractmethod
    async def update_chart_data(self, trade: TradeEvent) -> None:
        """به‌روزرسانی chart data با معامله جدید"""
        pass


class IEventProcessingService(ABC):
    """Service برای processing events"""
    
    @abstractmethod
    async def process_trade_event(self, raw_event: Dict[str, Any]) -> TradeEvent:
        """پردازش raw trade event"""
        pass
    
    @abstractmethod
    async def process_batch_events(self, raw_events: List[Dict[str, Any]]) -> List[TradeEvent]:
        """پردازش batch events"""
        pass
    
    @abstractmethod
    async def validate_event(self, raw_event: Dict[str, Any]) -> bool:
        """اعتبارسنجی event"""
        pass
    
    @abstractmethod
    async def enrich_event_data(self, trade: TradeEvent) -> TradeEvent:
        """غنی‌سازی event data"""
        pass


class IAlertService(ABC):
    """Service برای alerts و notifications"""
    
    @abstractmethod
    async def check_price_alerts(self, market_data: MarketData) -> None:
        """بررسی price alerts"""
        pass
    
    @abstractmethod
    async def check_volume_alerts(self, candle: OHLCVCandle) -> None:
        """بررسی volume alerts"""
        pass
    
    @abstractmethod
    async def send_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """ارسال alert"""
        pass
    
    @abstractmethod
    async def register_alert(
        self,
        user_id: str,
        token_address: TokenAddress,
        alert_type: str,
        threshold: Decimal
    ) -> str:
        """ثبت alert جدید"""
        pass


class IMetricsService(ABC):
    """Service برای performance metrics"""
    
    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """ثبت metric"""
        pass
    
    @abstractmethod
    async def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """افزایش counter"""
        pass
    
    @abstractmethod
    async def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """ثبت timer"""
        pass
    
    @abstractmethod
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه metrics"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        pass
