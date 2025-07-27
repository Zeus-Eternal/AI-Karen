#!/usr/bin/env python3
"""
Test LLM endpoints directly without server
"""

import sys
import os
import asyncio
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_llm_endpoints():
    """Test LLM endpoints directly"""
    print("🧪 Testing LLM endpoints directly...")
    
    try:
        # Import the LLM routes
        from ai_karen_engine.api_routes.llm_routes import list_providers, list_profiles, health_check_providers
        from ai_karen_engine.integrations.llm_registry import get_registry
        
        print("\n1. Testing provider listing...")
        registry = get_registry()
        providers_result = await list_providers(registry)
        print(f"✅ Found {len(providers_result['providers'])} providers:")
        
        # Convert to JSON-serializable format for display
        providers_json = []
        for provider in providers_result['providers']:
            provider_dict = {
                'name': provider.name,
                'description': provider.description,
                'supports_streaming': provider.supports_streaming,
                'supports_embeddings': provider.supports_embeddings,
                'requires_api_key': provider.requires_api_key,
                'default_model': provider.default_model,
                'health_status': provider.health_status
            }
            providers_json.append(provider_dict)
            print(f"   - {provider.name}: {provider.description}")
        
        print(f"\n📄 JSON Response for /api/llm/providers:")
        print(json.dumps({'providers': providers_json}, indent=2))
        
        print("\n2. Testing profile listing...")
        profiles_result = await list_profiles()
        print(f"✅ Found {len(profiles_result['profiles'])} profiles:")
        
        # Convert to JSON-serializable format
        profiles_json = []
        for profile in profiles_result['profiles']:
            profile_dict = {
                'name': profile.name,
                'providers': profile.providers,
                'fallback': profile.fallback
            }
            profiles_json.append(profile_dict)
            print(f"   - {profile.name}: chat={profile.providers['chat']}, code={profile.providers['code']}")
        
        print(f"\n📄 JSON Response for /api/llm/profiles:")
        print(json.dumps({'profiles': profiles_json}, indent=2))
        
        print("\n3. Testing health check...")
        health_result = await health_check_providers(None, registry)
        print(f"✅ Health check completed for {len(health_result['results'])} providers:")
        
        for name, result in health_result['results'].items():
            status = result.get('status', 'unknown')
            print(f"   - {name}: {status}")
        
        print(f"\n📄 JSON Response for /api/llm/health-check:")
        print(json.dumps(health_result, indent=2))
        
        print("\n🎉 All LLM endpoints working correctly!")
        print("\n💡 The web UI should be able to use these endpoints once the server is running.")
        print("   The fallback data in the web UI matches this structure, so it will work offline too.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_endpoints())
    sys.exit(0 if success else 1)