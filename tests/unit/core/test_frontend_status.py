#!/usr/bin/env python3
"""
Test script to verify frontend status mapping
"""

import json
import requests

def test_frontend_status():
    """Test what the frontend should be seeing"""
    
    print("🧪 Testing Frontend Status Mapping")
    print("=" * 50)
    
    try:
        # Test the degraded mode endpoint
        print("\n1. Testing degraded mode endpoint...")
        response = requests.get("http://localhost:8010/api/karen/api/health/degraded-mode")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Backend response received")
            
            # Simulate the frontend mapping (from reasoningService.ts)
            frontend_status = {
                "degraded": data.get("is_active"),
                "components": data.get("infrastructure_issues", []),
                "fallback_systems_active": data.get("core_helpers_available", {}).get("fallback_responses", False),
                "local_models_available": (data.get("core_helpers_available", {}).get("total_ai_capabilities", 0)) > 0,
                "ai_status": data.get("ai_status"),
                "failed_providers": data.get("failed_providers", []),
                "reason": data.get("reason"),
            }
            
            print("\n2. Frontend Status Mapping:")
            print(f"   degraded: {frontend_status['degraded']}")
            print(f"   local_models_available: {frontend_status['local_models_available']}")
            print(f"   ai_status: {frontend_status['ai_status']}")
            print(f"   components: {frontend_status['components']}")
            print(f"   fallback_systems_active: {frontend_status['fallback_systems_active']}")
            
            print("\n3. Expected Frontend Behavior:")
            if not frontend_status['degraded']:
                print("   ✅ Degraded mode banner should be HIDDEN")
                print("   ✅ SystemStatus should show 'Healthy'")
                print("   ✅ Chat should work normally")
            else:
                print("   ❌ Degraded mode banner would be VISIBLE")
                print(f"   ❌ Reason: {frontend_status['reason']}")
            
            print("\n4. Raw Backend Data:")
            print(f"   is_active: {data.get('is_active')}")
            print(f"   ai_status: {data.get('ai_status')}")
            print(f"   total_ai_capabilities: {data.get('core_helpers_available', {}).get('total_ai_capabilities')}")
            
        else:
            print(f"   ❌ Backend error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Frontend Status Test Complete")

if __name__ == "__main__":
    test_frontend_status()