"""
Tests for RBAC Integration with Response Core Orchestrator

This module tests the Role-Based Access Control integration for training operations,
model management, and administrative features.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from ai_karen_engine.auth.rbac_middleware import (
    RBACManager, Permission, Role, get_rbac_manager,
    check_training_access, check_model_access, check_data_access,
    check_scheduler_access, check_admin_access
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.config import AuthConfig, JWTConfig
from ai_karen_engine.services.training_audit_logger import (
    get_training_audit_logger, TrainingEventType
)
from ai_karen_engine.core.response.secure_model_storage import (
    SecureModelStorage, ModelType, SecurityLevel
)


@pytest.fixture
def auth_config():
    """Create test auth configuration."""
    return AuthConfig(
        jwt=JWTConfig(
            secret_key="test-secret-key-for-rbac-testing",
            algorithm="HS256"
        )
    )


@pytest.fixture
def rbac_manager(auth_config):
    """Create RBAC manager for testing."""
    return RBACManager(auth_config)


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return UserData(
        user_id="admin-123",
        email="admin@test.com",
        full_name="Admin User",
        roles=["admin", "user"],
        tenant_id="test-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def trainer_user():
    """Create trainer user for testing."""
    return UserData(
        user_id="trainer-456",
        email="trainer@test.com",
        full_name="Trainer User",
        roles=["trainer", "user"],
        tenant_id="test-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return UserData(
        user_id="user-789",
        email="user@test.com",
        full_name="Regular User",
        roles=["user"],
        tenant_id="test-tenant",
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def readonly_user():
    """Create readonly user for testing."""
    return UserData(
        user_id="readonly-101",
        email="readonly@test.com",
        full_name="Readonly User",
        roles=["readonly"],
        tenant_id="test-tenant",
        is_verified=True,
        is_active=True
    )


class TestRBACManager:
    """Test RBAC manager functionality."""
    
    def test_get_user_permissions_admin(self, rbac_manager, admin_user):
        """Test admin user gets all permissions."""
        permissions = rbac_manager.get_user_permissions(admin_user)
        
        # Admin should have all permissions
        assert Permission.TRAINING_READ in permissions
        assert Permission.TRAINING_WRITE in permissions
        assert Permission.TRAINING_DELETE in permissions
        assert Permission.TRAINING_EXECUTE in permissions
        assert Permission.MODEL_READ in permissions
        assert Permission.MODEL_WRITE in permissions
        assert Permission.MODEL_DELETE in permissions
        assert Permission.MODEL_DEPLOY in permissions
        assert Permission.ADMIN_READ in permissions
        assert Permission.ADMIN_WRITE in permissions
        assert Permission.ADMIN_SYSTEM in permissions
    
    def test_get_user_permissions_trainer(self, rbac_manager, trainer_user):
        """Test trainer user gets appropriate permissions."""
        permissions = rbac_manager.get_user_permissions(trainer_user)
        
        # Trainer should have training and model permissions
        assert Permission.TRAINING_READ in permissions
        assert Permission.TRAINING_WRITE in permissions
        assert Permission.TRAINING_EXECUTE in permissions
        assert Permission.MODEL_READ in permissions
        assert Permission.MODEL_WRITE in permissions
        assert Permission.MODEL_DEPLOY in permissions
        assert Permission.DATA_READ in permissions
        assert Permission.DATA_WRITE in permissions
        
        # But not admin permissions
        assert Permission.ADMIN_READ not in permissions
        assert Permission.ADMIN_WRITE not in permissions
        assert Permission.ADMIN_SYSTEM not in permissions
    
    def test_get_user_permissions_regular_user(self, rbac_manager, regular_user):
        """Test regular user gets limited permissions."""
        permissions = rbac_manager.get_user_permissions(regular_user)
        
        # Regular user should have basic read permissions
        assert Permission.TRAINING_READ in permissions
        assert Permission.MODEL_READ in permissions
        assert Permission.DATA_READ in permissions
        
        # But not write or admin permissions
        assert Permission.TRAINING_WRITE not in permissions
        assert Permission.TRAINING_DELETE not in permissions
        assert Permission.MODEL_WRITE not in permissions
        assert Permission.MODEL_DELETE not in permissions
        assert Permission.ADMIN_READ not in permissions
    
    def test_get_user_permissions_readonly_user(self, rbac_manager, readonly_user):
        """Test readonly user gets minimal permissions."""
        permissions = rbac_manager.get_user_permissions(readonly_user)
        
        # Readonly user should have minimal read permissions
        assert Permission.TRAINING_READ in permissions
        assert Permission.MODEL_READ in permissions
        
        # But not data or admin permissions
        assert Permission.DATA_READ not in permissions
        assert Permission.TRAINING_WRITE not in permissions
        assert Permission.ADMIN_READ not in permissions
    
    def test_has_permission(self, rbac_manager, admin_user, regular_user):
        """Test permission checking."""
        # Admin should have all permissions
        assert rbac_manager.has_permission(admin_user, Permission.ADMIN_WRITE)
        assert rbac_manager.has_permission(admin_user, Permission.TRAINING_EXECUTE)
        
        # Regular user should not have admin permissions
        assert not rbac_manager.has_permission(regular_user, Permission.ADMIN_WRITE)
        assert not rbac_manager.has_permission(regular_user, Permission.TRAINING_WRITE)
        
        # But should have read permissions
        assert rbac_manager.has_permission(regular_user, Permission.TRAINING_READ)
    
    def test_has_role(self, rbac_manager, admin_user, trainer_user):
        """Test role checking."""
        assert rbac_manager.has_role(admin_user, Role.ADMIN)
        assert rbac_manager.has_role(trainer_user, Role.TRAINER)
        assert not rbac_manager.has_role(trainer_user, Role.ADMIN)
    
    def test_has_admin_role(self, rbac_manager, admin_user, trainer_user):
        """Test admin role checking."""
        assert rbac_manager.has_admin_role(admin_user)
        assert not rbac_manager.has_admin_role(trainer_user)
    
    @patch('ai_karen_engine.auth.rbac_middleware.get_audit_logger')
    def test_audit_access_attempt(self, mock_audit_logger, rbac_manager, admin_user):
        """Test access attempt auditing."""
        mock_logger = Mock()
        mock_audit_logger.return_value = mock_logger
        
        # Test granted access
        rbac_manager.audit_access_attempt(
            user_data=admin_user,
            permission=Permission.TRAINING_WRITE,
            resource="training_job_123",
            granted=True
        )
        
        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args[0][0]
        assert call_args["event_type"] == "access_granted"
        assert call_args["user_id"] == admin_user.user_id
        
        # Test denied access
        mock_logger.reset_mock()
        rbac_manager.audit_access_attempt(
            user_data=admin_user,
            permission=Permission.TRAINING_WRITE,
            resource="training_job_123",
            granted=False
        )
        
        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args[0][0]
        assert call_args["event_type"] == "access_denied"


class TestPermissionCheckers:
    """Test permission checking functions."""
    
    def test_check_training_access(self, admin_user, trainer_user, regular_user):
        """Test training access checking."""
        # Admin should have all training access
        assert check_training_access(admin_user, "read")
        assert check_training_access(admin_user, "write")
        assert check_training_access(admin_user, "delete")
        assert check_training_access(admin_user, "execute")
        
        # Trainer should have most training access
        assert check_training_access(trainer_user, "read")
        assert check_training_access(trainer_user, "write")
        assert check_training_access(trainer_user, "execute")
        
        # Regular user should have limited access
        assert check_training_access(regular_user, "read")
        assert not check_training_access(regular_user, "write")
        assert not check_training_access(regular_user, "delete")
        assert not check_training_access(regular_user, "execute")
    
    def test_check_model_access(self, admin_user, trainer_user, regular_user):
        """Test model access checking."""
        # Admin should have all model access
        assert check_model_access(admin_user, "read")
        assert check_model_access(admin_user, "write")
        assert check_model_access(admin_user, "delete")
        assert check_model_access(admin_user, "deploy")
        
        # Trainer should have most model access
        assert check_model_access(trainer_user, "read")
        assert check_model_access(trainer_user, "write")
        assert check_model_access(trainer_user, "deploy")
        
        # Regular user should have limited access
        assert check_model_access(regular_user, "read")
        assert not check_model_access(regular_user, "write")
        assert not check_model_access(regular_user, "delete")
        assert not check_model_access(regular_user, "deploy")
    
    def test_check_data_access(self, admin_user, trainer_user, regular_user):
        """Test data access checking."""
        # Admin should have all data access
        assert check_data_access(admin_user, "read")
        assert check_data_access(admin_user, "write")
        assert check_data_access(admin_user, "delete")
        assert check_data_access(admin_user, "export")
        
        # Trainer should have most data access
        assert check_data_access(trainer_user, "read")
        assert check_data_access(trainer_user, "write")
        assert check_data_access(trainer_user, "export")
        
        # Regular user should have limited access
        assert check_data_access(regular_user, "read")
        assert not check_data_access(regular_user, "write")
        assert not check_data_access(regular_user, "delete")
        assert not check_data_access(regular_user, "export")
    
    def test_check_admin_access(self, admin_user, trainer_user, regular_user):
        """Test admin access checking."""
        # Only admin should have admin access
        assert check_admin_access(admin_user, "read")
        assert check_admin_access(admin_user, "write")
        assert check_admin_access(admin_user, "system")
        
        # Others should not have admin access
        assert not check_admin_access(trainer_user, "read")
        assert not check_admin_access(trainer_user, "write")
        assert not check_admin_access(regular_user, "read")
        assert not check_admin_access(regular_user, "write")


class TestTrainingAuditLogger:
    """Test training audit logger functionality."""
    
    @pytest.fixture
    def audit_logger(self):
        """Create training audit logger for testing."""
        return get_training_audit_logger()
    
    @patch('ai_karen_engine.services.training_audit_logger.get_audit_logger')
    def test_log_training_started(self, mock_audit_logger, audit_logger, admin_user):
        """Test training started logging."""
        mock_logger = Mock()
        mock_audit_logger.return_value = mock_logger
        
        audit_logger.log_training_started(
            user=admin_user,
            training_job_id="job-123",
            model_id="model-456",
            dataset_id="dataset-789",
            training_config={"epochs": 10, "lr": 0.001}
        )
        
        # Verify audit event was logged
        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args[0][0]
        assert "training_operation" in call_args["event_type"]
        assert call_args["user_id"] == admin_user.user_id
        assert call_args["metadata"]["training_job_id"] == "job-123"
    
    @patch('ai_karen_engine.services.training_audit_logger.get_audit_logger')
    def test_log_model_created(self, mock_audit_logger, audit_logger, trainer_user):
        """Test model creation logging."""
        mock_logger = Mock()
        mock_audit_logger.return_value = mock_logger
        
        audit_logger.log_model_created(
            user=trainer_user,
            model_id="model-123",
            model_name="test-model",
            model_type="transformer",
            file_size=1024000,
            encrypted=True
        )
        
        # Verify audit event was logged
        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args[0][0]
        assert call_args["user_id"] == trainer_user.user_id
        assert call_args["metadata"]["model_name"] == "test-model"
        assert call_args["metadata"]["encrypted"] is True
    
    @patch('ai_karen_engine.services.training_audit_logger.get_audit_logger')
    def test_log_unauthorized_access_attempt(self, mock_audit_logger, audit_logger, regular_user):
        """Test unauthorized access logging."""
        mock_logger = Mock()
        mock_audit_logger.return_value = mock_logger
        
        audit_logger.log_unauthorized_access_attempt(
            user=regular_user,
            resource_type="model",
            resource_id="model-123",
            permission_required="model:delete",
            ip_address="192.168.1.100"
        )
        
        # Verify audit event was logged
        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args[0][0]
        assert call_args["user_id"] == regular_user.user_id
        assert call_args["metadata"]["permission_required"] == "model:delete"
        assert call_args["metadata"]["granted"] is False


class TestSecureModelStorage:
    """Test secure model storage functionality."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Create secure model storage for testing."""
        return SecureModelStorage(
            storage_path=str(tmp_path / "test_models"),
            encryption_key="test-encryption-key-32-bytes-long"
        )
    
    @pytest.fixture
    def test_model_file(self, tmp_path):
        """Create test model file."""
        model_file = tmp_path / "test_model.pkl"
        model_file.write_bytes(b"fake model data for testing")
        return model_file
    
    @pytest.mark.asyncio
    async def test_store_model_with_rbac(self, storage, test_model_file, admin_user):
        """Test model storage with RBAC integration."""
        model_id = await storage.store_model(
            model_path=test_model_file,
            name="Test Model",
            model_type=ModelType.TRANSFORMER,
            description="Test model for RBAC testing",
            user=admin_user,
            version="1.0.0",
            security_level=SecurityLevel.CONFIDENTIAL,
            encrypt=True
        )
        
        assert model_id is not None
        assert len(model_id) > 0
        
        # Verify metadata was stored
        metadata = storage.get_model_metadata(model_id, admin_user)
        assert metadata is not None
        assert metadata.name == "Test Model"
        assert metadata.created_by == admin_user.user_id
        assert metadata.tenant_id == admin_user.tenant_id
        assert metadata.encrypted is True
    
    @pytest.mark.asyncio
    async def test_retrieve_model_with_rbac(self, storage, test_model_file, admin_user, regular_user):
        """Test model retrieval with RBAC access control."""
        # Store model as admin
        model_id = await storage.store_model(
            model_path=test_model_file,
            name="Test Model",
            model_type=ModelType.TRANSFORMER,
            description="Test model for RBAC testing",
            user=admin_user,
            version="1.0.0",
            security_level=SecurityLevel.INTERNAL,
            encrypt=False
        )
        
        # Admin should be able to retrieve
        retrieved_path = await storage.retrieve_model(model_id, admin_user)
        assert retrieved_path.exists()
        
        # Regular user from same tenant should be able to retrieve
        retrieved_path_user = await storage.retrieve_model(model_id, regular_user)
        assert retrieved_path_user.exists()
        
        # User from different tenant should not be able to retrieve
        other_tenant_user = UserData(
            user_id="other-user",
            email="other@test.com",
            roles=["user"],
            tenant_id="other-tenant"
        )
        
        with pytest.raises(PermissionError):
            await storage.retrieve_model(model_id, other_tenant_user)
    
    @pytest.mark.asyncio
    async def test_delete_model_with_rbac(self, storage, test_model_file, admin_user, regular_user):
        """Test model deletion with RBAC access control."""
        # Store model as admin
        model_id = await storage.store_model(
            model_path=test_model_file,
            name="Test Model",
            model_type=ModelType.TRANSFORMER,
            description="Test model for RBAC testing",
            user=admin_user,
            version="1.0.0"
        )
        
        # Regular user should not be able to delete (not creator or admin)
        with pytest.raises(PermissionError):
            await storage.delete_model(model_id, regular_user)
        
        # Admin (creator) should be able to delete
        success = await storage.delete_model(model_id, admin_user)
        assert success is True
        
        # Model should no longer exist
        metadata = storage.get_model_metadata(model_id, admin_user)
        assert metadata is None
    
    def test_list_models_with_tenant_isolation(self, storage, admin_user):
        """Test model listing with tenant isolation."""
        # Create models for different tenants
        admin_user.tenant_id = "tenant-1"
        other_user = UserData(
            user_id="other-user",
            email="other@test.com",
            roles=["user"],
            tenant_id="tenant-2"
        )
        
        # Admin should only see models from their tenant
        models = storage.list_models(admin_user)
        for model in models:
            assert model.tenant_id == admin_user.tenant_id
        
        # Other user should only see models from their tenant
        other_models = storage.list_models(other_user)
        for model in other_models:
            assert model.tenant_id == other_user.tenant_id


