#!/usr/bin/env python3
"""
Setup AI Karen Technology Stack and Admin User
Ensures the system follows the specified architecture and creates the default admin user.

Technology Stack Verification:
- Short-Term Memory: Redis (TTL-based, Streams for real-time events)
- Long-Term Memory: Milvus (vector embeddings, HNSW indexing) + DuckDB (OLAP staging & compaction)
- Persistent Memory: PostgreSQL (structured metadata with Milvus references)
- Observability: Prometheus (metrics) + Grafana (dashboards)
- Embeddings: all-MPNet-base-v2 + dual-embedding rerank (full model download)
- API Layer: FastAPI with dependency injection
"""

import asyncio
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def verify_environment_variables():
    """Verify all required environment variables are set."""
    print("🔧 Verifying environment variables...")
    
    required_vars = {
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'POSTGRES_PORT': os.getenv('POSTGRES_PORT', '5432'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER', 'karen_user'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB', 'ai_karen'),
        'KARI_DUCKDB_PASSWORD': os.getenv('KARI_DUCKDB_PASSWORD', 'dev-duckdb-pass'),
        'KARI_JOB_ENC_KEY': os.getenv('KARI_JOB_ENC_KEY', 'MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo='),
        'AUTH_SECRET_KEY': os.getenv('AUTH_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production-minimum-32-chars'),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://:redis_secure_pass_change_me@localhost:6379/0'),
        'MILVUS_HOST': os.getenv('MILVUS_HOST', 'localhost'),
        'MILVUS_PORT': os.getenv('MILVUS_PORT', '19530'),
    }
    
    missing_vars = []
    for var, value in required_vars.items():
        if not value or value.startswith('change-me') or value.startswith('your-'):
            missing_vars.append(var)
        else:
            print(f"   ✅ {var}: {value[:20]}{'...' if len(value) > 20 else ''}")
    
    if missing_vars:
        print(f"   ⚠️  Warning: Some environment variables need attention: {missing_vars}")
        print("   ℹ️  Using defaults for development - update for production")
    
    return required_vars

async def verify_database_clients():
    """Verify all required database clients are available."""
    print("🗄️  Verifying database clients...")
    
    clients_status = {}
    
    # PostgreSQL Client
    try:
        from ai_karen_engine.clients.database.postgres_client import PostgresClient
        postgres_client = PostgresClient()
        clients_status['postgresql'] = True
        print("   ✅ PostgreSQL client available")
    except Exception as e:
        clients_status['postgresql'] = False
        print(f"   ❌ PostgreSQL client error: {e}")
    
    # Redis Client
    try:
        from ai_karen_engine.clients.database.redis_client import RedisClient
        redis_client = RedisClient()
        clients_status['redis'] = True
        print("   ✅ Redis client available")
    except Exception as e:
        clients_status['redis'] = False
        print(f"   ❌ Redis client error: {e}")
    
    # Milvus Client
    try:
        from ai_karen_engine.clients.database.milvus_client import MilvusClient
        milvus_client = MilvusClient()
        clients_status['milvus'] = True
        print("   ✅ Milvus client available")
    except Exception as e:
        clients_status['milvus'] = False
        print(f"   ❌ Milvus client error: {e}")
    
    # DuckDB Client
    try:
        from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
        duckdb_client = DuckDBClient()
        clients_status['duckdb'] = True
        print("   ✅ DuckDB client available")
    except Exception as e:
        clients_status['duckdb'] = False
        print(f"   ❌ DuckDB client error: {e}")
    
    return clients_status

