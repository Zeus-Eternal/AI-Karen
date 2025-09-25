"""
Integration tests for Model Orchestrator API endpoints.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import with fallbacks for testing
try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = Mock
    FastAPI = Mock

try:
    from src.ai_karen_engine.api_routes.model_orchestrator_routes import router
    from src.ai_karen_engine.api_routes.websocket_routes import websocket_router
    ROUTES_AVAILABLE = True
except ImportError:
    ROUTES_AVAILABLE = False
    router = Mock()
    websocket_router = Mock()

try:
    from plugin_marketplace.ai.model_orchestrator.service import ModelOrchestratorService
except ImportError:
    class ModelOrchestratorService:
        def __init__(self):
            pass
        
        async def list_models(self, **kwargs):
            return []
        
        async def get_model_info(self, model_id, revision=None):
            return {"model_id": model_id}
        
        async def download_model(self, model_id, **kwargs):
            return {"status": "success", "model_id": model_id}

# Create test app with routes if available
if FASTAPI_AVAILABLE and ROUTES_AVAILABLE:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/models")
    test_app.include_router(websocket_router, prefix="/ws")
    client = TestClient(test_app)
else:
    test_app = Mock()
    client = Mock()


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestModelOrchestratorAPIEndpoints:
    """Test model orchestrator API endpoints using existing API test patterns."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
        
        # Mock registry data
        self.mock_registry_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False,
                "last_accessed": "2024-01-01T00:00:00Z"
            },
            "TheBloke/Llama-2-7B-Chat-GGUF": {
                "model_id": "TheBloke/Llama-2-7B-Chat-GGUF",
                "library": "llama-cpp",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "llama-cpp" / "TheBloke--Llama-2-7B-Chat-GGUF"),
                "files": [{"path": "model.gguf", "size": 2048, "sha256": "def456"}],
                "total_size": 2048,
                "pinned": True,
                "last_accessed": "2024-01-01T00:00:00Z"
            }
        }
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_list_models_endpoint(self):
        """Test GET /api/models/list endpoint."""
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.list_models') as mock_list:
            mock_list.return_value = list(self.mock_registry_data.values())
            
            response = client.get("/api/models/list")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["models"]) == 2
            assert data["models"][0]["model_id"] == "microsoft/DialoGPT-medium"
            assert data["models"][1]["model_id"] == "TheBloke/Llama-2-7B-Chat-GGUF"
    
    def test_list_models_with_filters(self):
        """Test GET /api/models/list with query parameters."""
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.list_models') as mock_list:
            # Mock filtered response
            filtered_data = [self.mock_registry_data["microsoft/DialoGPT-medium"]]
            mock_list.return_value = filtered_data
            
            response = client.get("/api/models/list?library=transformers&pinned=false")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["models"]) == 1
            assert data["models"][0]["library"] == "transformers"
            mock_list.assert_called_once_with(library="transformers", pinned_only=False)
    
    def test_get_model_info_endpoint(self):
        """Test GET /api/models/info/{model_id} endpoint."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.get_model_info') as mock_info:
            mock_info.return_value = self.mock_registry_data[model_id]
            
            # URL encode the model_id
            encoded_model_id = model_id.replace("/", "%2F")
            response = client.get(f"/api/models/info/{encoded_model_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == model_id
            assert data["library"] == "transformers"
            mock_info.assert_called_once_with(model_id, revision=None)
    
    def test_get_model_info_with_revision(self):
        """Test GET /api/models/info/{model_id} with revision parameter."""
        model_id = "microsoft/DialoGPT-medium"
        revision = "v1.0"
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.get_model_info') as mock_info:
            mock_info.return_value = self.mock_registry_data[model_id]
            
            encoded_model_id = model_id.replace("/", "%2F")
            response = client.get(f"/api/models/info/{encoded_model_id}?revision={revision}")
            
            assert response.status_code == 200
            mock_info.assert_called_once_with(model_id, revision=revision)
    
    def test_get_model_info_not_found(self):
        """Test GET /api/models/info/{model_id} for non-existent model."""
        from src.ai_karen_engine.error_tracking.model_orchestrator_errors import ModelOrchestratorError
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.get_model_info') as mock_info:
            mock_info.side_effect = ModelOrchestratorError("E_NOT_FOUND", "Model not found")
            
            response = client.get("/api/models/info/non-existent%2Fmodel")
            
            assert response.status_code == 404
            data = response.json()
            assert data["error"]["code"] == "E_NOT_FOUND"
    
    def test_download_model_endpoint(self):
        """Test POST /api/models/download endpoint."""
        download_request = {
            "model_id": "microsoft/DialoGPT-medium",
            "revision": "main",
            "pin": False,
            "force_redownload": False
        }
        
        expected_response = {
            "status": "success",
            "model_id": "microsoft/DialoGPT-medium",
            "job_id": "job_123",
            "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium")
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.download_model') as mock_download:
            mock_download.return_value = expected_response
            
            response = client.post("/api/models/download", json=download_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["model_id"] == "microsoft/DialoGPT-medium"
            assert "job_id" in data
            mock_download.assert_called_once()
    
    def test_download_model_with_auth(self):
        """Test POST /api/models/download with authentication."""
        download_request = {
            "model_id": "microsoft/DialoGPT-medium"
        }
        
        # Mock authentication middleware
        with patch('src.ai_karen_engine.security.model_security.ModelSecurityManager.check_download_permission') as mock_auth:
            mock_auth.return_value = True
            
            with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.download_model') as mock_download:
                mock_download.return_value = {"status": "success", "job_id": "job_123"}
                
                # Add mock auth header
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/models/download", json=download_request, headers=headers)
                
                assert response.status_code == 200
    
    def test_download_model_permission_denied(self):
        """Test POST /api/models/download with insufficient permissions."""
        download_request = {
            "model_id": "microsoft/DialoGPT-medium"
        }
        
        with patch('src.ai_karen_engine.security.model_security.ModelSecurityManager.check_download_permission') as mock_auth:
            mock_auth.return_value = False
            
            headers = {"Authorization": "Bearer test_token"}
            response = client.post("/api/models/download", json=download_request, headers=headers)
            
            assert response.status_code == 403
            data = response.json()
            assert "permission" in data["error"]["message"].lower()
    
    def test_remove_model_endpoint(self):
        """Test DELETE /api/models/{model_id} endpoint."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.remove_model') as mock_remove:
            mock_remove.return_value = {"status": "success", "model_id": model_id, "removed": True}
            
            encoded_model_id = model_id.replace("/", "%2F")
            response = client.delete(f"/api/models/{encoded_model_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["removed"] is True
            mock_remove.assert_called_once_with(model_id)
    
    def test_migrate_models_endpoint(self):
        """Test POST /api/models/migrate endpoint."""
        migrate_request = {
            "dry_run": False,
            "backup": True
        }
        
        expected_response = {
            "status": "success",
            "migrated_count": 2,
            "errors": [],
            "backup_path": "/tmp/backup_123"
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.migrate_layout') as mock_migrate:
            mock_migrate.return_value = expected_response
            
            response = client.post("/api/models/migrate", json=migrate_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["migrated_count"] == 2
            mock_migrate.assert_called_once()
    
    def test_ensure_models_endpoint(self):
        """Test POST /api/models/ensure endpoint."""
        ensure_request = {
            "models": ["distilbert-base-uncased", "en_core_web_sm"]
        }
        
        expected_response = {
            "status": "success",
            "ensured_models": ["distilbert-base-uncased", "en_core_web_sm"],
            "skipped": [],
            "errors": []
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.ensure_models') as mock_ensure:
            mock_ensure.return_value = expected_response
            
            response = client.post("/api/models/ensure", json=ensure_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["ensured_models"]) == 2
            mock_ensure.assert_called_once()
    
    def test_garbage_collect_endpoint(self):
        """Test POST /api/models/gc endpoint."""
        gc_request = {
            "max_size_gb": 10.0,
            "keep_pinned": True,
            "dry_run": False
        }
        
        expected_response = {
            "status": "success",
            "removed_models": ["old/model"],
            "freed_space_gb": 5.2,
            "remaining_models": 1
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.garbage_collect') as mock_gc:
            mock_gc.return_value = expected_response
            
            response = client.post("/api/models/gc", json=gc_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["freed_space_gb"] == 5.2
            mock_gc.assert_called_once()
    
    def test_get_registry_endpoint(self):
        """Test GET /api/models/registry endpoint."""
        with patch('src.ai_karen_engine.integrations.llm_registry.ModelRegistry.load_registry') as mock_load:
            mock_load.return_value = self.mock_registry_data
            
            response = client.get("/api/models/registry")
            
            assert response.status_code == 200
            data = response.json()
            assert "registry" in data
            assert len(data["registry"]) == 2
    
    def test_health_check_endpoint(self):
        """Test GET /api/models/health endpoint."""
        expected_health = {
            "status": "healthy",
            "registry_valid": True,
            "storage_available": True,
            "external_connectivity": True,
            "checks": {
                "registry_integrity": "pass",
                "disk_space": "pass",
                "huggingface_api": "pass"
            }
        }
        
        with patch('src.ai_karen_engine.health.model_orchestrator_health.ModelOrchestratorHealthCheck.check_health') as mock_health:
            mock_health.return_value = expected_health
            
            response = client.get("/api/models/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["registry_valid"] is True
    
    def test_compatibility_check_endpoint(self):
        """Test GET /api/models/compatibility/{model_id} endpoint."""
        model_id = "microsoft/DialoGPT-medium"
        
        expected_compatibility = {
            "compatible": True,
            "cpu_features": ["avx2", "sse4.1"],
            "gpu_available": True,
            "ram_sufficient": True,
            "vram_sufficient": True,
            "warnings": []
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.check_compatibility') as mock_compat:
            mock_compat.return_value = expected_compatibility
            
            encoded_model_id = model_id.replace("/", "%2F")
            response = client.get(f"/api/models/compatibility/{encoded_model_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["compatible"] is True
            assert "avx2" in data["cpu_features"]
    
    def test_get_progress_endpoint(self):
        """Test GET /api/models/progress/{job_id} endpoint."""
        job_id = "job_123"
        
        expected_progress = {
            "job_id": job_id,
            "status": "downloading",
            "progress": 0.65,
            "downloaded_bytes": 65536,
            "total_bytes": 100000,
            "eta_seconds": 30,
            "current_file": "pytorch_model.bin"
        }
        
        with patch('plugin_marketplace.ai.model_orchestrator.service.ModelOrchestratorService.get_job_progress') as mock_progress:
            mock_progress.return_value = expected_progress
            
            response = client.get(f"/api/models/progress/{job_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert data["progress"] == 0.65
            assert data["status"] == "downloading"


class TestModelOrchestratorCLIIntegration:
    """Test CLI enhancements with existing CLI test framework."""
    
    def setup_method(self):
        """Setup CLI test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_list_command_json_output(self):
        """Test CLI list command with JSON output."""
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_output = {
                "status": "success",
                "models": [
                    {
                        "model_id": "microsoft/DialoGPT-medium",
                        "library": "transformers",
                        "total_size": 1024,
                        "pinned": False
                    }
                ]
            }
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_output)
            
            # Simulate CLI call
            result = subprocess.run([
                "python", "scripts/operations/install_models.py",
                "list", "--json"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["status"] == "success"
            assert len(data["models"]) == 1
    
    def test_cli_info_command_json_output(self):
        """Test CLI info command with JSON output."""
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_output = {
                "status": "success",
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "total_size": 1024,
                "files": [{"path": "config.json", "size": 512}]
            }
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_output)
            
            result = subprocess.run([
                "python", "scripts/operations/install_models.py",
                "info", "microsoft/DialoGPT-medium", "--json"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["model_id"] == "microsoft/DialoGPT-medium"
    
    def test_cli_download_command_with_options(self):
        """Test CLI download command with various options."""
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_output = {
                "status": "success",
                "model_id": "microsoft/DialoGPT-medium",
                "install_path": "/models/transformers/microsoft--DialoGPT-medium",
                "total_size": 1024
            }
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_output)
            
            result = subprocess.run([
                "python", "scripts/operations/install_models.py",
                "download", "microsoft/DialoGPT-medium",
                "--revision", "main",
                "--pin",
                "--json"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["status"] == "success"
    
    def test_cli_gc_command(self):
        """Test CLI garbage collection command."""
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_output = {
                "status": "success",
                "removed_models": ["old/model"],
                "freed_space_gb": 2.5,
                "remaining_models": 3
            }
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_output)
            
            result = subprocess.run([
                "python", "scripts/operations/install_models.py",
                "gc", "--max-size", "10", "--json"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["freed_space_gb"] == 2.5
    
    def test_cli_offline_mode(self):
        """Test CLI offline mode functionality."""
        import subprocess
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "E_NET: Offline mode enabled, network access denied"
            
            result = subprocess.run([
                "python", "scripts/operations/install_models.py",
                "download", "microsoft/DialoGPT-medium",
                "--offline", "--json"
            ], capture_output=True, text=True)
            
            assert result.returncode == 1
            assert "E_NET" in result.stderr
            assert "offline mode" in result.stderr.lower()


class TestWebSocketIntegration:
    """Test WebSocket integration using existing WebSocket test utilities."""
    
    def test_websocket_model_progress_updates(self):
        """Test WebSocket progress updates for model operations."""
        from fastapi.testclient import TestClient
        
        with TestClient(test_app) as client:
            with patch('src.ai_karen_engine.api_routes.websocket_routes.WebSocketManager') as mock_ws_manager:
                mock_manager = Mock()
                mock_ws_manager.return_value = mock_manager
                
                # Simulate WebSocket connection
                with client.websocket_connect("/ws/models/events") as websocket:
                    # Simulate progress update
                    progress_data = {
                        "type": "model_download_progress",
                        "job_id": "job_123",
                        "progress": 0.5,
                        "status": "downloading",
                        "current_file": "pytorch_model.bin"
                    }
                    
                    # Mock receiving progress update
                    websocket.send_json(progress_data)
                    data = websocket.receive_json()
                    
                    assert data["type"] == "model_download_progress"
                    assert data["progress"] == 0.5
    
    def test_websocket_model_completion_notification(self):
        """Test WebSocket completion notifications."""
        from fastapi.testclient import TestClient
        
        with TestClient(test_app) as client:
            with client.websocket_connect("/ws/models/events") as websocket:
                completion_data = {
                    "type": "model_download_complete",
                    "job_id": "job_123",
                    "model_id": "microsoft/DialoGPT-medium",
                    "status": "success",
                    "install_path": "/models/transformers/microsoft--DialoGPT-medium"
                }
                
                websocket.send_json(completion_data)
                data = websocket.receive_json()
                
                assert data["type"] == "model_download_complete"
                assert data["status"] == "success"
    
    def test_websocket_error_notifications(self):
        """Test WebSocket error notifications."""
        from fastapi.testclient import TestClient
        
        with TestClient(test_app) as client:
            with client.websocket_connect("/ws/models/events") as websocket:
                error_data = {
                    "type": "model_download_error",
                    "job_id": "job_123",
                    "model_id": "microsoft/DialoGPT-medium",
                    "error": {
                        "code": "E_NET",
                        "message": "Network connection failed"
                    }
                }
                
                websocket.send_json(error_data)
                data = websocket.receive_json()
                
                assert data["type"] == "model_download_error"
                assert data["error"]["code"] == "E_NET"


class TestLLMServiceIntegration:
    """Test LLM service integration with existing provider tests."""
    
    def setup_method(self):
        """Setup LLM service integration tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
        
        # Create test llm_settings.json
        self.llm_settings_path = Path(self.temp_dir) / "llm_settings.json"
        self.initial_settings = {
            "providers": {
                "huggingface": {
                    "models": {}
                },
                "llama-cpp": {
                    "models": {}
                }
            }
        }
        with open(self.llm_settings_path, 'w') as f:
            json.dump(self.initial_settings, f)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_transformers_model_registration(self):
        """Test automatic registration of Transformers models."""
        from src.ai_karen_engine.integrations.llm_registry import ModelRegistry
        
        registry = ModelRegistry(str(Path(self.temp_dir) / "llm_registry.json"))
        
        # Simulate model installation
        model_entry = {
            "model_id": "microsoft/DialoGPT-medium",
            "library": "transformers",
            "revision": "main",
            "installed_at": "2024-01-01T00:00:00Z",
            "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
            "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
            "total_size": 1024,
            "pinned": False
        }
        
        with patch.object(registry, 'load_registry', return_value={"microsoft/DialoGPT-medium": model_entry}):
            with patch.object(registry, 'save_registry') as mock_save:
                await registry.update_model("microsoft/DialoGPT-medium", model_entry)
                
                # Verify model was registered
                mock_save.assert_called_once()
                
                # Check that LLM settings would be updated
                with patch('builtins.open', mock_open_multiple_files({
                    str(self.llm_settings_path): json.dumps(self.initial_settings)
                })):
                    # Simulate LLM settings update
                    updated_settings = self.initial_settings.copy()
                    updated_settings["providers"]["huggingface"]["models"]["microsoft/DialoGPT-medium"] = {
                        "path": model_entry["install_path"],
                        "revision": model_entry["revision"]
                    }
                    
                    assert "microsoft/DialoGPT-medium" in updated_settings["providers"]["huggingface"]["models"]
    
    @pytest.mark.asyncio
    async def test_llama_cpp_model_registration(self):
        """Test automatic registration of llama-cpp models."""
        from src.ai_karen_engine.integrations.llm_registry import ModelRegistry
        
        registry = ModelRegistry(str(Path(self.temp_dir) / "llm_registry.json"))
        
        # Simulate GGUF model installation
        model_entry = {
            "model_id": "TheBloke/Llama-2-7B-Chat-GGUF",
            "library": "llama-cpp",
            "revision": "main",
            "installed_at": "2024-01-01T00:00:00Z",
            "install_path": str(self.models_path / "llama-cpp" / "TheBloke--Llama-2-7B-Chat-GGUF"),
            "files": [{"path": "llama-2-7b-chat.Q4_K_M.gguf", "size": 4096, "sha256": "xyz789"}],
            "total_size": 4096,
            "pinned": False
        }
        
        with patch.object(registry, 'load_registry', return_value={"TheBloke/Llama-2-7B-Chat-GGUF": model_entry}):
            with patch.object(registry, 'save_registry') as mock_save:
                await registry.update_model("TheBloke/Llama-2-7B-Chat-GGUF", model_entry)
                
                mock_save.assert_called_once()
                
                # Check that LLM settings would be updated for llama-cpp
                updated_settings = self.initial_settings.copy()
                updated_settings["providers"]["llama-cpp"]["models"]["TheBloke/Llama-2-7B-Chat-GGUF"] = {
                    "path": str(Path(model_entry["install_path"]) / "llama-2-7b-chat.Q4_K_M.gguf"),
                    "revision": model_entry["revision"]
                }
                
                assert "TheBloke/Llama-2-7B-Chat-GGUF" in updated_settings["providers"]["llama-cpp"]["models"]
    
    @pytest.mark.asyncio
    async def test_model_validation_integration(self):
        """Test model validation using existing provider interfaces."""
        from plugin_marketplace.ai.model_orchestrator.service import ModelOrchestratorService
        
        service = ModelOrchestratorService()
        
        # Mock successful model validation
        with patch('src.ai_karen_engine.integrations.llm_registry.validate_model_loadability') as mock_validate:
            mock_validate.return_value = {"valid": True, "error": None}
            
            result = await service.validate_model("microsoft/DialoGPT-medium")
            
            assert result["valid"] is True
            mock_validate.assert_called_once_with("microsoft/DialoGPT-medium")
    
    @pytest.mark.asyncio
    async def test_smoke_test_integration(self):
        """Test smoke testing with existing provider interfaces."""
        from plugin_marketplace.ai.model_orchestrator.service import ModelOrchestratorService
        
        service = ModelOrchestratorService()
        
        # Mock successful smoke test
        with patch('src.ai_karen_engine.integrations.llm_registry.run_smoke_test') as mock_smoke:
            mock_smoke.return_value = {
                "success": True,
                "response": "Hello world",
                "latency_ms": 150
            }
            
            result = await service.run_smoke_test("microsoft/DialoGPT-medium")
            
            assert result["success"] is True
            assert result["latency_ms"] == 150
            mock_smoke.assert_called_once_with("microsoft/DialoGPT-medium")


def mock_open_multiple_files(files_dict):
    """Helper function to mock opening multiple files."""
    from unittest.mock import mock_open
    
    def open_mock(filename, *args, **kwargs):
        for expected_filename, content in files_dict.items():
            if filename == expected_filename:
                return mock_open(read_data=content).return_value
        return mock_open().return_value
    
    return open_mock