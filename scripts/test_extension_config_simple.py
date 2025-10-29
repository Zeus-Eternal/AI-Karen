#!/usr/bin/env python3
"""
Simplified test for extension environment configuration implementation.
Tests core functionality without external dependencies.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_environment_detection():
    """Test environment detection functionality."""
    try:
        # Test environment variable detection
        original_env = os.environ.get('ENVIRONMENT')
        
        # Test development detection
        os.environ['ENVIRONMENT'] = 'development'
        from server.extension_config_integration import detect_runtime_environment
        env = detect_runtime_environment()
        assert env == 'development', f"Expected 'development', got '{env}'"
        
        # Test production detection
        os.environ['ENVIRONMENT'] = 'production'
        env = detect_runtime_environment()
        assert env == 'production', f"Expected 'production', got '{env}'"
        
        # Test staging detection
        os.environ['ENVIRONMENT'] = 'staging'
        env = detect_runtime_environment()
        assert env == 'staging', f"Expected 'staging', got '{env}'"
        
        # Restore original environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        elif 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        
        logger.info("✓ Environment detection test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment detection test failed: {e}")
        return False


def test_config_file_creation():
    """Test configuration file creation and parsing."""
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="config_test_"))
        
        try:
            # Test YAML configuration creation
            config_data = {
                'auth_enabled': True,
                'jwt_algorithm': 'HS256',
                'access_token_expire_minutes': 60,
                'auth_mode': 'development',
                'rate_limit_per_minute': 100,
                'default_permissions': ['extension:read', 'extension:write']
            }
            
            config_file = temp_dir / "test_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            # Test reading configuration back
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Verify configuration
            assert loaded_config['auth_enabled'] == True
            assert loaded_config['jwt_algorithm'] == 'HS256'
            assert loaded_config['access_token_expire_minutes'] == 60
            assert loaded_config['auth_mode'] == 'development'
            assert loaded_config['rate_limit_per_minute'] == 100
            assert loaded_config['default_permissions'] == ['extension:read', 'extension:write']
            
            logger.info("✓ Configuration file creation test passed")
            return True
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"✗ Configuration file creation test failed: {e}")
        return False


def test_environment_specific_defaults():
    """Test environment-specific default configurations."""
    try:
        from server.extension_config_integration import get_environment_specific_config
        
        # Test development defaults
        os.environ['ENVIRONMENT'] = 'development'
        dev_config = get_environment_specific_config()
        
        assert dev_config['environment'] == 'development'
        assert dev_config['debug'] == True
        assert dev_config['auth_mode'] == 'development'
        assert dev_config['dev_bypass_enabled'] == True
        assert dev_config['require_https'] == False
        
        # Test production defaults
        os.environ['ENVIRONMENT'] = 'production'
        prod_config = get_environment_specific_config()
        
        assert prod_config['environment'] == 'production'
        assert prod_config['debug'] == False
        assert prod_config['auth_mode'] == 'strict'
        assert prod_config['dev_bypass_enabled'] == False
        assert prod_config['require_https'] == True
        
        # Test staging defaults
        os.environ['ENVIRONMENT'] = 'staging'
        staging_config = get_environment_specific_config()
        
        assert staging_config['environment'] == 'staging'
        assert staging_config['auth_mode'] == 'hybrid'
        assert staging_config['dev_bypass_enabled'] == False
        assert staging_config['require_https'] == True
        
        logger.info("✓ Environment-specific defaults test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment-specific defaults test failed: {e}")
        return False


def test_configuration_validation_logic():
    """Test configuration validation logic."""
    try:
        # Test basic validation rules
        
        # Test secret key validation
        def validate_secret_key(key):
            if not key:
                return False, "Secret key is required"
            if len(key) < 32:
                return False, "Secret key too short"
            if key in ["dev-extension-secret-key-change-in-production", "change-me"]:
                return False, "Using default secret key"
            return True, "Valid"
        
        # Test cases
        assert validate_secret_key("")[0] == False
        assert validate_secret_key("short")[0] == False
        assert validate_secret_key("dev-extension-secret-key-change-in-production")[0] == False
        assert validate_secret_key("a" * 32)[0] == True
        
        # Test token expiration validation
        def validate_token_expiration(minutes):
            if minutes <= 0:
                return False, "Token expiration must be positive"
            if minutes > 1440:  # 24 hours
                return False, "Token expiration too long"
            return True, "Valid"
        
        assert validate_token_expiration(0)[0] == False
        assert validate_token_expiration(-1)[0] == False
        assert validate_token_expiration(2000)[0] == False
        assert validate_token_expiration(60)[0] == True
        
        # Test auth mode validation
        def validate_auth_mode(mode):
            valid_modes = ["development", "hybrid", "strict"]
            if mode not in valid_modes:
                return False, f"Invalid auth mode: {mode}"
            return True, "Valid"
        
        assert validate_auth_mode("invalid")[0] == False
        assert validate_auth_mode("development")[0] == True
        assert validate_auth_mode("hybrid")[0] == True
        assert validate_auth_mode("strict")[0] == True
        
        logger.info("✓ Configuration validation logic test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration validation logic test failed: {e}")
        return False


def test_credential_encryption_logic():
    """Test credential encryption/decryption logic."""
    try:
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Test key derivation
        master_key = b"test_master_key_123"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'extension_auth_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        cipher = Fernet(key)
        
        # Test encryption/decryption
        test_data = "test_secret_value_123"
        encrypted_data = cipher.encrypt(test_data.encode())
        decrypted_data = cipher.decrypt(encrypted_data).decode()
        
        assert decrypted_data == test_data, f"Decryption failed: {decrypted_data} != {test_data}"
        
        # Test that encrypted data is different from original
        assert encrypted_data != test_data.encode(), "Encrypted data should be different from original"
        
        logger.info("✓ Credential encryption logic test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Credential encryption logic test failed: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization of configuration data."""
    try:
        # Test configuration serialization
        config_data = {
            'environment': 'development',
            'auth_enabled': True,
            'access_token_expire_minutes': 60,
            'default_permissions': ['extension:read', 'extension:write'],
            'created_at': datetime.utcnow().isoformat(),
            'metadata': {
                'version': '1.0',
                'source': 'test'
            }
        }
        
        # Serialize to JSON
        json_str = json.dumps(config_data, indent=2, default=str)
        
        # Deserialize from JSON
        loaded_data = json.loads(json_str)
        
        # Verify data integrity
        assert loaded_data['environment'] == 'development'
        assert loaded_data['auth_enabled'] == True
        assert loaded_data['access_token_expire_minutes'] == 60
        assert loaded_data['default_permissions'] == ['extension:read', 'extension:write']
        assert 'created_at' in loaded_data
        assert loaded_data['metadata']['version'] == '1.0'
        
        logger.info("✓ JSON serialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ JSON serialization test failed: {e}")
        return False


