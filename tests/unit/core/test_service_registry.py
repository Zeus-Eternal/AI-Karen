#!/usr/bin/env python3
"""
Test script to check service registry and AI orchestrator initialization
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_service_registry():
    """Test the service registry and AI orchestrator initialization"""
    
    print("🧪 Testing Service Registry and AI Orchestrator")
    print("=" * 60)
    
    try:
        # Test 1: Import and create service registry
        print("\n1. Testing Service Registry Import:")
        from src.ai_karen_engine.core.service_registry import ServiceRegistry, initialize_services
        registry = ServiceRegistry()
        print("   ✅ Service registry imported and created successfully")
        
        # Test 2: Test AI Orchestrator import
        print("\n2. Testing AI Orchestrator Import:")
        from src.ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
        print("   ✅ AI Orchestrator imported successfully")
        
        # Test 3: Test manual AI Orchestrator initialization
        print("\n3. Testing Manual AI Orchestrator Initialization:")
        try:
            # Create a simple config
            class SimpleServiceConfig:
                def __init__(self, name: str):
                    self.name = name
                    self.enabled = True
                    self.dependencies = []
                    self.config = {}
            
            config = SimpleServiceConfig("ai_orchestrator")
            orchestrator = AIOrchestrator(config)
            print("   ✅ AI Orchestrator created manually with config")
            
        except Exception as e:
            print(f"   ❌ Manual AI Orchestrator creation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Test service registration
        print("\n4. Testing Service Registration:")
        try:
            registry.register_service("ai_orchestrator", AIOrchestrator)
            print("   ✅ AI Orchestrator registered in service registry")
            
            # Check if it's registered
            services = registry.list_services()
            if "ai_orchestrator" in services:
                print(f"   ✅ AI Orchestrator found in registry: {services['ai_orchestrator']}")
            else:
                print("   ❌ AI Orchestrator not found in registry")
                
        except Exception as e:
            print(f"   ❌ Service registration failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 5: Test service initialization
        print("\n5. Testing Service Initialization:")
        try:
            await registry.initialize_all_services()
            print("   ✅ Service initialization completed")
            
            # Check service status
            services = registry.list_services()
            if "ai_orchestrator" in services:
                status = services["ai_orchestrator"]["status"]
                print(f"   AI Orchestrator status: {status}")
                
                if status == "ready":
                    print("   ✅ AI Orchestrator is ready!")
                else:
                    print(f"   ⚠️  AI Orchestrator status: {status}")
                    error = services["ai_orchestrator"].get("error_message")
                    if error:
                        print(f"   Error: {error}")
            
        except Exception as e:
            print(f"   ❌ Service initialization failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 6: Test getting the service
        print("\n6. Testing Service Retrieval:")
        try:
            orchestrator = await registry.get_service("ai_orchestrator")
            print("   ✅ AI Orchestrator retrieved from registry successfully")
            print(f"   Type: {type(orchestrator)}")
            
        except Exception as e:
            print(f"   ❌ Service retrieval failed: {e}")
        
        # Test 7: Test the full initialize_services function
        print("\n7. Testing Full initialize_services Function:")
        try:
            await initialize_services()
            print("   ✅ Full initialize_services completed")
            
        except Exception as e:
            print(f"   ❌ Full initialize_services failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Service Registry Test Complete")

if __name__ == "__main__":
    asyncio.run(test_service_registry())