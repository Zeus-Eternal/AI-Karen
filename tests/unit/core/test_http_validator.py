"""
Unit tests for HTTP Request Validation Framework
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi import Request
from starlette.datastructures import Headers, URL, QueryParams

from src.ai_karen_engine.server.http_validator import (
    HTTPRequestValidator,
    ValidationConfig,
    ValidationResult
)


class TestValidationConfig:
    """Test ValidationConfig data model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ValidationConfig()
        
        assert config.max_content_length == 10 * 1024 * 1024
        assert "GET" in config.allowed_methods
        assert "POST" in config.allowed_methods
        assert config.max_header_size == 8192
        assert config.max_headers_count == 100
        assert config.enable_security_analysis is True
        assert config.log_invalid_requests is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ValidationConfig(
            max_content_length=5 * 1024 * 1024,
            allowed_methods={"GET", "POST"},
            max_header_size=4096,
            enable_security_analysis=False
        )
        
        assert config.max_content_length == 5 * 1024 * 1024
        assert config.allowed_methods == {"GET", "POST"}
        assert config.max_header_size == 4096
        assert config.enable_security_analysis is False


class TestValidationResult:
    """Test ValidationResult data model."""
    
    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None
        assert result.security_threat_level == "none"
        assert result.should_rate_limit is False
    
    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            error_type="invalid_method",
            error_message="Method not allowed",
            security_threat_level="medium",
            should_rate_limit=True
        )
        
        assert result.is_valid is False
        assert result.error_type == "invalid_method"
        assert result.error_message == "Method not allowed"
        assert result.security_threat_level == "medium"
        assert result.should_rate_limit is True


