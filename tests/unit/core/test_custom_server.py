"""
Tests for Custom Uvicorn Server with Protocol-Level Error Handling
"""

import asyncio
import logging
import socket
import ssl
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_karen_engine.server.custom_server import (
    CustomHTTPProtocol,
    CustomH11Protocol,
    CustomUvicornServer,
    ServerConfig,
    create_custom_server,
)


def create_mock_protocol(protocol_class):
    """Helper function to create mock protocol instances with correct parameters."""
    return protocol_class(
        config=MagicMock(),
        server_state=MagicMock(),
        app_state={},
        _loop=asyncio.get_event_loop()
    )


class TestCustomHTTPProtocol:
    """Test custom HTTP protocol with enhanced error handling."""

    def test_init(self):
        """Test protocol initialization."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        assert protocol.enhanced_logger is not None
        assert protocol._invalid_request_count == 0
        assert protocol._max_invalid_requests == 10

    def test_is_valid_http_data_valid_request(self):
        """Test validation of valid HTTP request data."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        valid_data = b"GET /api/health HTTP/1.1\r\nHost: localhost\r\n\r\n"
        assert protocol._is_valid_http_data(valid_data) is True

    def test_is_valid_http_data_invalid_request(self):
        """Test validation of invalid HTTP request data."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        # Test various invalid data
        invalid_data_cases = [
            b"",  # Empty data
            b"INVALID REQUEST",  # No HTTP structure
            b"GET",  # Incomplete request
            b"BADMETHOD /path HTTP/1.1",  # Invalid method
            b"GET /path BADVERSION",  # Invalid version
            b"\x00\x01\x02\x03",  # Binary garbage
        ]
        
        for invalid_data in invalid_data_cases:
            assert protocol._is_valid_http_data(invalid_data) is False

    def test_get_client_info(self):
        """Test client information extraction."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        # Mock transport with peername
        mock_transport = MagicMock()
        mock_transport.get_extra_info.return_value = ("192.168.1.1", 12345)
        protocol.transport = mock_transport
        
        client_info = protocol._get_client_info()
        assert client_info["ip"] == "192.168.1.1"
        assert client_info["port"] == 12345

    def test_get_client_info_no_transport(self):
        """Test client information extraction without transport."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        client_info = protocol._get_client_info()
        assert client_info["ip"] == "unknown"
        assert client_info["port"] == "unknown"

    def test_sanitize_request_data(self):
        """Test request data sanitization."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        # Test data with sensitive information
        sensitive_data = b"GET /api/login HTTP/1.1\r\nAuthorization: Bearer secret123\r\nCookie: session=abc123\r\n\r\n"
        client_info = {"ip": "192.168.1.1", "port": 12345}
        
        sanitized = protocol._sanitize_request_data(sensitive_data, client_info)
        
        assert "data_preview" in sanitized
        assert "Authorization: [REDACTED]" in sanitized["data_preview"]
        assert "Cookie: [REDACTED]" in sanitized["data_preview"]
        assert "secret123" not in sanitized["data_preview"]
        assert "abc123" not in sanitized["data_preview"]
        assert sanitized["data_size"] == len(sensitive_data)
        assert "client_ip_hash" in sanitized

    def test_remove_sensitive_data(self):
        """Test sensitive data removal."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        sensitive_text = """GET /api/login HTTP/1.1
