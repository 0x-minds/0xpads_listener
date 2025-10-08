#!/usr/bin/env python3
"""
🚀 Startup Script
Quick startup script برای development
"""
import asyncio
import sys
from pathlib import Path
import sentry_sdk

# Initialize Sentry
sentry_sdk.init(
    dsn="https://45ad226ab6c373e24350f4aa8fbae72a@sentry.hamravesh.com/9137",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from listener.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔌 Application interrupted by user")
    except Exception as e:
        print(f"❌ Application failed: {e}")
        sys.exit(1)
