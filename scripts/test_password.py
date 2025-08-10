#!/usr/bin/env python3
"""
Test password verification for admin user
"""

import asyncio
import asyncpg
import bcrypt

async def test_password():
    """Test password verification"""
    
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
        
        # Get admin user and password hash
        admin_data = await conn.fetchrow("""
            SELECT u.user_id, u.email, u.full_name, u.is_active, u.is_verified, h.password_hash
            FROM auth_users u
            LEFT JOIN auth_password_hashes h ON u.user_id = h.user_id
            WHERE u.email = $1
        """, "admin@ai-karen.dev")
        
        if not admin_data:
            print("❌ Admin user not found")
            return False
        
        print(f"✅ Admin user found:")
        print(f"   Email: {admin_data['email']}")
        print(f"   Active: {admin_data['is_active']}")
        print(f"   Verified: {admin_data['is_verified']}")
        print(f"   Has password hash: {'Yes' if admin_data['password_hash'] else 'No'}")
        
        if not admin_data['password_hash']:
            print("❌ No password hash found")
            return False
        
        # Test password verification
        test_password = "admin123"
        try:
            password_valid = bcrypt.checkpw(
                test_password.encode('utf-8'), 
                admin_data['password_hash'].encode('utf-8')
            )
            print(f"✅ Password verification: {'Valid' if password_valid else 'Invalid'}")
            
            if not password_valid:
                print("❌ Password does not match stored hash")
                return False
                
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return False
        
        # Check if account is locked
        if admin_data.get('locked_until'):
            print(f"⚠️  Account locked until: {admin_data['locked_until']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing password: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_password())
    if success:
        print("\n🎉 Password verification successful!")
    else:
        print("\n💥 Password verification failed.")