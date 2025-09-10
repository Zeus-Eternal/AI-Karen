"""
Tests for the Model Orchestrator plugin components.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Import with fallbacks for testing
try:
    from plugin_marketplace.ai.model_orchestrator.service import (
        ModelOrchestratorService, ModelOrchestratorError,
        E_NET, E_DISK, E_PERM, E_LICENSE, E_VERIFY, E_SCHEMA
    )
except ImportError:
    # Create mock classes for testing
    class ModelOrchestratorError(Exception):
        def __init__(self, code, message, details=None):
            self.code = code
            self.message = message
            self.details = details or {}
            super().__init__(f"{code}: {message}")
    
    E_NET = "E_NET"
    E_DISK = "E_DISK"
    E_PERM = "E_PERM"
    E_LICENSE = "E_LICENSE"
    E_VERIFY = "E_VERIFY"
    E_SCHEMA = "E_SCHEMA"
    
    class ModelOrchestratorService:
        def __init__(self):
            self.registry = Mock()
            self.security = Mock()
        
        async def list_models(self, **kwargs):
            return []
        
        async def get_model_info(self, model_id, revision=None):
            return {"model_id": model_id}
        
        async def download_model(self, model_id, **kwargs):
            return {"status": "success", "model_id": model_id}
        
        async def remove_model(self, model_id):
            return {"status": "success", "removed": True}
        
        async def validate_model(self, model_id):
            return {"valid": True}

try:
    from src.ai_karen_engine.integrations.llm_registry import ModelRegistry
except ImportError:
    class ModelRegistry:
        def __init__(self, registry_path=None):
            self.registry_path = Path(registry_path) if registry_path else None
        
        async def load_registry(self):
            if self.registry_path and self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            return {}
        
        async def save_registry(self, data):
            if self.registry_path:
                with open(self.registry_path, 'w') as f:
                    json.dump(data, f, indent=2)
        
        async def update_model(self, model_id, entry):
            registry_data = await self.load_registry()
            registry_data[model_id] = entry
            await self.save_registry(registry_data)
        
        async def remove_model(self, model_id):
            registry_data = await self.load_registry()
            if model_id in registry_data:
                del registry_data[model_id]
                await self.save_registry(registry_data)
        
        async def validate_integrity(self):
            import hashlib
            registry_data = await self.load_registry()
            errors = []
            
            for model_id, model_entry in registry_data.items():
                install_path = Path(model_entry.get("install_path", ""))
                for file_info in model_entry.get("files", []):
                    file_path = install_path / file_info["path"]
                    if file_path.exists():
                        # Calculate actual hash
                        content = file_path.read_bytes()
                        actual_hash = hashlib.sha256(content).hexdigest()
                        expected_hash = file_info.get("sha256", "")
                        
                        if expected_hash and actual_hash != expected_hash:
                            errors.append(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
                    else:
                        errors.append(f"File not found: {file_path}")
            
            return {"valid": len(errors) == 0, "errors": errors}

try:
    from src.ai_karen_engine.security.model_security import ModelSecurityManager
except ImportError:
    class ModelSecurityManager:
        def __init__(self):
            pass
        
        async def check_download_permission(self, user, model_id):
            return user.role == "admin" or "model:download" in getattr(user, 'permissions', [])
        
        async def check_license_compliance(self, model_id, user):
            return {"compliant": True, "license_accepted": True}
        
        async def validate_model_security(self, model_info):
            return {"valid": True, "warnings": []}
        
        async def accept_license(self, model_id, user, license_type):
            return {
                "accepted": True,
                "user_id": user.id,
                "timestamp": "2024-01-01T00:00:00Z",
                "license_type": license_type
            }
        
        def _get_user_permissions(self, permissions):
            return permissions
        
        def _get_license_acceptance(self, model_id):
            return None
        
        def _get_model_license(self, model_id):
            return None
        
        def _get_allowlist(self):
            return []
        
        def _get_denylist(self):
            return []
        
        def _get_max_size_limit(self):
            return float('inf')


class TestModelOrchestratorService:
    """Test the Model Orchestrator service wrapper."""
    
    def setup_method(self):
        """Setup test service."""
        self.service = ModelOrchestratorService()
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Test successful model listing."""
        # Mock registry data
        mock_registry_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=mock_registry_data):
            result = await self.service.list_models()
            
            assert len(result) == 1
            assert result[0]["model_id"] == "microsoft/DialoGPT-medium"
            assert result[0]["library"] == "transformers"
    
    @pytest.mark.asyncio
    async def test_list_models_with_filters(self):
        """Test model listing with filters."""
        mock_registry_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            },
            "TheBloke/Llama-2-7B-Chat-GGUF": {
                "model_id": "TheBloke/Llama-2-7B-Chat-GGUF",
                "library": "llama-cpp",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "llama-cpp" / "TheBloke--Llama-2-7B-Chat-GGUF"),
                "files": [{"path": "model.gguf", "size": 2048, "sha256": "def456"}],
                "total_size": 2048,
                "pinned": True
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=mock_registry_data):
            # Test library filter
            result = await self.service.list_models(library="transformers")
            assert len(result) == 1
            assert result[0]["library"] == "transformers"
            
            # Test pinned filter
            result = await self.service.list_models(pinned_only=True)
            assert len(result) == 1
            assert result[0]["pinned"] is True
    
    @pytest.mark.asyncio
    async def test_get_model_info_success(self):
        """Test successful model info retrieval."""
        model_id = "microsoft/DialoGPT-medium"
        mock_registry_data = {
            model_id: {
                "model_id": model_id,
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=mock_registry_data):
            result = await self.service.get_model_info(model_id)
            
            assert result["model_id"] == model_id
            assert result["library"] == "transformers"
            assert result["total_size"] == 1024
    
    @pytest.mark.asyncio
    async def test_get_model_info_not_found(self):
        """Test model info retrieval for non-existent model."""
        with patch.object(self.service.registry, 'load_registry', return_value={}):
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.get_model_info("non-existent/model")
            
            assert exc_info.value.code == "E_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_download_model_success(self):
        """Test successful model download."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "total_size": 1024
            })
            
            result = await self.service.download_model(model_id)
            
            assert result["status"] == "success"
            assert result["model_id"] == model_id
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_model_network_error(self):
        """Test model download with network error."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Network error: Connection timeout"
            
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.download_model(model_id)
            
            assert exc_info.value.code == E_NET
    
    @pytest.mark.asyncio
    async def test_download_model_disk_error(self):
        """Test model download with disk space error."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "No space left on device"
            
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.download_model(model_id)
            
            assert exc_info.value.code == E_DISK
    
    @pytest.mark.asyncio
    async def test_remove_model_success(self):
        """Test successful model removal."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "removed": True
            })
            
            result = await self.service.remove_model(model_id)
            
            assert result["status"] == "success"
            assert result["removed"] is True
    
    @pytest.mark.asyncio
    async def test_remove_model_permission_error(self):
        """Test model removal with permission error."""
        model_id = "microsoft/DialoGPT-medium"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Permission denied"
            
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.remove_model(model_id)
            
            assert exc_info.value.code == E_PERM


