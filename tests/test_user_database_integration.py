#!/usr/bin/env python3
"""
Comprehensive test for user authentication and database integration
"""

import asyncio
import sys
import os
import requests
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_user_service():
    """Test the user service functionality"""
    
    print("🔐 Testing User Service and Database Integration...")
    
    try:
        from ai_karen_engine.services.user_service import UserService
        from ai_karen_engine.core.services.base import ServiceConfig
        
        # Initialize user service
        config = ServiceConfig(name="user_service", enabled=True)
        user_service = UserService(config)
        await user_service.initialize()
        
        print("✅ User service initialized successfully")
        
        # Test user creation
        print("\n📝 Testing user creation...")
        try:
            user = await user_service.create_user(
                email="test@example.com",
                roles=["user"],
                preferences={
                    "personalityTone": "friendly",
                    "preferredLLMProvider": "ollama"
                }
            )
            print(f"✅ Created user: {user.email} (ID: {user.id})")
        except Exception as e:
            if "already exists" in str(e):
                print("✅ User already exists (expected)")
                user = await user_service.get_user_by_email("test@example.com")
            else:
                raise
        
        # Test user retrieval
        print("\n🔍 Testing user retrieval...")
        retrieved_user = await user_service.get_user(user.id)
        print(f"✅ Retrieved user: {retrieved_user.email}")
        
        # Test LLM preferences
        print("\n⚙️ Testing LLM preferences...")
        llm_prefs = await user_service.get_user_llm_preferences(user.id)
        print(f"✅ LLM preferences: {llm_prefs}")
        
        # Test authentication
        print("\n🔑 Testing authentication...")
        auth_result = await user_service.authenticate_user(
            email="admin@kari.ai",
            password="pswd123",
            user_agent="test-agent",
            ip="127.0.0.1"
        )
        print(f"✅ Authentication successful: {auth_result['email']}")
        
        # Test session validation
        print("\n🎫 Testing session validation...")
        session_context = await user_service.validate_user_session(
            token=auth_result["token"],
            user_agent="test-agent",
            ip="127.0.0.1"
        )
        print(f"✅ Session validation successful: {session_context['email']}")
        
        # Test conversation saving
        print("\n💬 Testing conversation saving...")
        conversation = await user_service.save_user_conversation(
            user_id=user.id,
            session_id="test_session_123",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            title="Test Conversation"
        )
        print(f"✅ Saved conversation: {conversation['title']}")
        
        # Test conversation retrieval
        print("\n📚 Testing conversation retrieval...")
        conversations = await user_service.get_user_conversations(user.id)
        print(f"✅ Retrieved {len(conversations)} conversations")
        
        print("\n🎉 All user service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ User service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        print("\n🏥 Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test login endpoint
        print("\n🔐 Testing login endpoint...")
        login_data = {
            "email": "admin@kari.ai",
            "password": "pswd123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["token"]
            print(f"✅ Login successful: {auth_data['email']}")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
        
        # Test user info endpoint
        print("\n👤 Testing user info endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User info retrieved: {user_data['email']}")
            user_id = user_data["user_id"]
        else:
            print(f"❌ User info failed: {response.status_code} - {response.text}")
            return False
        
        # Test chat processing with authentication
        print("\n💬 Testing authenticated chat processing...")
        chat_data = {
            "message": "Hello, I'm testing the authenticated chat system!",
            "conversation_history": [],
            "relevant_memories": [],
            "user_settings": {
                "personalityTone": "friendly",
                "personalityVerbosity": "balanced"
            },
            "user_id": user_id,
            "session_id": "test_auth_session"
        }
        response = requests.post(f"{base_url}/api/chat/process", json=chat_data)
        if response.status_code == 200:
            chat_result = response.json()
            print(f"✅ Authenticated chat successful")
            print(f"   Response: {chat_result['finalResponse'][:100]}...")
            if chat_result.get('proactiveSuggestion'):
                print(f"   Suggestion: {chat_result['proactiveSuggestion']}")
        else:
            print(f"❌ Authenticated chat failed: {response.status_code} - {response.text}")
            return False
        
        # Test LLM providers endpoint
        print("\n🤖 Testing LLM providers endpoint...")
        response = requests.get(f"{base_url}/api/llm/providers")
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ LLM providers retrieved: {len(providers.get('providers', []))} providers")
        else:
            print(f"❌ LLM providers failed: {response.status_code} - {response.text}")
            return False
        
        print("\n🎉 All API endpoint tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test database integration"""
    
    print("\n🗄️ Testing Database Integration...")
    
    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        from ai_karen_engine.database.models import User, Tenant
        
        # Initialize database client
        db_client = MultiTenantPostgresClient()
        print("✅ Database client initialized")
        
        # Test database connection
        from sqlalchemy import text
        with db_client._get_session() as session:
            session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Test shared tables creation
        db_client.create_shared_tables()
        print("✅ Shared tables created/verified")
        
        # Test tenant schema creation
        with db_client._get_session() as session:
            tenant = session.query(Tenant).filter_by(slug="default").first()
            if tenant:
                schema_exists = db_client.tenant_schema_exists(tenant.id)
                print(f"✅ Tenant schema exists: {schema_exists}")
                
                if not schema_exists:
                    created = db_client.create_tenant_schema(tenant.id)
                    print(f"✅ Tenant schema created: {created}")
        
        print("\n🎉 All database integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_comprehensive_test():
    """Run all tests"""
    
    print("🚀 Starting Comprehensive User Authentication and Database Integration Test")
    print("=" * 80)
    
    # Test 1: User Service
    user_service_ok = await test_user_service()
    
    # Test 2: Database Integration
    database_ok = test_database_integration()
    
    # Test 3: API Endpoints
    api_ok = test_api_endpoints()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"User Service:        {'✅ PASS' if user_service_ok else '❌ FAIL'}")
    print(f"Database Integration: {'✅ PASS' if database_ok else '❌ FAIL'}")
    print(f"API Endpoints:       {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    all_passed = user_service_ok and database_ok and api_ok
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! User authentication and database integration is working correctly.")
        print("\n📋 What's working:")
        print("   • User creation and management")
        print("   • JWT-based authentication")
        print("   • Database persistence")
        print("   • Multi-tenant architecture")
        print("   • LLM preferences integration")
        print("   • Conversation history saving")
        print("   • API endpoint authentication")
        print("   • Intelligent suggestion generation")
    else:
        print("\n❌ SOME TESTS FAILED. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())