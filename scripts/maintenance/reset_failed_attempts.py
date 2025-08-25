#!/usr/bin/env python3
"""
Reset failed login attempts for admin user
"""

import asyncio
import asyncpg

async def reset_failed_attempts():
    """Reset failed login attempts"""
    
    # Database connection details
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'karen_user',
        'password': 'karen_secure_pass_change_me',
        'database': 'ai_karen'
    }
    
    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(**db_config)
        
        # Reset failed login attempts and unlock the account
        admin_email = "admin@ai-karen.dev"
        
        print(f"Resetting failed attempts for {admin_email}")
        
        result = await conn.execute("""
            UPDATE auth_users 
            SET failed_login_attempts = 0, 
                locked_until = NULL,
                updated_at = NOW()
            WHERE email = $1
        """, admin_email)
        
        print("✅ Failed attempts reset")
        
        # Verify the update
        admin_user = await conn.fetchrow("""
            SELECT email, failed_login_attempts, locked_until, is_active, is_verified
            FROM auth_users 
            WHERE email = $1
        """, admin_email)
        
        if admin_user:
            print(f"✅ Admin user status:")
            print(f"   Email: {admin_user['email']}")
            print(f"   Failed attempts: {admin_user['failed_login_attempts']}")
            print(f"   Locked until: {admin_user['locked_until']}")
            print(f"   Active: {admin_user['is_active']}")
            print(f"   Verified: {admin_user['is_verified']}")
        else:
            print("❌ Admin user not found")
            return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting failed attempts: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(reset_failed_attempts())
    if success:
        print(f"\n🎉 Failed attempts reset successfully!")
        print(f"Admin account is now unlocked and ready for login.")
    else:
        print("\n💥 Failed to reset failed attempts.")