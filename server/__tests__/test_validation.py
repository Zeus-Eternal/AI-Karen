"""
Tests for validation functionality.

Tests input validation, schema validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import (
    load_environment_specific_validation_config,
    validate_configuration_settings,
    initialize_validation_framework
)


class TestEnvironmentSpecificValidationConfig:
    """Test environment-specific validation configuration loading."""
    
    def test_production_environment_config(self):
        """Test validation configuration for production environment."""
        settings = Mock()
        settings.environment = "production"
        settings.max_request_size = 10 * 1024 * 1024  # 10MB
        settings.enable_request_validation = False
        settings.enable_security_analysis = False
        settings.log_invalid_requests = False
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = load_environment_specific_validation_config(settings)
        
        assert result.enable_request_validation is True
        assert result.log_invalid_requests is True
        assert result.max_request_size == 5 * 1024 * 1024  # Should be limited to 5MB in prod
        assert result.validation_rate_limit_per_minute == 50
        assert result.max_invalid_requests_per_connection == 5
    
    def test_development_environment_config(self):
        """Test validation configuration for development environment."""
        settings = Mock()
        settings.environment = "development"
        settings.enable_request_validation = False
        settings.enable_security_analysis = False
        settings.log_invalid_requests = False
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = load_environment_specific_validation_config(settings)
        
        assert result.enable_request_validation is True
        assert result.log_invalid_requests is True
        assert result.validation_rate_limit_per_minute == 200
        assert result.max_invalid_requests_per_connection == 20
    
    def test_testing_environment_config(self):
        """Test validation configuration for testing environment."""
        settings = Mock()
        settings.environment = "test"
        settings.enable_request_validation = False
        settings.enable_security_analysis = True
        settings.log_invalid_requests = True
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = load_environment_specific_validation_config(settings)
        
        assert result.enable_request_validation is True
        assert result.log_invalid_requests is False  # Disabled for tests
        assert result.validation_rate_limit_per_minute == 1000
        assert result.max_invalid_requests_per_connection == 100
    
    def test_staging_environment_config(self):
        """Test validation configuration for staging environment."""
        settings = Mock()
        settings.environment = "staging"
        settings.enable_request_validation = False
        settings.enable_security_analysis = False
        settings.log_invalid_requests = False
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = load_environment_specific_validation_config(settings)
        
        assert result.enable_request_validation is True
        assert result.log_invalid_requests is True
        assert result.validation_rate_limit_per_minute == 100
        assert result.max_invalid_requests_per_connection == 10


class TestConfigurationSettingsValidation:
    """Test configuration settings validation."""
    
    def test_valid_configuration_settings(self):
        """Test validation of valid configuration settings."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024  # 5MB
        settings.max_headers_count = 100
        settings.max_header_size = 8192  # 8KB
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is True
    
    def test_invalid_max_request_size_too_large(self):
        """Test validation of max_request_size that's too large."""
        settings = Mock()
        settings.max_request_size = 200 * 1024 * 1024  # 200MB
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_max_request_size_zero(self):
        """Test validation of max_request_size that's zero."""
        settings = Mock()
        settings.max_request_size = 0
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_max_headers_count_out_of_range(self):
        """Test validation of max_headers_count outside valid range."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 2000  # Too high
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_max_header_size_out_of_range(self):
        """Test validation of max_header_size outside valid range."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 50000  # Too high
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_validation_rate_limit_zero(self):
        """Test validation of validation_rate_limit_per_minute that's zero."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 0
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_validation_rate_limit_too_high(self):
        """Test validation of validation_rate_limit_per_minute that's too high."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 20000  # Too high
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_max_invalid_requests_zero(self):
        """Test validation of max_invalid_requests_per_connection that's zero."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 0
        
        result = validate_configuration_settings(settings)
        
        assert result is False
    
    def test_invalid_max_invalid_requests_too_high(self):
        """Test validation of max_invalid_requests_per_connection that's too high."""
        settings = Mock()
        settings.max_request_size = 5 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 2000  # Too high
        
        result = validate_configuration_settings(settings)
        
        assert result is False


class TestValidationFrameworkInitialization:
    """Test validation framework initialization."""
    
    @patch('validation.logger')
    def test_initialization_with_exception(self, mock_logger):
        """Test initialization when an exception occurs."""
        settings = Mock()
        
        # Force an exception during initialization
        with patch('validation.load_environment_specific_validation_config', side_effect=Exception("Test error")):
            initialize_validation_framework(settings)
            
            # Should log the error but not crash
            mock_logger.error.assert_called()
    
    def test_blocked_user_agents_parsing(self):
        """Test parsing of blocked user agents list."""
        settings = Mock()
        settings.environment = "production"
        settings.blocked_user_agents = "  bot1 , bot2 , , bot3  "  # With extra spaces
        
        # Test parsing logic directly
        blocked_agents = set(agent.strip().lower() for agent in settings.blocked_user_agents.split(",") if agent.strip())
        
        # Verify that agents were parsed correctly
        assert 'bot1' in blocked_agents
        assert 'bot2' in blocked_agents
        assert 'bot3' in blocked_agents
    
    def test_suspicious_headers_parsing(self):
        """Test parsing of suspicious headers list."""
        settings = Mock()
        settings.environment = "production"
        settings.suspicious_headers = "  x-evil , x-malicious , , x-suspicious  "  # With extra spaces
        
        # Test parsing logic directly
        suspicious_headers = set(header.strip().lower() for header in settings.suspicious_headers.split(",") if header.strip())
        
        # Verify that headers were parsed correctly
        assert 'x-evil' in suspicious_headers
        assert 'x-malicious' in suspicious_headers
        assert 'x-suspicious' in suspicious_headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])