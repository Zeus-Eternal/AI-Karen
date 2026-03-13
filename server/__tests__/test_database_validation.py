"""
Tests for database validation functionality.

Tests database connection validation, configuration parsing, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseValidation:
    """Test database validation functionality."""
    
    def test_request_size_validation(self):
        """Test request size configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test valid request size
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024  # 10MB
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid request size (zero)
        settings.max_request_size = 0
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid request size (too large)
        settings.max_request_size = 200 * 1024 * 1024  # 200MB
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid request size (negative)
        settings.max_request_size = -100
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_headers_count_validation(self):
        """Test headers count configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test valid headers count
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid headers count (zero)
        settings.max_headers_count = 0
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid headers count (too many)
        settings.max_headers_count = 2000
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid headers count (negative)
        settings.max_headers_count = -10
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_header_size_validation(self):
        """Test header size configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test valid header size
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid header size (zero)
        settings.max_header_size = 0
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid header size (too large)
        settings.max_header_size = 50000  # > 32KB
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid header size (negative)
        settings.max_header_size = -100
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_rate_limit_validation(self):
        """Test rate limit configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test valid rate limit
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid rate limit (zero)
        settings.validation_rate_limit_per_minute = 0
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid rate limit (too high)
        settings.validation_rate_limit_per_minute = 20000
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid rate limit (negative)
        settings.validation_rate_limit_per_minute = -100
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_invalid_requests_per_connection_validation(self):
        """Test invalid requests per connection configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test valid invalid requests per connection
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid invalid requests per connection (zero)
        settings.max_invalid_requests_per_connection = 0
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid invalid requests per connection (too high)
        settings.max_invalid_requests_per_connection = 2000
        result = validate_configuration_settings(settings)
        assert result is False
        
        # Test invalid invalid requests per connection (negative)
        settings.max_invalid_requests_per_connection = -10
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_combined_validation(self):
        """Test multiple validation settings together."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test all valid settings
        settings = Mock()
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test with multiple invalid settings
        settings.max_request_size = -1
        settings.max_headers_count = 0
        settings.max_header_size = 50000
        settings.validation_rate_limit_per_minute = -10
        settings.max_invalid_requests_per_connection = 2000
        
        result = validate_configuration_settings(settings)
        assert result is False
    
    def test_edge_case_values(self):
        """Test edge case values for validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Test minimum valid values
        settings = Mock()
        settings.max_request_size = 1  # Minimum positive
        settings.max_headers_count = 1  # Minimum valid
        settings.max_header_size = 1  # Minimum valid
        settings.validation_rate_limit_per_minute = 1  # Minimum valid
        settings.max_invalid_requests_per_connection = 1  # Minimum valid
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test maximum valid values
        settings.max_request_size = 100 * 1024 * 1024  # Maximum valid
        settings.max_headers_count = 1000  # Maximum valid
        settings.max_header_size = 32768  # Maximum valid
        settings.validation_rate_limit_per_minute = 10000  # Maximum valid
        settings.max_invalid_requests_per_connection = 1000  # Maximum valid
        
        result = validate_configuration_settings(settings)
        assert result is True
    
    def test_validation_with_missing_attributes(self):
        """Test validation when settings attributes are missing."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Create a mock settings object with missing attributes
        settings = Mock()
        
        # Delete some attributes to simulate missing settings
        del settings.max_request_size
        del settings.max_headers_count
        
        # This should handle missing attributes gracefully
        try:
            result = validate_configuration_settings(settings)
            assert result is False  # Should fail due to missing attributes
        except AttributeError:
            # If it raises AttributeError, that's also acceptable
            pass
    
    def test_graceful_shutdown_configuration_validation(self):
        """Test graceful shutdown configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Create a mock settings object
        settings = Mock()
        
        # Test graceful shutdown enabled
        settings.enable_graceful_shutdown = True
        settings.shutdown_timeout = 30
        settings.db_connection_timeout = 45
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        settings.db_pool_size = 10
        settings.db_max_overflow = 20
        settings.db_pool_recycle = 3600
        settings.db_pool_timeout = 30
        settings.db_health_check_interval = 30
        settings.db_max_connection_failures = 5
        settings.db_connection_retry_delay = 5
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test graceful shutdown disabled
        settings.enable_graceful_shutdown = False
        result = validate_configuration_settings(settings)
        assert result is True  # Should still be valid as it's optional
    
    def test_shutdown_timeout_validation(self):
        """Test shutdown timeout configuration validation."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Create a mock settings object
        settings = Mock()
        
        # Test valid timeout (shutdown_timeout is not validated by validate_configuration_settings)
        settings.shutdown_timeout = 30
        settings.max_request_size = 10 * 1024 * 1024
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid timeout (shutdown_timeout is not validated, so this should still pass)
        settings.shutdown_timeout = 5
        result = validate_configuration_settings(settings)
        assert result is True
        
        # Test invalid timeout (shutdown_timeout is not validated, so this should still pass)
        settings.shutdown_timeout = -10
        result = validate_configuration_settings(settings)
        assert result is True


class TestValidationIntegration:
    """Test validation integration with other components."""
    
    @patch('validation.logger')
    def test_validation_with_logging(self, mock_logger):
        """Test that validation functions log appropriately."""
        # Import the validation function
        from validation import validate_configuration_settings
        
        # Create a mock settings object with invalid values
        settings = Mock()
        settings.max_request_size = 0  # Invalid: too low
        settings.max_headers_count = 100
        settings.max_header_size = 8192
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        settings.db_pool_size = 10
        settings.db_max_overflow = 20
        settings.db_pool_recycle = 3600
        settings.db_pool_timeout = 30
        settings.db_health_check_interval = 30
        settings.db_max_connection_failures = 5
        settings.db_connection_retry_delay = 5
        settings.shutdown_timeout = 30
        
        # Call the validation function
        validate_configuration_settings(settings)
        
        # Verify that an error was logged
        mock_logger.error.assert_called()
        assert any("must be positive" in str(call) for call in mock_logger.error.call_args_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])