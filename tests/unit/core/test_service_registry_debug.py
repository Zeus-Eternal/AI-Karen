#!/usr/bin/env python3
"""
Debug script to test service registry initialization
"""
import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_service_registry():
    """Test the service registry initialization"""
    try:
        print("🔍 Testing service registry initialization...")
        
        # Import and initialize services
        from ai_karen_engine.core.service_registry import get_service_registry, initialize_services
        
        print("📋 Getting service registry...")
        registry = get_service_registry()
        
        print("🚀 Initializing services...")
        await initialize_services()
        
        print("📊 Getting initialization report...")
        report = registry.get_initialization_report()
        
        print(f"\n✅ Service Registry Report:")
        print(f"   Total services: {report['summary']['total_services']}")
        print(f"   Ready services: {report['summary']['ready_services']}")
        print(f"   Degraded services: {report['summary']['degraded_services']}")
        print(f"   Error services: {report['summary']['error_services']}")
        
        print(f"\n📋 Service Details:")
        for service_name, service_info in report['services'].items():
            status_emoji = {
                'ready': '✅',
                'degraded': '⚠️',
                'error': '❌',
                'initializing': '🔄',
                'pending': '⏳'
            }.get(service_info['status'], '❓')
            
            print(f"   {status_emoji} {service_name}: {service_info['status']}")
            if service_info.get('error_message'):
                print(f"      Error: {service_info['error_message']}")
        
        # Test getting ai_orchestrator specifically
        print(f"\n🎯 Testing ai_orchestrator service...")
        try:
            ai_orchestrator = await registry.get_service("ai_orchestrator")
            print(f"   ✅ ai_orchestrator retrieved successfully: {type(ai_orchestrator)}")
            
            # Test health check
            health = await ai_orchestrator.health_check()
            print(f"   🏥 Health check: {'✅ Healthy' if health else '❌ Unhealthy'}")
            
        except Exception as e:
            print(f"   ❌ Failed to get ai_orchestrator: {e}")
        
        # List all registered services
        print(f"\n📝 All registered services:")
        services = registry.list_services()
        for name, info in services.items():
            print(f"   - {name}: {info.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_service_registry())
    sys.exit(0 if success else 1)