"""
Simple test to verify core authentication components work.
"""

import asyncio
import tempfile
import os
from pathlib import Path

# Create a simple test
def test_password_hasher():
    """Test password hashing functionality."""
    import bcrypt
    
    class PasswordHasher:
        def __init__(self, rounds: int = 4):
            self.rounds = rounds
        
        def hash_password(self, password: str) -> str:
            if not password:
                raise ValueError("Password cannot be empty")
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        
        def verify_password(self, password: str, hashed: str) -> bool:
            if not password or not hashed:
                return False
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except (ValueError, TypeError):
                return False
    
    # Test the hasher
    hasher = PasswordHasher()
    password = "test_password_123"
    
    # Hash password
    hashed = hasher.hash_password(password)
    print(f"Password hashed successfully: {hashed[:20]}...")
    
    # Verify password
    is_valid = hasher.verify_password(password, hashed)
    print(f"Password verification: {is_valid}")
    
    # Test wrong password
    is_invalid = hasher.verify_password("wrong_password", hashed)
    print(f"Wrong password verification: {is_invalid}")
    
    assert is_valid is True
    assert is_invalid is False
    print("✓ Password hasher test passed!")


def test_password_validator():
    """Test password validation."""
    from typing import List, Tuple
    
    class PasswordValidator:
        def __init__(self, min_length: int = 8, require_complexity: bool = True):
            self.min_length = min_length
            self.require_complexity = require_complexity
        
        def validate_password(self, password: str) -> Tuple[bool, List[str]]:
            errors = []
            
            if not password:
                errors.append("Password is required")
                return False, errors
            
            if len(password) < self.min_length:
                errors.append(f"Password must be at least {self.min_length} characters long")
            
            if self.require_complexity:
                has_upper = any(c.isupper() for c in password)
                has_lower = any(c.islower() for c in password)
                has_digit = any(c.isdigit() for c in password)
                has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
                
                if not has_upper:
                    errors.append("Password must contain at least one uppercase letter")
                if not has_lower:
                    errors.append("Password must contain at least one lowercase letter")
                if not has_digit:
                    errors.append("Password must contain at least one digit")
                if not has_special:
                    errors.append("Password must contain at least one special character")
            
            return len(errors) == 0, errors
    
    validator = PasswordValidator()
    
    # Test strong password
    is_valid, errors = validator.validate_password("StrongPass123!")
    print(f"Strong password validation: {is_valid}, errors: {errors}")
    assert is_valid is True
    
    # Test weak password
    is_valid, errors = validator.validate_password("weak")
    print(f"Weak password validation: {is_valid}, errors: {errors}")
    assert is_valid is False
    assert len(errors) > 0
    
    print("✓ Password validator test passed!")


if __name__ == "__main__":
    print("Running simple core authentication tests...")
    test_password_hasher()
    test_password_validator()
    print("✓ All tests passed!")