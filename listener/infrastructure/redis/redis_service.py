"""
🔴 Redis Service Implementation
Cache service با Redis
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, AsyncIterator
import redis.asyncio as redis
from redis.asyncio import Redis
from loguru import logger

from ...application.interfaces import ICacheService
from ...config.settings import Settings


class RedisService(ICacheService):
    """Redis implementation برای cache service"""
    
    def __init__(self, settings: Settings):
        self.settings = settings.redis
        self._pool: Optional[Redis] = None
        self._pubsub_connection: Optional[Redis] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            # Build Redis URL from settings or use provided URL
            if hasattr(self.settings, 'password') and self.settings.password:
                redis_url = f"redis://:{self.settings.password}@{self.settings.host}:{self.settings.port}/{self.settings.db}"
            else:
                redis_url = self.settings.url
                
            logger.info(f"🔗 Connecting to Redis: redis://{self.settings.host}:{self.settings.port}/{self.settings.db}")
            
            self._pool = redis.from_url(
                redis_url,
                max_connections=self.settings.max_connections,
                socket_timeout=self.settings.socket_timeout,
                socket_connect_timeout=self.settings.socket_connect_timeout,
                retry_on_timeout=self.settings.retry_on_timeout,
                decode_responses=True
            )
            
            # Test connection
            await self._pool.ping()
            
            # Separate connection for pub/sub
            self._pubsub_connection = redis.from_url(
                redis_url,
                decode_responses=True
            )
            
            self._is_connected = True
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        try:
            if self._pool:
                await self._pool.close()
            if self._pubsub_connection:
                await self._pubsub_connection.close()
            self._is_connected = False
            logger.info("🔌 Redis disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Redis: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    async def _ensure_connection(self) -> None:
        """اطمینان از اتصال"""
        if not self._is_connected:
            await self.connect()
    
    # Basic cache operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value"""
        await self._ensure_connection()
        
        try:
            if ttl:
                await self._pool.setex(key, ttl, str(value))
            else:
                await self._pool.set(key, str(value))
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        await self._ensure_connection()
        
        try:
            value = await self._pool.get(key)
            return value if value is not None else None
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> None:
        """Delete cache key"""
        await self._ensure_connection()
        
        try:
            await self._pool.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        await self._ensure_connection()
        
        try:
            result = await self._pool.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking key existence {key}: {e}")
            return False
    
    # JSON operations
    async def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set JSON value"""
        try:
            json_str = json.dumps(value, default=str)
            await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {e}")
            raise
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value"""
        try:
            value = await self.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {e}")
            return None
    
    # Pub/Sub operations
    async def publish(self, channel: str, message: Any) -> None:
        """Publish to pub/sub channel"""
        await self._ensure_connection()
        
        try:
            if isinstance(message, dict):
                message = json.dumps(message, default=str)
            elif not isinstance(message, str):
                message = str(message)
                
            await self._pool.publish(channel, message)
            logger.debug(f"📢 Published to {channel}: {len(str(message))} chars")
            
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise
    
    async def subscribe(self, channel: str) -> AsyncIterator[Any]:
        """Subscribe to pub/sub channel"""
        await self._ensure_connection()
        
        try:
            pubsub = self._pubsub_connection.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"📡 Subscribed to channel: {channel}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Try to parse as JSON
                        data = json.loads(message['data'])
                        yield data
                    except json.JSONDecodeError:
                        # Return as string
                        yield message['data']
                        
        except Exception as e:
            logger.error(f"Error subscribing to {channel}: {e}")
            raise
    
    # Sorted Set operations (برای time-series data)
    async def zadd(self, key: str, mapping: Dict[str, float]) -> None:
        """Add to sorted set"""
        await self._ensure_connection()
        
        try:
            await self._pool.zadd(key, mapping)
        except Exception as e:
            logger.error(f"Error adding to sorted set {key}: {e}")
            raise
    
    async def zrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        with_scores: bool = False
    ) -> List[Any]:
        """Get range from sorted set"""
        await self._ensure_connection()
        
        try:
            if with_scores:
                result = await self._pool.zrange(key, start, end, withscores=True)
                # Convert tuples to list of dicts
                return [{'value': item[0], 'score': item[1]} for item in result]
            else:
                return await self._pool.zrange(key, start, end)
        except Exception as e:
            logger.error(f"Error getting range from sorted set {key}: {e}")
            return []
    
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove items by score range"""
        await self._ensure_connection()
        
        try:
            return await self._pool.zremrangebyscore(key, min_score, max_score)
        except Exception as e:
            logger.error(f"Error removing range from sorted set {key}: {e}")
            return 0
    
    # List operations (برای queues)
    async def lpush(self, key: str, *values: Any) -> None:
        """Push to left of list"""
        await self._ensure_connection()
        
        try:
            await self._pool.lpush(key, *[json.dumps(v, default=str) if isinstance(v, dict) else str(v) for v in values])
        except Exception as e:
            logger.error(f"Error pushing to list {key}: {e}")
            raise
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop from right of list"""
        await self._ensure_connection()
        
        try:
            value = await self._pool.rpop(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error popping from list {key}: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        await self._ensure_connection()
        
        try:
            return await self._pool.llen(key)
        except Exception as e:
            logger.error(f"Error getting list length {key}: {e}")
            return 0
    
    # Hash operations (برای structured data)
    async def hset(self, key: str, mapping: Dict[str, Any]) -> None:
        """Set hash fields"""
        await self._ensure_connection()
        
        try:
            # Convert values to strings
            str_mapping = {k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v) 
                          for k, v in mapping.items()}
            await self._pool.hset(key, mapping=str_mapping)
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
            raise
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        await self._ensure_connection()
        
        try:
            value = await self._pool.hget(key, field)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error getting hash field {key}.{field}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        await self._ensure_connection()
        
        try:
            result = await self._pool.hgetall(key)
            
            # Try to parse JSON values
            parsed_result = {}
            for k, v in result.items():
                try:
                    parsed_result[k] = json.loads(v)
                except json.JSONDecodeError:
                    parsed_result[k] = v
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error getting hash {key}: {e}")
            return {}
    
    # Utility methods
    async def flushdb(self) -> None:
        """Flush current database (برای testing)"""
        await self._ensure_connection()
        
        try:
            await self._pool.flushdb()
            logger.warning("🗑️ Redis database flushed")
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            raise
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        await self._ensure_connection()
        
        try:
            return await self._pool.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    async def ttl(self, key: str) -> int:
        """Get key TTL"""
        await self._ensure_connection()
        
        try:
            return await self._pool.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for {key}: {e}")
            return -1
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set key expiration"""
        await self._ensure_connection()
        
        try:
            return await self._pool.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiration for {key}: {e}")
            return False
    
    # Specialized methods for our use case
    async def cache_trade_data(self, token_address: str, trade_data: Dict[str, Any]) -> None:
        """Cache آخرین trade data"""
        key = f"{self.settings.trades_key_prefix}latest:{token_address}"
        await self.set_json(key, trade_data, ttl=300)  # 5 minutes
    
    async def cache_candle_data(self, token_address: str, interval: str, candles: List[Dict[str, Any]]) -> None:
        """Cache candle data"""
        key = f"{self.settings.candles_key_prefix}{token_address}:{interval}"
        await self.set_json(key, candles, ttl=60)  # 1 minute
    
    async def cache_market_data(self, token_address: str, market_data: Dict[str, Any]) -> None:
        """Cache market data"""
        key = f"{self.settings.market_data_key_prefix}{token_address}"
        await self.set_json(key, market_data, ttl=30)  # 30 seconds
    
    async def get_cached_market_data(self, token_address: str) -> Optional[Dict[str, Any]]:
        """دریافت cached market data"""
        key = f"{self.settings.market_data_key_prefix}{token_address}"
        return await self.get_json(key)
    
    async def add_to_trade_stream(self, token_address: str, trade_data: Dict[str, Any]) -> None:
        """اضافه کردن به trade stream (time-series)"""
        timestamp = trade_data.get('timestamp', asyncio.get_event_loop().time())
        key = f"{self.settings.trades_key_prefix}stream:{token_address}"
        
        # Add to sorted set with timestamp as score
        await self.zadd(key, {json.dumps(trade_data, default=str): timestamp})
        
        # Keep only last 1000 trades
        total_trades = await self._pool.zcard(key)
        if total_trades > 1000:
            await self._pool.zremrangebyrank(key, 0, total_trades - 1001)
    
    async def get_recent_trades(self, token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """دریافت trades اخیر"""
        key = f"{self.settings.trades_key_prefix}stream:{token_address}"
        
        # Get most recent trades
        results = await self.zrange(key, -limit, -1, with_scores=True)
        
        trades = []
        for item in results:
            try:
                trade_data = json.loads(item['value'])
                trade_data['timestamp'] = item['score']
                trades.append(trade_data)
            except json.JSONDecodeError:
                continue
        
        return list(reversed(trades))  # Most recent first
    
    async def cleanup_old_data(self, hours: int = 24) -> None:
        """پاک کردن داده‌های قدیمی"""
        cutoff_time = asyncio.get_event_loop().time() - (hours * 3600)
        
        # Clean up trade streams
        trade_keys = await self.keys(f"{self.settings.trades_key_prefix}stream:*")
        
        cleaned_count = 0
        for key in trade_keys:
            removed = await self.zremrangebyscore(key, 0, cutoff_time)
            cleaned_count += removed
        
        logger.info(f"🧹 Cleaned up {cleaned_count} old trade records")
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت Redis"""
        try:
            await self._ensure_connection()
            
            # Test basic operations
            test_key = "health_check_test"
            await self.set(test_key, "test_value", ttl=10)
            value = await self.get(test_key)
            await self.delete(test_key)
            
            # Get info
            info = await self._pool.info()
            
            return {
                'status': 'healthy',
                'connected': self._is_connected,
                'test_successful': value == "test_value",
                'redis_version': info.get('redis_version', 'unknown'),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }

    # Stream operations for real-time event processing
    async def xadd(self, stream: str, fields: Dict[str, Any], message_id: str = "*", max_len: Optional[int] = None) -> str:
        """Add message to Redis Stream"""
        await self._ensure_connection()
        
        try:
            # Convert all values to strings for Redis
            string_fields = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in fields.items()}
            
            result = await self._pool.xadd(
                stream, 
                string_fields, 
                id=message_id,
                maxlen=max_len,
                approximate=max_len is not None
            )
            
            logger.debug(f"Added message to stream {stream}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding to stream {stream}: {e}")
            raise

    async def send_event_to_stream(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Send blockchain event to Redis Stream for real-time processing"""
        stream_name = "blockchain:events"
        
        message_fields = {
            'event_type': event_type,
            'data': json.dumps(event_data, default=str),  # JSON encode the event data
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'blockchain_listener'
        }
        
        try:
            message_id = await self.xadd(
                stream_name, 
                message_fields,
                max_len=10000  # Keep last 10k events
            )
            
            logger.info(
                f"📡 Event sent to stream: {stream_name} | {event_type} | {message_id} | token: {event_data.get('token_address', 'unknown')}"
            )
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send event to stream: {e}")
            raise
