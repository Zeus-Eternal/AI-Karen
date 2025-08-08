"""
Comprehensive unit tests for the main AuthService interface.

This test suite verifies all core authentication methods, user management,
session handling, and the orchestration between different authentication layers.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_karen_engine.auth import (
    AnomalyDetectedError,
    AuthEvent,
    AuthEventType,
    InvalidCredentialsError,
    PasswordValidationError,
    RateLimitExceededError,
    SecurityError,
    SessionData,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserData,
    UserNotFoundError,
)
from ai_karen_engine.auth.service import AuthConfig, AuthService


class TestAuthService:
    """Test suite for the main AuthService interface."""

    @pytest.fixture
    def auth_config(self) -> AuthConfig:
        """Create test authentication configuration."""
        config = AuthConfig()
        config.database.database_url = "sqlite:///:memory:"
        config.features.enable_security_features = True
        config.features.enable_intelligent_auth = False  # Disable for basic tests
        config.security.enable_rate_limiting = True
        config.security.enable_audit_logging = True
        config.jwt.secret_key = "test-secret-key"
        return config

    @pytest.fixture
    def auth_config_with_intelligence(self) -> AuthConfig:
        """Create test configuration with intelligence features enabled."""
        config = AuthConfig()
        config.database.database_url = "sqlite:///:memory:"
        config.features.enable_security_features = True
        config.features.enable_intelligent_auth = True
        config.features.enable_anomaly_detection = True
        config.features.enable_behavioral_analysis = True
        config.security.enable_rate_limiting = True
        config.security.enable_audit_logging = True
        config.jwt.secret_key = "test-secret-key"
        return config

    @pytest.fixture
    def sample_user_data(self) -> UserData:
        """Create sample user data for testing."""
        return UserData(
            user_id="test-user-123",
            email="test@example.com",
            full_name="Test User",
            roles=["user"],
            tenant_id="test-tenant",
            preferences={"theme": "dark"},
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def sample_session_data(self, sample_user_data: UserData) -> SessionData:
        """Create sample session data for testing."""
        return SessionData(
            session_token="test-session-token",
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            user_data=sample_user_data,
            expires_in=3600,
            ip_address="192.168.1.1",
            user_agent="Test User Agent",
        )

    @pytest.mark.asyncio
    async def test_auth_service_initialization(self, auth_config: AuthConfig):
        """Test AuthService initialization with different configurations."""
        # Test basic initialization
        auth_service = AuthService(auth_config)
        assert auth_service.config == auth_config
        assert auth_service.core_auth is not None
        assert auth_service.security_layer is not None
        assert auth_service.intelligence_layer is None
        assert not auth_service._initialized

        # Test initialization
        await auth_service.initialize()
        assert auth_service._initialized

        # Test double initialization (should not raise error)
        await auth_service.initialize()
        assert auth_service._initialized

    @pytest.mark.asyncio
    async def test_auth_service_initialization_with_intelligence(
        self, auth_config_with_intelligence: AuthConfig
    ):
        """Test AuthService initialization with intelligence features."""
        auth_service = AuthService(auth_config_with_intelligence)
        assert auth_service.intelligence_layer is not None

        await auth_service.initialize()
        assert auth_service._initialized

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_config: AuthConfig):
        """Test successful user authentication."""
        auth_service = AuthService(auth_config)

        # Mock the core authenticator
        mock_user_data = UserData(
            user_id="test-user", email="test@example.com", full_name="Test User"
        )

        with patch.object(
            auth_service.core_auth, "authenticate_user", new_callable=AsyncMock
        ) as mock_auth:
            mock_auth.return_value = mock_user_data

            with patch.object(
                auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
            ) as mock_rate_limit:
                mock_rate_limit.return_value = True

                with patch.object(
                    auth_service.security_layer,
                    "record_successful_attempt",
                    new_callable=AsyncMock,
                ) as mock_record:
                    result = await auth_service.authenticate_user(
                        email="test@example.com",
                        password="test-password",
                        ip_address="192.168.1.1",
                        user_agent="Test Agent",
                    )

                    assert result == mock_user_data
                    mock_auth.assert_called_once()
                    mock_rate_limit.assert_called_once()
                    mock_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_config: AuthConfig):
        """Test authentication with invalid credentials."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "authenticate_user", new_callable=AsyncMock
        ) as mock_auth:
            mock_auth.side_effect = InvalidCredentialsError("Invalid credentials")

            with patch.object(
                auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
            ) as mock_rate_limit:
                mock_rate_limit.return_value = True

                with patch.object(
                    auth_service.security_layer,
                    "record_failed_attempt",
                    new_callable=AsyncMock,
                ) as mock_record:
                    with pytest.raises(InvalidCredentialsError):
                        await auth_service.authenticate_user(
                            email="test@example.com",
                            password="wrong-password",
                            ip_address="192.168.1.1",
                        )

                    mock_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_rate_limited(self, auth_config: AuthConfig):
        """Test authentication blocked by rate limiting."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
        ) as mock_rate_limit:
            mock_rate_limit.side_effect = RateLimitExceededError("Rate limit exceeded")

            with pytest.raises(RateLimitExceededError):
                await auth_service.authenticate_user(
                    email="test@example.com",
                    password="test-password",
                    ip_address="192.168.1.1",
                )

    @pytest.mark.asyncio
    async def test_authenticate_user_with_intelligence_block(
        self, auth_config_with_intelligence: AuthConfig
    ):
        """Test authentication blocked by intelligence system."""
        auth_service = AuthService(auth_config_with_intelligence)

        # Mock intelligence result that recommends blocking
        mock_intelligence_result = MagicMock()
        mock_intelligence_result.should_block = True
        mock_intelligence_result.risk_score = 0.9
        mock_intelligence_result.anomaly_result = MagicMock()
        mock_intelligence_result.anomaly_result.anomaly_types = ["unusual_location"]
        mock_intelligence_result.to_dict.return_value = {"risk_score": 0.9}

        with patch.object(
            auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
        ):
            with patch.object(
                auth_service.core_auth, "get_user_by_email", new_callable=AsyncMock
            ) as mock_get_user:
                mock_get_user.return_value = UserData(
                    user_id="test", email="test@example.com"
                )

                with patch.object(
                    auth_service.intelligence_layer,
                    "analyze_login_attempt",
                    new_callable=AsyncMock,
                ) as mock_analyze:
                    mock_analyze.return_value = mock_intelligence_result

                    with pytest.raises(AnomalyDetectedError):
                        await auth_service.authenticate_user(
                            email="test@example.com",
                            password="test-password",
                            ip_address="192.168.1.1",
                        )

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test successful session creation."""
        auth_service = AuthService(auth_config)

        mock_session_data = SessionData(
            session_token="test-token",
            access_token="access-token",
            refresh_token="refresh-token",
            user_data=sample_user_data,
            expires_in=3600,
        )

        with patch.object(
            auth_service.core_auth, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_session_data

            with patch.object(
                auth_service.security_layer,
                "validate_session_security",
                new_callable=AsyncMock,
            ) as mock_validate:
                mock_validate.return_value = {
                    "valid": True,
                    "security_flags": [],
                    "risk_score": 0.1,
                    "warnings": [],
                }

                with patch.object(
                    auth_service.security_layer,
                    "log_session_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    result = await auth_service.create_session(
                        user_data=sample_user_data,
                        ip_address="192.168.1.1",
                        user_agent="Test Agent",
                    )

                    assert result.session_token == "test-token"
                    assert result.risk_score == 0.1
                    mock_create.assert_called_once()
                    mock_validate.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_session_success(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test successful session validation."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "validate_session", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = sample_user_data

            with patch.object(
                auth_service.core_auth.session_manager.store,
                "get_session",
                new_callable=AsyncMock,
            ) as mock_get_session:
                mock_session = SessionData(
                    session_token="test-token",
                    access_token="access-token",
                    refresh_token="refresh-token",
                    user_data=sample_user_data,
                    expires_in=3600,
                )
                mock_get_session.return_value = mock_session

                with patch.object(
                    auth_service.security_layer,
                    "validate_session_security",
                    new_callable=AsyncMock,
                ) as mock_security:
                    mock_security.return_value = {
                        "valid": True,
                        "security_flags": ["ip_changed"],
                        "risk_score": 0.3,
                        "warnings": [],
                    }

                    with patch.object(
                        auth_service.core_auth.session_manager.store,
                        "update_session",
                        new_callable=AsyncMock,
                    ) as mock_update:
                        result = await auth_service.validate_session(
                            session_token="test-token",
                            ip_address="192.168.1.2",
                            user_agent="Test Agent",
                        )

                        assert result == sample_user_data
                        mock_validate.assert_called_once()
                        mock_security.assert_called_once()
                        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_session_security_failure(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test session validation failure due to security checks."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "validate_session", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = sample_user_data

            with patch.object(
                auth_service.core_auth.session_manager.store,
                "get_session",
                new_callable=AsyncMock,
            ) as mock_get_session:
                mock_session = SessionData(
                    session_token="test-token",
                    access_token="access-token",
                    refresh_token="refresh-token",
                    user_data=sample_user_data,
                    expires_in=3600,
                )
                mock_get_session.return_value = mock_session

                with patch.object(
                    auth_service.security_layer,
                    "validate_session_security",
                    new_callable=AsyncMock,
                ) as mock_security:
                    mock_security.return_value = {
                        "valid": False,
                        "security_flags": ["suspicious_activity"],
                        "risk_score": 0.9,
                        "warnings": ["High risk session"],
                    }

                    with patch.object(
                        auth_service, "invalidate_session", new_callable=AsyncMock
                    ) as mock_invalidate:
                        with pytest.raises(SecurityError):
                            await auth_service.validate_session(
                                session_token="test-token",
                                ip_address="192.168.1.100",
                                user_agent="Suspicious Agent",
                            )

                        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_session_success(self, auth_config: AuthConfig):
        """Test successful session invalidation."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "invalidate_session", new_callable=AsyncMock
        ) as mock_invalidate:
            mock_invalidate.return_value = True

            with patch.object(
                auth_service.core_auth.session_manager.store,
                "get_session",
                new_callable=AsyncMock,
            ) as mock_get_session:
                mock_session = SessionData(
                    session_token="test-token",
                    access_token="access-token",
                    refresh_token="refresh-token",
                    user_data=UserData(user_id="test", email="test@example.com"),
                    expires_in=3600,
                )
                mock_get_session.return_value = mock_session

                with patch.object(
                    auth_service.security_layer,
                    "log_session_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    result = await auth_service.invalidate_session(
                        session_token="test-token", reason="manual_logout"
                    )

                    assert result is True
                    mock_invalidate.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_config: AuthConfig):
        """Test successful user creation."""
        auth_service = AuthService(auth_config)

        mock_user_data = UserData(
            user_id="new-user-123", email="newuser@example.com", full_name="New User"
        )

        with patch.object(
            auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
        ) as mock_rate_limit:
            mock_rate_limit.return_value = True

            with patch.object(
                auth_service.core_auth, "create_user", new_callable=AsyncMock
            ) as mock_create:
                mock_create.return_value = mock_user_data

                with patch.object(
                    auth_service.security_layer,
                    "log_auth_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    result = await auth_service.create_user(
                        email="newuser@example.com",
                        password="secure-password",
                        full_name="New User",
                        ip_address="192.168.1.1",
                    )

                    assert result == mock_user_data
                    mock_rate_limit.assert_called_once()
                    mock_create.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, auth_config: AuthConfig):
        """Test user creation when user already exists."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
        ) as mock_rate_limit:
            mock_rate_limit.return_value = True

            with patch.object(
                auth_service.core_auth, "create_user", new_callable=AsyncMock
            ) as mock_create:
                mock_create.side_effect = UserAlreadyExistsError(
                    email="existing@example.com"
                )

                with patch.object(
                    auth_service.security_layer,
                    "log_auth_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    with pytest.raises(UserAlreadyExistsError):
                        await auth_service.create_user(
                            email="existing@example.com",
                            password="password",
                            ip_address="192.168.1.1",
                        )

                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_password_success(self, auth_config: AuthConfig):
        """Test successful password update."""
        auth_service = AuthService(auth_config)

        mock_user_data = UserData(
            user_id="test-user", email="test@example.com", tenant_id="test-tenant"
        )

        with patch.object(
            auth_service.core_auth, "update_user_password", new_callable=AsyncMock
        ) as mock_update:
            mock_update.return_value = True

            with patch.object(
                auth_service.core_auth, "get_user_by_id", new_callable=AsyncMock
            ) as mock_get_user:
                mock_get_user.return_value = mock_user_data

                with patch.object(
                    auth_service.security_layer,
                    "log_auth_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    result = await auth_service.update_user_password(
                        user_id="test-user",
                        new_password="new-secure-password",
                        current_password="old-password",
                        ip_address="192.168.1.1",
                    )

                    assert result is True
                    mock_update.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test getting user by ID."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "get_user_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user_data

            result = await auth_service.get_user_by_id("test-user-123")

            assert result == sample_user_data
            mock_get.assert_called_once_with("test-user-123")

    @pytest.mark.asyncio
    async def test_get_user_by_email(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test getting user by email."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "get_user_by_email", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user_data

            result = await auth_service.get_user_by_email("test@example.com")

            assert result == sample_user_data
            mock_get.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_update_user_preferences(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test updating user preferences."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "get_user_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user_data

            with patch.object(
                auth_service.core_auth.db_client, "update_user", new_callable=AsyncMock
            ) as mock_update:
                result = await auth_service.update_user_preferences(
                    user_id="test-user-123",
                    preferences={"theme": "light", "language": "en"},
                )

                assert result is True
                assert sample_user_data.preferences["theme"] == "light"
                assert sample_user_data.preferences["language"] == "en"
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_password_reset_token(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test creating password reset token."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "get_user_by_email", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user_data

            with patch.object(
                auth_service.security_layer, "check_rate_limit", new_callable=AsyncMock
            ) as mock_rate_limit:
                mock_rate_limit.return_value = True

                with patch.object(
                    auth_service.core_auth.token_manager,
                    "create_password_reset_token_with_storage",
                    new_callable=AsyncMock,
                ) as mock_create_token:
                    mock_create_token.return_value = "reset-token-123"

                    with patch.object(
                        auth_service.security_layer,
                        "log_auth_event",
                        new_callable=AsyncMock,
                    ) as mock_log:
                        result = await auth_service.create_password_reset_token(
                            email="test@example.com", ip_address="192.168.1.1"
                        )

                        assert result == "reset-token-123"
                        mock_create_token.assert_called_once()
                        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_password_reset_token_user_not_found(
        self, auth_config: AuthConfig
    ):
        """Test creating password reset token for non-existent user."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth, "get_user_by_email", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await auth_service.create_password_reset_token(
                email="nonexistent@example.com", ip_address="192.168.1.1"
            )

            # Should return None without revealing user doesn't exist
            assert result is None

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_success(
        self, auth_config: AuthConfig, sample_user_data: UserData
    ):
        """Test successful password reset token verification."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth.token_manager,
            "verify_password_reset_token_with_storage",
            new_callable=AsyncMock,
        ) as mock_verify:
            mock_verify.return_value = sample_user_data

            with patch.object(
                auth_service, "update_user_password", new_callable=AsyncMock
            ) as mock_update:
                mock_update.return_value = True

                with patch.object(
                    auth_service.security_layer,
                    "log_auth_event",
                    new_callable=AsyncMock,
                ) as mock_log:
                    result = await auth_service.verify_password_reset_token(
                        token="reset-token-123",
                        new_password="new-secure-password",
                        ip_address="192.168.1.1",
                    )

                    assert result is True
                    mock_verify.assert_called_once()
                    mock_update.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_stats(self, auth_config: AuthConfig):
        """Test getting service statistics."""
        auth_service = AuthService(auth_config)

        mock_security_stats = {"rate_limiter": {"active": True}}

        with patch.object(
            auth_service.security_layer, "get_stats", new_callable=AsyncMock
        ) as mock_security_stats_method:
            mock_security_stats_method.return_value = mock_security_stats

            stats = await auth_service.get_service_stats()

            assert stats["service_name"] == auth_config.service_name
            assert stats["initialized"] == auth_service._initialized
            assert stats["features"]["security_enabled"] is True
            assert stats["features"]["intelligence_enabled"] is False
            assert stats["security"] == mock_security_stats

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, auth_config: AuthConfig):
        """Test health check when all components are healthy."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth.db_client, "health_check", new_callable=AsyncMock
        ) as mock_db_health:
            mock_db_health.return_value = True

            with patch.object(
                auth_service.security_layer, "get_stats", new_callable=AsyncMock
            ) as mock_security_stats:
                mock_security_stats.return_value = {"status": "healthy"}

                health = await auth_service.health_check()

                assert health["status"] == "healthy"
                assert health["components"]["database"]["status"] == "healthy"
                assert health["components"]["security"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, auth_config: AuthConfig):
        """Test health check when some components are unhealthy."""
        auth_service = AuthService(auth_config)

        with patch.object(
            auth_service.core_auth.db_client, "health_check", new_callable=AsyncMock
        ) as mock_db_health:
            mock_db_health.side_effect = Exception("Database connection failed")

            with patch.object(
                auth_service.security_layer, "get_stats", new_callable=AsyncMock
            ) as mock_security_stats:
                mock_security_stats.return_value = {"status": "healthy"}

                health = await auth_service.health_check()

                assert health["status"] == "degraded"
                assert health["components"]["database"]["status"] == "unhealthy"
                assert (
                    "Database connection failed"
                    in health["components"]["database"]["error"]
                )


class TestAuthServiceFactoryFunctions:
    """Test suite for AuthService factory functions."""

    @pytest.mark.asyncio
    async def test_create_auth_service(self):
        """Test creating AuthService with factory function."""
        config = AuthConfig()
        config.database.database_url = "sqlite:///:memory:"

        with patch("ai_karen_engine.auth.service.AuthService") as MockAuthService:
            mock_service = AsyncMock()
            MockAuthService.return_value = mock_service

            from ai_karen_engine.auth.service import create_auth_service

            result = await create_auth_service(config)

            MockAuthService.assert_called_once_with(config)
            mock_service.initialize.assert_called_once()
            assert result == mock_service

    @pytest.mark.asyncio
    async def test_get_auth_service_creates_global_instance(self):
        """Test that get_auth_service creates and reuses global instance."""
        # Reset global instance
        import ai_karen_engine.auth.service as service_module
        from ai_karen_engine.auth.service import _global_auth_service, get_auth_service

        service_module._global_auth_service = None

        config = AuthConfig()
        config.database.database_url = "sqlite:///:memory:"

        with patch("ai_karen_engine.auth.service.create_auth_service") as mock_create:
            mock_service = AsyncMock()
            mock_create.return_value = mock_service

            # First call should create instance
            result1 = await get_auth_service(config)
            assert result1 == mock_service
            mock_create.assert_called_once()

            # Second call should reuse instance
            result2 = await get_auth_service()
            assert result2 == mock_service
            # create_auth_service should still only be called once
            assert mock_create.call_count == 1

    @pytest.mark.asyncio
    async def test_get_production_auth_service(self):
        """Test getting production-configured AuthService."""
        from ai_karen_engine.auth.service import get_production_auth_service

        with patch("ai_karen_engine.auth.service.AuthConfig.load") as mock_load:
            mock_config = AuthConfig()
            mock_load.return_value = mock_config

            with patch(
                "ai_karen_engine.auth.service.create_auth_service"
            ) as mock_create:
                mock_service = AsyncMock()
                mock_create.return_value = mock_service

                result = await get_production_auth_service()

                # Verify production settings are enabled
                assert mock_config.features.enable_security_features is True
                assert mock_config.features.enable_rate_limiting is True
                assert mock_config.features.enable_audit_logging is True

                mock_create.assert_called_once_with(mock_config)
                assert result == mock_service

    @pytest.mark.asyncio
    async def test_get_intelligent_auth_service(self):
        """Test getting intelligence-enabled AuthService."""
        from ai_karen_engine.auth.service import get_intelligent_auth_service

        with patch("ai_karen_engine.auth.service.AuthConfig.load") as mock_load:
            mock_config = AuthConfig()
            mock_load.return_value = mock_config

            with patch(
                "ai_karen_engine.auth.service.create_auth_service"
            ) as mock_create:
                mock_service = AsyncMock()
                mock_create.return_value = mock_service

                result = await get_intelligent_auth_service()

                # Verify intelligence settings are enabled
                assert mock_config.features.enable_intelligent_auth is True
                assert mock_config.features.enable_anomaly_detection is True
                assert mock_config.features.enable_behavioral_analysis is True

                mock_create.assert_called_once_with(mock_config)
                assert result == mock_service


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