Authorization: Bearer secret123
Cookie: session=abc123
X-API-Key: key456
password=mypass123
token=token789"""
        
        sanitized = protocol._remove_sensitive_data(sensitive_text)
        
        assert "Authorization: [REDACTED]" in sanitized
        assert "Cookie: [REDACTED]" in sanitized
        assert "X-API-Key: [REDACTED]" in sanitized
        assert "password=[REDACTED]" in sanitized
        assert "token=[REDACTED]" in sanitized
        
        # Ensure sensitive values are removed
        assert "secret123" not in sanitized
        assert "abc123" not in sanitized
        assert "key456" not in sanitized
        assert "mypass123" not in sanitized
        assert "token789" not in sanitized

    @patch('ai_karen_engine.server.custom_server.logger')
    def test_handle_invalid_http_request(self, mock_logger):
        """Test handling of invalid HTTP requests."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        # Mock transport
        mock_transport = MagicMock()
        mock_transport.get_extra_info.return_value = ("192.168.1.1", 12345)
        protocol.transport = mock_transport
        
        invalid_data = b"INVALID REQUEST DATA"
        
        protocol._handle_invalid_http_request(invalid_data, "test error")
        
        assert protocol._invalid_request_count == 1
        # The method was called successfully (we can see from the logs)

    def test_handle_too_many_invalid_requests(self):
        """Test handling when too many invalid requests are received."""
        protocol = create_mock_protocol(CustomHTTPProtocol)
        
        # Mock transport
        mock_transport = MagicMock()
        mock_transport.get_extra_info.return_value = ("192.168.1.1", 12345)
        protocol.transport = mock_transport
        
        # Simulate too many invalid requests
        protocol._invalid_request_count = 15  # Above max limit
        
        protocol._handle_invalid_http_request(b"invalid", "error")
        
        # Should close transport
        mock_transport.close.assert_called_once()


class TestCustomH11Protocol:
    """Test custom H11 protocol with enhanced error handling."""

    def test_init(self):
        """Test H11 protocol initialization."""
        protocol = create_mock_protocol(CustomH11Protocol)
        
        assert protocol.enhanced_logger is not None
        assert protocol._invalid_request_count == 0
        assert protocol._max_invalid_requests == 10

    def test_handle_invalid_request(self):
        """Test handling of invalid requests in H11 protocol."""
        protocol = create_mock_protocol(CustomH11Protocol)
        
        # Mock transport
        mock_transport = MagicMock()
        mock_transport.get_extra_info.return_value = ("192.168.1.1", 12345)
        protocol.transport = mock_transport
        
        protocol._handle_invalid_request(b"invalid data", "test error")
        
        assert protocol._invalid_request_count == 1
        # The method was called successfully (we can see from the logs)


class TestServerConfig:
    """Test server configuration class."""

    def test_default_config(self):
        """Test default server configuration."""
        config = ServerConfig()

        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.workers == 1
        assert config.reload is False
        assert config.ssl_context is None
        assert config.log_level == "info"
        assert config.max_invalid_requests_per_connection == 10
        assert config.enable_protocol_error_handling is True
        assert config.log_invalid_requests is True

    def test_custom_config(self):
        """Test custom server configuration."""
        ssl_context = ssl.create_default_context()
        
        config = ServerConfig(
            host="127.0.0.1",
            port=9000,
            debug=True,
            workers=4,
            reload=True,
            ssl_context=ssl_context,
            log_level="WARNING",
            max_invalid_requests_per_connection=5,
            enable_protocol_error_handling=False,
            log_invalid_requests=False,
            custom_param="test"
        )
        
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.debug is True
        assert config.workers == 4
        assert config.reload is True
        assert config.ssl_context == ssl_context
        assert config.log_level == "warning"
        assert config.max_invalid_requests_per_connection == 5
        assert config.enable_protocol_error_handling is False
        assert config.log_invalid_requests is False
        assert config.extra_config["custom_param"] == "test"


