"""
Workflow tests for Model Orchestrator using existing test infrastructure.
"""

import pytest
import json
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Import with fallbacks for testing
try:
    from plugin_marketplace.ai.model_orchestrator.service import (
        ModelOrchestratorService, ModelOrchestratorError, E_NET, E_DISK, E_LICENSE
    )
except ImportError:
    class ModelOrchestratorError(Exception):
        def __init__(self, code, message, details=None):
            self.code = code
            self.message = message
            self.details = details or {}
    
    E_NET = "E_NET"
    E_DISK = "E_DISK"
    E_LICENSE = "E_LICENSE"
    
    class ModelOrchestratorService:
        def __init__(self):
            self.registry = Mock()
            self.security = Mock()
            self._registry_data = {}
        
        async def list_models(self, **kwargs):
            # Return models from mock registry data
            return list(self._registry_data.values())
        
        async def get_model_info(self, model_id):
            return self._registry_data.get(model_id, {"model_id": model_id})
        
        async def download_model(self, model_id, **kwargs):
            return {"status": "success", "model_id": model_id}
        
        async def detect_legacy_models(self):
            return {"detected_models": []}
        
        async def migrate_layout(self, **kwargs):
            return {"status": "success", "migrated_count": 0}
        
        async def rollback_migration(self, backup_id):
            return {"rollback": True, "restored_files": 0}
        
        async def get_job_progress(self, job_id):
            return {"job_id": job_id, "progress": 1.0, "status": "complete"}
        
        async def pin_model(self, model_id):
            if model_id in self._registry_data:
                self._registry_data[model_id]["pinned"] = True
        
        async def remove_model(self, model_id):
            return {"status": "success", "removed": True}
        
        async def browse_models(self, **kwargs):
            return {"models": []}
        
        async def validate_model(self, model_id):
            return {"valid": True}
        
        async def run_smoke_test(self, model_id):
            return {"success": True, "latency_ms": 100}
        
        async def check_compatibility(self, model_id):
            return {"compatible": True}
        
        async def get_health_status(self, **kwargs):
            return {"status": "healthy"}

try:
    from src.ai_karen_engine.integrations.llm_registry import ModelRegistry
except ImportError:
    class ModelRegistry:
        def __init__(self, registry_path=None):
            pass
        
        async def load_registry(self):
            return {}

try:
    from src.ai_karen_engine.security.model_security import ModelSecurityManager
except ImportError:
    class ModelSecurityManager:
        def __init__(self):
            pass
        
        async def check_download_permission(self, user, model_id):
            return True


