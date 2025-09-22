"""
💰 Price Service
Fetches ETH/USDT price from exchange API and stores in Redis
"""
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger
from ...application.interfaces import ICacheService


class PriceService:
    """Service for fetching and managing cryptocurrency prices"""
    
    def __init__(self, cache_service: ICacheService):
        self.cache_service = cache_service
        self.session: Optional[aiohttp.ClientSession] = None
        self._running = False
        
        # Exchange API endpoint (using Binance public API)
        self.exchange_api_url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
        
        # Redis key for storing ETH/USDT price
        self.redis_key = "price:ETH:USDT"
        
        logger.info("💰 PriceService initialized")
    
    async def start(self) -> None:
        """Start the price fetching service"""
        logger.info("💰 Starting price fetching service...")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'Listener/1.0'}
        )
        
        self._running = True
        
        # Start price fetching task
        asyncio.create_task(self._price_fetching_loop())
        
        logger.info("✅ Price fetching service started")
    
    async def stop(self) -> None:
        """Stop the price fetching service"""
        logger.info("🛑 Stopping price fetching service...")
        
        self._running = False
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("✅ Price fetching service stopped")
    
    async def _price_fetching_loop(self) -> None:
        """Main loop for fetching prices every 2 seconds"""
        logger.info("🔄 Starting price fetching loop (2-second interval)...")
        
        while self._running:
            try:
                # Fetch ETH/USDT price
                price_data = await self._fetch_eth_usdt_price()
                
                if price_data:
                    await self._store_price_in_redis(price_data)
                
                # Wait 2 seconds before next fetch
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error in price fetching loop: {e}")
                # Wait 5 seconds before retry on error
                await asyncio.sleep(5)
    
    async def _fetch_eth_usdt_price(self) -> Optional[Dict[str, Any]]:
        """Fetch ETH/USDT price from Binance API"""
        try:
            if not self.session:
                logger.error("HTTP session not initialized")
                return None
            
            async with self.session.get(self.exchange_api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'symbol': data['symbol'],
                        'price': float(data['price']),
                        'timestamp': asyncio.get_event_loop().time(),
                        'source': 'binance'
                    }
                else:
                    logger.warning(f"⚠️ Exchange API returned status {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning("⚠️ Timeout fetching price from exchange")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching ETH/USDT price: {e}")
            return None
    
    async def _store_price_in_redis(self, price_data: Dict[str, Any]) -> None:
        """Store only the latest price data in Redis"""
        try:
            # Store only current price as JSON
            await self.cache_service.set_json(
                self.redis_key,
                price_data,
                ttl=10  # Expire after 10 seconds (5x fetch interval)
            )
            
        except Exception as e:
            logger.error(f"❌ Error storing price in Redis: {e}")
    
    async def get_current_price(self) -> Optional[Dict[str, Any]]:
        """Get current ETH/USDT price from Redis"""
        try:
            return await self.cache_service.get_json(self.redis_key)
        except Exception as e:
            logger.error(f"❌ Error getting current price: {e}")
            return None
    
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for price service"""
        try:
            current_price = await self.get_current_price()
            
            return {
                'status': 'healthy' if current_price else 'unhealthy',
                'running': self._running,
                'current_price': current_price,
                'last_update': current_price.get('timestamp') if current_price else None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'running': self._running
            }