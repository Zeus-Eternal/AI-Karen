#!/usr/bin/env python3
"""
Test DistilBERT service functionality.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment variables for offline mode
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_distilbert_service():
    """Test DistilBERT service functionality."""
    try:
        from ai_karen_engine.services.distilbert_service import DistilBertService
        from ai_karen_engine.services.nlp_config import DistilBertConfig
        
        logger.info("Testing DistilBERT service...")
        
        # Create service with default config
        config = DistilBertConfig()
        service = DistilBertService(config)
        
        # Check health status
        health = service.get_health_status()
        logger.info(f"Health status: {health}")
        
        # Test embeddings
        test_text = "This is a test sentence for embedding generation."
        logger.info(f"Testing embeddings for: '{test_text}'")
        
        embeddings = await service.get_embeddings(test_text)
        logger.info(f"Generated embeddings: {len(embeddings)} dimensions")
        logger.info(f"First 5 values: {embeddings[:5]}")
        
        # Test classification
        classification = await service.classify_text(test_text)
        logger.info(f"Classification result: {classification}")
        
        # Test sentiment analysis
        sentiment = await service.analyze_sentiment(test_text)
        logger.info(f"Sentiment result: {sentiment}")
        
        logger.info("✓ DistilBERT service test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"DistilBERT service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    logger.info("DistilBERT Service Test")
    logger.info("=" * 30)
    
    success = asyncio.run(test_distilbert_service())
    
    if success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())