async def verify_embedding_model():
    """Verify the embedding model is configured correctly."""
    print("🧠 Verifying embedding model configuration...")
    
    try:
        from ai_karen_engine.core.embedding_manager import EmbeddingManager
        
        # Check if the model is configured to use all-MPNet-base-v2
        embedding_manager = EmbeddingManager()
        
        if 'all-MPNet-base-v2' in embedding_manager.model_name:
            print(f"   ✅ Embedding model correctly configured: {embedding_manager.model_name}")
            
            # Try to initialize the model
            await embedding_manager.initialize()
            
            if embedding_manager.model_loaded:
                print(f"   ✅ Embedding model loaded successfully (dim={embedding_manager.dim})")
                
                # Test embedding generation
                test_embedding = await embedding_manager.get_embedding("test memory content")
                if len(test_embedding) == embedding_manager.dim:
                    print("   ✅ Embedding generation test passed")
                    return True
                else:
                    print(f"   ❌ Embedding dimension mismatch: expected {embedding_manager.dim}, got {len(test_embedding)}")
            else:
                print("   ⚠️  Embedding model not loaded - will use fallback")
                return True  # Fallback is acceptable
        else:
            print(f"   ⚠️  Embedding model not using all-MPNet-base-v2: {embedding_manager.model_name}")
            return False
            
    except Exception as e:
        print(f"   ❌ Embedding model verification failed: {e}")
        return False

async def verify_memory_flow():
    """Verify the memory flow architecture is in place."""
    print("🧠 Verifying memory flow architecture...")
    
    try:
        # Check memory service
        from ai_karen_engine.services.memory_service import WebUIMemoryService, MemoryType, UISource
        print("   ✅ Memory service with web UI integration available")
        
        # Check memory routes
        from ai_karen_engine.api_routes.memory_routes import router
        print("   ✅ Memory API routes available")
        
        # Check database schema
        schema_file = "data/migrations/postgres/015_neuro_vault_schema_extensions.sql"
        if os.path.exists(schema_file):
            print("   ✅ NeuroVault schema extensions available")
        else:
            print("   ⚠️  NeuroVault schema extensions not found")
        
        # Check memory manager
        from ai_karen_engine.database.memory_manager import MemoryManager
        print("   ✅ Memory manager available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Memory flow verification failed: {e}")
        return False

async def verify_observability():
    """Verify observability components are available."""
    print("📊 Verifying observability components...")
    
    try:
        # Check Prometheus metrics
        from ai_karen_engine.utils.metrics import init_metrics
        metrics = init_metrics()
        print("   ✅ Prometheus metrics available")
        
        # Check plugin metrics
        from ai_karen_engine.core.plugin_metrics import PLUGIN_CALLS
        print("   ✅ Plugin metrics available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Observability verification failed: {e}")
        return False

async def setup_admin_user():
    """Set up the default admin user using the consolidated auth service."""
    print("👤 Setting up admin user...")
    
    try:
        from ai_karen_engine.auth.service import get_auth_service
        
        # Get auth service
        auth_service = await get_auth_service()
        print("   ✅ Auth service initialized")
        
        # Admin user details (password meets complexity requirements: uppercase, lowercase, digit, special char)
        admin_email = "admin@kari.ai"
        admin_password = "Password123!"
        
        # Try to authenticate first to see if user exists
        try:
            user_data = await auth_service.authenticate_user(
                email=admin_email,
                password=admin_password,
                ip_address='127.0.0.1',
                user_agent='setup-script'
            )
            print(f"   ✅ Admin user {admin_email} already exists and can authenticate")
            print(f"      User ID: {user_data.user_id}")
            print(f"      Roles: {user_data.roles}")
            print(f"      Tenant: {user_data.tenant_id}")
            return True
            
        except Exception:
            print(f"   ℹ️  Admin user {admin_email} not found or cannot authenticate")
            print("   🔧 Creating admin user...")
            
            # Create the admin user
            try:
                user = await auth_service.create_user(
                    email=admin_email,
                    password=admin_password,
                    roles=['admin', 'user'],
                    preferences={
                        'personalityTone': 'professional',
                        'personalityVerbosity': 'balanced',
                        'preferredLLMProvider': 'ollama',
                        'preferredModel': 'llama3.2:latest',
                        'memoryDepth': 'high',
                        'customPersonaInstructions': 'You are an AI assistant with administrative privileges.'
                    }
                )
                print(f"   ✅ Admin user created successfully!")
                print(f"      User ID: {user.user_id}")
                print(f"      Email: {user.email}")
                print(f"      Roles: {user.roles}")
                print(f"      Tenant: {user.tenant_id}")
                
                # Test authentication
                auth_result = await auth_service.authenticate_user(
                    email=admin_email,
                    password=admin_password,
                    ip_address='127.0.0.1',
                    user_agent='setup-script'
                )
                print("   ✅ Admin user authentication test passed")
                return True
                
            except Exception as create_error:
                print(f"   ❌ Failed to create admin user: {create_error}")
                return False
                
    except Exception as service_error:
        print(f"   ❌ Failed to get auth service: {service_error}")
        return False

