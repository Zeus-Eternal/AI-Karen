#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_karen_engine.auth.service import get_auth_service

async def create_test_user():
    """Create test user using the auth service"""
    try:
        print("🚀 Creating test user using auth service...")
        
        # Get auth service
        auth_service = await get_auth_service()
        print("✅ Auth service obtained")
        
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email("test@example.com")
        if existing_user:
            print("✅ Test user already exists in auth system")
            print(f"  User ID: {existing_user.user_id}")
            print(f"  Email: {existing_user.email}")
            print(f"  Is verified: {existing_user.is_verified}")
            return True
        
        # Create test user
        print("👤 Creating test user...")
        user_data = await auth_service.create_user(
            email="test@example.com",
            password="testpassword",
            full_name="Test User",
            tenant_id="default",
            roles=["user"],
            ip_address="127.0.0.1",
            user_agent="setup-script"
        )
        
        print("✅ Test user created successfully!")
        print(f"  User ID: {user_data.user_id}")
        print(f"  Email: {user_data.email}")
        print(f"  Tenant ID: {user_data.tenant_id}")
        print(f"  Is verified: {user_data.is_verified}")
        print("  Password: testpassword")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(create_test_user())