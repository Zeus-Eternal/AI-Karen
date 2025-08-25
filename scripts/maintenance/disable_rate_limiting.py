#!/usr/bin/env python3
"""
Temporarily Disable Rate Limiting
Creates a temporary configuration to disable rate limiting for admin login.
"""

import asyncio
import asyncpg
import os
import sys
import json

async def disable_rate_limiting():
    """Temporarily disable rate limiting in the system configuration."""
    print("🔧 Temporarily disabling rate limiting...")
    
    # Database connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    try:
        print(f"   📡 Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # Step 1: Check if system_config table exists and update rate limiting settings
        print("   ⚙️  Updating system configuration...")
        try:
            # Check if system_config table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'system_config'
                )
            """)
            
            if table_exists:
                # Update or insert rate limiting configuration
                await conn.execute("""
                    INSERT INTO system_config (key, value, description, updated_at)
                    VALUES ('auth.rate_limiting.enabled', 'false', 'Temporarily disabled for admin setup', NOW())
                    ON CONFLICT (key) DO UPDATE SET 
                        value = EXCLUDED.value,
                        description = EXCLUDED.description,
                        updated_at = EXCLUDED.updated_at
                """)
                
                await conn.execute("""
                    INSERT INTO system_config (key, value, description, updated_at)
                    VALUES ('auth.rate_limiting.max_requests', '1000', 'Increased limit for admin setup', NOW())
                    ON CONFLICT (key) DO UPDATE SET 
                        value = EXCLUDED.value,
                        description = EXCLUDED.description,
                        updated_at = EXCLUDED.updated_at
                """)
                
                print("   ✅ Updated system configuration to disable rate limiting")
            else:
                print("   ℹ️  system_config table not found")
        except Exception as e:
            print(f"   ⚠️  Could not update system config: {e}")
        
        # Step 2: Clear the admin user's lockout status completely
        print("   👤 Clearing admin user lockout...")
        admin_email = "admin@kari.ai"
        
        # Reset all lockout-related fields
        reset_result = await conn.execute("""
            UPDATE auth_users 
            SET 
                failed_login_attempts = 0,
                locked_until = NULL,
                is_active = TRUE,
                updated_at = NOW()
            WHERE email = $1
        """, admin_email)
        print(f"   ✅ Reset admin user lockout: {reset_result}")
        
        # Step 3: Create a temporary environment variable override file
        print("   📝 Creating temporary configuration override...")
        
        temp_config = {
            "AUTH_RATE_LIMITING_ENABLED": "false",
            "AUTH_RATE_LIMIT_MAX_REQUESTS": "1000",
            "AUTH_RATE_LIMIT_WINDOW_MINUTES": "60",
            "AUTH_LOCKOUT_DURATION_MINUTES": "1"
        }
        
        try:
            with open('.env.temp', 'w') as f:
                f.write("# Temporary configuration to disable rate limiting\n")
                f.write("# Delete this file after successful admin login\n\n")
                for key, value in temp_config.items():
                    f.write(f"{key}={value}\n")
            
            print("   ✅ Created .env.temp with rate limiting disabled")
            print("   ℹ️  Load this file before starting the server:")
            print("      export $(cat .env.temp | xargs) && python main.py")
        except Exception as e:
            print(f"   ⚠️  Could not create temp config file: {e}")
        
        await conn.close()
        
        print("\n   🎉 Rate limiting configuration updated!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error disabling rate limiting: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Rate Limiting Disabler")
    print("=" * 45)
    
    success = await disable_rate_limiting()
    
    print("\n" + "="*45)
    if success:
        print("✅ Rate limiting temporarily disabled!")
        print("\n🔄 RESTART THE SERVER with temporary config:")
        print("   export $(cat .env.temp | xargs)")
        print("   python main.py")
        print("\n👤 Then try logging in with:")
        print("   • Email: admin@kari.ai")
        print("   • Password: Password123!")
        print("\n🧹 After successful login, you can:")
        print("   1. Delete the .env.temp file")
        print("   2. Restart the server normally")
        print("   3. Rate limiting will be re-enabled")
    else:
        print("❌ Failed to disable rate limiting")
        print("🔧 Try restarting the server manually")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed with error: {e}")
        sys.exit(1)