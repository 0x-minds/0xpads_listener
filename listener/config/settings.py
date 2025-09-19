
import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal

# Load .env file at module level
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    print("⚠️ python-dotenv not installed, skipping .env file loading")


class BlockchainSettings(BaseSettings):
    """Blockchain settings"""
    model_config = SettingsConfigDict(env_prefix='BLOCKCHAIN_')
    
    ws_url: str = Field(default="ws://127.0.0.1:8545", description="Blockchain WebSocket URL")
    http_url: str = Field(default="http://127.0.0.1:8545", description="Blockchain HTTP URL")
    chain_id: int = Field(default=31337, description="Chain ID")
    factory_address: Optional[str] = Field(default=None, description="Factory contract address", alias="BONDING_CURVE_FACTORY_ADDRESS")
    max_reconnection_attempts: int = Field(default=10, description="Max reconnection attempts")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    
    @validator('factory_address')
    def validate_factory_address(cls, v):
        if v and not v.startswith('0x'):
            raise ValueError('Factory address must start with 0x')
        return v


class RedisSettings(BaseSettings):
    """Redis settings"""
    model_config = SettingsConfigDict(env_prefix='REDIS_')
    
    url: str = Field(default="redis://localhost:6379", description="Redis URL")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=20, description="Max connection pool size")
    socket_timeout: float = Field(default=5.0, description="Socket timeout in seconds")
    socket_connect_timeout: float = Field(default=5.0, description="Connection timeout")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    
    # Keys for different data types
    trades_key_prefix: str = Field(default="trades:", description="Prefix for trade keys")
    candles_key_prefix: str = Field(default="candles:", description="Prefix for candle keys")
    market_data_key_prefix: str = Field(default="market:", description="Prefix for market data keys")
    events_key_prefix: str = Field(default="events:", description="Prefix for event keys")


class ProcessingSettings(BaseSettings):
    """تنظیمات data processing"""
    batch_size: int = Field(default=100, description="Event batch size")
    processing_interval_ms: int = Field(default=1000, description="Processing interval")
    ohlcv_intervals: List[str] = Field(
        default=["1m", "5m", "15m", "1h", "4h", "1d"],
        description="OHLCV intervals"
    )
    max_candles_memory: int = Field(default=1000, description="Max candles in memory per token")
    large_trade_threshold_eth: Decimal = Field(default=Decimal('1.0'), description="Large trade threshold")
    price_change_alert_threshold: Decimal = Field(default=Decimal('10.0'), description="Price change alert %")
    
    @validator('ohlcv_intervals')
    def validate_intervals(cls, v):
        valid_intervals = {'1m', '5m', '15m', '1h', '4h', '1d'}
        for interval in v:
            if interval not in valid_intervals:
                raise ValueError(f'Invalid interval: {interval}. Valid: {valid_intervals}')
        return v


class WebSocketSettings(BaseSettings):
    """تنظیمات WebSocket server"""
    host: str = Field(default="0.0.0.0", description="WebSocket host")
    port: int = Field(default=3001, description="WebSocket port")
    max_connections: int = Field(default=1000, description="Max concurrent connections")
    ping_interval: int = Field(default=20, description="Ping interval in seconds")
    ping_timeout: int = Field(default=10, description="Ping timeout in seconds")
    cors_allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Node.js backend connection
    backend_socket_url: str = Field(
        default="http://localhost:3000", 
        description="Backend Socket.IO server URL"
    )
    backend_namespace: str = Field(default="/charts", description="Socket.IO namespace")


class LoggingSettings(BaseSettings):
    """تنظیمات logging"""
    level: str = Field(default="INFO", description="Log level")
    file_path: str = Field(default="./logs/listener.log", description="Log file path")
    max_file_size: str = Field(default="10MB", description="Max log file size")
    backup_count: int = Field(default=5, description="Number of backup files")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name} | {message}",
        description="Log format"
    )
    
    # Special loggers
    blockchain_level: str = Field(default="INFO", description="Blockchain logger level")
    processing_level: str = Field(default="INFO", description="Processing logger level")
    websocket_level: str = Field(default="INFO", description="WebSocket logger level")


class PerformanceSettings(BaseSettings):
    """تنظیمات performance و monitoring"""
    enable_metrics: bool = Field(default=True, description="Enable performance metrics")
    metrics_interval: int = Field(default=60, description="Metrics collection interval")
    memory_threshold_mb: int = Field(default=512, description="Memory usage threshold")
    cpu_threshold_percent: float = Field(default=80.0, description="CPU usage threshold")
    
    # Cache settings
    candle_cache_ttl: int = Field(default=300, description="Candle cache TTL in seconds")
    market_data_cache_ttl: int = Field(default=30, description="Market data cache TTL")
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    max_requests_per_minute: int = Field(default=100, description="Max requests per minute per IP")


class DatabaseSettings(BaseSettings):
    """تنظیمات database (اگر نیاز بود)"""
    url: Optional[str] = Field(default=None, description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")


class Settings(BaseSettings):
    """تنظیمات کلی"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Environment
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Sub-settings
    blockchain: BlockchainSettings = Field(default_factory=BlockchainSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    websocket: WebSocketSettings = Field(default_factory=WebSocketSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = {'development', 'staging', 'production'}
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of {valid_envs}')
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance - برای dependency injection"""
    return settings
