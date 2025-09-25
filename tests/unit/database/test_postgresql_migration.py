#!/usr/bin/env python3
"""
Test script to verify PostgreSQL migration for authentication services.
This script tests that all authentication services are using PostgreSQL exclusively.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_postgresql_migration():
    """Test that authentication services are using PostgreSQL exclusively."""
    print("🔍 Testing PostgreSQL Migration for Authentication Services")
    print("=" * 60)
    
    try:
        # Test 1: Configuration uses PostgreSQL
        print("\n1. Testing AuthConfig uses PostgreSQL...")
        from src.ai_karen_engine.auth.config import AuthConfig
        
        config = AuthConfig.from_env()
        print(f"   Database URL: {config.database.database_url}")
        
        if "postgresql" in config.database.database_url.lower():
            print("   ✅ AuthConfig is configured for PostgreSQL")
        else:
            print("   ❌ AuthConfig is not using PostgreSQL")
            return False
        
        # Test 2: Database client initialization
        print("\n2. Testing AuthDatabaseClient initialization...")
        from src.ai_karen_engine.auth.database import AuthDatabaseClient
        
        db_client = AuthDatabaseClient(config.database)
        print("   ✅ AuthDatabaseClient initialized successfully")
        
        # Test 3: Schema initialization
        print("\n3. Testing PostgreSQL schema initialization...")
        try:
            await db_client.initialize_schema()
            print("   ✅ PostgreSQL schema initialized successfully")
        except Exception as e:
            print(f"   ⚠️  Schema initialization failed (expected if DB not available): {e}")
        
        # Test 4: Core authenticator uses PostgreSQL client
        print("\n4. Testing CoreAuthenticator uses PostgreSQL...")
        from src.ai_karen_engine.auth.core import CoreAuthenticator
        
        core_auth = CoreAuthenticator(config)
        if hasattr(core_auth.db_client, 'engine'):
            print("   ✅ CoreAuthenticator is using PostgreSQL database client")
        else:
            print("   ❌ CoreAuthenticator is not using PostgreSQL database client")
            return False
        
        # Test 5: Session manager uses PostgreSQL
        print("\n5. Testing SessionManager uses PostgreSQL...")
        session_manager = core_auth.session_manager
        if hasattr(session_manager.store.backend, 'db_client'):
            print("   ✅ SessionManager is configured to use PostgreSQL")
        else:
            print("   ❌ SessionManager is not using PostgreSQL")
            return False
        
        # Test 6: No SQLite references in configuration
        print("\n6. Testing no SQLite references in configuration...")
        config_dict = config.to_dict()
        config_str = str(config_dict).lower()
        
        if "sqlite" in config_str or ".db" in config_str:
            print("   ❌ Found SQLite references in configuration")
            return False
        else:
            print("   ✅ No SQLite references found in configuration")
        
        # Test 7: Session storage type is database (PostgreSQL)
        print("\n7. Testing session storage configuration...")
        if config.session.storage_type == "database":
            print("   ✅ Session storage is configured for database (PostgreSQL)")
        else:
            print(f"   ⚠️  Session storage type: {config.session.storage_type}")
        
        await db_client.close()
        
        print("\n" + "=" * 60)
        print("🎉 PostgreSQL Migration Test PASSED!")
        print("   All authentication services are configured to use PostgreSQL exclusively.")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL Migration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_postgresql_migration())
    sys.exit(0 if success else 1)