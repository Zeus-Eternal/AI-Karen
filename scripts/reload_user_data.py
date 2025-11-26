#!/usr/bin/env python3
"""
Script to reload user data in the authentication service.
This forces the service to reload users from the JSON file.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_karen_engine.services.production_auth_service import AuthService
from datetime import datetime, timezone


async def reload_user_data():
    """Reload user data from the JSON file."""
    print("Reloading user data...")
    
    # Create auth service instance
    auth_service = AuthService()
    
    # Initialize and load users
    await auth_service.initialize()
    
    # Print user status
    print(f"Loaded {len(auth_service.users)} users:")
    for email, user in auth_service.users.items():
        locked_status = "LOCKED" if user.locked_until and user.locked_until > datetime.now(timezone.utc) else "UNLOCKED"
        print(f"  - {email}: {locked_status} (failed attempts: {user.failed_login_attempts})")
    
    print("User data reloaded successfully!")


if __name__ == "__main__":
    asyncio.run(reload_user_data())