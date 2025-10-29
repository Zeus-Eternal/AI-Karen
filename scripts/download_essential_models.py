#!/usr/bin/env python3
"""
Download Essential Models for AI-Karen

Downloads essential models including:
1. A small text generation model (TinyLlama)
2. A sentence transformer for embeddings
3. Stable Diffusion model (if requested)

Uses the correct .env_karen virtual environment
"""

import os
import sys
import logging
import subprocess
import json
from pathlib import Path
from urllib.request import urlretrieve
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we're using the correct virtual environment
VENV_PATH = Path(".env_karen")
if VENV_PATH.exists():
    # Update PATH to use the correct Python
    venv_bin = VENV_PATH / "bin"
    if venv_bin.exists():
        os.environ["PATH"] = f"{venv_bin}:{os.environ.get('PATH', '')}"
        sys.executable = str(venv_bin / "python")
        logger.info(f"✅ Using virtual environment: {VENV_PATH}")
    else:
        logger.warning(f"⚠️ Virtual environment bin directory not found: {venv_bin}")
else:
    logger.warning(f"⚠️ Virtual environment not found: {VENV_PATH}")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import huggingface_hub
        logger.info("✅ Hugging Face Hub available")
        return True
    except ImportError:
        logger.warning("⚠️ Hugging Face Hub not available")
        try:
            logger.info("📦 Installing huggingface_hub using .env_karen environment...")
            # Use the correct Python executable from .env_karen
            python_exe = VENV_PATH / "bin" / "python" if VENV_PATH.exists() else sys.executable
            subprocess.check_call([str(python_exe), "-m", "pip", "install", "huggingface_hub"])
            import huggingface_hub
            logger.info("✅ Hugging Face Hub installed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to install huggingface_hub: {e}")
            return False

