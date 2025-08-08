#!/usr/bin/env python3
"""
Test script for the unified authentication models, configuration, and exceptions.

This script validates that all components of task 1 are working correctly:
- Unified data models (UserData, SessionData, AuthEvent)
- Comprehensive configuration system (AuthConfig)
- Unified exception hierarchy

Run this script to verify the implementation meets the requirements.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta

# Import the unified auth components
from ai_karen_engine.auth import (
    AccountLockedError,
    AuthConfig,
    AuthEvent,
    AuthEventType,
    DatabaseConfig,
    FeatureToggles,
    IntelligenceConfig,
    InvalidCredentialsError,
    JWTConfig,
    RateLimitExceededError,
    SecurityConfig,
    SessionConfig,
    SessionData,
    SessionExpiredError,
    UserData,
    get_http_status_code,
    is_user_error,
)


def test_user_data_model():
    """Test the unified UserData model."""
    print("🧪 Testing UserData model...")

    # Test basic creation
    user = UserData(
        user_id="user123",
        email="test@example.com",
        full_name="Test User",
        roles=["user", "admin"],
        tenant_id="tenant1",
        preferences={"theme": "dark", "language": "en"},
    )

    # Test validation
    assert user.validate(), "UserData validation should pass"
    assert user.has_role("admin"), "User should have admin role"
    assert not user.is_locked(), "User should not be locked initially"

    # Test role management
    user.add_role("moderator")
    assert user.has_role("moderator"), "User should have moderator role after adding"

    user.remove_role("admin")
    assert not user.has_role("admin"), "User should not have admin role after removing"

    # Test account locking
    user.lock_account(30)
    assert user.is_locked(), "User should be locked after lock_account"

    user.unlock_account()
    assert not user.is_locked(), "User should not be locked after unlock_account"

    # Test serialization
    user_dict = user.to_dict()
    assert isinstance(user_dict, dict), "to_dict should return dictionary"
    assert user_dict["user_id"] == "user123", "Serialized user_id should match"

    # Test deserialization
    user2 = UserData.from_dict(user_dict)
    assert user2.user_id == user.user_id, "Deserialized user should match original"
    assert user2.email == user.email, "Deserialized email should match original"

    print("✅ UserData model tests passed")


def test_session_data_model():
    """Test the unified SessionData model."""
    print("🧪 Testing SessionData model...")

    # Create test user
    user = UserData(user_id="user123", email="test@example.com")

    # Test basic creation
    session = SessionData(
        session_token="session123",
        access_token="access123",
        refresh_token="refresh123",
        user_data=user,
        expires_in=3600,
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        risk_score=0.2,
    )

    # Test validation
    assert session.validate(), "SessionData validation should pass"
    assert not session.is_expired(), "Session should not be expired initially"
    assert session.is_active, "Session should be active initially"

    # Test security flags
    session.add_security_flag("suspicious_location")
    assert (
        "suspicious_location" in session.security_flags
    ), "Security flag should be added"

    session.remove_security_flag("suspicious_location")
    assert (
        "suspicious_location" not in session.security_flags
    ), "Security flag should be removed"

    # Test risk score update
    session.update_risk_score(0.9)
    assert session.risk_score == 0.9, "Risk score should be updated"

    # Test invalidation
    session.invalidate("manual_logout")
    assert not session.is_active, "Session should not be active after invalidation"
    assert (
        session.invalidation_reason == "manual_logout"
    ), "Invalidation reason should be set"

    # Test serialization
    session_dict = session.to_dict()
    assert isinstance(session_dict, dict), "to_dict should return dictionary"
    assert (
        session_dict["session_token"] == "session123"
    ), "Serialized session_token should match"

    # Test deserialization
    session2 = SessionData.from_dict(session_dict)
    assert (
        session2.session_token == session.session_token
    ), "Deserialized session should match original"
    assert (
        session2.user_data.user_id == session.user_data.user_id
    ), "Deserialized user data should match"

    print("✅ SessionData model tests passed")


def test_auth_event_model():
    """Test the unified AuthEvent model."""
    print("🧪 Testing AuthEvent model...")

    # Test basic creation
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id="user123",
        email="test@example.com",
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        success=True,
        risk_score=0.1,
    )

    # Test validation
    assert event.validate(), "AuthEvent validation should pass"
    assert event.success, "Event should be successful"

    # Test adding details
    event.add_detail("login_method", "password")
    assert event.details["login_method"] == "password", "Detail should be added"

    # Test security flags
    event.add_security_flag("new_device")
    assert "new_device" in event.security_flags, "Security flag should be added"

    # Test error handling
    event.set_error("Invalid password")
    assert not event.success, "Event should not be successful after error"
    assert event.error_message == "Invalid password", "Error message should be set"

    # Test processing time
    start_time = datetime.utcnow() - timedelta(milliseconds=100)
    event.set_processing_time(start_time)
    assert event.processing_time_ms > 0, "Processing time should be positive"

    # Test serialization
    event_dict = event.to_dict()
    assert isinstance(event_dict, dict), "to_dict should return dictionary"
    assert (
        event_dict["event_type"] == "login_success"
    ), "Serialized event_type should match"

    # Test deserialization
    event2 = AuthEvent.from_dict(event_dict)
    assert (
        event2.event_type == event.event_type
    ), "Deserialized event should match original"
    assert event2.user_id == event.user_id, "Deserialized user_id should match"

    print("✅ AuthEvent model tests passed")


def test_auth_config():
    """Test the unified AuthConfig system."""
    print("🧪 Testing AuthConfig system...")

    # Test default configuration
    config = AuthConfig()
    assert isinstance(
        config.database, DatabaseConfig
    ), "Database config should be DatabaseConfig instance"
    assert isinstance(config.jwt, JWTConfig), "JWT config should be JWTConfig instance"
    assert isinstance(
        config.session, SessionConfig
    ), "Session config should be SessionConfig instance"
    assert isinstance(
        config.security, SecurityConfig
    ), "Security config should be SecurityConfig instance"
    assert isinstance(
        config.intelligence, IntelligenceConfig
    ), "Intelligence config should be IntelligenceConfig instance"
    assert isinstance(
        config.features, FeatureToggles
    ), "Features config should be FeatureToggles instance"

    # Test configuration from environment
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    os.environ["AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["AUTH_USE_DATABASE"] = "true"
    os.environ["AUTH_ENABLE_RATE_LIMITING"] = "true"

    config_from_env = AuthConfig.from_env()
    assert (
        config_from_env.jwt.secret_key == "test-secret-key"
    ), "Secret key should be loaded from env"
    assert (
        config_from_env.jwt.access_token_expire_minutes == 30
    ), "Access token expiry should be loaded from env"
    assert (
        config_from_env.features.use_database
    ), "Database feature should be enabled from env"
    assert (
        config_from_env.features.enable_rate_limiting
    ), "Rate limiting should be enabled from env"

    # Test configuration from dictionary
    config_dict = {
        "jwt": {"secret_key": "dict-secret", "access_token_expire_minutes": 45},
        "security": {"max_failed_attempts": 3, "lockout_duration_minutes": 10},
        "features": {"enable_intelligent_auth": True},
    }

    config_from_dict = AuthConfig.from_dict(config_dict)
    assert (
        config_from_dict.jwt.secret_key == "dict-secret"
    ), "Secret key should be loaded from dict"
    assert (
        config_from_dict.jwt.access_token_expire_minutes == 45
    ), "Access token expiry should be loaded from dict"
    assert (
        config_from_dict.security.max_failed_attempts == 3
    ), "Max failed attempts should be loaded from dict"
    assert (
        config_from_dict.features.enable_intelligent_auth
    ), "Intelligent auth should be enabled from dict"

    # Test configuration serialization
    config_dict_out = config.to_dict()
    assert isinstance(config_dict_out, dict), "to_dict should return dictionary"
    assert "jwt" in config_dict_out, "JWT config should be in serialized dict"
    assert "database" in config_dict_out, "Database config should be in serialized dict"

    # Test configuration from JSON file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_dict, f)
        json_file = f.name

    try:
        config_from_json = AuthConfig.from_file(json_file)
        assert (
            config_from_json.jwt.secret_key == "dict-secret"
        ), "Config should be loaded from JSON file"
    finally:
        os.unlink(json_file)

    # Test configuration validation
    config.jwt.secret_key = "test-key"  # Set a valid key
    try:
        config.validate()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        raise

    # Test mode description
    mode_desc = config.get_mode_description()
    assert isinstance(mode_desc, str), "Mode description should be string"
    assert (
        "Consolidated auth service" in mode_desc
    ), "Mode description should mention consolidated service"

    # Clean up environment variables
    for key in [
        "AUTH_SECRET_KEY",
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
        "AUTH_USE_DATABASE",
        "AUTH_ENABLE_RATE_LIMITING",
    ]:
        if key in os.environ:
            del os.environ[key]

    print("✅ AuthConfig system tests passed")


def test_auth_config_legacy_env_mapping():
    """Ensure legacy environment variables map to new feature toggles."""
    # Set legacy variable names only
    os.environ["AUTH_ENABLE_RATE_LIMITER"] = "true"
    os.environ["AUTH_ENABLE_INTELLIGENT_CHECKS"] = "true"

    cfg = AuthConfig.from_env()

    assert cfg.features.enable_rate_limiting is True
    assert cfg.features.enable_intelligent_auth is True
    assert cfg.features.enable_anomaly_detection is True
    assert cfg.features.enable_behavioral_analysis is True

    # Clean up environment variables
    for key in [
        "AUTH_ENABLE_RATE_LIMITER",
        "AUTH_ENABLE_INTELLIGENT_CHECKS",
    ]:
        if key in os.environ:
            del os.environ[key]

    print("✅ Legacy environment variable mapping works")


def test_unified_exceptions():
    """Test the unified exception hierarchy."""
    print("🧪 Testing unified exceptions...")

    # Test basic exception creation
    error = InvalidCredentialsError(
        message="Invalid email or password", email="test@example.com"
    )

    assert (
        str(error) == "InvalidCredentialsError: Invalid email or password"
    ), "Exception string representation should be correct"
    assert (
        error.details["email"] == "test@example.com"
    ), "Exception details should be set"
    assert (
        error.user_message == "Invalid email or password"
    ), "User message should be set"

    # Test exception serialization
    error_dict = error.to_dict()
    assert isinstance(error_dict, dict), "Exception to_dict should return dictionary"
    assert (
        error_dict["error_type"] == "InvalidCredentialsError"
    ), "Error type should be correct"
    assert (
        error_dict["message"] == "Invalid email or password"
    ), "Message should be correct"

    # Test different exception types
    exceptions_to_test = [
        (AccountLockedError("Account locked", locked_until="2024-01-01T00:00:00"), 429),
        (SessionExpiredError("Session expired", session_token="token123"), 401),
        (RateLimitExceededError("Rate limit exceeded", retry_after=60), 429),
    ]

    for exception, expected_status in exceptions_to_test:
        assert is_user_error(
            exception
        ), f"{exception.__class__.__name__} should be a user error"
        status_code = get_http_status_code(exception)
        assert (
            status_code == expected_status
        ), f"{exception.__class__.__name__} should return status {expected_status}, got {status_code}"

    print("✅ Unified exceptions tests passed")


def test_integration():
    """Test integration between all components."""
    print("🧪 Testing component integration...")

    # Create a complete authentication scenario
    config = AuthConfig()
    config.jwt.secret_key = "integration-test-key"
    config.features.use_database = True
    config.features.enable_security_features = True
    config.security.max_failed_attempts = 3

    # Create user
    user = UserData(
        user_id="integration_user",
        email="integration@example.com",
        full_name="Integration Test User",
        roles=["user"],
        tenant_id="test_tenant",
    )

    # Create session
    session = SessionData(
        session_token="integration_session",
        access_token="integration_access",
        refresh_token="integration_refresh",
        user_data=user,
        expires_in=config.jwt.access_token_expire_minutes * 60,
        ip_address="127.0.0.1",
        user_agent="Integration Test",
    )

    # Create auth event
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id=user.user_id,
        email=user.email,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        session_token=session.session_token,
        success=True,
    )

    # Validate all components work together
    assert user.validate(), "User should be valid"
    assert session.validate(), "Session should be valid"
    assert event.validate(), "Event should be valid"

    # Test serialization round-trip
    user_dict = user.to_dict()
    session_dict = session.to_dict()
    event_dict = event.to_dict()
    config_dict = config.to_dict()

    user2 = UserData.from_dict(user_dict)
    session2 = SessionData.from_dict(session_dict)
    event2 = AuthEvent.from_dict(event_dict)
    config2 = AuthConfig.from_dict(config_dict)

    assert user2.user_id == user.user_id, "User round-trip should preserve data"
    assert (
        session2.session_token == session.session_token
    ), "Session round-trip should preserve data"
    assert (
        event2.event_type == event.event_type
    ), "Event round-trip should preserve data"
    assert (
        config2.jwt.secret_key == config.jwt.secret_key
    ), "Config round-trip should preserve data"

    print("✅ Integration tests passed")


def main():
    """Run all tests for the unified authentication system."""
    print("🚀 Testing Unified Authentication System - Task 1 Implementation")
    print("=" * 70)

    try:
        test_user_data_model()
        test_session_data_model()
        test_auth_event_model()
        test_auth_config()
        test_unified_exceptions()
        test_integration()

        print("=" * 70)
        print("🎉 All tests passed successfully!")
        print("\nThe unified authentication models, configuration, and exceptions")
        print(
            "are working correctly and ready for use in the consolidated auth service."
        )

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