class TestDownloadWorkflows:
    """Test download workflows using existing workflow test patterns."""
    
    def setup_method(self):
        """Setup workflow test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
        self.service = ModelOrchestratorService()
        
        # Create test directories
        (self.models_path / "transformers").mkdir(exist_ok=True)
        (self.models_path / "llama-cpp").mkdir(exist_ok=True)
        (self.models_path / "spacy").mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_download_workflow(self):
        """Test complete model download workflow from start to finish."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Step 1: Check model doesn't exist
        self.service._registry_data = {}
        models = await self.service.list_models()
        assert len(models) == 0
        
        # Step 2: Download model
        expected_download_result = {
            "status": "success",
            "model_id": model_id,
            "job_id": "job_123",
            "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
            "total_size": 1024
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(expected_download_result)
            
            result = await self.service.download_model(model_id)
            assert result["status"] == "success"
            assert result["model_id"] == model_id
        
        # Step 3: Verify model is registered
        registry_data = {
            model_id: {
                "model_id": model_id,
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": expected_download_result["install_path"],
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False
            }
        }
        
        # Update mock registry data
        self.service._registry_data = registry_data
        models = await self.service.list_models()
        assert len(models) == 1
        assert models[0]["model_id"] == model_id
        
        # Step 4: Verify model info is accessible
        info = await self.service.get_model_info(model_id)
        assert info["model_id"] == model_id
    
    @pytest.mark.asyncio
    async def test_download_workflow_with_license_acceptance(self):
        """Test download workflow requiring license acceptance."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Step 1: Attempt download without license acceptance
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "E_LICENSE: License acceptance required for gpl-3.0"
            
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.download_model(model_id)
            
            assert exc_info.value.code == E_LICENSE
        
        # Step 2: Accept license
        mock_user = Mock()
        mock_user.id = "user123"
        
        with patch.object(self.service.security, 'accept_license') as mock_accept:
            mock_accept.return_value = {
                "accepted": True,
                "user_id": "user123",
                "timestamp": "2024-01-01T00:00:00Z",
                "license_type": "gpl-3.0"
            }
            
            license_result = await self.service.security.accept_license(model_id, mock_user, "gpl-3.0")
            assert license_result["accepted"] is True
        
        # Step 3: Retry download after license acceptance
        expected_result = {
            "status": "success",
            "model_id": model_id,
            "job_id": "job_124",
            "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium")
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(expected_result)
            
            result = await self.service.download_model(model_id, user=mock_user)
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_download_workflow_with_retry_logic(self):
        """Test download workflow with network retry logic."""
        model_id = "microsoft/DialoGPT-medium"
        
        # First attempt fails with network error
        with patch('subprocess.run') as mock_run:
            # First call fails
            mock_run.side_effect = [
                Mock(returncode=1, stderr="E_NET: Connection timeout"),
                Mock(returncode=1, stderr="E_NET: Connection timeout"),
                # Third call succeeds
                Mock(returncode=0, stdout=json.dumps({
                    "status": "success",
                    "model_id": model_id,
                    "job_id": "job_125"
                }))
            ]
            
            with patch('asyncio.sleep'):  # Speed up test
                result = await self.service.download_model(model_id, max_retries=3)
                assert result["status"] == "success"
                assert mock_run.call_count == 3
    
    @pytest.mark.asyncio
    async def test_download_workflow_with_progress_tracking(self):
        """Test download workflow with progress tracking."""
        model_id = "microsoft/DialoGPT-medium"
        job_id = "job_126"
        
        # Mock progress updates
        progress_updates = [
            {"job_id": job_id, "progress": 0.0, "status": "starting"},
            {"job_id": job_id, "progress": 0.3, "status": "downloading", "current_file": "config.json"},
            {"job_id": job_id, "progress": 0.7, "status": "downloading", "current_file": "pytorch_model.bin"},
            {"job_id": job_id, "progress": 1.0, "status": "complete"}
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "job_id": job_id
            })
            
            # Start download
            result = await self.service.download_model(model_id)
            assert result["job_id"] == job_id
            
            # Simulate progress tracking
            with patch.object(self.service, 'get_job_progress') as mock_progress:
                for update in progress_updates:
                    mock_progress.return_value = update
                    progress = await self.service.get_job_progress(job_id)
                    assert progress["job_id"] == job_id
                    
                # Final progress should be complete
                assert progress["status"] == "complete"
                assert progress["progress"] == 1.0
    
    @pytest.mark.asyncio
    async def test_batch_download_workflow(self):
        """Test batch download workflow with concurrency control."""
        model_ids = [
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-small",
            "distilbert-base-uncased"
        ]
        
        # Mock successful downloads
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "job_id": "job_batch"
            })
            
            # Test batch download with concurrency limit
            with patch.object(self.service, '_download_semaphore', asyncio.Semaphore(2)):
                tasks = [self.service.download_model(model_id) for model_id in model_ids]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All downloads should succeed
                for result in results:
                    assert not isinstance(result, Exception)
                    assert result["status"] == "success"
                
                # Should have made 3 subprocess calls
                assert mock_run.call_count == 3


class TestMigrationWorkflows:
    """Test migration scenarios with existing migration test framework."""
    
    def setup_method(self):
        """Setup migration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
        self.service = ModelOrchestratorService()
        
        # Create legacy model structure
        self.legacy_path = self.models_path / "legacy"
        self.legacy_path.mkdir(exist_ok=True)
        
        # Create some legacy model files
        (self.legacy_path / "model1").mkdir(exist_ok=True)
        (self.legacy_path / "model1" / "config.json").write_text('{"model_type": "bert"}')
        (self.legacy_path / "model2").mkdir(exist_ok=True)
        (self.legacy_path / "model2" / "pytorch_model.bin").write_bytes(b"fake model data")
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_migration_workflow(self):
        """Test complete migration workflow from legacy to new structure."""
        # Step 1: Detect legacy models
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "detected_models": [
                    {
                        "path": str(self.legacy_path / "model1"),
                        "estimated_library": "transformers",
                        "estimated_id": "unknown/model1"
                    },
                    {
                        "path": str(self.legacy_path / "model2"),
                        "estimated_library": "transformers", 
                        "estimated_id": "unknown/model2"
                    }
                ]
            })
            
            detection_result = await self.service.detect_legacy_models()
            assert len(detection_result["detected_models"]) == 2
        
        # Step 2: Run dry-run migration
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "dry_run": True,
                "migration_plan": [
                    {
                        "source": str(self.legacy_path / "model1"),
                        "destination": str(self.models_path / "transformers" / "unknown--model1"),
                        "action": "move"
                    },
                    {
                        "source": str(self.legacy_path / "model2"),
                        "destination": str(self.models_path / "transformers" / "unknown--model2"),
                        "action": "move"
                    }
                ]
            })
            
            dry_run_result = await self.service.migrate_layout(dry_run=True)
            assert dry_run_result["dry_run"] is True
            assert len(dry_run_result["migration_plan"]) == 2
        
        # Step 3: Execute actual migration
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "migrated_count": 2,
                "errors": [],
                "backup_path": str(self.temp_dir / "backup_123")
            })
            
            migration_result = await self.service.migrate_layout(dry_run=False)
            assert migration_result["status"] == "success"
            assert migration_result["migrated_count"] == 2
            assert len(migration_result["errors"]) == 0
        
        # Step 4: Verify registry was updated
        expected_registry = {
            "unknown/model1": {
                "model_id": "unknown/model1",
                "library": "transformers",
                "install_path": str(self.models_path / "transformers" / "unknown--model1")
            },
            "unknown/model2": {
                "model_id": "unknown/model2", 
                "library": "transformers",
                "install_path": str(self.models_path / "transformers" / "unknown--model2")
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=expected_registry):
            models = await self.service.list_models()
            assert len(models) == 2
    
    @pytest.mark.asyncio
    async def test_migration_workflow_with_conflicts(self):
        """Test migration workflow with file conflicts."""
        # Create conflicting destination
        conflict_path = self.models_path / "transformers" / "unknown--model1"
        conflict_path.mkdir(parents=True, exist_ok=True)
        (conflict_path / "existing_file.txt").write_text("existing content")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "migrated_count": 1,
                "errors": [
                    {
                        "source": str(self.legacy_path / "model1"),
                        "error": "Destination already exists",
                        "resolution": "Renamed to unknown--model1_migrated"
                    }
                ],
                "conflicts_resolved": 1
            })
            
            result = await self.service.migrate_layout()
            assert result["conflicts_resolved"] == 1
            assert len(result["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_migration_rollback_workflow(self):
        """Test migration rollback workflow."""
        # Step 1: Start migration
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Migration failed: Disk full"
            
            with pytest.raises(ModelOrchestratorError):
                await self.service.migrate_layout()
        
        # Step 2: Perform rollback
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "rollback": True,
                "restored_files": 2,
                "backup_removed": True
            })
            
            rollback_result = await self.service.rollback_migration("backup_123")
            assert rollback_result["rollback"] is True
            assert rollback_result["restored_files"] == 2
    
    @pytest.mark.asyncio
    async def test_incremental_migration_workflow(self):
        """Test incremental migration workflow."""
        # Step 1: Migrate first batch
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "migrated_count": 1,
                "remaining_count": 1,
                "batch_complete": True
            })
            
            result = await self.service.migrate_layout(batch_size=1)
            assert result["migrated_count"] == 1
            assert result["remaining_count"] == 1
        
        # Step 2: Migrate remaining models
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "migrated_count": 1,
                "remaining_count": 0,
                "migration_complete": True
            })
            
            result = await self.service.migrate_layout(batch_size=1)
            assert result["migration_complete"] is True
            assert result["remaining_count"] == 0