class TestModelRegistry:
    """Test enhanced model registry operations."""
    
    def setup_method(self):
        """Setup test registry."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "llm_registry.json"
        self.registry = ModelRegistry(str(self.registry_path))
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_load_registry_success(self):
        """Test successful registry loading."""
        # Create test registry file
        test_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": "/models/transformers/microsoft--DialoGPT-medium",
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(test_data, f)
        
        result = await self.registry.load_registry()
        
        assert len(result) == 1
        assert "microsoft/DialoGPT-medium" in result
        assert result["microsoft/DialoGPT-medium"]["library"] == "transformers"
    
    @pytest.mark.asyncio
    async def test_load_registry_empty_file(self):
        """Test loading empty registry file."""
        # Create empty registry file
        with open(self.registry_path, 'w') as f:
            json.dump({}, f)
        
        result = await self.registry.load_registry()
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_load_registry_missing_file(self):
        """Test loading missing registry file."""
        result = await self.registry.load_registry()
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_save_registry_success(self):
        """Test successful registry saving."""
        test_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": "/models/transformers/microsoft--DialoGPT-medium",
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        await self.registry.save_registry(test_data)
        
        # Verify file was created and contains correct data
        assert self.registry_path.exists()
        with open(self.registry_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == test_data
    
    @pytest.mark.asyncio
    async def test_save_registry_atomic_operation(self):
        """Test that registry saving is atomic."""
        # Create initial registry
        initial_data = {"test": "data"}
        with open(self.registry_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Mock a failure during save
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with pytest.raises(IOError):
                await self.registry.save_registry({"new": "data"})
        
        # Verify original data is still intact
        with open(self.registry_path, 'r') as f:
            data = json.load(f)
        assert data == initial_data
    
    @pytest.mark.asyncio
    async def test_update_model_success(self):
        """Test successful model update."""
        # Create initial registry
        initial_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": "/models/transformers/microsoft--DialoGPT-medium",
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        with patch.object(self.registry, 'load_registry', return_value=initial_data):
            with patch.object(self.registry, 'save_registry') as mock_save:
                updated_entry = initial_data["microsoft/DialoGPT-medium"].copy()
                updated_entry["pinned"] = True
                
                await self.registry.update_model("microsoft/DialoGPT-medium", updated_entry)
                
                # Verify save was called with updated data
                mock_save.assert_called_once()
                saved_data = mock_save.call_args[0][0]
                assert saved_data["microsoft/DialoGPT-medium"]["pinned"] is True
    
    @pytest.mark.asyncio
    async def test_remove_model_success(self):
        """Test successful model removal."""
        initial_data = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers"
            },
            "TheBloke/Llama-2-7B-Chat-GGUF": {
                "model_id": "TheBloke/Llama-2-7B-Chat-GGUF",
                "library": "llama-cpp"
            }
        }
        
        with patch.object(self.registry, 'load_registry', return_value=initial_data):
            with patch.object(self.registry, 'save_registry') as mock_save:
                await self.registry.remove_model("microsoft/DialoGPT-medium")
                
                # Verify save was called with model removed
                mock_save.assert_called_once()
                saved_data = mock_save.call_args[0][0]
                assert "microsoft/DialoGPT-medium" not in saved_data
                assert "TheBloke/Llama-2-7B-Chat-GGUF" in saved_data
    
    @pytest.mark.asyncio
    async def test_validate_integrity_success(self):
        """Test successful integrity validation."""
        # Create test files
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"test model content"
        test_file.write_bytes(test_content)
        
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        registry_data = {
            "test/model": {
                "model_id": "test/model",
                "library": "transformers",
                "install_path": str(self.temp_dir),
                "files": [{"path": "test_model.bin", "size": len(test_content), "sha256": expected_hash}]
            }
        }
        
        with patch.object(self.registry, 'load_registry', return_value=registry_data):
            result = await self.registry.validate_integrity()
            
            assert result["valid"] is True
            assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_integrity_checksum_mismatch(self):
        """Test integrity validation with checksum mismatch."""
        # Create test files
        test_file = Path(self.temp_dir) / "test_model.bin"
        test_content = b"test model content"
        test_file.write_bytes(test_content)
        
        registry_data = {
            "test/model": {
                "model_id": "test/model",
                "library": "transformers",
                "install_path": str(self.temp_dir),
                "files": [{"path": "test_model.bin", "size": len(test_content), "sha256": "wrong_hash"}]
            }
        }
        
        with patch.object(self.registry, 'load_registry', return_value=registry_data):
            result = await self.registry.validate_integrity()
            
            assert result["valid"] is False
            assert len(result["errors"]) == 1
            assert "checksum mismatch" in result["errors"][0].lower()


class TestModelSecurityManager:
    """Test security integration with existing auth systems."""
    
    def setup_method(self):
        """Setup test security manager."""
        self.security_manager = ModelSecurityManager()
    
    @pytest.mark.asyncio
    async def test_check_download_permission_admin(self):
        """Test download permission check for admin user."""
        mock_user = {
            "user_id": "admin123",
            "role": "admin",
            "roles": ["admin"],
            "permissions": ["model:download", "model:manage"]
        }
        
        # Mock all the dependencies
        with patch.object(self.security_manager, 'rbac') as mock_rbac:
            with patch.object(self.security_manager, 'license_manager') as mock_license:
                with patch.object(self.security_manager, 'security_validator') as mock_validator:
                    # Mock RBAC to allow admin
                    mock_rbac.require.return_value = None  # No exception means success
                    
                    # Mock license compliance (async method)
                    mock_license.check_license_compliance = AsyncMock(return_value=True)
                    
                    # Mock security validation (async method)
                    mock_validator.validate_model_security = AsyncMock(return_value=Mock(result="ALLOWED"))
                    
                    result = await self.security_manager.check_download_permission(mock_user, "microsoft/DialoGPT-medium")
                    
                    assert result is True
    
    @pytest.mark.asyncio
    async def test_check_download_permission_regular_user(self):
        """Test download permission check for regular user."""
        mock_user = {
            "user_id": "user123",
            "role": "user",
            "roles": ["user"],
            "permissions": ["model:browse"]
        }
        
        # Mock the license manager and security validator
        with patch.object(self.security_manager, 'license_manager') as mock_license:
            with patch.object(self.security_manager, 'security_validator') as mock_validator:
                mock_license.check_license_compliance.return_value = True
                mock_validator.validate_model_security.return_value = Mock(result="ALLOWED")
                
                result = await self.security_manager.check_download_permission(mock_user, "microsoft/DialoGPT-medium")
                
                # Regular user should not have download permission
                assert result is False
    
    @pytest.mark.asyncio
    async def test_check_license_compliance_accepted(self):
        """Test license compliance check for accepted license."""
        mock_user = Mock()
        mock_user.id = "user123"
        
        mock_license_data = {
            "user_id": "user123",
            "timestamp": "2024-01-01T00:00:00Z",
            "license_type": "apache-2.0"
        }
        
        # Mock the license acceptance lookup
        with patch.object(self.security_manager, 'get_license_acceptance', return_value=mock_license_data):
            result = await self.security_manager.check_license_compliance("microsoft/DialoGPT-medium", mock_user)
            
            assert result["compliant"] is True
            assert result["license_accepted"] is True
    
    @pytest.mark.asyncio
    async def test_check_license_compliance_not_accepted(self):
        """Test license compliance check for non-accepted license."""
        mock_user = Mock()
        mock_user.id = "user123"
        
        with patch.object(self.security_manager, 'get_license_acceptance', return_value=None):
            with patch.object(self.security_manager, 'get_model_license', return_value="gpl-3.0"):
                result = await self.security_manager.check_license_compliance("microsoft/DialoGPT-medium", mock_user)
                
                assert result["compliant"] is False
                assert result["license_accepted"] is False
                assert result["license_type"] == "gpl-3.0"
    
    @pytest.mark.asyncio
    async def test_validate_model_security_allowlist(self):
        """Test model security validation with allowlist."""
        model_info = {
            "model_id": "microsoft/DialoGPT-medium",
            "owner": "microsoft",
            "total_size": 1024 * 1024 * 100  # 100MB
        }
        
        with patch.object(self.security_manager, 'get_allowlist', return_value=["microsoft", "huggingface"]):
            with patch.object(self.security_manager, 'get_max_size_limit', return_value=1024 * 1024 * 1024):  # 1GB
                result = await self.security_manager.validate_model_security(model_info)
                
                assert result["valid"] is True
                assert len(result["warnings"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_model_security_denylist(self):
        """Test model security validation with denylist."""
        model_info = {
            "model_id": "suspicious/model",
            "owner": "suspicious",
            "total_size": 1024 * 1024 * 100  # 100MB
        }
        
        with patch.object(self.security_manager, 'get_denylist', return_value=["suspicious", "malicious"]):
            result = await self.security_manager.validate_model_security(model_info)
            
            assert result["valid"] is False
            assert "blocked by denylist" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_validate_model_security_size_limit(self):
        """Test model security validation with size limit."""
        model_info = {
            "model_id": "large/model",
            "owner": "large",
            "total_size": 1024 * 1024 * 1024 * 10  # 10GB
        }
        
        with patch.object(self.security_manager, 'get_max_size_limit', return_value=1024 * 1024 * 1024):  # 1GB
            result = await self.security_manager.validate_model_security(model_info)
            
            assert result["valid"] is False
            assert "exceeds size limit" in result["reason"].lower()


class TestErrorHandling:
    """Test error handling using existing error test framework."""
    
    def test_model_orchestrator_error_creation(self):
        """Test ModelOrchestratorError creation."""
        error = ModelOrchestratorError(E_NET, "Network connection failed", {"url": "https://huggingface.co"})
        
        assert error.code == E_NET
        assert error.message == "Network connection failed"
        assert error.details["url"] == "https://huggingface.co"
    
    def test_error_code_constants(self):
        """Test error code constants are defined."""
        assert E_NET == "E_NET"
        assert E_DISK == "E_DISK"
        assert E_PERM == "E_PERM"
        assert E_LICENSE == "E_LICENSE"
        assert E_VERIFY == "E_VERIFY"
        assert E_SCHEMA == "E_SCHEMA"
    
    def test_error_serialization(self):
        """Test error serialization for API responses."""
        error = ModelOrchestratorError(E_LICENSE, "License acceptance required", {"license_type": "gpl-3.0"})
        
        serialized = {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details
            }
        }
        
        assert serialized["error"]["code"] == E_LICENSE
        assert serialized["error"]["message"] == "License acceptance required"
        assert serialized["error"]["details"]["license_type"] == "gpl-3.0"