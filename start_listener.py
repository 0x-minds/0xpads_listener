#!/usr/bin/env python3
"""
🎧 0xPads Blockchain Listener Runner
راه‌انداز ساده برای listener
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from listener.main import BlockchainListener
from listener.config.settings import get_settings
from loguru import logger


async def run_listener():
    """راه‌اندازی listener"""
    
    print("🚀 Starting 0xPads Blockchain Listener")
    print("=" * 60)
    
    # Check environment
    try:
        settings = get_settings()
        print(f"✅ Environment loaded")
        print(f"🏭 Factory Address: {settings.blockchain.factory_address}")
        print(f"🌐 Blockchain URL: {settings.blockchain.ws_url}")
        print(f"🔴 Redis URL: {settings.redis.url}")
        print()
    except Exception as e:
        print(f"❌ Environment error: {e}")
        print("💡 Make sure you have a .env file with proper settings")
        return
    
    # Initialize and start listener
    try:
        print("🔧 Initializing listener...")
        listener = BlockchainListener()
        await listener.initialize()
        
        print("✅ All services initialized!")
        print("🎧 Blockchain Listener is now RUNNING...")
        print("🔊 Monitoring for events...")
        print("💡 Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Run indefinitely
        await listener.start()
        
    except KeyboardInterrupt:
        print("\n⚠️ Stopping listener... (Ctrl+C pressed)")
    except Exception as e:
        print(f"\n❌ Listener error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🛑 Listener stopped")
        print("👋 Goodbye!")


def main():
    """Entry point"""
    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
