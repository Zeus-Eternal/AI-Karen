#!/usr/bin/env python3
"""
Test script for token management utilities.
Verifies JWT token generation, validation, refresh logic, blacklisting, and service-to-service authentication.
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


async def test_token_generation():
    """Test JWT token generation functions."""
    print("\n=== Testing Token Generation ===")
    
    try:
        from server.token_manager import TokenManager, TokenType
        
        # Create test configuration
        config = {
            "secret_key": "test-secret-key-for-token-generation",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
            "service_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
            "token_blacklist_enabled": True
        }
        
        token_manager = TokenManager(config)
        
        # Test access token generation
        access_token, access_payload = token_manager.generate_access_token(
            user_id="test_user_123",
            tenant_id="test_tenant",
            roles=["user", "extension_user"],
            permissions=["extension:read", "extension:write"]
        )
        
        print(f"✓ Access token generated: {access_token[:50]}...")
        print(f"  - User ID: {access_payload.user_id}")
        print(f"  - Token Type: {access_payload.token_type}")
        print(f"  - JTI: {access_payload.jti}")
        print(f"  - Expires: {access_payload.expires_at}")
        
        # Test service token generation
        service_token, service_payload = token_manager.generate_service_token(
            service_name="extension_manager",
            permissions=["extension:background_tasks", "extension:health"]
        )
        
        print(f"✓ Service token generated: {service_token[:50]}...")
        print(f"  - Service Name: {service_payload.service_name}")
        print(f"  - Token Type: {service_payload.token_type}")
        print(f"  - JTI: {service_payload.jti}")
        
        # Test background task token generation
        bg_token, bg_payload = token_manager.generate_background_task_token(
            task_name="data_sync_task",
            user_id="test_user_123",
            permissions=["extension:background_tasks", "extension:data"]
        )
        
        print(f"✓ Background task token generated: {bg_token[:50]}...")
        print(f"  - Task User ID: {bg_payload.user_id}")
        print(f"  - Token Type: {bg_payload.token_type}")
        print(f"  - JTI: {bg_payload.jti}")
        
        # Test refresh token generation
        refresh_token, refresh_payload = token_manager.generate_refresh_token(
            user_id="test_user_123",
            tenant_id="test_tenant"
        )
        
        print(f"✓ Refresh token generated: {refresh_token[:50]}...")
        print(f"  - User ID: {refresh_payload.user_id}")
        print(f"  - Token Type: {refresh_payload.token_type}")
        print(f"  - JTI: {refresh_payload.jti}")
        
        return {
            "access_token": access_token,
            "service_token": service_token,
            "bg_token": bg_token,
            "refresh_token": refresh_token,
            "token_manager": token_manager
        }
        
    except Exception as e:
        print(f"✗ Token generation test failed: {e}")
        return None


async def test_token_validation(tokens):
    """Test JWT token validation functions."""
    print("\n=== Testing Token Validation ===")
    
    if not tokens:
        print("✗ Skipping validation tests - no tokens available")
        return
    
    try:
        token_manager = tokens["token_manager"]
        
        # Test access token validation
        status, payload = await token_manager.validate_token(tokens["access_token"])
        print(f"✓ Access token validation: {status}")
        if payload:
            print(f"  - User ID: {payload.get('user_id')}")
            print(f"  - Token Type: {payload.get('token_type')}")
            print(f"  - Permissions: {payload.get('permissions')}")
        
        # Test service token validation
        status, payload = await token_manager.validate_token(tokens["service_token"])
        print(f"✓ Service token validation: {status}")
        if payload:
            print(f"  - Service Name: {payload.get('service_name')}")
            print(f"  - Token Type: {payload.get('token_type')}")
        
        # Test background task token validation
        status, payload = await token_manager.validate_token(tokens["bg_token"])
        print(f"✓ Background task token validation: {status}")
        if payload:
            print(f"  - User ID: {payload.get('user_id')}")
            print(f"  - Token Type: {payload.get('token_type')}")
        
        # Test refresh token validation
        status, payload = await token_manager.validate_token(tokens["refresh_token"])
        print(f"✓ Refresh token validation: {status}")
        if payload:
            print(f"  - User ID: {payload.get('user_id')}")
            print(f"  - Token Type: {payload.get('token_type')}")
        
        # Test invalid token
        status, payload = await token_manager.validate_token("invalid.token.here")
        print(f"✓ Invalid token validation: {status} (should be INVALID)")
        
    except Exception as e:
        print(f"✗ Token validation test failed: {e}")


async def test_token_refresh(tokens):
    """Test token refresh logic."""
    print("\n=== Testing Token Refresh ===")
    
    if not tokens:
        print("✗ Skipping refresh tests - no tokens available")
        return
    
    try:
        token_manager = tokens["token_manager"]
        
        # Test token refresh
        new_access, new_refresh, payload = await token_manager.refresh_access_token(
            tokens["refresh_token"],
            new_permissions=["extension:read", "extension:write", "extension:admin"]
        )
        
        if new_access and new_refresh:
            print(f"✓ Token refresh successful")
            print(f"  - New access token: {new_access[:50]}...")
            print(f"  - New refresh token: {new_refresh[:50]}...")
            print(f"  - New permissions: {payload.get('permissions') if payload else 'N/A'}")
            
            # Validate new tokens
            status, _ = await token_manager.validate_token(new_access)
            print(f"  - New access token validation: {status}")
            
            status, _ = await token_manager.validate_token(new_refresh)
            print(f"  - New refresh token validation: {status}")
            
            # Try to use old refresh token (should fail)
            old_access, old_refresh, _ = await token_manager.refresh_access_token(tokens["refresh_token"])
            if not old_access:
                print("✓ Old refresh token correctly rejected")
            else:
                print("✗ Old refresh token incorrectly accepted")
        else:
            print("✗ Token refresh failed")
        
    except Exception as e:
        print(f"✗ Token refresh test failed: {e}")


async def test_token_blacklisting(tokens):
    """Test token blacklisting functionality."""
    print("\n=== Testing Token Blacklisting ===")
    
    if not tokens:
        print("✗ Skipping blacklist tests - no tokens available")
        return
    
    try:
        token_manager = tokens["token_manager"]
        
        # Create a test token for blacklisting
        test_token, test_payload = token_manager.generate_access_token(
            user_id="blacklist_test_user",
            tenant_id="test_tenant"
        )
        
        # Validate token before blacklisting
        status, _ = await token_manager.validate_token(test_token)
        print(f"✓ Token validation before blacklisting: {status}")
        
        # Blacklist the token
        success = await token_manager.revoke_token(test_token)
        print(f"✓ Token blacklisting: {'successful' if success else 'failed'}")
        
        # Try to validate blacklisted token
        status, _ = await token_manager.validate_token(test_token)
        print(f"✓ Blacklisted token validation: {status} (should be BLACKLISTED)")
        
        # Test bulk revocation
        revoked_count = await token_manager.revoke_all_user_tokens("test_user_123")
        print(f"✓ Bulk token revocation: {revoked_count} tokens revoked")
        
    except Exception as e:
        print(f"✗ Token blacklisting test failed: {e}")


async def test_utility_functions():
    """Test token utility functions."""
    print("\n=== Testing Utility Functions ===")
    
    try:
        from server.token_utils import (
            create_user_session_tokens,
            create_service_authentication_token,
            create_background_task_authentication_token,
            BackgroundTaskTokenManager,
            ServiceTokenManager
        )
        
        # Test user session token creation
        session_tokens = await create_user_session_tokens(
            user_id="utility_test_user",
            tenant_id="test_tenant",
            roles=["user", "admin"],
            permissions=["extension:read", "extension:write", "extension:admin"]
        )
        
        if session_tokens:
            print("✓ User session tokens created")
            print(f"  - Access token: {session_tokens.get('access_token', 'N/A')[:50]}...")
            print(f"  - Token type: {session_tokens.get('token_type', 'N/A')}")
            print(f"  - Expires in: {session_tokens.get('expires_in', 'N/A')} seconds")
        else:
            print("✗ User session token creation failed")
        
        # Test service authentication token
        service_token = await create_service_authentication_token(
            service_name="test_extension_service",
            permissions=["extension:background_tasks", "extension:health"],
            expires_minutes=15
        )
        
        if service_token:
            print(f"✓ Service authentication token created: {service_token[:50]}...")
        else:
            print("✗ Service authentication token creation failed")
        
        # Test background task token
        bg_task_token = await create_background_task_authentication_token(
            task_name="test_background_task",
            user_id="utility_test_user",
            permissions=["extension:background_tasks", "extension:execute"],
            expires_minutes=30
        )
        
        if bg_task_token:
            print(f"✓ Background task token created: {bg_task_token[:50]}...")
        else:
            print("✗ Background task token creation failed")
        
        # Test BackgroundTaskTokenManager
        task_token = await BackgroundTaskTokenManager.create_task_token(
            task_name="scheduled_maintenance",
            task_type="system_maintenance",
            service_context="maintenance_service"
        )
        
        if task_token:
            print(f"✓ Background task manager token created: {task_token[:50]}...")
            
            # Validate the task token
            is_valid = await BackgroundTaskTokenManager.validate_task_token(
                task_token, "scheduled_maintenance"
            )
            print(f"✓ Background task token validation: {'valid' if is_valid else 'invalid'}")
        
        # Test ServiceTokenManager
        inter_service_token = await ServiceTokenManager.create_inter_service_token(
            source_service="extension_manager",
            target_service="background_processor",
            operation="background_task",
            expires_minutes=10
        )
        
        if inter_service_token:
            print(f"✓ Inter-service token created: {inter_service_token[:50]}...")
            
            # Validate the service token
            is_valid = await ServiceTokenManager.validate_service_token(
                inter_service_token,
                expected_source="extension_manager",
                expected_target="background_processor",
                required_operation="background_task"
            )
            print(f"✓ Inter-service token validation: {'valid' if is_valid else 'invalid'}")
        
    except Exception as e:
        print(f"✗ Utility functions test failed: {e}")


async def test_token_information():
    """Test token information extraction."""
    print("\n=== Testing Token Information ===")
    
    try:
        from server.token_utils import get_token_information
        from server.token_manager import TokenManager
        
        # Create test configuration
        config = {
            "secret_key": "test-secret-key-for-info",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60
        }
        
        token_manager = TokenManager(config)
        
        # Generate a test token
        test_token, _ = token_manager.generate_access_token(
            user_id="info_test_user",
            tenant_id="test_tenant",
            roles=["user"],
            permissions=["extension:read"]
        )
        
        # Get token information
        token_info = get_token_information(test_token)
        
        if token_info:
            print("✓ Token information extracted:")
            print(f"  - User ID: {token_info.get('user_id')}")
            print(f"  - Token Type: {token_info.get('token_type')}")
            print(f"  - JTI: {token_info.get('jti')}")
            print(f"  - Issued At: {token_info.get('issued_at_readable')}")
            print(f"  - Expires At: {token_info.get('expires_at_readable')}")
            print(f"  - Time Until Expiry: {token_info.get('time_until_expiry')}")
            print(f"  - Permissions: {token_info.get('permissions')}")
        else:
            print("✗ Failed to extract token information")
        
    except Exception as e:
        print(f"✗ Token information test failed: {e}")


async def main():
    """Run all token management tests."""
    print("Starting Token Management Tests")
    print("=" * 50)
    
    # Test token generation
    tokens = await test_token_generation()
    
    # Test token validation
    await test_token_validation(tokens)
    
    # Test token refresh
    await test_token_refresh(tokens)
    
    # Test token blacklisting
    await test_token_blacklisting(tokens)
    
    # Test utility functions
    await test_utility_functions()
    
    # Test token information
    await test_token_information()
    
    print("\n" + "=" * 50)
    print("Token Management Tests Completed")


if __name__ == "__main__":
    asyncio.run(main())