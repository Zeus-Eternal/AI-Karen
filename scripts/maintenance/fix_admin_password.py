#!/usr/bin/env python3
"""
Fix the admin user password hash
"""

import asyncio
import asyncpg
import bcrypt

async def fix_admin_password():
    """Fix the admin user password"""
    
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
        
        # Generate correct password hash for "admin123"
        password = "admin123"
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        print(f"Generated password hash for '{password}'")
        
        # Update admin user password
        result = await conn.execute("""
            UPDATE auth_password_hashes 
            SET password_hash = $1, updated_at = NOW()
            WHERE user_id = (
                SELECT user_id FROM auth_users WHERE email = 'admin@ai-karen.local'
            )
        """, password_hash)
        
        print("✅ Admin password hash updated")
        
        # Verify the fix
        admin_hash = await conn.fetchval("""
            SELECT h.password_hash
            FROM auth_users u
            JOIN auth_password_hashes h ON u.user_id = h.user_id
            WHERE u.email = 'admin@ai-karen.local'
        """)
        
        if admin_hash:
            password_valid = bcrypt.checkpw(password.encode('utf-8'), admin_hash.encode('utf-8'))
            if password_valid:
                print("✅ Password verification successful!")
                print(f"✅ Admin login: admin@ai-karen.local / {password}")
            else:
                print("❌ Password verification still failing")
                return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing admin password: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_admin_password())
    if success:
        print("\n🎉 Admin password fixed successfully!")
    else:
        print("\n💥 Failed to fix admin password.")