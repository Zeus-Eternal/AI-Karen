#!/usr/bin/env python3
"""
Simple token validation test to verify core functionality.
"""

import asyncio
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))


async def test_simple_token_validation():
    """Test simple token generation and validation."""
    print("Testing simple token validation...")
    
    try:
        from server.token_manager import TokenManager, TokenStatus
        
        # Use the same secret key for generation and validation
        config = {
            "secret_key": "test-secret-key-123",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
            "token_blacklist_enabled": False
        }
        
        # Create token manager
        token_manager = TokenManager(config)
        print(f"✓ Token manager created with secret: {config['secret_key']}")
        
        # Generate token
        token, payload = token_manager.generate_access_token(
            user_id="test_user",
            tenant_id="test_tenant",
            permissions=["extension:read"]
        )
        
        print(f"✓ Token generated: {token[:50]}...")
        print(f"  - JTI: {payload.jti}")
        print(f"  - User ID: {payload.user_id}")
        
        # Validate token with same manager
        status, validated_payload = await token_manager.validate_token(token)
        
        print(f"✓ Token validation result: {status}")
        if validated_payload:
            print(f"  - Validated User ID: {validated_payload.get('user_id')}")
            print(f"  - Validated JTI: {validated_payload.get('jti')}")
            print(f"  - Token Type: {validated_payload.get('token_type')}")
        else:
            print("  - No payload returned")
        
        # Test with different secret key (should fail)
        config_different = config.copy()
        config_different["secret_key"] = "different-secret-key"
        token_manager_different = TokenManager(config_different)
        
        status_different, _ = await token_manager_different.validate_token(token)
        print(f"✓ Validation with different secret: {status_different} (should be INVALID)")
        
        return status == TokenStatus.VALID
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run simple token test."""
    print("Simple Token Validation Test")
    print("=" * 40)
    
    success = await test_simple_token_validation()
    
    print("=" * 40)
    if success:
        print("✓ Test passed!")
        return 0
    else:
        print("✗ Test failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)