#!/usr/bin/env python3
"""
Test script for LLM API routes
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.api_routes.llm_routes import list_providers, list_profiles, health_check_providers
from ai_karen_engine.integrations.llm_registry import get_registry

async def test_llm_routes():
    """Test the LLM API routes"""
    print("Testing LLM API Routes...")
    
    try:
        # Test provider listing
        print("\n1. Testing provider listing...")
        registry = get_registry()
        providers_result = await list_providers(registry)
        print(f"✅ Providers: {len(providers_result['providers'])} found")
        for provider in providers_result['providers']:
            print(f"   - {provider.name}: {provider.description}")
        
        # Test profile listing
        print("\n2. Testing profile listing...")
        profiles_result = await list_profiles()
        print(f"✅ Profiles: {len(profiles_result['profiles'])} found")
        for profile in profiles_result['profiles']:
            print(f"   - {profile.name}: chat={profile.providers['chat']}, code={profile.providers['code']}")
        
        # Test health check
        print("\n3. Testing health check...")
        health_result = await health_check_providers(None, registry)
        print(f"✅ Health check completed for {len(health_result['results'])} providers")
        for name, result in health_result['results'].items():
            status = result.get('status', 'unknown')
            print(f"   - {name}: {status}")
        
        print("\n🎉 All LLM API routes working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM routes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_routes())
    sys.exit(0 if success else 1)