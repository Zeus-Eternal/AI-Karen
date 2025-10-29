#!/usr/bin/env python3
"""
Run download script with correct .env_karen environment and environment variables
"""

import os
import sys
import subprocess
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ .env file not found")
        return
    
    print("📋 Loading environment variables from .env...")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    print("✅ Environment variables loaded")

def setup_karen_env():
    """Setup .env_karen virtual environment"""
    venv_path = Path(".env_karen")
    if not venv_path.exists():
        print("❌ .env_karen virtual environment not found!")
        return False
    
    # Update PATH to use .env_karen
    venv_bin = venv_path / "bin"
    if venv_bin.exists():
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{venv_bin}:{current_path}"
        os.environ["VIRTUAL_ENV"] = str(venv_path.absolute())
        print(f"✅ Using virtual environment: {venv_path}")
        return True
    else:
        print(f"❌ Virtual environment bin directory not found: {venv_bin}")
        return False

def main():
    """Main function"""
    print("🚀 Setting up .env_karen environment and running download script...")
    
    # Setup virtual environment
    if not setup_karen_env():
        sys.exit(1)
    
    # Load environment variables
    load_env_file()
    
    # Find Python executable
    python_exe = Path(".env_karen/bin/python3")
    if not python_exe.exists():
        python_exe = Path(".env_karen/bin/python")
        if not python_exe.exists():
            print("❌ Python executable not found in .env_karen")
            sys.exit(1)
    
    print(f"🐍 Using Python: {python_exe}")
    
    # Run the download script
    print("📥 Running download_essential_models.py...")
    try:
        result = subprocess.run([str(python_exe), "download_essential_models.py"], 
                              env=os.environ, 
                              check=True)
        print("✅ Download script completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Download script failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"❌ Error running download script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()