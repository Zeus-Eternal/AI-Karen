#!/usr/bin/env python3
"""
Clear Rate Limit for Admin User
Simple script to clear rate limiting from the database directly.
"""

import asyncio
import asyncpg
import os
import sys

async def clear_rate_limit():
    """Clear rate limiting for admin user directly from database."""
    print("🧹 Clearing rate limit for admin@kari.ai...")
    
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
        
        # Clear rate limiting entries for admin user
        admin_email = "admin@kari.ai"
        
        # Clear from rate_limits table if it exists
        try:
            cleared_rate_limits = await conn.execute("""
                DELETE FROM rate_limits 
                WHERE identifier = $1 OR identifier LIKE $2
            """, f"user:{admin_email}", f"%{admin_email}%")
            print(f"   ✅ Cleared rate limit entries: {cleared_rate_limits}")
        except Exception as e:
            print(f"   ℹ️  Rate limits table not found or empty: {e}")
        
        # Reset failed login attempts in auth_users table
        try:
            reset_attempts = await conn.execute("""
                UPDATE auth_users 
                SET failed_login_attempts = 0, locked_until = NULL 
                WHERE email = $1
            """, admin_email)
            print(f"   ✅ Reset failed login attempts: {reset_attempts}")
        except Exception as e:
            print(f"   ℹ️  Could not reset auth_users attempts: {e}")
        
        # Clear any session-based rate limiting
        try:
            cleared_sessions = await conn.execute("""
                DELETE FROM auth_sessions 
                WHERE user_id IN (
                    SELECT user_id FROM auth_users WHERE email = $1
                )
            """, admin_email)
            print(f"   ✅ Cleared old sessions: {cleared_sessions}")
        except Exception as e:
            print(f"   ℹ️  Could not clear sessions: {e}")
        
        await conn.close()
        
        print("   ✅ Rate limit clearing completed!")
        print(f"\n👤 You can now try logging in with:")
        print(f"   • Email: {admin_email}")
        print(f"   • Password: Password123!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to clear rate limit: {e}")
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Rate Limit Cleaner")
    print("=" * 40)
    
    success = await clear_rate_limit()
    
    print("\n" + "="*40)
    if success:
        print("✅ Rate limit cleared successfully!")
        print("🌐 You can now try logging in to the web UI")
    else:
        print("❌ Failed to clear rate limit")
        print("⏰ You may need to wait for the rate limit to expire naturally")
    
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