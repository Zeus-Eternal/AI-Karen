#!/usr/bin/env python3
# mypy: ignore-errors
"""
Root entrypoint for Kari AI Assistant Server.
This is the new modular entry point that replaces main.py.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the modular server components
from server.app import create_app
from server.run import run_server, parse_args
from server.config import Settings

logger = logging.getLogger("kari")


def main():
    """Main entry point for the Kari server"""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Create the FastAPI app using the factory
        app = create_app()
        
        # Run the server
        run_server(args)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()