def download_gguf_model():
    """Download a small GGUF model for immediate use"""
    models_dir = Path("./models/llama-cpp")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # TinyLlama GGUF model (small and fast)
    model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = models_dir / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    
    if model_path.exists():
        logger.info(f"✅ Model already exists: {model_path}")
        return str(model_path)
    
    try:
        logger.info(f"📥 Downloading TinyLlama GGUF model...")
        logger.info(f"URL: {model_url}")
        logger.info(f"Destination: {model_path}")
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                if block_num % 100 == 0:  # Print every 100 blocks
                    logger.info(f"Progress: {percent}%")
        
        urlretrieve(model_url, model_path, progress_hook)
        logger.info(f"✅ Downloaded TinyLlama GGUF model to {model_path}")
        return str(model_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to download GGUF model: {e}")
        return None

def download_transformers_model():
    """Download a small transformers model to the correct transformers directory"""
    if not check_dependencies():
        return None
    
    try:
        from huggingface_hub import snapshot_download
        
        # Ensure transformers models go to the correct location
        models_dir = Path("./models/transformers")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download sentence transformer (small and useful)
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_local_dir = models_dir / model_name.replace("/", "--")
        
        logger.info(f"📥 Downloading {model_name} to {model_local_dir}...")
        
        model_path = snapshot_download(
            repo_id=model_name,
            local_dir=str(model_local_dir),
            local_dir_use_symlinks=False
        )
        
        logger.info(f"✅ Downloaded {model_name} to {model_path}")
        return str(model_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to download transformers model: {e}")
        return None

def download_additional_transformers_models():
    """Download additional essential transformers models"""
    if not check_dependencies():
        return []
    
    try:
        from huggingface_hub import snapshot_download
        
        models_dir = Path("./models/transformers")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # List of essential models to download
        essential_models = [
            "microsoft/DialoGPT-medium",  # Conversational AI
            "distilbert-base-uncased",    # Text classification
            "gpt2",                       # Text generation (already exists, but ensure it's there)
        ]
        
        downloaded_paths = []
        
        for model_name in essential_models:
            model_local_dir = models_dir / model_name.replace("/", "--")
            
            # Skip if already exists
            if model_local_dir.exists() and any(model_local_dir.iterdir()):
                logger.info(f"✅ Model already exists: {model_name}")
                downloaded_paths.append(str(model_local_dir))
                continue
            
            try:
                logger.info(f"📥 Downloading {model_name} to {model_local_dir}...")
                
                model_path = snapshot_download(
                    repo_id=model_name,
                    local_dir=str(model_local_dir),
                    local_dir_use_symlinks=False
                )
                
                logger.info(f"✅ Downloaded {model_name} to {model_path}")
                downloaded_paths.append(str(model_path))
                
            except Exception as e:
                logger.error(f"❌ Failed to download {model_name}: {e}")
                continue
        
        return downloaded_paths
        
    except Exception as e:
        logger.error(f"❌ Failed to download additional transformers models: {e}")
        return []

def download_stable_diffusion():
    """Download Stable Diffusion model"""
    if not check_dependencies():
        return None
    
    try:
        from huggingface_hub import snapshot_download
        
        models_dir = Path("./models/stable-diffusion")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download a small/fast SD model
        model_name = "runwayml/stable-diffusion-v1-5"
        cache_dir = str(models_dir)
        
        logger.info(f"📥 Downloading Stable Diffusion model (this may take a while)...")
        logger.info(f"Model: {model_name}")
        
        # Only download essential files to save space
        model_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_dir=models_dir / "stable-diffusion-v1-5",
            local_dir_use_symlinks=False,
            allow_patterns=["*.json", "*.txt", "unet/*", "text_encoder/*", "vae/*", "tokenizer/*", "scheduler/*"]
        )
        
        logger.info(f"✅ Downloaded Stable Diffusion to {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"❌ Failed to download Stable Diffusion: {e}")
        return None

def ensure_transformers_models_in_correct_location():
    """Ensure all transformers models are in the correct models/transformers/ directory"""
    models_root = Path("./models")
    transformers_dir = models_root / "transformers"
    transformers_dir.mkdir(parents=True, exist_ok=True)
    
    # Look for transformers models in wrong locations
    moved_models = []
    
    for item in models_root.iterdir():
        if item.is_dir() and item.name not in ["transformers", "llama-cpp", "stable-diffusion", "downloads", "configs", "metadata_cache", "basic_cls"]:
            # Check if this looks like a transformers model
            if any((item / file).exists() for file in ["config.json", "tokenizer.json", "pytorch_model.bin", "model.safetensors"]):
                target_path = transformers_dir / item.name
                
                if not target_path.exists():
                    logger.info(f"📁 Moving transformers model {item.name} to correct location...")
                    shutil.move(str(item), str(target_path))
                    moved_models.append(item.name)
                    logger.info(f"✅ Moved {item.name} to models/transformers/")
                else:
                    logger.info(f"⚠️ Model {item.name} already exists in transformers directory, removing duplicate...")
                    shutil.rmtree(str(item))
                    logger.info(f"✅ Removed duplicate {item.name}")
    
    # Also check for nested model structures in transformers directory and flatten them
    for item in transformers_dir.iterdir():
        if item.is_dir():
            # Check if this is a nested structure (like deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B)
            subdirs = [d for d in item.iterdir() if d.is_dir()]
            if len(subdirs) == 1 and not any((item / file).exists() for file in ["config.json", "tokenizer.json", "pytorch_model.bin", "model.safetensors"]):
                # This looks like a nested structure, flatten it
                subdir = subdirs[0]
                if any((subdir / file).exists() for file in ["config.json", "tokenizer.json", "pytorch_model.bin", "model.safetensors"]):
                    new_name = f"{item.name}--{subdir.name}"
                    target_path = transformers_dir / new_name
                    
                    if not target_path.exists():
                        logger.info(f"📁 Flattening nested model structure: {item.name}/{subdir.name} -> {new_name}")
                        shutil.move(str(subdir), str(target_path))
                        shutil.rmtree(str(item))
                        moved_models.append(new_name)
                        logger.info(f"✅ Flattened {new_name}")
    
    return moved_models

def update_model_registry_with_downloads(downloaded_models):
    """Update model registry with downloaded models"""
    registry_path = Path("./model_registry.json")
    
    # Load existing registry
    registry = []
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)
    
    # Add downloaded models
    for model_info in downloaded_models:
        if model_info:
            # Check if model already exists in registry
            exists = any(m.get('name') == model_info['name'] or m.get('path') == model_info.get('path') for m in registry)
            if not exists:
                registry.append(model_info)
    
    # Save updated registry
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"✅ Updated model registry with {len(downloaded_models)} models")

