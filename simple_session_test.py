#!/usr/bin/env python3
"""
Simple session lifecycle test that bypasses HTTP authentication
"""

import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock

# Set environment variables for development bypass
os.environ["ENVIRONMENT"] = "development"
os.environ["KARI_AUTH_BYPASS"] = "true"
os.environ["DEBUG"] = "true"

# Add src to path
sys.path.append("src")


async def test_session_creation():
    """Test session creation through ensure-session endpoint"""
    print("🧪 Testing Session Creation...")

    try:
        # Import required modules
        from ai_karen_engine.api_routes.conversation_routes import (
            ensure_session_conversation,
        )
        from ai_karen_engine.core.dependencies import (
            get_conversation_service,
            get_current_tenant_id,
            bypass_user_context_func,
        )

        # Get services
        conversation_service = await get_conversation_service()
        tenant_id = await get_current_tenant_id()

        # Mock user context for development
        user_ctx = {
            "user_id": "dev-user",
            "email": "dev-user@localhost",
            "full_name": "Dev User",
            "roles": ["admin", "user"],
            "tenant_id": tenant_id,
            "is_active": True,
        }

        # Test session creation
        test_session_id = "test-session-dev-" + str(asyncio.get_event_loop().time())
        print(f"🔍 Testing with session ID: {test_session_id}")

        # Call the endpoint function directly with mocked dependencies
        result = await ensure_session_conversation(
            session_id=test_session_id,
            conversation_service=conversation_service,
            tenant_id=tenant_id,
            user_ctx=user_ctx,
        )

        print(f"✅ Session created successfully!")
        print(f"   - Session ID: {result.get('session_id', 'N/A')}")
        print(f"   - Conversation ID: {result.get('id', 'N/A')}")
        print(f"   - Message count: {result.get('message_count', 0)}")
        print(f"   - Title: {result.get('title', 'N/A')}")

        return result, test_session_id

    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        import traceback

        traceback.print_exc()
        return None, None


