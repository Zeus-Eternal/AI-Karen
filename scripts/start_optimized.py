#!/usr/bin/env python3
"""
Optimized startup script for AI-Karen with lazy loading and resource management.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load optimized environment variables
def load_optimized_env():
    """Load optimized environment variables."""
    env_file = project_root / ".env.optimized"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("🚀 Loaded optimized environment configuration")

# Load optimized settings
load_optimized_env()

# Import the modular server components
from server.app import create_app
from server.run import run_server, parse_args

logger = logging.getLogger("kari")


def main():
    """Main entry point for the optimized Kari server"""
    try:
        print("⚡ Starting AI-Karen in optimized mode")
        print("🔧 Resource optimization: ENABLED")
        print("💡 Lazy loading: ENABLED") 
        print("🎯 Essential services only: ENABLED")
        print("🧹 Automatic cleanup: ENABLED")
        print("")
        
        # Parse command line arguments
        args = parse_args()
        
        # Override with optimized defaults
        if not hasattr(args, 'host') or args.host == "0.0.0.0":
            args.host = "0.0.0.0"
        if not hasattr(args, 'port') or args.port == 8000:
            args.port = args.port or 8000
            
        print(f"🌐 Server will start on {args.host}:{args.port}")
        print("⏱️  Expected startup time: <5 seconds")
        print("📊 Memory usage should be <50% of normal")
        print("")
        
        # Create the FastAPI app using the factory
        app = create_app()
        
        # Run the server
        run_server(args)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start optimized server: {e}")
        print(f"\n💡 Tip: Check logs/performance.log for details")
        print(f"🔧 Try: KARI_ULTRA_MINIMAL=true for even lighter startup")
        sys.exit(1)


if __name__ == "__main__":
    main()
