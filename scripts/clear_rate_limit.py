#!/usr/bin/env python3
"""
Clear rate limit for admin user
"""

import asyncio
import redis.asyncio as redis

async def clear_rate_limit():
    """Clear rate limit for admin user"""
    
    try:
        print("Connecting to Redis...")
        redis_client = redis.from_url("redis://:redis_secure_pass_change_me@localhost:6379/1")
        
        # Clear rate limit keys for admin user
        admin_email = "admin@ai-karen.dev"
        ip_address = "127.0.0.1"
        
        keys_to_clear = [
            f"rate_limit:user:{admin_email}:login_attempt",
            f"rate_limit:ip:{ip_address}:login_attempt",
            f"rate_limit:global:login_attempt"
        ]
        
        for key in keys_to_clear:
            result = await redis_client.delete(key)
            print(f"Cleared key {key}: {result}")
        
        # Also clear any lockout keys
        lockout_keys = [
            f"lockout:user:{admin_email}",
            f"lockout:ip:{ip_address}"
        ]
        
        for key in lockout_keys:
            result = await redis_client.delete(key)
            print(f"Cleared lockout key {key}: {result}")
        
        await redis_client.close()
        print("✅ Rate limits cleared")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing rate limits: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(clear_rate_limit())
    if success:
        print("\n🎉 Rate limits cleared! You can now try logging in again.")
    else:
        print("\n💥 Failed to clear rate limits.")