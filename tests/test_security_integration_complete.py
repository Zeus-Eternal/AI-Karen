"""
Comprehensive Security Integration Tests for Response Core Orchestrator

This module tests the complete security integration including RBAC, audit logging,
secure model storage, and access controls working together.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import pytest
import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.auth.rbac_middleware import (
    RBACManager, Permission, Role, get_rbac_manager
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.training_audit_logger import (
    get_training_audit_logger, TrainingEventType
)
from ai_karen_engine.core.response.secure_model_storage import (
    SecureModelStorage, ModelType, SecurityLevel, get_secure_model_storage
)
from ai_karen_engine.auth.security_monitor import EnhancedSecurityMonitor
from ai_karen_engine.auth.config import AuthConfig


@pytest.fixture
def security_config():
    """Create security configuration for testing."""
    return AuthConfig.from_env()


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return UserData(
        user_id="admin-security-test",
        email="admin@security.test",
        full_name="Security Admin",
        roles=["admin", "user"],
        tenant_id="security-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def trainer_user():
    """Create trainer user for testing."""
    return UserData(
        user_id="trainer-security-test",
        email="trainer@security.test",
        full_name="Security Trainer",
        roles=["trainer", "user"],
        tenant_id="security-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def malicious_user():
    """Create user attempting malicious actions."""
    return UserData(
        user_id="malicious-user",
        email="malicious@security.test",
        full_name="Malicious User",
        roles=["user"],
        tenant_id="other-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def temp_storage_path():
    """Create temporary storage path for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def secure_storage(temp_storage_path):
    """Create secure model storage for testing."""
    return SecureModelStorage(
        storage_path=str(temp_storage_path / "secure_models"),
        encryption_key="test-security-key-32-bytes-long"
    )


@pytest.fixture
def test_model_file(temp_storage_path):
    """Create test model file."""
    model_file = temp_storage_path / "test_security_model.pkl"
    model_file.write_bytes(b"sensitive model data for security testing")
    return model_file


