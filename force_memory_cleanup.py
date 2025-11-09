#!/usr/bin/env python3
"""
Force memory cleanup script for AI-Karen API.
This script connects to the running API and forces garbage collection and service cleanup.
"""

import asyncio
import aiohttp
import sys
import json

async def force_cleanup():
    """Force memory cleanup via API endpoints."""
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🧹 Forcing memory cleanup...")
            
            # Try to trigger garbage collection
            try:
                async with session.post(f"{base_url}/api/admin/gc") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Garbage collection: {result}")
                    else:
                        print(f"⚠️ GC endpoint returned {response.status}")
            except Exception as e:
                print(f"⚠️ GC endpoint not available: {e}")
            
            # Try to cleanup lazy services
            try:
                async with session.post(f"{base_url}/api/admin/cleanup-services") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Service cleanup: {result}")
                    else:
                        print(f"⚠️ Service cleanup returned {response.status}")
            except Exception as e:
                print(f"⚠️ Service cleanup endpoint not available: {e}")
            
            # Get current service status
            try:
                async with session.get(f"{base_url}/api/admin/services") as response:
                    if response.status == 200:
                        services = await response.json()
                        print(f"📊 Active services: {len(services)}")
                        for name, info in services.items():
                            if info.get('is_initialized'):
                                print(f"  - {name}: {info['state']} (used {info['usage_count']} times)")
                    else:
                        print(f"⚠️ Services endpoint returned {response.status}")
            except Exception as e:
                print(f"⚠️ Services endpoint not available: {e}")
                
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 AI-Karen Memory Cleanup Tool")
    success = asyncio.run(force_cleanup())
    
    if success:
        print("✅ Cleanup completed!")
        sys.exit(0)
    else:
        print("❌ Cleanup failed!")
        sys.exit(1)