"""
Comprehensive unit tests for the core authentication layer.

This test suite covers all functionality of the CoreAuthenticator class
including user authentication, session management, password operations,
and error handling.
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Import the auth components
from ai_karen_engine.auth import (
    AuthConfig,
    AuthEventType,
    DatabaseConfig,
    InvalidCredentialsError,
    JWTConfig,
    PasswordValidationError,
    SecurityConfig,
    SessionConfig,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserData,
    UserNotFoundError,
)
from ai_karen_engine.auth.core import (
    CoreAuthenticator,
    PasswordHasher,
    PasswordValidator,
)


class TestPasswordHasher:
    """Test password hashing functionality."""

    def test_hash_password_success(self):
        """Test successful password hashing."""
        hasher = PasswordHasher(rounds=4)  # Use low rounds for testing
        password = "test_password_123"

        hashed = hasher.hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$04$")  # bcrypt format with 4 rounds

    def test_hash_password_empty(self):
        """Test hashing empty password raises error."""
        hasher = PasswordHasher()

        with pytest.raises(ValueError, match="Password cannot be empty"):
            hasher.hash_password("")

    def test_verify_password_success(self):
        """Test successful password verification."""
        hasher = PasswordHasher(rounds=4)
        password = "test_password_123"
        hashed = hasher.hash_password(password)

        assert hasher.verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification failure."""
        hasher = PasswordHasher(rounds=4)
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hasher.hash_password(password)

        assert hasher.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_inputs(self):
        """Test password verification with empty inputs."""
        hasher = PasswordHasher()

        assert hasher.verify_password("", "hash") is False
        assert hasher.verify_password("password", "") is False
        assert hasher.verify_password("", "") is False

    def test_needs_rehash(self):
        """Test password rehash detection."""
        hasher = PasswordHasher(rounds=12)

        # Hash with lower rounds
        old_hasher = PasswordHasher(rounds=4)
        old_hash = old_hasher.hash_password("password")

        assert hasher.needs_rehash(old_hash) is True

        # Hash with current rounds
        new_hash = hasher.hash_password("password")
        assert hasher.needs_rehash(new_hash) is False

    def test_invalid_rounds(self):
        """Test invalid bcrypt rounds raise error."""
        with pytest.raises(ValueError, match="Bcrypt rounds must be between 4 and 20"):
            PasswordHasher(rounds=3)

        with pytest.raises(ValueError, match="Bcrypt rounds must be between 4 and 20"):
            PasswordHasher(rounds=21)


