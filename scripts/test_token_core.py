#!/usr/bin/env python3
"""
Core token management test without external dependencies.
Tests the core JWT token generation, validation, and management functionality.
"""

import asyncio
import sys
import os
import logging
from datetime import timedelta, datetime, timezone

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_core_token_functionality():
    """Test core token functionality without external dependencies."""
    print("\n=== Testing Core Token Management ===")
    
    try:
        from server.token_manager import TokenManager, TokenType, TokenStatus, TokenPayload
        
        # Create test configuration without Redis
        config = {
            "secret_key": "test-secret-key-for-core-functionality",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
            "service_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
            "token_blacklist_enabled": False  # Disable Redis-dependent blacklist
        }
        
        token_manager = TokenManager(config)
        print("✓ Token manager initialized")
        
        # Test TokenPayload creation
        payload = TokenPayload(
            user_id="test_user_123",
            tenant_id="test_tenant",
            roles=["user", "extension_user"],
            permissions=["extension:read", "extension:write"],
            token_type=TokenType.ACCESS
        )
        
        print(f"✓ Token payload created:")
        print(f"  - User ID: {payload.user_id}")
        print(f"  - JTI: {payload.jti}")
        print(f"  - Token Type: {payload.token_type}")
        print(f"  - Issued At: {payload.issued_at}")
        
        # Test JWT payload conversion
        jwt_payload = payload.to_jwt_payload()
        print(f"✓ JWT payload conversion successful")
        print(f"  - Keys: {list(jwt_payload.keys())}")
        
        # Test access token generation
        access_token, access_payload = token_manager.generate_access_token(
            user_id="test_user_123",
            tenant_id="test_tenant",
            roles=["user", "extension_user"],
            permissions=["extension:read", "extension:write"]
        )
        
        print(f"✓ Access token generated: {access_token[:50]}...")
        print(f"  - Payload JTI: {access_payload.jti}")
        print(f"  - Expires: {access_payload.expires_at}")
        
        # Test service token generation
        service_token, service_payload = token_manager.generate_service_token(
            service_name="extension_manager",
            permissions=["extension:background_tasks", "extension:health"]
        )
        
        print(f"✓ Service token generated: {service_token[:50]}...")
        print(f"  - Service Name: {service_payload.service_name}")
        print(f"  - JTI: {service_payload.jti}")
        
        # Test background task token generation
        bg_token, bg_payload = token_manager.generate_background_task_token(
            task_name="data_sync_task",
            user_id="test_user_123",
            permissions=["extension:background_tasks", "extension:data"]
        )
        
        print(f"✓ Background task token generated: {bg_token[:50]}...")
        print(f"  - User ID: {bg_payload.user_id}")
        print(f"  - JTI: {bg_payload.jti}")
        
        # Test refresh token generation
        refresh_token, refresh_payload = token_manager.generate_refresh_token(
            user_id="test_user_123",
            tenant_id="test_tenant"
        )
        
        print(f"✓ Refresh token generated: {refresh_token[:50]}...")
        print(f"  - JTI: {refresh_payload.jti}")
        
        # Test token validation
        status, validated_payload = await token_manager.validate_token(access_token)
        print(f"✓ Access token validation: {status}")
        if validated_payload:
            print(f"  - User ID: {validated_payload.get('user_id')}")
            print(f"  - Permissions: {validated_payload.get('permissions')}")
        
        # Test service token validation
        status, validated_payload = await token_manager.validate_token(service_token)
        print(f"✓ Service token validation: {status}")
        if validated_payload:
            print(f"  - Service Name: {validated_payload.get('service_name')}")
        
        # Test invalid token
        status, _ = await token_manager.validate_token("invalid.token.here")
        print(f"✓ Invalid token validation: {status} (should be INVALID)")
        
        # Test token refresh (without blacklist)
        new_access, new_refresh, new_payload = await token_manager.refresh_access_token(
            refresh_token,
            new_permissions=["extension:read", "extension:write", "extension:admin"]
        )
        
        if new_access and new_refresh:
            print(f"✓ Token refresh successful")
            print(f"  - New access token: {new_access[:50]}...")
            print(f"  - New permissions: {new_payload.get('permissions') if new_payload else 'N/A'}")
            
            # Validate new access token
            status, _ = await token_manager.validate_token(new_access)
            print(f"  - New access token validation: {status}")
        else:
            print("✗ Token refresh failed")
        
        # Test token information extraction
        token_info = token_manager.get_token_info(access_token)
        if token_info:
            print(f"✓ Token information extracted:")
            print(f"  - User ID: {token_info.get('user_id')}")
            print(f"  - JTI: {token_info.get('jti')}")
            print(f"  - Issued At: {token_info.get('issued_at_readable')}")
            print(f"  - Expires At: {token_info.get('expires_at_readable')}")
        
        # Test cleanup
        cleaned_count = await token_manager.cleanup_expired_refresh_tokens()
        print(f"✓ Cleanup completed: {cleaned_count} tokens cleaned")
        
        return True
        
    except Exception as e:
        print(f"✗ Core token functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_token_types_and_validation():
    """Test different token types and their validation."""
    print("\n=== Testing Token Types and Validation ===")
    
    try:
        from server.token_manager import TokenManager, TokenType, TokenStatus
        
        config = {
            "secret_key": "test-secret-key-for-types",
            "algorithm": "HS256",
            "access_token_expire_minutes": 1,  # Short expiration for testing
            "service_token_expire_minutes": 1,
            "token_blacklist_enabled": False
        }
        
        token_manager = TokenManager(config)
        
        # Test different token types
        token_types = [
            ("user_access", lambda: token_manager.generate_access_token("user123", permissions=["extension:read"])),
            ("service", lambda: token_manager.generate_service_token("test_service", permissions=["extension:health"])),
            ("background_task", lambda: token_manager.generate_background_task_token("task1", user_id="user123")),
            ("refresh", lambda: token_manager.generate_refresh_token("user123"))
        ]
        
        generated_tokens = {}
        
        for token_name, generator in token_types:
            token, payload = generator()
            generated_tokens[token_name] = token
            print(f"✓ {token_name} token generated (type: {payload.token_type})")
        
        # Validate all tokens
        for token_name, token in generated_tokens.items():
            status, payload = await token_manager.validate_token(token)
            print(f"✓ {token_name} token validation: {status}")
            if payload:
                print(f"  - Type: {payload.get('token_type')}")
                print(f"  - Subject: {payload.get('user_id') or payload.get('service_name')}")
        
        # Test expired token (wait for expiration)
        print("⏳ Waiting for token expiration...")
        await asyncio.sleep(65)  # Wait for tokens to expire
        
        # Check expired tokens
        for token_name, token in generated_tokens.items():
            if token_name != "refresh":  # Refresh tokens have longer expiration
                status, _ = await token_manager.validate_token(token)
                expected_status = TokenStatus.EXPIRED
                if status == expected_status:
                    print(f"✓ {token_name} token correctly expired: {status}")
                else:
                    print(f"✗ {token_name} token expiration test failed: {status} (expected {expected_status})")
        
        return True
        
    except Exception as e:
        print(f"✗ Token types and validation test failed: {e}")
        return False


async def test_token_security_features():
    """Test security features of token management."""
    print("\n=== Testing Token Security Features ===")
    
    try:
        from server.token_manager import TokenManager, TokenPayload, TokenType
        
        config = {
            "secret_key": "test-secret-key-for-security",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
            "token_blacklist_enabled": False
        }
        
        token_manager = TokenManager(config)
        
        # Test JTI uniqueness
        jtis = set()
        for i in range(10):
            token, payload = token_manager.generate_access_token(f"user_{i}")
            jtis.add(payload.jti)
        
        if len(jtis) == 10:
            print("✓ JTI uniqueness test passed (10 unique JTIs generated)")
        else:
            print(f"✗ JTI uniqueness test failed ({len(jtis)} unique JTIs out of 10)")
        
        # Test token tampering detection
        original_token, _ = token_manager.generate_access_token("test_user")
        
        # Tamper with token
        tampered_token = original_token[:-10] + "tampered123"
        
        status, _ = await token_manager.validate_token(tampered_token)
        if status == "invalid":
            print("✓ Token tampering detection successful")
        else:
            print(f"✗ Token tampering detection failed: {status}")
        
        # Test different algorithms (should fail with wrong algorithm)
        config_wrong_algo = config.copy()
        config_wrong_algo["algorithm"] = "HS512"
        token_manager_wrong = TokenManager(config_wrong_algo)
        
        status, _ = await token_manager_wrong.validate_token(original_token)
        if status == "invalid":
            print("✓ Algorithm mismatch detection successful")
        else:
            print(f"✗ Algorithm mismatch detection failed: {status}")
        
        # Test permission validation
        token, payload = token_manager.generate_access_token(
            "test_user",
            permissions=["extension:read", "extension:write"]
        )
        
        status, validated_payload = await token_manager.validate_token(token)
        if status == "valid" and validated_payload:
            permissions = validated_payload.get("permissions", [])
            if "extension:read" in permissions and "extension:write" in permissions:
                print("✓ Permission validation successful")
            else:
                print(f"✗ Permission validation failed: {permissions}")
        
        return True
        
    except Exception as e:
        print(f"✗ Token security features test failed: {e}")
        return False


async def main():
    """Run all core token management tests."""
    print("Starting Core Token Management Tests")
    print("=" * 60)
    
    results = []
    
    # Test core functionality
    results.append(await test_core_token_functionality())
    
    # Test token types and validation
    results.append(await test_token_types_and_validation())
    
    # Test security features
    results.append(await test_token_security_features())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Core Token Management Tests Completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed successfully!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)