def main():
    """Main function to download essential models using .env_karen environment"""
    logger.info("🚀 Starting essential model downloads using .env_karen environment...")
    
    # First, ensure all existing transformers models are in the correct location
    logger.info("\n0. Organizing existing transformers models...")
    moved_models = ensure_transformers_models_in_correct_location()
    if moved_models:
        logger.info(f"✅ Moved {len(moved_models)} models to correct transformers directory")
    else:
        logger.info("✅ All transformers models are already in correct locations")
    
    downloaded_models = []
    
    # Download GGUF model
    logger.info("\n1. Downloading GGUF model...")
    gguf_path = download_gguf_model()
    if gguf_path:
        downloaded_models.append({
            "name": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "path": gguf_path,
            "type": "llama-gguf",
            "source": "local",
            "family": "tinyllama",
            "capabilities": ["text-generation", "chat"],
            "size": "~700MB",
            "context_length": 2048
        })
    
    # Download primary transformers model
    logger.info("\n2. Downloading primary transformers model...")
    transformers_path = download_transformers_model()
    if transformers_path:
        downloaded_models.append({
            "name": "sentence-transformers/all-MiniLM-L6-v2",
            "path": transformers_path,
            "type": "transformers",
            "source": "local",
            "family": "sentence-transformers",
            "capabilities": ["embeddings", "semantic-search"],
            "size": "~90MB",
            "context_length": 512
        })
    
    # Download additional transformers models
    logger.info("\n3. Downloading additional transformers models...")
    additional_paths = download_additional_transformers_models()
    for path in additional_paths:
        model_name = Path(path).name
        downloaded_models.append({
            "name": model_name,
            "path": path,
            "type": "transformers",
            "source": "local",
            "family": "transformers",
            "capabilities": ["text-generation", "classification"],
            "size": "varies",
            "context_length": 1024
        })
    
    # Ask user about Stable Diffusion
    logger.info("\n4. Stable Diffusion download...")
    download_sd = input("Download Stable Diffusion model? (large download ~4GB) [y/N]: ").lower().strip()
    
    if download_sd in ['y', 'yes']:
        sd_path = download_stable_diffusion()
        if sd_path:
            downloaded_models.append({
                "name": "stable-diffusion-v1-5",
                "path": sd_path,
                "type": "diffusion",
                "source": "local",
                "family": "stable-diffusion",
                "capabilities": ["text-to-image", "image-generation"],
                "size": "~4GB",
                "resolution": "512x512"
            })
    else:
        logger.info("⏭️ Skipping Stable Diffusion download")
    
    # Update registry
    if downloaded_models:
        update_model_registry_with_downloads(downloaded_models)
    
    # Summary
    logger.info(f"\n✅ Download completed! Downloaded {len(downloaded_models)} models:")
    for model in downloaded_models:
        logger.info(f"  • {model['name']} ({model.get('size', 'unknown size')})")
    
    logger.info(f"\n📁 All transformers models are located in: ./models/transformers/")
    logger.info(f"📁 GGUF models are located in: ./models/llama-cpp/")
    logger.info(f"📁 Stable Diffusion models are located in: ./models/stable-diffusion/")
    
    logger.info("\n📋 Next steps:")
    logger.info("1. Restart your backend server")
    logger.info("2. Check the model library in your UI")
    logger.info("3. Test the models in your chat interface")
    logger.info("4. Verify all models are in their correct directories")

if __name__ == "__main__":
    main()