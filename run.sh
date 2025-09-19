#!/bin/bash
# 🎧 0xPads Blockchain Listener - Simple Runner

echo "🚀 Starting 0xPads Blockchain Listener..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "💡 Run 'make install' first to set up the environment"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found"
    echo "💡 Copying from env.example..."
    cp env.example .env
    echo "✅ Created .env file - please configure it with your settings"
fi

# Run the listener
echo "🎧 Launching listener..."
uv run python start_listener.py
