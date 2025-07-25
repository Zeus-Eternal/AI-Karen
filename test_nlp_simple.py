#!/usr/bin/env python3
"""
Simple test script for NLP services without full service imports.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly to avoid circular imports
from ai_karen_engine.services.spacy_service import SpacyService
from ai_karen_engine.services.distilbert_service import DistilBertService
from ai_karen_engine.services.nlp_config import NLPConfig


async def test_nlp_services_simple():
    """Test the NLP services directly."""
    print("🚀 Testing NLP Services (Simple)")
    print("=" * 50)
    
    try:
        # Create configuration
        config = NLPConfig()
        print(f"📋 Configuration loaded:")
        print(f"  spaCy model: {config.spacy.model_name}")
        print(f"  DistilBERT model: {config.distilbert.model_name}")
        
        # Initialize services
        print("\n🔧 Initializing services...")
        spacy_service = SpacyService(config.spacy)
        distilbert_service = DistilBertService(config.distilbert)
        
        # Check health status
        spacy_health = spacy_service.get_health_status()
        distilbert_health = distilbert_service.get_health_status()
        
        print(f"✅ spaCy healthy: {spacy_health.is_healthy}")
        print(f"   Model loaded: {spacy_health.model_loaded}")
        print(f"   Fallback mode: {spacy_health.fallback_mode}")
        
        print(f"✅ DistilBERT healthy: {distilbert_health.is_healthy}")
        print(f"   Model loaded: {distilbert_health.model_loaded}")
        print(f"   Fallback mode: {distilbert_health.fallback_mode}")
        print(f"   Device: {distilbert_health.device}")
        
        # Test message parsing
        print("\n🔍 Testing spaCy Message Parsing...")
        test_message = "Hello, my name is John Doe and I work at OpenAI in San Francisco. I love machine learning!"
        
        parsed = await spacy_service.parse_message(test_message)
        print(f"  Tokens found: {len(parsed.tokens)}")
        print(f"  Entities found: {len(parsed.entities)}")
        print(f"  Entities: {parsed.entities}")
        print(f"  Processing time: {parsed.processing_time:.4f}s")
        print(f"  Used fallback: {parsed.used_fallback}")
        
        # Test embedding generation
        print("\n🧠 Testing DistilBERT Embeddings...")
        embeddings = await distilbert_service.get_embeddings(test_message)
        print(f"  Embedding dimension: {len(embeddings)}")
        print(f"  Embedding norm: {sum(x*x for x in embeddings) ** 0.5:.4f}")
        
        # Test batch processing
        print("\n📦 Testing Batch Processing...")
        test_texts = [
            "First test sentence",
            "Second test sentence", 
            "Third test sentence"
        ]
        
        batch_embeddings = await distilbert_service.batch_embeddings(test_texts)
        print(f"  Batch size: {len(test_texts)}")
        print(f"  Embeddings generated: {len(batch_embeddings)}")
        
        # Test semantic similarity calculation
        print("\n📏 Testing Semantic Similarity...")
        text1 = "I love machine learning and artificial intelligence"
        text2 = "AI and ML are fascinating fields of study"
        text3 = "I enjoy cooking and baking delicious food"
        
        embeddings_batch = await distilbert_service.get_embeddings([text1, text2, text3])
        
        # Calculate cosine similarity
        import numpy as np
        
        def cosine_similarity(vec1, vec2):
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        
        similarity_12 = cosine_similarity(embeddings_batch[0], embeddings_batch[1])
        similarity_13 = cosine_similarity(embeddings_batch[0], embeddings_batch[2])
        
        print(f"  Similarity (ML texts): {similarity_12:.4f}")
        print(f"  Similarity (ML vs cooking): {similarity_13:.4f}")
        
        # Test cache performance
        print("\n⚡ Testing Cache Performance...")
        import time
        
        # First call (cache miss)
        start_time = time.time()
        await spacy_service.parse_message(test_message)
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        await spacy_service.parse_message(test_message)
        second_call_time = time.time() - start_time
        
        print(f"  First call (cache miss): {first_call_time:.4f}s")
        print(f"  Second call (cache hit): {second_call_time:.4f}s")
        print(f"  Speedup: {first_call_time / second_call_time:.2f}x")
        
        # Test error handling with empty input
        print("\n🛡️ Testing Error Handling...")
        empty_parsed = await spacy_service.parse_message("")
        empty_embeddings = await distilbert_service.get_embeddings("")
        
        print(f"  Empty text parsing: {len(empty_parsed.tokens)} tokens")
        print(f"  Empty text embeddings: {len(empty_embeddings)} dimensions")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_nlp_services_simple())
    sys.exit(0 if success else 1)