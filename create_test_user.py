#!/usr/bin/env python3
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
        print("\n🧪 Testing login...")
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
