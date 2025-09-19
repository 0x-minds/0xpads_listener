"""
🚀 Main Entry Point
Blockchain Listener Service
"""
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional
from loguru import logger

from .config.settings import get_settings
from .infrastructure.redis.redis_service import RedisService
from .infrastructure.websocket.websocket_service import WebSocketService, MockWebSocketService
from .infrastructure.blockchain.blockchain_service import BlockchainService
from .infrastructure.logging.logger_config import setup_logging
from .application.use_cases import ProcessTradeEventUseCase, GetChartDataUseCase, ManageBondingCurvesUseCase
from .application.services.chart_service import ChartService
from .application.services.alert_service import AlertService
from .infrastructure.repositories.redis_repositories import (
    RedisTradeRepository, RedisCandleRepository, RedisBondingCurveRepository, 
    RedisMarketDataRepository
)


class BlockchainListener:
    """🎧 Main Blockchain Listener Service"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Infrastructure services
        self.redis_service: Optional[RedisService] = None
        self.websocket_service: Optional[WebSocketService] = None
        self.blockchain_service: Optional[BlockchainService] = None
        
        # Repositories
        self.trade_repo: Optional[RedisTradeRepository] = None
        self.candle_repo: Optional[RedisCandleRepository] = None
        self.curve_repo: Optional[RedisBondingCurveRepository] = None
        self.market_data_repo: Optional[RedisMarketDataRepository] = None
        
        # Application services
        self.chart_service: Optional[ChartService] = None
        self.alert_service: Optional[AlertService] = None
        
        # Use cases
        self.process_trade_use_case: Optional[ProcessTradeEventUseCase] = None
        self.get_chart_data_use_case: Optional[GetChartDataUseCase] = None
        self.manage_curves_use_case: Optional[ManageBondingCurvesUseCase] = None
        
        # Control flags
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info("🎧 BlockchainListener initialized")
    
    async def initialize(self) -> None:
        """🔧 Initialize all services and dependencies"""
        logger.info("🔧 Initializing blockchain listener...")
        
        try:
            # 1. Initialize Redis service
            await self._initialize_redis()
            
            # 2. Initialize WebSocket service  
            await self._initialize_websocket()
            
            # 3. Initialize blockchain service
            await self._initialize_blockchain()
            
            # 4. Initialize repositories
            await self._initialize_repositories()
            
            # 5. Initialize application services
            await self._initialize_application_services()
            
            # 6. Initialize use cases
            await self._initialize_use_cases()
            
            logger.info("✅ All services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis service"""
        logger.info("🔴 Initializing Redis service...")
        
        self.redis_service = RedisService(self.settings)
        await self.redis_service.connect()
        
        # Test Redis connection
        health = await self.redis_service.health_check()
        if health['status'] != 'healthy':
            raise Exception(f"Redis health check failed: {health}")
        
        logger.info("✅ Redis service initialized")
    
    async def _initialize_websocket(self) -> None:
        """Initialize WebSocket service"""
        logger.info("🔗 Initializing WebSocket service...")
        
        if self.settings.environment == 'development':
            # Use mock service for development
            self.websocket_service = MockWebSocketService()
            logger.info("🔧 Using Mock WebSocket service for development")
        else:
            self.websocket_service = WebSocketService(self.settings)
            await self.websocket_service.connect_to_backend()
        
        await self.websocket_service.start_server()
        
        logger.info("✅ WebSocket service initialized")
    
    async def _initialize_blockchain(self) -> None:
        """Initialize blockchain service"""
        logger.info("⛓️ Initializing blockchain service...")
        
        self.blockchain_service = BlockchainService(self.settings)
        await self.blockchain_service.connect()
        
        # Test blockchain connection
        health = await self.blockchain_service.health_check()
        if health['status'] != 'healthy':
            raise Exception(f"Blockchain health check failed: {health}")
        
        logger.info("✅ Blockchain service initialized")
    
    async def _initialize_repositories(self) -> None:
        """Initialize repositories"""
        logger.info("🗄️ Initializing repositories...")
        
        self.trade_repo = RedisTradeRepository(self.redis_service)
        self.candle_repo = RedisCandleRepository(self.redis_service)
        self.curve_repo = RedisBondingCurveRepository(self.redis_service)
        self.market_data_repo = RedisMarketDataRepository(self.redis_service)
        
        logger.info("✅ Repositories initialized")
    
    async def _initialize_application_services(self) -> None:
        """Initialize application services"""
        logger.info("🔧 Initializing application services...")
        
        self.chart_service = ChartService(
            self.candle_repo,
            self.market_data_repo,
            self.redis_service
        )
        
        self.alert_service = AlertService(
            self.redis_service,
            self.websocket_service
        )
        
        logger.info("✅ Application services initialized")
    
    async def _initialize_use_cases(self) -> None:
        """Initialize use cases"""
        logger.info("🎯 Initializing use cases...")
        
        self.process_trade_use_case = ProcessTradeEventUseCase(
            self.trade_repo,
            self.candle_repo,
            self.curve_repo,
            self.market_data_repo,
            self.redis_service,
            self.websocket_service,
            self.alert_service
        )
        
        self.get_chart_data_use_case = GetChartDataUseCase(
            self.candle_repo,
            self.market_data_repo,
            self.redis_service
        )
        
        self.manage_curves_use_case = ManageBondingCurvesUseCase(
            self.curve_repo,
            self.redis_service,
            self.websocket_service
        )
        
        logger.info("✅ Use cases initialized")
    
    async def start(self) -> None:
        """🚀 Start the blockchain listener"""
        logger.info("🚀 Starting blockchain listener...")
        
        self._running = True
        
        try:
            # Start main event processing loop
            await self._run_event_loop()
            
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _run_event_loop(self) -> None:
        """🔄 Main event processing loop"""
        logger.info("🔄 Starting main event processing loop...")
        
        # Create tasks
        tasks = [
            asyncio.create_task(self._process_blockchain_events(), name="blockchain_events"),
            asyncio.create_task(self._periodic_cleanup(), name="periodic_cleanup"),
            asyncio.create_task(self._health_monitor(), name="health_monitor"),
            asyncio.create_task(self._wait_for_shutdown(), name="shutdown_waiter")
        ]
        
        try:
            # Wait for first completed task
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check if any task failed
            for task in done:
                if task.exception():
                    logger.error(f"Task {task.get_name()} failed: {task.exception()}")
                    raise task.exception()
                    
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
            raise
    
    async def _process_blockchain_events(self) -> None:
        """🎯 Process blockchain events"""
        logger.info("🎯 Starting blockchain event processing...")
        
        try:
            async for event in self.blockchain_service.subscribe_to_events():
                if not self._running:
                    break
                
                try:
                    await self._handle_blockchain_event(event)
                except Exception as e:
                    logger.error(f"Error handling blockchain event: {e}")
                    # Continue processing other events
                    continue
                    
        except Exception as e:
            logger.error(f"Error in blockchain event processing: {e}")
            raise
    
    async def _handle_blockchain_event(self, event: dict) -> None:
        """🎪 Handle individual blockchain event"""
        event_type = event.get('event_type')
        
        try:
            if event_type == 'Trade':
                # Process trade event
                await self.process_trade_use_case.execute(event)
                logger.info(f"✅ Processed {event_type} event for {event.get('token_address', 'unknown')[:8]}...")
                
            elif event_type == 'BondingCurveDeployed':
                # Handle new bonding curve
                await self.manage_curves_use_case.add_new_curve(event)
                logger.info(f"✅ Added new bonding curve: {event.get('name', 'unknown')}")
                
            elif event_type in ['TokensPurchased', 'TokensSold']:
                # Convert to Trade event format and process
                trade_event = self._convert_to_trade_event(event)
                await self.process_trade_use_case.execute(trade_event)
                logger.info(f"✅ Processed {event_type} as trade event")
                
            else:
                logger.debug(f"Unhandled event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling {event_type} event: {e}")
            raise
    
    def _convert_to_trade_event(self, event: dict) -> dict:
        """Convert TokensPurchased/TokensSold to Trade event format"""
        event_type = event.get('event_type')
        
        if event_type == 'TokensPurchased':
            return {
                'event_type': 'Trade',
                'token_address': event['token_address'],
                'curve_address': event['curve_address'],
                'user_address': event['buyer'],
                'is_buy': True,
                'eth_amount': event['eth_spent'],
                'token_amount': event['tokens_received'],
                'price_before': '0',  # Would need to calculate
                'price_after': event['new_price'],
                'total_supply': '0',  # Would need to get from contract
                'timestamp': event.get('block_timestamp', 0),
                'block_number': event['block_number'],
                'block_timestamp': event['block_timestamp'],
                'block_hash': event['block_hash'],
                'tx_hash': event['tx_hash']
            }
        
        elif event_type == 'TokensSold':
            return {
                'event_type': 'Trade',
                'token_address': event['token_address'],
                'curve_address': event['curve_address'],
                'user_address': event['seller'],
                'is_buy': False,
                'eth_amount': event['eth_received'],
                'token_amount': event['token_amount'],
                'price_before': '0',  # Would need to calculate
                'price_after': event['new_price'],
                'total_supply': '0',  # Would need to get from contract
                'timestamp': event.get('block_timestamp', 0),
                'block_number': event['block_number'],
                'block_timestamp': event['block_timestamp'],
                'block_hash': event['block_hash'],
                'tx_hash': event['tx_hash']
            }
        
        return event
    
    async def _periodic_cleanup(self) -> None:
        """🧹 Periodic cleanup tasks"""
        logger.info("🧹 Starting periodic cleanup...")
        
        while self._running:
            try:
                # Cleanup old Redis data
                await self.redis_service.cleanup_old_data(hours=24)
                
                # Log system stats
                await self._log_system_stats()
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _health_monitor(self) -> None:
        """💗 Health monitoring"""
        logger.info("💗 Starting health monitor...")
        
        while self._running:
            try:
                # Check all services
                redis_health = await self.redis_service.health_check()
                blockchain_health = await self.blockchain_service.health_check()
                websocket_health = await self.websocket_service.health_check()
                
                # Log unhealthy services
                if redis_health['status'] != 'healthy':
                    logger.warning(f"⚠️ Redis unhealthy: {redis_health}")
                    
                if blockchain_health['status'] != 'healthy':
                    logger.warning(f"⚠️ Blockchain unhealthy: {blockchain_health}")
                    
                if websocket_health['status'] != 'healthy':
                    logger.warning(f"⚠️ WebSocket unhealthy: {websocket_health}")
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(10)
    
    async def _log_system_stats(self) -> None:
        """📊 Log system statistics"""
        try:
            redis_stats = await self.redis_service.health_check()
            blockchain_stats = await self.blockchain_service.get_connection_stats()
            websocket_stats = await self.websocket_service.get_connection_stats()
            
            logger.info("📊 System Stats:")
            logger.info(f"   Redis: {redis_stats.get('connected_clients', 0)} clients, {redis_stats.get('used_memory', 'unknown')} memory")
            logger.info(f"   Blockchain: Block {blockchain_stats.get('last_block_number', 0)}, {blockchain_stats.get('events_received', 0)} events")
            logger.info(f"   WebSocket: {websocket_stats.get('total_subscriptions', 0)} subscriptions, {websocket_stats.get('active_rooms', 0)} rooms")
            
        except Exception as e:
            logger.error(f"Error logging system stats: {e}")
    
    async def _wait_for_shutdown(self) -> None:
        """⏹️ Wait for shutdown signal"""
        await self._shutdown_event.wait()
        logger.info("🛑 Shutdown signal received")
    
    async def shutdown(self) -> None:
        """🛑 Graceful shutdown"""
        logger.info("🛑 Starting graceful shutdown...")
        
        self._running = False
        self._shutdown_event.set()
        
        await self._cleanup()
        
        logger.info("✅ Shutdown completed")
    
    async def _cleanup(self) -> None:
        """🧹 Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")
        
        try:
            # Stop services
            if self.websocket_service:
                await self.websocket_service.stop_server()
            
            if self.blockchain_service:
                await self.blockchain_service.disconnect()
            
            if self.redis_service:
                await self.redis_service.disconnect()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """🚀 Main entry point"""
    # Setup logging
    setup_logging()
    
    logger.info("🚀 Starting 0xPads Blockchain Listener")
    
    # Create listener instance
    listener = BlockchainListener()
    
    # Setup signal handlers
    def signal_handler():
        logger.info("📡 Received shutdown signal")
        asyncio.create_task(listener.shutdown())
    
    # Register signal handlers
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # Initialize and start
        await listener.initialize()
        await listener.start()
        
    except KeyboardInterrupt:
        logger.info("🔌 Keyboard interrupt received")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
        
    finally:
        await listener.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🔌 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        sys.exit(1)
