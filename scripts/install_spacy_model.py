#!/usr/bin/env python3
"""
Quick script to install the required spaCy English model.
Run this to fix spaCy model errors.
"""

import subprocess
import sys
import os
from pathlib import Path


def print_status(message: str, status: str = "INFO"):
    """Print a status message with visual indicator."""
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{icons.get(status, 'ℹ️')} {message}")


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print_status(f"Running: {description}")
    print(f"   Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        print_status(f"Success: {description}", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Failed: {description}", "ERROR")
        print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print_status(f"Command not found: {command[0]}", "ERROR")
        return False


def check_virtual_env():
    """Check if we're in a virtual environment."""
    venv_active = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if venv_active:
        print_status("Virtual environment detected", "SUCCESS")
        return True
    else:
        print_status("No virtual environment detected", "WARNING")
        return False


def install_spacy_model():
    """Install the spaCy English model."""
    print("=" * 60)
    print("🚀 spaCy Model Installation Script")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path(".env").exists():
        print_status("No .env file found. Are you in the project root?", "WARNING")
    
    # Check virtual environment
    venv_active = check_virtual_env()
    
    if not venv_active:
        print()
        print_status("Recommendation: Activate your virtual environment first:", "INFO")
        print("   $ source .env_kari/bin/activate")
        print("   $ python scripts/install_spacy_model.py")
        print()
        
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            print_status("Installation cancelled", "INFO")
            return False
    
    print()
    print_status("Installing spaCy English model...", "INFO")
    
    # Try to install spaCy first if not available
    try:
        import spacy
        print_status("spaCy is already installed", "SUCCESS")
    except ImportError:
        print_status("spaCy not found, installing...", "WARNING")
        if not run_command([sys.executable, "-m", "pip", "install", "spacy"], "Install spaCy"):
            return False
    
    # Install the English model
    success = run_command(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
        "Download en_core_web_sm model"
    )
    
    if success:
        print()
        print_status("Testing model installation...", "INFO")
        
        # Test the model
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("This is a test sentence.")
            print_status("Model test successful!", "SUCCESS")
            print(f"   Processed: '{doc.text}'")
            print(f"   Tokens: {[token.text for token in doc]}")
            
        except Exception as e:
            print_status(f"Model test failed: {e}", "ERROR")
            return False
        
        print()
        print("=" * 60)
        print_status("spaCy model installation completed successfully!", "SUCCESS")
        print("=" * 60)
        print()
        print("You can now restart your application:")
        print("   $ python start.py")
        print()
        
        return True
    
    else:
        print()
        print_status("Installation failed", "ERROR")
        print()
        print("Manual installation steps:")
        print("1. Activate your virtual environment:")
        print("   $ source .env_kari/bin/activate")
        print("2. Install spaCy:")
        print("   $ pip install spacy")
        print("3. Download the model:")
        print("   $ python -m spacy download en_core_web_sm")
        print()
        
        return False


if __name__ == "__main__":
    try:
        success = install_spacy_model()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print_status("Installation cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print()
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)