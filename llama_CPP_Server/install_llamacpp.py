#!/usr/bin/env python3
"""
Installation wizard for llama.cpp server

This script helps users set up the llama.cpp server by:
1. Checking system requirements
2. Detecting if llama.cpp is already installed
3. Installing llama.cpp if needed
4. Setting up configuration
5. Testing the installation
"""

import os
import sys
import subprocess
import json
import platform
import logging
import shutil
import venv
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add _server directory to Python path
server_path = Path(__file__).parent / "_server"
sys.path.insert(0, str(server_path))

# Import configuration manager
try:
    from _server.config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LlamaCppInstaller:
    """Installation wizard for llama.cpp server"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        
        # Initialize configuration manager
        if CONFIG_MANAGER_AVAILABLE:
            self.config_manager = ConfigManager()
            self.config_path = self.config_manager.config_path
            self.installation_path = self.config_manager.get_installation_path()
            self.models_path = self.config_manager.get_model_directory()
            self.venv_path = self.config_manager.get_venv_path()
            self.use_venv = self.config_manager.use_virtual_environment()
        else:
            # Fallback to hardcoded paths
            self.config_manager = None
            self.config_path = Path.cwd() / "config.json"
            self.installation_path = Path.cwd() / "_llama_cpp"
            self.models_path = Path.cwd() / "models" / "llama-cpp"
            self.venv_path = Path.cwd() / "venv"
            self.use_venv = False
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for compatibility checks"""
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "pip_available": self._check_pip_available()
        }
        return info
    
    def _check_pip_available(self) -> bool:
        """Check if pip is available"""
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"],
                          check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _create_virtual_environment(self) -> bool:
        """Create a virtual environment for the installation"""
        logger.info(f"Creating virtual environment at {self.venv_path}")
        
        try:
            # Create virtual environment
            venv.create(self.venv_path, with_pip=True)
            
            # Get paths to the virtual environment Python and pip
            if platform.system() == "Windows":
                self.venv_python = str(self.venv_path / "Scripts" / "python.exe")
                self.venv_pip = str(self.venv_path / "Scripts" / "pip.exe")
            else:
                self.venv_python = str(self.venv_path / "bin" / "python")
                self.venv_pip = str(self.venv_path / "bin" / "pip")
            
            # Make sure the virtual environment Python is executable
            if platform.system() != "Windows":
                os.chmod(self.venv_python, 0o755)
                os.chmod(self.venv_pip, 0o755)
            
            logger.info(f"Virtual environment created successfully")
            self.use_venv = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def _get_pip_executable(self) -> str:
        """Get the pip executable to use"""
        if self.use_venv:
            return self.venv_pip
        elif self._check_pip_available():
            return f"{sys.executable} -m pip"
        else:
            raise RuntimeError("pip is not available and virtual environment creation failed")
    
    def _check_llamacpp_installed(self) -> bool:
        """Check if llama-cpp-python is already installed"""
        try:
            import llama_cpp
            logger.info("llama-cpp-python is already installed")
            return True
        except ImportError:
            logger.info("llama-cpp-python is not installed")
            return False
    
    def _get_recommended_installation_method(self) -> str:
        """Get recommended installation method based on system"""
        system = self.system_info["platform"]
        arch = self.system_info["architecture"]
        
        if system == "Windows":
            return "pip"
        elif system == "Darwin":  # macOS
            if arch == "arm64":
                return "pip-metal"
            else:
                return "pip"
        elif system == "Linux":
            return "pip"
        else:
            return "pip"
    
    def _install_llamacpp(self, method: str = "auto") -> bool:
        """Install llama-cpp-python using the specified method"""
        if method == "auto":
            if self.config_manager:
                method = self.config_manager.get_install_method()
                if method == "auto":
                    method = self._get_recommended_installation_method()
            else:
                method = self._get_recommended_installation_method()
        
        logger.info(f"Installing llama-cpp-python using method: {method}")
        
        try:
            pip_executable = self._get_pip_executable()
            
            if method == "pip":
                # Standard CPU installation
                subprocess.run([
                    pip_executable, "install", "llama-cpp-python"
                ], check=True)
                
            elif method == "pip-metal":
                # macOS Metal GPU acceleration
                subprocess.run([
                    pip_executable, "install",
                    "llama-cpp-python",
                    "--prefer-binary",
                    "--extra-index-url",
                    "https://jllllll.github.io/llama-cpp-python-metal-wheels/AVX2"
                ], check=True)
                
            elif method == "pip-cuda":
                # CUDA GPU acceleration
                cuda_version = None
                if self.config_manager:
                    cuda_version = self.config_manager.get_cuda_version()
                
                if not cuda_version:
                    cuda_version = input("Enter CUDA version (e.g., 11.8, 12.0) or press Enter for default: ").strip()
                
                if cuda_version:
                    index_url = f"https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu{cuda_version}"
                else:
                    index_url = "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118"
                
                subprocess.run([
                    pip_executable, "install",
                    "llama-cpp-python",
                    "--prefer-binary",
                    "--extra-index-url", index_url
                ], check=True)
            
            logger.info("Successfully installed llama-cpp-python")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install llama-cpp-python: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Create necessary directories"""
        if self.config_manager:
            self.config_manager.create_directories()
        else:
            # Fallback to hardcoded directories
            directories = [
                self.installation_path,
                self.models_path,
                self.models_path / "downloads"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
    
    def _create_config(self) -> None:
        """Create configuration file"""
        if self.config_manager:
            # Update configuration with current paths
            self.config_manager.set_model_directory(self.models_path)
            self.config_manager.set_installation_path(self.installation_path)
            self.config_manager.set_venv_path(self.venv_path)
            self.config_manager.set_use_virtual_environment(self.use_venv)
            
            # Save configuration
            self.config_manager.save_config()
            logger.info(f"Created configuration file: {self.config_path}")
        else:
            # Fallback to hardcoded configuration
            config = {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "log_level": "INFO",
                    "cors_allow_origins": ["*"],
                    "rate_limit_per_min": 120,
                    "auth_token": None
                },
                "models": {
                    "directory": str(self.models_path),
                    "default_model": None,
                    "auto_load_default": True,
                    "max_loaded_models": 2,
                    "max_cache_gb": 8
                },
                "performance": {
                    "optimize_for": "balanced",
                    "enable_gpu": True,
                    "num_threads": 4,
                    "batch_size": 128,
                    "context_window": 4096,
                    "low_vram": False
                },
                "backend": {
                    "type": "auto",
                    "local": {
                        "n_ctx": 4096,
                        "n_threads": 4,
                        "n_batch": 512,
                        "use_mmap": True,
                        "use_mlock": False,
                        "embedding": False,
                        "low_mem": False,
                        "verbose": False
                    },
                    "remote": {
                        "url": "http://localhost:8000",
                        "timeout": 30,
                        "auth_token": None
                    }
                },
                "karen": {
                    "integration_enabled": True,
                    "endpoint": "http://localhost:8000",
                    "health_timeout_s": 2
                },
                "observability": {
                    "enable_prometheus": False,
                    "prometheus_port": 9090,
                    "enable_tracing": False
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Created configuration file: {self.config_path}")
    
    def _download_sample_model(self) -> bool:
        """Download a small sample model for testing"""
        logger.info("Would you like to download a sample model for testing?")
        choice = input("Download Phi-3-mini-4k-instruct-q4 (approx 2.2GB)? [y/N]: ").strip().lower()
        
        if choice == 'y':
            logger.info("Model download feature will be implemented in the next version.")
            logger.info("For now, please download models manually from HuggingFace.")
            return False
        else:
            logger.info("Skipping model download.")
            return False
    
    def _test_installation(self) -> bool:
        """Test the installation"""
        logger.info("Testing installation...")
        
        # Add _server directory to Python path
        server_path = Path(__file__).parent / "_server"
        sys.path.insert(0, str(server_path))
        
        try:
            # If we're using a virtual environment, use its Python executable
            if self.use_venv:
                # Run the test in the virtual environment
                test_script = f"""
