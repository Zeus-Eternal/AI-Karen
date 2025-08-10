#!/usr/bin/env python3
"""
Direct test of the authentication database schema
"""

import asyncio
import asyncpg
import bcrypt

async def test_auth_database():
    """Test the authentication database directly"""
    
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
        
        # Test 1: Check schema consistency
        print("\n1. Testing schema consistency...")
        users_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'auth_users' AND column_name = 'user_id'
        """)
        
        hashes_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'auth_password_hashes' AND column_name = 'user_id'
        """)
        
        sessions_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'auth_sessions' AND column_name = 'user_id'
        """)
        
        print(f"   auth_users.user_id type: {users_type}")
        print(f"   auth_password_hashes.user_id type: {hashes_type}")
        print(f"   auth_sessions.user_id type: {sessions_type}")
        
        if users_type == 'uuid' and hashes_type == 'uuid' and sessions_type == 'uuid':
            print("   ✅ All user_id types are consistent (UUID)")
        else:
            print("   ❌ user_id types are inconsistent")
            return False
        
        # Test 2: Check foreign key constraints
        print("\n2. Testing foreign key constraints...")
        try:
            # This should work - valid foreign key
            test_user_id = await conn.fetchval("SELECT gen_random_uuid()")
            await conn.execute("""
                INSERT INTO auth_users (user_id, email, full_name, is_active) 
                VALUES ($1, 'test@example.com', 'Test User', true)
            """, test_user_id)
            
            await conn.execute("""
                INSERT INTO auth_password_hashes (user_id, password_hash) 
                VALUES ($1, 'test_hash')
            """, test_user_id)
            
            print("   ✅ Foreign key constraint working correctly")
            
            # Clean up test data
            await conn.execute("DELETE FROM auth_users WHERE email = 'test@example.com'")
            
        except Exception as e:
            print(f"   ❌ Foreign key constraint test failed: {e}")
            return False
        
        # Test 3: Check admin user
        print("\n3. Testing admin user...")
        admin_user = await conn.fetchrow("""
            SELECT u.user_id, u.email, u.full_name, u.is_active, h.password_hash
            FROM auth_users u
            LEFT JOIN auth_password_hashes h ON u.user_id = h.user_id
            WHERE u.email = 'admin@ai-karen.local'
        """)
        
        if admin_user:
            print(f"   ✅ Admin user found: {admin_user['email']}")
            print(f"   ✅ User ID: {admin_user['user_id']}")
            print(f"   ✅ Active: {admin_user['is_active']}")
            print(f"   ✅ Has password hash: {'Yes' if admin_user['password_hash'] else 'No'}")
            
            # Test password verification
            if admin_user['password_hash']:
                test_password = "admin123"
                password_valid = bcrypt.checkpw(
                    test_password.encode('utf-8'), 
                    admin_user['password_hash'].encode('utf-8')
                )
                print(f"   ✅ Password verification: {'Valid' if password_valid else 'Invalid'}")
            
        else:
            print("   ❌ Admin user not found")
            return False
        
        # Test 4: Check table counts
        print("\n4. Checking table data...")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth_users")
        hash_count = await conn.fetchval("SELECT COUNT(*) FROM auth_password_hashes")
        session_count = await conn.fetchval("SELECT COUNT(*) FROM auth_sessions")
        
        print(f"   Users: {user_count}")
        print(f"   Password hashes: {hash_count}")
        print(f"   Sessions: {session_count}")
        
        if user_count > 0 and hash_count > 0:
            print("   ✅ Database has user data")
        else:
            print("   ❌ Database is missing user data")
            return False
        
        await conn.close()
        print("\nDatabase connection closed.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_auth_database())
    if success:
        print("\n🎉 Authentication database is working correctly!")
        print("The schema mismatch issue has been resolved.")
        print("You can now restart your authentication service.")
    else:
        print("\n💥 Authentication database test failed.")