#!/usr/bin/env python3
"""
Setup Admin User - Proper Schema Version
Creates admin user using the correct database schema with separate password table.
"""

import asyncio
import asyncpg
import bcrypt
import uuid
import os
import sys
import json
from datetime import datetime, timezone

async def setup_admin_user():
    """Set up admin user using the correct database schema."""
    print("👤 Setting up admin user with proper schema...")
    
    # Database connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    # Admin user details (password meets complexity requirements)
    admin_email = "admin@kari.ai"
    admin_password = "Password123!"  # Uppercase, lowercase, digit, special char
    
    try:
        print(f"   📡 Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # Step 1: Check if admin user already exists
        existing_user = await conn.fetchrow("""
            SELECT user_id, email, roles, is_active, tenant_id 
            FROM auth_users 
            WHERE email = $1
        """, admin_email)
        
        if existing_user:
            print(f"   ✅ Admin user {admin_email} already exists")
            print(f"      User ID: {existing_user['user_id']}")
            print(f"      Roles: {existing_user['roles']}")
            print(f"      Active: {existing_user['is_active']}")
            print(f"      Tenant: {existing_user['tenant_id']}")
            
            # Check if password exists
            password_exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM auth_password_hashes WHERE user_id = $1)
            """, existing_user['user_id'])
            
            if not password_exists:
                print("   🔧 Setting up password for existing user...")
                # Hash password
                salt = bcrypt.gensalt(rounds=12)
                password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
                
                # Insert password
                await conn.execute("""
                    INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET 
                        password_hash = EXCLUDED.password_hash,
                        updated_at = EXCLUDED.updated_at
                """, existing_user['user_id'], password_hash, 
                     datetime.now(timezone.utc), datetime.now(timezone.utc))
                
                print("   ✅ Password set for existing admin user")
            else:
                print("   ✅ Password already exists for admin user")
            
            await conn.close()
            return True
        
        # Step 2: Create new admin user
        print(f"   🔧 Creating new admin user: {admin_email}")
        
        # Generate IDs
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        
        # Hash password
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
        
        # Step 3: Create tenant first (if needed)
        tenant_exists = await conn.fetchval("""
            SELECT EXISTS(SELECT 1 FROM tenants WHERE id = $1)
        """, uuid.UUID(tenant_id))
        
        if not tenant_exists:
            try:
                await conn.execute("""
                    INSERT INTO tenants (id, name, slug, subscription_tier, settings, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, uuid.UUID(tenant_id), 'Default Tenant', 'default', 'premium',
                     json.dumps({'max_users': 1000, 'features': ['chat', 'memory', 'llm']}),
                     True, datetime.now(timezone.utc), datetime.now(timezone.utc))
                print(f"   ✅ Created tenant: {tenant_id}")
            except Exception as tenant_error:
                print(f"   ⚠️  Tenant creation failed: {tenant_error}")
                # Use existing default tenant or create a simple one
                tenant_id = str(uuid.uuid4())
        
        # Step 4: Insert admin user
        await conn.execute("""
            INSERT INTO auth_users (
                user_id, email, full_name, roles, tenant_id, preferences,
                is_verified, is_active, created_at, updated_at, last_login_at,
                failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10, $11,
                $12, $13, $14, $15
            )
        """, uuid.UUID(user_id), admin_email, 'Admin User', 
             json.dumps(['admin', 'user']), uuid.UUID(tenant_id),
             json.dumps({
                 'personalityTone': 'professional',
                 'personalityVerbosity': 'balanced',
                 'preferredLLMProvider': 'llama-cpp',
                 'preferredModel': 'llama3.2:latest',
                 'memoryDepth': 'high',
                 'customPersonaInstructions': 'You are an AI assistant with administrative privileges.'
             }),
             True,  # is_verified
             True,  # is_active
             datetime.now(timezone.utc),  # created_at
             datetime.now(timezone.utc),  # updated_at
             None,  # last_login_at
             0,     # failed_login_attempts
             None,  # locked_until
             False, # two_factor_enabled
             None   # two_factor_secret
        )
        
        print(f"   ✅ Created admin user: {user_id}")
        
        # Step 5: Insert password hash
        await conn.execute("""
            INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
            VALUES ($1, $2, $3, $4)
        """, uuid.UUID(user_id), password_hash, 
             datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        print("   ✅ Set admin password")
        
        # Step 6: Verify the setup
        print("   🔍 Verifying setup...")
        
        # Check user
        admin_user = await conn.fetchrow("""
            SELECT user_id, email, full_name, roles, is_verified, is_active, tenant_id
            FROM auth_users
            WHERE email = $1
        """, admin_email)
        
        if admin_user:
            print(f"   ✅ Admin user verified:")
            print(f"      User ID: {admin_user['user_id']}")
            print(f"      Email: {admin_user['email']}")
            print(f"      Name: {admin_user['full_name']}")
            print(f"      Roles: {admin_user['roles']}")
            print(f"      Verified: {admin_user['is_verified']}")
            print(f"      Active: {admin_user['is_active']}")
            print(f"      Tenant: {admin_user['tenant_id']}")
        
        # Verify password hash
        stored_hash = await conn.fetchval("""
            SELECT password_hash FROM auth_password_hashes WHERE user_id = $1
        """, admin_user['user_id'])
        
        if stored_hash and bcrypt.checkpw(admin_password.encode('utf-8'), stored_hash.encode('utf-8')):
            print("   ✅ Password hash verified")
        else:
            print("   ❌ Password hash verification failed!")
            await conn.close()
            return False
        
        await conn.close()
        
        print("\n🎉 Admin user setup complete!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error setting up admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Admin User Setup (Proper Schema)")
    print("=" * 50)
    
    success = await setup_admin_user()
    
    print("\n" + "="*50)
    if success:
        print("✅ Admin user setup completed successfully!")
        print("\n👤 Default Admin Credentials:")
        print("   • Email: admin@kari.ai")
        print("   • Password: Password123!")
        print("   • Roles: admin, user")
        print("\n🌐 You can now login to the web UI")
        print("⚠️  Remember to change the password after first login!")
        return True
    else:
        print("❌ Admin user setup failed - check the logs above")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)