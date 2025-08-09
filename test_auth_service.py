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

async def test_auth_service():
    """Test the authentication service directly"""
    try:
        print("Getting auth service...")
        auth_service = await get_auth_service()
        print("Auth service obtained successfully")
        
        print("Testing authentication...")
        user_data = await auth_service.authenticate_user(
            email="test@example.com",
            password="testpassword",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if user_data:
            print("✅ Authentication successful!")
            print(f"User ID: {user_data.user_id}")
            print(f"Email: {user_data.email}")
            print(f"Tenant ID: {user_data.tenant_id}")
            print(f"Is verified: {user_data.is_verified}")
            return True
        else:
            print("❌ Authentication failed - returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing auth service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_auth_service())