class TestPasswordValidator:
    """Test password validation functionality."""

    def test_validate_strong_password(self):
        """Test validation of strong password."""
        validator = PasswordValidator(min_length=8, require_complexity=True)
        password = "StrongPass123!"

        is_valid, errors = validator.validate_password(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_weak_password(self):
        """Test validation of weak password."""
        validator = PasswordValidator(min_length=8, require_complexity=True)
        password = "weak"

        is_valid, errors = validator.validate_password(password)

        assert is_valid is False
        assert len(errors) > 0
        assert any("at least 8 characters" in error for error in errors)

    def test_validate_no_complexity_requirements(self):
        """Test validation without complexity requirements."""
        validator = PasswordValidator(min_length=6, require_complexity=False)
        password = "simple"

        is_valid, errors = validator.validate_password(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_empty_password(self):
        """Test validation of empty password."""
        validator = PasswordValidator()

        is_valid, errors = validator.validate_password("")

        assert is_valid is False
        assert "Password is required" in errors

    def test_complexity_requirements(self):
        """Test individual complexity requirements."""
        validator = PasswordValidator(min_length=8, require_complexity=True)

        # Missing uppercase
        is_valid, errors = validator.validate_password("lowercase123!")
        assert not is_valid
        assert any("uppercase" in error for error in errors)

        # Missing lowercase
        is_valid, errors = validator.validate_password("UPPERCASE123!")
        assert not is_valid
        assert any("lowercase" in error for error in errors)

        # Missing digit
        is_valid, errors = validator.validate_password("NoDigits!")
        assert not is_valid
        assert any("digit" in error for error in errors)

        # Missing special character
        is_valid, errors = validator.validate_password("NoSpecial123")
        assert not is_valid
        assert any("special character" in error for error in errors)


class TestCoreAuthenticator:
    """Test CoreAuthenticator functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def auth_config(self, temp_db_path):
        """Create test authentication configuration."""
        return AuthConfig(
            database=DatabaseConfig(database_url=f"sqlite:///{temp_db_path}"),
            jwt=JWTConfig(secret_key="test-secret-key"),
            session=SessionConfig(storage_type="memory"),
            security=SecurityConfig(
                password_hash_rounds=4,  # Low rounds for testing
                max_failed_attempts=3,
                lockout_duration_minutes=5,
            ),
        )

    @pytest.fixture
    def core_auth(self, auth_config):
        """Create CoreAuthenticator instance for testing."""
        return CoreAuthenticator(auth_config)

    @pytest.fixture
    def sample_user_data(self):
        """Create sample user data for testing."""
        return UserData(
            user_id=str(uuid4()),
            email="test@example.com",
            full_name="Test User",
            tenant_id="test_tenant",
            roles=["user"],
        )

    @pytest.mark.asyncio
    async def test_create_user_success(self, core_auth, sample_user_data):
        """Test successful user creation."""
        password = "StrongPass123!"

        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
            tenant_id=sample_user_data.tenant_id,
        )

        assert created_user is not None
        assert created_user.email == sample_user_data.email
        assert created_user.full_name == sample_user_data.full_name
        assert created_user.tenant_id == sample_user_data.tenant_id
        assert created_user.is_active is True
        assert "user" in created_user.roles

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, core_auth, sample_user_data):
        """Test creating user with duplicate email raises error."""
        password = "StrongPass123!"

        # Create first user
        await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Try to create second user with same email
        with pytest.raises(UserAlreadyExistsError):
            await core_auth.create_user(
                email=sample_user_data.email,
                password=password,
                full_name="Another User",
            )

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, core_auth):
        """Test creating user with weak password raises error."""
        with pytest.raises(PasswordValidationError):
            await core_auth.create_user(
                email="test@example.com", password="weak", full_name="Test User"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, core_auth, sample_user_data):
        """Test successful user authentication."""
        password = "StrongPass123!"

        # Create user first
        await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Authenticate user
        authenticated_user = await core_auth.authenticate_user(
            email=sample_user_data.email,
            password=password,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        assert authenticated_user is not None
        assert authenticated_user.email == sample_user_data.email
        assert authenticated_user.last_login_at is not None
        assert authenticated_user.failed_login_attempts == 0

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(
        self, core_auth, sample_user_data
    ):
        """Test authentication with invalid credentials."""
        password = "StrongPass123!"
        wrong_password = "WrongPass123!"

        # Create user first
        await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Try to authenticate with wrong password
        with pytest.raises(InvalidCredentialsError):
            await core_auth.authenticate_user(
                email=sample_user_data.email, password=wrong_password
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, core_auth):
        """Test authentication with nonexistent user."""
        with pytest.raises(InvalidCredentialsError):
            await core_auth.authenticate_user(
                email="nonexistent@example.com", password="password"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_account_lockout(self, core_auth, sample_user_data):
        """Test account lockout after failed attempts."""
        password = "StrongPass123!"
        wrong_password = "WrongPass123!"

        # Create user first
        await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Make multiple failed attempts
        for _ in range(3):  # max_failed_attempts = 3
            with pytest.raises(InvalidCredentialsError):
                await core_auth.authenticate_user(
                    email=sample_user_data.email, password=wrong_password
                )

        # Next attempt should be blocked due to lockout
        from ai_karen_engine.auth.exceptions import AccountLockedError

        with pytest.raises(AccountLockedError):
            await core_auth.authenticate_user(
                email=sample_user_data.email,
                password=password,  # Even correct password should be blocked
            )

    @pytest.mark.asyncio
    async def test_create_session_success(self, core_auth, sample_user_data):
        """Test successful session creation."""
        session_data = await core_auth.create_session(
            user_data=sample_user_data, ip_address="127.0.0.1", user_agent="test-agent"
        )

        assert session_data is not None
        assert session_data.session_token is not None
        assert session_data.access_token is not None
        assert session_data.refresh_token is not None
        assert session_data.user_data.user_id == sample_user_data.user_id
        assert session_data.ip_address == "127.0.0.1"
        assert session_data.user_agent == "test-agent"
        assert session_data.is_active is True

    @pytest.mark.asyncio
    async def test_validate_session_success(self, core_auth, sample_user_data):
        """Test successful session validation."""
        # Create session first
        session_data = await core_auth.create_session(
            user_data=sample_user_data, ip_address="127.0.0.1"
        )

        # Validate session
        validated_user = await core_auth.validate_session(session_data.session_token)

        assert validated_user is not None
        assert validated_user.user_id == sample_user_data.user_id
        assert validated_user.email == sample_user_data.email

    @pytest.mark.asyncio
    async def test_validate_session_not_found(self, core_auth):
        """Test session validation with invalid token."""
        with pytest.raises(SessionNotFoundError):
            await core_auth.validate_session("invalid_token")

    @pytest.mark.asyncio
    async def test_invalidate_session_success(self, core_auth, sample_user_data):
        """Test successful session invalidation."""
        # Create session first
        session_data = await core_auth.create_session(
            user_data=sample_user_data, ip_address="127.0.0.1"
        )

        # Invalidate session
        result = await core_auth.invalidate_session(
            session_data.session_token, reason="test_logout"
        )

        assert result is True

        # Session should no longer be valid
        with pytest.raises(SessionNotFoundError):
            await core_auth.validate_session(session_data.session_token)

    @pytest.mark.asyncio
    async def test_invalidate_session_not_found(self, core_auth):
        """Test invalidating nonexistent session."""
        result = await core_auth.invalidate_session("invalid_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_user_password_success(self, core_auth, sample_user_data):
        """Test successful password update."""
        old_password = "OldPass123!"
        new_password = "NewPass123!"

        # Create user first
        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=old_password,
            full_name=sample_user_data.full_name,
        )

        # Update password
        result = await core_auth.update_user_password(
            user_id=created_user.user_id,
            new_password=new_password,
            current_password=old_password,
        )

        assert result is True

        # Should be able to authenticate with new password
        authenticated_user = await core_auth.authenticate_user(
            email=sample_user_data.email, password=new_password
        )
        assert authenticated_user is not None

        # Should not be able to authenticate with old password
        with pytest.raises(InvalidCredentialsError):
            await core_auth.authenticate_user(
                email=sample_user_data.email, password=old_password
            )

    @pytest.mark.asyncio
    async def test_update_user_password_wrong_current(
        self, core_auth, sample_user_data
    ):
        """Test password update with wrong current password."""
        old_password = "OldPass123!"
        new_password = "NewPass123!"
        wrong_current = "WrongPass123!"

        # Create user first
        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=old_password,
            full_name=sample_user_data.full_name,
        )

        # Try to update with wrong current password
        with pytest.raises(InvalidCredentialsError):
            await core_auth.update_user_password(
                user_id=created_user.user_id,
                new_password=new_password,
                current_password=wrong_current,
            )

    @pytest.mark.asyncio
    async def test_update_user_password_weak_new(self, core_auth, sample_user_data):
        """Test password update with weak new password."""
        old_password = "OldPass123!"
        weak_password = "weak"

        # Create user first
        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=old_password,
            full_name=sample_user_data.full_name,
        )

        # Try to update with weak password
        with pytest.raises(PasswordValidationError):
            await core_auth.update_user_password(
                user_id=created_user.user_id,
                new_password=weak_password,
                current_password=old_password,
            )

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, core_auth, sample_user_data):
        """Test getting user by ID."""
        password = "StrongPass123!"

        # Create user first
        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Get user by ID
        retrieved_user = await core_auth.get_user_by_id(created_user.user_id)

        assert retrieved_user is not None
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.email == created_user.email
        assert retrieved_user.full_name == created_user.full_name

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, core_auth):
        """Test getting nonexistent user by ID."""
        result = await core_auth.get_user_by_id("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, core_auth, sample_user_data):
        """Test getting user by email."""
        password = "StrongPass123!"

        # Create user first
        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Get user by email
        retrieved_user = await core_auth.get_user_by_email(sample_user_data.email)

        assert retrieved_user is not None
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.email == created_user.email
        assert retrieved_user.full_name == created_user.full_name

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, core_auth):
        """Test getting nonexistent user by email."""
        result = await core_auth.get_user_by_email("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_password_rehashing(self, core_auth, sample_user_data):
        """Test automatic password rehashing on login."""
        password = "StrongPass123!"

        # Create user with low rounds
        old_config = core_auth.config.security.password_hash_rounds
        core_auth.config.security.password_hash_rounds = 4
        core_auth.password_hasher = core_auth.password_hasher.__class__(4)

        created_user = await core_auth.create_user(
            email=sample_user_data.email,
            password=password,
            full_name=sample_user_data.full_name,
        )

        # Get initial hash
        initial_hash = await core_auth.db_client.get_user_password_hash(
            created_user.user_id
        )

        # Update config to higher rounds
        core_auth.config.security.password_hash_rounds = 8
        core_auth.password_hasher = core_auth.password_hasher.__class__(8)

        # Authenticate (should trigger rehashing)
        await core_auth.authenticate_user(
            email=sample_user_data.email, password=password
        )

        # Hash should be updated
        updated_hash = await core_auth.db_client.get_user_password_hash(
            created_user.user_id
        )
        assert updated_hash != initial_hash
        assert "$2b$08$" in updated_hash  # Should use 8 rounds now

        # Restore original config
        core_auth.config.security.password_hash_rounds = old_config


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
