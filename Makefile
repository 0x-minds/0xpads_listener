# 🎧 0xPads Blockchain Listener Makefile

.PHONY: help install dev test lint format clean run

# Default target
help:
	@echo "🎧 0xPads Blockchain Listener"
	@echo ""
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - 🎧 Run the blockchain listener (main command)"
	@echo "  dev        - Run in development mode" 
	@echo "  test       - Run tests"
	@echo "  lint       - Check code quality"
	@echo "  format     - Format code"
	@echo "  clean      - Clean cache and temp files"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	uv sync

# Development mode
dev:
	@echo "🚀 Starting development server..."
	uv run python run.py

# Run application
run:
	@echo "🚀 Starting blockchain listener..."
	uv run python start_listener.py

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

# Lint code
lint:
	@echo "🔍 Linting code..."
	uv run flake8 listener/ --max-line-length=100
	uv run mypy listener/ --ignore-missing-imports

# Format code
format:
	@echo "✨ Formatting code..."
	uv run black listener/ tests/
	uv run isort listener/ tests/

# Clean cache
clean:
	@echo "🧹 Cleaning cache..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/

# Health check
health:
	@echo "💗 Checking system health..."
	redis-cli ping || echo "⚠️ Redis not running"
	curl -s http://localhost:3000/health || echo "⚠️ Backend not running"

# Setup development environment
setup-dev:
	@echo "🔧 Setting up development environment..."
	cp env.example .env
	mkdir -p logs
	@echo "✅ Development environment ready!"
	@echo "📝 Don't forget to edit .env file!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t 0xpads-listener .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run --env-file .env 0xpads-listener

# Production deployment
deploy:
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d

# View logs
logs:
	@echo "📋 Viewing logs..."
	tail -f logs/listener.log

# Monitor system
monitor:
	@echo "📊 Monitoring system..."
	watch -n 5 'echo "=== Redis Stats ===" && redis-cli info stats | grep -E "(connected_clients|used_memory_human|total_commands_processed)" && echo "\n=== Logs ===" && tail -3 logs/listener.log'