async def verify_api_layer():
    """Verify the FastAPI layer with dependency injection."""
    print("🚀 Verifying API layer...")
    
    try:
        # Check core dependencies
        from ai_karen_engine.core.dependencies import (
            get_current_user_context,
            get_memory_service,
            get_ai_orchestrator_service
        )
        print("   ✅ Core dependencies available")
        
        # Check auth routes
        from ai_karen_engine.api_routes.auth import router as auth_router
        print("   ✅ Auth routes available")
        
        # Check memory routes
        from ai_karen_engine.api_routes.memory_routes import router as memory_router
        print("   ✅ Memory routes available")
        
        # Check web UI compatibility
        from ai_karen_engine.api_routes.web_api_compatibility import router as web_router
        print("   ✅ Web UI compatibility layer available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API layer verification failed: {e}")
        return False

async def print_stack_summary():
    """Print a summary of the technology stack status."""
    print("\n" + "="*60)
    print("🏗️  AI KAREN TECHNOLOGY STACK SUMMARY")
    print("="*60)
    
    print("\n📋 Architecture Components:")
    print("   • Short-Term Memory: Redis (TTL-based, Streams)")
    print("   • Long-Term Memory: Milvus (HNSW indexing) + DuckDB (OLAP)")
    print("   • Persistent Memory: PostgreSQL (metadata + refs)")
    print("   • Observability: Prometheus metrics")
    print("   • Embeddings: all-MPNet-base-v2 + dual-embedding rerank")
    print("   • API Layer: FastAPI with dependency injection")
    
    print("\n🔄 Memory Flow:")
    print("   1. Insert: Events → embeddings → Redis (short-term) → PostgreSQL + Milvus (persistent)")
    print("   2. Query: Prompt planner → Redis + Milvus → DuckDB → Titan-style reranking")
    print("   3. Decay: TTL in Redis, importance-based eviction, archival in DuckDB")
    print("   4. Monitor: Prometheus metrics → Grafana dashboards")
    
    print("\n👤 Default Admin Account:")
    print("   • Email: admin@kari.ai")
    print("   • Password: Password123!")
    print("   • Roles: admin, user")
    print("   • ⚠️  Change password after first login!")

async def main():
    """Main setup function."""
    print("🚀 AI Karen Technology Stack Setup & Verification")
    print("=" * 60)
    
    # Verify environment
    env_vars = await verify_environment_variables()
    
    # Verify database clients
    clients_status = await verify_database_clients()
    
    # Verify embedding model
    embedding_ok = await verify_embedding_model()
    
    # Verify memory flow
    memory_flow_ok = await verify_memory_flow()
    
    # Verify observability
    observability_ok = await verify_observability()
    
    # Verify API layer
    api_ok = await verify_api_layer()
    
    # Setup admin user
    admin_ok = await setup_admin_user()
    
    # Print summary
    await print_stack_summary()
    
    # Final status
    print("\n" + "="*60)
    print("📊 SETUP STATUS")
    print("="*60)
    
    all_good = all([
        all(clients_status.values()),
        embedding_ok,
        memory_flow_ok,
        observability_ok,
        api_ok,
        admin_ok
    ])
    
    if all_good:
        print("✅ All systems verified and admin user ready!")
        print("\n🎉 You can now start the AI Karen server:")
        print("   python main.py")
        print("\n🌐 Web UI will be available at:")
        print("   http://localhost:8000")
        return True
    else:
        print("⚠️  Some components need attention - check the logs above")
        print("   The system may still work with fallback mechanisms")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)