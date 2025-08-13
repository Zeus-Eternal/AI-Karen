"""
System initialization module for AI Karen Engine.
Ensures all necessary files, folders, models, and dependencies are properly set up on first run.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class SystemInitializer:
    """
    Handles system initialization and setup on first run.
    Ensures all necessary components are available and properly configured.
    """
    
    def __init__(self):
        self.logger = logger
        self.base_dir = Path.cwd()
        # Use local models directory instead of /models to avoid permission issues
        self.models_dir = Path(os.getenv("KARI_MODEL_DIR", "models"))
        self.data_dir = Path("data")
        self.config_dir = Path("config")
        
        # Default models to download/setup (only if not already present)
        self.default_models = {
            "llama-cpp": [
                {
                    "name": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                    "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                    "size_mb": 669,
                    "description": "Small efficient model for basic tasks"
                }
            ],
            "transformers": [
                "gpt2",  # Will be downloaded via transformers library if not present
                # "distilbert-base-uncased" - already available in models/
            ]
        }
        
        # Required directories
        self.required_dirs = [
            self.models_dir,
            self.models_dir / "llama-cpp",
            self.models_dir / "transformers", 
            self.models_dir / "groq",
            self.data_dir,
            self.data_dir / "attachments",
            self.data_dir / "bootstrap",
            self.data_dir / "migrations",
            self.config_dir,
            Path("logs"),
            Path("extensions"),
            Path("plugins"),
        ]
        
        # Required config files
        self.required_configs = {
            "config.json": self._get_default_config,
            "model_registry.json": self._get_default_model_registry,
            "config/llm_profiles.yml": self._get_default_llm_profiles,
            "config/memory.yml": self._get_default_memory_config,
            "config/security_config.yml": self._get_default_security_config,
        }
    
    async def initialize_system(self, force_reinstall: bool = False) -> Dict[str, bool]:
        """
        Initialize the entire system on first run.
        
        Args:
            force_reinstall: Force reinstallation of all components
            
        Returns:
            Dict with initialization results for each component
        """
        results = {}
        
        self.logger.info("Starting system initialization...")
        
        # 1. Create required directories
        results["directories"] = await self._setup_directories()
        
        # 2. Setup configuration files
        results["configs"] = await self._setup_config_files(force_reinstall)
        
        # 3. Install required Python packages
        results["packages"] = await self._install_required_packages()
        
        # 4. Download and setup models
        results["models"] = await self._setup_models(force_reinstall)
        
        # 5. Initialize databases
        results["databases"] = await self._initialize_databases()
        
        # 6. Setup CopilotKit if configured
        results["copilotkit"] = await self._setup_copilotkit()
        
        # 7. Validate system health
        results["validation"] = await self._validate_system_health()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            self.logger.info("✅ System initialization completed successfully!")
        else:
            self.logger.warning(f"⚠️ System initialization completed with issues: {success_count}/{total_count} components successful")
        
        return results
    
    async def _setup_directories(self) -> bool:
        """Create all required directories."""
        try:
            for directory in self.required_dirs:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"✅ Created directory: {directory}")
            
            # Set proper permissions for models directory
            if self.models_dir.exists():
                os.chmod(self.models_dir, 0o755)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    async def _setup_config_files(self, force_reinstall: bool = False) -> bool:
        """Setup all required configuration files."""
        try:
            for config_path, config_generator in self.required_configs.items():
                file_path = Path(config_path)
                
                if file_path.exists() and not force_reinstall:
                    self.logger.info(f"✅ Config file already exists: {config_path}")
                    continue
                
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Generate and write config
                config_content = config_generator()
                
                if config_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(config_content, f, indent=2)
                else:
                    with open(file_path, 'w') as f:
                        f.write(config_content)
                
                self.logger.info(f"✅ Created config file: {config_path}")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to setup config files: {e}")
            return False
    
    async def _install_required_packages(self) -> bool:
        """Install required Python packages."""
        required_packages = [
            "transformers>=4.21.0",
            "torch>=1.12.0",
            "sentence-transformers>=2.2.0",
            "spacy>=3.4.0",
            "huggingface-hub>=0.10.0",
        ]
        
        optional_packages = [
            "copilotkit",  # Optional CopilotKit integration
        ]
        
        try:
            # Install required packages
            for package in required_packages:
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        self.logger.info(f"✅ Installed package: {package}")
                    else:
                        self.logger.warning(f"⚠️ Failed to install {package}: {result.stderr}")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"⚠️ Timeout installing {package}")
            
            # Install optional packages (don't fail if they can't be installed)
            for package in optional_packages:
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], capture_output=True, text=True, timeout=180)
                    
                    if result.returncode == 0:
                        self.logger.info(f"✅ Installed optional package: {package}")
                    else:
                        self.logger.info(f"ℹ️ Optional package {package} not installed (this is OK)")
                except subprocess.TimeoutExpired:
                    self.logger.info(f"ℹ️ Timeout installing optional package {package} (this is OK)")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to install packages: {e}")
            return False
    
    async def _setup_models(self, force_reinstall: bool = False) -> bool:
        """Download and setup required models."""
        try:
            # Setup transformers models
            await self._setup_transformers_models(force_reinstall)
            
            # Setup llama-cpp models
            await self._setup_llama_cpp_models(force_reinstall)
            
            # Download spaCy model
            await self._setup_spacy_models()
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to setup models: {e}")
            return False
    
    async def _setup_transformers_models(self, force_reinstall: bool = False) -> None:
        """Setup transformers models."""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            # Check if distilbert-base-uncased already exists
            existing_distilbert = self.models_dir / "distilbert-base-uncased"
            if existing_distilbert.exists():
                self.logger.info("✅ distilbert-base-uncased already available in models directory")
            
            for model_name in self.default_models["transformers"]:
                # Check if model already exists locally
                cache_dir = self.models_dir / "transformers" / model_name
                if cache_dir.exists() and not force_reinstall:
                    self.logger.info(f"✅ Transformers model already exists: {model_name}")
                    continue
                
                try:
                    self.logger.info(f"📥 Downloading transformers model: {model_name}")
                    
                    # Download tokenizer and model
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModel.from_pretrained(model_name)
                    
                    # Save to local cache
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    
                    tokenizer.save_pretrained(cache_dir)
                    model.save_pretrained(cache_dir)
                    
                    self.logger.info(f"✅ Setup transformers model: {model_name}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to setup transformers model {model_name}: {e}")
                    
        except ImportError:
            self.logger.warning("⚠️ Transformers library not available - skipping transformers models")
    
    async def _setup_llama_cpp_models(self, force_reinstall: bool = False) -> None:
        """Download and setup llama-cpp models."""
        for model_info in self.default_models["llama-cpp"]:
            model_path = self.models_dir / "llama-cpp" / model_info["name"]
            
            if model_path.exists() and not force_reinstall:
                self.logger.info(f"✅ Model already exists: {model_info['name']}")
                continue
            
            try:
                self.logger.info(f"📥 Downloading model: {model_info['name']} ({model_info['size_mb']}MB)")
                
                # Download with progress
                await self._download_file_with_progress(model_info["url"], model_path)
                
                self.logger.info(f"✅ Downloaded model: {model_info['name']}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to download model {model_info['name']}: {e}")
    
    async def _setup_spacy_models(self) -> None:
        """Download spaCy models."""
        try:
            # Download English model
            result = subprocess.run([
                sys.executable, "-m", "spacy", "download", "en_core_web_sm"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("✅ Downloaded spaCy English model")
            else:
                self.logger.warning(f"⚠️ Failed to download spaCy model: {result.stderr}")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to setup spaCy models: {e}")
    
    async def _download_file_with_progress(self, url: str, destination: Path) -> None:
        """Download a file with progress logging."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                if block_num % 100 == 0:  # Log every 100 blocks to avoid spam
                    self.logger.info(f"📥 Download progress: {percent}%")
        
        try:
            urllib.request.urlretrieve(url, destination, reporthook=progress_hook)
        except urllib.error.URLError as e:
            raise Exception(f"Failed to download from {url}: {e}")
    
    async def _initialize_databases(self) -> bool:
        """Initialize required databases."""
        try:
            # Create database files if they don't exist
            db_files = [
                "auth.db",
                "auth_sessions.db", 
                "data/kari_automation.db"
            ]
            
            for db_file in db_files:
                db_path = Path(db_file)
                if not db_path.exists():
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    db_path.touch()
                    self.logger.info(f"✅ Created database: {db_file}")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize databases: {e}")
            return False
    
    async def _setup_copilotkit(self) -> bool:
        """Setup CopilotKit if available and configured."""
        try:
            # Check if CopilotKit is available
            try:
                import copilotkit
                self.logger.info("✅ CopilotKit library is available")
                
                # Check for API key configuration
                api_key = os.getenv("COPILOTKIT_API_KEY")
                if api_key:
                    self.logger.info("✅ CopilotKit API key is configured")
                else:
                    self.logger.info("ℹ️ CopilotKit API key not configured - using fallback mode")
                
                return True
                
            except ImportError:
                self.logger.info("ℹ️ CopilotKit library not installed - using fallback mode")
                return True  # This is OK - fallback mode works
                
        except Exception as e:
            self.logger.warning(f"⚠️ CopilotKit setup issue: {e}")
            return True  # Don't fail initialization for optional component
    
    async def _validate_system_health(self) -> bool:
        """Validate that the system is properly initialized."""
        try:
            health_checks = []
            
            # Check directories exist
            for directory in self.required_dirs:
                health_checks.append(directory.exists())
            
            # Check models directory has content or is properly set up
            models_exist = (
                len(list(self.models_dir.glob("**/*.gguf"))) > 0 or
                len(list(self.models_dir.glob("**/*.bin"))) > 0 or
                (self.models_dir / "transformers").exists()
            )
            health_checks.append(models_exist)
            
            # Check config files exist
            for config_path in self.required_configs.keys():
                health_checks.append(Path(config_path).exists())
            
            success_rate = sum(health_checks) / len(health_checks)
            
            if success_rate >= 0.8:  # 80% success rate
                self.logger.info(f"✅ System health validation passed ({success_rate:.1%})")
                return True
            else:
                self.logger.warning(f"⚠️ System health validation concerns ({success_rate:.1%})")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ System health validation failed: {e}")
            return False
    
    # Configuration generators
    def _get_default_config(self) -> Dict:
        """Generate default config.json."""
        return {
            "app_name": "AI Karen Engine",
            "version": "0.4.0",
            "environment": "development",
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "models": {
                "default_provider": "transformers",
                "model_dir": str(self.models_dir),
                "cache_enabled": True
            },
            "features": {
                "extensions_enabled": True,
                "plugins_enabled": True,
                "memory_system_enabled": True,
                "copilotkit_enabled": False
            }
        }
    
    def _get_default_model_registry(self) -> Dict:
        """Generate default model registry."""
        return {
            "providers": {
                "llama-cpp": {
                    "enabled": True,
                    "models_dir": str(self.models_dir / "llama-cpp"),
                    "supported_formats": [".gguf", ".bin"]
                },
                "transformers": {
                    "enabled": True,
                    "models_dir": str(self.models_dir / "transformers"),
                    "cache_dir": str(self.models_dir / "transformers")
                },
                "copilotkit": {
                    "enabled": False,
                    "api_key": None,
                    "base_url": "https://api.copilotkit.ai"
                }
            },
            "default_models": {
                "chat": "gpt2",
                "completion": "gpt2", 
                "embedding": "distilbert-base-uncased"
            }
        }
    
    def _get_default_llm_profiles(self) -> str:
        """Generate default LLM profiles YAML."""
        return """
profiles:
  default:
    provider: transformers
    model: gpt2
    temperature: 0.7
    max_tokens: 150
    
  creative:
    provider: transformers
    model: gpt2
    temperature: 0.9
    max_tokens: 200
    
  precise:
    provider: transformers
    model: distilbert-base-uncased
    temperature: 0.3
    max_tokens: 100
"""
    
    def _get_default_memory_config(self) -> str:
        """Generate default memory configuration YAML."""
        return """
memory:
  enabled: true
  provider: local
  
  storage:
    type: sqlite
    path: data/memory.db
    
  embedding:
    provider: transformers
    model: distilbert-base-uncased
    dimension: 768
    
  retrieval:
    top_k: 10
    similarity_threshold: 0.7
"""
    
    def _get_default_security_config(self) -> str:
        """Generate default security configuration YAML."""
        return """
security:
  authentication:
    enabled: true
    session_timeout: 3600
    
  authorization:
    rbac_enabled: true
    default_role: user
    
  encryption:
    algorithm: AES-256-GCM
    key_rotation_days: 90
    
  audit:
    enabled: true
    log_level: INFO
"""


