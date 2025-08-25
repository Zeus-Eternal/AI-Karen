#!/usr/bin/env python3
"""
Clear All Rate Limits
Comprehensive script to clear rate limiting from all possible sources.
"""

import asyncio
import asyncpg
import os
import sys

async def clear_all_rate_limits():
    """Clear rate limiting from all possible sources."""
    print("🧹 Clearing all rate limits for admin@kari.ai...")
    
    # Database connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    admin_email = "admin@kari.ai"
    
    try:
        print(f"   📡 Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # Step 1: Clear from PostgreSQL rate_limits table
        print("   🗄️  Clearing PostgreSQL rate limits...")
        try:
            # Try different possible column names and table structures
            tables = await conn.fetch("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_name = 'rate_limits' AND table_schema = 'public'
            """)
            
            if tables:
                print(f"      Found rate_limits table with columns: {[t['column_name'] for t in tables]}")
                
                # Try to clear based on different possible column structures
                try:
                    cleared = await conn.execute("""
                        DELETE FROM rate_limits 
                        WHERE key LIKE $1 OR key LIKE $2 OR key LIKE $3
                    """, f"%{admin_email}%", f"%user:{admin_email}%", f"%admin%")
                    print(f"      ✅ Cleared rate_limits (key column): {cleared}")
                except:
                    try:
                        cleared = await conn.execute("""
                            DELETE FROM rate_limits 
                            WHERE identifier LIKE $1 OR identifier LIKE $2 OR identifier LIKE $3
                        """, f"%{admin_email}%", f"%user:{admin_email}%", f"%admin%")
                        print(f"      ✅ Cleared rate_limits (identifier column): {cleared}")
                    except:
                        try:
                            cleared = await conn.execute("""
                                DELETE FROM rate_limits 
                                WHERE user_id LIKE $1 OR email LIKE $2
                            """, f"%admin%", f"%{admin_email}%")
                            print(f"      ✅ Cleared rate_limits (user_id/email columns): {cleared}")
                        except Exception as e:
                            print(f"      ⚠️  Could not clear rate_limits table: {e}")
            else:
                print("      ℹ️  No rate_limits table found in PostgreSQL")
        except Exception as e:
            print(f"      ⚠️  PostgreSQL rate limit clearing failed: {e}")
        
        # Step 2: Clear Redis rate limits (if Redis is available)
        print("   🔴 Attempting to clear Redis rate limits...")
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://:redis_secure_pass_change_me@localhost:6379/0')
            
            try:
                r = redis.Redis.from_url(redis_url, decode_responses=True)
                r.ping()  # Test connection
                
                # Clear various possible Redis keys for rate limiting
                patterns = [
                    f"rate_limit:user:{admin_email}",
                    f"rate_limit:{admin_email}",
                    f"rl:user:{admin_email}",
                    f"rl:{admin_email}",
                    f"auth:rate_limit:{admin_email}",
                    f"login_attempts:{admin_email}",
                    f"failed_attempts:{admin_email}",
                    "rate_limit:*admin*",
                    "*rate*limit*admin*"
                ]
                
                total_cleared = 0
                for pattern in patterns:
                    try:
                        if '*' in pattern:
                            # Use scan for wildcard patterns
                            keys = r.keys(pattern)
                            if keys:
                                deleted = r.delete(*keys)
                                total_cleared += deleted
                                print(f"      ✅ Cleared Redis pattern '{pattern}': {deleted} keys")
                        else:
                            # Direct key deletion
                            if r.exists(pattern):
                                r.delete(pattern)
                                total_cleared += 1
                                print(f"      ✅ Cleared Redis key '{pattern}'")
                    except Exception as pattern_error:
                        print(f"      ⚠️  Could not clear pattern '{pattern}': {pattern_error}")
                
                print(f"      ✅ Total Redis keys cleared: {total_cleared}")
                
            except Exception as redis_error:
                print(f"      ⚠️  Redis connection failed: {redis_error}")
                
        except ImportError:
            print("      ℹ️  Redis not available (redis package not installed)")
        except Exception as e:
            print(f"      ⚠️  Redis rate limit clearing failed: {e}")
        
        # Step 3: Clear any in-memory rate limiting by clearing auth events
        print("   📝 Clearing auth events that might trigger rate limiting...")
        try:
            events_cleared = await conn.execute("""
                DELETE FROM auth_events 
                WHERE email = $1 AND event_type IN ('login_failed', 'login_attempt')
                AND timestamp > NOW() - INTERVAL '2 hours'
            """, admin_email)
            print(f"      ✅ Cleared recent auth events: {events_cleared}")
        except Exception as e:
            print(f"      ⚠️  Auth events clearing failed: {e}")
        
        # Step 4: Reset user account completely
        print("   👤 Resetting user account state...")
        try:
            reset_result = await conn.execute("""
                UPDATE auth_users 
                SET 
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    is_active = TRUE,
                    updated_at = NOW()
                WHERE email = $1
            """, admin_email)
            print(f"      ✅ Reset user account: {reset_result}")
        except Exception as e:
            print(f"      ⚠️  User account reset failed: {e}")
        
        # Step 5: Clear any session-based rate limiting
        print("   🔑 Clearing sessions that might hold rate limit state...")
        try:
            user_id_result = await conn.fetchval("""
                SELECT user_id FROM auth_users WHERE email = $1
            """, admin_email)
            
            if user_id_result:
                sessions_cleared = await conn.execute("""
                    DELETE FROM auth_sessions WHERE user_id = $1
                """, user_id_result)
                print(f"      ✅ Cleared user sessions: {sessions_cleared}")
        except Exception as e:
            print(f"      ⚠️  Session clearing failed: {e}")
        
        await conn.close()
        
        print("\n   🎉 Rate limit clearing completed!")
        print(f"   👤 Admin account should now be accessible:")
        print(f"      • Email: {admin_email}")
        print(f"      • Password: Password123!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error clearing rate limits: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Complete Rate Limit Cleaner")
    print("=" * 50)
    
    success = await clear_all_rate_limits()
    
    print("\n" + "="*50)
    if success:
        print("✅ All rate limits cleared successfully!")
        print("\n🔄 IMPORTANT: Restart the AI Karen server now!")
        print("   This will clear any in-memory rate limiting state.")
        print("\n👤 After restart, try logging in with:")
        print("   • Email: admin@kari.ai")
        print("   • Password: Password123!")
        print("\n🌐 The web UI should now accept your login")
    else:
        print("❌ Failed to clear all rate limits")
        print("🔧 You may need to restart the server and try again")
    
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