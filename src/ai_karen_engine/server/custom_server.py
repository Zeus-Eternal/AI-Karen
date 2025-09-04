"""
Custom Uvicorn Server Configuration with Protocol-Level Error Handling

This module provides enhanced uvicorn server configuration that handles
malformed HTTP requests at the protocol level, preventing them from
generating warning logs and ensuring proper error responses.
"""

import asyncio
import logging
import socket
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union

import uvicorn
from uvicorn.config import Config
from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol
from uvicorn.protocols.http.h11_impl import H11Protocol
from uvicorn.server import Server

from ai_karen_engine.server.enhanced_logger import EnhancedLogger, LoggingConfig

logger = logging.getLogger(__name__)


class CustomHTTPProtocol(HttpToolsProtocol):
    """Custom HTTP protocol that handles invalid requests gracefully."""
    
    def __init__(self, config, server_state, app_state, _loop=None):
        super().__init__(config, server_state, app_state, _loop)
        self.enhanced_logger = EnhancedLogger(LoggingConfig())
        self._invalid_request_count = 0
        self._max_invalid_requests = 10  # Rate limit invalid requests per connection
    
    def connection_made(self, transport):
        """Override connection_made to add custom error handling."""
        try:
            super().connection_made(transport)
        except Exception as e:
            self._handle_protocol_error("connection_setup", str(e))
            transport.close()
    
    def data_received(self, data: bytes) -> None:
        """Override data_received to handle malformed HTTP data."""
        try:
            # Check for obviously malformed data before processing
            if not self._is_valid_http_data(data):
                self._handle_invalid_http_request(data)
                return
            
            super().data_received(data)
            
        except (UnicodeDecodeError, ValueError, ConnectionError) as e:
            self._handle_invalid_http_request(data, str(e))
        except Exception as e:
            # Log unexpected errors but don't crash the server
            logger.error(f"Unexpected error in data_received: {e}", exc_info=True)
            self._handle_protocol_error("data_processing", str(e))
    
    def _is_valid_http_data(self, data: bytes) -> bool:
        """Basic validation of HTTP request data."""
        if not data:
            return False
        
        try:
            # Check for null bytes or other control characters that shouldn't be in HTTP
            if b'\x00' in data or any(b in data for b in [b'\x01', b'\x02', b'\x03', b'\x04']):
                return False
            
            # Try to decode as UTF-8 - HTTP should be ASCII/UTF-8
            try:
                data_str = data.decode('utf-8')[:100]  # Check first 100 chars
            except UnicodeDecodeError:
                # If it can't be decoded as UTF-8, it's likely not valid HTTP
                return False
            
            # Valid HTTP methods
            valid_methods = {
                'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'
            }
            
            # Check if it starts with a valid method
            first_word = data_str.split(' ')[0].upper()
            if first_word not in valid_methods:
                return False
            
            # Check for basic HTTP structure (method + space + path + space + version)
            parts = data_str.split(' ', 2)
            if len(parts) < 3:
                return False
            
            # Check for HTTP version
            version_part = parts[2].split('\r\n')[0]  # Get version before any headers
            if not version_part.startswith('HTTP/'):
                return False
            
            # Validate HTTP version format (HTTP/1.0, HTTP/1.1, HTTP/2.0, etc.)
            version = version_part[5:]  # Remove "HTTP/"
            if not version or '.' not in version:
                return False
            
            # Check that version parts are numeric
            try:
                major, minor = version.split('.', 1)
                int(major)
                int(minor.split()[0])  # Handle cases like "1.1 " with trailing space
            except (ValueError, IndexError):
                return False
            
            return True
            
        except (IndexError, AttributeError):
            return False
    
    def _handle_invalid_http_request(self, data: bytes, error: Optional[str] = None) -> None:
        """Handle invalid HTTP requests at protocol level."""
        self._invalid_request_count += 1
        
        # Rate limit invalid requests per connection
        if self._invalid_request_count > self._max_invalid_requests:
            logger.warning("Too many invalid requests from connection, closing")
            self.transport.close()
            return
        
        # Get client info safely
        client_info = self._get_client_info()
        
        # Log the invalid request with sanitized data
        sanitized_data = self._sanitize_request_data(data, client_info)
        
        self.enhanced_logger.log_invalid_request(
            sanitized_data,
            error_type="malformed_http_protocol"
        )
        
        # Send appropriate HTTP error response
        self._send_error_response(400, "Bad Request")
    
    def _handle_protocol_error(self, error_type: str, error_message: str) -> None:
        """Handle protocol-level errors."""
        client_info = self._get_client_info()
        
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "client_info": client_info,
            "timestamp": self.enhanced_logger._get_timestamp()
        }
        
        self.enhanced_logger.log_security_event({
            "event_type": "protocol_error",
            "threat_level": "medium",
            "details": error_data
        })
        
        # Close the connection for protocol errors
        if hasattr(self, 'transport') and self.transport:
            self.transport.close()
    
    def _get_client_info(self) -> Dict[str, Any]:
        """Safely get client connection information."""
        client_info = {"ip": "unknown", "port": "unknown"}
        
        try:
            if hasattr(self, 'transport') and self.transport:
                peername = self.transport.get_extra_info('peername')
                if peername:
                    client_info["ip"] = peername[0]
                    client_info["port"] = peername[1]
        except Exception:
            pass  # Use defaults
        
        return client_info
    
    def _sanitize_request_data(self, data: bytes, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize request data for safe logging."""
        try:
            # Limit data size for logging
            max_log_size = 500
            data_preview = data[:max_log_size]
            
            # Try to decode as UTF-8, replace invalid chars
            try:
                data_str = data_preview.decode('utf-8', errors='replace')
            except Exception:
                data_str = str(data_preview)
            
            # Remove potentially sensitive information
            sanitized_str = self._remove_sensitive_data(data_str)
            
            return {
                "data_preview": sanitized_str,
                "data_size": len(data),
                "client_ip_hash": self.enhanced_logger.sanitizer.hash_ip_address(client_info.get("ip", "unknown")),
                "client_port": client_info.get("port", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sanitizing request data: {e}")
            return {
                "error": "failed_to_sanitize",
                "data_size": len(data) if data else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _remove_sensitive_data(self, data_str: str) -> str:
        """Remove potentially sensitive information from request data."""
        import re
        
        # Remove common sensitive patterns
        patterns = [
            (r'Authorization:\s*[^\r\n]+', 'Authorization: [REDACTED]'),
            (r'Cookie:\s*[^\r\n]+', 'Cookie: [REDACTED]'),
            (r'X-API-Key:\s*[^\r\n]+', 'X-API-Key: [REDACTED]'),
            (r'password["\']?\s*[:=]\s*["\']?[^\s"\'&]+', 'password=[REDACTED]'),
            (r'token["\']?\s*[:=]\s*["\']?[^\s"\'&]+', 'token=[REDACTED]'),
        ]
        
        sanitized = data_str
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _send_error_response(self, status_code: int, reason_phrase: str) -> None:
        """Send HTTP error response for invalid requests."""
        try:
            response = (
                f"HTTP/1.1 {status_code} {reason_phrase}\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(reason_phrase)}\r\n"
                f"Connection: close\r\n"
                f"Server: Kari-AI\r\n"
                f"\r\n"
                f"{reason_phrase}"
            ).encode('utf-8')
            
            if hasattr(self, 'transport') and self.transport:
                self.transport.write(response)
                # Close connection after sending error
                self.transport.close()
                
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
            # Force close connection if response fails
            if hasattr(self, 'transport') and self.transport:
                self.transport.close()


class CustomH11Protocol(H11Protocol):
    """Custom H11 protocol with enhanced error handling."""
    
    def __init__(self, config, server_state, app_state, _loop=None):
        super().__init__(config, server_state, app_state, _loop)
        self.enhanced_logger = EnhancedLogger(LoggingConfig())
        self._invalid_request_count = 0
        self._max_invalid_requests = 10
    
    def data_received(self, data: bytes) -> None:
        """Override data_received to handle malformed HTTP data."""
        try:
            super().data_received(data)
        except Exception as e:
            self._handle_invalid_request(data, str(e))
    
    def _handle_invalid_request(self, data: bytes, error: str) -> None:
        """Handle invalid requests in H11 protocol."""
        self._invalid_request_count += 1
        
        if self._invalid_request_count > self._max_invalid_requests:
            logger.warning("Too many invalid requests from H11 connection, closing")
            if hasattr(self, 'transport') and self.transport:
                self.transport.close()
            return
        
        # Log the invalid request
        client_info = self._get_client_info()
        sanitized_data = {
            "protocol": "h11",
            "error": error,
            "data_size": len(data) if data else 0,
            "client_ip_hash": self.enhanced_logger.sanitizer.hash_ip_address(client_info.get("ip", "unknown")),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.enhanced_logger.log_invalid_request(
            sanitized_data,
            error_type="malformed_http_h11"
        )
    
    def _get_client_info(self) -> Dict[str, Any]:
        """Safely get client connection information."""
        client_info = {"ip": "unknown", "port": "unknown"}
        
        try:
            if hasattr(self, 'transport') and self.transport:
                peername = self.transport.get_extra_info('peername')
                if peername:
                    client_info["ip"] = peername[0]
                    client_info["port"] = peername[1]
        except Exception:
            pass
        
        return client_info


class ServerConfig:
    """Configuration class for custom uvicorn server."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        debug: bool = False,
        workers: int = 1,
        ssl_context: Optional[ssl.SSLContext] = None,
        max_invalid_requests_per_connection: int = 10,
        enable_protocol_error_handling: bool = True,
        log_invalid_requests: bool = True,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.debug = debug
        self.workers = workers
        self.ssl_context = ssl_context
        self.max_invalid_requests_per_connection = max_invalid_requests_per_connection
        self.enable_protocol_error_handling = enable_protocol_error_handling
        self.log_invalid_requests = log_invalid_requests
        self.extra_config = kwargs


class CustomUvicornServer:
    """Custom Uvicorn server with enhanced protocol-level error handling."""
    
    def __init__(self, app: str, config: ServerConfig):
        self.app = app
        self.config = config
        self.enhanced_logger = EnhancedLogger(LoggingConfig())
        self._server: Optional[Server] = None
    
    def create_server_config(self) -> Dict[str, Any]:
        """Create uvicorn configuration with custom error handling."""
        # Configure custom logging to suppress invalid HTTP warnings
        log_config = self._create_log_config()
        
        # Base uvicorn configuration
        uvicorn_config = {
            "app": self.app,
            "host": self.config.host,
            "port": self.config.port,
            "reload": self.config.debug,
            "workers": self.config.workers,
            "log_config": log_config,
            "access_log": False,  # We handle access logging in middleware
            "timeout_keep_alive": 30,
            "timeout_graceful_shutdown": 30,
            "factory": True,
            "server_header": False,  # Reduce attack surface
            "date_header": False,   # Performance optimization
            "limit_concurrency": 200,
            "limit_max_requests": 10000,
            "backlog": 4096,
        }
        
        # Add SSL configuration if provided
        if self.config.ssl_context:
            uvicorn_config["ssl"] = self.config.ssl_context
        
        # Configure HTTP implementation with custom protocols
        if self.config.enable_protocol_error_handling:
            uvicorn_config["http"] = "httptools"  # Use httptools for better performance
            uvicorn_config["loop"] = "auto"
        
        # Add any extra configuration
        uvicorn_config.update(self.config.extra_config)
        
        return uvicorn_config
    
    def _create_log_config(self) -> Dict[str, Any]:
        """Create logging configuration that handles invalid HTTP requests properly."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "suppress_invalid_http": {
                    "()": "ai_karen_engine.server.logging_filters.SuppressInvalidHTTPFilter",
                },
            },
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
                    "use_colors": None,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
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
                "uvicorn": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
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
    
    def setup_protocol_handlers(self) -> None:
        """Setup custom protocol handlers for invalid requests."""
        # Monkey patch the protocol classes to use our custom implementations
        if self.config.enable_protocol_error_handling:
            # Store original classes for potential restoration
            self._original_httptools_protocol = uvicorn.protocols.http.httptools_impl.HttpToolsProtocol
            self._original_h11_protocol = uvicorn.protocols.http.h11_impl.H11Protocol
            
            # Replace with our custom implementations
            uvicorn.protocols.http.httptools_impl.HttpToolsProtocol = CustomHTTPProtocol
            uvicorn.protocols.http.h11_impl.H11Protocol = CustomH11Protocol
            
            logger.info("Custom HTTP protocol handlers installed")
    
    def restore_protocol_handlers(self) -> None:
        """Restore original protocol handlers."""
        if hasattr(self, '_original_httptools_protocol'):
            uvicorn.protocols.http.httptools_impl.HttpToolsProtocol = self._original_httptools_protocol
        
        if hasattr(self, '_original_h11_protocol'):
            uvicorn.protocols.http.h11_impl.H11Protocol = self._original_h11_protocol
        
        logger.info("Original HTTP protocol handlers restored")
    
    async def start(self) -> None:
        """Start the custom uvicorn server."""
        try:
            # Setup custom protocol handlers
            self.setup_protocol_handlers()
            
            # Create uvicorn configuration
            config_dict = self.create_server_config()
            config = Config(**config_dict)
            
            # Create and start server
            self._server = Server(config)
            
            logger.info(f"Starting custom uvicorn server on {self.config.host}:{self.config.port}")
            await self._server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start custom uvicorn server: {e}", exc_info=True)
            raise
        finally:
            # Always restore original protocol handlers
            self.restore_protocol_handlers()
    
    def run(self) -> None:
        """Run the custom uvicorn server (blocking)."""
        try:
            # Setup custom protocol handlers
            self.setup_protocol_handlers()
            
            # Create uvicorn configuration
            config_dict = self.create_server_config()
            
            logger.info(f"Starting custom uvicorn server on {self.config.host}:{self.config.port}")
            uvicorn.run(**config_dict)
            
        except Exception as e:
            logger.error(f"Failed to run custom uvicorn server: {e}", exc_info=True)
            raise
        finally:
            # Always restore original protocol handlers
            self.restore_protocol_handlers()
    
    def stop(self) -> None:
        """Stop the server gracefully."""
        if self._server:
            self._server.should_exit = True
            logger.info("Custom uvicorn server stop requested")


def create_custom_server(
    app: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
    ssl_context: Optional[ssl.SSLContext] = None,
    **kwargs
) -> CustomUvicornServer:
    """Factory function to create a custom uvicorn server."""
    config = ServerConfig(
        host=host,
        port=port,
        debug=debug,
        ssl_context=ssl_context,
        **kwargs
    )
    
    return CustomUvicornServer(app, config)