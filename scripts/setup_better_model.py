#!/usr/bin/env python3
"""
Setup script to configure a better model for coherent responses.
"""

import os
import json
import requests
from pathlib import Path

def download_better_model():
    """Download a better model for coherent responses."""
    
    models_dir = Path("./models/llama-cpp")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Better model options (in order of preference)
    model_options = [
        {
            "name": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "size": "~2GB",
            "description": "Llama 3.2 3B - Much better reasoning than TinyLlama"
        },
        {
            "name": "Phi-3.5-mini-instruct-Q4_K_M.gguf", 
            "url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "size": "~2.3GB",
            "description": "Phi-3.5 Mini - Excellent for reasoning and explanations"
        },
        {
            "name": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf", 
            "size": "~2GB",
            "description": "Qwen2.5 3B - Great for detailed responses"
        }
    ]
    
    print("Available better models:")
    for i, model in enumerate(model_options, 1):
        print(f"{i}. {model['name']} ({model['size']}) - {model['description']}")
    
    choice = input("\nSelect model to download (1-3, or 'skip' to configure existing): ").strip()
    
    if choice.lower() == 'skip':
        return configure_existing_model()
    
    try:
        model_idx = int(choice) - 1
        if 0 <= model_idx < len(model_options):
            selected_model = model_options[model_idx]
            model_path = models_dir / selected_model["name"]
            
            if model_path.exists():
                print(f"Model {selected_model['name']} already exists!")
                return str(model_path)
            
            print(f"Downloading {selected_model['name']}...")
            print(f"Size: {selected_model['size']} - This may take a while...")
            
            response = requests.get(selected_model["url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}%", end='', flush=True)
            
            print(f"\nDownloaded {selected_model['name']} successfully!")
            return str(model_path)
            
    except (ValueError, IndexError):
        print("Invalid choice. Using existing model configuration.")
        return configure_existing_model()
    except Exception as e:
        print(f"Download failed: {e}")
        return configure_existing_model()

def configure_existing_model():
    """Configure existing Phi-3 model if available."""
    models_dir = Path("./models/llama-cpp")
    
    # Look for existing better models
    existing_models = []
    for model_file in models_dir.glob("*.gguf"):
        if "phi-3" in model_file.name.lower() or "llama" in model_file.name.lower():
            if "tinyllama" not in model_file.name.lower():
                existing_models.append(model_file)
    
    if existing_models:
        print("Found existing models:")
        for i, model in enumerate(existing_models, 1):
            print(f"{i}. {model.name}")
        
        choice = input(f"Select model (1-{len(existing_models)}): ").strip()
        try:
            model_idx = int(choice) - 1
            if 0 <= model_idx < len(existing_models):
                return str(existing_models[model_idx])
        except (ValueError, IndexError):
            pass
    
    # Default to Phi-3 if it exists
    phi3_path = models_dir / "Phi-3-mini-4k-instruct-q4.gguf"
    if phi3_path.exists():
        print(f"Using existing Phi-3 model: {phi3_path}")
        return str(phi3_path)
    
    print("No suitable models found. Please download a better model.")
    return None

def update_model_config(model_path):
    """Update the model configuration to use the better model."""
    
    # Update model registry
    registry_path = Path("model_registry.json")
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)
    else:
        registry = []
    
    model_name = Path(model_path).name
    
    # Add new model to registry if not exists
    model_entry = {
        "name": model_name,
        "path": model_path,
        "type": "llama-gguf",
        "source": "local"
    }
    
    # Remove existing entry with same name
    registry = [m for m in registry if m.get("name") != model_name]
    registry.append(model_entry)
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"Updated model registry with {model_name}")
    
    # Update TinyLlama config to use better model
    config_dir = Path("models/configs")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    tinyllama_config = {
        "model_name": model_name,
        "model_path": model_path,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "enable_fallback": True,
        "cache_enabled": True
    }
    
    with open(config_dir / "tinyllama.json", 'w') as f:
        json.dump(tinyllama_config, f, indent=2)
    
    print(f"Updated TinyLlama service to use {model_name}")

def main():
    print("=== AI-Karen Model Upgrade Setup ===")
    print("Current issue: TinyLlama (1.1B) is too small for coherent responses")
    print("Solution: Configure a larger, more capable model\n")
    
    model_path = download_better_model()
    
    if model_path:
        update_model_config(model_path)
        print("\n✅ Model configuration updated!")
        print("\nNext steps:")
        print("1. Restart your AI-Karen backend")
        print("2. Test with a simple question")
        print("3. The responses should now be much more coherent")
        
        # Create restart script
        with open("restart_with_better_model.sh", 'w') as f:
            f.write("""#!/bin/bash
echo "Restarting AI-Karen with better model..."
pkill -f "python.*start"
sleep 2
python start.py
""")
        os.chmod("restart_with_better_model.sh", 0o755)
        print("4. Run: ./restart_with_better_model.sh")
        
    else:
        print("\n❌ Could not configure a better model.")
        print("Please manually download a better model or configure cloud providers.")

if __name__ == "__main__":
    main()