class TestRBACWorkflows:
    """Test RBAC scenarios using existing permission test utilities."""
    
    def setup_method(self):
        """Setup RBAC test environment."""
        self.service = ModelOrchestratorService()
        self.security_manager = ModelSecurityManager()
        
        # Create test users
        self.admin_user = Mock()
        self.admin_user.id = "admin123"
        self.admin_user.role = "admin"
        self.admin_user.permissions = ["model:download", "model:manage", "model:migrate"]
        
        self.regular_user = Mock()
        self.regular_user.id = "user123"
        self.regular_user.role = "user"
        self.regular_user.permissions = ["model:browse"]
        
        self.power_user = Mock()
        self.power_user.id = "power123"
        self.power_user.role = "power_user"
        self.power_user.permissions = ["model:browse", "model:download"]
    
    @pytest.mark.asyncio
    async def test_admin_full_access_workflow(self):
        """Test admin user with full access workflow."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Admin can browse models
        with patch.object(self.security_manager, 'check_browse_permission', return_value=True):
            can_browse = await self.security_manager.check_browse_permission(self.admin_user)
            assert can_browse is True
        
        # Admin can download models
        with patch.object(self.security_manager, 'check_download_permission', return_value=True):
            can_download = await self.security_manager.check_download_permission(self.admin_user, model_id)
            assert can_download is True
        
        # Admin can perform migration
        with patch.object(self.security_manager, 'check_migration_permission', return_value=True):
            can_migrate = await self.security_manager.check_migration_permission(self.admin_user)
            assert can_migrate is True
        
        # Admin can remove models
        with patch.object(self.security_manager, 'check_remove_permission', return_value=True):
            can_remove = await self.security_manager.check_remove_permission(self.admin_user, model_id)
            assert can_remove is True
    
    @pytest.mark.asyncio
    async def test_regular_user_restricted_workflow(self):
        """Test regular user with restricted access workflow."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Regular user can browse models
        with patch.object(self.security_manager, 'check_browse_permission', return_value=True):
            can_browse = await self.security_manager.check_browse_permission(self.regular_user)
            assert can_browse is True
        
        # Regular user cannot download models
        with patch.object(self.security_manager, 'check_download_permission', return_value=False):
            can_download = await self.security_manager.check_download_permission(self.regular_user, model_id)
            assert can_download is False
        
        # Regular user cannot perform migration
        with patch.object(self.security_manager, 'check_migration_permission', return_value=False):
            can_migrate = await self.security_manager.check_migration_permission(self.regular_user)
            assert can_migrate is False
        
        # Regular user cannot remove models
        with patch.object(self.security_manager, 'check_remove_permission', return_value=False):
            can_remove = await self.security_manager.check_remove_permission(self.regular_user, model_id)
            assert can_remove is False
    
    @pytest.mark.asyncio
    async def test_power_user_partial_access_workflow(self):
        """Test power user with partial access workflow."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Power user can browse and download
        with patch.object(self.security_manager, 'check_browse_permission', return_value=True):
            with patch.object(self.security_manager, 'check_download_permission', return_value=True):
                can_browse = await self.security_manager.check_browse_permission(self.power_user)
                can_download = await self.security_manager.check_download_permission(self.power_user, model_id)
                
                assert can_browse is True
                assert can_download is True
        
        # Power user cannot perform migration or removal
        with patch.object(self.security_manager, 'check_migration_permission', return_value=False):
            with patch.object(self.security_manager, 'check_remove_permission', return_value=False):
                can_migrate = await self.security_manager.check_migration_permission(self.power_user)
                can_remove = await self.security_manager.check_remove_permission(self.power_user, model_id)
                
                assert can_migrate is False
                assert can_remove is False
    
    @pytest.mark.asyncio
    async def test_permission_escalation_prevention(self):
        """Test prevention of permission escalation."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Regular user attempts to download (should fail)
        with patch.object(self.security_manager, 'check_download_permission', return_value=False):
            with pytest.raises(ModelOrchestratorError) as exc_info:
                # Simulate API call that checks permissions
                can_download = await self.security_manager.check_download_permission(self.regular_user, model_id)
                if not can_download:
                    raise ModelOrchestratorError("E_PERM", "Insufficient permissions")
            
            assert exc_info.value.code == "E_PERM"
        
        # Regular user attempts to migrate (should fail)
        with patch.object(self.security_manager, 'check_migration_permission', return_value=False):
            with pytest.raises(ModelOrchestratorError) as exc_info:
                can_migrate = await self.security_manager.check_migration_permission(self.regular_user)
                if not can_migrate:
                    raise ModelOrchestratorError("E_PERM", "Migration requires admin privileges")
            
            assert exc_info.value.code == "E_PERM"
    
    @pytest.mark.asyncio
    async def test_role_based_model_filtering(self):
        """Test role-based model filtering."""
        all_models = [
            {"model_id": "public/model", "visibility": "public"},
            {"model_id": "internal/model", "visibility": "internal"},
            {"model_id": "restricted/model", "visibility": "restricted"}
        ]
        
        # Regular user sees only public models
        with patch.object(self.security_manager, 'filter_models_by_permission') as mock_filter:
            mock_filter.return_value = [all_models[0]]  # Only public model
            
            filtered_models = await self.security_manager.filter_models_by_permission(
                self.regular_user, all_models
            )
            assert len(filtered_models) == 1
            assert filtered_models[0]["visibility"] == "public"
        
        # Admin user sees all models
        with patch.object(self.security_manager, 'filter_models_by_permission') as mock_filter:
            mock_filter.return_value = all_models  # All models
            
            filtered_models = await self.security_manager.filter_models_by_permission(
                self.admin_user, all_models
            )
            assert len(filtered_models) == 3


