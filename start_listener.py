import asyncio
import sys
from pathlib import Path
import sentry_sdk

# Initialize Sentry
sentry_sdk.init(
    dsn="https://ab02b3f44d6ec5f99e512d1694488a5f@o4509688918769664.ingest.de.sentry.io/4510137458557008",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from listener.main import BlockchainListener
from listener.config.settings import get_settings


async def run_listener():
    # Check environment
    try:
        settings = get_settings()
        print(f"🏭 Factory Address: {settings.blockchain.factory_address}")
        print(f"🌐 Blockchain URL: {settings.blockchain.ws_url}")
        print(f"🔴 Redis URL: {settings.redis.url}")
    except Exception as e:
        print(f"❌ Environment error: {e}")
        return
    
    # Initialize and start listener
    try:
        print("🔧 Initializing listener...")
        listener = BlockchainListener()
        await listener.initialize()
        
        # Run indefinitely
        await listener.start()
        
    except KeyboardInterrupt:
        print("\n⚠️ Stopping listener... (Ctrl+C pressed)")
    except Exception as e:
        print(f"\n❌ Listener error: {e}")
        import traceback
        traceback.print_exc()
    finally:
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
