# mypy: ignore-errors
"""
Uvicorn runner for Kari FastAPI Server.
Handles CLI argument parsing and server startup with custom configuration.
"""

import argparse
import logging
import logging.config
import os
from typing import Optional

from .config import Settings
from .server_logging_filters import SuppressInvalidHTTPFilter

logger = logging.getLogger("kari")


def configure_logging(log_level: str) -> None:
    """Configure application logging before the server starts."""

    level = getattr(logging, log_level.upper(), logging.INFO)
    level_name = logging.getLevelName(level)

    # Reset existing handlers so repeated invocations (e.g. tests) reconfigure cleanly
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(lineno)d",
                "rename_fields": {"levelname": "severity", "asctime": "timestamp"},
            },
            "uvicorn_access": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(client_addr)s %(request_line)s %(status_code)s",
                "rename_fields": {"levelname": "severity", "asctime": "timestamp"},
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json",
            },
            "uvicorn_access": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "uvicorn_access",
            },
        },
        "loggers": {
            "kari": {"handlers": ["default"], "level": level_name, "propagate": False},
            "uvicorn": {"handlers": ["default"], "level": level_name, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": level_name, "propagate": False},
            "uvicorn.access": {"handlers": ["uvicorn_access"], "level": level_name, "propagate": False},
        },
        "root": {"handlers": ["default"], "level": level_name},
    }

    logging.config.dictConfig(logging_config)

    # Ensure key loggers inherit the configured level (dictConfig mutates them but be explicit)
    logger.setLevel(level)
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)


def _coerce_int(value: Optional[str], default: int) -> int:
    """Safely coerce string values to integers with a fallback."""

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid integer value '%s', falling back to %s", value, default)
        return default


def _coerce_bool(value: Optional[str], default: bool) -> bool:
    """Convert environment string flags to booleans."""

    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    logger.warning("Invalid boolean value '%s', falling back to %s", value, default)
    return default


def _validate_runtime_args(args: argparse.Namespace) -> argparse.Namespace:
    """Validate and normalize runtime arguments for safe server startup."""

    if not (0 < args.port < 65536):
        raise ValueError(f"Port must be between 1 and 65535, got {args.port}")

    if args.workers < 1:
        logger.warning("Workers must be >= 1, forcing to 1 (received %s)", args.workers)
        args.workers = 1

    if args.reload and args.workers != 1:
        logger.warning(
            "Reload mode is incompatible with multiple workers. Forcing workers to 1."
        )
        args.workers = 1

    if args.debug:
        args.log_level = "DEBUG"

    args.log_level = args.log_level.upper()

    return args


def parse_args(settings: Optional[Settings] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    settings = settings or Settings()

    parser = argparse.ArgumentParser(description="Kari AI Assistant Server")

    default_host = os.getenv("KARI_SERVER_HOST", "0.0.0.0")
    default_port = _coerce_int(os.getenv("KARI_SERVER_PORT"), 8000)
    default_workers = _coerce_int(os.getenv("KARI_SERVER_WORKERS"), 1)
    default_reload = _coerce_bool(os.getenv("KARI_SERVER_RELOAD"), False)
    default_debug = _coerce_bool(os.getenv("KARI_SERVER_DEBUG"), settings.debug)
    default_log_level = os.getenv("KARI_SERVER_LOG_LEVEL", settings.log_level).upper()

    parser.add_argument("--host", default=default_host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind to")

    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument("--reload", dest="reload", action="store_true", help="Enable auto-reload")
    reload_group.add_argument("--no-reload", dest="reload", action="store_false", help="Disable auto-reload")
    parser.set_defaults(reload=default_reload)

    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument("--debug", dest="debug", action="store_true", help="Enable debug mode")
    debug_group.add_argument("--no-debug", dest="debug", action="store_false", help="Disable debug mode")
    parser.set_defaults(debug=default_debug)

    parser.add_argument("--workers", type=int, default=default_workers, help="Number of workers")
    parser.add_argument(
        "--log-level",
        default=default_log_level,
        type=lambda value: value.upper(),
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Log level for server output",
    )

    args = parser.parse_args()
    return _validate_runtime_args(args)


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


def run_server(args: Optional[argparse.Namespace] = None, settings: Optional[Settings] = None):
    """Run the Kari server with uvicorn"""
    settings = settings or Settings()

    if args is None:
        args = parse_args(settings=settings)
    else:
        args = _validate_runtime_args(args)

    # Setup uvicorn logging filters
    setup_uvicorn_logging_filters()

    # Disable SSL for development
    ssl_context = None
    
    # Use standard uvicorn for now to avoid potential hanging issues
    logger.info(
        "🚀 Starting Kari AI server on %s:%s (workers=%s, reload=%s, log_level=%s)",
        args.host,
        args.port,
        args.workers,
        args.reload,
        args.log_level,
    )

    import uvicorn
    uvicorn.run(
        "server.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
        access_log=False,
    )


if __name__ == "__main__":
    run_server()