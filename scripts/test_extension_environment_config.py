#!/usr/bin/env python3
"""
Test script for extension environment configuration implementation.
Validates all components of the environment-aware configuration system.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import sys
import json
import yaml
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server.extension_environment_config import (
    ExtensionEnvironmentConfigManager,
    SecureCredentialManager,
    Environment,
    ExtensionEnvironmentConfig
)
from server.extension_config_validator import (
    ExtensionConfigValidator,
    ExtensionConfigHealthChecker,
    ValidationSeverity
)
from server.extension_config_hot_reload import (
    ExtensionConfigHotReloader,
    ReloadTrigger
)
from server.extension_config_integration import (
    ExtensionConfigIntegration,
    detect_runtime_environment,
    get_environment_specific_config
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtensionConfigTestSuite:
    """Comprehensive test suite for extension configuration system."""
    
    def __init__(self):
        self.temp_dir = None
        self.config_manager = None
        self.test_results = []
    
    def setup(self):
        """Setup test environment."""
        try:
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix="extension_config_test_"))
            logger.info(f"Created test directory: {self.temp_dir}")
            
            # Create config directories
            config_dir = self.temp_dir / "config" / "extensions"
            credentials_dir = self.temp_dir / "config" / "extensions" / "credentials"
            config_dir.mkdir(parents=True, exist_ok=True)
            credentials_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test configuration files
            self._create_test_config_files(config_dir)
            
            # Initialize configuration manager
            self.config_manager = ExtensionEnvironmentConfigManager(
                config_dir=str(config_dir),
                credentials_dir=str(credentials_dir),
                enable_hot_reload=False  # Disable for testing
            )
            
            logger.info("Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Test setup failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup test environment."""
        try:
            if self.config_manager:
                self.config_manager.stop_services()
            
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("Test environment cleaned up")
                
        except Exception as e:
            logger.error(f"Test cleanup failed: {e}")
    
    def _create_test_config_files(self, config_dir: Path):
        """Create test configuration files."""
        try:
            # Development config
            dev_config = {
                'auth_enabled': True,
                'jwt_algorithm': 'HS256',
                'access_token_expire_minutes': 120,
                'service_token_expire_minutes': 60,
                'auth_mode': 'development',
                'dev_bypass_enabled': True,
                'require_https': False,
                'rate_limit_per_minute': 1000,
                'burst_limit': 100,
                'max_failed_attempts': 10,
                'lockout_duration_minutes': 1,
                'health_check_enabled': True,
                'health_check_interval_seconds': 60,
                'health_check_timeout_seconds': 10,
                'log_level': 'DEBUG',
                'enable_debug_logging': True,
                'log_sensitive_data': True
            }
            
            with open(config_dir / "development.yaml", 'w') as f:
                yaml.dump(dev_config, f, default_flow_style=False, indent=2)
            
            # Production config
            prod_config = {
                'auth_enabled': True,
                'jwt_algorithm': 'HS256',
                'access_token_expire_minutes': 60,
                'service_token_expire_minutes': 30,
                'auth_mode': 'strict',
                'dev_bypass_enabled': False,
                'require_https': True,
                'rate_limit_per_minute': 100,
                'burst_limit': 20,
                'max_failed_attempts': 3,
                'lockout_duration_minutes': 30,
                'health_check_enabled': True,
                'health_check_interval_seconds': 30,
                'health_check_timeout_seconds': 5,
                'log_level': 'INFO',
                'enable_debug_logging': False,
                'log_sensitive_data': False
            }
            
            with open(config_dir / "production.yaml", 'w') as f:
                yaml.dump(prod_config, f, default_flow_style=False, indent=2)
            
            logger.info("Created test configuration files")
            
        except Exception as e:
            logger.error(f"Failed to create test config files: {e}")
            raise
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        try:
            logger.info(f"Running test: {test_name}")
            start_time = datetime.utcnow()
            
            result = test_func()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.test_results.append({
                'name': test_name,
                'status': 'PASS' if result else 'FAIL',
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            })
            
            logger.info(f"Test {test_name}: {'PASS' if result else 'FAIL'} ({duration:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            self.test_results.append({
                'name': test_name,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False
    
    async def run_async_test(self, test_name: str, test_func):
        """Run an async test and record results."""
        try:
            logger.info(f"Running async test: {test_name}")
            start_time = datetime.utcnow()
            
            result = await test_func()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.test_results.append({
                'name': test_name,
                'status': 'PASS' if result else 'FAIL',
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            })
            
            logger.info(f"Test {test_name}: {'PASS' if result else 'FAIL'} ({duration:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            self.test_results.append({
                'name': test_name,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        try:
            # Check if manager is initialized
            if not self.config_manager:
                return False
            
            # Check if configurations are loaded
            if len(self.config_manager.configurations) == 0:
                return False
            
            # Check if current environment is detected
            if not self.config_manager.current_environment:
                return False
            
            logger.info(f"Config manager initialized with {len(self.config_manager.configurations)} environments")
            logger.info(f"Current environment: {self.config_manager.current_environment.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Config manager initialization test failed: {e}")
            return False
    
    def test_environment_specific_configs(self):
        """Test environment-specific configuration loading."""
        try:
            # Test development config
            dev_config = self.config_manager.get_config(Environment.DEVELOPMENT)
            if not dev_config:
                return False
            
            if dev_config.auth_mode != 'development':
                logger.error(f"Expected development auth_mode, got: {dev_config.auth_mode}")
                return False
            
            if not dev_config.dev_bypass_enabled:
                logger.error("Expected dev_bypass_enabled to be True in development")
                return False
            
            # Test production config
            prod_config = self.config_manager.get_config(Environment.PRODUCTION)
            if not prod_config:
                return False
            
            if prod_config.auth_mode != 'strict':
                logger.error(f"Expected strict auth_mode in production, got: {prod_config.auth_mode}")
                return False
            
            if prod_config.dev_bypass_enabled:
                logger.error("Expected dev_bypass_enabled to be False in production")
                return False
            
            logger.info("Environment-specific configurations loaded correctly")
            return True
            
        except Exception as e:
            logger.error(f"Environment-specific config test failed: {e}")
            return False
    
    def test_credential_management(self):
        """Test secure credential storage and retrieval."""
        try:
            credentials_manager = self.config_manager.credentials_manager
            
            # Store a test credential
            success = credentials_manager.store_credential(
                name="test_secret",
                value="test_secret_value_123",
                environment="development",
                description="Test credential"
            )
            
            if not success:
                logger.error("Failed to store test credential")
                return False
            
            # Retrieve the credential
            retrieved_value = credentials_manager.get_credential("test_secret", "development")
            if retrieved_value != "test_secret_value_123":
                logger.error(f"Retrieved credential value mismatch: {retrieved_value}")
                return False
            
            # List credentials
            credentials_list = credentials_manager.list_credentials("development")
            if not any(c['name'] == 'test_secret' for c in credentials_list):
                logger.error("Test credential not found in list")
                return False
            
            # Test credential rotation
            rotation_success = credentials_manager.rotate_credential("test_secret")
            if not rotation_success:
                logger.error("Failed to rotate test credential")
                return False
            
            # Verify credential was rotated
            new_value = credentials_manager.get_credential("test_secret", "development")
            if new_value == "test_secret_value_123":
                logger.error("Credential was not rotated")
                return False
            
            logger.info("Credential management tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Credential management test failed: {e}")
            return False
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        try:
            validator = ExtensionConfigValidator()
            
            # Test valid configuration
            valid_config = self.config_manager.get_config(Environment.DEVELOPMENT)
            issues = validator.validate_config(valid_config)
            
            # Should have minimal issues for development config
            critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
            if critical_issues:
                logger.error(f"Unexpected critical issues in development config: {len(critical_issues)}")
                return False
            
            # Test invalid configuration
            invalid_config = ExtensionEnvironmentConfig(
                environment=Environment.PRODUCTION,
                secret_key="",  # Invalid: empty secret key
                access_token_expire_minutes=-1,  # Invalid: negative expiration
                auth_mode="invalid_mode"  # Invalid: unknown auth mode
            )
            
            invalid_issues = validator.validate_config(invalid_config)
            critical_invalid = [i for i in invalid_issues if i.severity == ValidationSeverity.CRITICAL]
            error_invalid = [i for i in invalid_issues if i.severity == ValidationSeverity.ERROR]
            
            if len(critical_invalid) == 0 and len(error_invalid) == 0:
                logger.error("Expected validation issues for invalid config")
                return False
            
            logger.info(f"Configuration validation found {len(invalid_issues)} issues in invalid config")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation test failed: {e}")
            return False
    
    async def test_health_checks(self):
        """Test configuration health checks."""
        try:
            health_checker = ExtensionConfigHealthChecker()
            
            # Run health checks
            health_result = await health_checker.run_all_health_checks()
            
            if not health_result:
                logger.error("Health check returned no results")
                return False
            
            if 'overall_status' not in health_result:
                logger.error("Health check missing overall_status")
                return False
            
            if 'results' not in health_result:
                logger.error("Health check missing individual results")
                return False
            
            # Check that we have some health check results
            results = health_result['results']
            if len(results) == 0:
                logger.error("No individual health check results")
                return False
            
            logger.info(f"Health checks completed: {health_result['overall_status']}")
            logger.info(f"Individual checks: {len(results)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Health checks test failed: {e}")
            return False
    
    async def test_hot_reload_system(self):
        """Test configuration hot-reload system."""
        try:
            # Create hot-reloader with file watching disabled for testing
            hot_reloader = ExtensionConfigHotReloader(self.config_manager)
            
            # Test reload without changes
            reload_event = await hot_reloader.reload_configuration(
                environment=Environment.DEVELOPMENT,
                trigger=ReloadTrigger.API_REQUEST
            )
            
            if not reload_event:
                logger.error("Hot reload returned no event")
                return False
            
            if reload_event.status.value not in ['success', 'failed']:
                logger.error(f"Unexpected reload status: {reload_event.status}")
                return False
            
            # Test reload history
            history = hot_reloader.get_reload_history(10)
            if len(history) == 0:
                logger.error("No reload history found")
                return False
            
            # Test snapshots
            snapshots = hot_reloader.get_snapshots(Environment.DEVELOPMENT, 5)
            if len(snapshots) == 0:
                logger.error("No configuration snapshots found")
                return False
            
            # Test status
            status = hot_reloader.get_status()
            if 'reload_in_progress' not in status:
                logger.error("Hot reload status missing required fields")
                return False
            
            logger.info("Hot-reload system tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Hot-reload system test failed: {e}")
            return False
    
    def test_integration_utilities(self):
        """Test integration utilities."""
        try:
            # Test environment detection
            env = detect_runtime_environment()
            if not env:
                logger.error("Environment detection returned empty value")
                return False
            
            # Test environment-specific config
            env_config = get_environment_specific_config()
            if not env_config or 'environment' not in env_config:
                logger.error("Environment-specific config missing required fields")
                return False
            
            # Test integration class
            integration = ExtensionConfigIntegration()
            status = integration.get_status()
            
            if 'initialized' not in status:
                logger.error("Integration status missing required fields")
                return False
            
            logger.info(f"Integration utilities tests passed (env: {env})")
            return True
            
        except Exception as e:
            logger.error(f"Integration utilities test failed: {e}")
            return False
    
    def test_config_update_and_persistence(self):
        """Test configuration updates and file persistence."""
        try:
            # Update configuration
            updates = {
                'rate_limit_per_minute': 500,
                'burst_limit': 50,
                'log_level': 'WARNING'
            }
            
            success = self.config_manager.update_config(
                Environment.DEVELOPMENT,
                updates,
                save_to_file=True
            )
            
            if not success:
                logger.error("Configuration update failed")
                return False
            
            # Verify updates were applied
            updated_config = self.config_manager.get_config(Environment.DEVELOPMENT)
            
            if updated_config.rate_limit_per_minute != 500:
                logger.error(f"Rate limit not updated: {updated_config.rate_limit_per_minute}")
                return False
            
            if updated_config.burst_limit != 50:
                logger.error(f"Burst limit not updated: {updated_config.burst_limit}")
                return False
            
            if updated_config.log_level != 'WARNING':
                logger.error(f"Log level not updated: {updated_config.log_level}")
                return False
            
            # Verify file was saved (check if file exists and has content)
            config_file = Path(self.config_manager.config_dir) / "development.yaml"
            if not config_file.exists():
                logger.error("Configuration file was not saved")
                return False
            
            with open(config_file, 'r') as f:
                saved_config = yaml.safe_load(f)
                if saved_config.get('rate_limit_per_minute') != 500:
                    logger.error("Configuration not properly saved to file")
                    return False
            
            logger.info("Configuration update and persistence tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Config update and persistence test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in the test suite."""
        logger.info("Starting extension configuration test suite")
        
        # Setup test environment
        if not self.setup():
            logger.error("Test setup failed, aborting")
            return False
        
        try:
            # Run synchronous tests
            sync_tests = [
                ("Config Manager Initialization", self.test_config_manager_initialization),
                ("Environment-Specific Configs", self.test_environment_specific_configs),
                ("Credential Management", self.test_credential_management),
                ("Configuration Validation", self.test_configuration_validation),
                ("Integration Utilities", self.test_integration_utilities),
                ("Config Update and Persistence", self.test_config_update_and_persistence),
            ]
            
            for test_name, test_func in sync_tests:
                self.run_test(test_name, test_func)
            
            # Run asynchronous tests
            async_tests = [
                ("Health Checks", self.test_health_checks),
                ("Hot-Reload System", self.test_hot_reload_system),
            ]
            
            for test_name, test_func in async_tests:
                await self.run_async_test(test_name, test_func)
            
            # Print test results
            self.print_test_results()
            
            # Return overall success
            failed_tests = [r for r in self.test_results if r['status'] != 'PASS']
            return len(failed_tests) == 0
            
        finally:
            self.cleanup()
    
    def print_test_results(self):
        """Print comprehensive test results."""
        logger.info("\n" + "="*60)
        logger.info("EXTENSION CONFIGURATION TEST RESULTS")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Errors: {error_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nDetailed Results:")
        logger.info("-" * 60)
        
        for result in self.test_results:
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            duration = result.get('duration_seconds', 0)
            logger.info(f"{status_symbol} {result['name']} ({duration:.2f}s)")
            
            if result['status'] == 'ERROR' and 'error' in result:
                logger.info(f"    Error: {result['error']}")
        
        logger.info("="*60)
        
        if failed_tests == 0 and error_tests == 0:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.info(f"❌ {failed_tests + error_tests} TESTS FAILED")


async def main():
    """Main test execution function."""
    try:
        # Create and run test suite
        test_suite = ExtensionConfigTestSuite()
        success = await test_suite.run_all_tests()
        
        if success:
            logger.info("✅ Extension configuration implementation is working correctly!")
            return 0
        else:
            logger.error("❌ Extension configuration implementation has issues!")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)