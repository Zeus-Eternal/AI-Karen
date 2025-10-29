#!/usr/bin/env python3
"""
Fix LLM Intelligence Issues

This script addresses the problem of unintelligent LLM responses by:
1. Upgrading from TinyLlama to better models
2. Downloading additional capable models
3. Configuring proper model parameters
4. Testing the improvements
"""

import json
import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_current_model():
    """Check what model is currently configured"""
    config_path = Path("config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    current_model = config.get('llm', {}).get('model', 'unknown')
    logger.info(f"Current model: {current_model}")
    
    if 'tinyllama' in current_model.lower():
        logger.warning("🚨 TinyLlama detected - this explains poor responses!")
        return False, current_model
    else:
        logger.info("✅ Using a better model than TinyLlama")
        return True, current_model

def download_better_models():
    """Download additional capable models"""
    logger.info("📥 Downloading better models for intelligent responses...")
    
    models_to_download = [
        {
            "name": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "size": "~2GB",
            "description": "Meta's Llama 3.2 3B - excellent for reasoning"
        },
        {
            "name": "Qwen2.5-3B-Instruct-Q4_K_M.gguf", 
            "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            "size": "~2GB",
            "description": "Alibaba's Qwen 2.5 3B - great for coding and reasoning"
        }
    ]
    
    models_dir = Path("./models/llama-cpp")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    
    for model in models_to_download:
        model_path = models_dir / model["name"]
        
        if model_path.exists():
            logger.info(f"✅ {model['name']} already exists")
            downloaded.append(model["name"])
            continue
        
        # Ask user if they want to download this model
        response = input(f"\nDownload {model['name']} ({model['size']})?\n{model['description']}\n[y/N]: ").lower().strip()
        
        if response in ['y', 'yes']:
            try:
                logger.info(f"📥 Downloading {model['name']}...")
                subprocess.run([
                    "wget", "-O", str(model_path), model["url"]
                ], check=True)
                logger.info(f"✅ Downloaded {model['name']}")
                downloaded.append(model["name"])
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to download {model['name']}: {e}")
            except FileNotFoundError:
                logger.error("❌ wget not found. Please install wget or download manually")
        else:
            logger.info(f"⏭️ Skipping {model['name']}")
    
    return downloaded

def update_model_configuration(model_name):
    """Update configuration to use a better model"""
    config_path = Path("config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update LLM configuration
    config['llm']['model'] = model_name
    config['llm']['temperature'] = 0.7  # Good balance for intelligence
    config['llm']['max_tokens'] = 4096  # Longer responses
    config['llm_model'] = model_name
    
    # Update user profile
    if 'user_profiles' in config and 'profiles' in config['user_profiles']:
        for profile in config['user_profiles']['profiles']:
            if 'assignments' in profile:
                # Update summarization to use better model
                if 'summarization' in profile['assignments']:
                    profile['assignments']['summarization']['model'] = model_name
    
    # Save updated configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Updated configuration to use {model_name}")

def recommend_model_settings():
    """Recommend optimal model settings for intelligence"""
    recommendations = {
        "temperature": {
            "current": 0.7,
            "reasoning": "Good balance between creativity and consistency"
        },
        "max_tokens": {
            "current": 4096,
            "reasoning": "Allows for detailed, comprehensive responses"
        },
        "top_p": {
            "recommended": 0.9,
            "reasoning": "Nucleus sampling for better quality"
        },
        "repeat_penalty": {
            "recommended": 1.1,
            "reasoning": "Prevents repetitive responses"
        }
    }
    
    logger.info("🎛️ Recommended settings for intelligent responses:")
    for param, info in recommendations.items():
        if "current" in info:
            logger.info(f"   {param}: {info['current']} - {info['reasoning']}")
        else:
            logger.info(f"   {param}: {info['recommended']} - {info['reasoning']}")

def create_model_comparison():
    """Create a comparison of model capabilities"""
    comparison = """
📊 Model Intelligence Comparison:

TinyLlama 1.1B (POOR - what you were using):
- Parameters: 1.1 billion
- Capabilities: Basic text completion only
- Intelligence: Very limited, often incoherent
- Use case: Testing only, not production

Phi-3-mini 3.8B (GOOD - current upgrade):
- Parameters: 3.8 billion  
- Capabilities: Reasoning, coding, conversation
- Intelligence: Much better, coherent responses
- Use case: General purpose, good for most tasks

Llama 3.2 3B (EXCELLENT):
- Parameters: 3 billion (but better architecture)
- Capabilities: Advanced reasoning, coding, math
- Intelligence: Very high quality responses
- Use case: Professional applications

Qwen 2.5 3B (EXCELLENT):
- Parameters: 3 billion
- Capabilities: Coding, reasoning, multilingual
- Intelligence: State-of-the-art for size
- Use case: Development and technical tasks

The key difference: TinyLlama was designed for basic testing,
while the others are designed for intelligent conversation.
"""
    
    print(comparison)

def main():
    """Main function to fix LLM intelligence"""
    logger.info("🧠 Fixing LLM Intelligence Issues")
    logger.info("=" * 50)
    
    # Check current model
    is_good, current_model = check_current_model()
    
    if not is_good:
        logger.info("🔧 TinyLlama detected - upgrading to Phi-3...")
        update_model_configuration("Phi-3-mini-4k-instruct-q4.gguf")
        logger.info("✅ Upgraded to Phi-3 - responses should be much better!")
    
    # Show model comparison
    create_model_comparison()
    
    # Offer to download even better models
    download_more = input("\nDownload additional high-quality models? [y/N]: ").lower().strip()
    
    if download_more in ['y', 'yes']:
        downloaded = download_better_models()
        
        if downloaded:
            # Ask which model to use as primary
            logger.info(f"\nDownloaded models: {downloaded}")
            choice = input(f"Set one as primary model? Enter model name or 'no': ").strip()
            
            if choice != 'no' and choice in downloaded:
                update_model_configuration(choice)
                logger.info(f"✅ Set {choice} as primary model")
    
    # Show recommendations
    recommend_model_settings()
    
    # Final instructions
    logger.info("\n🚀 Next Steps:")
    logger.info("1. Restart your backend: ./restart_with_better_model.sh")
    logger.info("2. Test with: 'Explain object-oriented programming'")
    logger.info("3. You should get detailed, intelligent responses!")
    logger.info("\n✨ Your AI should now be much more intelligent!")

if __name__ == "__main__":
    main()