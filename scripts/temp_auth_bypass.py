#!/usr/bin/env python3
"""
Temporary Authentication Bypass for Development
This script helps bypass authentication for specific endpoints during development.
"""

import os
import sys

def create_auth_bypass_env():
    """Create environment variables to bypass authentication for development."""
    
    print("🔧 Creating temporary authentication bypass for development...")
    
    # Environment variables to disable authentication for specific endpoints
    env_vars = {
        'DEV_DISABLE_AUTH': 'true',
        'DEV_BYPASS_ENDPOINTS': '/api/providers/*,/api/plugins/*',
        'DEV_MODE': 'true',
        'AUTH_ENABLE_RATE_LIMITING': 'false',
        'AUTH_RATE_LIMIT_MAX_REQUESTS': '1000',
    }
    
    # Create a .env.dev file
    with open('.env.dev', 'w') as f:
        f.write("# Temporary Development Environment Variables\n")
        f.write("# DO NOT USE IN PRODUCTION\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Created .env.dev file with development settings")
    
    # Also export them for current session
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    print("\n🚀 To apply these settings:")
    print("1. Stop the current server (Ctrl+C)")
    print("2. Run: source .env.dev && python main.py")
    print("3. Or restart with: DEV_DISABLE_AUTH=true python main.py")
    
    return env_vars

def create_test_user_script():
    """Create a script to add a test user with known credentials."""
    
    script_content = '''#!/usr/bin/env python3
"""
Create Test User Script
Run this to create a test user with known credentials.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def create_test_user():
    try:
        from ai_karen_engine.auth.service import AuthService
        from ai_karen_engine.database.client import DatabaseClient
        
        # Initialize database and auth service
        db_client = DatabaseClient()
        auth_service = AuthService(db_client)
        
        # Create test user
        test_email = "test@example.com"
        test_password = "testpass123"
        
        print(f"🔧 Creating test user: {test_email}")
        
        user_data = await auth_service.create_user(
            email=test_email,
            password=test_password,
            full_name="Test User",
            roles=["admin", "user"]
        )
        
        print(f"✅ Test user created successfully!")
        print(f"📧 Email: {test_email}")
        print(f"🔑 Password: {test_password}")
        print(f"👤 User ID: {user_data.get('user_id')}")
        
        # Test login
        print("\\n🧪 Testing login...")
        login_result = await auth_service.authenticate_user(
            email=test_email,
            password=test_password,
            ip_address="127.0.0.1",
            user_agent="test-script"
        )
        
        if login_result:
            print("✅ Login test successful!")
            print(f"🎫 Access token: {login_result.get('access_token', 'N/A')[:50]}...")
        else:
            print("❌ Login test failed")
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        print("💡 Make sure the database is running and accessible")

if __name__ == "__main__":
    asyncio.run(create_test_user())
'''
    
    with open('create_test_user.py', 'w') as f:
        f.write(script_content)
    
    os.chmod('create_test_user.py', 0o755)
    print("✅ Created create_test_user.py script")
    print("   Run: python create_test_user.py")

def main():
    print("🔧 Authentication Fix Options")
    print("=" * 50)
    
    print("\n1. 🚫 Temporary Auth Bypass (Recommended for Development)")
    create_auth_bypass_env()
    
    print("\n2. 👤 Create Test User")
    create_test_user_script()
    
    print("\n3. 🔍 Manual Token Creation")
    print("   If you have database access, you can manually create a long-lived token")
    
    print("\n" + "=" * 50)
    print("🎯 Recommended Next Steps:")
    print("1. Try option 1 (Auth Bypass) for immediate development")
    print("2. Use option 2 (Test User) for proper authentication testing")
    print("3. Fix the login credentials for production use")

if __name__ == "__main__":
    main()