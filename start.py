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
from server.run import run_server, parse_args, configure_logging
from server.config import Settings

logger = logging.getLogger("kari")


def main():
    """Main entry point for the Kari server"""
    try:
        # Load settings first to ensure environment validation happens early
        settings = Settings()

        # Configure logging according to settings/environment
        configure_logging(settings.log_level)

        # Parse command line arguments with settings-aware defaults
        args = parse_args(settings=settings)

        # Create the FastAPI app using the factory to fail fast on startup issues
        _ = create_app()

        # Run the server
        run_server(args=args, settings=settings)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except ValueError as e:
        logger.error("Invalid startup configuration: %s", e)
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to start server: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
