#!/usr/bin/env python3
"""
Quick diagnostic script to check rate limiting configuration and status
"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def test_rate_limits():
    """Test the current rate limiting configuration"""
    print("🔍 Testing AI Karen rate limiting configuration...")
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    base_url = "http://127.0.0.1:8000"
    
    # Test health endpoint (should not be rate limited)
    print("1. Testing health endpoint...")
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.get(f"{base_url}/health") as response:
                duration = time.time() - start_time
                print(f"   ✅ Health check: {response.status} ({duration:.2f}s)")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
    
    print()
    
    # Test multiple rapid requests to see rate limiting
    print("2. Testing rapid requests (10 requests in quick succession)...")
    async with aiohttp.ClientSession() as session:
        success_count = 0
        rate_limited_count = 0
        
        for i in range(10):
            try:
                start_time = time.time()
                async with session.get(f"{base_url}/health") as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        success_count += 1
                        print(f"   ✅ Request {i+1}: {response.status} ({duration:.2f}s)")
                    elif response.status == 429:
                        rate_limited_count += 1
                        print(f"   🚦 Request {i+1}: Rate limited (429)")
                    else:
                        print(f"   ⚠️  Request {i+1}: {response.status}")
                        
                # Small delay between requests
                await asyncio.sleep(0.1)
                        
            except Exception as e:
                print(f"   ❌ Request {i+1} failed: {e}")
    
    print()
    print(f"📊 Results: {success_count} successful, {rate_limited_count} rate limited")
    
    if rate_limited_count > 5:
        print("⚠️  High rate limiting detected - consider increasing limits")
    elif rate_limited_count == 0:
        print("✅ No rate limiting issues detected")
    else:
        print("ℹ️  Some rate limiting observed - this is normal")

if __name__ == "__main__":
    asyncio.run(test_rate_limits())