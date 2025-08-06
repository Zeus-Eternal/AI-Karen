#!/usr/bin/env python3
"""
Test script to verify Task 1 implementation:
- Unified data models (UserData, SessionData, AuthEvent)
- AuthConfig class with comprehensive configuration options
- Base exception classes for unified error handling
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.ai_karen_engine.auth import (
    # Data models
    UserData, SessionData, AuthEvent,
    AuthEventType, SessionStorageType, AuthMode,
    PasswordResetToken, RateLimitInfo, SecurityResult, IntelligenceResult,
    
    # Configuration
    AuthConfig, DatabaseConfig, RedisConfig, TokenConfig, SessionConfig,
    SecurityConfig, IntelligenceConfig, LoggingConfig,
    get_development_config, get_testing_config, get_production_config,
    
    # Exceptions
    AuthError, InvalidCredentialsError, UserNotFoundError, SessionExpiredError,
    RateLimitExceededError, SecurityBlockError, WeakPasswordError,
    get_user_friendly_message, categorize_error, is_retryable_error
)

def test_data_models():
    """Test unified data models."""
    print("Testing unified data models...")
    
    # Test UserData
    user = UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        roles=["user", "admin"],
        tenant_id="test-tenant"
    )
    
    assert user.user_id == "test-user-123"
    assert user.email == "test@example.com"
    assert user.has_role("admin")
    assert not user.is_locked()
    
    # Test serialization
    user_dict = user.to_dict()
    user_restored = UserData.from_dict(user_dict)
    assert user_restored.user_id == user.user_id
    assert user_restored.email == user.email
    
    # Test SessionData
    session = SessionData(
        session_token="session-123",
        access_token="access-123",
        refresh_token="refresh-123",
        user_data=user,
        expires_in=3600,
        ip_address="192.168.1.1",
        user_agent="Test Agent"
    )
    
    assert session.session_token == "session-123"
    assert not session.is_expired()
    assert session.is_active
    
    # Test AuthEvent
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id=user.user_id,
        email=user.email,
        ip_address="192.168.1.1",
        success=True
    )
    
    assert event.event_type == AuthEventType.LOGIN_SUCCESS
    assert event.success
    assert event.user_id == user.user_id
    
    print("✅ Data models test passed")

def test_configuration_system():
    """Test AuthConfig and related configuration classes."""
    print("Testing configuration system...")
    
    # Test basic AuthConfig
    config = AuthConfig(
        auth_mode=AuthMode.ENHANCED,
        debug=True
    )
    
    assert config.auth_mode == AuthMode.ENHANCED
    assert config.enable_security_features
    assert not config.enable_intelligent_auth
    
    # Test configuration serialization
    config_dict = config.to_dict()
    config_restored = AuthConfig.from_dict(config_dict)
    assert config_restored.auth_mode == config.auth_mode
    assert config_restored.debug == config.debug
    
    # Test predefined configurations
    dev_config = get_development_config()
    assert dev_config.debug
    assert not dev_config.security.require_https
    
    test_config = get_testing_config()
    assert test_config.auth_mode == AuthMode.BASIC
    assert test_config.sessions.storage_type == SessionStorageType.MEMORY
    
    prod_config = get_production_config()
    assert prod_config.auth_mode == AuthMode.PRODUCTION
    assert prod_config.security.require_https
    assert prod_config.sessions.storage_type == SessionStorageType.REDIS
    
    # Test configuration validation
    errors = config.validate()
    print(f"Configuration validation errors: {errors}")
    
    print("✅ Configuration system test passed")

def test_exception_system():
    """Test unified exception classes."""
    print("Testing exception system...")
    
    # Test basic AuthError
    error = AuthError("Test error", error_code="TEST_ERROR")
    assert error.error_code == "TEST_ERROR"
    assert error.message == "Test error"
    
    # Test specific exceptions
    cred_error = InvalidCredentialsError(email="test@example.com")
    assert cred_error.error_code == "INVALID_CREDENTIALS"
    assert cred_error.details["email"] == "test@example.com"
    
    session_error = SessionExpiredError(expired_at="2024-01-01T00:00:00")
    assert session_error.error_code == "SESSION_EXPIRED"
    
    rate_limit_error = RateLimitExceededError(retry_after=60)
    assert rate_limit_error.error_code == "RATE_LIMIT_EXCEEDED"
    assert rate_limit_error.details["retry_after"] == 60
    
    # Test utility functions
    user_msg = get_user_friendly_message(cred_error)
    assert "Invalid email or password" in user_msg
    
    category = categorize_error(cred_error)
    assert category == "authentication"
    
    is_retryable = is_retryable_error(cred_error)
    assert not is_retryable
    
    print("✅ Exception system test passed")

def test_additional_models():
    """Test additional models for enhanced functionality."""
    print("Testing additional models...")
    
    # Test PasswordResetToken
    reset_token = PasswordResetToken(
        token="reset-123",
        user_id="user-123",
        email="test@example.com",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    assert not reset_token.is_expired()
    assert not reset_token.is_used()
    
    # Test RateLimitInfo
    rate_limit = RateLimitInfo(
        identifier="192.168.1.1",
        attempts=0,
        window_start=datetime.utcnow(),
        window_duration=timedelta(minutes=15),
        max_attempts=5
    )
    
    assert not rate_limit.is_locked()
    assert not rate_limit.add_attempt()  # First attempt should not exceed limit
    
    # Test SecurityResult
    security_result = SecurityResult(
        allowed=True,
        risk_score=0.3
    )
    
    security_result.add_flag("low_risk")
    assert "low_risk" in security_result.flags
    
    # Test IntelligenceResult
    intel_result = IntelligenceResult(
        risk_score=0.7,
        confidence=0.9,
        anomaly_detected=True
    )
    
    intel_result.add_behavioral_flag("unusual_location")
    assert "unusual_location" in intel_result.behavioral_flags
    
    print("✅ Additional models test passed")

def main():
    """Run all tests."""
    print("Testing Task 1 Implementation: Unified Data Models and Configuration System")
    print("=" * 80)
    
    try:
        test_data_models()
        test_configuration_system()
        test_exception_system()
        test_additional_models()
        
        print("\n" + "=" * 80)
        print("🎉 All Task 1 tests passed successfully!")
        print("\nImplemented components:")
        print("✅ UserData, SessionData, AuthEvent models")
        print("✅ AuthConfig with comprehensive configuration options")
        print("✅ Unified exception classes for error handling")
        print("✅ Additional models for enhanced functionality")
        print("✅ Enums for type safety (AuthEventType, SessionStorageType, AuthMode)")
        print("✅ Utility functions for error handling")
        print("✅ Predefined configurations for different environments")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()