import sys
sys.path.insert(0, '{str(server_path)}')
import backend
import asyncio

async def test():
    test_model = '{str(self.models_path / "test.gguf")}'
    test_backend = backend.LocalLlamaBackend(
        model_path=test_model,
        threads=2,
        low_vram=False,
        n_ctx=1024
    )
    
    await test_backend.load()
    if test_backend.loaded:
        response = await test_backend.perform_inference(
            "Test prompt",
            {{"temperature": 0.7, "max_tokens": 10}}
        )
        print(f"Test successful. Response: {{response}}")
        await test_backend.unload()
        return True
    else:
        print("Failed to load test backend")
        return False

if not backend.LLAMA_CPP_AVAILABLE:
    print("llama-cpp-python is not available after installation")
    sys.exit(1)

result = asyncio.run(test())
sys.exit(0 if result else 1)
"""
                
                with open("test_installation.py", "w") as f:
                    f.write(test_script)
                
                try:
                    result = subprocess.run([
                        self.venv_python, "test_installation.py"
                    ], capture_output=True, text=True)
                    
                    if result.stdout:
                        logger.info(result.stdout)
                    if result.stderr:
                        logger.error(result.stderr)
                    
                    return result.returncode == 0
                finally:
                    if os.path.exists("test_installation.py"):
                        os.remove("test_installation.py")
            else:
                # Use the current Python environment
                import backend
                
                if not backend.LLAMA_CPP_AVAILABLE:
                    logger.error("llama-cpp-python is not available after installation")
                    return False
                
                # Create a test backend
                test_model = self.models_path / "test.gguf"
                test_backend = backend.LocalLlamaBackend(
                    model_path=test_model,
                    threads=2,
                    low_vram=False,
                    n_ctx=1024
                )
                
                # Test loading and inference (will use stub since model doesn't exist)
                import asyncio
                
                async def test():
                    await test_backend.load()
                    if test_backend.loaded:
                        response = await test_backend.perform_inference(
                            "Test prompt",
                            {"temperature": 0.7, "max_tokens": 10}
                        )
                        logger.info(f"Test successful. Response: {response}")
                        await test_backend.unload()
                        return True
                    else:
                        logger.error("Failed to load test backend")
                        return False
                
                return asyncio.run(test())
            
        except Exception as e:
            logger.error(f"Installation test failed: {e}")
            return False
    
    def run_interactive_install(self) -> bool:
        """Run interactive installation"""
        print("=== Llama.cpp Server Installation Wizard ===")
        print(f"System: {self.system_info['platform']} {self.system_info['architecture']}")
        print(f"Python: {self.system_info['python_version'].split()[0]}")
        print()
        
        # Check if already installed
        if self._check_llamacpp_installed():
            print("✓ llama-cpp-python is already installed")
        else:
            print("✗ llama-cpp-python is not installed")
            
            # Check if pip is available, if not create virtual environment
            if not self._check_pip_available():
                print("✗ pip is not available in the system Python")
                print("Creating a virtual environment for installation...")
                
                if not self._create_virtual_environment():
                    print("Failed to create virtual environment. Installation aborted.")
                    return False
            else:
                # Ask if user wants to use a virtual environment
                use_venv = input("Use a virtual environment for installation? [Y/n]: ").strip().lower()
                if use_venv != 'n':
                    if not self._create_virtual_environment():
                        print("Failed to create virtual environment. Continuing with system Python.")
            
            # Ask to install
            install = input("Install llama-cpp-python? [Y/n]: ").strip().lower()
            if install != 'n':
                method = self._get_recommended_installation_method()
                print(f"Recommended installation method: {method}")
                
                custom_method = input("Use recommended method? [Y/n]: ").strip().lower()
                if custom_method == 'n':
                    print("Available methods:")
                    print("  1. pip (CPU-only)")
                    print("  2. pip-metal (macOS Metal GPU)")
                    print("  3. pip-cuda (NVIDIA CUDA GPU)")
                    
                    choice = input("Select method [1-3]: ").strip()
                    methods = {"1": "pip", "2": "pip-metal", "3": "pip-cuda"}
                    method = methods.get(choice, "pip")
                
                if not self._install_llamacpp(method):
                    print("Installation failed. Please check the error messages above.")
                    return False
            else:
                print("Skipping llama-cpp-python installation")
        
        # Create directories
        print("\nCreating directories...")
        self._create_directories()
        
        # Create configuration
        print("\nCreating configuration...")
        self._create_config()
        
        # Offer to download sample model
        print("\nModel setup...")
        self._download_sample_model()
        
        # Test installation
        print("\nTesting installation...")
        if self._test_installation():
            print("\n✓ Installation completed successfully!")
            print("\nNext steps:")
            print(f"1. Download GGUF models to: {self.models_path}")
            print(f"2. Edit configuration in: {self.config_path}")
            
            if self.use_venv:
                print("3. Activate the virtual environment:")
                if platform.system() == "Windows":
                    print(f"   {self.venv_path}\\Scripts\\activate")
                else:
                    print(f"   source {self.venv_path}/bin/activate")
                print("4. Run the server: python runServer.py")
            else:
                print("3. Run the server: python runServer.py")
            
            return True
        else:
            print("\n✗ Installation test failed")
            print("Please check the error messages above and try again.")
            return False

def main():
    """Main entry point"""
    installer = LlamaCppInstaller()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--non-interactive":
        # Non-interactive mode for automation
        success = installer._check_llamacpp_installed()
        
        if not success:
            # Check if pip is available, if not create virtual environment
            if not installer._check_pip_available():
                print("pip is not available in the system Python")
                print("Creating a virtual environment for installation...")
                
                if not installer._create_virtual_environment():
                    print("Failed to create virtual environment. Installation aborted.")
                    sys.exit(1)
            
            success = installer._install_llamacpp()
        
        if success:
            installer._create_directories()
            installer._create_config()
            success = installer._test_installation()
        
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        success = installer.run_interactive_install()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()