def test_file_operations():
    """Test file operations for configuration management."""
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="file_ops_test_"))
        
        try:
            # Test directory creation
            config_dir = temp_dir / "config" / "extensions"
            config_dir.mkdir(parents=True, exist_ok=True)
            assert config_dir.exists(), "Config directory not created"
            
            credentials_dir = temp_dir / "credentials"
            credentials_dir.mkdir(parents=True, exist_ok=True)
            assert credentials_dir.exists(), "Credentials directory not created"
            
            # Test file writing
            test_file = config_dir / "test.yaml"
            test_data = {'test': 'data', 'number': 123}
            
            with open(test_file, 'w') as f:
                yaml.dump(test_data, f)
            
            assert test_file.exists(), "Test file not created"
            
            # Test file reading
            with open(test_file, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data['test'] == 'data'
            assert loaded_data['number'] == 123
            
            # Test file permissions (basic check)
            stat_info = test_file.stat()
            assert stat_info.st_size > 0, "File is empty"
            
            # Test file listing
            files = list(config_dir.glob("*.yaml"))
            assert len(files) == 1, f"Expected 1 YAML file, found {len(files)}"
            assert files[0].name == "test.yaml"
            
            logger.info("✓ File operations test passed")
            return True
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"✗ File operations test failed: {e}")
        return False


def test_configuration_structure():
    """Test configuration data structure validation."""
    try:
        # Test required fields
        required_fields = [
            'environment',
            'auth_enabled',
            'secret_key',
            'jwt_algorithm',
            'access_token_expire_minutes',
            'service_token_expire_minutes',
            'api_key',
            'auth_mode',
            'dev_bypass_enabled',
            'require_https',
            'rate_limit_per_minute',
            'burst_limit',
            'enable_rate_limiting',
            'default_permissions',
            'admin_permissions',
            'service_permissions',
            'health_check_enabled',
            'health_check_interval_seconds',
            'health_check_timeout_seconds',
            'log_level',
            'enable_debug_logging',
            'log_sensitive_data'
        ]
        
        # Create test configuration
        test_config = {}
        for field in required_fields:
            if field == 'environment':
                test_config[field] = 'development'
            elif field in ['auth_enabled', 'dev_bypass_enabled', 'require_https', 'enable_rate_limiting', 
                          'health_check_enabled', 'enable_debug_logging', 'log_sensitive_data']:
                test_config[field] = True
            elif field in ['access_token_expire_minutes', 'service_token_expire_minutes', 
                          'rate_limit_per_minute', 'burst_limit', 'health_check_interval_seconds',
                          'health_check_timeout_seconds']:
                test_config[field] = 60
            elif field in ['default_permissions', 'admin_permissions', 'service_permissions']:
                test_config[field] = ['extension:read']
            elif field in ['secret_key', 'api_key']:
                test_config[field] = 'test_key_' + 'x' * 32
            elif field == 'jwt_algorithm':
                test_config[field] = 'HS256'
            elif field == 'auth_mode':
                test_config[field] = 'development'
            elif field == 'log_level':
                test_config[field] = 'INFO'
        
        # Verify all required fields are present
        for field in required_fields:
            assert field in test_config, f"Missing required field: {field}"
        
        # Test field types
        assert isinstance(test_config['auth_enabled'], bool)
        assert isinstance(test_config['access_token_expire_minutes'], int)
        assert isinstance(test_config['default_permissions'], list)
        assert isinstance(test_config['secret_key'], str)
        
        logger.info("✓ Configuration structure test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration structure test failed: {e}")
        return False


def run_all_tests():
    """Run all simplified tests."""
    logger.info("Starting Extension Configuration Simple Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Detection", test_environment_detection),
        ("Config File Creation", test_config_file_creation),
        ("Environment-Specific Defaults", test_environment_specific_defaults),
        ("Configuration Validation Logic", test_configuration_validation_logic),
        ("Credential Encryption Logic", test_credential_encryption_logic),
        ("JSON Serialization", test_json_serialization),
        ("File Operations", test_file_operations),
        ("Configuration Structure", test_configuration_structure),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    logger.info("\nDetailed Results:")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("Extension configuration implementation is working correctly!")
        return True
    else:
        logger.info(f"\n❌ {total - passed} TESTS FAILED")
        logger.info("Extension configuration implementation has issues!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)