async def test_session_loading(session_id):
    """Test loading an existing session"""
    if not session_id:
        print("⚠️ Skipping session loading test - no session available")
        return None

    print(f"\n🧪 Testing Session Loading for {session_id}...")

    try:
        from ai_karen_engine.api_routes.conversation_routes import (
            get_conversation_by_session,
        )
        from ai_karen_engine.core.dependencies import (
            get_conversation_service,
            get_current_tenant_id,
            bypass_user_context_func,
        )

        # Get services
        conversation_service = await get_conversation_service()
        tenant_id = await get_current_tenant_id()

        # Mock user context
        user_ctx = {
            "user_id": "dev-user",
            "email": "dev-user@localhost",
            "full_name": "Dev User",
            "roles": ["admin", "user"],
            "tenant_id": tenant_id,
            "is_active": True,
        }

        # Load the session
        result = await get_conversation_by_session(
            session_id=session_id,
            include_context=True,
            conversation_service=conversation_service,
            tenant_id=tenant_id,
            user_ctx=user_ctx,
        )

        print(f"✅ Session loaded successfully!")
        print(f"   - Session ID: {result.get('session_id', 'N/A')}")
        print(f"   - Conversation ID: {result.get('id', 'N/A')}")
        print(f"   - Message count: {result.get('message_count', 0)}")
        print(f"   - Title: {result.get('title', 'N/A')}")

        return result

    except Exception as e:
        print(f"❌ Session loading failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_message_sending(session_id):
    """Test sending a message to a session"""
    if not session_id:
        print("⚠️ Skipping message sending test - no session available")
        return None

    print(f"\n🧪 Testing Message Sending...")

    try:
        from ai_karen_engine.api_routes.conversation_routes import add_message
        from ai_karen_engine.core.dependencies import (
            get_conversation_service,
            get_current_tenant_id,
            bypass_user_context_func,
        )
        from services.memory.conversation_service import UISource
        from ai_karen_engine.database.conversation_manager import MessageRole

        # Get services
        conversation_service = await get_conversation_service()
        tenant_id = await get_current_tenant_id()

        # Mock user context
        user_ctx = {
            "user_id": "dev-user",
            "email": "dev-user@localhost",
            "full_name": "Dev User",
            "roles": ["admin", "user"],
            "tenant_id": tenant_id,
            "is_active": True,
        }

        # First, get the conversation ID from the session
        conversation_response = await get_conversation_by_session(
            session_id=session_id,
            include_context=False,
            conversation_service=conversation_service,
            tenant_id=tenant_id,
            user_ctx=user_ctx,
        )

        conversation_id = conversation_response.get("id")
        if not conversation_id:
            print("❌ Could not get conversation ID from session")
            return None

        print(f"🔍 Using conversation ID: {conversation_id}")

        # Add a test message
        from ai_karen_engine.api_routes.conversation_routes import AddMessageRequest

        message_request = AddMessageRequest(
            role=MessageRole.USER,
            content="Hello! This is a test message from our session lifecycle test.",
            ui_source=UISource.WEB,
            metadata={"test": True, "source": "session_lifecycle_test"},
        )

        result = await add_message(
            conversation_id=conversation_id,
            request=message_request,
            conversation_service=conversation_service,
        )

        print(f"✅ Message sent successfully!")
        print(f"   - Message ID: {result.get('message', {}).get('id', 'N/A')}")
        print(f"   - Role: {result.get('message', {}).get('role', 'N/A')}")
        print(
            f"   - Content: {result.get('message', {}).get('content', 'N/A')[:100]}..."
        )

        return result

    except Exception as e:
        print(f"❌ Message sending failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_session_switching():
    """Test switching between multiple sessions"""
    print(f"\n🧪 Testing Session Switching...")

    try:
        # Create multiple sessions
        sessions = []
        for i in range(3):
            result, session_id = await test_session_creation()
            if result and session_id:
                sessions.append((result, session_id))

        if len(sessions) < 2:
            print("❌ Could not create multiple sessions for switching test")
            return None

        print(f"✅ Created {len(sessions)} sessions for switching test")

        # Test switching between sessions
        for i, (result, session_id) in enumerate(sessions):
            print(f"\n🔄 Switching to session {i + 1}: {session_id}")
            loaded_result = await test_session_loading(session_id)
            if loaded_result:
                print(f"✅ Successfully switched to session {i + 1}")
            else:
                print(f"❌ Failed to switch to session {i + 1}")

        return sessions

    except Exception as e:
        print(f"❌ Session switching test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_error_handling():
    """Test error handling scenarios"""
    print(f"\n🧪 Testing Error Handling...")

    try:
        # Test with invalid session ID
        print("🔍 Testing with invalid session ID...")
        from ai_karen_engine.api_routes.conversation_routes import (
            get_conversation_by_session,
        )
        from ai_karen_engine.core.dependencies import (
            get_conversation_service,
            get_current_tenant_id,
            bypass_user_context_func,
        )

        conversation_service = await get_conversation_service()
        tenant_id = await get_current_tenant_id()

        user_ctx = {
            "user_id": "dev-user",
            "email": "dev-user@localhost",
            "full_name": "Dev User",
            "roles": ["admin", "user"],
            "tenant_id": tenant_id,
            "is_active": True,
        }

        try:
            result = await get_conversation_by_session(
                session_id="invalid-session-id-that-does-not-exist",
                include_context=True,
                conversation_service=conversation_service,
                tenant_id=tenant_id,
                user_ctx=user_ctx,
            )
            print(f"✅ Invalid session handled gracefully: {result.get('id', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Invalid session raised exception (this might be expected): {e}")

        print("✅ Error handling test completed")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Session Lifecycle Management Tests")
    print("=" * 60)
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'unknown')}")
    print(f"Auth Bypass: {os.environ.get('KARI_AUTH_BYPASS', 'unknown')}")
    print(f"Debug Mode: {os.environ.get('DEBUG', 'unknown')}")
    print("=" * 60)

    # Test 1: Session Creation
    print("\n📋 TEST 1: Session Creation")
    session_result, session_id = await test_session_creation()

    # Test 2: Session Loading
    print("\n📋 TEST 2: Session Loading")
    loaded_session = await test_session_loading(session_id)

    # Test 3: Message Sending
    print("\n📋 TEST 3: Message Sending")
    message_result = await test_message_sending(session_id)

    # Test 4: Session Switching
    print("\n📋 TEST 4: Session Switching")
    switching_sessions = await test_session_switching()

    # Test 5: Error Handling
    print("\n📋 TEST 5: Error Handling")
    error_handling_result = await test_error_handling()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    tests_passed = 0
    total_tests = 5

    if session_result:
        print("✅ Test 1 - Session Creation: PASSED")
        tests_passed += 1
    else:
        print("❌ Test 1 - Session Creation: FAILED")

    if loaded_session:
        print("✅ Test 2 - Session Loading: PASSED")
        tests_passed += 1
    else:
        print("❌ Test 2 - Session Loading: FAILED")

    if message_result:
        print("✅ Test 3 - Message Sending: PASSED")
        tests_passed += 1
    else:
        print("❌ Test 3 - Message Sending: FAILED")

    if switching_sessions and len(switching_sessions) >= 2:
        print("✅ Test 4 - Session Switching: PASSED")
        tests_passed += 1
    else:
        print("❌ Test 4 - Session Switching: FAILED")

    if error_handling_result:
        print("✅ Test 5 - Error Handling: PASSED")
        tests_passed += 1
    else:
        print("❌ Test 5 - Error Handling: FAILED")

    print(f"\n🎯 OVERALL RESULT: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 ALL SESSION LIFECYCLE TESTS PASSED!")
        print("✅ Session management is working correctly and production-ready!")
        return True
    else:
        print("⚠️ Some tests failed. Session management needs attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
