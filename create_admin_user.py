#!/usr/bin/env python3
"""
Create Admin User Script for AI Karen
Creates a verified admin user account for getting started with the system.
"""

import asyncio
import requests
import json
import sys
import getpass
from typing import Optional

def create_admin_user(email: str, password: str, backend_url: str = "http://localhost:8000") -> bool:
    """
    Create and verify an admin user account.
    
    Args:
        email: Admin email address
        password: Admin password
        backend_url: Backend API URL
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Register the admin user
        print(f"Creating admin user: {email}")
        
        register_data = {
            "email": email,
            "password": password,
            "roles": ["admin", "user"]
        }
        
        response = requests.post(
            f"{backend_url}/api/auth/register",
            headers={"Content-Type": "application/json"},
            json=register_data,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data["user"]["user_id"]
            print(f"✅ Admin user registered successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Roles: {user_data['user']['roles']}")
        else:
            print(f"❌ Failed to register admin user: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        # Step 2: Verify the user in the database
        print("Verifying admin user in database...")
        
        try:
            # Updated to use PostgreSQL through the unified auth service
            async def verify_admin_user():
                from src.ai_karen_engine.auth.config import AuthConfig
                from src.ai_karen_engine.auth.database import AuthDatabaseClient
                
                config = AuthConfig.from_env()
                db_client = AuthDatabaseClient(config.database)
                await db_client.initialize_schema()
                
                # Verify the admin account
                async with db_client.session_factory() as session:
                    from sqlalchemy import text
                    await session.execute(text("""
                        UPDATE auth_users SET is_verified = true WHERE email = :email
                    """), {"email": email})
                    await session.commit()
                    
                    # Check the verification
                    result = await session.execute(text("""
                        SELECT email, is_verified, roles FROM auth_users WHERE email = :email
                    """), {"email": email})
                    admin_user = result.fetchone()
                    
                    if admin_user and admin_user.is_verified:
                        print(f"✅ Admin user verified in database!")
                        print(f"   Email: {admin_user.email}")
                        print(f"   Verified: {admin_user.is_verified}")
                        print(f"   Roles: {admin_user.roles}")
                        return True
                    else:
                        print("❌ Failed to verify admin user in database")
                        return False
            
            # Run the async verification
            verification_success = asyncio.run(verify_admin_user())
            if not verification_success:
                return False
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            return False
            
        # Step 3: Test login
        print("Testing admin login...")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data,
            timeout=10
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"✅ Admin login test successful!")
            print(f"   Access token: {login_result['access_token'][:50]}...")
            print(f"   User verified: {login_result['user']['is_verified']}")
            return True
        else:
            print(f"⚠️  Admin user created but login test failed: {login_response.status_code}")
            print(f"   This might be due to rate limiting. Try logging in manually.")
            return True  # Still consider it successful since user was created
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to create admin user interactively."""
    print("🔧 AI Karen Admin User Creator")
    print("=" * 40)
    
    # Get admin email
    default_email = "admin@karen.ai"
    email = input(f"Enter admin email (default: {default_email}): ").strip()
    if not email:
        email = default_email
    
    # Get admin password
    password = getpass.getpass("Enter admin password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        sys.exit(1)
    
    # Get backend URL
    default_backend = "http://localhost:8000"
    backend_url = input(f"Enter backend URL (default: {default_backend}): ").strip()
    if not backend_url:
        backend_url = default_backend
    
    print(f"\nCreating admin user with:")
    print(f"  Email: {email}")
    print(f"  Backend: {backend_url}")
    print()
    
    # Create the admin user
    success = create_admin_user(email, password, backend_url)
    
    if success:
        print("\n🎉 Admin user setup complete!")
        print(f"You can now login to the web UI at http://localhost:8010 with:")
        print(f"  Email: {email}")
        print(f"  Password: [the password you entered]")
    else:
        print("\n❌ Failed to create admin user. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()