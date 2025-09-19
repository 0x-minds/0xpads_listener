# 🎧 0xPads Blockchain Listener

**Async blockchain event listener برای real-time trading data و candlestick charts**

یک سیستم کاملاً async و clean architecture که به blockchain متصل می‌شه، trade eventها رو پردازش می‌کنه و داده‌های OHLCV برای نمودارها تولید می‌کنه.

## ✨ Features

- 🔥 **Async Event Processing**: پردازش async چندتایی bonding curves
- 📊 **Real-time OHLCV Generation**: تولید candlestick data برای intervals مختلف
- 🔴 **Redis Caching**: cache کردن high-performance با Redis
- 🔗 **WebSocket Integration**: اتصال به Node.js backend
- 🏗️ **Clean Architecture**: Domain, Application, Infrastructure layers
- 📡 **Multi-Curve Support**: پشتیبانی از چندین bonding curve همزمان
- ⚡ **High Performance**: optimized برای high-frequency trading data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Blockchain    │───▶│  Event Listener │───▶│  OHLCV Processor│
│   (WebSocket)   │    │     (Async)     │    │     (Async)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Node.js       │◀───│  WebSocket      │◀───│  Redis Cache    │
│   Backend       │    │   Service       │    │   (Real-time)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📂 Project Structure

```
listener/
├── domain/              # Business logic
│   ├── entities.py      # Core entities (TradeEvent, OHLCVCandle, etc.)
│   ├── value_objects.py # Value objects (Price, Volume, TokenAddress)
│   └── events.py        # Domain events
├── application/         # Use cases & interfaces  
│   ├── interfaces.py    # Repository & service interfaces
│   ├── use_cases.py     # Business use cases
│   └── services/        # Application services
├── infrastructure/     # External services
│   ├── blockchain/     # Blockchain connection
│   ├── redis/          # Redis implementation
│   ├── websocket/      # WebSocket client
│   └── repositories/   # Data persistence
├── config/
│   └── settings.py     # Configuration management
└── main.py             # Entry point
```

## 🚀 Quick Start

### 1. تنظیم Environment

```bash
# Copy environment file
cp env.example .env

# Edit configuration
nano .env
```

### 2. نصب Dependencies

```bash
# Install with uv (recommended)
uv install

# Or with pip
pip install -r requirements.txt
```

### 3. تنظیم Redis

```bash
# Start Redis server
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. تنظیم Blockchain

```bash
# Start Hardhat node (for development)
npx hardhat node

# Deploy contracts
npx hardhat run scripts/deploy.js --network localhost
```

### 5. اجرا

```bash
# Development mode
uv run python -m listener.main

# Or with Python
python -m listener.main

# Production mode with env
ENV=production uv run python -m listener.main
```

## ⚙️ Configuration

تنظیمات در فایل `.env`:

```bash
# Blockchain
BLOCKCHAIN_WS_URL=ws://127.0.0.1:8545
BLOCKCHAIN_HTTP_URL=http://127.0.0.1:8545
CHAIN_ID=31337
BONDING_CURVE_FACTORY_ADDRESS=0x...

# Redis
REDIS_URL=redis://localhost:6379

# WebSocket (Node.js Backend)
WEBSOCKET_PORT=3001
BACKEND_SOCKET_URL=http://localhost:3000

# Processing
BATCH_SIZE=100
PROCESSING_INTERVAL_MS=1000
OHLCV_INTERVALS=1m,5m,15m,1h,4h,1d

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/listener.log
```

## 📊 Data Flow

### 1. Event Processing

```python
Blockchain Event → EventListener → ProcessTradeUseCase → [
    ├── Update OHLCV Candles (all intervals)
    ├── Update Market Data (24h stats)  
    ├── Cache Real-time Data (Redis)
    ├── Send WebSocket Updates
    ├── Check Alerts & Notifications
    └── Emit Domain Events
]
```

### 2. OHLCV Generation

```python
TradeEvent → OHLCVProcessor → [
    ├── 1m Candle Update
    ├── 5m Candle Update
    ├── 15m Candle Update
    ├── 1h Candle Update
    ├── 4h Candle Update
    └── 1d Candle Update
] → Redis Cache → WebSocket Broadcast
```

### 3. WebSocket Communication

```python
Python Listener ←→ Node.js Backend ←→ Frontend Clients
     │                      │                │
     ├─ Trade Updates       ├─ Chart Data    ├─ Subscribe to tokens
     ├─ Market Data         ├─ Real-time     ├─ Receive updates
     └─ Chart Data          └─ Broadcasts    └─ Display charts
```

## 🔧 Development

### Running Tests

```bash
# Unit tests
uv run pytest tests/

# Integration tests  
uv run pytest tests/integration/

# Coverage
uv run pytest --cov=listener tests/
```

### Code Quality

```bash
# Format code
uv run black listener/

# Lint code  
uv run flake8 listener/

# Type checking
uv run mypy listener/
```

## 📈 Performance

### Optimizations

- **Async Processing**: همه operations به صورت async
- **Batch Processing**: events در batch پردازش می‌شن
- **Redis Caching**: data های hot در Redis
- **Connection Pooling**: efficient database connections
- **Memory Management**: automatic cleanup برای old data

### Metrics

- **Events/Second**: 1000+ events پردازش
- **Latency**: <10ms برای event processing
- **Memory**: <512MB برای normal operation
- **CPU**: optimized برای multi-core systems

## 🛡️ Error Handling

### Resilience Features

- **Auto-Reconnection**: blockchain و Redis connections
- **Circuit Breaker**: protection از cascade failures
- **Graceful Degradation**: continue با reduced functionality
- **Health Checks**: monitoring system health
- **Retry Logic**: exponential backoff برای failed operations

## 📋 Monitoring

### Health Endpoints

```python
# Service health
await blockchain_service.health_check()
await redis_service.health_check()  
await websocket_service.health_check()

# System metrics
await get_system_metrics()
```

### Logs

```bash
# View logs
tail -f logs/listener.log

# Filter by level
grep "ERROR" logs/listener.log

# Real-time monitoring  
tail -f logs/listener.log | grep -E "(Trade|Candle|Error)"
```

## 🔄 Deployment

### Production Setup

```bash
# Build production image
docker build -t 0xpads-listener .

# Run with docker-compose
docker-compose up -d

# Scale instances
docker-compose up -d --scale listener=3
```

### Environment Variables

```bash
# Production settings
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export REDIS_URL=redis://prod-redis:6379
export BLOCKCHAIN_WS_URL=wss://mainnet.infura.io/ws/v3/YOUR_KEY
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`  
5. Open Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- 📧 Email: support@0xpads.com
- 💬 Discord: [0xPads Community](https://discord.gg/0xpads)
- 📖 Docs: [docs.0xpads.com](https://docs.0xpads.com)

---

**Built with ❤️ by the 0xPads team**
