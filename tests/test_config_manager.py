"""
Tests for the configuration management system.

This module tests the comprehensive configuration management capabilities
including dynamic updates, versioning, hot-reloading, and validation.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ai_karen_engine.security.config_manager import (
    ConfigurationManager,
    ConfigVersion,
    ConfigChangeEvent,
    ConfigSource,
    ConfigFormat,
    load_config_from_file,
    save_config_to_file,
    create_default_config
)
from ai_karen_engine.security.models import IntelligentAuthConfig, RiskThresholds
from ai_karen_engine.security.intelligent_auth_base import Configurable


class MockConfigurableService:
    """Mock configurable service for testing."""
    
    def __init__(self):
        self.update_config_called = False
        self.last_config = None
    
    async def update_config(self, config: IntelligentAuthConfig) -> bool:
        self.update_config_called = True
        self.last_config = config
        return True


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    @pytest.fixture
    def config_manager(self):
        """Create test configuration manager."""
        return ConfigurationManager(
            enable_hot_reload=False,  # Disable for testing
            enable_versioning=True,
            max_versions=10
        )

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return IntelligentAuthConfig(
            enable_nlp_analysis=True,
            enable_embedding_analysis=True,
            max_processing_time=3.0,
            cache_size=5000,
            cache_ttl=1800
        )

    @pytest.mark.asyncio
    async def test_config_manager_initialization(self, config_manager):
        """Test configuration manager initialization."""
        assert config_manager.config_class == IntelligentAuthConfig
        assert config_manager.enable_versioning is True
        assert config_manager.max_versions == 10
        assert config_manager.get_current_config() is None

    @pytest.mark.asyncio
    async def test_initialize_with_config(self, config_manager, sample_config):
        """Test initialization with initial configuration."""
        success = await config_manager.initialize(sample_config)
        
        assert success is True
        current_config = config_manager.get_current_config()
        assert current_config is not None
        assert current_config.max_processing_time == 3.0
        assert current_config.cache_size == 5000

    @pytest.mark.asyncio
    async def test_initialize_from_environment(self, config_manager):
        """Test initialization from environment variables."""
        with patch.dict('os.environ', {
            'INTELLIGENT_AUTH_MAX_PROCESSING_TIME': '4.0',
            'INTELLIGENT_AUTH_CACHE_SIZE': '8000',
            'INTELLIGENT_AUTH_ENABLE_NLP': 'false'
        }):
            success = await config_manager.initialize()
            
            assert success is True
            current_config = config_manager.get_current_config()
            assert current_config is not None
            assert current_config.max_processing_time == 4.0
            assert current_config.cache_size == 8000
            assert current_config.enable_nlp_analysis is False

    @pytest.mark.asyncio
    async def test_update_config(self, config_manager, sample_config):
        """Test configuration update."""
        await config_manager.initialize()
        
        # Update configuration
        new_config = IntelligentAuthConfig(
            enable_nlp_analysis=False,
            max_processing_time=5.0,
            cache_size=10000
        )
        
        success = await config_manager.update_config(
            new_config, 
            ConfigSource.ENVIRONMENT, 
            "Test update"
        )
        
        assert success is True
        current_config = config_manager.get_current_config()
        assert current_config.enable_nlp_analysis is False
        assert current_config.max_processing_time == 5.0
        assert current_config.cache_size == 10000

    @pytest.mark.asyncio
    async def test_config_versioning(self, config_manager, sample_config):
        """Test configuration versioning."""
        await config_manager.initialize(sample_config)
        
        # Update configuration to create new version
        new_config = IntelligentAuthConfig(max_processing_time=4.0)
        await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Check version history
        versions = config_manager.get_version_history()
        assert len(versions) == 2  # Initial + update
        
        # Check active version
        active_versions = [v for v in versions if v.is_active]
        assert len(active_versions) == 1
        assert active_versions[0].config_data['max_processing_time'] == 4.0

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, config_manager, sample_config):
        """Test configuration rollback."""
        await config_manager.initialize(sample_config)
        
        # Create a new version
        new_config = IntelligentAuthConfig(max_processing_time=4.0)
        await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Get version to rollback to
        versions = config_manager.get_version_history()
        first_version = versions[0]
        
        # Rollback
        success = await config_manager.rollback_to_version(first_version.version_id)
        assert success is True
        
        # Check current configuration
        current_config = config_manager.get_current_config()
        assert current_config.max_processing_time == sample_config.max_processing_time

    @pytest.mark.asyncio
    async def test_load_from_file_json(self, config_manager):
        """Test loading configuration from JSON file."""
        config_data = {
            'enable_nlp_analysis': False,
            'max_processing_time': 6.0,
            'cache_size': 12000
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = await config_manager.load_from_file(temp_path, watch=False)
            
            assert config.enable_nlp_analysis is False
            assert config.max_processing_time == 6.0
            assert config.cache_size == 12000
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_save_to_file_json(self, config_manager, sample_config):
        """Test saving configuration to JSON file."""
        await config_manager.initialize(sample_config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            await config_manager.save_to_file(temp_path)
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['enable_nlp_analysis'] is True
            assert saved_data['max_processing_time'] == 3.0
            assert saved_data['cache_size'] == 5000
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_load_from_environment(self, config_manager):
        """Test loading configuration from environment variables."""
        with patch.dict('os.environ', {
            'INTELLIGENT_AUTH_ENABLE_NLP': 'true',
            'INTELLIGENT_AUTH_MAX_PROCESSING_TIME': '7.0',
            'INTELLIGENT_AUTH_LOW_RISK_THRESHOLD': '0.2',
            'INTELLIGENT_AUTH_HIGH_RISK_THRESHOLD': '0.9'
        }):
            config = await config_manager.load_from_environment()
            
            assert config.enable_nlp_analysis is True
            assert config.max_processing_time == 7.0
            assert config.risk_thresholds.low_risk_threshold == 0.2
            assert config.risk_thresholds.high_risk_threshold == 0.9

    @pytest.mark.asyncio
    async def test_config_validation(self, config_manager):
        """Test configuration validation."""
        # Valid configuration
        valid_config = IntelligentAuthConfig(max_processing_time=5.0)
        is_valid, errors = await config_manager.validate_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = IntelligentAuthConfig(max_processing_time=-1.0)
        is_valid, errors = await config_manager.validate_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
        assert any("max_processing_time must be positive" in error for error in errors)

    @pytest.mark.asyncio
    async def test_change_listeners(self, config_manager, sample_config):
        """Test configuration change listeners."""
        await config_manager.initialize(sample_config)
        
        change_events = []
        
        def change_listener(event: ConfigChangeEvent):
            change_events.append(event)
        
        config_manager.add_change_listener(change_listener)
        
        # Update configuration
        new_config = IntelligentAuthConfig(max_processing_time=4.0)
        await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Check that listener was called
        assert len(change_events) == 1
        event = change_events[0]
        assert event.success is True
        assert event.source == ConfigSource.ENVIRONMENT
        assert 'max_processing_time' in event.changed_keys

    @pytest.mark.asyncio
    async def test_configurable_services(self, config_manager, sample_config):
        """Test configurable service notifications."""
        await config_manager.initialize(sample_config)
        
        # Register mock service
        mock_service = MockConfigurableService()
        config_manager.register_configurable_service(mock_service)
        
        # Update configuration
        new_config = IntelligentAuthConfig(max_processing_time=4.0)
        await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Check that service was notified
        assert mock_service.update_config_called is True
        assert mock_service.last_config.max_processing_time == 4.0

    @pytest.mark.asyncio
    async def test_change_history(self, config_manager, sample_config):
        """Test configuration change history tracking."""
        await config_manager.initialize(sample_config)
        
        # Make several changes
        for i in range(3):
            new_config = IntelligentAuthConfig(max_processing_time=float(i + 2))
            await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Check change history
        history = config_manager.get_change_history()
        assert len(history) == 4  # Initial + 3 updates
        
        # Check that changes are recorded correctly
        for i, event in enumerate(history[1:], 1):  # Skip initial
            assert event.new_config.max_processing_time == float(i + 1)

    def test_configuration_summary(self, config_manager):
        """Test configuration summary."""
        summary = config_manager.get_configuration_summary()
        
        assert 'has_current_config' in summary
        assert 'total_versions' in summary
        assert 'total_changes' in summary
        assert 'hot_reload_enabled' in summary
        assert 'versioning_enabled' in summary
        
        assert summary['has_current_config'] is False
        assert summary['total_versions'] == 0
        assert summary['versioning_enabled'] is True

    @pytest.mark.asyncio
    async def test_invalid_config_update(self, config_manager):
        """Test handling of invalid configuration updates."""
        await config_manager.initialize()
        
        # Create invalid configuration
        invalid_config = IntelligentAuthConfig(max_processing_time=-1.0)
        
        # Attempt to update with invalid config
        success = await config_manager.update_config(invalid_config, ConfigSource.ENVIRONMENT)
        
        assert success is False
        
        # Check that change was recorded as failed
        history = config_manager.get_change_history()
        failed_changes = [event for event in history if not event.success]
        assert len(failed_changes) > 0

    @pytest.mark.asyncio
    async def test_version_limit(self, config_manager, sample_config):
        """Test version history limit."""
        config_manager.max_versions = 3
        await config_manager.initialize(sample_config)
        
        # Create more versions than the limit
        for i in range(5):
            new_config = IntelligentAuthConfig(max_processing_time=float(i + 2))
            await config_manager.update_config(new_config, ConfigSource.ENVIRONMENT)
        
        # Check that only max_versions are kept
        versions = config_manager.get_version_history()
        assert len(versions) <= config_manager.max_versions

    @pytest.mark.asyncio
    async def test_shutdown(self, config_manager, sample_config):
        """Test configuration manager shutdown."""
        await config_manager.initialize(sample_config)
        
        # Add some data
        mock_service = MockConfigurableService()
        config_manager.register_configurable_service(mock_service)
        
        # Shutdown
        await config_manager.shutdown()
        
        # Check that data is cleared
        summary = config_manager.get_configuration_summary()
        assert summary['total_versions'] == 0
        assert summary['configurable_services'] == 0

    def test_env_value_conversion(self, config_manager):
        """Test environment value conversion."""
        # Test boolean conversion
        assert config_manager._convert_env_value('true') is True
        assert config_manager._convert_env_value('false') is False
        assert config_manager._convert_env_value('True') is True
        
        # Test integer conversion
        assert config_manager._convert_env_value('123') == 123
        assert config_manager._convert_env_value('-456') == -456
        
        # Test float conversion
        assert config_manager._convert_env_value('3.14') == 3.14
        assert config_manager._convert_env_value('-2.5') == -2.5
        
        # Test string fallback
        assert config_manager._convert_env_value('hello') == 'hello'
        assert config_manager._convert_env_value('') == ''

    def test_nested_value_setting(self, config_manager):
        """Test setting nested values in configuration."""
        data = {}
        
        # Set simple value
        config_manager._set_nested_value(data, 'simple', 'value')
        assert data['simple'] == 'value'
        
        # Set nested value
        config_manager._set_nested_value(data, 'nested.key', 'nested_value')
        assert data['nested']['key'] == 'nested_value'
        
        # Set deeply nested value
        config_manager._set_nested_value(data, 'deep.nested.key', 'deep_value')
        assert data['deep']['nested']['key'] == 'deep_value'

    def test_changed_keys_detection(self, config_manager):
        """Test detection of changed configuration keys."""
        old_config = IntelligentAuthConfig(
            enable_nlp_analysis=True,
            max_processing_time=3.0,
            cache_size=5000
        )
        
        new_config = IntelligentAuthConfig(
            enable_nlp_analysis=False,  # Changed
            max_processing_time=3.0,   # Unchanged
            cache_size=8000            # Changed
        )
        
        changed_keys = config_manager._get_changed_keys(old_config, new_config)
        
        assert 'enable_nlp_analysis' in changed_keys
        assert 'cache_size' in changed_keys
        assert 'max_processing_time' not in changed_keys

    def test_file_format_detection(self, config_manager):
        """Test file format detection."""
        assert config_manager._detect_file_format(Path('config.json')) == ConfigFormat.JSON
        assert config_manager._detect_file_format(Path('config.yaml')) == ConfigFormat.YAML
        assert config_manager._detect_file_format(Path('config.yml')) == ConfigFormat.YAML
        assert config_manager._detect_file_format(Path('config.txt')) == ConfigFormat.JSON  # Default


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.mark.asyncio
    async def test_load_config_from_file(self):
        """Test utility function for loading config from file."""
        config_data = {
            'enable_nlp_analysis': True,
            'max_processing_time': 5.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = await load_config_from_file(temp_path)
            assert config.enable_nlp_analysis is True
            assert config.max_processing_time == 5.0
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_save_config_to_file(self):
        """Test utility function for saving config to file."""
        config = IntelligentAuthConfig(
            enable_nlp_analysis=False,
            max_processing_time=6.0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            await save_config_to_file(config, temp_path)
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['enable_nlp_analysis'] is False
            assert saved_data['max_processing_time'] == 6.0
        finally:
            temp_path.unlink()

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = create_default_config()
        
        assert isinstance(config, IntelligentAuthConfig)
        assert config.validate() is True


class TestConfigVersion:
    """Test ConfigVersion dataclass."""

    def test_config_version_serialization(self):
        """Test ConfigVersion serialization."""
        version = ConfigVersion(
            version_id="v1",
            timestamp=datetime.now(),
            source=ConfigSource.FILE,
            config_data={'key': 'value'},
            description="Test version",
            is_active=True
        )
        
        # Test to_dict
        version_dict = version.to_dict()
        assert version_dict['version_id'] == "v1"
        assert version_dict['source'] == "file"
        assert version_dict['config_data'] == {'key': 'value'}
        assert version_dict['is_active'] is True
        
        # Test from_dict
        restored_version = ConfigVersion.from_dict(version_dict)
        assert restored_version.version_id == version.version_id
        assert restored_version.source == version.source
        assert restored_version.config_data == version.config_data
        assert restored_version.is_active == version.is_active


class TestConfigChangeEvent:
    """Test ConfigChangeEvent dataclass."""

    def test_config_change_event_serialization(self):
        """Test ConfigChangeEvent serialization."""
        old_config = IntelligentAuthConfig(max_processing_time=3.0)
        new_config = IntelligentAuthConfig(max_processing_time=4.0)
        
        event = ConfigChangeEvent(
            timestamp=datetime.now(),
            old_config=old_config,
            new_config=new_config,
            source=ConfigSource.ENVIRONMENT,
            changed_keys=['max_processing_time'],
            success=True
        )
        
        # Test to_dict
        event_dict = event.to_dict()
        assert event_dict['source'] == "environment"
        assert event_dict['changed_keys'] == ['max_processing_time']
        assert event_dict['success'] is True
        assert event_dict['old_config'] is not None
        assert event_dict['new_config'] is not None


if __name__ == "__main__":
    pytest.main([__file__])