# Convenience function for easy initialization
async def initialize_system(force_reinstall: bool = False) -> Dict[str, bool]:
    """
    Initialize the AI Karen Engine system.
    
    Args:
        force_reinstall: Force reinstallation of all components
        
    Returns:
        Dict with initialization results
    """
    initializer = SystemInitializer()
    return await initializer.initialize_system(force_reinstall)


# Auto-initialization on import (can be disabled with environment variable)
if os.getenv("KARI_SKIP_AUTO_INIT", "false").lower() != "true":
    def _auto_initialize():
        """Auto-initialize system if needed."""
        try:
            # Quick check if system needs initialization
            models_dir = Path(os.getenv("KARI_MODEL_DIR", "models"))
            config_file = Path("config.json")
            
            needs_init = not models_dir.exists() or not config_file.exists()
            
            if needs_init:
                logger.info("🚀 Auto-initializing AI Karen Engine system...")
                # Try to run initialization if event loop is available
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule for later execution
                        asyncio.create_task(initialize_system())
                    else:
                        # Run immediately if no loop is running
                        asyncio.run(initialize_system())
                except RuntimeError:
                    # No event loop available, skip auto-init
                    logger.debug("No event loop available for auto-initialization")
            
        except Exception as e:
            logger.debug(f"Auto-initialization check failed: {e}")
    
    # Schedule auto-initialization
    try:
        _auto_initialize()
    except Exception:
        pass  # Don't fail imports if auto-init has issues