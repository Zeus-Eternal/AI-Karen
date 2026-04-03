#!/usr/bin/env python3
"""
Test script to verify API endpoints are working correctly
"""
import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock

# Add src to path
sys.path.append('src')

async def test_ensure_session_endpoint():
    """Test the /ensure-session endpoint"""
    print("Testing /ensure-session endpoint...")
    
    try:
        from ai_karen_engine.api_routes.conversation_routes import ensure_session_conversation
        from ai_karen_engine.core.dependencies import get_conversation_service
        
        # Get the conversation service
        conversation_service = await get_conversation_service()
        
        # Test data
        test_session_id = "test-session-123"
        tenant_id = "default"
        user_ctx = {"user_id": "test-user", "tenant_id": "default"}
        
        # Call the endpoint function directly with dependencies
        result = await ensure_session_conversation(
            session_id=test_session_id,
            conversation_service=conversation_service,
            tenant_id=tenant_id,
            user_ctx=user_ctx
        )
        print(f"✅ /ensure-session endpoint working: {result}")
        return True
        
    except Exception as e:
        print(f"❌ /ensure-session endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_copilot_assist_endpoint():
    """Test the /copilot/assist endpoint"""
    print("Testing /copilot/assist endpoint...")
    
    try:
        from ai_karen_engine.api_routes.copilot_routes import copilot_assist, AssistRequest
        from fastapi import Request
        from ai_karen_engine.core.dependencies import get_chat_orchestrator_service
        
        # Get the chat orchestrator
        chat_orchestrator = await get_chat_orchestrator_service()
        
        # Test data using AssistRequest model
        test_request = AssistRequest(
            message="Can you help me debug this Python code?",
            session_id="test-session-123",
            user_id="test-user",
            context={
                "code_language": "python",
                "difficulty_level": "intermediate"
            }
        )
        
        # Call the endpoint function directly
        http_request = Request({"type": "http", "method": "POST", "headers": {}})
        result = await copilot_assist(
            request=test_request, 
            http_request=http_request,
            chat_orchestrator=chat_orchestrator
        )
        print(f"✅ /copilot/assist endpoint working: {type(result)}")
        return True
        
    except Exception as e:
        print(f"❌ /copilot/assist endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting API endpoint tests...")
    print("=" * 50)
    
    # Test both endpoints
    copilot_assist_success = await test_copilot_assist_endpoint()
    print()
    ensure_session_success = await test_ensure_session_endpoint()
    print()
    
    # Summary
    print("=" * 50)
    if ensure_session_success and copilot_assist_success:
        print("🎉 All API endpoints are working correctly!")
        return True
    else:
        print("❌ Some API endpoints are still failing")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)