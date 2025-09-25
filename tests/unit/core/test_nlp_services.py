#!/usr/bin/env python3
"""
Test script for NLP services integration.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.services import nlp_service_manager


async def test_nlp_services():
    """Test the NLP services integration."""
    print("🚀 Testing NLP Services Integration")
    print("=" * 50)
    
    try:
        # Initialize the NLP service manager
        print("📋 Initializing NLP Service Manager...")
        await nlp_service_manager.initialize()
        
        # Check if services are ready
        print(f"✅ Services ready: {nlp_service_manager.is_ready()}")
        
        # Get service info
        service_info = nlp_service_manager.get_service_info()
        print("\n📊 Service Information:")
        print(f"  spaCy model: {service_info['spacy']['model_name']}")
        print(f"  spaCy loaded: {service_info['spacy']['model_loaded']}")
        print(f"  spaCy fallback: {service_info['spacy']['fallback_mode']}")
        print(f"  DistilBERT model: {service_info['distilbert']['model_name']}")
        print(f"  DistilBERT loaded: {service_info['distilbert']['model_loaded']}")
        print(f"  DistilBERT fallback: {service_info['distilbert']['fallback_mode']}")
        print(f"  DistilBERT device: {service_info['distilbert']['device']}")
        
        # Test message parsing
        print("\n🔍 Testing spaCy Message Parsing...")
        test_message = "Hello, my name is John Doe and I work at OpenAI in San Francisco. I love machine learning!"
        
        parsed = await nlp_service_manager.parse_message(test_message)
        print(f"  Tokens found: {len(parsed.tokens)}")
        print(f"  Entities found: {len(parsed.entities)}")
        print(f"  Entities: {parsed.entities}")
        print(f"  Processing time: {parsed.processing_time:.4f}s")
        print(f"  Used fallback: {parsed.used_fallback}")
        
        # Test embedding generation
        print("\n🧠 Testing DistilBERT Embeddings...")
        embeddings = await nlp_service_manager.get_embeddings(test_message)
        print(f"  Embedding dimension: {len(embeddings)}")
        print(f"  Embedding norm: {sum(x*x for x in embeddings) ** 0.5:.4f}")
        
        # Test full message processing
        print("\n🔄 Testing Full Message Processing...")
        full_result = await nlp_service_manager.process_message_full(test_message)
        print(f"  Tokens: {len(full_result['parsed']['tokens'])}")
        print(f"  Entities: {len(full_result['parsed']['entities'])}")
        print(f"  Embedding dimension: {full_result['embedding_dimension']}")
        
        # Test semantic similarity
        print("\n📏 Testing Semantic Similarity...")
        text1 = "I love machine learning and artificial intelligence"
        text2 = "AI and ML are fascinating fields of study"
        text3 = "I enjoy cooking and baking delicious food"
        
        similarity_12 = await nlp_service_manager.semantic_similarity(text1, text2)
        similarity_13 = await nlp_service_manager.semantic_similarity(text1, text3)
        
        print(f"  Similarity (ML texts): {similarity_12:.4f}")
        print(f"  Similarity (ML vs cooking): {similarity_13:.4f}")
        
        # Test batch processing
        print("\n📦 Testing Batch Processing...")
        test_texts = [
            "First test sentence",
            "Second test sentence", 
            "Third test sentence"
        ]
        
        batch_embeddings = await nlp_service_manager.batch_embeddings(test_texts)
        print(f"  Batch size: {len(test_texts)}")
        print(f"  Embeddings generated: {len(batch_embeddings)}")
        
        # Test entity extraction with embeddings
        print("\n🏷️ Testing Entity Extraction with Embeddings...")
        entities_with_embeddings = await nlp_service_manager.extract_entities_with_embeddings(test_message)
        print(f"  Entities with embeddings: {len(entities_with_embeddings)}")
        for entity in entities_with_embeddings:
            print(f"    {entity['text']} ({entity['label']}) - embedding dim: {len(entity['embedding'])}")
        
        # Get health status
        print("\n🏥 Health Status:")
        health_summary = nlp_service_manager.get_health_summary()
        print(f"  Overall status: {health_summary['status']}")
        print(f"  Uptime: {health_summary['uptime']:.2f}s")
        if health_summary['alerts']:
            print(f"  Alerts: {health_summary['alerts']}")
        
        # Run diagnostics
        print("\n🔧 Running Diagnostics...")
        diagnostic_results = await nlp_service_manager.run_diagnostic()
        print(f"  Overall status: {diagnostic_results['overall_status']}")
        print(f"  Tests passed: {diagnostic_results['passed_tests']}/{diagnostic_results['total_tests']}")
        
        for test_name, test_result in diagnostic_results['tests'].items():
            status_emoji = "✅" if test_result['status'] == 'pass' else "❌"
            print(f"    {status_emoji} {test_name}: {test_result['status']}")
            if test_result['status'] == 'pass' and 'processing_time' in test_result:
                print(f"      Processing time: {test_result['processing_time']:.4f}s")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Shutdown services
        print("\n🛑 Shutting down services...")
        await nlp_service_manager.shutdown()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_nlp_services())
    sys.exit(0 if success else 1)