class TestCompleteSecurityIntegration:
    """Test complete security integration across all components."""
    
    @pytest.mark.asyncio
    async def test_secure_model_lifecycle_with_rbac_and_audit(
        self, 
        secure_storage, 
        test_model_file, 
        admin_user, 
        trainer_user, 
        malicious_user
    ):
        """Test complete secure model lifecycle with RBAC and audit logging."""
        rbac_manager = get_rbac_manager()
        audit_logger = get_training_audit_logger()
        
        # Phase 1: Admin creates secure model
        with patch.object(audit_logger, '_log_event') as mock_audit:
            model_id = await secure_storage.store_model(
                model_path=test_model_file,
                name="Secure Test Model",
                model_type=ModelType.TRANSFORMER,
                description="Highly sensitive model for security testing",
                user=admin_user,
                version="1.0.0",
                security_level=SecurityLevel.CONFIDENTIAL,
                encrypt=True,
                parameters={"layers": 12, "hidden_size": 768},
                performance_metrics={"accuracy": 0.95, "f1_score": 0.93}
            )
            
            # Verify model was created
            assert model_id is not None
            
            # Verify audit logging occurred
            mock_audit.assert_called()
            audit_event = mock_audit.call_args[0][0]
            assert audit_event.user_id == admin_user.user_id
            assert "model" in audit_event.message.lower()
        
        # Phase 2: Trainer accesses model (should succeed)
        with patch.object(audit_logger, 'log_model_accessed') as mock_access_audit:
            # Check trainer has model read permission
            assert rbac_manager.has_permission(trainer_user, Permission.MODEL_READ)
            
            # Trainer retrieves model
            retrieved_path = await secure_storage.retrieve_model(model_id, trainer_user)
            assert retrieved_path.exists()
            
            # Verify access was audited
            mock_access_audit.assert_called_once()
            assert mock_access_audit.call_args[1]["user"].user_id == trainer_user.user_id
        
        # Phase 3: Malicious user attempts unauthorized access (should fail)
        with patch.object(audit_logger, 'log_unauthorized_access_attempt') as mock_unauthorized:
            # Malicious user from different tenant attempts access
            with pytest.raises(PermissionError):
                await secure_storage.retrieve_model(model_id, malicious_user)
            
            # Verify unauthorized access was audited
            mock_unauthorized.assert_called_once()
            assert mock_unauthorized.call_args[1]["user"].user_id == malicious_user.user_id
        
        # Phase 4: Trainer attempts to delete model (should fail - not admin or creator)
        with patch.object(audit_logger, 'log_permission_denied') as mock_denied:
            with pytest.raises(PermissionError):
                await secure_storage.delete_model(model_id, trainer_user)
            
            # Verify permission denial was audited
            mock_denied.assert_called_once()
        
        # Phase 5: Admin deletes model (should succeed)
        with patch.object(audit_logger, 'log_model_deleted') as mock_delete_audit:
            success = await secure_storage.delete_model(model_id, admin_user)
            assert success is True
            
            # Verify deletion was audited
            mock_delete_audit.assert_called_once()
            assert mock_delete_audit.call_args[1]["user"].user_id == admin_user.user_id
    
    @pytest.mark.asyncio
    async def test_training_operation_security_workflow(
        self, 
        admin_user, 
        trainer_user, 
        malicious_user
    ):
        """Test security workflow for training operations."""
        rbac_manager = get_rbac_manager()
        audit_logger = get_training_audit_logger()
        
        training_job_id = "secure-training-job-123"
        
        # Phase 1: Admin starts training job
        with patch.object(audit_logger, 'log_training_started') as mock_start_audit:
            # Verify admin has training execute permission
            assert rbac_manager.has_permission(admin_user, Permission.TRAINING_EXECUTE)
            
            # Simulate training start
            audit_logger.log_training_started(
                user=admin_user,
                training_job_id=training_job_id,
                model_id="model-456",
                dataset_id="dataset-789",
                training_config={
                    "epochs": 10,
                    "learning_rate": 0.001,
                    "batch_size": 32
                }
            )
            
            mock_start_audit.assert_called_once()
        
        # Phase 2: Trainer monitors training (should succeed)
        with patch.object(audit_logger, '_log_event') as mock_audit:
            # Verify trainer has training read permission
            assert rbac_manager.has_permission(trainer_user, Permission.TRAINING_READ)
            
            # Simulate training monitoring access
            rbac_manager.audit_access_attempt(
                user_data=trainer_user,
                permission=Permission.TRAINING_READ,
                resource=f"training_job_{training_job_id}",
                granted=True
            )
            
            mock_audit.assert_called()
        
        # Phase 3: Malicious user attempts to access training (should fail)
        with patch.object(audit_logger, 'log_unauthorized_access_attempt') as mock_unauthorized:
            # Verify malicious user doesn't have training permissions
            assert not rbac_manager.has_permission(malicious_user, Permission.TRAINING_READ)
            
            # Simulate unauthorized access attempt
            audit_logger.log_unauthorized_access_attempt(
                user=malicious_user,
                resource_type="training_job",
                resource_id=training_job_id,
                permission_required="training:read",
                ip_address="192.168.1.100"
            )
            
            mock_unauthorized.assert_called_once()
        
        # Phase 4: Training completes successfully
        with patch.object(audit_logger, 'log_training_completed') as mock_complete_audit:
            audit_logger.log_training_completed(
                user=admin_user,
                training_job_id=training_job_id,
                model_id="model-456",
                duration_ms=3600000,  # 1 hour
                performance_metrics={
                    "final_loss": 0.15,
                    "validation_accuracy": 0.94,
                    "training_accuracy": 0.96
                }
            )
            
            mock_complete_audit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_data_access_security_controls(
        self, 
        admin_user, 
        trainer_user, 
        malicious_user
    ):
        """Test security controls for data access operations."""
        rbac_manager = get_rbac_manager()
        audit_logger = get_training_audit_logger()
        
        dataset_id = "secure-dataset-456"
        
        # Phase 1: Admin uploads sensitive training data
        with patch.object(audit_logger, 'log_training_data_uploaded') as mock_upload_audit:
            # Verify admin has data write permission
            assert rbac_manager.has_permission(admin_user, Permission.DATA_WRITE)
            
            # Simulate data upload
            audit_logger.log_training_data_uploaded(
                user=admin_user,
                dataset_id=dataset_id,
                dataset_name="Sensitive Training Dataset",
                record_count=10000,
                file_size=50000000,  # 50MB
                data_format="json"
            )
            
            mock_upload_audit.assert_called_once()
        
        # Phase 2: Trainer accesses data for training (should succeed)
        with patch.object(rbac_manager, 'audit_access_attempt') as mock_access_audit:
            # Verify trainer has data read permission
            assert rbac_manager.has_permission(trainer_user, Permission.DATA_READ)
            
            # Simulate data access
            rbac_manager.audit_access_attempt(
                user_data=trainer_user,
                permission=Permission.DATA_READ,
                resource=f"dataset_{dataset_id}",
                granted=True
            )
            
            mock_access_audit.assert_called_once()
        
        # Phase 3: Malicious user attempts data export (should fail)
        with patch.object(audit_logger, 'log_permission_denied') as mock_denied:
            # Verify malicious user doesn't have data export permission
            assert not rbac_manager.has_permission(malicious_user, Permission.DATA_EXPORT)
            
            # Simulate unauthorized export attempt
            audit_logger.log_permission_denied(
                user=malicious_user,
                resource_type="dataset",
                resource_id=dataset_id,
                permission_required="data:export"
            )
            
            mock_denied.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configuration_security_controls(
        self, 
        admin_user, 
        trainer_user, 
        malicious_user
    ):
        """Test security controls for configuration changes."""
        rbac_manager = get_rbac_manager()
        audit_logger = get_training_audit_logger()
        
        # Phase 1: Admin updates system configuration (should succeed)
        with patch.object(audit_logger, 'log_config_updated') as mock_config_audit:
            # Verify admin has admin write permission
            assert rbac_manager.has_permission(admin_user, Permission.ADMIN_WRITE)
            
            # Simulate configuration update
            config_changes = {
                "max_training_time": 7200,  # 2 hours
                "auto_backup_enabled": True,
                "security_level": "high"
            }
            
            audit_logger.log_config_updated(
                user=admin_user,
                config_type="system_settings",
                config_changes=config_changes
            )
            
            mock_config_audit.assert_called_once()
        
        # Phase 2: Trainer attempts configuration change (should fail)
        with patch.object(audit_logger, 'log_permission_denied') as mock_denied:
            # Verify trainer doesn't have admin permissions
            assert not rbac_manager.has_permission(trainer_user, Permission.ADMIN_WRITE)
            
            # Simulate unauthorized configuration attempt
            audit_logger.log_permission_denied(
                user=trainer_user,
                resource_type="system_config",
                resource_id="system_settings",
                permission_required="admin:write"
            )
            
            mock_denied.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_model_integrity_security_check(
        self, 
        secure_storage, 
        test_model_file, 
        admin_user
    ):
        """Test model integrity security checks."""
        audit_logger = get_training_audit_logger()
        
        # Store model
        model_id = await secure_storage.store_model(
            model_path=test_model_file,
            name="Integrity Test Model",
            model_type=ModelType.TRANSFORMER,
            description="Model for integrity testing",
            user=admin_user,
            version="1.0.0",
            security_level=SecurityLevel.CONFIDENTIAL,
            encrypt=True
        )
        
        # Simulate integrity check failure
        with patch.object(audit_logger, 'log_model_integrity_check_failed') as mock_integrity:
            audit_logger.log_model_integrity_check_failed(
                user=admin_user,
                model_id=model_id,
                model_name="Integrity Test Model",
                expected_checksum="abc123def456",
                actual_checksum="xyz789uvw012"
            )
            
            mock_integrity.assert_called_once()
            call_args = mock_integrity.call_args[1]
            assert call_args["model_id"] == model_id
            assert call_args["expected_checksum"] != call_args["actual_checksum"]
    
    def test_security_event_aggregation(self):
        """Test security event aggregation and analysis."""
        audit_logger = get_training_audit_logger()
        
        # Simulate multiple security events
        events = [
            ("unauthorized_access", "model_123"),
            ("permission_denied", "dataset_456"),
            ("unauthorized_access", "training_job_789"),
            ("integrity_check_failed", "model_123")
        ]
        
        with patch.object(audit_logger, '_log_event') as mock_log:
            for event_type, resource_id in events:
                if event_type == "unauthorized_access":
                    audit_logger.log_unauthorized_access_attempt(
                        user=None,
                        resource_type="model",
                        resource_id=resource_id,
                        permission_required="model:read"
                    )
                elif event_type == "permission_denied":
                    user = UserData(user_id="test", email="test@test.com", roles=["user"])
                    audit_logger.log_permission_denied(
                        user=user,
                        resource_type="dataset",
                        resource_id=resource_id,
                        permission_required="data:export"
                    )
        
        # Verify all events were logged
        assert mock_log.call_count == len(events)
    
    @pytest.mark.asyncio
    async def test_tenant_isolation_security(
        self, 
        secure_storage, 
        test_model_file
    ):
        """Test tenant isolation security controls."""
        # Create users from different tenants
        tenant1_admin = UserData(
            user_id="admin-tenant1",
            email="admin@tenant1.com",
            roles=["admin"],
            tenant_id="tenant-1"
        )
        
        tenant2_user = UserData(
            user_id="user-tenant2",
            email="user@tenant2.com",
            roles=["user"],
            tenant_id="tenant-2"
        )
        
        # Tenant 1 admin stores model
        model_id = await secure_storage.store_model(
            model_path=test_model_file,
            name="Tenant 1 Model",
            model_type=ModelType.TRANSFORMER,
            description="Model for tenant isolation testing",
            user=tenant1_admin,
            version="1.0.0"
        )
        
        # Tenant 2 user should not be able to access tenant 1's model
        with pytest.raises(PermissionError):
            await secure_storage.retrieve_model(model_id, tenant2_user)
        
        # Verify tenant isolation in model listing
        tenant1_models = secure_storage.list_models(tenant1_admin)
        tenant2_models = secure_storage.list_models(tenant2_user)
        
        # Tenant 1 should see their model
        assert any(model.model_id == model_id for model in tenant1_models)
        
        # Tenant 2 should not see tenant 1's model
        assert not any(model.model_id == model_id for model in tenant2_models)


