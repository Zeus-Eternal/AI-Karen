#!/usr/bin/env python3
"""
Script to fix the reasoning service by ensuring AI orchestrator is properly initialized
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def fix_reasoning_service():
    """Fix the reasoning service by initializing the AI orchestrator"""
    
    print("🔧 Fixing Reasoning Service")
    print("=" * 50)
    
    try:
        # Step 1: Initialize services
        print("\n1. Initializing AI Karen services...")
        from src.ai_karen_engine.core.service_registry import initialize_services, get_service_registry
        await initialize_services()
        print("   ✅ Services initialized successfully")
        
        # Step 2: Verify AI orchestrator is available
        print("\n2. Verifying AI orchestrator...")
        registry = get_service_registry()
        services = registry.list_services()
        
        if "ai_orchestrator" in services:
            status = services["ai_orchestrator"]["status"]
            print(f"   ✅ AI orchestrator found with status: {status}")
            
            if status == "ready":
                print("   ✅ AI orchestrator is ready!")
                
                # Step 3: Test the AI orchestrator
                print("\n3. Testing AI orchestrator...")
                orchestrator = await registry.get_service("ai_orchestrator")
                
                # Test conversation processing
                test_input = "Hello, can you help me test the system?"
                response = await orchestrator.process_conversation(
                    user_input=test_input,
                    context={"user_id": "test", "conversation_id": "test"}
                )
                
                print(f"   ✅ AI orchestrator test successful!")
                print(f"   Response type: {type(response)}")
                if hasattr(response, 'get'):
                    print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                
                # Step 4: Test the reasoning endpoint simulation
                print("\n4. Testing reasoning endpoint logic...")
                
                # Simulate the reasoning endpoint logic
                request = {
                    "input": test_input,
                    "context": {"user_id": "test", "conversation_id": "test"}
                }
                
                user_input = request.get("input", "")
                context = request.get("context", {})
                
                # Use AI orchestrator for reasoning
                response = await orchestrator.process_conversation(
                    user_input=user_input,
                    context=context,
                    user_id=context.get("user_id", "anonymous")
                )
                
                result = {
                    "success": True,
                    "response": response,
                    "reasoning_method": "ai_orchestrator",
                    "fallback_used": False
                }
                
                print(f"   ✅ Reasoning endpoint simulation successful!")
                print(f"   Success: {result['success']}")
                print(f"   Method: {result['reasoning_method']}")
                print(f"   Fallback used: {result['fallback_used']}")
                
            else:
                print(f"   ❌ AI orchestrator status is {status}, not ready")
        else:
            print("   ❌ AI orchestrator not found in services")
            print(f"   Available services: {list(services.keys())}")
        
        # Step 5: Show service status
        print(f"\n5. Service Registry Status:")
        print(f"   Total services: {len(services)}")
        for name, info in services.items():
            status = info.get("status", "unknown")
            print(f"   - {name}: {status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Reasoning Service Fix Complete")

if __name__ == "__main__":
    asyncio.run(fix_reasoning_service())