class TestHTTPRequestValidator:
    """Test HTTPRequestValidator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = ValidationConfig()
        self.validator = HTTPRequestValidator(self.config)
    
    def create_mock_request(self, method="GET", path="/", headers=None, query_params=None):
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.method = method
        request.url = Mock(spec=URL)
        request.url.path = path
        request.url.query = "&".join([f"{k}={v}" for k, v in (query_params or {}).items()])
        request.headers = Headers(headers or {})
        request.query_params = QueryParams(query_params or {})
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = HTTPRequestValidator()
        assert validator.config is not None
        assert hasattr(validator, 'sql_injection_patterns')
        assert hasattr(validator, 'xss_patterns')
        assert hasattr(validator, 'path_traversal_patterns')
    
    def test_validator_with_custom_config(self):
        """Test validator with custom configuration."""
        custom_config = ValidationConfig(max_content_length=1024)
        validator = HTTPRequestValidator(custom_config)
        assert validator.config.max_content_length == 1024
    
    def test_is_valid_http_method_valid(self):
        """Test valid HTTP method validation."""
        assert self.validator.is_valid_http_method("GET") is True
        assert self.validator.is_valid_http_method("POST") is True
        assert self.validator.is_valid_http_method("PUT") is True
        assert self.validator.is_valid_http_method("DELETE") is True
        assert self.validator.is_valid_http_method("PATCH") is True
        assert self.validator.is_valid_http_method("HEAD") is True
        assert self.validator.is_valid_http_method("OPTIONS") is True
    
    def test_is_valid_http_method_invalid(self):
        """Test invalid HTTP method validation."""
        assert self.validator.is_valid_http_method("INVALID") is False
        assert self.validator.is_valid_http_method("TRACE") is False
        assert self.validator.is_valid_http_method("") is False
        assert self.validator.is_valid_http_method(None) is False
        assert self.validator.is_valid_http_method(123) is False
    
    def test_is_valid_http_method_case_insensitive(self):
        """Test HTTP method validation is case insensitive."""
        assert self.validator.is_valid_http_method("get") is True
        assert self.validator.is_valid_http_method("post") is True
        assert self.validator.is_valid_http_method("Get") is True
        assert self.validator.is_valid_http_method("POST") is True
    
    @pytest.mark.asyncio
    async def test_validate_headers_valid(self):
        """Test valid headers validation."""
        request = self.create_mock_request(
            headers={"content-type": "application/json", "user-agent": "test-client"}
        )
        
        result = await self.validator.validate_headers(request)
        
        assert result["is_valid"] is True
        assert result["threat_level"] == "none"
    
    @pytest.mark.asyncio
    async def test_validate_headers_too_many(self):
        """Test headers validation with too many headers."""
        # Create more headers than allowed
        headers = {f"header-{i}": f"value-{i}" for i in range(150)}
        request = self.create_mock_request(headers=headers)
        
        result = await self.validator.validate_headers(request)
        
        assert result["is_valid"] is False
        assert "Too many headers" in result["error_message"]
        assert result["threat_level"] == "medium"
    
    @pytest.mark.asyncio
    async def test_validate_headers_too_large(self):
        """Test headers validation with oversized header."""
        large_value = "x" * 10000  # Larger than max_header_size
        request = self.create_mock_request(headers={"large-header": large_value})
        
        result = await self.validator.validate_headers(request)
        
        assert result["is_valid"] is False
        assert "Header too large" in result["error_message"]
        assert result["threat_level"] == "medium"
    
    @pytest.mark.asyncio
    async def test_validate_headers_blocked_user_agent(self):
        """Test headers validation with blocked user agent."""
        request = self.create_mock_request(headers={"user-agent": "sqlmap/1.0"})
        
        result = await self.validator.validate_headers(request)
        
        assert result["is_valid"] is False
        assert "Blocked user agent detected" in result["error_message"]
        assert result["threat_level"] == "medium"
        assert result["blocked_user_agent"] is True
    
    @pytest.mark.asyncio
    async def test_validate_headers_suspicious_headers(self):
        """Test headers validation with suspicious headers."""
        request = self.create_mock_request(
            headers={"x-forwarded-host": "evil.com", "user-agent": "normal-client"}
        )
        
        result = await self.validator.validate_headers(request)
        
        assert result["is_valid"] is True  # Suspicious but not blocked
        assert result["threat_level"] == "low"
        assert "x-forwarded-host" in result["suspicious_headers"]
    
    @pytest.mark.asyncio
    async def test_check_content_length_valid(self):
        """Test valid content length validation."""
        request = self.create_mock_request(headers={"content-length": "1024"})
        
        result = await self.validator.check_content_length(request)
        
        assert result["is_valid"] is True
        assert result["content_length"] == 1024
    
    @pytest.mark.asyncio
    async def test_check_content_length_too_large(self):
        """Test content length validation with oversized content."""
        large_size = str(20 * 1024 * 1024)  # Larger than max_content_length
        request = self.create_mock_request(headers={"content-length": large_size})
        
        result = await self.validator.check_content_length(request)
        
        assert result["is_valid"] is False
        assert "Content too large" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_check_content_length_invalid_format(self):
        """Test content length validation with invalid format."""
        request = self.create_mock_request(headers={"content-length": "invalid"})
        
        result = await self.validator.check_content_length(request)
        
        assert result["is_valid"] is False
        assert "Invalid content-length header" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_check_content_length_negative(self):
        """Test content length validation with negative value."""
        request = self.create_mock_request(headers={"content-length": "-100"})
        
        result = await self.validator.check_content_length(request)
        
        assert result["is_valid"] is False
        assert "Negative content-length" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_check_content_length_no_header_get(self):
        """Test content length validation with no header for GET request."""
        request = self.create_mock_request(method="GET")
        
        result = await self.validator.check_content_length(request)
        
        assert result["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_security_threats_sql_injection(self):
        """Test security analysis for SQL injection."""
        request = self.create_mock_request(
            path="/api/users",
            query_params={"id": "1 UNION SELECT * FROM users"}
        )
        
        result = await self.validator.analyze_security_threats(request)
        
        assert result["threat_level"] in ["high", "critical"]  # SecurityAnalyzer is more accurate
        assert "sql_injection" in result["threats_found"]
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_security_threats_xss(self):
        """Test security analysis for XSS."""
        request = self.create_mock_request(
            path="/search",
            query_params={"q": "<script>alert('xss')</script>"}
        )
        
        result = await self.validator.analyze_security_threats(request)
        
        assert result["threat_level"] in ["medium", "high"]  # SecurityAnalyzer is more accurate
        assert "xss" in result["threats_found"]
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_security_threats_path_traversal(self):
        """Test security analysis for path traversal."""
        request = self.create_mock_request(path="/files/../../../etc/passwd")
        
        result = await self.validator.analyze_security_threats(request)
        
        assert result["threat_level"] == "medium"
        assert "path_traversal" in result["threats_found"]
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_security_threats_header_injection(self):
        """Test security analysis for header injection."""
        request = self.create_mock_request(
            headers={"x-custom": "value'; DROP TABLE users; --"}
        )
        
        result = await self.validator.analyze_security_threats(request)
        
        assert result["threat_level"] in ["medium", "high", "critical"]  # SecurityAnalyzer detects SQL in headers as critical
        assert "sql_injection" in result["threats_found"]  # SQL injection detected in header
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_security_threats_clean_request(self):
        """Test security analysis for clean request."""
        request = self.create_mock_request(
            path="/api/users",
            query_params={"page": "1", "limit": "10"}
        )
        
        result = await self.validator.analyze_security_threats(request)
        
        assert result["threat_level"] == "none"
        assert result["threats_found"] == []
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_validate_request_valid(self):
        """Test complete request validation for valid request."""
        request = self.create_mock_request(
            method="GET",
            path="/api/users",
            headers={"content-type": "application/json", "user-agent": "test-client"},
            query_params={"page": "1"}
        )
        
        result = await self.validator.validate_request(request)
        
        assert result.is_valid is True
        assert result.error_type is None
        assert result.security_threat_level == "none"
        assert result.validation_details is not None
    
    @pytest.mark.asyncio
    async def test_validate_request_invalid_method(self):
        """Test complete request validation for invalid method."""
        request = self.create_mock_request(method="INVALID")
        
        result = await self.validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type == "invalid_method"
        assert "not allowed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_request_malformed_structure(self):
        """Test complete request validation for malformed structure."""
        request = Mock()
        request.method = None  # Missing method
        
        result = await self.validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type == "malformed_request"
    
    @pytest.mark.asyncio
    async def test_validate_request_security_threat(self):
        """Test complete request validation with security threat."""
        request = self.create_mock_request(
            path="/api/users",
            query_params={"id": "1'; DROP TABLE users; --"},
            headers={"user-agent": "test-client"}
        )
        
        result = await self.validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type == "security_threat"
        assert result.security_threat_level in ["high", "critical"]  # SecurityAnalyzer is more accurate
        assert result.should_rate_limit is True
    
    @pytest.mark.asyncio
    async def test_validate_request_blocked_user_agent(self):
        """Test complete request validation with blocked user agent."""
        request = self.create_mock_request(
            headers={"user-agent": "sqlmap/1.0"}
        )
        
        result = await self.validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type == "invalid_headers"
        assert result.security_threat_level == "medium"
    
    def test_sanitize_request_data(self):
        """Test request data sanitization."""
        request = self.create_mock_request(
            method="POST",
            path="/api/login",
            headers={
                "authorization": "Bearer secret-token",
                "content-type": "application/json",
                "user-agent": "test-client"
            },
            query_params={"password": "secret123", "username": "testuser"}
        )
        
        sanitized = self.validator.sanitize_request_data(request)
        
        assert sanitized["method"] == "POST"
        assert sanitized["path"] == "/api/login"
        assert sanitized["headers"]["authorization"] == "[REDACTED]"
        assert sanitized["headers"]["content-type"] == "application/json"
        assert sanitized["query_params"]["password"] == "[REDACTED]"
        assert sanitized["query_params"]["username"] == "testuser"
        assert sanitized["client_ip"] == "127.0.0.1"
    
    def test_sanitize_request_data_long_header(self):
        """Test request data sanitization with long header."""
        long_value = "x" * 200
        request = self.create_mock_request(
            headers={"x-long-header": long_value}
        )
        
        sanitized = self.validator.sanitize_request_data(request)
        
        assert len(sanitized["headers"]["x-long-header"]) == 103  # 100 chars + "..."
        assert sanitized["headers"]["x-long-header"].endswith("...")
    
    @pytest.mark.asyncio
    async def test_validate_request_with_security_disabled(self):
        """Test request validation with security analysis disabled."""
        config = ValidationConfig(enable_security_analysis=False)
        validator = HTTPRequestValidator(config)
        
        request = self.create_mock_request(
            path="/api/users",
            query_params={"id": "1'; DROP TABLE users; --"}
        )
        
        result = await validator.validate_request(request)
        
        # Should pass because security analysis is disabled
        assert result.is_valid is True
        assert result.security_threat_level == "none"
        assert "security_analysis" not in result.validation_details