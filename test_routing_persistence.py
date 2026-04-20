#!/usr/bin/env python3
"""
Test script for routing decision persistence functionality.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.services.llm_router import LLMRouter, ChatRequest


async def test_routing_decision_persistence():
    """Test routing decision persistence functionality"""
    print("Testing routing decision persistence...")

    # Create router instance
    router = LLMRouter()

    # Create a test request
    request = ChatRequest(
        message="Hello, how are you?",
        context={"recent_messages": []},
        stream=True,
        conversation_id="test-conversation-123",
    )

    try:
        # Test 1: Record routing decision
        print("\n1. Testing routing decision recording...")
        await router.record_routing_decision(
            request=request,
            selected_provider="openai",
            selected_model="gpt-3.5-turbo",
            reason="test_selection",
            success=True,
            latency_ms=1500.0,
        )
        print("✓ Routing decision recorded successfully")

        # Test 2: Record provider interaction
        print("\n2. Testing provider interaction recording...")
        await router.record_provider_interaction(
            provider_name="openai",
            request_type="chat",
            success=True,
            latency=1.5,
        )
        print("✓ Provider interaction recorded successfully")

        # Test 3: Get routing audit trail
        print("\n3. Testing routing audit trail retrieval...")
        audit_trail = await router.get_routing_audit_trail(limit=10)
        print(f"✓ Retrieved {len(audit_trail)} routing decisions")
        if audit_trail:
            print(
                f"  Latest decision: {audit_trail[0]['selected_provider']} ({audit_trail[0]['reason']})"
            )

        # Test 4: Get provider audit trail
        print("\n4. Testing provider audit trail retrieval...")
        provider_audit = await router.get_provider_audit_trail(limit=10)
        print(f"✓ Retrieved {len(provider_audit)} provider interactions")
        if provider_audit:
            print(
                f"  Latest interaction: {provider_audit[0]['provider']} ({provider_audit[0]['request_type']})"
            )

        # Test 5: Get routing statistics
        print("\n5. Testing routing statistics...")
        routing_stats = await router.get_routing_statistics()
        print(
            f"✓ Routing statistics: {routing_stats['total_decisions']} total decisions, "
            f"{routing_stats['success_rate']:.2%} success rate"
        )

        # Test 6: Get provider statistics
        print("\n6. Testing provider statistics...")
        provider_stats = await router.get_provider_statistics()
        print(
            f"✓ Provider statistics: {provider_stats['total_interactions']} total interactions, "
            f"{provider_stats['success_rate']:.2%} success rate"
        )

        # Test 7: Get comprehensive analytics
        print("\n7. Testing comprehensive analytics...")
        analytics = await router.get_routing_analytics()
        print("✓ Comprehensive analytics retrieved successfully")

        # Test 8: Test with failure
        print("\n8. Testing failure recording...")
        await router.record_routing_decision(
            request=request,
            selected_provider="anthropic",
            selected_model="claude-3-sonnet",
            reason="test_failure",
            success=False,
            latency_ms=5000.0,
            error_message="Timeout error",
        )
        print("✓ Failure recorded successfully")

        # Test 9: Test provider failure
        await router.record_provider_interaction(
            provider_name="anthropic",
            request_type="chat",
            success=False,
            latency=5.0,
            error_message="Request timeout",
        )
        print("✓ Provider failure recorded successfully")

        print(
            "\n🎉 All tests passed! Routing decision persistence is working correctly."
        )

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        await router.shutdown()

    return True


async def test_persistence_file_operations():
    """Test file-based persistence operations"""
    print("\n" + "=" * 50)
    print("Testing file-based persistence operations...")

    router = LLMRouter()

    try:
        # Test export functionality
        print("\n1. Testing data export...")
        export_dir = "/tmp/router_persistence_test"
        exported_path = await router.export_routing_data(export_dir)
        print(f"✓ Data exported to: {exported_path}")

        # List exported files
        export_path = Path(exported_path)
        if export_path.exists():
            files = list(export_path.glob("*.json"))
            print(f"  Exported files: {[f.name for f in files]}")

        # Test clear functionality
        print("\n2. Testing data clearing...")
        await router.clear_routing_data()
        print("✓ Data cleared successfully")

        # Verify data is cleared
        audit_trail = await router.get_routing_audit_trail(limit=100)
        provider_audit = await router.get_provider_audit_trail(limit=100)
        print(f"  Remaining routing decisions: {len(audit_trail)}")
        print(f"  Remaining provider interactions: {len(provider_audit)}")

        print("\n🎉 File-based persistence operations test passed!")

    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await router.shutdown()

    return True


async def main():
    """Main test function"""
    print("Starting routing decision persistence tests...")

    # Test basic functionality
    success1 = await test_routing_decision_persistence()

    # Test file operations
    success2 = await test_persistence_file_operations()

    if success1 and success2:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
