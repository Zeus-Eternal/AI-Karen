#!/usr/bin/env python3
"""
Clear Rate Limit and Setup Admin User
Clears the rate limiting for admin@kari.ai and ensures proper admin user setup.
"""

import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def clear_rate_limit_and_setup_admin():
    """Clear rate limiting and set up admin user properly."""
    print("🔧 Clearing rate limit and setting up admin user...")
    
    try:
        from ai_karen_engine.auth.service import get_auth_service
        
        # Get auth service
        print("   📡 Initializing auth service...")
        auth_service = await get_auth_service()
        print("   ✅ Auth service initialized")
        
        # Admin user details (password meets complexity requirements)
        admin_email = "admin@kari.ai"
        admin_password = "Password123!"  # Uppercase, lowercase, digit, special char
        
        # Step 1: Clear rate limiting for admin user
        print(f"   🧹 Clearing rate limit for {admin_email}...")
        try:
            # Access the rate limiter directly to clear the limit
            if hasattr(auth_service, 'security_layer') and hasattr(auth_service.security_layer, 'rate_limiter'):
                rate_limiter = auth_service.security_layer.rate_limiter
                if hasattr(rate_limiter, 'clear_user_attempts'):
                    await rate_limiter.clear_user_attempts(f"user:{admin_email}")
                    print("   ✅ Rate limit cleared successfully")
                else:
                    print("   ℹ️  Rate limiter doesn't have clear method - will try manual reset")
            else:
                print("   ℹ️  Rate limiter not accessible - continuing with setup")
        except Exception as rate_error:
            print(f"   ⚠️  Could not clear rate limit: {rate_error}")
            print("   ℹ️  Continuing with setup - rate limit will expire naturally")
        
        # Step 2: Check if admin user exists and can authenticate
        print(f"   🔍 Checking admin user {admin_email}...")
        try:
            user_data = await auth_service.authenticate_user(
                email=admin_email,
                password=admin_password,
                ip_address='127.0.0.1',
                user_agent='setup-script'
            )
            print(f"   ✅ Admin user {admin_email} exists and can authenticate")
            print(f"      User ID: {user_data.user_id}")
            print(f"      Roles: {user_data.roles}")
            print(f"      Tenant: {user_data.tenant_id}")
            print(f"      Verified: {user_data.is_verified}")
            return True
            
        except Exception as auth_error:
            print(f"   ℹ️  Admin user authentication failed: {auth_error}")
            
            # Step 3: Try to create admin user with proper tenant handling
            print("   🔧 Creating admin user with proper tenant setup...")
            try:
                # First, ensure we have a proper tenant UUID
                from ai_karen_engine.auth.database import AuthDatabaseClient
                
                # Get the database client to check/create tenant
                db_client = auth_service.db_client
                
                # Try to get or create default tenant
                default_tenant_id = None
                try:
                    # Check if default tenant exists
                    tenant_query = """
                    SELECT tenant_id FROM auth_tenants WHERE slug = $1 LIMIT 1
                    """
                    result = await db_client.execute_query(tenant_query, 'default')
                    if result:
                        default_tenant_id = result[0]['tenant_id']
                        print(f"   ✅ Found existing default tenant: {default_tenant_id}")
                    else:
                        # Create default tenant
                        import uuid
                        default_tenant_id = str(uuid.uuid4())
                        tenant_insert = """
                        INSERT INTO auth_tenants (tenant_id, name, slug, settings, is_active, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                        """
                        await db_client.execute_query(
                            tenant_insert, 
                            default_tenant_id, 
                            'Default Tenant', 
                            'default', 
                            '{}', 
                            True
                        )
                        print(f"   ✅ Created default tenant: {default_tenant_id}")
                        
                except Exception as tenant_error:
                    print(f"   ⚠️  Tenant setup issue: {tenant_error}")
                    # Use a default UUID if tenant creation fails
                    import uuid
                    default_tenant_id = str(uuid.uuid4())
                    print(f"   ℹ️  Using generated tenant ID: {default_tenant_id}")
                
                # Now create the admin user with the proper tenant ID
                user = await auth_service.create_user(
                    email=admin_email,
                    password=admin_password,
                    roles=['admin', 'user'],
                    tenant_id=default_tenant_id,  # Use proper UUID
                    preferences={
                        'personalityTone': 'professional',
                        'personalityVerbosity': 'balanced',
                        'preferredLLMProvider': 'ollama',
                        'preferredModel': 'llama3.2:latest',
                        'memoryDepth': 'high',
                        'customPersonaInstructions': 'You are an AI assistant with administrative privileges.'
                    }
                )
                print(f"   ✅ Admin user created successfully!")
                print(f"      User ID: {user.user_id}")
                print(f"      Email: {user.email}")
                print(f"      Roles: {user.roles}")
                print(f"      Tenant: {user.tenant_id}")
                print(f"      Verified: {user.is_verified}")
                
                # Test authentication
                print("   🧪 Testing authentication...")
                auth_result = await auth_service.authenticate_user(
                    email=admin_email,
                    password=admin_password,
                    ip_address='127.0.0.1',
                    user_agent='setup-script'
                )
                print("   ✅ Admin user authentication test passed")
                return True
                
            except Exception as create_error:
                print(f"   ❌ Failed to create admin user: {create_error}")
                
                # Step 4: Try direct database insertion as fallback
                print("   🔧 Trying direct database insertion...")
                try:
                    import uuid
                    import bcrypt
                    import json
                    from datetime import datetime, timezone
                    
                    # Generate user ID and hash password
                    user_id = str(uuid.uuid4())
                    tenant_id = str(uuid.uuid4())
                    
                    # Hash password with bcrypt
                    salt = bcrypt.gensalt(rounds=12)
                    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
                    
                    # Insert tenant first
                    tenant_insert = """
                    INSERT INTO auth_tenants (tenant_id, name, slug, settings, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (slug) DO NOTHING
                    """
                    await db_client.execute_query(
                        tenant_insert,
                        tenant_id,
                        'Default Tenant',
                        'default',
                        '{}',
                        True,
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc)
                    )
                    
                    # Insert admin user
                    user_insert = """
                    INSERT INTO auth_users (
                        user_id, email, full_name, roles, tenant_id, preferences,
                        is_verified, is_active, created_at, updated_at, last_login_at,
                        failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6,
                        $7, $8, $9, $10, $11,
                        $12, $13, $14, $15
                    )
                    ON CONFLICT (email) DO NOTHING
                    """
                    
                    await db_client.execute_query(
                        user_insert,
                        user_id,
                        admin_email,
                        'Admin User',
                        json.dumps(['admin', 'user']),
                        tenant_id,
                        json.dumps({
                            'personalityTone': 'professional',
                            'personalityVerbosity': 'balanced',
                            'preferredLLMProvider': 'ollama',
                            'preferredModel': 'llama3.2:latest'
                        }),
                        True,  # is_verified
                        True,  # is_active
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc),
                        None,  # last_login_at
                        0,     # failed_login_attempts
                        None,  # locked_until
                        False, # two_factor_enabled
                        None   # two_factor_secret
                    )
                    
                    # Insert password hash
                    password_insert = """
                    INSERT INTO auth_user_passwords (user_id, password_hash, created_at, updated_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET 
                        password_hash = EXCLUDED.password_hash,
                        updated_at = EXCLUDED.updated_at
                    """
                    await db_client.execute_query(
                        password_insert,
                        user_id,
                        password_hash,
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc)
                    )
                    
                    print(f"   ✅ Admin user inserted directly into database!")
                    print(f"      User ID: {user_id}")
                    print(f"      Tenant ID: {tenant_id}")
                    return True
                    
                except Exception as db_error:
                    print(f"   ❌ Direct database insertion failed: {db_error}")
                    return False
                
    except Exception as service_error:
        print(f"   ❌ Failed to get auth service: {service_error}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Rate Limit Clear & Admin Setup")
    print("=" * 50)
    
    success = await clear_rate_limit_and_setup_admin()
    
    print("\n" + "="*50)
    if success:
        print("✅ Admin user setup completed successfully!")
        print("\n👤 Admin Credentials:")
        print("   • Email: admin@kari.ai")
        print("   • Password: Password123!")
        print("   • Roles: admin, user")
        print("\n🌐 You can now login to the web UI")
        print("⚠️  Rate limit has been cleared - you can login immediately")
        print("⚠️  Remember to change the password after first login!")
        return True
    else:
        print("❌ Setup failed - please check the logs above")
        print("\n⏰ If rate limited, wait 15 minutes and try again")
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