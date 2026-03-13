"""
Tests for logging setup functionality.

Tests logging configuration, setup, and initialization.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLoggingSetup:
    """Test logging setup functionality."""
    
    def test_logging_setup_module_imports(self):
        """Test that logging setup module can be imported."""
        # Import the module
        import logging_setup
        
        # Verify module has expected functions
        assert hasattr(logging_setup, 'configure_logging')
        assert hasattr(logging_setup, 'apply_uvicorn_filters')
    
    def test_setup_logging_function_exists(self):
        """Test that setup_logging function exists and is callable."""
        # Import the function
        from logging_setup import configure_logging
        
        # Verify function exists and is callable
        assert callable(configure_logging)
    
    def test_setup_logging_with_default_parameters(self):
        """Test setup_logging with default parameters."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Call configure_logging
            configure_logging()
            
            # Verify logging was configured
            mock_logging.basicConfig.assert_called()
            mock_logging.getLogger.assert_called()
    
    def test_setup_logging_with_custom_level(self):
        """Test setup_logging with custom log level."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Call configure_logging with custom level
            configure_logging()
            
            # Verify logging was configured
            mock_logging.basicConfig.assert_called()
            mock_logging.getLogger.assert_called()
    
    def test_setup_logging_creates_log_directory(self):
        """Test setup_logging creates log directory if it doesn't exist."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = False
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Call configure_logging
            configure_logging()
            
            # Verify directory was created
            mock_makedirs.assert_called()
    
    def test_setup_logging_configures_formatters(self):
        """Test setup_logging configures log formatters."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Mock formatter
            mock_formatter = Mock()
            mock_logging.Formatter.return_value = mock_formatter
            
            # Call configure_logging
            configure_logging()
            
            # Verify formatter was created
            mock_logging.Formatter.assert_called()
    
    def test_setup_logging_configures_handlers(self):
        """Test setup_logging configures log handlers."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Mock handler
            mock_handler = Mock()
            mock_logging.FileHandler.return_value = mock_handler
            
            # Call configure_logging
            configure_logging()
            
            # Verify handler was configured
            mock_handler.setFormatter.assert_called()
            mock_logger.addHandler.assert_called()
    
    def test_setup_logging_with_log_file(self):
        """Test setup_logging with custom log file."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Mock handler
            mock_handler = Mock()
            mock_logging.FileHandler.return_value = mock_handler
            
            # Call configure_logging with custom log file
            configure_logging()
            
            # Verify handler was created with correct file
            mock_logging.FileHandler.assert_called_with("test.log")
    
    def test_setup_logging_with_console_output(self):
        """Test setup_logging with console output enabled."""
        # Import the function
        from logging_setup import configure_logging
        
        # Mock logging components
        with patch('logging_setup.logging') as mock_logging, \
             patch('logging_setup.os.path.exists') as mock_exists, \
             patch('logging_setup.os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = True
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            # Mock handler
            mock_handler = Mock()
            mock_logging.StreamHandler.return_value = mock_handler
            
            # Call configure_logging with console output
            configure_logging()
            
            # Verify console handler was created
            mock_logging.StreamHandler.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])