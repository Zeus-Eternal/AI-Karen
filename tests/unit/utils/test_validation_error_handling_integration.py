"""
Error Handling and Edge Case Integration Tests for HTTP Request Validation

This module provides comprehensive integration tests for error handling scenarios
and edge cases in the HTTP request validation enhancement system, including:
- Malformed request handling
- System failure recovery
- Edge case scenarios
- Error propagation and logging
- Graceful degradation testing

Requirements covered: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2
"""

import asyncio
import json
import logging
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

import pytest_asyncio

# Import validation system components
from src.ai_karen_engine.server.http_validator import (
    HTTPRequestValidator,
    ValidationConfig,
    ValidationResult
)
from src.ai_karen_engine.server.security_analyzer import (
    SecurityAnalyzer,
    SecurityAssessment,
    ThreatIntelligence
)
from src.ai_karen_engine.server.rate_limiter import (
    EnhancedRateLimiter,
    MemoryRateLimitStorage,
    RateLimitRule,
    RateLimitScope,
    RateLimitAlgorithm,
    RateLimitResult
)
from src.ai_karen_engine.server.enhanced_logger import EnhancedLogger


class TestMalformedRequestHandling:
    """Test handling of various malformed HTTP requests."""
    
    @pytest.fixture
    def validator(self):
        """Create validator for testing."""
        config = ValidationConfig(
            max_content_length=1024,
            max_header_size=512,
            max_headers_count=10,
            enable_security_analysis=True
        )
        return HTTPRequestValidator(config)
    
    def create_malformed_request(self, malformation_type: str):
        """Create various types of malformed requests for testing."""
        if malformation_type == "missing_method":
            request = Mock()
            request.method = None
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            return request
        
        elif malformation_type == "missing_url":
            request = Mock()
            request.method = "GET"
            request.url = None
            request.headers = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            return request
        
        elif malformation_type == "missing_headers":
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = None
            request.client = Mock()
            request.client.host = "127.0.0.1"
            return request
        
        elif malformation_type == "missing_client":
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {}
            request.client = None
            return request
        
        elif malformation_type == "invalid_headers_type":
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = "invalid_headers_type"  # Should be dict-like
            request.client = Mock()
            request.client.host = "127.0.0.1"
            return request
        
        elif malformation_type == "circular_reference":
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            # Create circular reference
            request.circular_ref = request
            return request
        
        elif malformation_type == "exception_on_access":
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            # Make headers raise exception when accessed
            def raise_exception(*args, **kwargs):
                raise RuntimeError("Headers access failed")
            
            request.headers = Mock()
            request.headers.__iter__ = raise_exception
            request.headers.items = raise_exception
            request.headers.get = raise_exception
            
            return request
        
        else:
            raise ValueError(f"Unknown malformation type: {malformation_type}")
    
    @pytest.mark.asyncio
    async def test_missing_basic_attributes(self, validator):
        """Test handling of requests missing basic attributes."""
        malformation_types = [
            "missing_method",
            "missing_url", 
            "missing_headers",
            "missing_client"
        ]
        
        for malformation_type in malformation_types:
            print(f"\nTesting malformation: {malformation_type}")
            
            request = self.create_malformed_request(malformation_type)
            
            # Should handle gracefully without raising exceptions
            result = await validator.validate_request(request)
            
            assert result.is_valid is False
            assert result.error_type in ["malformed_request", "validation_error"]
            assert result.error_message is not None
            
            # Should be able to sanitize even malformed requests
            sanitized = validator.sanitize_request_data(request)
            assert sanitized is not None
            assert isinstance(sanitized, dict)
    
    @pytest.mark.asyncio
    async def test_invalid_data_types(self, validator):
        """Test handling of requests with invalid data types."""
        malformation_types = [
            "invalid_headers_type",
            "circular_reference"
        ]
        
        for malformation_type in malformation_types:
            print(f"\nTesting invalid data type: {malformation_type}")
            
            request = self.create_malformed_request(malformation_type)
            
            # Should handle gracefully
            result = await validator.validate_request(request)
            
            assert result.is_valid is False
            assert result.error_type in ["malformed_request", "validation_error", "invalid_headers"]
            
            # Sanitization should also handle invalid types
            sanitized = validator.sanitize_request_data(request)
            assert sanitized is not None
    
    @pytest.mark.asyncio
    async def test_exception_during_processing(self, validator):
        """Test handling when request attributes raise exceptions."""
        request = self.create_malformed_request("exception_on_access")
        
        # Should handle exceptions during processing
        result = await validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type in ["validation_error", "invalid_headers"]
        
        # Sanitization should handle exceptions too
        sanitized = validator.sanitize_request_data(request)
        assert sanitized is not None
        assert "error" in sanitized or sanitized.get("headers", {}).get("error") is not None
    
    @pytest.mark.asyncio
    async def test_extremely_large_requests(self, validator):
        """Test handling of extremely large request data."""
        # Create request with very large headers
        request = Mock()
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Create headers that exceed limits
        large_headers = {}
        for i in range(50):  # Exceeds max_headers_count of 10
            large_headers[f"header-{i}"] = "x" * 1000  # Each header is large
        
        request.headers = large_headers
        
        result = await validator.validate_request(request)
        
        assert result.is_valid is False
        assert result.error_type == "invalid_headers"
        assert "Too many headers" in result.error_message
    
    @pytest.mark.asyncio
    async def test_unicode_and_encoding_issues(self, validator):
        """Test handling of unicode and encoding issues in requests."""
        # Create request with various unicode and encoding challenges
        request = Mock()
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/test/ñoño/测试/🚀"  # Mixed unicode
        request.url.query = "param=value%20with%20spaces&unicode=测试参数"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Headers with unicode and special characters
        request.headers = {
            "user-agent": "Test/1.0 (测试客户端)",
            "x-custom": "Value with émojis 🎉 and ñoño",
            "x-binary": "\x00\x01\x02\x03",  # Binary data
            "x-long-unicode": "测试" * 100,  # Long unicode string
        }
        
        # Should handle unicode gracefully
        result = await validator.validate_request(request)
        
        # May be valid or invalid depending on size limits, but shouldn't crash
        assert isinstance(result, ValidationResult)
        
        # Sanitization should handle unicode
        sanitized = validator.sanitize_request_data(request)
        assert sanitized is not None
        assert isinstance(sanitized["path"], str)


