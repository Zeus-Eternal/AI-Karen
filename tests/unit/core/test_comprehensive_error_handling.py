"""
Test Comprehensive Error Handling

Tests the comprehensive error handling system implemented for task 10.1 and 10.2:
- Network error handling with retry mechanisms
- Disk space and permission error handling
- User-friendly error messages with resolution steps
- Error categorization and logging
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, SSLError

from ai_karen_engine.utils.error_handling import (
    ErrorHandler, ErrorCategory, ErrorSeverity, ErrorInfo,
    ModelLibraryError, NetworkError, DiskSpaceError, PermissionError,
    ValidationError, SecurityError,
    handle_network_error, handle_disk_space_error, handle_permission_error,
    handle_validation_error, handle_download_error,
    validate_disk_space, validate_file_permissions, execute_with_retry
)


class TestErrorHandler:
    """Test the ErrorHandler class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handle_network_error_connection_error(self):
        """Test handling of connection errors."""
        error = ConnectionError("Connection failed")
        error_info = self.error_handler.handle_network_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Connection Failed" in error_info.title
        assert "internet connection" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "NET_001"
    
    def test_handle_network_error_timeout(self):
        """Test handling of timeout errors."""
        error = Timeout("Request timeout")
        error_info = self.error_handler.handle_network_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "Request Timeout" in error_info.title
        assert "took too long" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "NET_002"
    
    def test_handle_network_error_ssl_error(self):
        """Test handling of SSL errors."""
        error = SSLError("SSL certificate verification failed")
        error_info = self.error_handler.handle_network_error(error)
        
        assert error_info.category == ErrorCategory.SECURITY
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Security Certificate Error" in error_info.title
        assert "certificate" in error_info.message
        assert error_info.retry_possible is False
        assert error_info.user_action_required is True
        assert error_info.error_code == "SEC_001"
    
    def test_handle_network_error_http_error(self):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = HTTPError("Not found")
        error.response = mock_response
        
        error_info = self.error_handler.handle_network_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "Server Error" in error_info.title
        assert "HTTP 404" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "NET_003"
    
    def test_handle_disk_space_error(self):
        """Test handling of disk space errors."""
        required_space = 5 * 1024**3  # 5GB
        available_space = 1 * 1024**3  # 1GB
        path = str(self.temp_dir)
        
        error_info = self.error_handler.handle_disk_space_error(
            required_space, available_space, path
        )
        
        assert error_info.category == ErrorCategory.DISK_SPACE
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Insufficient Disk Space" in error_info.title
        assert "5.00GB" in error_info.message
        assert "1.00GB" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.user_action_required is True
        assert error_info.error_code == "DISK_001"
    
    def test_handle_permission_error(self):
        """Test handling of permission errors."""
        path = str(self.temp_dir / "test_file.txt")
        operation = "write to"
        
        error_info = self.error_handler.handle_permission_error(path, operation)
        
        assert error_info.category == ErrorCategory.PERMISSION
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Permission Denied" in error_info.title
        assert "write to" in error_info.message
        assert path in error_info.message
        assert error_info.retry_possible is True
        assert error_info.user_action_required is True
        assert error_info.error_code == "PERM_001"
    
    def test_handle_validation_error_model_id(self):
        """Test handling of model ID validation errors."""
        error_info = self.error_handler.handle_validation_error(
            "model_id", "Model not found"
        )
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "Invalid Model" in error_info.title
        assert "not found" in error_info.message
        assert error_info.retry_possible is False
        assert error_info.error_code == "VAL_001"
    
    def test_handle_validation_error_checksum(self):
        """Test handling of checksum validation errors."""
        error_info = self.error_handler.handle_validation_error(
            "checksum", "Checksum mismatch"
        )
        
        assert error_info.category == ErrorCategory.SECURITY
        assert error_info.severity == ErrorSeverity.HIGH
        assert "File Integrity Check Failed" in error_info.title
        assert "corrupted" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "SEC_002"
    
    def test_handle_download_error_interrupted(self):
        """Test handling of interrupted download errors."""
        error_info = self.error_handler.handle_download_error(
            "interrupted", "Connection lost"
        )
        
        assert error_info.category == ErrorCategory.DOWNLOAD
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "Download Interrupted" in error_info.title
        assert "interrupted" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "DL_001"
    
    def test_handle_download_error_corrupted(self):
        """Test handling of corrupted download errors."""
        error_info = self.error_handler.handle_download_error(
            "corrupted", "File integrity check failed"
        )
        
        assert error_info.category == ErrorCategory.DOWNLOAD
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Download Corrupted" in error_info.title
        assert "corrupted" in error_info.message
        assert error_info.retry_possible is True
        assert error_info.error_code == "DL_002"
    
    def test_should_retry_logic(self):
        """Test retry logic for different error types."""
        # Network errors should be retryable
        network_error = ErrorInfo(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            title="Network Error",
            message="Connection failed",
            technical_details="",
            resolution_steps=[],
            retry_possible=True
        )
        
        assert self.error_handler.should_retry(network_error, 0) is True
        assert self.error_handler.should_retry(network_error, 1) is True
        assert self.error_handler.should_retry(network_error, 2) is True
        assert self.error_handler.should_retry(network_error, 3) is False  # Exceeds max retries
        
        # Validation errors should not be retryable
        validation_error = ErrorInfo(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            title="Validation Error",
            message="Invalid input",
            technical_details="",
            resolution_steps=[],
            retry_possible=False
        )
        
        assert self.error_handler.should_retry(validation_error, 0) is False
    
    def test_calculate_retry_delay(self):
        """Test retry delay calculation with exponential backoff."""
        network_error = ErrorInfo(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            title="Network Error",
            message="Connection failed",
            technical_details="",
            resolution_steps=[],
            retry_possible=True
        )
        
        # Test exponential backoff (with jitter, so we check ranges)
        delay_0 = self.error_handler.calculate_retry_delay(network_error, 0)
        delay_1 = self.error_handler.calculate_retry_delay(network_error, 1)
        delay_2 = self.error_handler.calculate_retry_delay(network_error, 2)
        
        # Base delay with jitter should be between 0.5 and 1.0
        assert 0.5 <= delay_0 <= 1.0
        # Second delay should be between 1.0 and 2.0 (2^1 with jitter)
        assert 1.0 <= delay_1 <= 2.0
        # Third delay should be between 2.0 and 4.0 (2^2 with jitter)
        assert 2.0 <= delay_2 <= 4.0
        
        # Test max delay cap
        delay_10 = self.error_handler.calculate_retry_delay(network_error, 10)
        assert delay_10 <= 60.0  # Should not exceed max delay
    
    def test_create_error_response(self):
        """Test creation of standardized error responses."""
        error_info = ErrorInfo(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="Network Error",
            message="Connection failed",
            technical_details="TCP connection timeout",
            resolution_steps=["Check internet", "Try again"],
            retry_possible=True,
            user_action_required=False,
            error_code="NET_001",
            context={"url": "https://example.com"}
        )
        
        response = self.error_handler.create_error_response(error_info)
        
        assert response["error"] is True
        assert response["error_code"] == "NET_001"
        assert response["category"] == "network"
        assert response["severity"] == "high"
        assert response["title"] == "Network Error"
        assert response["message"] == "Connection failed"
        assert response["technical_details"] == "TCP connection timeout"
        assert response["resolution_steps"] == ["Check internet", "Try again"]
        assert response["retry_possible"] is True
        assert response["user_action_required"] is False
        assert response["context"]["url"] == "https://example.com"