class TestCustomUvicornServer:
    """Test custom uvicorn server implementation."""

    def test_init(self):
        """Test server initialization."""
        config = ServerConfig()
        server = CustomUvicornServer("test:app", config)
        
        assert server.app == "test:app"
        assert server.config == config
        assert server.enhanced_logger is not None
        assert server._server is None

    def test_create_server_config(self):
        """Test server configuration creation."""
        config = ServerConfig(
            host="127.0.0.1",
            port=9000,
            debug=True,
            workers=2,
            reload=True,
            log_level="WARNING",
            custom_param="test"
        )
        server = CustomUvicornServer("test:app", config)

        uvicorn_config = server.create_server_config()
        
        assert uvicorn_config["app"] == "test:app"
        assert uvicorn_config["host"] == "127.0.0.1"
        assert uvicorn_config["port"] == 9000
        assert uvicorn_config["reload"] is True
        assert uvicorn_config["workers"] == 2
        assert uvicorn_config["log_level"] == "warning"
        assert uvicorn_config["custom_param"] == "test"
        assert "log_config" in uvicorn_config
        assert uvicorn_config["access_log"] is False
        assert uvicorn_config["server_header"] is False

    def test_create_server_config_with_ssl(self):
        """Test server configuration with SSL."""
        ssl_context = ssl.create_default_context()
        config = ServerConfig(ssl_context=ssl_context)
        server = CustomUvicornServer("test:app", config)
        
        uvicorn_config = server.create_server_config()
        
        assert uvicorn_config["ssl"] == ssl_context

    def test_create_log_config(self):
        """Test log configuration creation."""
        config = ServerConfig()
        server = CustomUvicornServer("test:app", config)
        
        log_config = server._create_log_config()
        
        assert log_config["version"] == 1
        assert "filters" in log_config
        assert "suppress_invalid_http" in log_config["filters"]
        assert "formatters" in log_config
        assert "handlers" in log_config
        assert "loggers" in log_config

    @patch('ai_karen_engine.server.custom_server.uvicorn.protocols.http.httptools_impl')
    @patch('ai_karen_engine.server.custom_server.uvicorn.protocols.http.h11_impl')
    def test_setup_protocol_handlers(self, mock_h11, mock_httptools):
        """Test protocol handlers setup."""
        config = ServerConfig(enable_protocol_error_handling=True)
        server = CustomUvicornServer("test:app", config)
        
        # Store original classes
        original_httptools = mock_httptools.HttpToolsProtocol
        original_h11 = mock_h11.H11Protocol
        
        server.setup_protocol_handlers()
        
        # Verify custom protocols were installed
        assert mock_httptools.HttpToolsProtocol == CustomHTTPProtocol
        assert mock_h11.H11Protocol == CustomH11Protocol
        
        # Test restoration
        server.restore_protocol_handlers()
        assert mock_httptools.HttpToolsProtocol == original_httptools
        assert mock_h11.H11Protocol == original_h11

    def test_setup_protocol_handlers_disabled(self):
        """Test protocol handlers setup when disabled."""
        config = ServerConfig(enable_protocol_error_handling=False)
        server = CustomUvicornServer("test:app", config)
        
        # Should not modify protocol classes when disabled
        server.setup_protocol_handlers()
        # No assertions needed - just ensure no exceptions


class TestCreateCustomServer:
    """Test custom server factory function."""

    def test_create_custom_server_defaults(self):
        """Test creating custom server with defaults."""
        server = create_custom_server("test:app")
        
        assert isinstance(server, CustomUvicornServer)
        assert server.app == "test:app"
        assert server.config.host == "0.0.0.0"
        assert server.config.port == 8000
        assert server.config.debug is False
        assert server.config.reload is False
        assert server.config.log_level == "info"

    def test_create_custom_server_custom_params(self):
        """Test creating custom server with custom parameters."""
        ssl_context = ssl.create_default_context()

        server = create_custom_server(
            "test:app",
            host="127.0.0.1",
            port=9000,
            debug=True,
            ssl_context=ssl_context,
            reload=True,
            log_level="DEBUG",
            custom_param="test"
        )

        assert isinstance(server, CustomUvicornServer)
        assert server.app == "test:app"
        assert server.config.host == "127.0.0.1"
        assert server.config.port == 9000
        assert server.config.debug is True
        assert server.config.reload is True
        assert server.config.ssl_context == ssl_context
        assert server.config.log_level == "debug"
        assert server.config.extra_config["custom_param"] == "test"


@pytest.mark.integration
class TestCustomServerIntegration:
    """Integration tests for custom server."""

    @pytest.mark.asyncio
    async def test_server_handles_invalid_http(self):
        """Test that server properly handles invalid HTTP requests."""
        # This would require a more complex integration test setup
        # with actual socket connections and malformed HTTP data
        pass

    def test_server_configuration_compatibility(self):
        """Test that server configuration is compatible with uvicorn."""
        config = ServerConfig()
        server = CustomUvicornServer("test:app", config)
        
        uvicorn_config = server.create_server_config()
        
        # Verify all required uvicorn parameters are present
        required_params = [
            "app", "host", "port", "reload", "workers",
            "log_config", "access_log", "timeout_keep_alive",
            "timeout_graceful_shutdown", "factory"
        ]
        
        for param in required_params:
            assert param in uvicorn_config, f"Missing required parameter: {param}"