#!/usr/bin/env python3
"""
Setup Single Admin User Script for AI Karen
Cleans up existing users and creates only one default admin user.
"""

import asyncio
import asyncpg
import bcrypt
import uuid
import os
import json
from datetime import datetime

async def setup_single_admin():
    """Clean up database and create single admin user"""
    
    # Database connection details from environment or defaults
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    # Admin user details
    admin_email = "admin@kari.ai"
    admin_password = "password123"
    
    try:
        print("🔧 Setting up single admin user...")
        print(f"Connecting to database at {db_config['host']}:{db_config['port']}")
        
        conn = await asyncpg.connect(**db_config)
        
        # Step 1: Clean up existing users and related data
        print("🧹 Cleaning up existing users...")
        
        # Delete all sessions first (due to foreign key constraints)
        sessions_deleted = await conn.execute("DELETE FROM auth_sessions")
        print(f"   ✅ Cleared auth_sessions ({sessions_deleted})")
        
        # Delete all user identities (if table exists)
        try:
            identities_deleted = await conn.execute("DELETE FROM user_identities")
            print(f"   ✅ Cleared user_identities ({identities_deleted})")
        except Exception:
            print("   ℹ️  user_identities table doesn't exist, skipping")
        
        # Delete all users (password_hash is in the same table)
        users_deleted = await conn.execute("DELETE FROM auth_users")
        print(f"   ✅ Cleared auth_users ({users_deleted})")
        
        # Step 2: Create single admin user
        print("👤 Creating admin user...")
        
        # Generate user ID and password hash
        user_id = str(uuid.uuid4())
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
        
        # Insert admin user with password hash in the same table
        await conn.execute("""
            INSERT INTO auth_users (
                user_id, tenant_id, email, full_name, password_hash, roles, 
                is_verified, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
        """, user_id, 'default', admin_email, 'Admin User', password_hash, 
             json.dumps(['admin', 'user']), True, True)
        
        print(f"   ✅ Created admin user: {admin_email}")
        print(f"   ✅ User ID: {user_id}")
        print("   ✅ Set admin password")
        
        # Step 3: Verify the setup
        print("🔍 Verifying setup...")
        
        # Check user count
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth_users")
        print(f"   ✅ Total users in database: {user_count}")
        
        # Verify admin user
        admin_user = await conn.fetchrow("""
            SELECT user_id, email, full_name, roles, is_verified, is_active, password_hash
            FROM auth_users
            WHERE email = $1
        """, admin_email)
        
        if admin_user:
            print(f"   ✅ Admin user verified:")
            print(f"      Email: {admin_user['email']}")
            print(f"      Name: {admin_user['full_name']}")
            print(f"      Roles: {admin_user['roles']}")
            print(f"      Verified: {admin_user['is_verified']}")
            print(f"      Active: {admin_user['is_active']}")
        else:
            print("   ❌ Admin user not found!")
            return False
        
        # Verify password hash
        stored_hash = admin_user['password_hash']
        
        if stored_hash and bcrypt.checkpw(admin_password.encode('utf-8'), stored_hash.encode('utf-8')):
            print("   ✅ Password hash verified")
        else:
            print("   ❌ Password hash verification failed!")
            return False
        
        await conn.close()
        
        print("\n🎉 Single admin user setup complete!")
        print(f"Default admin credentials:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print(f"\nYou can now login to the web UI at http://localhost:9002")
        print("⚠️  Remember to change the default password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_single_admin())
    if success:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")