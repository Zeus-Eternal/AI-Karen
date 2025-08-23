"""
Comprehensive unit tests for the enhanced token management service.

Tests cover JWT token creation, validation, rotation, JTI tracking,
and security features as specified in the requirements.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import secrets

from ai_karen_engine.auth.tokens import EnhancedTokenManager, TokenManager
from ai_karen_engine.auth.config import JWTConfig
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.exceptions import InvalidTokenError, TokenExpiredError


@pytest.fixture
def jwt_config():
    """Create a test JWT configuration."""
    return JWTConfig(
        secret_key="test-secret-key-for-testing-only",
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
        password_reset_token_expire_hours=1,
        email_verification_token_expire_hours=24,
    )


@pytest.fixture
def token_manager(jwt_config):
    """Create an enhanced token manager instance."""
    return EnhancedTokenManager(jwt_config)


@pytest.fixture
def user_data():
    """Create test user data."""
    return UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        tenant_id="test-tenant",
        is_verified=True,
        is_active=True,
    )


class TestEnhancedTokenManager:
    """Test suite for EnhancedTokenManager."""

    def test_initialization(self, jwt_config):
        """Test token manager initialization."""
        manager = EnhancedTokenManager(jwt_config)
        assert manager.config == jwt_config
        assert isinstance(manager._revoked_jtis, set)
        assert isinstance(manager._issued_jtis, set)

    def test_initialization_without_jwt_library(self, jwt_config):
        """Test initialization fails without PyJWT."""
        with patch('ai_karen_engine.auth.tokens.jwt', None):
            with pytest.raises(ImportError, match="PyJWT is required"):
                EnhancedTokenManager(jwt_config)

    def test_backward_compatibility_alias(self, jwt_config):
        """Test that TokenManager is an alias for EnhancedTokenManager."""
        manager = TokenManager(jwt_config)
        assert isinstance(manager, EnhancedTokenManager)

    @pytest.mark.asyncio
    async def test_create_access_token(self, token_manager, user_data):
        """Test access token creation with enhanced security."""
        token = await token_manager.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Validate token structure
        payload = token_manager.get_token_payload_without_validation(token)
        assert payload is not None
        assert payload["sub"] == user_data.user_id
        assert payload["email"] == user_data.email
        assert payload["typ"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload

    @pytest.mark.asyncio
    async def test_create_access_token_custom_expiry(self, token_manager, user_data):
        """Test access token creation with custom expiry."""
        custom_expiry = timedelta(minutes=30)
        token = await token_manager.create_access_token(user_data, custom_expiry)
        
        payload = token_manager.get_token_payload_without_validation(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + custom_expiry
        
        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, token_manager, user_data):
        """Test refresh token creation with enhanced security."""
        token = await token_manager.create_refresh_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Validate token structure
        payload = token_manager.get_token_payload_without_validation(token)
        assert payload is not None
        assert payload["sub"] == user_data.user_id
        assert payload["email"] == user_data.email
        assert payload["typ"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload

    @pytest.mark.asyncio
    async def test_create_refresh_token_custom_expiry(self, token_manager, user_data):
        """Test refresh token creation with custom expiry."""
        custom_expiry = timedelta(days=14)
        token = await token_manager.create_refresh_token(user_data, custom_expiry)
        
        payload = token_manager.get_token_payload_without_validation(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + custom_expiry
        
        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_jti_generation_uniqueness(self, token_manager):
        """Test that JTI generation produces unique values."""
        jtis = set()
        for _ in range(100):
            jti = token_manager._generate_jti()
            assert jti not in jtis
            jtis.add(jti)
            assert jti in token_manager._issued_jtis

    def test_jti_revocation(self, token_manager):
        """Test JTI revocation functionality."""
        jti = "test-jti-123"
        
        # Initially not revoked
        assert not token_manager._is_jti_revoked(jti)
        
        # Revoke JTI
        token_manager._revoke_jti(jti)
        assert token_manager._is_jti_revoked(jti)

    @pytest.mark.asyncio
    async def test_validate_access_token_success(self, token_manager, user_data):
        """Test successful access token validation."""
        token = await token_manager.create_access_token(user_data)
        payload = await token_manager.validate_access_token(token)
        
        assert payload["sub"] == user_data.user_id
        assert payload["email"] == user_data.email
        assert payload["typ"] == "access"

    @pytest.mark.asyncio
    async def test_validate_refresh_token_success(self, token_manager, user_data):
        """Test successful refresh token validation."""
        token = await token_manager.create_refresh_token(user_data)
        payload = await token_manager.validate_refresh_token(token)
        
        assert payload["sub"] == user_data.user_id
        assert payload["email"] == user_data.email
        assert payload["typ"] == "refresh"

    @pytest.mark.asyncio
    async def test_validate_token_wrong_type(self, token_manager, user_data):
        """Test token validation with wrong expected type."""
        access_token = await token_manager.create_access_token(user_data)
        
        with pytest.raises(InvalidTokenError, match="Invalid token type"):
            await token_manager.validate_token(access_token, "refresh")

    @pytest.mark.asyncio
    async def test_validate_revoked_token(self, token_manager, user_data):
        """Test validation of revoked token fails."""
        token = await token_manager.create_access_token(user_data)
        
        # Get JTI and revoke it
        jti = token_manager.get_jti_from_token(token)
        token_manager._revoke_jti(jti)
        
        with pytest.raises(InvalidTokenError, match="Token has been revoked"):
            await token_manager.validate_access_token(token)

    @pytest.mark.asyncio
    async def test_validate_expired_token(self, token_manager, user_data):
        """Test validation of expired token fails."""
        # Create token with very short expiry
        short_expiry = timedelta(seconds=1)
        token = await token_manager.create_access_token(user_data, short_expiry)
        
        # Wait for token to expire
        import asyncio
        await asyncio.sleep(2)
        
        with pytest.raises(TokenExpiredError):
            await token_manager.validate_access_token(token)

    @pytest.mark.asyncio
    async def test_validate_malformed_token(self, token_manager):
        """Test validation of malformed token fails."""
        malformed_token = "not.a.valid.jwt.token"
        
        with pytest.raises(InvalidTokenError, match="Invalid token"):
            await token_manager.validate_access_token(malformed_token)

    @pytest.mark.asyncio
    async def test_token_rotation(self, token_manager, user_data):
        """Test token rotation functionality."""
        # Create initial refresh token
        refresh_token = await token_manager.create_refresh_token(user_data)
        old_jti = token_manager.get_jti_from_token(refresh_token)
        
        # Rotate tokens
        new_access_token, new_refresh_token, expires_at = await token_manager.rotate_tokens(
            refresh_token, user_data
        )
        
        # Verify new tokens are different
        assert new_access_token != refresh_token
        assert new_refresh_token != refresh_token
        
        # Verify new tokens are valid
        access_payload = await token_manager.validate_access_token(new_access_token)
        refresh_payload = await token_manager.validate_refresh_token(new_refresh_token)
        
        assert access_payload["sub"] == user_data.user_id
        assert refresh_payload["sub"] == user_data.user_id
        
        # Verify old refresh token is revoked
        assert token_manager._is_jti_revoked(old_jti)
        
        # Verify expiry time is correct
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_token_rotation_invalid_refresh_token(self, token_manager, user_data):
        """Test token rotation with invalid refresh token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(InvalidTokenError):
            await token_manager.rotate_tokens(invalid_token, user_data)

    @pytest.mark.asyncio
    async def test_token_rotation_wrong_user(self, token_manager, user_data):
        """Test token rotation with token belonging to different user."""
        # Create token for one user
        refresh_token = await token_manager.create_refresh_token(user_data)
        
        # Try to rotate with different user data
        different_user = UserData(
            user_id="different-user-456",
            email="different@example.com",
            full_name="Different User",
            roles=["user"],
            tenant_id="test-tenant",
            is_verified=True,
            is_active=True,
        )
        
        with pytest.raises(InvalidTokenError, match="does not belong to user"):
            await token_manager.rotate_tokens(refresh_token, different_user)

    @pytest.mark.asyncio
    async def test_refresh_access_token_legacy(self, token_manager, user_data):
        """Test legacy refresh_access_token method uses rotation."""
        refresh_token = await token_manager.create_refresh_token(user_data)
        old_jti = token_manager.get_jti_from_token(refresh_token)
        
        new_access_token = await token_manager.refresh_access_token(refresh_token, user_data)
        
        # Verify new access token is valid
        payload = await token_manager.validate_access_token(new_access_token)
        assert payload["sub"] == user_data.user_id
        
        # Verify old refresh token is revoked (rotation happened)
        assert token_manager._is_jti_revoked(old_jti)

    @pytest.mark.asyncio
    async def test_revoke_token(self, token_manager, user_data):
        """Test token revocation."""
        token = await token_manager.create_access_token(user_data)
        jti = token_manager.get_jti_from_token(token)
        
        # Token should be valid initially
        await token_manager.validate_access_token(token)
        
        # Revoke token
        result = await token_manager.revoke_token(token)
        assert result is True
        
        # Token should now be invalid
        with pytest.raises(InvalidTokenError, match="Token has been revoked"):
            await token_manager.validate_access_token(token)

    @pytest.mark.asyncio
    async def test_revoke_token_without_jti(self, token_manager):
        """Test revoking token without JTI."""
        # Create a token-like string without JTI
        result = await token_manager.revoke_token("invalid.token")
        assert result is False

    def test_get_jti_from_token(self, token_manager, user_data):
        """Test extracting JTI from token."""
        import asyncio
        token = asyncio.run(token_manager.create_access_token(user_data))
        jti = token_manager.get_jti_from_token(token)
        
        assert jti is not None
        assert isinstance(jti, str)
        assert len(jti) == 32  # 16 bytes hex = 32 chars

    def test_get_jti_from_invalid_token(self, token_manager):
        """Test extracting JTI from invalid token."""
        jti = token_manager.get_jti_from_token("invalid.token")
        assert jti is None

    def test_get_token_expiry(self, token_manager, user_data):
        """Test getting token expiry time."""
        import asyncio
        token = asyncio.run(token_manager.create_access_token(user_data))
        expiry = token_manager.get_token_expiry(token)
        
        assert expiry is not None
        assert isinstance(expiry, datetime)
        assert expiry.tzinfo == timezone.utc
        
        # Should expire in approximately 15 minutes
        expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        assert abs((expiry - expected_expiry).total_seconds()) < 5

    def test_get_token_expiry_invalid_token(self, token_manager):
        """Test getting expiry from invalid token."""
        expiry = token_manager.get_token_expiry("invalid.token")
        assert expiry is None

    def test_is_token_expired(self, token_manager, user_data):
        """Test checking if token is expired."""
        import asyncio
        
        # Create token with short expiry
        short_expiry = timedelta(seconds=1)
        token = asyncio.run(token_manager.create_access_token(user_data, short_expiry))
        
        # Should not be expired initially
        assert not token_manager.is_token_expired(token)
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should now be expired
        assert token_manager.is_token_expired(token)

    def test_is_token_expired_invalid_token(self, token_manager):
        """Test checking expiry of invalid token."""
        assert token_manager.is_token_expired("invalid.token") is True

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_placeholder(self, token_manager):
        """Test placeholder implementation of revoke_all_user_tokens."""
        # This is a placeholder implementation
        result = await token_manager.revoke_all_user_tokens("test-user-123")
        assert result == 0

    def test_cleanup_expired_jtis_placeholder(self, token_manager):
        """Test placeholder implementation of cleanup_expired_jtis."""
        # This is a placeholder implementation
        result = token_manager.cleanup_expired_jtis()
        assert result == 0

    def test_get_token_payload_without_validation(self, token_manager, user_data):
        """Test getting token payload without validation."""
        import asyncio
        token = asyncio.run(token_manager.create_access_token(user_data))
        payload = token_manager.get_token_payload_without_validation(token)
        
        assert payload is not None
        assert payload["sub"] == user_data.user_id
        assert payload["typ"] == "access"

    def test_get_token_payload_without_validation_invalid(self, token_manager):
        """Test getting payload from invalid token."""
        payload = token_manager.get_token_payload_without_validation("invalid.token")
        assert payload is None


