# mypy: ignore-errors
"""
Logging filters for Kari FastAPI Server.
Handles suppression of noisy HTTP warnings and invalid request logs.
"""

import logging


class SuppressInvalidHTTPFilter(logging.Filter):
    """Filter to suppress invalid HTTP request warnings from uvicorn"""
    
    def filter(self, record):
        """Filter out noisy HTTP warnings"""
        message = record.getMessage()
        
        # Suppress common invalid HTTP warnings
        suppress_patterns = [
            "Invalid HTTP request received",
            "Invalid request line",
            "Connection broken",
            "Connection lost",
            "Protocol error",
            "Invalid header",
            "Malformed request",
            "Connection closed by client",
            "Bad request syntax",
            "Request line too long",
            "Header line too long",
        ]
        
        for pattern in suppress_patterns:
            if pattern in message:
                return False
        
        return True


class SuppressNoiseFilter(logging.Filter):
    """Filter to suppress general noisy log messages"""
    
    def filter(self, record):
        """Filter out noisy log messages"""
        message = record.getMessage()
        
        # Suppress common noise patterns
        suppress_patterns = [
            "Connection attempt failed",
            "Retrying connection",
            "Temporary connection error",
            "Client disconnected",
            "WebSocket connection closed",
            "Heartbeat failed",
        ]
        
        for pattern in suppress_patterns:
            if pattern in message:
                return False
        
        return True