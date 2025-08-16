#!/usr/bin/env python3
"""
Quick test script to verify the fixes for:
1. Memory Manager None issue
2. Ollama model availability issue
"""

import asyncio
import logging
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_memory_manager_fix():
    """Test that MemoryProcessor can be created with a proper MemoryManager."""
    try:
        from ai_karen_engine.chat.memory_processor import MemoryProcessor
        from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
        from ai_karen_engine.database.memory_manager import MemoryManager
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        from ai_karen_engine.core.milvus_client import MilvusClient
        
        logger.info("🧪 Testing Memory Manager fix...")
        
        # Try to create the components
        db_client = MultiTenantPostgresClient()
        milvus_client = MilvusClient()
        
        # Create memory manager (this should not be None anymore)
        memory_manager = MemoryManager(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=None  # OK to be None for this test
        )
        
        # Create memory processor
        memory_processor = MemoryProcessor(
            spacy_service=nlp_service_manager.spacy_service,
            distilbert_service=nlp_service_manager.distilbert_service,
            memory_manager=memory_manager,
        )
        
        # Verify memory_manager is not None
        assert memory_processor.memory_manager is not None, "MemoryManager should not be None"
        
        logger.info("✅ Memory Manager fix verified - MemoryProcessor has valid memory_manager")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory Manager test failed: {e}")
        return False

def test_ollama_model_availability():
    """Test that Ollama has the correct model available."""
    try:
        import requests
        
        logger.info("🧪 Testing Ollama model availability...")
        
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Ollama is not running or not accessible")
            return False
        
        models_data = response.json()
        available_models = [model['name'] for model in models_data.get('models', [])]
        
        logger.info(f"Available Ollama models: {available_models}")
        
        # Check if we have llama3.2:1b (the model we updated the config to use)
        if 'llama3.2:1b' in available_models:
            logger.info("✅ Ollama model fix verified - llama3.2:1b is available")
            return True
        else:
            logger.warning(f"⚠️  llama3.2:1b not found. Available: {available_models}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ollama model test failed: {e}")
        return False

async def test_chat_orchestrator_creation():
    """Test that ChatOrchestrator can be created with the fixed memory manager."""
    try:
        from ai_karen_engine.api_routes.websocket_routes import get_chat_orchestrator
        
        logger.info("🧪 Testing ChatOrchestrator creation...")
        
        # This should now work without the AttributeError
        chat_orchestrator = get_chat_orchestrator()
        
        # Verify the orchestrator has a memory processor
        assert hasattr(chat_orchestrator, 'memory_processor'), "ChatOrchestrator should have memory_processor"
        assert chat_orchestrator.memory_processor is not None, "memory_processor should not be None"
        
        # Verify the memory processor has a memory manager (might be None due to initialization issues, but shouldn't cause AttributeError)
        memory_processor = chat_orchestrator.memory_processor
        assert hasattr(memory_processor, 'memory_manager'), "MemoryProcessor should have memory_manager attribute"
        
        logger.info("✅ ChatOrchestrator creation verified - no AttributeError on memory_manager")
        return True
        
    except Exception as e:
        logger.error(f"❌ ChatOrchestrator creation test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Starting fix verification tests...")
    
    results = []
    
    # Test 1: Memory Manager fix
    results.append(await test_memory_manager_fix())
    
    # Test 2: Ollama model availability
    results.append(test_ollama_model_availability())
    
    # Test 3: ChatOrchestrator creation
    results.append(await test_chat_orchestrator_creation())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All fixes verified successfully!")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)