class TestValidationFunctions:
    """Test validation utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('shutil.disk_usage')
    def test_validate_disk_space_sufficient(self, mock_disk_usage):
        """Test disk space validation with sufficient space."""
        # Mock sufficient disk space (10GB available, 1GB required)
        mock_disk_usage.return_value = Mock(free=10 * 1024**3)
        
        # Should not raise an exception
        validate_disk_space(self.temp_dir, 1 * 1024**3)
    
    @patch('shutil.disk_usage')
    def test_validate_disk_space_insufficient(self, mock_disk_usage):
        """Test disk space validation with insufficient space."""
        # Mock insufficient disk space (1GB available, 10GB required)
        mock_disk_usage.return_value = Mock(free=1 * 1024**3)
        
        with pytest.raises(DiskSpaceError) as exc_info:
            validate_disk_space(self.temp_dir, 10 * 1024**3)
        
        assert exc_info.value.error_info.category == ErrorCategory.DISK_SPACE
        assert "Insufficient Disk Space" in exc_info.value.error_info.title
    
    def test_validate_file_permissions_readable_file(self):
        """Test file permission validation for readable file."""
        test_file = self.temp_dir / "readable.txt"
        test_file.write_text("test content")
        
        # Should not raise an exception
        validate_file_permissions(test_file, "read")
    
    def test_validate_file_permissions_writable_directory(self):
        """Test file permission validation for writable directory."""
        # Should not raise an exception for writable temp directory
        validate_file_permissions(self.temp_dir, "write")
    
    @patch('os.access')
    def test_validate_file_permissions_no_read_access(self, mock_access):
        """Test file permission validation with no read access."""
        mock_access.return_value = False
        
        test_file = self.temp_dir / "unreadable.txt"
        test_file.write_text("test content")
        
        with pytest.raises(PermissionError) as exc_info:
            validate_file_permissions(test_file, "read")
        
        assert exc_info.value.error_info.category == ErrorCategory.PERMISSION
        assert "Permission Denied" in exc_info.value.error_info.title


class TestRetryMechanism:
    """Test the retry mechanism functionality."""
    
    def test_execute_with_retry_success_first_attempt(self):
        """Test successful operation on first attempt."""
        mock_operation = Mock(return_value="success")
        mock_error_handler = Mock()
        
        result = execute_with_retry(mock_operation, mock_error_handler)
        
        assert result == "success"
        assert mock_operation.call_count == 1
        assert mock_error_handler.call_count == 0
    
    def test_execute_with_retry_success_after_retries(self):
        """Test successful operation after retries."""
        # Mock operation that fails twice then succeeds
        mock_operation = Mock(side_effect=[
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"),
            "success"
        ])
        
        def mock_error_handler(error):
            return ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                title="Network Error",
                message="Connection failed",
                technical_details="",
                resolution_steps=[],
                retry_possible=True
            )
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = execute_with_retry(mock_operation, mock_error_handler)
        
        assert result == "success"
        assert mock_operation.call_count == 3
    
    def test_execute_with_retry_max_retries_exceeded(self):
        """Test operation that fails after max retries."""
        # Mock operation that always fails
        mock_operation = Mock(side_effect=ConnectionError("Connection failed"))
        
        def mock_error_handler(error):
            return ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                title="Network Error",
                message="Connection failed",
                technical_details="",
                resolution_steps=[],
                retry_possible=True
            )
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(ModelLibraryError) as exc_info:
                execute_with_retry(mock_operation, mock_error_handler)
        
        assert exc_info.value.error_info.category == ErrorCategory.NETWORK
        assert mock_operation.call_count == 4  # Initial attempt + 3 retries
    
    def test_execute_with_retry_non_retryable_error(self):
        """Test operation with non-retryable error."""
        mock_operation = Mock(side_effect=ValueError("Invalid input"))
        
        def mock_error_handler(error):
            return ErrorInfo(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                title="Validation Error",
                message="Invalid input",
                technical_details="",
                resolution_steps=[],
                retry_possible=False
            )
        
        with pytest.raises(ModelLibraryError) as exc_info:
            execute_with_retry(mock_operation, mock_error_handler)
        
        assert exc_info.value.error_info.category == ErrorCategory.VALIDATION
        assert mock_operation.call_count == 1  # No retries for non-retryable errors


class TestConvenienceFunctions:
    """Test convenience functions for error handling."""
    
    def test_handle_network_error_convenience(self):
        """Test convenience function for network errors."""
        error = ConnectionError("Connection failed")
        error_info = handle_network_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert "Connection Failed" in error_info.title
    
    def test_handle_disk_space_error_convenience(self):
        """Test convenience function for disk space errors."""
        error_info = handle_disk_space_error(
            5 * 1024**3, 1 * 1024**3, "/tmp"
        )
        
        assert error_info.category == ErrorCategory.DISK_SPACE
        assert "Insufficient Disk Space" in error_info.title
    
    def test_handle_permission_error_convenience(self):
        """Test convenience function for permission errors."""
        error_info = handle_permission_error("/tmp/test", "write to")
        
        assert error_info.category == ErrorCategory.PERMISSION
        assert "Permission Denied" in error_info.title
    
    def test_handle_validation_error_convenience(self):
        """Test convenience function for validation errors."""
        error_info = handle_validation_error("model_id", "Model not found")
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert "Invalid Model" in error_info.title
    
    def test_handle_download_error_convenience(self):
        """Test convenience function for download errors."""
        error_info = handle_download_error("interrupted", "Connection lost")
        
        assert error_info.category == ErrorCategory.DOWNLOAD
        assert "Download Interrupted" in error_info.title


if __name__ == "__main__":
    pytest.main([__file__])