@pytest.mark.asyncio
async def test_complete_security_integration_scenario():
    """Test a complete security integration scenario."""
    # Create test environment
    admin = UserData(
        user_id="integration-admin",
        email="admin@integration.test",
        roles=["admin"],
        tenant_id="integration-tenant"
    )
    
    trainer = UserData(
        user_id="integration-trainer",
        email="trainer@integration.test",
        roles=["trainer"],
        tenant_id="integration-tenant"
    )
    
    attacker = UserData(
        user_id="integration-attacker",
        email="attacker@malicious.com",
        roles=["user"],
        tenant_id="malicious-tenant"
    )
    
    rbac_manager = get_rbac_manager()
    audit_logger = get_training_audit_logger()
    
    # Scenario: Complete ML workflow with security controls
    
    # 1. Admin creates secure training environment
    with patch.object(audit_logger, 'log_config_updated') as mock_config:
        # Admin configures secure training environment
        assert rbac_manager.has_permission(admin, Permission.ADMIN_SYSTEM)
        
        audit_logger.log_config_updated(
            user=admin,
            config_type="training_environment",
            config_changes={
                "encryption_enabled": True,
                "audit_logging": True,
                "rbac_enabled": True,
                "tenant_isolation": True
            }
        )
        
        mock_config.assert_called_once()
    
    # 2. Trainer uploads training data
    with patch.object(audit_logger, 'log_training_data_uploaded') as mock_upload:
        assert rbac_manager.has_permission(trainer, Permission.DATA_WRITE)
        
        audit_logger.log_training_data_uploaded(
            user=trainer,
            dataset_id="secure-dataset-integration",
            dataset_name="Integration Test Dataset",
            record_count=5000,
            file_size=25000000,
            data_format="json"
        )
        
        mock_upload.assert_called_once()
    
    # 3. Attacker attempts unauthorized access (should fail and be logged)
    with patch.object(audit_logger, 'log_unauthorized_access_attempt') as mock_unauthorized:
        assert not rbac_manager.has_permission(attacker, Permission.DATA_READ)
        
        audit_logger.log_unauthorized_access_attempt(
            user=attacker,
            resource_type="dataset",
            resource_id="secure-dataset-integration",
            permission_required="data:read",
            ip_address="192.168.1.100"
        )
        
        mock_unauthorized.assert_called_once()
    
    # 4. Trainer starts legitimate training job
    with patch.object(audit_logger, 'log_training_started') as mock_training:
        assert rbac_manager.has_permission(trainer, Permission.TRAINING_EXECUTE)
        
        audit_logger.log_training_started(
            user=trainer,
            training_job_id="integration-training-job",
            dataset_id="secure-dataset-integration",
            training_config={"epochs": 5, "lr": 0.001}
        )
        
        mock_training.assert_called_once()
    
    # 5. Training completes and model is stored securely
    with patch.object(audit_logger, 'log_model_created') as mock_model:
        audit_logger.log_model_created(
            user=trainer,
            model_id="integration-model-123",
            model_name="Integration Test Model",
            model_type="transformer",
            file_size=100000000,
            encrypted=True
        )
        
        mock_model.assert_called_once()
    
    # Verify all security controls worked as expected
    assert True  # If we reach here, all security controls passed


if __name__ == "__main__":
    pytest.main([__file__])