#!/usr/bin/env python3
"""
Download DistilBERT model for offline use.

This script downloads the DistilBERT model and tokenizer to the local cache
so the service can run in offline mode.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_distilbert_model():
    """Download DistilBERT model and tokenizer for offline use."""
    try:
        # Import transformers
        from transformers import AutoTokenizer, AutoModel
        
        # Model name from config
        model_name = os.getenv("TRANSFORMER_MODEL", "distilbert-base-uncased")
        
        logger.info(f"Downloading DistilBERT model: {model_name}")
        
        # Download tokenizer
        logger.info("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info("✓ Tokenizer downloaded successfully")
        
        # Download model
        logger.info("Downloading model...")
        model = AutoModel.from_pretrained(model_name)
        logger.info("✓ Model downloaded successfully")
        
        # Test the model works
        logger.info("Testing model...")
        test_text = "This is a test sentence."
        inputs = tokenizer(test_text, return_tensors="pt", truncation=True, padding=True)
        outputs = model(**inputs)
        logger.info("✓ Model test successful")
        
        logger.info(f"✓ DistilBERT model '{model_name}' is ready for offline use")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import transformers: {e}")
        logger.error("Please install transformers: pip install transformers torch")
        return False
    except Exception as e:
        logger.error(f"Failed to download DistilBERT model: {e}")
        return False

def check_model_availability():
    """Check if the model is already available locally."""
    try:
        from transformers import AutoTokenizer, AutoModel
        
        model_name = os.getenv("TRANSFORMER_MODEL", "distilbert-base-uncased")
        
        logger.info(f"Checking local availability of model: {model_name}")
        
        # Try to load from cache only
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        model = AutoModel.from_pretrained(model_name, local_files_only=True)
        
        logger.info("✓ Model is available locally")
        return True
        
    except Exception as e:
        logger.info(f"Model not available locally: {e}")
        return False

def main():
    """Main function."""
    logger.info("DistilBERT Model Download Script")
    logger.info("=" * 40)
    
    # Check if model is already available
    if check_model_availability():
        logger.info("Model is already available locally. No download needed.")
        return 0
    
    # Download the model
    if download_distilbert_model():
        logger.info("Model download completed successfully!")
        return 0
    else:
        logger.error("Model download failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())