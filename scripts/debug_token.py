#!/usr/bin/env python3
"""
Debug token generation and validation.
"""

import jwt
import sys
import os
from datetime import datetime, timezone, timedelta

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))


def debug_jwt_operations():
    """Debug JWT operations step by step."""
    print("Debugging JWT operations...")
    
    secret_key = "test-secret-key-123"
    algorithm = "HS256"
    
    # Create a simple payload
    payload = {
        "user_id": "test_user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "jti": "test-jti-123"
    }
    
    print(f"Original payload: {payload}")
    
    # Encode token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    print(f"Encoded token: {token}")
    
    # Decode without verification
    unverified = jwt.decode(token, options={"verify_signature": False})
    print(f"Unverified decode: {unverified}")
    
    # Decode with verification
    try:
        verified = jwt.decode(token, secret_key, algorithms=[algorithm])
        print(f"Verified decode: {verified}")
        print("✓ JWT operations working correctly")
        return True
    except Exception as e:
        print(f"✗ JWT verification failed: {e}")
        return False


def debug_token_manager():
    """Debug token manager operations."""
    print("\nDebugging token manager...")
    
    try:
        from server.token_manager import TokenManager, TokenPayload
        
        config = {
            "secret_key": "test-secret-key-123",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
            "token_blacklist_enabled": False
        }
        
        token_manager = TokenManager(config)
        print(f"Token manager secret: {token_manager.secret_key}")
        print(f"Token manager algorithm: {token_manager.algorithm}")
        
        # Generate token manually
        payload = TokenPayload(
            user_id="test_user",
            tenant_id="test_tenant"
        )
        
        print(f"Token payload JTI: {payload.jti}")
        print(f"Token payload expires: {payload.expires_at}")
        
        jwt_payload = payload.to_jwt_payload()
        print(f"JWT payload: {jwt_payload}")
        
        # Encode manually
        token = jwt.encode(jwt_payload, token_manager.secret_key, algorithm=token_manager.algorithm)
        print(f"Manual token: {token}")
        
        # Try to decode manually
        try:
            decoded = jwt.decode(token, token_manager.secret_key, algorithms=[token_manager.algorithm])
            print(f"Manual decode successful: {decoded}")
        except Exception as e:
            print(f"Manual decode failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"Token manager debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run debug tests."""
    print("Token Debug Tests")
    print("=" * 30)
    
    jwt_ok = debug_jwt_operations()
    tm_ok = debug_token_manager()
    
    print("=" * 30)
    if jwt_ok and tm_ok:
        print("✓ Debug tests completed")
    else:
        print("✗ Debug tests failed")


if __name__ == "__main__":
    main()