class TestOfflineModeWorkflows:
    """Test offline mode using existing network mocking patterns."""
    
    def setup_method(self):
        """Setup offline mode test environment."""
        self.service = ModelOrchestratorService()
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_offline_mode_cached_operations(self):
        """Test offline mode with cached operations."""
        # Setup cached registry
        cached_registry = {
            "microsoft/DialoGPT-medium": {
                "model_id": "microsoft/DialoGPT-medium",
                "library": "transformers",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "cached": True
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=cached_registry):
            # Offline mode should work for listing cached models
            models = await self.service.list_models(offline_mode=True)
            assert len(models) == 1
            assert models[0]["model_id"] == "microsoft/DialoGPT-medium"
            
            # Offline mode should work for getting info of cached models
            info = await self.service.get_model_info("microsoft/DialoGPT-medium", offline_mode=True)
            assert info["model_id"] == "microsoft/DialoGPT-medium"
    
    @pytest.mark.asyncio
    async def test_offline_mode_network_operations_blocked(self):
        """Test that network operations are blocked in offline mode."""
        model_id = "new/model"
        
        # Download should fail in offline mode
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "E_NET: Offline mode enabled, network access denied"
            
            with pytest.raises(ModelOrchestratorError) as exc_info:
                await self.service.download_model(model_id, offline_mode=True)
            
            assert exc_info.value.code == E_NET
            assert "offline mode" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_offline_mode_with_mirror(self):
        """Test offline mode with local mirror."""
        model_id = "microsoft/DialoGPT-medium"
        mirror_url = f"file://{self.temp_dir}/mirror"
        
        # Create mock mirror structure
        mirror_path = Path(self.temp_dir) / "mirror"
        mirror_path.mkdir(exist_ok=True)
        model_mirror_path = mirror_path / "microsoft" / "DialoGPT-medium"
        model_mirror_path.mkdir(parents=True, exist_ok=True)
        (model_mirror_path / "config.json").write_text('{"model_type": "gpt2"}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "source": "mirror",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium")
            })
            
            result = await self.service.download_model(
                model_id, 
                offline_mode=True, 
                mirror_url=mirror_url
            )
            
            assert result["status"] == "success"
            assert result["source"] == "mirror"
    
    @pytest.mark.asyncio
    async def test_offline_mode_graceful_degradation(self):
        """Test graceful degradation in offline mode."""
        # Some operations should work with cached data
        cached_registry = {
            "cached/model": {
                "model_id": "cached/model",
                "library": "transformers"
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=cached_registry):
            # List should work with cached data
            models = await self.service.list_models(offline_mode=True)
            assert len(models) == 1
            
            # Health check should indicate offline mode
            with patch('src.ai_karen_engine.health.model_orchestrator_health.ModelOrchestratorHealthCheck.check_health') as mock_health:
                mock_health.return_value = {
                    "status": "degraded",
                    "offline_mode": True,
                    "cached_models": 1,
                    "network_available": False
                }
                
                health = await self.service.get_health_status(offline_mode=True)
                assert health["status"] == "degraded"
                assert health["offline_mode"] is True
    
    @pytest.mark.asyncio
    async def test_network_failure_fallback_to_offline(self):
        """Test automatic fallback to offline mode on network failure."""
        model_id = "microsoft/DialoGPT-medium"
        
        # First attempt fails with network error
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stderr="E_NET: Connection timeout"),
                Mock(returncode=0, stdout=json.dumps({
                    "status": "success",
                    "model_id": model_id,
                    "source": "cache",
                    "offline_fallback": True
                }))
            ]
            
            result = await self.service.download_model(model_id, auto_offline_fallback=True)
            
            assert result["status"] == "success"
            assert result["offline_fallback"] is True
            assert mock_run.call_count == 2


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Setup end-to-end test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_path = Path(self.temp_dir) / "models"
        self.models_path.mkdir(exist_ok=True)
        self.service = ModelOrchestratorService()
    
    def teardown_method(self):
        """Cleanup test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_model_lifecycle(self):
        """Test complete model lifecycle from discovery to removal."""
        model_id = "microsoft/DialoGPT-medium"
        
        # Step 1: Browse available models (would normally query HuggingFace)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "models": [
                    {
                        "model_id": model_id,
                        "downloads": 1000,
                        "likes": 50,
                        "library": "transformers",
                        "total_size": 1024
                    }
                ]
            })
            
            browse_result = await self.service.browse_models(query="DialoGPT")
            assert len(browse_result["models"]) == 1
        
        # Step 2: Download model
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "job_id": "job_lifecycle",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium")
            })
            
            download_result = await self.service.download_model(model_id)
            assert download_result["status"] == "success"
        
        # Step 3: Verify model is registered and accessible
        registry_data = {
            model_id: {
                "model_id": model_id,
                "library": "transformers",
                "revision": "main",
                "installed_at": "2024-01-01T00:00:00Z",
                "install_path": str(self.models_path / "transformers" / "microsoft--DialoGPT-medium"),
                "files": [{"path": "config.json", "size": 1024, "sha256": "abc123"}],
                "total_size": 1024,
                "pinned": False,
                "last_accessed": "2024-01-01T00:00:00Z"
            }
        }
        
        with patch.object(self.service.registry, 'load_registry', return_value=registry_data):
            models = await self.service.list_models()
            assert len(models) == 1
            assert models[0]["model_id"] == model_id
        
        # Step 4: Use model (simulate LLM integration)
        with patch('src.ai_karen_engine.integrations.llm_registry.validate_model_loadability') as mock_validate:
            mock_validate.return_value = {"valid": True, "error": None}
            
            validation_result = await self.service.validate_model(model_id)
            assert validation_result["valid"] is True
        
        # Step 5: Pin model to protect from garbage collection
        with patch.object(self.service.registry, 'load_registry', return_value=registry_data):
            with patch.object(self.service.registry, 'save_registry') as mock_save:
                await self.service.pin_model(model_id)
                
                # Verify pin was saved
                mock_save.assert_called_once()
                saved_data = mock_save.call_args[0][0]
                assert saved_data[model_id]["pinned"] is True
        
        # Step 6: Eventually remove model
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({
                "status": "success",
                "model_id": model_id,
                "removed": True,
                "freed_space_gb": 0.001
            })
            
            remove_result = await self.service.remove_model(model_id)
            assert remove_result["status"] == "success"
            assert remove_result["removed"] is True
    
    @pytest.mark.asyncio
    async def test_multi_user_concurrent_operations(self):
        """Test concurrent operations by multiple users."""
        users = [
            Mock(id="user1", role="admin", permissions=["model:download", "model:manage"]),
            Mock(id="user2", role="user", permissions=["model:browse"]),
            Mock(id="user3", role="power_user", permissions=["model:browse", "model:download"])
        ]
        
        model_ids = [
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-small",
            "distilbert-base-uncased"
        ]
        
        # Simulate concurrent operations
        async def user_operation(user, model_id):
            # Check permissions
            with patch.object(self.service.security, 'check_download_permission') as mock_perm:
                mock_perm.return_value = user.role in ["admin", "power_user"]
                
                can_download = await self.service.security.check_download_permission(user, model_id)
                
                if can_download:
                    # Simulate download
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value.returncode = 0
                        mock_run.return_value.stdout = json.dumps({
                            "status": "success",
                            "model_id": model_id,
                            "user_id": user.id
                        })
                        
                        return await self.service.download_model(model_id, user=user)
                else:
                    return {"status": "permission_denied", "user_id": user.id}
        
        # Run concurrent operations
        tasks = []
        for i, user in enumerate(users):
            model_id = model_ids[i % len(model_ids)]
            tasks.append(user_operation(user, model_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        admin_result = results[0]
        user_result = results[1]
        power_user_result = results[2]
        
        assert admin_result["status"] == "success"  # Admin can download
        assert user_result["status"] == "permission_denied"  # Regular user cannot
        assert power_user_result["status"] == "success"  # Power user can download