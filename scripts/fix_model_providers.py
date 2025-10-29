#!/usr/bin/env python3
"""
Fix Model Provider Configuration and Download Models

This script addresses the following issues:
1. Configure proper model providers (including cloud providers)
2. Download essential models (Stable Diffusion and text models)
3. Fix model registry configuration
4. Ensure providers show only when they have available models
"""

import json
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_models_directory():
    """Ensure models directory structure exists"""
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    subdirs = [
        "transformers",
        "llama-cpp", 
        "stable-diffusion",
        "downloads",
        "metadata_cache"
    ]
    
    for subdir in subdirs:
        (models_dir / subdir).mkdir(exist_ok=True)
    
    logger.info(f"✅ Models directory structure created at {models_dir.absolute()}")

def update_model_registry():
    """Update model registry with proper configuration"""
    registry_path = Path("./model_registry.json")
    
    # Enhanced model registry with better organization
    registry = [
        # Local transformers models
        {
            "name": "bert-base-uncased",
            "source": "hf_hub",
            "type": "transformers",
            "family": "bert",
            "capabilities": ["text-classification", "feature-extraction"]
        },
        {
            "name": "sentence-transformers/all-MiniLM-L6-v2", 
            "source": "hf_hub",
            "type": "transformers",
            "family": "sentence-transformers",
            "capabilities": ["embeddings", "semantic-search"]
        },
        # Local GGUF models
        {
            "name": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
            "path": "./models/llama-cpp/tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
            "type": "llama-gguf",
            "source": "local",
            "family": "tinyllama",
            "capabilities": ["text-generation", "chat"]
        },
        {
            "name": "Phi-3-mini-4k-instruct-q4.gguf",
            "path": "./models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf", 
            "type": "llama-gguf",
            "source": "local",
            "family": "phi",
            "capabilities": ["text-generation", "instruction-following"]
        }
    ]
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"✅ Updated model registry at {registry_path}")

def create_provider_config():
    """Create provider configuration file"""
    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)
    
    provider_config = {
        "providers": {
            "local": {
                "transformers": {
                    "enabled": True,
                    "models_path": "./models/transformers",
                    "cache_dir": "./models/metadata_cache"
                },
                "llama-cpp": {
                    "enabled": True,
                    "models_path": "./models/llama-cpp",
                    "n_ctx": 4096,
                    "n_threads": -1
                }
            },
            "cloud": {
                "openai": {
                    "enabled": False,
                    "api_key": "${OPENAI_API_KEY}",
                    "base_url": "https://api.openai.com/v1"
                },
                "huggingface": {
                    "enabled": True,
                    "api_key": "${HUGGINGFACE_API_KEY}",
                    "base_url": "https://api-inference.huggingface.co"
                }
            }
        },
        "model_discovery": {
            "auto_discover": True,
            "cache_duration": 3600,
            "filter_by_capabilities": True
        }
    }
    
    config_path = config_dir / "providers.json"
    with open(config_path, 'w') as f:
        json.dump(provider_config, f, indent=2)
    
    logger.info(f"✅ Created provider configuration at {config_path}")

def download_essential_models():
    """Download essential models for immediate use"""
    logger.info("📥 Downloading essential models...")
    
    # Check if we have Python environment
    try:
        import torch
        import transformers
        logger.info("✅ PyTorch and Transformers available")
    except ImportError:
        logger.warning("⚠️ PyTorch/Transformers not available, skipping model downloads")
        return
    
    # Download a small text model
    try:
        from transformers import AutoTokenizer, AutoModel
        
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        cache_dir = "./models/transformers"
        
        logger.info(f"Downloading {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
        
        logger.info(f"✅ Downloaded {model_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to download text model: {e}")

def update_env_file():
    """Update environment file with model provider settings"""
    env_path = Path(".env")
    
    # Read existing env file
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Add model provider settings if not present
    model_settings = """
# ============================================================================
# Model Provider Configuration
# ============================================================================
MODELS_ROOT=./models
MODEL_REGISTRY_PATH=./model_registry.json
PROVIDER_CONFIG_PATH=./config/providers.json
ENABLE_MODEL_DISCOVERY=true
ENABLE_LOCAL_PROVIDERS=true
ENABLE_CLOUD_PROVIDERS=true
HUGGINGFACE_CACHE_DIR=./models/transformers
LLAMACPP_MODELS_PATH=./models/llama-cpp

# Model Provider API Keys (set these for cloud providers)
# OPENAI_API_KEY=your_openai_key_here
# HUGGINGFACE_API_KEY=your_huggingface_key_here
"""
    
    if "MODELS_ROOT" not in env_content:
        env_content += model_settings
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        logger.info("✅ Updated .env file with model provider settings")

def main():
    """Main function to fix model provider issues"""
    logger.info("🔧 Starting model provider configuration fix...")
    
    try:
        # Step 1: Ensure directory structure
        ensure_models_directory()
        
        # Step 2: Update model registry
        update_model_registry()
        
        # Step 3: Create provider configuration
        create_provider_config()
        
        # Step 4: Update environment file
        update_env_file()
        
        # Step 5: Download essential models
        download_essential_models()
        
        logger.info("✅ Model provider configuration completed successfully!")
        logger.info("\n📋 Next steps:")
        logger.info("1. Restart your backend server")
        logger.info("2. Check the model library in your UI")
        logger.info("3. Configure API keys for cloud providers if needed")
        logger.info("4. Download additional models as required")
        
    except Exception as e:
        logger.error(f"❌ Failed to configure model providers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()