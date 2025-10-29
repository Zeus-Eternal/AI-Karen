#!/usr/bin/env python3
"""
Setup cloud providers for better AI responses.
"""

import os
import json
from pathlib import Path

def setup_openai():
    """Setup OpenAI provider."""
    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        return False
    
    # Update .env file
    env_path = Path(".env")
    env_content = env_path.read_text() if env_path.exists() else ""
    
    # Remove existing OPENAI_API_KEY line
    lines = [line for line in env_content.split('\n') if not line.startswith('OPENAI_API_KEY=')]
    lines.append(f'OPENAI_API_KEY={api_key}')
    
    env_path.write_text('\n'.join(lines))
    
    # Update providers config
    providers_path = Path("config/providers.json")
    if providers_path.exists():
        with open(providers_path, 'r') as f:
            config = json.load(f)
    else:
        config = {"providers": {"cloud": {}}}
    
    config["providers"]["cloud"]["openai"] = {
        "enabled": True,
        "api_key": "${OPENAI_API_KEY}",
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo"
        ]
    }
    
    providers_path.parent.mkdir(exist_ok=True)
    with open(providers_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ OpenAI configured successfully!")
    return True

def setup_huggingface():
    """Setup Hugging Face provider."""
    api_key = input("Enter your Hugging Face API key (or press Enter to skip): ").strip()
    
    if not api_key:
        return False
    
    # Update .env file
    env_path = Path(".env")
    env_content = env_path.read_text() if env_path.exists() else ""
    
    # Remove existing HUGGINGFACE_API_KEY line
    lines = [line for line in env_content.split('\n') if not line.startswith('HUGGINGFACE_API_KEY=')]
    lines.append(f'HUGGINGFACE_API_KEY={api_key}')
    
    env_path.write_text('\n'.join(lines))
    
    # Update providers config
    providers_path = Path("config/providers.json")
    if providers_path.exists():
        with open(providers_path, 'r') as f:
            config = json.load(f)
    else:
        config = {"providers": {"cloud": {}}}
    
    config["providers"]["cloud"]["huggingface"] = {
        "enabled": True,
        "api_key": "${HUGGINGFACE_API_KEY}",
        "base_url": "https://api-inference.huggingface.co",
        "models": [
            "microsoft/Phi-3-mini-4k-instruct",
            "meta-llama/Llama-3.2-3B-Instruct",
            "Qwen/Qwen2.5-3B-Instruct"
        ]
    }
    
    providers_path.parent.mkdir(exist_ok=True)
    with open(providers_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Hugging Face configured successfully!")
    return True

def create_training_ui_config():
    """Create configuration for training UI in settings."""
    
    settings_dir = Path(".kiro/settings")
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    training_config = {
        "training_ui": {
            "enabled": True,
            "models": {
                "current_model": "auto-detect",
                "available_models": [],
                "training_datasets": "./data/training",
                "fine_tuning": {
                    "enabled": False,
                    "learning_rate": 0.0001,
                    "batch_size": 4,
                    "epochs": 3
                }
            },
            "model_evaluation": {
                "test_prompts": [
                    "Explain how promises work in JavaScript",
                    "What are the benefits of using TypeScript?",
                    "How do I optimize database queries?"
                ],
                "quality_metrics": ["coherence", "accuracy", "helpfulness"]
            }
        }
    }
    
    with open(settings_dir / "training.json", 'w') as f:
        json.dump(training_config, f, indent=2)
    
    print("✅ Training UI configuration created!")

def main():
    print("=== AI-Karen Cloud Provider Setup ===")
    print("This will configure better models for coherent responses.\n")
    
    print("Cloud providers offer much better models than local TinyLlama:")
    print("- OpenAI: GPT-4o-mini, GPT-4o (best quality)")
    print("- Hugging Face: Free tier with good models")
    print()
    
    configured_any = False
    
    print("1. Setting up OpenAI (recommended for best quality):")
    if setup_openai():
        configured_any = True
    
    print("\n2. Setting up Hugging Face (free tier available):")
    if setup_huggingface():
        configured_any = True
    
    print("\n3. Creating training UI configuration:")
    create_training_ui_config()
    
    if configured_any:
        print("\n✅ Cloud providers configured!")
        print("\nNext steps:")
        print("1. Restart your AI-Karen backend")
        print("2. The system will automatically use better models")
        print("3. Responses should be much more coherent")
        
        # Update the restart script
        with open("restart_with_better_model.sh", 'w') as f:
            f.write("""#!/bin/bash
echo "Restarting AI-Karen with cloud providers..."
pkill -f "python.*start"
sleep 2
python start.py
""")
        os.chmod("restart_with_better_model.sh", 0o755)
        print("4. Run: ./restart_with_better_model.sh")
        
    else:
        print("\n⚠️  No cloud providers configured.")
        print("You can still run the local model setup: python setup_better_model.py")
    
    print("\n📚 API Key Information:")
    print("- OpenAI: https://platform.openai.com/api-keys")
    print("- Hugging Face: https://huggingface.co/settings/tokens")

if __name__ == "__main__":
    main()