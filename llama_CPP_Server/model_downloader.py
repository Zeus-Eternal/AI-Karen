#!/usr/bin/env python3
"""
Automatic model downloader for llama.cpp server

This script provides a user-friendly interface for downloading
popular GGUF models compatible with llama.cpp.
"""

import os
import sys
import json
import shutil
import logging
import platform
import hashlib
import requests
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Add _server directory to Python path
server_path = Path(__file__).parent / "_server"
sys.path.insert(0, str(server_path))

# Import configuration manager
ConfigManager = None
CONFIG_MANAGER_AVAILABLE = False
try:
    from _server.config_manager import ConfigManager as _ConfigManager
    ConfigManager = _ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """Downloads GGUF models from popular sources"""
    
    # Popular model repositories
    MODEL_REPOSITORIES = {
        "TheBloke": {
            "url": "https://huggingface.co/TheBloke",
            "description": "Popular quantized models by TheBloke"
        },
        "MaziyarPanahi": {
            "url": "https://huggingface.co/MaziyarPanahi",
            "description": "High-quality quantized models"
        },
        "QuantFactory": {
            "url": "https://huggingface.co/QuantFactory",
            "description": "Quantized models for various use cases"
        }
    }
    
    # Popular models with their download URLs and descriptions
    POPULAR_MODELS = {
        "Llama-2-7B-Chat-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
                    "size": "4.08 GB",
                    "description": "Good balance between quality and size"
                },
                "Q5_K_M": {
                    "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q5_K_M.gguf",
                    "size": "4.65 GB",
                    "description": "Higher quality, slightly larger"
                }
            }
        },
        "Llama-2-13B-Chat-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf",
                    "size": "7.87 GB",
                    "description": "Good balance between quality and size"
                },
                "Q5_K_M": {
                    "url": "https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF/resolve/main/llama-2-13b-chat.Q5_K_M.gguf",
                    "size": "8.94 GB",
                    "description": "Higher quality, slightly larger"
                }
            }
        },
        "Mistral-7B-Instruct-v0.2-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                    "size": "4.31 GB",
                    "description": "Good balance between quality and size"
                },
                "Q5_K_M": {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf",
                    "size": "4.94 GB",
                    "description": "Higher quality, slightly larger"
                }
            }
        },
        "Mixtral-8x7B-Instruct-v0.1-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
                    "size": "26.7 GB",
                    "description": "Good balance between quality and size"
                }
            }
        },
        "Phi-2-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
                    "size": "1.64 GB",
                    "description": "Small but capable model"
                }
            }
        },
        "CodeLlama-7B-Instruct-GGUF": {
            "repo": "TheBloke",
            "files": {
                "Q4_K_M": {
                    "url": "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
                    "size": "4.09 GB",
                    "description": "Good balance between quality and size"
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize the model downloader"""
        self.config_manager = None
        self.model_dir = None
        
        # Try to load configuration
        if CONFIG_MANAGER_AVAILABLE and ConfigManager:
            try:
                self.config_manager = ConfigManager()
                self.model_dir = Path(self.config_manager.get("models.directory"))
            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}")
        
        # Fallback to default model directory
        if not self.model_dir:
            self.model_dir = Path.cwd() / "models" / "llama-cpp"
        
        # Ensure model directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Model directory: {self.model_dir}")
    
    def _show_header(self) -> None:
        """Display the downloader header"""
        print("=" * 60)
        print("    Llama.cpp Model Downloader")
        print("=" * 60)
        print()
        print("This tool helps you download popular GGUF models")
        print("for use with the llama.cpp server.")
        print()
    
    def _clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    def _get_input(self, prompt: str, default: Any = None, options: Optional[List[str]] = None) -> str:
        """Get user input with validation"""
        if default is not None:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        while True:
            user_input = input(prompt).strip()
            
            if not user_input and default is not None:
                return str(default)
            
            if options and user_input not in options:
                print(f"Invalid option. Please choose from: {', '.join(options)}")
                continue
            
            return user_input
    
    def _get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user"""
        default_str = "Y/n" if default else "y/N"
        user_input = self._get_input(prompt, default_str).lower()
        return user_input in ('y', 'yes', 'true', '1')
    
    def _download_with_progress(self, url: str, file_path: Path, description: Optional[str] = None) -> bool:
        """Download a file with progress bar"""
        if description:
            print(f"Downloading {description}...")
        else:
            print(f"Downloading {Path(url).name}...")
        
        try:
            # Create request with User-Agent header
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Open URL
            with urlopen(req) as response:
                # Get file size
                file_size = int(response.info().get('Content-Length', 0))
                
                # Open file for writing
                with open(file_path, 'wb') as f:
                    downloaded = 0
                    block_size = 1024 * 1024  # 1MB
                    
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Calculate progress
                        if file_size > 0:
                            percent = int(downloaded / file_size * 100)
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = file_size / (1024 * 1024)
                            
                            # Print progress
                            print(f"\rProgress: {percent}% [{mb_downloaded:.1f}/{mb_total:.1f} MB]", end="")
                
                print()  # New line after progress
                
                # Verify file size
                if file_size > 0 and downloaded != file_size:
                    logger.warning(f"Downloaded file size ({downloaded}) does not match expected size ({file_size})")
                    return False
                
                return True
                
        except (URLError, HTTPError, Exception) as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def _verify_download(self, file_path: Path, expected_size: Optional[str] = None) -> bool:
        """Verify the downloaded file"""
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
        
        if expected_size:
            # Convert expected size string (e.g., "4.08 GB") to bytes
            size_parts = expected_size.split()
            size_value = float(size_parts[0])
            size_unit = size_parts[1].upper()
            
            if size_unit == "GB":
                expected_bytes = size_value * 1024 * 1024 * 1024
            elif size_unit == "MB":
                expected_bytes = size_value * 1024 * 1024
            else:
                expected_bytes = size_value
            
            # Get actual file size
            actual_bytes = file_path.stat().st_size
            
            # Allow 5% tolerance
            tolerance = expected_bytes * 0.05
            if abs(actual_bytes - expected_bytes) > tolerance:
                logger.warning(f"File size verification failed. Expected: {expected_bytes}, Actual: {actual_bytes}")
                return False
        
        return True
    
    def list_models(self) -> None:
        """List available models"""
        print("Available Models:")
        print("-" * 40)
        
        for i, (model_name, model_info) in enumerate(self.POPULAR_MODELS.items(), 1):
            print(f"{i}. {model_name}")
            print(f"   Repository: {model_info['repo']}")
            print(f"   Variants: {', '.join(model_info['files'].keys())}")
            print()
    
    def download_model(self) -> bool:
        """Download a selected model"""
        self._clear_screen()
        self._show_header()
        
        # List available models
        self.list_models()
        
        # Get user selection
        model_names = list(self.POPULAR_MODELS.keys())
        model_indices = [str(i) for i in range(1, len(model_names) + 1)]
        
        selection = self._get_input("Select a model to download", None, model_indices)
        model_index = int(selection) - 1
        model_name = model_names[model_index]
        
        # Get model info
        model_info = self.POPULAR_MODELS[model_name]
        
        # List available variants
        print(f"\nAvailable variants for {model_name}:")
        print("-" * 40)
        
        for i, (variant_name, variant_info) in enumerate(model_info['files'].items(), 1):
            print(f"{i}. {variant_name}")
            print(f"   Size: {variant_info['size']}")
            print(f"   Description: {variant_info['description']}")
            print()
        
        # Get variant selection
        variant_names = list(model_info['files'].keys())
        variant_indices = [str(i) for i in range(1, len(variant_names) + 1)]
        
        variant_selection = self._get_input("Select a variant", None, variant_indices)
        variant_index = int(variant_selection) - 1
        variant_name = variant_names[variant_index]
        
        # Get variant info
        variant_info = model_info['files'][variant_name]
        
        # Confirm download
        print(f"\nYou are about to download:")
        print(f"Model: {model_name}")
        print(f"Variant: {variant_name}")
        print(f"Size: {variant_info['size']}")
        print(f"Description: {variant_info['description']}")
        print(f"Destination: {self.model_dir}")
        print()
        
        if not self._get_yes_no("Continue with download?", True):
            print("Download cancelled.")
            return False
        
        # Create filename
        file_name = f"{model_name.lower().replace('-gguf', '')}-{variant_name.lower()}.gguf"
        file_path = self.model_dir / file_name
        
        # Check if file already exists
        if file_path.exists():
            print(f"File already exists: {file_path}")
            if not self._get_yes_no("Overwrite existing file?", False):
                print("Download cancelled.")
                return False
        
        # Download file
        success = self._download_with_progress(
            variant_info['url'], 
            file_path, 
            f"{model_name} ({variant_name})"
        )
        
        if success:
            # Verify download
            if self._verify_download(file_path, variant_info['size']):
                print(f"\nDownload completed successfully!")
                print(f"Model saved to: {file_path}")
                
                # Update configuration if possible
                if self.config_manager:
                    if self._get_yes_no("Set as default model?", True):
                        self.config_manager.set("models.default_model", str(file_path))
                        print("Model set as default.")
                
                return True
            else:
                print("\nDownload verification failed!")
                return False
        else:
            print("\nDownload failed!")
            return False
    
    def download_custom_model(self) -> bool:
        """Download a custom model from a URL"""
        self._clear_screen()
        self._show_header()
        
        print("Download Custom Model")
        print("-" * 40)
        
        # Get URL
        url = self._get_input("Enter model URL")
        if not url:
            print("Invalid URL.")
            return False
        
        # Validate URL
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                print("Invalid URL format.")
                return False
        except Exception:
            print("Invalid URL format.")
            return False
        
        # Get filename
        file_name = Path(parsed_url.path).name
        if not file_name:
            print("Could not determine filename from URL.")
            return False
        
        # Get custom filename if desired
        custom_name = self._get_input("Enter custom filename (leave empty to use original)", file_name)
        if custom_name:
            file_name = custom_name
        
        # Ensure it ends with .gguf
        if not file_name.endswith('.gguf'):
            file_name += '.gguf'
        
        # Create file path
        file_path = self.model_dir / file_name
        
        # Check if file already exists
        if file_path.exists():
            print(f"File already exists: {file_path}")
            if not self._get_yes_no("Overwrite existing file?", False):
                print("Download cancelled.")
                return False
        
        # Confirm download
        print(f"\nYou are about to download:")
        print(f"URL: {url}")
        print(f"Filename: {file_name}")
        print(f"Destination: {self.model_dir}")
        print()
        
        if not self._get_yes_no("Continue with download?", True):
            print("Download cancelled.")
            return False
        
        # Download file
        success = self._download_with_progress(url, file_path)
        
        if success:
            print(f"\nDownload completed successfully!")
            print(f"Model saved to: {file_path}")
            
            # Update configuration if possible
            if self.config_manager:
                if self._get_yes_no("Set as default model?", True):
                    self.config_manager.set("models.default_model", str(file_path))
                    print("Model set as default.")
            
            return True
        else:
            print("\nDownload failed!")
            return False
    
    def list_downloaded_models(self) -> None:
        """List already downloaded models"""
        self._clear_screen()
        self._show_header()
        
        print("Downloaded Models:")
        print("-" * 40)
        
        # Find all .gguf files in model directory
        model_files = list(self.model_dir.glob("*.gguf"))
        
        if not model_files:
            print("No models found in the model directory.")
            return
        
        for i, model_file in enumerate(model_files, 1):
            size_mb = model_file.stat().st_size / (1024 * 1024)
            size_gb = size_mb / 1024
            
            if size_gb >= 1:
                size_str = f"{size_gb:.2f} GB"
            else:
                size_str = f"{size_mb:.2f} MB"
            
            print(f"{i}. {model_file.name}")
            print(f"   Size: {size_str}")
            print(f"   Path: {model_file}")
            print()
        
        input("Press Enter to continue...")
    
    def run(self) -> bool:
        """Run the model downloader"""
        self._clear_screen()
        self._show_header()
        
        # Main menu loop
        while True:
            print("Main Menu:")
            print("1. List Available Models")
            print("2. Download a Model")
            print("3. Download Custom Model")
            print("4. List Downloaded Models")
            print("5. Exit")
            print()
            
            choice = self._get_input("Select an option", None, ["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self._clear_screen()
                self._show_header()
                self.list_models()
                input("\nPress Enter to continue...")
            elif choice == "2":
                self.download_model()
                input("\nPress Enter to continue...")
            elif choice == "3":
                self.download_custom_model()
                input("\nPress Enter to continue...")
            elif choice == "4":
                self.list_downloaded_models()
            elif choice == "5":
                return True
            
            self._clear_screen()
            self._show_header()


def main():
    """Main entry point"""
    downloader = ModelDownloader()
    downloader.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())