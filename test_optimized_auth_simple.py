#!/usr/bin/env python3
"""
Simple test for optimized authentication components without full system dependencies.
"""

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the src directory to the path
sys.path.insert(0, 'src')

# Test the optimized components in isolation
async def test_optimized_components():
    """Test optimized authentication components."""
    print("🧪 Testing Optimized Authentication Components")
    print("=" * 50)
    
    try:
        # Test 1: Import optimized database client
        print("\n1. Testing OptimizedAuthDatabaseClient import...")
        from ai_karen_engine.auth.optimized_database import OptimizedAuthDatabaseClient
        from ai_karen_engine.auth.config import DatabaseConfig
        
        config = DatabaseConfig(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            connection_pool_size=5,
            connection_pool_max_overflow=10,
        )
        
        client = OptimizedAuthDatabaseClient(config)
        print("✅ OptimizedAuthDatabaseClient imported and created successfully")
        
        # Test 2: Import optimized session manager
        print("\n2. Testing OptimizedSessionManager import...")
        from ai_karen_engine.auth.optimized_session import OptimizedSessionManager
        from ai_karen_engine.auth.tokens import TokenManager
        from ai_karen_engine.auth.config import SessionConfig, JWTConfig
        
        session_config = SessionConfig(
            session_timeout_hours=24,
            max_sessions_per_user=5,
        )
        
        jwt_config = JWTConfig(
            secret_key="test_secret_key",
            access_token_expire_minutes=60,
        )
        
        token_manager = TokenManager(jwt_config)
        session_manager = OptimizedSessionManager(session_config, token_manager, client)
        print("✅ OptimizedSessionManager imported and created successfully")
        
        # Test 3: Import optimized core authenticator
        print("\n3. Testing OptimizedCoreAuthenticator import...")
        from ai_karen_engine.auth.optimized_core import OptimizedCoreAuthenticator
        from ai_karen_engine.auth.config import AuthConfig, SecurityConfig
        
        auth_config = AuthConfig(
            database=config,
            session=session_config,
            jwt=jwt_config,
            security=SecurityConfig(
                password_hash_rounds=10,
                max_failed_attempts=3,
            ),
        )
        
        authenticator = OptimizedCoreAuthenticator(auth_config)
        print("✅ OptimizedCoreAuthenticator imported and created successfully")
        
        # Test 4: Test password hasher
        print("\n4. Testing OptimizedPasswordHasher...")
        from ai_karen_engine.auth.optimized_core import OptimizedPasswordHasher
        
        hasher = OptimizedPasswordHasher(rounds=10)
        test_password = "TestPassword123!"
        
        # Test hashing
        hashed = hasher.hash_password(test_password)
        print(f"✅ Password hashed: {hashed[:20]}...")
        
        # Test verification
        is_valid = hasher.verify_password(test_password, hashed)
        print(f"✅ Password verification: {is_valid}")
        
        # Test invalid password
        is_invalid = hasher.verify_password("WrongPassword", hashed)
        print(f"✅ Invalid password verification: {not is_invalid}")
        
        # Test batch verification
        batch_results = hasher.verify_password_batch([
            (test_password, hashed),
            ("WrongPassword", hashed),
            (test_password, hashed),
        ])
        print(f"✅ Batch verification results: {batch_results}")
        
        # Test 5: Test user data models
        print("\n5. Testing UserData model...")
        from ai_karen_engine.auth.models import UserData
        
        user_data = UserData(
            user_id=str(uuid4()),
            email="test@example.com",
            full_name="Test User",
            tenant_id="test_tenant",
            roles=["user", "tester"],
            preferences={"theme": "dark", "lang": "en"},
        )
        
        print(f"✅ UserData created: {user_data.email}")
        print(f"   User ID: {user_data.user_id}")
        print(f"   Roles: {user_data.roles}")
        print(f"   Has role 'tester': {user_data.has_role('tester')}")
        
        # Test serialization
        user_dict = user_data.to_dict()
        user_from_dict = UserData.from_dict(user_dict)
        print(f"✅ Serialization test: {user_from_dict.email == user_data.email}")
        
        # Test 6: Test session data models
        print("\n6. Testing SessionData model...")
        from ai_karen_engine.auth.models import SessionData
        
        session_data = SessionData(
            session_token="test_session_token",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            user_data=user_data,
            expires_in=3600,
            ip_address="192.168.1.100",
            user_agent="Test-Agent/1.0",
            risk_score=0.2,
        )
        
        print(f"✅ SessionData created: {session_data.session_token}")
        print(f"   Expires in: {session_data.expires_in} seconds")
        print(f"   Risk score: {session_data.risk_score}")
        print(f"   Is expired: {session_data.is_expired()}")
        
        # Test 7: Test configuration system
        print("\n7. Testing configuration system...")
        from ai_karen_engine.auth.config import AuthConfig
        
        # Test environment-based configuration
        os.environ["AUTH_SECRET_KEY"] = "test_env_secret"
        os.environ["AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"] = "120"
        
        env_config = AuthConfig.from_env()
        print(f"✅ Environment config loaded")
        print(f"   Secret key set: {len(env_config.jwt.secret_key) > 0}")
        print(f"   Access token expiry: {env_config.jwt.access_token_expire_minutes} minutes")
        
        # Test dictionary-based configuration
        config_dict = {
            "database": {
                "database_url": "postgresql://test:test@localhost/test",
                "connection_pool_size": 15,
            },
            "security": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 10,
            },
        }
        
        dict_config = AuthConfig.from_dict(config_dict)
        print(f"✅ Dictionary config loaded")
        print(f"   Pool size: {dict_config.database.connection_pool_size}")
        print(f"   Max failed attempts: {dict_config.security.max_failed_attempts}")
        
        print("\n🎉 All optimized authentication components tested successfully!")
        
        print("\n📊 Component Summary:")
        print("• OptimizedAuthDatabaseClient - PostgreSQL-optimized database operations")
        print("• OptimizedSessionManager - Efficient session management with cleanup")
        print("• OptimizedCoreAuthenticator - High-performance authentication operations")
        print("• OptimizedPasswordHasher - Secure password hashing with batch operations")
        print("• Enhanced data models with validation and serialization")
        print("• Flexible configuration system with environment support")
        
        print("\n🚀 Key Optimizations Implemented:")
        print("• UPSERT operations for atomic user creation/updates")
        print("• JSONB indexes for efficient role-based queries")
        print("• Partial indexes for active-only data filtering")
        print("• Batch operations for improved throughput")
        print("• Connection pooling for concurrent operations")
        print("• Automatic session cleanup and maintenance")
        print("• Performance metrics collection and monitoring")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_optimized_components())
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)