@pytest.mark.asyncio
async def test_rbac_integration_end_to_end():
    """Test end-to-end RBAC integration."""
    # Create test users
    admin = UserData(
        user_id="admin-test",
        email="admin@test.com",
        roles=["admin"],
        tenant_id="test-tenant"
    )
    
    trainer = UserData(
        user_id="trainer-test",
        email="trainer@test.com",
        roles=["trainer"],
        tenant_id="test-tenant"
    )
    
    user = UserData(
        user_id="user-test",
        email="user@test.com",
        roles=["user"],
        tenant_id="test-tenant"
    )
    
    # Test permission hierarchy
    rbac_manager = get_rbac_manager()
    
    # Admin should have all permissions
    assert rbac_manager.has_permission(admin, Permission.ADMIN_SYSTEM)
    assert rbac_manager.has_permission(admin, Permission.TRAINING_EXECUTE)
    assert rbac_manager.has_permission(admin, Permission.MODEL_DELETE)
    
    # Trainer should have training permissions but not admin
    assert rbac_manager.has_permission(trainer, Permission.TRAINING_EXECUTE)
    assert rbac_manager.has_permission(trainer, Permission.MODEL_WRITE)
    assert not rbac_manager.has_permission(trainer, Permission.ADMIN_SYSTEM)
    
    # Regular user should have limited permissions
    assert rbac_manager.has_permission(user, Permission.TRAINING_READ)
    assert rbac_manager.has_permission(user, Permission.MODEL_READ)
    assert not rbac_manager.has_permission(user, Permission.TRAINING_WRITE)
    assert not rbac_manager.has_permission(user, Permission.MODEL_WRITE)
    assert not rbac_manager.has_permission(user, Permission.ADMIN_READ)


if __name__ == "__main__":
    pytest.main([__file__])