#!/usr/bin/env python3
"""
Test Pydantic validation for login request
"""

from pydantic import BaseModel, EmailStr, ValidationError

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def test_login_validation():
    """Test login request validation"""
    
    test_cases = [
        {
            "name": "Valid admin login",
            "data": {
                "email": "admin@ai-karen.local",
                "password": "admin123"
            }
        },
        {
            "name": "Simple email",
            "data": {
                "email": "admin@example.com",
                "password": "admin123"
            }
        },
        {
            "name": "Invalid email",
            "data": {
                "email": "not-an-email",
                "password": "admin123"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            login_req = LoginRequest(**test_case['data'])
            print(f"✅ Validation passed")
            print(f"   Email: {login_req.email}")
            print(f"   Password: {login_req.password}")
        except ValidationError as e:
            print(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    test_login_validation()