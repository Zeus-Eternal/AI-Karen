#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import AuthUser

def check_user():
    """Check if test user exists and show details"""
    try:
        with get_db_session_context() as session:
            user = session.query(AuthUser).filter(AuthUser.email == "test@example.com").first()
            if user:
                print(f"User found: {user.email}")
                print(f"User ID: {user.user_id}")
                print(f"Password hash: {user.password_hash}")
                print(f"Is active: {user.is_active}")
                print(f"Is verified: {user.is_verified}")
                print(f"Tenant ID: {user.tenant_id}")
                return True
            else:
                print("User not found")
                return False
    except Exception as e:
        print(f"Error checking user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_user()