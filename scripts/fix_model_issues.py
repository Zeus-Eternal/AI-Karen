#!/usr/bin/env python3
"""
Fix Model Issues Script

This script diagnoses and fixes common model-related issues that cause
poor AI responses, including:
1. Missing or corrupted model files
2. Incorrect model configuration
3. Prompt template issues
4. Model loading failures
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelIssuesFixer:
    def __init__(self):
        self.models_dir = Path("models")
        self.llama_cpp_dir = self.models_dir / "llama-cpp"
        self.issues_found = []
        self.fixes_applied = []
    
    def diagnose_issues(self) -> Dict[str, Any]:
        """Diagnose all model-related issues."""
        logger.info("🔍 Diagnosing model issues...")
        
        issues = {
            "missing_models": self._check_missing_models(),
            "corrupted_models": self._check_corrupted_models(),
            "configuration_issues": self._check_configuration_issues(),
            "prompt_template_issues": self._check_prompt_templates(),
            "model_loading_issues": self._check_model_loading(),
            "inference_issues": self._check_inference_setup()
        }
        
        return issues
    
    def _check_missing_models(self) -> List[Dict[str, Any]]:
        """Check for missing model files."""
        missing = []
        
        # Check for TinyLlama GGUF model
        tinyllama_path = self.llama_cpp_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
        if not tinyllama_path.exists():
            missing.append({
                "model": "TinyLlama 1.1B Chat Q4_K_M",
                "path": str(tinyllama_path),
                "url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                "size_mb": 669,
                "description": "Primary local LLM for chat responses"
            })
        
        # Check for alternative TinyLlama models
        alt_tinyllama = self.llama_cpp_dir / "TinyLlama" / "TinyLlama-1.1B-Chat-v1.0"
        if alt_tinyllama.exists() and not any(alt_tinyllama.glob("*.gguf")):
            missing.append({
                "model": "TinyLlama Alternative Format",
                "path": str(alt_tinyllama),
                "issue": "Directory exists but no GGUF files found",
                "description": "Alternative TinyLlama installation incomplete"
            })
        
        return missing
    
    def _check_corrupted_models(self) -> List[Dict[str, Any]]:
        """Check for corrupted model files."""
        corrupted = []
        
        # Check GGUF files for proper headers
        for gguf_file in self.llama_cpp_dir.rglob("*.gguf"):
            try:
                with open(gguf_file, "rb") as f:
                    header = f.read(4)
                    if header != b"GGUF":
                        corrupted.append({
                            "model": gguf_file.name,
                            "path": str(gguf_file),
                            "issue": "Invalid GGUF header",
                            "expected": "GGUF",
                            "found": header.hex()
                        })
            except Exception as e:
                corrupted.append({
                    "model": gguf_file.name,
                    "path": str(gguf_file),
                    "issue": f"Cannot read file: {e}"
                })
        
        return corrupted
    
    def _check_configuration_issues(self) -> List[Dict[str, Any]]:
        """Check model configuration issues."""
        config_issues = []
        
        # Check model registry
        registry_path = self.models_dir / "llm_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                
                # Check for TinyLlama in registry
                tinyllama_found = False
                for model in registry.get("models", []):
                    if "tinyllama" in model.get("name", "").lower():
                        tinyllama_found = True
                        # Check if path exists
                        model_path = Path(model.get("path", ""))
                        if not model_path.exists():
                            config_issues.append({
                                "issue": "Registry points to non-existent model",
                                "model": model.get("name"),
                                "path": str(model_path)
                            })
                
                if not tinyllama_found:
                    config_issues.append({
                        "issue": "TinyLlama not found in model registry",
                        "registry_path": str(registry_path)
                    })
                    
            except Exception as e:
                config_issues.append({
                    "issue": f"Cannot read model registry: {e}",
                    "registry_path": str(registry_path)
                })
        else:
            config_issues.append({
                "issue": "Model registry file missing",
                "registry_path": str(registry_path)
            })
        
        return config_issues
    
    def _check_prompt_templates(self) -> List[Dict[str, Any]]:
        """Check prompt template configuration."""
        template_issues = []
        
        # Check if proper chat templates are configured
        try:
            # Look for prompt template configurations
            config_files = list(self.models_dir.rglob("*config*.json"))
            
            chat_template_found = False
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    if "chat_template" in config or "prompt_template" in config:
                        chat_template_found = True
                        break
                except:
                    continue
            
            if not chat_template_found:
                template_issues.append({
                    "issue": "No chat templates found in model configurations",
                    "impact": "Models may produce poor conversational responses",
                    "suggestion": "Add proper chat templates for better responses"
                })
                
        except Exception as e:
            template_issues.append({
                "issue": f"Error checking prompt templates: {e}"
            })
        
        return template_issues
    
    def _check_model_loading(self) -> List[Dict[str, Any]]:
        """Check model loading configuration."""
        loading_issues = []
        
        # Check if llama-cpp-python is available
        try:
            import llama_cpp
            loading_issues.append({
                "status": "OK",
                "component": "llama-cpp-python",
                "version": getattr(llama_cpp, "__version__", "unknown")
            })
        except ImportError:
            loading_issues.append({
                "issue": "llama-cpp-python not installed",
                "component": "llama-cpp-python",
                "impact": "Cannot load GGUF models",
                "fix": "pip install llama-cpp-python"
            })
        
        # Check if transformers is available for other models
        try:
            import transformers
            loading_issues.append({
                "status": "OK",
                "component": "transformers",
                "version": transformers.__version__
            })
        except ImportError:
            loading_issues.append({
                "issue": "transformers not installed",
                "component": "transformers",
                "impact": "Cannot load HuggingFace models",
                "fix": "pip install transformers"
            })
        
        return loading_issues
    
    def _check_inference_setup(self) -> List[Dict[str, Any]]:
        """Check inference configuration."""
        inference_issues = []
        
        # Check if inference services are properly configured
        try:
            # Check for inference runtime configurations
            runtime_files = [
                "src/ai_karen_engine/inference/llamacpp_runtime.py",
                "src/ai_karen_engine/services/nlp_service_manager.py"
            ]
            
            for runtime_file in runtime_files:
                if not Path(runtime_file).exists():
                    inference_issues.append({
                        "issue": f"Missing inference runtime: {runtime_file}",
                        "impact": "Model inference may not work properly"
                    })
        
        except Exception as e:
            inference_issues.append({
                "issue": f"Error checking inference setup: {e}"
            })
        
        return inference_issues
    
    def fix_issues(self, issues: Dict[str, Any]) -> Dict[str, Any]:
        """Fix identified issues."""
        logger.info("🔧 Fixing model issues...")
        
        fixes = {
            "models_downloaded": self._fix_missing_models(issues["missing_models"]),
            "configurations_fixed": self._fix_configuration_issues(issues["configuration_issues"]),
            "templates_added": self._fix_prompt_templates(issues["prompt_template_issues"]),
            "dependencies_installed": self._fix_dependencies(issues["model_loading_issues"])
        }
        
        return fixes
    
    def _fix_missing_models(self, missing_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download missing models."""
        downloaded = []
        
        for model in missing_models:
            if "url" in model:
                logger.info(f"📥 Downloading {model['model']}...")
                
                try:
                    # Create directory
                    model_path = Path(model["path"])
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Download with progress
                    response = requests.get(model["url"], stream=True)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(model_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Progress indicator
                                if total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    print(f"\r   Progress: {progress:.1f}%", end="", flush=True)
                    
                    print()  # New line after progress
                    
                    # Verify download
                    if model_path.exists() and model_path.stat().st_size > 1000000:  # At least 1MB
                        downloaded.append({
                            "model": model["model"],
                            "path": str(model_path),
                            "size_mb": model_path.stat().st_size / (1024 * 1024),
                            "status": "success"
                        })
                        logger.info(f"✅ Successfully downloaded {model['model']}")
                    else:
                        downloaded.append({
                            "model": model["model"],
                            "status": "failed",
                            "error": "Download incomplete or file too small"
                        })
                        
                except Exception as e:
                    downloaded.append({
                        "model": model["model"],
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"❌ Failed to download {model['model']}: {e}")
        
        return downloaded
    
    def _fix_configuration_issues(self, config_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix configuration issues."""
        fixed = []
        
        for issue in config_issues:
            if "Registry points to non-existent model" in issue.get("issue", ""):
                # Update registry to point to correct model path
                try:
                    registry_path = self.models_dir / "llm_registry.json"
                    if registry_path.exists():
                        with open(registry_path, 'r') as f:
                            registry = json.load(f)
                        
                        # Find and fix the model entry
                        for model in registry.get("models", []):
                            if model.get("name") == issue.get("model"):
                                # Update path to correct location
                                new_path = self.llama_cpp_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
                                if new_path.exists():
                                    model["path"] = str(new_path)
                                    fixed.append({
                                        "issue": "Updated model path in registry",
                                        "model": model.get("name"),
                                        "new_path": str(new_path)
                                    })
                        
                        # Save updated registry
                        with open(registry_path, 'w') as f:
                            json.dump(registry, f, indent=2)
                            
                except Exception as e:
                    fixed.append({
                        "issue": "Failed to fix registry",
                        "error": str(e)
                    })
            
            elif "TinyLlama not found in model registry" in issue.get("issue", ""):
                # Add TinyLlama to registry
                try:
                    registry_path = self.models_dir / "llm_registry.json"
                    tinyllama_path = self.llama_cpp_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
                    
                    if tinyllama_path.exists():
                        if registry_path.exists():
                            with open(registry_path, 'r') as f:
                                registry = json.load(f)
                        else:
                            registry = {"models": [], "repositories": []}
                        
                        # Add TinyLlama entry
                        tinyllama_entry = {
                            "id": "tinyllama-1.1b-chat-q4",
                            "name": "TinyLlama 1.1B Chat Q4_K_M",
                            "path": str(tinyllama_path),
                            "type": "gguf",
                            "source": "downloaded",
                            "provider": "llama-cpp",
                            "capabilities": ["text-generation", "chat", "local-inference"],
                            "metadata": {
                                "parameters": "1.1B",
                                "quantization": "Q4_K_M",
                                "context_length": 2048,
                                "description": "A compact 1.1B parameter language model optimized for chat applications"
                            }
                        }
                        
                        registry["models"].append(tinyllama_entry)
                        
                        # Save registry
                        with open(registry_path, 'w') as f:
                            json.dump(registry, f, indent=2)
                        
                        fixed.append({
                            "issue": "Added TinyLlama to model registry",
                            "model": "TinyLlama 1.1B Chat Q4_K_M",
                            "path": str(tinyllama_path)
                        })
                        
                except Exception as e:
                    fixed.append({
                        "issue": "Failed to add TinyLlama to registry",
                        "error": str(e)
                    })
        
        return fixed
    
    def _fix_prompt_templates(self, template_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix prompt template issues."""
        fixed = []
        
        # Create a proper chat template configuration
        try:
            template_config = {
                "chat_template": {
                    "system_prefix": "<|system|>\\n",
                    "system_suffix": "<|end|>\\n",
                    "user_prefix": "<|user|>\\n",
                    "user_suffix": "<|end|>\\n",
                    "assistant_prefix": "<|assistant|>\\n",
                    "assistant_suffix": "<|end|>\\n",
                    "default_system_message": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."
                },
                "generation_config": {
                    "max_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "stop_sequences": ["<|end|>", "<|user|>", "<|system|>"]
                }
            }
            
            # Save template configuration
            template_path = self.models_dir / "configs" / "chat_template.json"
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(template_path, 'w') as f:
                json.dump(template_config, f, indent=2)
            
            fixed.append({
                "issue": "Created chat template configuration",
                "path": str(template_path),
                "description": "Added proper chat templates for better conversational responses"
            })
            
        except Exception as e:
            fixed.append({
                "issue": "Failed to create chat template",
                "error": str(e)
            })
        
        return fixed
    
    def _fix_dependencies(self, loading_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix dependency issues."""
        fixed = []
        
        for issue in loading_issues:
            if issue.get("issue") and "not installed" in issue.get("issue", ""):
                component = issue.get("component")
                fix_command = issue.get("fix")
                
                fixed.append({
                    "issue": f"Missing dependency: {component}",
                    "fix_command": fix_command,
                    "status": "manual_fix_required",
                    "description": f"Run: {fix_command}"
                })
        
        return fixed
    
    def create_test_script(self) -> str:
        """Create a test script to verify model functionality."""
        test_script = '''#!/usr/bin/env python3
"""
Test Model Functionality

This script tests if the models are working correctly after fixes.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_model_functionality():
    """Test model functionality."""
    print("🧪 Testing model functionality...")
    
    try:
        # Test 1: Check if models are loaded
        from ai_karen_engine.llm_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        models = orchestrator.registry.list_models()
        print(f"   Found {len(models)} registered models:")
        for model in models:
            print(f"     - {model['model_id']}: {model['status']}")
        
        # Test 2: Try generating a response
        if models:
            print("\\n   Testing response generation...")
            try:
                response = orchestrator.route("Hello, how are you?", skill="conversation")
                print(f"   Response: {response[:100]}...")
                
                if len(response) > 10 and not response.startswith("I"):
                    print("   ✅ Model generating proper responses!")
                else:
                    print("   ⚠️ Model responses may still need improvement")
                    
            except Exception as e:
                print(f"   ❌ Response generation failed: {e}")
        else:
            print("   ❌ No models available for testing")
    
    except Exception as e:
        print(f"   ❌ Model testing failed: {e}")
    
    # Test 3: Check chat orchestrator
    try:
        from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
        from ai_karen_engine.chat.memory_processor import MemoryProcessor
        
        print("\\n   Testing chat orchestrator...")
        
        # Create minimal orchestrator for testing
        orchestrator = ChatOrchestrator(memory_processor=None)
        
        request = ChatRequest(
            message="What is Python?",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        response = await orchestrator.process_message(request)
        
        if response and hasattr(response, 'response') and response.response:
            print(f"   Chat response: {response.response[:100]}...")
            print("   ✅ Chat orchestrator working!")
        else:
            print("   ⚠️ Chat orchestrator returned empty response")
            
    except Exception as e:
        print(f"   ❌ Chat orchestrator test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_model_functionality())
'''
        
        test_path = Path("test_model_functionality.py")
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        return str(test_path)

def main():
    """Main function to diagnose and fix model issues."""
    print("🔍 AI Karen Model Issues Diagnostic & Fix Tool")
    print("=" * 50)
    
    fixer = ModelIssuesFixer()
    
    # Diagnose issues
    issues = fixer.diagnose_issues()
    
    # Print diagnosis results
    print("\\n📊 Diagnosis Results:")
    for category, category_issues in issues.items():
        if category_issues:
            print(f"\\n{category.replace('_', ' ').title()}:")
            for issue in category_issues:
                if isinstance(issue, dict):
                    if "issue" in issue:
                        print(f"  ❌ {issue['issue']}")
                        if "impact" in issue:
                            print(f"     Impact: {issue['impact']}")
                        if "fix" in issue:
                            print(f"     Fix: {issue['fix']}")
                    elif "status" in issue and issue["status"] == "OK":
                        print(f"  ✅ {issue['component']}: OK")
                    else:
                        print(f"  ⚠️ {issue}")
    
    # Ask user if they want to apply fixes
    print("\\n" + "=" * 50)
    apply_fixes = input("Apply automatic fixes? (y/N): ").lower().strip()
    
    if apply_fixes == 'y':
        fixes = fixer.fix_issues(issues)
        
        print("\\n🔧 Fix Results:")
        for category, category_fixes in fixes.items():
            if category_fixes:
                print(f"\\n{category.replace('_', ' ').title()}:")
                for fix in category_fixes:
                    if isinstance(fix, dict):
                        if fix.get("status") == "success":
                            print(f"  ✅ {fix.get('model', 'Fix')}: {fix.get('status')}")
                        elif fix.get("status") == "failed":
                            print(f"  ❌ {fix.get('model', 'Fix')}: {fix.get('error')}")
                        elif fix.get("status") == "manual_fix_required":
                            print(f"  ⚠️ {fix.get('issue')}: {fix.get('description')}")
                        else:
                            print(f"  ✅ {fix.get('issue', 'Applied fix')}")
        
        # Create test script
        test_script_path = fixer.create_test_script()
        print(f"\\n📝 Created test script: {test_script_path}")
        print("   Run this script to verify fixes: python test_model_functionality.py")
    
    print("\\n" + "=" * 50)
    print("🎯 Recommendations:")
    print("1. Ensure all required dependencies are installed")
    print("2. Download missing model files (especially TinyLlama)")
    print("3. Update model registry with correct paths")
    print("4. Test model functionality after fixes")
    print("5. Check server logs for any remaining issues")

if __name__ == "__main__":
    main()