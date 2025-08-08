"""
Unit tests for password reset and user management features (Task 7).

This module tests the implementation of:
- Secure password reset token generation and validation
- User preference management and profile update capabilities
- Email verification and account activation features
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ai_karen_engine.auth.exceptions import (
    InvalidTokenError,
    PasswordValidationError,
    RateLimitExceededError,
    TokenExpiredError,
    UserNotFoundError,
)
from ai_karen_engine.auth.models import AuthEvent, AuthEventType, UserData

# Import the auth modules
from ai_karen_engine.auth.service import AuthConfig, AuthService


class TestPasswordResetFeatures:
    """Test password reset token generation and validation."""

    @pytest_asyncio.fixture
    async def auth_service(self):
        """Create a test auth service instance."""
        config = AuthConfig()
        config.features.enable_security_features = True
        config.features.enable_audit_logging = True

        service = AuthService(config)

        # Mock the database client and token manager
        service.core_auth.db_client = AsyncMock()
        service.core_auth.token_manager = AsyncMock()
        service.security_layer = AsyncMock()

        await service.initialize()
        return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return UserData(
            user_id="test-user-123",
            email="test@example.com",
            full_name="Test User",
            tenant_id="default",
            roles=["user"],
            is_verified=True,
            is_active=True,
        )

    async def test_create_password_reset_token_success(self, auth_service, sample_user):
        """Test successful password reset token creation."""
        # Setup mocks
        auth_service.core_auth.get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service.core_auth.token_manager.create_password_reset_token_with_storage = AsyncMock(
            return_value="reset-token-123"
        )
        auth_service.security_layer.check_rate_limit = AsyncMock(return_value=None)
        auth_service.security_layer.log_auth_event = AsyncMock(return_value=None)

        # Test token creation
        token = await auth_service.create_password_reset_token(
            email="test@example.com", ip_address="192.168.1.1", user_agent="test-agent"
        )

        # Verify results
        assert token == "reset-token-123"
        auth_service.core_auth.get_user_by_email.assert_called_once_with(
            "test@example.com"
        )
        auth_service.core_auth.token_manager.create_password_reset_token_with_storage.assert_called_once()
        auth_service.security_layer.check_rate_limit.assert_called_once()
        auth_service.security_layer.log_auth_event.assert_called_once()

    async def test_create_password_reset_token_user_not_found(self, auth_service):
        """Test password reset token creation when user doesn't exist."""
        # Setup mocks
        auth_service.core_auth.get_user_by_email = AsyncMock(return_value=None)
        auth_service.security_layer.log_auth_event = AsyncMock(return_value=None)

        # Test token creation
        token = await auth_service.create_password_reset_token(
            email="nonexistent@example.com",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify results - should return None but still log attempt
        assert token is None
        auth_service.core_auth.get_user_by_email.assert_called_once_with(
            "nonexistent@example.com"
        )
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify the logged event indicates failure
        call_args = auth_service.security_layer.log_auth_event.call_args[0][0]
        assert call_args.success is False
        assert call_args.error_message == "User not found"

    async def test_create_password_reset_token_rate_limited(
        self, auth_service, sample_user
    ):
        """Test password reset token creation when rate limited."""
        # Setup mocks
        auth_service.core_auth.get_user_by_email = AsyncMock(return_value=sample_user)
        auth_service.security_layer.check_rate_limit = AsyncMock(
            side_effect=RateLimitExceededError()
        )

        # Test token creation
        with pytest.raises(RateLimitExceededError):
            await auth_service.create_password_reset_token(
                email="test@example.com",
                ip_address="192.168.1.1",
                user_agent="test-agent",
            )

        # Verify rate limit was checked
        auth_service.security_layer.check_rate_limit.assert_called_once()

    async def test_verify_password_reset_token_success(self, auth_service, sample_user):
        """Test successful password reset token verification."""
        # Setup mocks
        auth_service.core_auth.token_manager.verify_password_reset_token_with_storage.return_value = (
            sample_user
        )
        auth_service.update_user_password = AsyncMock(return_value=True)
        auth_service.security_layer.log_auth_event.return_value = None

        # Test token verification
        result = await auth_service.verify_password_reset_token(
            token="reset-token-123",
            new_password="NewSecurePassword123!",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify results
        assert result is True
        auth_service.core_auth.token_manager.verify_password_reset_token_with_storage.assert_called_once()
        auth_service.update_user_password.assert_called_once_with(
            user_id=sample_user.user_id,
            new_password="NewSecurePassword123!",
            current_password=None,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )
        auth_service.security_layer.log_auth_event.assert_called_once()

    async def test_verify_password_reset_token_invalid_token(self, auth_service):
        """Test password reset token verification with invalid token."""
        # Setup mocks
        auth_service.core_auth.token_manager.verify_password_reset_token_with_storage.return_value = (
            None
        )
        auth_service.security_layer.log_auth_event.return_value = None

        # Test token verification
        result = await auth_service.verify_password_reset_token(
            token="invalid-token",
            new_password="NewSecurePassword123!",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify results
        assert result is False
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify the logged event indicates failure
        call_args = auth_service.security_layer.log_auth_event.call_args[0][0]
        assert call_args.success is False
        assert call_args.error_message == "Invalid or expired token"


class TestEmailVerificationFeatures:
    """Test email verification and account activation features."""

    @pytest_asyncio.fixture
    async def auth_service(self):
        """Create a test auth service instance."""
        config = AuthConfig()
        config.features.enable_security_features = True
        config.features.enable_audit_logging = True
        config.features.enable_email_verification = True

        service = AuthService(config)

        # Mock the database client and token manager
        service.core_auth.db_client = AsyncMock()
        service.core_auth.token_manager = AsyncMock()
        service.core_auth.get_user_by_id = AsyncMock()
        service.security_layer = AsyncMock()

        await service.initialize()
        return service

    @pytest.fixture
    def unverified_user(self):
        """Create an unverified user for testing."""
        return UserData(
            user_id="test-user-456",
            email="unverified@example.com",
            full_name="Unverified User",
            tenant_id="default",
            roles=["user"],
            is_verified=False,  # Not verified
            is_active=True,
        )

    @pytest.fixture
    def verified_user(self):
        """Create a verified user for testing."""
        return UserData(
            user_id="test-user-789",
            email="verified@example.com",
            full_name="Verified User",
            tenant_id="default",
            roles=["user"],
            is_verified=True,  # Already verified
            is_active=True,
        )

    async def test_create_email_verification_token_success(
        self, auth_service, unverified_user
    ):
        """Test successful email verification token creation."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = unverified_user
        auth_service.core_auth.token_manager.create_email_verification_token_with_storage.return_value = (
            "verify-token-123"
        )
        auth_service.security_layer.check_rate_limit.return_value = None
        auth_service.security_layer.log_auth_event.return_value = None

        # Test token creation
        token = await auth_service.create_email_verification_token(
            user_id="test-user-456", ip_address="192.168.1.1", user_agent="test-agent"
        )

        # Verify results
        assert token == "verify-token-123"
        auth_service.core_auth.get_user_by_id.assert_called_once_with("test-user-456")
        auth_service.core_auth.token_manager.create_email_verification_token_with_storage.assert_called_once()
        auth_service.security_layer.check_rate_limit.assert_called_once()
        auth_service.security_layer.log_auth_event.assert_called_once()

    async def test_create_email_verification_token_already_verified(
        self, auth_service, verified_user
    ):
        """Test email verification token creation for already verified user."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = verified_user

        # Test token creation
        token = await auth_service.create_email_verification_token(
            user_id="test-user-789", ip_address="192.168.1.1", user_agent="test-agent"
        )

        # Verify results - should return None for already verified user
        assert token is None
        auth_service.core_auth.get_user_by_id.assert_called_once_with("test-user-789")

    async def test_create_email_verification_token_user_not_found(self, auth_service):
        """Test email verification token creation when user doesn't exist."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id = AsyncMock(return_value=None)

        # Test token creation - should return None instead of raising exception
        # based on the actual implementation
        result = await auth_service.create_email_verification_token(
            user_id="nonexistent-user",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify result is None (user not found)
        assert result is None

    async def test_verify_email_address_success(self, auth_service, unverified_user):
        """Test successful email address verification."""
        # Setup mocks
        auth_service.core_auth.token_manager.verify_email_verification_token_with_storage.return_value = (
            unverified_user
        )
        auth_service.core_auth.db_client.update_user.return_value = None
        auth_service.security_layer.log_auth_event.return_value = None

        # Test email verification
        result = await auth_service.verify_email_address(
            token="verify-token-123", ip_address="192.168.1.1", user_agent="test-agent"
        )

        # Verify results
        assert result is True
        auth_service.core_auth.token_manager.verify_email_verification_token_with_storage.assert_called_once()
        auth_service.core_auth.db_client.update_user.assert_called_once()
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify user was marked as verified
        updated_user = auth_service.core_auth.db_client.update_user.call_args[0][0]
        assert updated_user.is_verified is True

    async def test_verify_email_address_invalid_token(self, auth_service):
        """Test email address verification with invalid token."""
        # Setup mocks
        auth_service.core_auth.token_manager.verify_email_verification_token_with_storage.return_value = (
            None
        )
        auth_service.security_layer.log_auth_event.return_value = None

        # Test email verification
        result = await auth_service.verify_email_address(
            token="invalid-token", ip_address="192.168.1.1", user_agent="test-agent"
        )

        # Verify results
        assert result is False
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify the logged event indicates failure
        call_args = auth_service.security_layer.log_auth_event.call_args[0][0]
        assert call_args.success is False
        assert "Invalid or expired verification token" in call_args.error_message


class TestUserManagementFeatures:
    """Test user preference management and profile update capabilities."""

    @pytest_asyncio.fixture
    async def auth_service(self):
        """Create a test auth service instance."""
        config = AuthConfig()
        config.features.enable_security_features = True
        config.features.enable_audit_logging = True

        service = AuthService(config)

        # Mock the database client
        service.core_auth.db_client = AsyncMock()
        service.core_auth.get_user_by_id = AsyncMock()
        service.security_layer = AsyncMock()

        await service.initialize()
        return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return UserData(
            user_id="test-user-999",
            email="user@example.com",
            full_name="Sample User",
            tenant_id="default",
            roles=["user"],
            preferences={"theme": "dark", "language": "en"},
            is_verified=True,
            is_active=True,
        )

    async def test_update_user_preferences_success(self, auth_service, sample_user):
        """Test successful user preferences update."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = sample_user
        auth_service.core_auth.db_client.update_user.return_value = None

        # Test preferences update
        new_preferences = {"theme": "light", "notifications": True}
        result = await auth_service.update_user_preferences(
            user_id="test-user-999", preferences=new_preferences
        )

        # Verify results
        assert result is True
        auth_service.core_auth.get_user_by_id.assert_called_once_with("test-user-999")
        auth_service.core_auth.db_client.update_user.assert_called_once()

        # Verify preferences were merged correctly
        updated_user = auth_service.core_auth.db_client.update_user.call_args[0][0]
        expected_preferences = {
            "theme": "light",
            "language": "en",
            "notifications": True,
        }
        assert updated_user.preferences == expected_preferences

    async def test_update_user_preferences_user_not_found(self, auth_service):
        """Test user preferences update when user doesn't exist."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = None

        # Test preferences update
        with pytest.raises(UserNotFoundError):
            await auth_service.update_user_preferences(
                user_id="nonexistent-user", preferences={"theme": "light"}
            )

    async def test_update_user_profile_success(self, auth_service, sample_user):
        """Test successful user profile update."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = sample_user
        auth_service.core_auth.db_client.update_user.return_value = None
        auth_service.security_layer.log_auth_event.return_value = None

        # Test profile update
        result = await auth_service.update_user_profile(
            user_id="test-user-999",
            full_name="Updated Name",
            preferences={"timezone": "UTC"},
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify results
        assert result is True
        auth_service.core_auth.get_user_by_id.assert_called_once_with("test-user-999")
        auth_service.core_auth.db_client.update_user.assert_called_once()
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify profile was updated correctly
        updated_user = auth_service.core_auth.db_client.update_user.call_args[0][0]
        assert updated_user.full_name == "Updated Name"
        assert "timezone" in updated_user.preferences
        assert updated_user.preferences["timezone"] == "UTC"

    async def test_update_user_profile_user_not_found(self, auth_service):
        """Test user profile update when user doesn't exist."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = None

        # Test profile update
        with pytest.raises(UserNotFoundError):
            await auth_service.update_user_profile(
                user_id="nonexistent-user", full_name="New Name"
            )

    async def test_deactivate_user_success(self, auth_service, sample_user):
        """Test successful user deactivation."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = sample_user
        auth_service.core_auth.db_client.update_user.return_value = None
        auth_service.security_layer.log_auth_event.return_value = None

        # Test user deactivation
        result = await auth_service.deactivate_user(
            user_id="test-user-999",
            reason="account_closure",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify results
        assert result is True
        auth_service.core_auth.get_user_by_id.assert_called_once_with("test-user-999")
        auth_service.core_auth.db_client.update_user.assert_called_once()
        auth_service.security_layer.log_auth_event.assert_called_once()

        # Verify user was deactivated
        updated_user = auth_service.core_auth.db_client.update_user.call_args[0][0]
        assert updated_user.is_active is False

        # Verify the logged event
        call_args = auth_service.security_layer.log_auth_event.call_args[0][0]
        assert call_args.event_type == AuthEventType.USER_DEACTIVATED
        assert call_args.success is True
        assert call_args.details["reason"] == "account_closure"

    async def test_deactivate_user_not_found(self, auth_service):
        """Test user deactivation when user doesn't exist."""
        # Setup mocks
        auth_service.core_auth.get_user_by_id.return_value = None

        # Test user deactivation
        with pytest.raises(UserNotFoundError):
            await auth_service.deactivate_user(
                user_id="nonexistent-user", reason="test"
            )


class TestTokenManagerEnhancements:
    """Test the enhanced token manager functionality."""

    @pytest.fixture
    def token_manager(self):
        """Create a test token manager instance."""
        from ai_karen_engine.auth.config import JWTConfig
        from ai_karen_engine.auth.tokens import TokenManager

        config = JWTConfig()
        config.secret_key = "test-secret-key-for-testing-only"
        config.password_reset_token_expire_hours = 1
        config.email_verification_token_expire_hours = 24

        return TokenManager(config)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return UserData(
            user_id="test-user-token",
            email="token@example.com",
            full_name="Token User",
            tenant_id="default",
            roles=["user"],
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def mock_db_client(self):
        """Create a mock database client."""
        return AsyncMock()

    async def test_create_password_reset_token_with_storage(
        self, token_manager, sample_user, mock_db_client
    ):
        """Test password reset token creation with database storage."""
        # Mock database storage
        mock_db_client.store_password_reset_token.return_value = None

        # Create token
        token = await token_manager.create_password_reset_token_with_storage(
            user_data=sample_user,
            db_client=mock_db_client,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify token was created
        assert token is not None
        assert isinstance(token, str)

        # Verify database storage was called
        mock_db_client.store_password_reset_token.assert_called_once()
        call_args = mock_db_client.store_password_reset_token.call_args
        assert call_args[1]["user_id"] == sample_user.user_id
        assert call_args[1]["ip_address"] == "192.168.1.1"
        assert call_args[1]["user_agent"] == "test-agent"

    async def test_verify_password_reset_token_with_storage_success(
        self, token_manager, sample_user, mock_db_client
    ):
        """Test successful password reset token verification with database storage."""
        # Create a token first
        token = await token_manager.create_password_reset_token_with_storage(
            user_data=sample_user,
            db_client=mock_db_client,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Mock database responses for verification
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        mock_db_client.get_password_reset_token.return_value = {
            "token_id": "test-token-id",
            "user_id": sample_user.user_id,
            "token_hash": token_hash,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "used_at": None,
            "ip_address": "192.168.1.1",
            "user_agent": "test-agent",
        }
        mock_db_client.mark_password_reset_token_used.return_value = None
        mock_db_client.get_user_by_id.return_value = sample_user

        # Verify token
        verified_user = await token_manager.verify_password_reset_token_with_storage(
            token=token, db_client=mock_db_client
        )

        # Verify results
        assert verified_user is not None
        assert verified_user.user_id == sample_user.user_id
        assert verified_user.email == sample_user.email

        # Verify database calls
        mock_db_client.get_password_reset_token.assert_called_once()
        mock_db_client.mark_password_reset_token_used.assert_called_once()
        mock_db_client.get_user_by_id.assert_called_once_with(sample_user.user_id)

    async def test_verify_password_reset_token_with_storage_invalid_token(
        self, token_manager, mock_db_client
    ):
        """Test password reset token verification with invalid token."""
        # Mock database response for non-existent token
        mock_db_client.get_password_reset_token.return_value = None

        # Try to verify invalid token
        verified_user = await token_manager.verify_password_reset_token_with_storage(
            token="invalid-token", db_client=mock_db_client
        )

        # Verify results
        assert verified_user is None

    async def test_create_email_verification_token_with_storage(
        self, token_manager, sample_user, mock_db_client
    ):
        """Test email verification token creation with database storage."""
        # Mock database storage
        mock_db_client.store_email_verification_token.return_value = None

        # Create token
        token = await token_manager.create_email_verification_token_with_storage(
            user_data=sample_user,
            db_client=mock_db_client,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Verify token was created
        assert token is not None
        assert isinstance(token, str)

        # Verify database storage was called
        mock_db_client.store_email_verification_token.assert_called_once()
        call_args = mock_db_client.store_email_verification_token.call_args
        assert call_args[1]["user_id"] == sample_user.user_id
        assert call_args[1]["ip_address"] == "192.168.1.1"
        assert call_args[1]["user_agent"] == "test-agent"


class TestDatabaseTokenStorage:
    """Test database token storage functionality."""

    @pytest.fixture
    def db_client(self):
        """Create a test database client."""
        from ai_karen_engine.auth.config import DatabaseConfig
        from ai_karen_engine.auth.database import DatabaseClient

        config = DatabaseConfig()
        config.database_url = "sqlite:///:memory:"  # In-memory database for testing

        return DatabaseClient(config)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return "test-user-db-123"

    async def test_store_and_retrieve_password_reset_token(
        self, db_client, sample_user_id
    ):
        """Test storing and retrieving password reset tokens."""
        token_id = "test-token-id-123"
        token_hash = "test-token-hash-456"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store token
        await db_client.store_password_reset_token(
            token_id=token_id,
            user_id=sample_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Retrieve token
        stored_token = await db_client.get_password_reset_token(token_id)

        # Verify results
        assert stored_token is not None
        assert stored_token["token_id"] == token_id
        assert stored_token["user_id"] == sample_user_id
        assert stored_token["token_hash"] == token_hash
        assert stored_token["used_at"] is None
        assert stored_token["ip_address"] == "192.168.1.1"
        assert stored_token["user_agent"] == "test-agent"

    async def test_mark_password_reset_token_used(self, db_client, sample_user_id):
        """Test marking password reset token as used."""
        token_id = "test-token-used-123"
        token_hash = "test-token-hash-used"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store token
        await db_client.store_password_reset_token(
            token_id=token_id,
            user_id=sample_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Mark as used
        await db_client.mark_password_reset_token_used(token_id)

        # Retrieve token - should return None since it's used
        stored_token = await db_client.get_password_reset_token(token_id)
        assert stored_token is None

    async def test_cleanup_expired_password_reset_tokens(
        self, db_client, sample_user_id
    ):
        """Test cleanup of expired password reset tokens."""
        # Store expired token
        expired_token_id = "expired-token-123"
        expired_expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

        await db_client.store_password_reset_token(
            token_id=expired_token_id,
            user_id=sample_user_id,
            token_hash="expired-hash",
            expires_at=expired_expires_at,
        )

        # Store valid token
        valid_token_id = "valid-token-123"
        valid_expires_at = datetime.utcnow() + timedelta(hours=1)  # Still valid

        await db_client.store_password_reset_token(
            token_id=valid_token_id,
            user_id=sample_user_id,
            token_hash="valid-hash",
            expires_at=valid_expires_at,
        )

        # Cleanup expired tokens
        deleted_count = await db_client.cleanup_expired_password_reset_tokens()

        # Verify results
        assert deleted_count == 1

        # Verify expired token is gone
        expired_token = await db_client.get_password_reset_token(expired_token_id)
        assert expired_token is None

        # Verify valid token still exists
        valid_token = await db_client.get_password_reset_token(valid_token_id)
        assert valid_token is not None

    async def test_store_and_retrieve_email_verification_token(
        self, db_client, sample_user_id
    ):
        """Test storing and retrieving email verification tokens."""
        token_id = "verify-token-id-123"
        token_hash = "verify-token-hash-456"
        expires_at = datetime.utcnow() + timedelta(days=1)

        # Store token
        await db_client.store_email_verification_token(
            token_id=token_id,
            user_id=sample_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        # Retrieve token
        stored_token = await db_client.get_email_verification_token(token_id)

        # Verify results
        assert stored_token is not None
        assert stored_token["token_id"] == token_id
        assert stored_token["user_id"] == sample_user_id
        assert stored_token["token_hash"] == token_hash
        assert stored_token["used_at"] is None
        assert stored_token["ip_address"] == "192.168.1.1"
        assert stored_token["user_agent"] == "test-agent"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