class TestTokenLifecycleManagement:
    """Test suite for comprehensive token lifecycle management."""

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, token_manager, user_data):
        """Test complete token lifecycle: create, validate, rotate, revoke."""
        # 1. Create initial tokens
        access_token = await token_manager.create_access_token(user_data)
        refresh_token = await token_manager.create_refresh_token(user_data)
        
        # 2. Validate tokens
        access_payload = await token_manager.validate_access_token(access_token)
        refresh_payload = await token_manager.validate_refresh_token(refresh_token)
        
        assert access_payload["sub"] == user_data.user_id
        assert refresh_payload["sub"] == user_data.user_id
        
        # 3. Rotate tokens
        new_access, new_refresh, expires_at = await token_manager.rotate_tokens(
            refresh_token, user_data
        )
        
        # 4. Validate new tokens
        new_access_payload = await token_manager.validate_access_token(new_access)
        new_refresh_payload = await token_manager.validate_refresh_token(new_refresh)
        
        assert new_access_payload["sub"] == user_data.user_id
        assert new_refresh_payload["sub"] == user_data.user_id
        
        # 5. Verify old refresh token is revoked
        old_jti = token_manager.get_jti_from_token(refresh_token)
        assert token_manager._is_jti_revoked(old_jti)
        
        # 6. Revoke new access token
        revoke_result = await token_manager.revoke_token(new_access)
        assert revoke_result is True
        
        # 7. Verify revoked token is invalid
        with pytest.raises(InvalidTokenError, match="Token has been revoked"):
            await token_manager.validate_access_token(new_access)

    @pytest.mark.asyncio
    async def test_multiple_token_rotations(self, token_manager, user_data):
        """Test multiple consecutive token rotations."""
        refresh_token = await token_manager.create_refresh_token(user_data)
        revoked_jtis = []
        
        # Perform multiple rotations
        for i in range(5):
            old_jti = token_manager.get_jti_from_token(refresh_token)
            revoked_jtis.append(old_jti)
            
            access_token, refresh_token, _ = await token_manager.rotate_tokens(
                refresh_token, user_data
            )
            
            # Verify new tokens are valid
            await token_manager.validate_access_token(access_token)
            await token_manager.validate_refresh_token(refresh_token)
        
        # Verify all old JTIs are revoked
        for jti in revoked_jtis:
            assert token_manager._is_jti_revoked(jti)

    @pytest.mark.asyncio
    async def test_concurrent_token_operations(self, token_manager, user_data):
        """Test concurrent token operations for thread safety."""
        import asyncio
        
        async def create_and_validate_token():
            token = await token_manager.create_access_token(user_data)
            payload = await token_manager.validate_access_token(token)
            return payload["jti"]
        
        # Run multiple concurrent operations
        tasks = [create_and_validate_token() for _ in range(10)]
        jtis = await asyncio.gather(*tasks)
        
        # Verify all JTIs are unique
        assert len(set(jtis)) == len(jtis)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])