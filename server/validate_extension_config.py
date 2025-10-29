#!/usr/bin/env python3
"""
Extension Authentication Configuration Validation Script.
Tests the extension authentication configuration settings.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_extension_config():
    """Test extension authentication configuration."""
    try:
        from server.config import settings
        from server.security import get_extension_auth_manager
        
        print("=" * 60)
        print("Extension Authentication Configuration Validation")
        print("=" * 60)
        
        # Test configuration loading
        print("\n1. Testing configuration loading...")
        config = settings.get_extension_auth_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Auth enabled: {config['enabled']}")
        print(f"  - Auth mode: {config['auth_mode']}")
        print(f"  - Development mode: {config['development_mode']}")
        print(f"  - Algorithm: {config['algorithm']}")
        
        # Test environment-specific configuration
        print("\n2. Testing environment-specific configuration...")
        env_config = settings.get_environment_specific_extension_config()
        print(f"✓ Environment-specific configuration loaded")
        print(f"  - Dev bypass enabled: {env_config['dev_bypass_enabled']}")
        print(f"  - HTTPS required: {env_config['require_https']}")
        print(f"  - Rate limit: {env_config['rate_limit_per_minute']}/min")
        print(f"  - Max failed attempts: {env_config['max_failed_attempts']}")
        
        # Test configuration validation
        print("\n3. Testing configuration validation...")
        is_valid = settings.validate_extension_auth_config()
        if is_valid:
            print("✓ Configuration validation passed")
        else:
            print("✗ Configuration validation failed")
            return False
        
        # Test authentication manager initialization
        print("\n4. Testing authentication manager initialization...")
        auth_manager = get_extension_auth_manager()
        print(f"✓ Authentication manager initialized")
        print(f"  - Secret key configured: {'***' if auth_manager.secret_key else 'No'}")
        print(f"  - Algorithm: {auth_manager.algorithm}")
        print(f"  - Auth mode: {auth_manager.auth_mode}")
        
        # Test token creation
        print("\n5. Testing token creation...")
        try:
            access_token = auth_manager.create_access_token(
                user_id="test-user",
                tenant_id="test-tenant",
                roles=["user"],
                permissions=["extension:read", "extension:write"]
            )
            print("✓ Access token created successfully")
            print(f"  - Token length: {len(access_token)} characters")
            
            service_token = auth_manager.create_service_token(
                service_name="test-service",
                permissions=["extension:background_tasks"]
            )
            print("✓ Service token created successfully")
            print(f"  - Token length: {len(service_token)} characters")
            
        except Exception as e:
            print(f"✗ Token creation failed: {e}")
            return False
        
        # Test permission checking
        print("\n6. Testing permission checking...")
        test_user_context = {
            'user_id': 'test-user',
            'tenant_id': 'test-tenant',
            'roles': ['user'],
            'permissions': ['extension:read', 'extension:write'],
            'token_type': 'access'
        }
        
        has_read = auth_manager.has_permission(test_user_context, 'read')
        has_write = auth_manager.has_permission(test_user_context, 'write')
        has_admin = auth_manager.has_permission(test_user_context, 'admin')
        
        print(f"✓ Permission checking working")
        print(f"  - Read permission: {has_read}")
        print(f"  - Write permission: {has_write}")
        print(f"  - Admin permission: {has_admin}")
        
        print("\n" + "=" * 60)
        print("✓ All extension authentication configuration tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test that required environment variables are set."""
    print("\n" + "=" * 60)
    print("Environment Variables Validation")
    print("=" * 60)
    
    required_vars = [
        "EXTENSION_SECRET_KEY",
        "EXTENSION_API_KEY",
        "EXTENSION_AUTH_MODE",
        "EXTENSION_JWT_ALGORITHM"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'***' if 'KEY' in var else value}")
        else:
            print(f"✗ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("These will use default values from config.py")
    else:
        print("\n✓ All required environment variables are set")
    
    return len(missing_vars) == 0

def main():
    """Main validation function."""
    print("Starting Extension Authentication Configuration Validation...")
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test configuration
    config_ok = test_extension_config()
    
    if config_ok:
        print("\n🎉 Extension authentication configuration is ready!")
        if not env_ok:
            print("⚠️  Some environment variables are using defaults - consider setting them explicitly")
        return 0
    else:
        print("\n❌ Extension authentication configuration has issues that need to be resolved")
        return 1

if __name__ == "__main__":
    sys.exit(main())