"""
🔗 WebSocket Service Implementation
WebSocket client برای اتصال به Node.js backend
"""
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
import socketio
from loguru import logger

from ...application.interfaces import IWebSocketService
from ...config.settings import Settings


class WebSocketService(IWebSocketService):
    """WebSocket service برای ارتباط با Node.js backend"""
    
    def __init__(self, settings: Settings):
        self.settings = settings.websocket
        self._sio: Optional[socketio.AsyncClient] = None
        self._is_connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._rooms: Dict[str, List[str]] = {}  # room -> list of client_ids (در حال حاضر mock)
        
        # Stats
        self._messages_sent = 0
        self._messages_received = 0
    
    async def connect_to_backend(self) -> None:
        """اتصال به Node.js backend Socket.IO server"""
        try:
            logger.info(f"🔗 Connecting to backend Socket.IO: {self.settings.backend_socket_url}")
            
            self._sio = socketio.AsyncClient(
                reconnection=True,
                reconnection_attempts=self._max_reconnect_attempts,
                reconnection_delay=1,
                reconnection_delay_max=5,
                max_listeners=100
            )
            
            # Setup event handlers
            self._setup_backend_handlers()
            
            # Connect to backend
            await self._sio.connect(
                self.settings.backend_socket_url,
                namespaces=[self.settings.backend_namespace]
            )
            
            self._is_connected = True
            self._reconnect_attempts = 0
            
            logger.info("✅ Connected to backend Socket.IO server")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            self._is_connected = False
            await self._handle_reconnection()
    
    def _setup_backend_handlers(self) -> None:
        """Setup event handlers برای backend connection"""
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def connect():
            logger.info("🎉 Connected to backend Socket.IO")
            self._is_connected = True
            
            # Send identification
            await self._sio.emit('client_identify', {
                'type': 'blockchain_listener',
                'version': '1.0.0',
                'capabilities': ['trade_data', 'chart_data', 'market_data']
            }, namespace=self.settings.backend_namespace)
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def disconnect():
            logger.warning("🔌 Disconnected from backend Socket.IO")
            self._is_connected = False
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def connect_error(data):
            logger.error(f"❌ Connection error: {data}")
            self._is_connected = False
            await self._handle_reconnection()
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def message(data):
            """دریافت پیام از backend"""
            self._messages_received += 1
            logger.debug(f"📨 Received message from backend: {data.get('type', 'unknown')}")
            
            # Handle different message types
            await self._handle_backend_message(data)
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def subscribe_request(data):
            """درخواست subscribe از frontend clients"""
            logger.info(f"📡 Subscribe request: {data}")
            
            # Process subscription
            token_address = data.get('token_address')
            interval = data.get('interval', '1m')
            client_id = data.get('client_id')
            
            if token_address and client_id:
                room = f"token:{token_address}:{interval}"
                if room not in self._rooms:
                    self._rooms[room] = []
                if client_id not in self._rooms[room]:
                    self._rooms[room].append(client_id)
                
                logger.info(f"✅ Client {client_id[:8]}... subscribed to {room}")
        
        @self._sio.event(namespace=self.settings.backend_namespace)
        async def unsubscribe_request(data):
            """درخواست unsubscribe از frontend clients"""
            logger.info(f"📡 Unsubscribe request: {data}")
            
            token_address = data.get('token_address')
            interval = data.get('interval', '1m')
            client_id = data.get('client_id')
            
            if token_address and client_id:
                room = f"token:{token_address}:{interval}"
                if room in self._rooms and client_id in self._rooms[room]:
                    self._rooms[room].remove(client_id)
                    if not self._rooms[room]:
                        del self._rooms[room]
                
                logger.info(f"❌ Client {client_id[:8]}... unsubscribed from {room}")
    
    async def _handle_backend_message(self, data: Dict[str, Any]) -> None:
        """پردازش پیام‌های دریافتی از backend"""
        message_type = data.get('type')
        
        if message_type == 'ping':
            # Respond to ping
            await self.send_to_backend('pong', {'timestamp': data.get('timestamp')})
            
        elif message_type == 'chart_data_request':
            # Handle chart data request
            await self._handle_chart_data_request(data.get('data', {}))
            
        elif message_type == 'market_data_request':
            # Handle market data request  
            await self._handle_market_data_request(data.get('data', {}))
        
        # Call registered handlers
        if message_type in self._event_handlers:
            for handler in self._event_handlers[message_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {message_type}: {e}")
    
    async def _handle_chart_data_request(self, request_data: Dict[str, Any]) -> None:
        """پردازش درخواست chart data"""
        logger.info(f"📊 Chart data request: {request_data}")
        # اینجا باید از use case مربوطه استفاده کنیم
        # فعلاً placeholder
        pass
    
    async def _handle_market_data_request(self, request_data: Dict[str, Any]) -> None:
        """پردازش درخواست market data"""
        logger.info(f"💹 Market data request: {request_data}")
        # اینجا باید از use case مربوطه استفاده کنیم
        # فعلاً placeholder
        pass
    
    async def send_to_backend(self, event: str, data: Dict[str, Any]) -> None:
        """ارسال data به backend"""
        if not self._is_connected or not self._sio:
            logger.warning("⚠️ Cannot send to backend: not connected")
            return
        
        try:
            await self._sio.emit(
                event,
                data,
                namespace=self.settings.backend_namespace
            )
            
            self._messages_sent += 1
            logger.debug(f"📤 Sent {event} to backend: {len(str(data))} chars")
            
        except Exception as e:
            logger.error(f"Error sending {event} to backend: {e}")
            self._is_connected = False
            await self._handle_reconnection()
    
    async def broadcast_to_frontend(self, message: Dict[str, Any]) -> None:
        """Broadcast پیام به frontend clients (از طریق backend)"""
        await self.send_to_backend('broadcast', {
            'type': 'broadcast',
            'data': message
        })
    
    async def send_to_room(self, room: str, message: Dict[str, Any]) -> None:
        """ارسال پیام به room مشخص"""
        if room in self._rooms and self._rooms[room]:
            await self.send_to_backend('room_message', {
                'room': room,
                'data': message,
                'client_count': len(self._rooms[room])
            })
            
            logger.debug(f"📤 Sent to room {room}: {len(self._rooms[room])} clients")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast عمومی"""
        await self.broadcast_to_frontend(message)
    
    async def get_active_connections(self) -> int:
        """تعداد اتصالات فعال"""
        total_connections = sum(len(clients) for clients in self._rooms.values())
        return total_connections
    
    # Event handler registration
    def on(self, event: str, handler: Callable) -> None:
        """Register event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """Unregister event handler"""
        if event in self._event_handlers:
            try:
                self._event_handlers[event].remove(handler)
            except ValueError:
                pass
    
    # Connection management
    async def _handle_reconnection(self) -> None:
        """مدیریت reconnection"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("❌ Max reconnection attempts reached. Giving up.")
            return
        
        self._reconnect_attempts += 1
        delay = min(2 ** self._reconnect_attempts, 30)  # Exponential backoff, max 30s
        
        logger.warning(f"🔄 Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts} in {delay}s")
        
        await asyncio.sleep(delay)
        
        try:
            await self.connect_to_backend()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
    
    async def disconnect(self) -> None:
        """قطع اتصال"""
        try:
            if self._sio and self._is_connected:
                await self._sio.disconnect()
            self._is_connected = False
            logger.info("🔌 WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    # Stats and monitoring
    async def get_connection_stats(self) -> Dict[str, Any]:
        """آمار اتصال"""
        return {
            'is_connected': self._is_connected,
            'reconnect_attempts': self._reconnect_attempts,
            'messages_sent': self._messages_sent,
            'messages_received': self._messages_received,
            'active_rooms': len(self._rooms),
            'total_subscriptions': sum(len(clients) for clients in self._rooms.values()),
            'rooms': {
                room: len(clients) 
                for room, clients in self._rooms.items()
            }
        }
    
    async def get_room_info(self, room: str) -> Dict[str, Any]:
        """اطلاعات room"""
        if room in self._rooms:
            return {
                'room': room,
                'client_count': len(self._rooms[room]),
                'clients': self._rooms[room][:5]  # First 5 clients for privacy
            }
        return {'room': room, 'client_count': 0, 'clients': []}
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت WebSocket"""
        try:
            if self._is_connected and self._sio:
                # Send ping to backend
                start_time = asyncio.get_event_loop().time()
                await self.send_to_backend('ping', {'timestamp': start_time})
                
                return {
                    'status': 'healthy',
                    'connected': self._is_connected,
                    'backend_url': self.settings.backend_socket_url,
                    'namespace': self.settings.backend_namespace,
                    'reconnect_attempts': self._reconnect_attempts,
                    'messages_sent': self._messages_sent,
                    'messages_received': self._messages_received
                }
            else:
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'reconnect_attempts': self._reconnect_attempts
                }
                
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
    
    # Mock implementations for interface compliance
    async def start_server(self) -> None:
        """شروع WebSocket server (mock - ما client هستیم)"""
        await self.connect_to_backend()
    
    async def stop_server(self) -> None:
        """توقف WebSocket server (mock)"""
        await self.disconnect()


