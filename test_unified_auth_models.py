#!/usr/bin/env python3
"""
Test script for unified authentication models, configuration, and exceptions.

This script verifies that the unified data models and configuration system
work correctly and can be imported and used as expected.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the auth module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_models():
    """Test the unified data models."""
    print("Testing unified data models...")
    
    from ai_karen_engine.auth import (
        UserData, SessionData, AuthEvent, AuthEventType,
        SessionStorageType, AuthMode
    )
    
    # Test UserData
    user = UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        roles=["user", "admin"],
        tenant_id="tenant-1",
        preferences={"theme": "dark", "language": "en"}
    )
    
    assert user.user_id == "test-user-123"
    assert user.email == "test@example.com"
    assert user.has_role("admin")
    assert not user.has_role("superuser")
    assert not user.is_locked()
    
    # Test serialization
    user_dict = user.to_dict()
    user_restored = UserData.from_dict(user_dict)
    assert user_restored.user_id == user.user_id
    assert user_restored.email == user.email
    
    print("✓ UserData model works correctly")
    
    # Test SessionData
    session = SessionData(
        session_token="session-123",
        access_token="access-456",
        refresh_token="refresh-789",
        user_data=user,
        expires_in=3600,
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        risk_score=0.2
    )
    
    assert session.session_token == "session-123"
    assert session.user_data.email == "test@example.com"
    assert not session.is_expired()
    assert session.is_active
    
    # Test serialization
    session_dict = session.to_dict()
    session_restored = SessionData.from_dict(session_dict)
    assert session_restored.session_token == session.session_token
    assert session_restored.user_data.email == session.user_data.email
    
    print("✓ SessionData model works correctly")
    
    # Test AuthEvent
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id="test-user-123",
        email="test@example.com",
        ip_address="192.168.1.1",
        success=True,
        details={"method": "password"}
    )
    
    assert event.event_type == AuthEventType.LOGIN_SUCCESS
    assert event.success is True
    assert event.details["method"] == "password"
    
    # Test serialization
    event_dict = event.to_dict()
    event_restored = AuthEvent.from_dict(event_dict)
    assert event_restored.event_type == event.event_type
    assert event_restored.user_id == event.user_id
    
    print("✓ AuthEvent model works correctly")
    
    print("✓ All data models work correctly\n")


def test_config():
    """Test the configuration system."""
    print("Testing configuration system...")
    
    from ai_karen_engine.auth import (
        AuthConfig, AuthMode, SessionStorageType,
        get_development_config, get_testing_config, get_production_config
    )
    
    # Test basic configuration
    config = AuthConfig(
        auth_mode=AuthMode.ENHANCED,
        debug=True
    )
    
    assert config.auth_mode == AuthMode.ENHANCED
    assert config.enable_security_features is True
    assert config.enable_intelligent_auth is False
    
    print("✓ Basic AuthConfig works correctly")
    
    # Test serialization
    config_dict = config.to_dict()
    config_restored = AuthConfig.from_dict(config_dict)
    assert config_restored.auth_mode == config.auth_mode
    assert config_restored.debug == config.debug
    
    print("✓ AuthConfig serialization works correctly")
    
    # Test validation
    errors = config.validate()
    print(f"✓ Config validation found {len(errors)} errors (expected for test config)")
    
    # Test predefined configurations
    dev_config = get_development_config()
    assert dev_config.auth_mode == AuthMode.ENHANCED
    assert dev_config.debug is True
    
    test_config = get_testing_config()
    assert test_config.auth_mode == AuthMode.BASIC
    assert test_config.sessions.storage_type == SessionStorageType.MEMORY
    
    prod_config = get_production_config()
    assert prod_config.auth_mode == AuthMode.PRODUCTION
    assert prod_config.security.require_https is True
    
    print("✓ Predefined configurations work correctly")
    
    # Test environment configuration
    os.environ['AUTH_MODE'] = 'intelligent'
    os.environ['AUTH_DEBUG'] = 'true'
    env_config = AuthConfig.from_env()
    assert env_config.auth_mode == AuthMode.INTELLIGENT
    assert env_config.debug is True
    
    print("✓ Environment configuration works correctly")
    
    print("✓ Configuration system works correctly\n")


def test_exceptions():
    """Test the exception system."""
    print("Testing exception system...")
    
    from ai_karen_engine.auth import (
        AuthError, InvalidCredentialsError, SessionExpiredError,
        RateLimitExceededError, get_user_friendly_message,
        categorize_error, is_retryable_error
    )
    
    # Test base AuthError
    error = AuthError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"key": "value"},
        user_message="User-friendly message"
    )
    
    assert error.message == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.user_message == "User-friendly message"
    assert error.details["key"] == "value"
    
    # Test serialization
    error_dict = error.to_dict()
    assert error_dict["error_type"] == "AuthError"
    assert error_dict["message"] == "Test error"
    
    print("✓ Base AuthError works correctly")
    
    # Test specific exceptions
    cred_error = InvalidCredentialsError(email="test@example.com")
    assert cred_error.error_code == "INVALID_CREDENTIALS"
    assert cred_error.details["email"] == "test@example.com"
    
    session_error = SessionExpiredError(expired_at="2023-01-01T00:00:00")
    assert session_error.error_code == "SESSION_EXPIRED"
    assert session_error.details["expired_at"] == "2023-01-01T00:00:00"
    
    rate_error = RateLimitExceededError(retry_after=300)
    assert rate_error.error_code == "RATE_LIMIT_EXCEEDED"
    assert rate_error.details["retry_after"] == 300
    
    print("✓ Specific exceptions work correctly")
    
    # Test utility functions
    user_msg = get_user_friendly_message(cred_error)
    assert user_msg == "Invalid email or password"
    
    category = categorize_error(session_error)
    assert category == "session"
    
    retryable = is_retryable_error(cred_error)
    assert retryable is False
    
    print("✓ Exception utility functions work correctly")
    
    print("✓ Exception system works correctly\n")


def test_integration():
    """Test integration between components."""
    print("Testing component integration...")
    
    from ai_karen_engine.auth import (
        AuthConfig, UserData, SessionData, AuthEvent,
        AuthEventType, AuthMode, InvalidCredentialsError
    )
    
    # Create a configuration
    config = AuthConfig(auth_mode=AuthMode.ENHANCED)
    
    # Create user data
    user = UserData(
        user_id="integration-test",
        email="integration@example.com"
    )
    
    # Create session data
    session = SessionData(
        session_token="integration-session",
        access_token="integration-access",
        refresh_token="integration-refresh",
        user_data=user,
        expires_in=config.tokens.access_token_expire_minutes * 60
    )
    
    # Create auth event
    event = AuthEvent(
        event_type=AuthEventType.SESSION_CREATED,
        user_id=user.user_id,
        email=user.email,
        success=True,
        details={"session_token": session.session_token}
    )
    
    # Verify integration
    assert session.user_data.user_id == user.user_id
    assert event.user_id == user.user_id
    assert event.details["session_token"] == session.session_token
    
    print("✓ Component integration works correctly")
    
    # Test error handling integration
    try:
        raise InvalidCredentialsError(email=user.email)
    except InvalidCredentialsError as e:
        error_event = AuthEvent(
            event_type=AuthEventType.LOGIN_FAILED,
            user_id=user.user_id,
            email=user.email,
            success=False,
            error_message=e.message
        )
        assert error_event.success is False
        assert error_event.error_message == e.message
    
    print("✓ Error handling integration works correctly")
    
    print("✓ All integration tests passed\n")


def main():
    """Run all tests."""
    print("Testing Unified Authentication System Components")
    print("=" * 50)
    
    try:
        test_models()
        test_config()
        test_exceptions()
        test_integration()
        
        print("🎉 All tests passed successfully!")
        print("\nThe unified authentication models, configuration, and exceptions")
        print("are working correctly and ready for use in the consolidated auth service.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()