#!/usr/bin/env python3
"""
AI Karen Database System Showcase
Demonstrates the full power of the production-grade database integration system.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.database.integration_manager import (
    DatabaseIntegrationManager, DatabaseConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseShowcase:
    """Comprehensive showcase of AI Karen's database capabilities."""
    
    def __init__(self):
        """Initialize the showcase."""
        self.db_manager = None
        self.tenant_id = None
        self.user_id = str(uuid.uuid4())
        self.conversation_id = None
        
    async def initialize(self):
        """Initialize the database system."""
        print("🚀 Initializing AI Karen Database System...")
        
        # Configure database with all features enabled
        config = DatabaseConfig(
            postgres_url="postgresql://postgres:postgres@localhost:5432/ai_karen_dev",
            redis_url="redis://localhost:6379/0",
            milvus_host="localhost",
            milvus_port=19530,
            elasticsearch_host="localhost",
            elasticsearch_port=9200,
            enable_redis=True,
            enable_milvus=True,
            enable_elasticsearch=True
        )
        
        self.db_manager = DatabaseIntegrationManager(config)
        
        try:
            await self.db_manager.initialize()
            print("✅ Database system initialized successfully!")
        except Exception as e:
            print(f"⚠️  Database initialization failed: {e}")
            print("📝 Note: This demo requires PostgreSQL, Redis, Milvus, and Elasticsearch")
            print("   You can still see the code structure and API design!")
            return False
        
        return True
    
    async def demonstrate_tenant_management(self):
        """Demonstrate multi-tenant capabilities."""
        print("\n🏢 === TENANT MANAGEMENT SHOWCASE ===")
        
        try:
            # Create a new tenant
            print("Creating a new tenant...")
            tenant_data = await self.db_manager.create_tenant(
                name="Acme Corporation",
                slug="acme-corp",
                admin_email="admin@acme.com",
                subscription_tier="enterprise",
                settings={
                    "features": ["advanced_memory", "analytics", "custom_plugins"],
                    "branding": {"primary_color": "#007acc", "logo_url": "https://acme.com/logo.png"},
                    "integrations": ["slack", "teams", "jira"]
                }
            )
            
            self.tenant_id = tenant_data["tenant_id"]
            print(f"✅ Created tenant: {tenant_data['name']} (ID: {self.tenant_id})")
            print(f"   Subscription: {tenant_data['subscription_tier']}")
            print(f"   Features: {tenant_data.get('settings', {}).get('features', [])}")
            
            # Get tenant information
            print("\nRetrieving tenant information...")
            tenant_info = await self.db_manager.get_tenant(self.tenant_id)
            print(f"✅ Retrieved tenant: {tenant_info['name']}")
            print(f"   Active: {tenant_info['is_active']}")
            print(f"   Created: {tenant_info['created_at']}")
            
            # Get tenant statistics
            print("\nGetting tenant statistics...")
            stats = await self.db_manager.get_tenant_stats(self.tenant_id)
            if stats:
                print(f"✅ Tenant Stats:")
                print(f"   Users: {stats['user_count']}")
                print(f"   Conversations: {stats['conversation_count']}")
                print(f"   Memory Entries: {stats['memory_entry_count']}")
                print(f"   Storage Used: {stats['storage_used_mb']:.2f} MB")
            
        except Exception as e:
            print(f"❌ Tenant management error: {e}")
    
    async def demonstrate_memory_system(self):
        """Demonstrate the advanced memory system."""
        print("\n🧠 === MEMORY SYSTEM SHOWCASE ===")
        
        if not self.tenant_id:
            print("❌ No tenant available for memory demo")
            return
        
        try:
            # Store various types of memories
            print("Storing diverse memory entries...")
            
            memories_to_store = [
                {
                    "content": "User prefers dark mode interface and minimal notifications",
                    "tags": ["preference", "ui"],
                    "metadata": {"category": "user_preference", "importance": "high"}
                },
                {
                    "content": "Discussed implementing a new authentication system using OAuth 2.0",
                    "tags": ["technical", "auth"],
                    "metadata": {"category": "technical_discussion", "project": "auth_upgrade"}
                },
                {
                    "content": "User mentioned they work in the healthcare industry and need HIPAA compliance",
                    "tags": ["compliance", "healthcare"],
                    "metadata": {"category": "business_context", "compliance_requirement": "HIPAA"}
                },
                {
                    "content": "Favorite programming languages are Python and TypeScript",
                    "tags": ["preference", "programming"],
                    "metadata": {"category": "technical_preference", "languages": ["python", "typescript"]}
                },
                {
                    "content": "Meeting scheduled for next Tuesday at 2 PM to review project progress",
                    "tags": ["schedule", "meeting"],
                    "metadata": {"category": "calendar", "meeting_type": "progress_review"}
                }
            ]
            
            stored_ids = []
            for memory_data in memories_to_store:
                memory_id = await self.db_manager.store_memory(
                    tenant_id=self.tenant_id,
                    content=memory_data["content"],
                    user_id=self.user_id,
                    tags=memory_data["tags"],
                    metadata=memory_data["metadata"]
                )
                
                if memory_id:
                    stored_ids.append(memory_id)
                    print(f"✅ Stored memory: {memory_data['content'][:50]}...")
                else:
                    print(f"⚠️  Skipped (not surprising): {memory_data['content'][:50]}...")
            
            print(f"\n📊 Successfully stored {len(stored_ids)} memory entries")
            
            # Demonstrate semantic search
            print("\nDemonstrating semantic memory search...")
            
            search_queries = [
                "What are the user's interface preferences?",
                "Tell me about authentication discussions",
                "What compliance requirements were mentioned?",
                "What programming languages does the user like?",
                "Any upcoming meetings?"
            ]
            
            for query in search_queries:
                print(f"\n🔍 Query: '{query}'")
                
                memories = await self.db_manager.query_memories(
                    tenant_id=self.tenant_id,
                    query_text=query,
                    user_id=self.user_id,
                    top_k=3,
                    similarity_threshold=0.6
                )
                
                if memories:
                    for i, memory in enumerate(memories, 1):
                        score = memory.get('similarity_score', 0)
                        content = memory['content'][:80] + "..." if len(memory['content']) > 80 else memory['content']
                        print(f"   {i}. [{score:.3f}] {content}")
                        print(f"      Tags: {memory.get('tags', [])}")
                else:
                    print("   No relevant memories found")
            
        except Exception as e:
            print(f"❌ Memory system error: {e}")
    
    async def demonstrate_conversation_system(self):
        """Demonstrate the conversation management system."""
        print("\n💬 === CONVERSATION SYSTEM SHOWCASE ===")
        
        if not self.tenant_id:
            print("❌ No tenant available for conversation demo")
            return
        
        try:
            # Create a new conversation
            print("Creating a new conversation...")
            conversation_data = await self.db_manager.create_conversation(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                title="AI Assistant Chat",
                initial_message="Hello! I need help with setting up a new project."
            )
            
            self.conversation_id = conversation_data["id"]
            print(f"✅ Created conversation: {conversation_data['title']}")
            print(f"   ID: {self.conversation_id}")
            print(f"   Messages: {conversation_data['message_count']}")
            
            # Add a series of messages to simulate a conversation
            print("\nSimulating a conversation...")
            
            conversation_flow = [
                ("assistant", "I'd be happy to help you set up a new project! What type of project are you working on?"),
                ("user", "I'm building a web application with Python and React. I need help with the backend architecture."),
                ("assistant", "Great choice! For a Python backend with React frontend, I recommend using FastAPI for the API layer. Based on your preferences for Python, this would be ideal. Would you like me to explain the architecture?"),
                ("user", "Yes, please explain the recommended architecture. Also, remember that I work in healthcare so we need HIPAA compliance."),
                ("assistant", "Perfect! Given your healthcare industry requirement for HIPAA compliance, here's a secure architecture recommendation:\n\n1. FastAPI backend with proper authentication\n2. PostgreSQL database with encryption at rest\n3. Redis for caching (with encryption)\n4. Docker containers for deployment\n5. HTTPS everywhere with proper certificate management\n\nWould you like me to detail any specific component?"),
                ("user", "This looks great! Can you help me set up the authentication system? I remember we discussed OAuth 2.0 before."),
                ("assistant", "Absolutely! Since we previously discussed OAuth 2.0 for authentication, I'll help you implement a secure OAuth 2.0 flow that meets HIPAA requirements. We'll use industry-standard libraries and ensure proper token management.")
            ]
            
            for role, content in conversation_flow:
                message_data = await self.db_manager.add_message(
                    tenant_id=self.tenant_id,
                    conversation_id=self.conversation_id,
                    role=role,
                    content=content,
                    metadata={"timestamp": datetime.utcnow().isoformat()}
                )
                
                if message_data:
                    print(f"✅ Added {role} message: {content[:60]}...")
            
            # Retrieve the full conversation
            print("\nRetrieving full conversation with context...")
            full_conversation = await self.db_manager.get_conversation(
                tenant_id=self.tenant_id,
                conversation_id=self.conversation_id
            )
            
            if full_conversation:
                print(f"✅ Retrieved conversation: {full_conversation['title']}")
                print(f"   Total messages: {full_conversation['message_count']}")
                print(f"   Last activity: {full_conversation['last_message_at']}")
                
                # Show memory context if available
                memory_context = full_conversation.get('metadata', {}).get('memory_context', [])
                if memory_context:
                    print(f"   Memory context items: {len(memory_context)}")
                    for i, context in enumerate(memory_context, 1):
                        print(f"     {i}. [{context['similarity_score']:.3f}] {context['content'][:50]}...")
            
            # List all conversations for the user
            print("\nListing all conversations for user...")
            conversations = await self.db_manager.list_conversations(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                limit=10
            )
            
            print(f"✅ Found {len(conversations)} conversations:")
            for conv in conversations:
                print(f"   - {conv['title']} ({conv['message_count']} messages)")
            
        except Exception as e:
            print(f"❌ Conversation system error: {e}")
    
    async def demonstrate_analytics_and_insights(self):
        """Demonstrate analytics and insights capabilities."""
        print("\n📊 === ANALYTICS & INSIGHTS SHOWCASE ===")
        
        if not self.tenant_id:
            print("❌ No tenant available for analytics demo")
            return
        
        try:
            # Get comprehensive system metrics
            print("Gathering system metrics...")
            metrics = await self.db_manager.get_system_metrics()
            
            print("✅ System Metrics:")
            if 'memory_manager' in metrics:
                mm = metrics['memory_manager']
                print(f"   Memory System:")
                print(f"     - Memories stored: {mm.get('memories_stored', 0)}")
                print(f"     - Queries processed: {mm.get('queries_total', 0)}")
                print(f"     - Cache hit rate: {mm.get('queries_cached', 0) / max(mm.get('queries_total', 1), 1) * 100:.1f}%")
                print(f"     - Avg query time: {mm.get('avg_query_time', 0):.3f}s")
            
            if 'conversation_manager' in metrics:
                cm = metrics['conversation_manager']
                print(f"   Conversation System:")
                print(f"     - Conversations created: {cm.get('conversations_created', 0)}")
                print(f"     - Messages added: {cm.get('messages_added', 0)}")
                print(f"     - Avg response time: {cm.get('avg_response_time', 0):.3f}s")
            
            # Perform health check
            print("\nPerforming comprehensive health check...")
            health = await self.db_manager.health_check()
            
            print(f"✅ System Health: {health['status'].upper()}")
            for component, status in health.get('components', {}).items():
                component_status = status.get('status', 'unknown')
                print(f"   - {component.title()}: {component_status.upper()}")
            
            # Run maintenance tasks
            print("\nRunning maintenance tasks...")
            maintenance = await self.db_manager.maintenance_tasks()
            
            print(f"✅ Maintenance: {maintenance['status'].upper()}")
            for task in maintenance.get('tasks_completed', []):
                print(f"   - {task}")
            
        except Exception as e:
            print(f"❌ Analytics error: {e}")
    
    async def demonstrate_advanced_features(self):
        """Demonstrate advanced features and integrations."""
        print("\n🚀 === ADVANCED FEATURES SHOWCASE ===")
        
        if not self.tenant_id:
            print("❌ No tenant available for advanced features demo")
            return
        
        try:
            # Demonstrate bulk memory storage
            print("Demonstrating bulk memory operations...")
            
            bulk_memories = [
                f"Project meeting notes from {datetime.now().strftime('%Y-%m-%d')}: Discussed API design patterns",
                f"User feedback: The new interface is much more intuitive than the previous version",
                f"Technical decision: We decided to use PostgreSQL for the main database",
                f"Performance optimization: Implemented Redis caching for frequently accessed data",
                f"Security update: Added multi-factor authentication to all admin accounts"
            ]
            
            stored_count = 0
            for content in bulk_memories:
                memory_id = await self.db_manager.store_memory(
                    tenant_id=self.tenant_id,
                    content=content,
                    user_id=self.user_id,
                    metadata={"batch": "demo_bulk", "timestamp": datetime.utcnow().isoformat()}
                )
                if memory_id:
                    stored_count += 1
            
            print(f"✅ Bulk stored {stored_count} memories")
            
            # Demonstrate contextual memory retrieval
            print("\nDemonstrating contextual memory retrieval...")
            
            context_queries = [
                "What technical decisions have been made?",
                "Any user feedback about the interface?",
                "What security measures are in place?"
            ]
            
            for query in context_queries:
                memories = await self.db_manager.query_memories(
                    tenant_id=self.tenant_id,
                    query_text=query,
                    user_id=self.user_id,
                    top_k=2
                )
                
                print(f"\n🔍 Context Query: '{query}'")
                for memory in memories:
                    score = memory.get('similarity_score', 0)
                    print(f"   [{score:.3f}] {memory['content']}")
            
            # Demonstrate conversation context integration
            if self.conversation_id:
                print("\nDemonstrating conversation-memory integration...")
                
                # Add a message that should trigger memory context
                await self.db_manager.add_message(
                    tenant_id=self.tenant_id,
                    conversation_id=self.conversation_id,
                    role="user",
                    content="Can you remind me what technical decisions we've made for this project?"
                )
                
                # The system should automatically find relevant memories
                conversation = await self.db_manager.get_conversation(
                    tenant_id=self.tenant_id,
                    conversation_id=self.conversation_id
                )
                
                memory_context = conversation.get('metadata', {}).get('memory_context', [])
                if memory_context:
                    print(f"✅ Found {len(memory_context)} relevant memories for context:")
                    for context in memory_context:
                        print(f"   - {context['content'][:60]}...")
                else:
                    print("ℹ️  No memory context found (may require actual vector database)")
            
        except Exception as e:
            print(f"❌ Advanced features error: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        print("\n🧹 Cleaning up resources...")
        
        if self.db_manager:
            try:
                await self.db_manager.cleanup()
                print("✅ Database resources cleaned up successfully")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
    
    async def run_showcase(self):
        """Run the complete database showcase."""
        print("=" * 80)
        print("🎯 AI KAREN DATABASE SYSTEM SHOWCASE")
        print("=" * 80)
        print("This demo showcases the production-grade database capabilities:")
        print("• Multi-tenant architecture with schema isolation")
        print("• Advanced memory system with semantic search")
        print("• Intelligent conversation management")
        print("• Real-time analytics and health monitoring")
        print("• Comprehensive maintenance and optimization")
        print("=" * 80)
        
        try:
            # Initialize the system
            initialized = await self.initialize()
            if not initialized:
                print("\n⚠️  Running in demo mode (showing API structure)")
                await self.demo_mode()
                return
            
            # Run all demonstrations
            await self.demonstrate_tenant_management()
            await self.demonstrate_memory_system()
            await self.demonstrate_conversation_system()
            await self.demonstrate_analytics_and_insights()
            await self.demonstrate_advanced_features()
            
            print("\n" + "=" * 80)
            print("🎉 DATABASE SHOWCASE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("Key achievements demonstrated:")
            print("✅ Multi-tenant data isolation")
            print("✅ Semantic memory storage and retrieval")
            print("✅ Context-aware conversations")
            print("✅ Real-time system monitoring")
            print("✅ Automated maintenance tasks")
            print("✅ Production-ready scalability")
            
        except Exception as e:
            print(f"\n❌ Showcase error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup()
    
    async def demo_mode(self):
        """Run in demo mode without actual database connections."""
        print("\n📋 DEMO MODE - API Structure Overview")
        print("=" * 50)
        
        # Show the API structure
        api_examples = {
            "Tenant Management": [
                "POST /api/v1/database/tenants - Create tenant",
                "GET /api/v1/database/tenants/{id} - Get tenant info",
                "GET /api/v1/database/tenants/{id}/stats - Get statistics"
            ],
            "Memory System": [
                "POST /api/v1/database/tenants/{id}/memories - Store memory",
                "POST /api/v1/database/tenants/{id}/memories/query - Search memories",
                "POST /api/v1/database/tenants/{id}/memories/bulk - Bulk store"
            ],
            "Conversations": [
                "POST /api/v1/database/tenants/{id}/conversations - Create conversation",
                "GET /api/v1/database/tenants/{id}/conversations/{id} - Get conversation",
                "POST /api/v1/database/tenants/{id}/conversations/{id}/messages - Add message"
            ],
            "System": [
                "GET /api/v1/database/health - Health check",
                "GET /api/v1/database/metrics - System metrics",
                "POST /api/v1/database/maintenance - Run maintenance"
            ]
        }
        
        for category, endpoints in api_examples.items():
            print(f"\n{category}:")
            for endpoint in endpoints:
                print(f"  • {endpoint}")
        
        print("\n🏗️  Database Architecture:")
        print("  • PostgreSQL: Multi-tenant with schema-per-tenant")
        print("  • Milvus: Vector database for semantic search")
        print("  • Redis: High-performance caching layer")
        print("  • Elasticsearch: Full-text search capabilities")
        
        print("\n🔧 Key Features:")
        print("  • Automatic schema management")
        print("  • Intelligent memory deduplication")
        print("  • Context-aware conversation handling")
        print("  • Real-time health monitoring")
        print("  • Automated maintenance tasks")


async def main():
    """Main function to run the showcase."""
    showcase = DatabaseShowcase()
    await showcase.run_showcase()


if __name__ == "__main__":
    asyncio.run(main())