class MockWebSocketService(IWebSocketService):
    """Mock WebSocket service برای testing"""
    
    def __init__(self):
        self._is_connected = True
        self._rooms: Dict[str, List[str]] = {}
        self._messages: List[Dict[str, Any]] = []
    
    async def start_server(self) -> None:
        logger.info("🔧 Mock WebSocket server started")
    
    async def stop_server(self) -> None:
        logger.info("🔧 Mock WebSocket server stopped")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        self._messages.append({'type': 'broadcast', 'message': message})
        logger.info(f"🔧 Mock broadcast: {message.get('type', 'unknown')}")
    
    async def send_to_room(self, room: str, message: Dict[str, Any]) -> None:
        self._messages.append({'type': 'room', 'room': room, 'message': message})
        logger.info(f"🔧 Mock send to room {room}: {message.get('type', 'unknown')}")
    
    async def connect_to_backend(self) -> None:
        logger.info("🔧 Mock backend connection")
    
    async def send_to_backend(self, event: str, data: Dict[str, Any]) -> None:
        self._messages.append({'type': 'backend', 'event': event, 'data': data})
        logger.info(f"🔧 Mock send to backend {event}")
    
    async def get_active_connections(self) -> int:
        return 0
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """دریافت پیام‌های mock شده"""
        return self._messages.copy()
    
    def clear_messages(self) -> None:
        """پاک کردن پیام‌های mock"""
        self._messages.clear()
