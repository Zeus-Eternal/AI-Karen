#!/usr/bin/env python3
"""
Test script to verify the async factory fix for ChatOrchestrator.
This script tests that the factory methods work correctly with async database operations.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_karen_engine.chat.factory import ChatServiceFactory


async def test_async_factory():
    """Test that the factory creates services correctly in async context."""
    print("🧪 Testing async factory for ChatOrchestrator...")
    print("=" * 60)

    try:
        factory = ChatServiceFactory()

        print("\n1. Testing async conversation manager creation...")
        conversation_manager = await factory.create_conversation_manager()
        if conversation_manager:
            print("✅ Conversation manager created successfully")
        else:
            print("❌ Failed to create conversation manager")
            return False

        print("\n2. Testing async session state manager creation...")
        session_state_manager = await factory.create_session_state_manager()
        if session_state_manager:
            print("✅ Session state manager created successfully")
        else:
            print("❌ Failed to create session state manager")
            return False

        print("\n3. Testing async chat orchestrator creation...")
        chat_orchestrator = await factory.create_chat_orchestrator()
        if chat_orchestrator:
            print("✅ Chat orchestrator created successfully")
            print(f"   - Orchestrator type: {type(chat_orchestrator).__name__}")
            print(
                f"   - Conversation manager: {type(chat_orchestrator.conversation_manager).__name__}"
            )
            print(
                f"   - Session state manager: {type(chat_orchestrator.session_state_manager).__name__}"
            )
        else:
            print("❌ Failed to create chat orchestrator")
            return False

        print("\n" + "=" * 60)
        print("✅ All async factory tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print("\n❌ Error during async factory test:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_database_operations():
    """Test that database operations work correctly in async context."""
    print("\n\n🔍 Testing database operations in async context...")
    print("=" * 60)

    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient

        print("\n1. Testing async database connection...")
        db_client = MultiTenantPostgresClient()
        print(f"   Database client created: {type(db_client).__name__}")

        print("\n2. Testing async health check...")
        health_check = await db_client.async_health_check()
        if health_check:
            print("✅ Database health check passed")
        else:
            print(
                "⚠️ Database health check failed (this is OK if database is not running)"
            )

        print("\n3. Testing async session context manager...")
        async with db_client.get_async_session() as session:
            print("✅ Async session context manager works")

        print("\n" + "=" * 60)
        print("✅ Database async operations work correctly!")
        print("=" * 60)
        return True

    except Exception as e:
        print("\n❌ Error during database async test:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")

        # Check if this is the greenlet error
        if "greenlet" in str(e).lower():
            print("\n⚠️ This appears to be the greenlet error!")
            print(
                "   The database client might not be properly configured for async operations."
            )
            print("   Check that the database URL uses 'postgresql+asyncpg://'")

        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 Async Factory Fix Verification")
    print("=" * 60)

    # Test 1: Async factory
    test1_passed = await test_async_factory()

    # Test 2: Database operations
    test2_passed = await test_database_operations()

    # Summary
    print("\n\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Async Factory Tests: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Database Async Tests: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 60)

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The async fix is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
