#!/usr/bin/env python3

import os
import sys
import bcrypt
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import AuthUser

def test_password():
    """Test password verification"""
    try:
        with get_db_session_context() as session:
            user = session.query(AuthUser).filter(AuthUser.email == "test@example.com").first()
            if user:
                print(f"User found: {user.email}")
                print(f"Password hash: {user.password_hash}")
                
                # Test password verification
                test_password = "testpassword"
                print(f"Testing password: {test_password}")
                
                # Verify password
                is_valid = bcrypt.checkpw(test_password.encode("utf-8"), user.password_hash.encode("utf-8"))
                print(f"Password verification result: {is_valid}")
                
                return is_valid
            else:
                print("User not found")
                return False
    except Exception as e:
        print(f"Error testing password: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_password()