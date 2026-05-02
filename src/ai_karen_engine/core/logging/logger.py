from __future__ import annotations

import logging
from typing import Any

class RuntimeLogger(logging.Logger):
    """Kari Runtime Logger with structured event support."""

    def event(self, event_name: str, **kwargs: Any):
        """Log a structured event with the given name and metadata."""
        # Standardize metadata naming for events
        self.info(event_name, extra=kwargs)

def get_logger(name: str | None = None) -> RuntimeLogger:
    """Return a RuntimeLogger instance for the given name."""
    if name is None:
        name = "kari.runtime"
    
    # Ensure the logger class is registered
    original_class = logging.getLoggerClass()
    logging.setLoggerClass(RuntimeLogger)
    try:
        logger = logging.getLogger(name)
    finally:
        logging.setLoggerClass(original_class)
        
    return logger # type: ignore

def configure_runtime_logging():
    """Perform initial global logging configuration."""
    from .sinks import setup_sinks
    setup_sinks()

# Compatibility aliases
StructuredLogger = RuntimeLogger
get_structured_logger = get_logger
configure_logging = configure_runtime_logging
