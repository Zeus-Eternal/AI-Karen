#!/usr/bin/env python3
"""
Clear all rate limits and lockouts
"""

import asyncio
import redis.asyncio as redis

async def clear_all_rate_limits():
    """Clear all rate limits"""
    
    try:
        print("Connecting to Redis...")
        # Try both Redis databases that might be used for rate limiting
        redis_urls = [
            "redis://:redis_secure_pass_change_me@localhost:6379/1",  # Rate limiting
            "redis://:redis_secure_pass_change_me@localhost:6379/0",  # Sessions
        ]
        
        total_cleared = 0
        
        for redis_url in redis_urls:
            print(f"\nChecking Redis database: {redis_url}")
            try:
                redis_client = redis.from_url(redis_url)
                
                # Get all keys that might be rate limit related
                all_keys = await redis_client.keys("*")
                print(f"Found {len(all_keys)} keys in this database")
                
                if all_keys:
                    print("All keys:")
                    for key in all_keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                        print(f"  - {key_str}")
                
                rate_limit_keys = []
                for key in all_keys:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                    if any(pattern in key_str.lower() for pattern in ['rate_limit', 'lockout', 'limit', 'block', 'user:', 'ip:']):
                        rate_limit_keys.append(key_str)
                
                print(f"Found {len(rate_limit_keys)} potential rate limit keys")
                
                if rate_limit_keys:
                    # Delete all rate limit keys
                    deleted = await redis_client.delete(*rate_limit_keys)
                    print(f"✅ Deleted {deleted} keys from this database")
                    total_cleared += deleted
                
                # Also try to clear some common patterns
                patterns_to_clear = [
                    "rate_limit:*",
                    "lockout:*",
                    "*rate_limit*",
                    "*lockout*",
                    "user:*",
                    "ip:*"
                ]
                
                for pattern in patterns_to_clear:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        deleted = await redis_client.delete(*keys)
                        print(f"✅ Cleared {deleted} keys matching pattern: {pattern}")
                        total_cleared += deleted
                
                await redis_client.aclose()
                
            except Exception as e:
                print(f"❌ Error with database {redis_url}: {e}")
        
        print(f"\n✅ Total keys cleared: {total_cleared}")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing rate limits: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(clear_all_rate_limits())
    if success:
        print("\n🎉 All rate limits cleared! You can now try logging in again.")
    else:
        print("\n💥 Failed to clear rate limits.")