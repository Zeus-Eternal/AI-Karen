#!/usr/bin/env python3
"""
Setup a test user in the fallback authentication database
"""

import asyncio
import sys
import os

# Add the repository `src` directory to the path so local package imports (ai_karen_engine)
# resolve correctly in editors (Pylance) and at runtime. Use an absolute path one level
# up from the scripts folder (repo root /src).
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(repo_root, 'src'))

# Also add backup/legacy source locations used in this repo (some modules live in backups)
backup_src = os.path.join(repo_root, 'backups', 'complex_auth_system', 'src')
if os.path.isdir(backup_src):
    sys.path.insert(0, backup_src)

async def setup_test_user():
    """Create a test user in the fallback database"""
    
    print("🔧 Setting up test user in fallback database")
    print("=" * 50)
    
    try:
        from ai_karen_engine.auth.fallback_auth import SQLiteFallbackAuth
        
        # Initialize fallback auth
        auth_service = SQLiteFallbackAuth()
        await auth_service.initialize()
        
        print("✅ Fallback auth service initialized")
        
        # Test user credentials
        email = "admin@example.com"
        password = "admin123"
        
        try:
            # Try to create the test user
            user_data = await auth_service.create_user(
                email=email,
                password=password,
                full_name="Test Admin",
                roles=["admin", "user"],
                tenant_id="default"
            )
            
            print(f"✅ Test user created successfully!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   User ID: {user_data.user_id}")
            
        except Exception as create_error:
            if "already exists" in str(create_error).lower():
                print(f"ℹ️  Test user already exists: {email}")
                
                # Try to authenticate to verify it works
                try:
                    user_data = await auth_service.authenticate_user(
                        email=email,
                        password=password,
                        ip_address="127.0.0.1",
                        user_agent="test"
                    )
                    print(f"✅ Test user authentication successful!")
                    print(f"   User ID: {user_data.user_id}")
                except Exception as auth_error:
                    print(f"❌ Test user authentication failed: {auth_error}")
                    return False
            else:
                print(f"❌ Failed to create test user: {create_error}")
                return False
        
        print("\n🎉 Test user setup complete!")
        print("   You can now test login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_test_user())
    
    if success:
        print("\n✅ Ready to test authentication!")
    else:
        print("\n❌ Setup failed. Check the errors above.")