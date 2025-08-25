#!/usr/bin/env python3
"""
Fix the admin user email to use a valid domain
"""

import asyncio
import asyncpg

async def fix_admin_email():
    """Fix the admin user email"""
    
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
        
        # Update admin user email to use a valid domain
        old_email = "admin@ai-karen.local"
        new_email = "admin@ai-karen.dev"
        
        print(f"Updating admin email from {old_email} to {new_email}")
        
        result = await conn.execute("""
            UPDATE auth_users 
            SET email = $1, updated_at = NOW()
            WHERE email = $2
        """, new_email, old_email)
        
        print("✅ Admin email updated")
        
        # Verify the update
        admin_user = await conn.fetchrow("""
            SELECT user_id, email, full_name, is_active
            FROM auth_users 
            WHERE email = $1
        """, new_email)
        
        if admin_user:
            print(f"✅ Admin user verified:")
            print(f"   Email: {admin_user['email']}")
            print(f"   Full Name: {admin_user['full_name']}")
            print(f"   Active: {admin_user['is_active']}")
        else:
            print("❌ Admin user not found after update")
            return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing admin email: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_admin_email())
    if success:
        print(f"\n🎉 Admin email fixed successfully!")
        print(f"New login credentials: admin@ai-karen.dev / admin123")
    else:
        print("\n💥 Failed to fix admin email.")