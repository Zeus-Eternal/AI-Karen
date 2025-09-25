"""
Unit tests for Enhanced Configuration Manager

Tests for the enhanced configuration manager addressing requirements 9.1-9.5
from the system-warnings-errors-fix specification.
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.ai_karen_engine.config.enhanced_config_manager import (
    ConfigurationManager,
    ConfigValidationResult,
    ConfigIssue,
    ConfigValidationSeverity,
    ConfigSource,
    EnvironmentVariableConfig,
    ConfigurationError,
    get_enhanced_config_manager,
    initialize_enhanced_config_manager
)


class TestConfigurationManager:
    """Test cases for ConfigurationManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.manager = ConfigurationManager(
            config_path=self.config_path,
            enable_migration=True,
            enable_health_checks=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test configuration manager initialization"""
        assert self.manager.config_path == self.config_path
        assert self.manager.enable_migration is True
        assert self.manager.enable_health_checks is True
        assert len(self.manager.env_mappings) > 0
        assert self.manager._config is None
    
    def test_load_config_with_defaults(self):
        """Test loading configuration with default values"""
        config = self.manager.load_config()
        
        assert config is not None
        assert 'environment' in config
        assert 'database' in config
        assert 'redis' in config
        assert 'llm' in config
        assert 'security' in config
        
        # Check default values
        assert config['environment'] == 'development'
        assert config['database']['host'] == 'localhost'
        assert config['database']['port'] == 5432
    
    def test_load_config_from_file(self):
        """Test loading configuration from JSON file"""
        test_config = {
            'environment': 'test',
            'database': {
                'host': 'test-db',
                'port': 3306
            },
            'custom_setting': 'test_value'
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        config = self.manager.load_config()
        
        assert config['environment'] == 'test'
        assert config['database']['host'] == 'test-db'
        assert config['database']['port'] == 3306
        assert config['custom_setting'] == 'test_value'
        
        # Ensure defaults are still present for missing keys
        assert 'redis' in config
        assert config['redis']['host'] == 'localhost'
    
    @patch.dict(os.environ, {
        'KARI_ENV': 'production',
        'DB_HOST': 'prod-db',
        'DB_PORT': '5433',
        'REDIS_PASSWORD': 'secret123',
        'KARI_DEBUG': 'true'
    })
    def test_load_config_with_environment_variables(self):
        """Test loading configuration with environment variable overrides"""
        config = self.manager.load_config()
        
        assert config['environment'] == 'production'
        assert config['database']['host'] == 'prod-db'
        assert config['database']['port'] == 5433
        assert config['redis']['password'] == 'secret123'
        assert config['debug'] is True
    
    def test_validate_environment_success(self):
        """Test successful environment validation"""
        with patch.dict(os.environ, {
            'JWT_SECRET': 'test-secret-key',
            'DB_HOST': 'localhost'
        }):
            result = self.manager.validate_environment()
            
            assert isinstance(result, ConfigValidationResult)
            # Should have warnings for missing optional vars but no errors
            assert not result.has_errors
    
    def test_validate_environment_missing_required(self):
        """Test environment validation with missing required variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = self.manager.validate_environment()
            
            assert isinstance(result, ConfigValidationResult)
            assert result.has_errors
            assert 'JWT_SECRET' in result.missing_required
            
            # Check for specific error issue
            jwt_issues = [issue for issue in result.issues if issue.key == 'JWT_SECRET']
            assert len(jwt_issues) > 0
            assert jwt_issues[0].severity == ConfigValidationSeverity.ERROR
    
    def test_validate_environment_invalid_type(self):
        """Test environment validation with invalid value types"""
        with patch.dict(os.environ, {
            'DB_PORT': 'not-a-number',
            'KARI_DEBUG': 'maybe'
        }):
            result = self.manager.validate_environment()
            
            assert result.has_errors
            
            # Check for type conversion errors
            port_issues = [issue for issue in result.issues if issue.key == 'DB_PORT']
            assert len(port_issues) > 0
            assert port_issues[0].severity == ConfigValidationSeverity.ERROR
    
    def test_migrate_pydantic_config(self):
        """Test Pydantic V1 to V2 migration"""
        config_with_deprecated = {
            'model_config': {
                'schema_extra': {'example': 'value'}
            },
            'other_setting': 'value'
        }
        
        migrated_config = self.manager.migrate_pydantic_config(config_with_deprecated)
        
        # Check that schema_extra was replaced with json_schema_extra
        config_str = json.dumps(migrated_config)
        assert 'json_schema_extra' in config_str
        # Check that the standalone 'schema_extra' key was replaced
        assert '"schema_extra"' not in config_str
    
    def test_get_with_fallback(self):
        """Test getting configuration values with fallback"""
        test_config = {
            'database': {
                'host': 'test-host',
                'nested': {
                    'deep_value': 'found'
                }
            }
        }
        
        self.manager._config = test_config
        
        # Test existing values
        assert self.manager.get_with_fallback('database.host') == 'test-host'
        assert self.manager.get_with_fallback('database.nested.deep_value') == 'found'
        
        # Test missing values with fallback
        assert self.manager.get_with_fallback('missing.key', 'default') == 'default'
        assert self.manager.get_with_fallback('database.missing', 'fallback') == 'fallback'
    
    def test_report_missing_configs(self):
        """Test reporting missing configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            missing_configs = self.manager.report_missing_configs()
            
            assert isinstance(missing_configs, list)
            assert len(missing_configs) > 0
            
            # Should include JWT_SECRET as it's required
            jwt_missing = [config for config in missing_configs if config.key == 'JWT_SECRET']
            assert len(jwt_missing) > 0
    
    def test_perform_health_checks(self):
        """Test configuration health checks"""
        # Create a config file
        with open(self.config_path, 'w') as f:
            json.dump({'test': 'config'}, f)
        
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret'}):
            health_result = self.manager.perform_health_checks()
            
            assert isinstance(health_result, dict)
            assert 'timestamp' in health_result
            assert 'overall_status' in health_result
            assert 'checks' in health_result
            
            # Check specific health checks
            assert 'config_file' in health_result['checks']
            assert 'environment' in health_result['checks']
            assert 'critical_configs' in health_result['checks']
            
            # Config file should be healthy since we created it
            assert health_result['checks']['config_file']['status'] == 'healthy'
    
    def test_change_listeners(self):
        """Test configuration change listeners"""
        listener_called = threading.Event()
        received_config = {}
        
        def test_listener(config):
            received_config.update(config)
            listener_called.set()
        
        self.manager.add_change_listener(test_listener)
        
        # Load config should trigger listener
        config = self.manager.load_config()
        
        # Wait for listener to be called
        assert listener_called.wait(timeout=1.0)
        assert len(received_config) > 0
        assert received_config['environment'] == config['environment']
        
        # Test removing listener
        self.manager.remove_change_listener(test_listener)
        assert test_listener not in self.manager._change_listeners
    
    def test_configuration_summary(self):
        """Test getting configuration summary"""
        summary = self.manager.get_configuration_summary()
        
        assert isinstance(summary, dict)
        assert 'config_loaded' in summary
        assert 'config_path' in summary
        assert 'config_exists' in summary
        assert 'validation_status' in summary
        assert 'env_mappings_count' in summary
        assert 'migration_enabled' in summary
        assert 'health_checks_enabled' in summary
        
        # Initially config should not be loaded
        assert summary['config_loaded'] is False
        assert summary['migration_enabled'] is True
        assert summary['health_checks_enabled'] is True
    
    def test_thread_safety(self):
        """Test thread safety of configuration manager"""
        results = []
        errors = []
        
        def load_config_worker():
            try:
                config = self.manager.load_config()
                results.append(config)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_config_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    def test_yaml_config_loading(self):
        """Test loading YAML configuration files"""
        yaml_config_path = Path(self.temp_dir) / "test_config.yaml"
        yaml_content = """
environment: test
database:
  host: yaml-db
  port: 3307
custom_list:
  - item1
  - item2
"""
        
        with open(yaml_config_path, 'w') as f:
            f.write(yaml_content)
        
        manager = ConfigurationManager(config_path=yaml_config_path)
        
        try:
            config = manager.load_config()
            assert config['environment'] == 'test'
            assert config['database']['host'] == 'yaml-db'
            assert config['database']['port'] == 3307
            assert config['custom_list'] == ['item1', 'item2']
        except ImportError:
            # PyYAML not available, should fall back to JSON parsing and fail
            pytest.skip("PyYAML not available for YAML config testing")
    
    def test_production_validation(self):
        """Test production-specific validation"""
        prod_config = {
            'environment': 'production',
            'security': {
                'jwt_secret': 'change-me-in-production'  # This should trigger error
            }
        }
        
        self.manager._config = prod_config
        validation_result = self.manager._validate_config(prod_config)
        
        assert validation_result.has_errors
        
        # Should have critical error for default JWT secret in production
        jwt_issues = [issue for issue in validation_result.issues 
                     if issue.key == 'security.jwt_secret']
        assert len(jwt_issues) > 0
        assert jwt_issues[0].severity == ConfigValidationSeverity.CRITICAL


class TestEnvironmentVariableConfig:
    """Test cases for EnvironmentVariableConfig"""
    
    def test_environment_variable_config_creation(self):
        """Test creating environment variable configuration"""
        env_config = EnvironmentVariableConfig(
            env_var="TEST_VAR",
            config_path="test.path",
            required=True,
            default_value="default",
            value_type="str",
            description="Test variable"
        )
        
        assert env_config.env_var == "TEST_VAR"
        assert env_config.config_path == "test.path"
        assert env_config.required is True
        assert env_config.default_value == "default"
        assert env_config.value_type == "str"
        assert env_config.description == "Test variable"
    
    def test_environment_variable_config_defaults(self):
        """Test default values for environment variable configuration"""
        env_config = EnvironmentVariableConfig(
            env_var="TEST_VAR",
            config_path="test.path"
        )
        
        assert env_config.required is False
        assert env_config.default_value is None
        assert env_config.value_type == "str"
        assert env_config.description == ""
        assert env_config.validation_pattern is None


class TestConfigValidationResult:
    """Test cases for ConfigValidationResult"""
    
    def test_validation_result_properties(self):
        """Test validation result properties"""
        issues = [
            ConfigIssue(
                key="test1",
                issue_type="error",
                message="Error message",
                suggested_fix="Fix it",
                severity=ConfigValidationSeverity.ERROR,
                source=ConfigSource.FILE
            ),
            ConfigIssue(
                key="test2",
                issue_type="warning",
                message="Warning message",
                suggested_fix="Consider fixing",
                severity=ConfigValidationSeverity.WARNING,
                source=ConfigSource.ENVIRONMENT
            )
        ]
        
        result = ConfigValidationResult(
            is_valid=False,
            issues=issues
        )
        
        assert result.has_errors is True
        assert result.has_warnings is True
        
        # Test with no errors
        warning_only_result = ConfigValidationResult(
            is_valid=True,
            issues=[issues[1]]  # Only warning
        )
        
        assert warning_only_result.has_errors is False
        assert warning_only_result.has_warnings is True


class TestGlobalConfigManager:
    """Test cases for global configuration manager functions"""
    
    def test_get_enhanced_config_manager(self):
        """Test getting global configuration manager"""
        manager1 = get_enhanced_config_manager()
        manager2 = get_enhanced_config_manager()
        
        # Should return the same instance
        assert manager1 is manager2
        assert isinstance(manager1, ConfigurationManager)
    
    def test_initialize_enhanced_config_manager(self):
        """Test initializing global configuration manager"""
        temp_dir = tempfile.mkdtemp()
        config_path = str(Path(temp_dir) / "global_test_config.json")
        
        try:
            manager = initialize_enhanced_config_manager(config_path=config_path)
            
            assert isinstance(manager, ConfigurationManager)
            assert str(manager.config_path) == config_path
            
            # Should be the same as get_enhanced_config_manager
            assert get_enhanced_config_manager() is manager
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestConfigurationIntegration:
    """Integration tests for configuration manager"""
    
    def test_full_configuration_lifecycle(self):
        """Test complete configuration lifecycle"""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "integration_config.json"
        
        try:
            # Create initial config file
            initial_config = {
                'environment': 'test',
                'database': {
                    'host': 'initial-db'
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(initial_config, f)
            
            # Initialize manager
            manager = ConfigurationManager(config_path=config_path)
            
            # Set up environment variables
            with patch.dict(os.environ, {
                'DB_PORT': '5434',
                'JWT_SECRET': 'integration-test-secret',
                'REDIS_PASSWORD': 'redis-secret'
            }):
                # Load configuration
                config = manager.load_config()
                
                # Verify file config was loaded
                assert config['environment'] == 'test'
                assert config['database']['host'] == 'initial-db'
                
                # Verify environment overrides
                assert config['database']['port'] == 5434
                assert config['security']['jwt_secret'] == 'integration-test-secret'
                assert config['redis']['password'] == 'redis-secret'
                
                # Test validation
                validation_result = manager.validate_environment()
                assert validation_result.is_valid
                
                # Test health checks
                health_result = manager.perform_health_checks()
                assert health_result['overall_status'] in ['healthy', 'warning']
                
                # Test configuration access
                assert manager.get_with_fallback('database.host') == 'initial-db'
                assert manager.get_with_fallback('database.port') == 5434
                assert manager.get_with_fallback('nonexistent.key', 'default') == 'default'
                
                # Test summary
                summary = manager.get_configuration_summary()
                assert summary['config_loaded'] is True
                assert summary['config_exists'] is True
                
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "error_test_config.json"
        
        try:
            # Test with invalid JSON file
            with open(config_path, 'w') as f:
                f.write("{ invalid json content")
            
            manager = ConfigurationManager(config_path=config_path)
            
            # Should still load with defaults despite invalid file
            config = manager.load_config()
            assert config is not None
            assert 'environment' in config
            
            # Test with missing required environment variables
            with patch.dict(os.environ, {}, clear=True):
                validation_result = manager.validate_environment()
                assert validation_result.has_errors
                assert len(validation_result.missing_required) > 0
            
            # Test health checks with issues
            health_result = manager.perform_health_checks()
            assert 'checks' in health_result
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__])