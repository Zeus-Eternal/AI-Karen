# mypy: ignore-errors
"""
Uvicorn runner for Kari FastAPI Server.
Handles CLI argument parsing and server startup with custom configuration.
"""

import argparse
import logging
import os
from .config import Settings
from .server_logging_filters import SuppressInvalidHTTPFilter

logger = logging.getLogger("kari")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Kari AI Assistant Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def setup_uvicorn_logging_filters():
    """Setup uvicorn logging filters to suppress invalid HTTP warnings"""
    
    # Apply the filter to all relevant uvicorn loggers immediately
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(SuppressInvalidHTTPFilter())
    uvicorn_error_logger.setLevel(logging.ERROR)  # Set to ERROR level to suppress warnings

    # Also apply to the root uvicorn logger to catch all messages
    uvicorn_root_logger = logging.getLogger("uvicorn")
    uvicorn_root_logger.addFilter(SuppressInvalidHTTPFilter())

    # Apply to any existing handlers on the uvicorn.error logger
    for handler in uvicorn_error_logger.handlers:
        handler.addFilter(SuppressInvalidHTTPFilter())

    # Set the uvicorn.protocols logger to ERROR level to suppress protocol warnings
    uvicorn_protocols_logger = logging.getLogger("uvicorn.protocols")
    uvicorn_protocols_logger.setLevel(logging.ERROR)

    # Set the uvicorn.protocols.http logger specifically
    uvicorn_http_logger = logging.getLogger("uvicorn.protocols.http")
    uvicorn_http_logger.setLevel(logging.ERROR)

    # Apply filter to all uvicorn-related loggers
    for logger_name in [
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
    ]:
        logger_obj = logging.getLogger(logger_name)
        logger_obj.addFilter(SuppressInvalidHTTPFilter())
        logger_obj.setLevel(logging.ERROR)

    # Completely disable the specific logger that generates "Invalid HTTP request received"
    logging.getLogger("uvicorn.protocols.http.h11_impl").disabled = True
    logging.getLogger("uvicorn.protocols.http.httptools_impl").disabled = True

    # Also try to suppress at the uvicorn.error level more aggressively
    uvicorn_error_logger.disabled = False  # Keep it enabled but filtered
    uvicorn_error_logger.propagate = False  # Don't propagate to parent loggers


def create_log_config():
    """Create custom log config to suppress uvicorn HTTP warnings"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "filters": {
            "suppress_invalid_http": {
                "()": SuppressInvalidHTTPFilter,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "filters": ["suppress_invalid_http"],
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }


def run_server(args=None):
    """Run the Kari server with uvicorn"""
    if args is None:
        args = parse_args()
    
    settings = Settings()
    
    # Setup uvicorn logging filters
    setup_uvicorn_logging_filters()
    
    # Disable SSL for development
    ssl_context = None
    
    # Use custom uvicorn server with enhanced protocol-level error handling
    from ai_karen_engine.server.custom_server import create_custom_server

    # Create custom server with enhanced protocol-level error handling using settings
    custom_server = create_custom_server(
        app="server.app:create_app",
        host=args.host,
        port=args.port,
        debug=args.debug,
        ssl_context=ssl_context,
        workers=args.workers,
        # Enhanced configuration for protocol-level error handling from settings
        max_invalid_requests_per_connection=settings.max_invalid_requests_per_connection,
        enable_protocol_error_handling=settings.enable_protocol_error_handling,
        log_invalid_requests=settings.log_invalid_requests,
        # Production-ready limits to prevent resource exhaustion
        limit_concurrency=200,
        limit_max_requests=10000,
        backlog=4096,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
        access_log=False,
        # Use httptools for better error handling
        http="httptools",
        loop="auto",
        server_header=False,
        date_header=False,
    )

    # Run the custom server
    logger.info("🚀 Starting Kari AI server with enhanced protocol-level error handling")
    custom_server.run()


if __name__ == "__main__":
    run_server()