class TestSystemFailureRecovery:
    """Test system behavior during various failure scenarios."""
    
    @pytest.fixture
    def temp_threat_file(self):
        """Create temporary threat intelligence file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            temp_file = f.name
        yield temp_file
        Path(temp_file).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_security_analyzer_failure_fallback(self):
        """Test fallback when security analyzer fails."""
        config = ValidationConfig(enable_security_analysis=True)
        validator = HTTPRequestValidator(config)
        
        # Create request with potential security issues
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users"
        request.url.query = "id=1' OR 1=1--"  # SQL injection
        request.headers = {"user-agent": "test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock security analyzer to fail
        with patch.object(validator, '_security_analyzer', None):
            # Should fall back to basic security analysis
            result = await validator.analyze_security_threats(request)
            
            assert result["analysis_complete"] is True
            assert result["threat_level"] in ["none", "low", "medium", "high"]
            # Should still detect SQL injection with basic analysis
            assert result["threat_level"] != "none"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_storage_failure(self):
        """Test rate limiter behavior when storage fails."""
        # Create failing storage
        class FailingStorage(MemoryRateLimitStorage):
            async def get_count(self, key, window_seconds):
                raise Exception("Storage failure")
            
            async def increment_count(self, key, window_seconds, amount=1):
                raise Exception("Storage failure")
            
            async def get_request_timestamps(self, key, since):
                raise Exception("Storage failure")
        
        failing_storage = FailingStorage()
        rules = [RateLimitRule(
            name="test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=10,
            window_seconds=60
        )]
        
        rate_limiter = EnhancedRateLimiter(failing_storage, rules)
        
        # Should handle storage failure gracefully
        try:
            result = await rate_limiter.check_rate_limit("127.0.0.1", "/test")
            # If it returns a result, it should be valid
            assert isinstance(result, RateLimitResult)
        except Exception as e:
            # If it raises an exception, it should be handled at a higher level
            assert "Storage failure" in str(e)
    
    @pytest.mark.asyncio
    async def test_threat_intelligence_corruption(self, temp_threat_file):
        """Test handling of corrupted threat intelligence data."""
        # Write corrupted JSON to file
        with open(temp_threat_file, 'w') as f:
            f.write("{ invalid json data }")
        
        # Should handle corrupted file gracefully
        analyzer = SecurityAnalyzer(threat_intelligence_file=temp_threat_file)
        
        # Should initialize with empty threat intelligence
        assert isinstance(analyzer.threat_intelligence, dict)
        assert len(analyzer.threat_intelligence) == 0
        
        # Should still function normally
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        request.headers = {"user-agent": "test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        result = await analyzer.analyze_request(request)
        assert isinstance(result, SecurityAssessment)
    
    @pytest.mark.asyncio
    async def test_logging_system_failure(self):
        """Test behavior when logging system fails."""
        config = ValidationConfig(log_invalid_requests=True)
        validator = HTTPRequestValidator(config)
        
        # Mock logger to fail
        with patch('src.ai_karen_engine.server.http_validator.logger') as mock_logger:
            mock_logger.error.side_effect = Exception("Logging failed")
            mock_logger.info.side_effect = Exception("Logging failed")
            
            # Create invalid request
            request = Mock()
            request.method = "INVALID"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            # Should handle logging failure gracefully
            result = await validator.validate_request(request)
            
            assert result.is_valid is False
            assert result.error_type == "invalid_method"
            # Validation should still work even if logging fails
    
    @pytest.mark.asyncio
    async def test_metrics_collection_failure(self):
        """Test behavior when metrics collection fails."""
        config = ValidationConfig()
        validator = HTTPRequestValidator(config)
        
        # Mock metrics collector to fail
        with patch.object(validator, 'metrics_collector') as mock_collector:
            mock_collector.record_validation_event.side_effect = Exception("Metrics failed")
            mock_collector.record_request_characteristics.side_effect = Exception("Metrics failed")
            
            # Create valid request
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {"user-agent": "test"}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            # Should handle metrics failure gracefully
            result = await validator.validate_request(request)
            
            assert result.is_valid is True
            # Validation should work even if metrics collection fails


class TestEdgeCaseScenarios:
    """Test various edge case scenarios."""
    
    @pytest.fixture
    def validator(self):
        return HTTPRequestValidator(ValidationConfig())
    
    @pytest.fixture
    def rate_limiter(self):
        storage = MemoryRateLimitStorage()
        rules = [RateLimitRule(
            name="test",
            scope=RateLimitScope.IP,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            limit=5,
            window_seconds=60
        )]
        return EnhancedRateLimiter(storage, rules)
    
    @pytest.mark.asyncio
    async def test_zero_length_requests(self, validator):
        """Test handling of zero-length or empty requests."""
        # Request with empty path
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = ""
        request.url.query = ""
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        result = await validator.validate_request(request)
        assert isinstance(result, ValidationResult)
        
        # Request with empty headers
        request.headers = {}
        result = await validator.validate_request(request)
        assert isinstance(result, ValidationResult)
    
    @pytest.mark.asyncio
    async def test_boundary_value_testing(self, validator):
        """Test boundary values for various limits."""
        config = validator.config
        
        # Test exactly at content length limit
        request = Mock()
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        request.headers = {"content-length": str(config.max_content_length)}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        result = await validator.check_content_length(request)
        assert result["is_valid"] is True
        
        # Test exactly over content length limit
        request.headers = {"content-length": str(config.max_content_length + 1)}
        result = await validator.check_content_length(request)
        assert result["is_valid"] is False
        
        # Test exactly at header count limit
        headers = {f"header-{i}": "value" for i in range(config.max_headers_count)}
        request.headers = headers
        result = await validator.validate_headers(request)
        assert result["is_valid"] is True
        
        # Test exactly over header count limit
        headers = {f"header-{i}": "value" for i in range(config.max_headers_count + 1)}
        request.headers = headers
        result = await validator.validate_headers(request)
        assert result["is_valid"] is False
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limit_edge_cases(self, rate_limiter):
        """Test edge cases in concurrent rate limiting."""
        ip_address = "127.0.0.1"
        endpoint = "/test"
        
        # Test rapid concurrent requests at the limit boundary
        async def make_request():
            result = await rate_limiter.check_rate_limit(ip_address, endpoint)
            if result.allowed:
                await rate_limiter.record_request(ip_address, endpoint)
            return result.allowed
        
        # Make exactly the limit number of concurrent requests
        tasks = [make_request() for _ in range(5)]  # Limit is 5
        results = await asyncio.gather(*tasks)
        
        # Some should be allowed, some might be blocked due to race conditions
        allowed_count = sum(1 for allowed in results if allowed)
        assert 0 < allowed_count <= 5
        
        # Additional request should definitely be blocked
        result = await rate_limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
    
    @pytest.mark.asyncio
    async def test_time_boundary_edge_cases(self, rate_limiter):
        """Test edge cases around time boundaries."""
        ip_address = "127.0.0.2"
        endpoint = "/time-test"
        
        # Make requests up to the limit
        for _ in range(5):
            result = await rate_limiter.check_rate_limit(ip_address, endpoint)
            assert result.allowed is True
            await rate_limiter.record_request(ip_address, endpoint)
        
        # Next request should be blocked
        result = await rate_limiter.check_rate_limit(ip_address, endpoint)
        assert result.allowed is False
        
        # Test retry_after calculation
        assert result.retry_after_seconds > 0
        assert result.retry_after_seconds <= 60  # Should be within window
    
    @pytest.mark.asyncio
    async def test_ip_address_edge_cases(self, validator, rate_limiter):
        """Test edge cases with IP addresses."""
        edge_case_ips = [
            "0.0.0.0",
            "255.255.255.255",
            "127.0.0.1",
            "::1",  # IPv6 localhost
            "2001:db8::1",  # IPv6 example
            "",  # Empty IP
            "invalid-ip",
            None
        ]
        
        for ip in edge_case_ips:
            print(f"Testing IP: {ip}")
            
            # Create request with edge case IP
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {"user-agent": "test"}
            request.client = Mock()
            request.client.host = ip
            
            # Validator should handle all IP types
            result = await validator.validate_request(request)
            assert isinstance(result, ValidationResult)
            
            # Rate limiter should handle all IP types
            try:
                rate_result = await rate_limiter.check_rate_limit(
                    ip or "unknown", "/test"
                )
                assert isinstance(rate_result, RateLimitResult)
            except Exception as e:
                # Some invalid IPs might cause exceptions, which is acceptable
                print(f"  IP {ip} caused exception: {e}")
    
    @pytest.mark.asyncio
    async def test_header_encoding_edge_cases(self, validator):
        """Test edge cases with header encoding."""
        edge_case_headers = [
            # Normal headers
            {"user-agent": "normal-client"},
            
            # Headers with special characters
            {"x-special": "value with spaces and symbols !@#$%^&*()"},
            
            # Headers with unicode
            {"x-unicode": "测试值 🚀 émojis"},
            
            # Headers with control characters
            {"x-control": "value\twith\ncontrol\rcharacters"},
            
            # Very long header names and values
            {"x-" + "long" * 100: "value"},
            {"x-long-value": "x" * 1000},
            
            # Headers with null bytes (should be handled safely)
            {"x-null": "value\x00with\x00nulls"},
            
            # Empty headers
            {"": "empty-name"},
            {"x-empty": ""},
            
            # Headers that look like attacks
            {"x-sql": "'; DROP TABLE users; --"},
            {"x-xss": "<script>alert('xss')</script>"},
        ]
        
        for headers in edge_case_headers:
            print(f"Testing headers: {list(headers.keys())}")
            
            request = Mock()
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = headers
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            # Should handle all header types without crashing
            result = await validator.validate_request(request)
            assert isinstance(result, ValidationResult)
            
            # Sanitization should handle all header types
            sanitized = validator.sanitize_request_data(request)
            assert sanitized is not None
            assert isinstance(sanitized, dict)


class TestErrorPropagationAndLogging:
    """Test error propagation and logging behavior."""
    
    @pytest.fixture
    def enhanced_logger(self):
        return EnhancedLogger()
    
    @pytest.mark.asyncio
    async def test_error_logging_integration(self, enhanced_logger):
        """Test integration between validation and logging systems."""
        config = ValidationConfig(log_invalid_requests=True)
        validator = HTTPRequestValidator(config)
        
        # Mock the enhanced logger
        with patch.object(validator, '_enhanced_logger', enhanced_logger):
            # Create invalid request
            request = Mock()
            request.method = "INVALID"
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            request.headers = {}
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            # Validate request
            result = await validator.validate_request(request)
            
            assert result.is_valid is False
            assert result.error_type == "invalid_method"
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self):
        """Test logging of security events."""
        config = ValidationConfig(enable_security_analysis=True)
        validator = HTTPRequestValidator(config)
        
        # Create request with security threat
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users"
        request.url.query = "id=1' OR 1=1--"
        request.headers = {"user-agent": "test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock logger to capture calls
        with patch('src.ai_karen_engine.server.http_validator.logger') as mock_logger:
            result = await validator.validate_request(request)
            
            # Should log security events appropriately
            if not result.is_valid and result.error_type == "security_threat":
                # Verify logging was attempted (exact calls depend on implementation)
                assert mock_logger.info.called or mock_logger.warning.called or mock_logger.error.called
    
    @pytest.mark.asyncio
    async def test_error_context_preservation(self):
        """Test that error context is preserved through the validation pipeline."""
        validator = HTTPRequestValidator(ValidationConfig())
        
        # Create request that will fail at different stages
        request = Mock()
        request.method = "INVALID"  # Will fail method validation
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        request.headers = {"content-length": "invalid"}  # Would fail content length if reached
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        result = await validator.validate_request(request)
        
        # Should fail at method validation and preserve context
        assert result.is_valid is False
        assert result.error_type == "invalid_method"
        assert result.error_message is not None
        assert "not allowed" in result.error_message.lower()
        
        # Validation details should contain information about what was checked
        assert result.validation_details is not None
        assert "method_valid" in result.validation_details
        assert result.validation_details["method_valid"] is False


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    @pytest.mark.asyncio
    async def test_partial_system_failure(self):
        """Test behavior when parts of the system fail."""
        config = ValidationConfig(enable_security_analysis=True)
        validator = HTTPRequestValidator(config)
        
        # Create request
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = "param=value"
        request.headers = {"user-agent": "test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock security analyzer to fail
        with patch.object(validator, 'analyze_security_threats') as mock_analyze:
            mock_analyze.side_effect = Exception("Security analysis failed")
            
            # Should still validate basic request structure
            result = await validator.validate_request(request)
            
            # Should handle the failure gracefully
            assert isinstance(result, ValidationResult)
            # Might be valid (if basic validation passes) or invalid (if error handling blocks it)
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios."""
        validator = HTTPRequestValidator(ValidationConfig())
        
        # Simulate memory pressure by creating many large requests
        large_requests = []
        
        try:
            for i in range(100):
                request = Mock()
                request.method = "POST"
                request.url = Mock()
                request.url.path = f"/test/{i}"
                request.url.query = "param=value" * 1000  # Large query
                request.headers = {f"header-{j}": "x" * 100 for j in range(50)}  # Many headers
                request.client = Mock()
                request.client.host = f"192.168.1.{i % 255 + 1}"
                
                large_requests.append(request)
            
            # Process all requests - should handle resource pressure gracefully
            results = []
            for request in large_requests:
                try:
                    result = await validator.validate_request(request)
                    results.append(result)
                except Exception as e:
                    # Should not raise unhandled exceptions even under pressure
                    print(f"Request failed with: {e}")
                    results.append(None)
            
            # Should have processed most requests successfully
            successful_results = [r for r in results if r is not None]
            success_rate = len(successful_results) / len(results)
            
            assert success_rate >= 0.8, f"Success rate too low under resource pressure: {success_rate:.2%}"
            
        finally:
            # Clean up
            large_requests.clear()


if __name__ == "__main__":
    # Run error handling tests
    pytest.main([__file__, "-v", "--tb=short"])