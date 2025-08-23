"""
Tests for secure session cookie management utilities.

This module tests cookie configuration, security flag validation,
environment-based settings, and cookie operations.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import Request, Response

from ai_karen_engine.auth.cookie_manager import (
    CookieConfig,
    SessionCookieManager,
    get_cookie_manager,
    reset_cookie_manager
)
from ai_karen_engine.auth.config import AuthConfig, SessionConfig, JWTConfig


class TestCookieConfig:
    """Test cookie configuration with environment-based settings."""
    
    def test_production_defaults(self):
        """Test that production environment sets secure defaults."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            config = CookieConfig()
            
            assert config.is_production is True
            assert config.is_development is False
            assert config.secure is True  # Should be True in production
            assert config.httponly is True
            assert config.samesite == "lax"
    
    def test_development_defaults(self):
        """Test that development environment sets appropriate defaults."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = CookieConfig()
            
            assert config.is_production is False
            assert config.is_development is True
            assert config.secure is False  # Should be False in development
            assert config.httponly is True
            assert config.samesite == "lax"
    
    def test_explicit_secure_flag_override(self):
        """Test that explicit secure flag overrides environment defaults."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "AUTH_SESSION_COOKIE_SECURE": "true"
        }):
            config = CookieConfig()
            assert config.secure is True  # Explicit override
    
    def test_samesite_validation(self):
        """Test SameSite flag validation and fallback."""
        # Test valid SameSite values
        auth_config = AuthConfig()
        auth_config.session.cookie_samesite = "strict"
        config = CookieConfig(auth_config)
        assert config.samesite == "strict"
        
        # Test invalid SameSite value falls back to 'lax'
        auth_config.session.cookie_samesite = "invalid"
        config = CookieConfig(auth_config)
        assert config.samesite == "lax"
    
    def test_development_samesite_adjustment(self):
        """Test that strict SameSite is adjusted to lax in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            auth_config = AuthConfig()
            auth_config.session.cookie_samesite = "strict"
            config = CookieConfig(auth_config)
            assert config.samesite == "lax"  # Adjusted for development
    
    def test_custom_cookie_names(self):
        """Test custom cookie name configuration."""
        with patch.dict(os.environ, {
            "AUTH_REFRESH_TOKEN_COOKIE_NAME": "custom_refresh",
            "AUTH_SESSION_COOKIE_NAME": "custom_session"
        }):
            auth_config = AuthConfig()
            auth_config.session.cookie_name = "custom_session"
            config = CookieConfig(auth_config)
            
            assert config.refresh_token_cookie == "custom_refresh"
            assert config.session_cookie == "custom_session"
    
    def test_expiry_settings(self):
        """Test cookie expiry configuration."""
        auth_config = AuthConfig()
        auth_config.jwt.refresh_token_expire_days = 7
        auth_config.session.session_timeout_hours = 24
        
        config = CookieConfig(auth_config)
        
        assert config.refresh_token_max_age == 7 * 24 * 60 * 60  # 7 days in seconds
        assert config.session_max_age == 24 * 60 * 60  # 24 hours in seconds


class TestSessionCookieManager:
    """Test session cookie manager operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.response = Mock(spec=Response)
        self.request = Mock(spec=Request)
        self.request.cookies = {}
        
        # Reset global manager for clean tests
        reset_cookie_manager()
    
    def test_set_refresh_token_cookie(self):
        """Test setting refresh token cookie with security flags."""
        manager = SessionCookieManager()
        refresh_token = "test_refresh_token"
        
        manager.set_refresh_token_cookie(self.response, refresh_token)
        
        # Verify cookie was set with correct parameters
        self.response.set_cookie.assert_called_once()
        call_args = self.response.set_cookie.call_args
        
        assert call_args[1]["key"] == manager.config.refresh_token_cookie
        assert call_args[1]["value"] == refresh_token
        assert call_args[1]["httponly"] is True
        assert call_args[1]["path"] == "/auth"
        assert "max_age" in call_args[1]
    
    def test_set_refresh_token_cookie_with_expiry(self):
        """Test setting refresh token cookie with custom expiry."""
        manager = SessionCookieManager()
        refresh_token = "test_refresh_token"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        manager.set_refresh_token_cookie(self.response, refresh_token, expires_at)
        
        call_args = self.response.set_cookie.call_args
        max_age = call_args[1]["max_age"]
        
        # Should be approximately 1 hour (3600 seconds), allow some tolerance
        assert 3590 <= max_age <= 3610
    
    def test_set_session_cookie(self):
        """Test setting session cookie."""
        manager = SessionCookieManager()
        session_token = "test_session_token"
        
        manager.set_session_cookie(self.response, session_token)
        
        call_args = self.response.set_cookie.call_args
        assert call_args[1]["key"] == manager.config.session_cookie
        assert call_args[1]["value"] == session_token
        assert call_args[1]["path"] == "/"
    
    def test_get_refresh_token(self):
        """Test extracting refresh token from request."""
        manager = SessionCookieManager()
        test_token = "test_refresh_token"
        
        self.request.cookies[manager.config.refresh_token_cookie] = test_token
        
        result = manager.get_refresh_token(self.request)
        assert result == test_token
    
    def test_get_refresh_token_missing(self):
        """Test extracting refresh token when not present."""
        manager = SessionCookieManager()
        
        result = manager.get_refresh_token(self.request)
        assert result is None
    
    def test_get_session_token(self):
        """Test extracting session token from request."""
        manager = SessionCookieManager()
        test_token = "test_session_token"
        
        self.request.cookies[manager.config.session_cookie] = test_token
        
        result = manager.get_session_token(self.request)
        assert result == test_token
    
    def test_clear_refresh_token_cookie(self):
        """Test clearing refresh token cookie."""
        manager = SessionCookieManager()
        
        manager.clear_refresh_token_cookie(self.response)
        
        call_args = self.response.set_cookie.call_args
        assert call_args[1]["key"] == manager.config.refresh_token_cookie
        assert call_args[1]["value"] == ""
        assert call_args[1]["max_age"] == 0
    
    def test_clear_session_cookie(self):
        """Test clearing session cookie."""
        manager = SessionCookieManager()
        
        manager.clear_session_cookie(self.response)
        
        call_args = self.response.set_cookie.call_args
        assert call_args[1]["key"] == manager.config.session_cookie
        assert call_args[1]["value"] == ""
        assert call_args[1]["max_age"] == 0
    
    def test_clear_all_auth_cookies(self):
        """Test clearing all authentication cookies."""
        manager = SessionCookieManager()
        
        manager.clear_all_auth_cookies(self.response)
        
        # Should have been called twice (refresh + session)
        assert self.response.set_cookie.call_count == 2
        
        # Verify both cookies were cleared
        calls = self.response.set_cookie.call_args_list
        cookie_names = [call[1]["key"] for call in calls]
        
        assert manager.config.refresh_token_cookie in cookie_names
        assert manager.config.session_cookie in cookie_names
        
        # Verify all were set to expire
        for call in calls:
            assert call[1]["value"] == ""
            assert call[1]["max_age"] == 0
    
    def test_get_cookie_security_info(self):
        """Test getting cookie security information."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            manager = SessionCookieManager()
            
            info = manager.get_cookie_security_info()
            
            assert info["environment"] == "production"
            assert info["is_production"] is True
            assert info["secure"] is True
            assert info["httponly"] is True
            assert "refresh_token_cookie" in info
            assert "session_cookie" in info
    
    def test_validate_cookie_security_production_valid(self):
        """Test cookie security validation in production with valid config."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            manager = SessionCookieManager()
            
            validation = manager.validate_cookie_security()
            
            assert validation["valid"] is True
            assert len(validation["issues"]) == 0
            assert len(validation["recommendations"]) == 0
    
    def test_validate_cookie_security_production_issues(self):
        """Test cookie security validation in production with issues."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "AUTH_SESSION_COOKIE_SECURE": "false",
            "AUTH_SESSION_COOKIE_HTTPONLY": "false"
        }):
            auth_config = AuthConfig.from_env()
            manager = SessionCookieManager(auth_config)
            
            validation = manager.validate_cookie_security()
            
            assert validation["valid"] is False
            assert len(validation["issues"]) >= 2
            assert "Secure flag should be True in production" in validation["issues"]
            assert "HttpOnly flag should be True for security" in validation["issues"]
            assert len(validation["recommendations"]) >= 2
    
    def test_validate_cookie_security_development_https_warning(self):
        """Test cookie security validation in development with HTTPS warning."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "AUTH_SESSION_COOKIE_SECURE": "true"
        }, clear=True):  # Clear HTTPS_ENABLED
            auth_config = AuthConfig.from_env()
            manager = SessionCookieManager(auth_config)
            
            validation = manager.validate_cookie_security()
            
            # Should have warning about secure flag in HTTP development
            assert any("Secure flag may prevent cookies in HTTP development" in issue 
                     for issue in validation["issues"])
    
    def test_validate_cookie_security_samesite_none_warning(self):
        """Test cookie security validation with SameSite=None warning."""
        auth_config = AuthConfig()
        auth_config.session.cookie_samesite = "none"
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            manager = SessionCookieManager(auth_config)
            
            validation = manager.validate_cookie_security()
            
            assert any("SameSite=None requires careful CSRF protection" in issue 
                     for issue in validation["issues"])


class TestGlobalCookieManager:
    """Test global cookie manager instance management."""
    
    def setup_method(self):
        """Reset global manager for clean tests."""
        reset_cookie_manager()
    
    def test_get_cookie_manager_singleton(self):
        """Test that get_cookie_manager returns singleton instance."""
        manager1 = get_cookie_manager()
        manager2 = get_cookie_manager()
        
        assert manager1 is manager2
    
    def test_get_cookie_manager_with_config(self):
        """Test get_cookie_manager with custom config."""
        auth_config = AuthConfig()
        auth_config.session.cookie_name = "custom_session"
        
        manager = get_cookie_manager(auth_config)
        
        assert manager.config.session_cookie == "custom_session"
    
    def test_reset_cookie_manager(self):
        """Test resetting global cookie manager."""
        manager1 = get_cookie_manager()
        reset_cookie_manager()
        manager2 = get_cookie_manager()
        
        assert manager1 is not manager2


class TestCookieSecurityFlags:
    """Test cookie security flag behavior in different environments."""
    
    @pytest.mark.parametrize("environment,expected_secure", [
        ("production", True),
        ("prod", True),
        ("staging", False),
        ("development", False),
        ("dev", False),
        ("local", False),
        ("test", False),
    ])
    def test_environment_secure_defaults(self, environment, expected_secure):
        """Test secure flag defaults for different environments."""
        with patch.dict(os.environ, {"ENVIRONMENT": environment}):
            config = CookieConfig()
            assert config.secure == expected_secure
    
    @pytest.mark.parametrize("samesite_value,expected", [
        ("strict", "strict"),
        ("lax", "lax"),
        ("none", "none"),
        ("STRICT", "strict"),  # Case insensitive
        ("invalid", "lax"),    # Invalid falls back to lax
        ("", "lax"),           # Empty falls back to lax
    ])
    def test_samesite_validation(self, samesite_value, expected):
        """Test SameSite value validation and normalization."""
        auth_config = AuthConfig()
        auth_config.session.cookie_samesite = samesite_value
        
        config = CookieConfig(auth_config)
        assert config.samesite == expected
    
    def test_cookie_expiry_edge_cases(self):
        """Test cookie expiry calculation edge cases."""
        manager = SessionCookieManager()
        response = Mock(spec=Response)
        
        # Test with past expiry date (should result in max_age=0)
        past_expiry = datetime.utcnow() - timedelta(hours=1)
        manager.set_refresh_token_cookie(response, "token", past_expiry)
        
        call_args = response.set_cookie.call_args
        assert call_args[1]["max_age"] == 0
    
    def test_cookie_path_restrictions(self):
        """Test that cookies have appropriate path restrictions."""
        manager = SessionCookieManager()
        response = Mock(spec=Response)
        
        # Refresh token should be restricted to /auth
        manager.set_refresh_token_cookie(response, "refresh_token")
        call_args = response.set_cookie.call_args
        assert call_args[1]["path"] == "/auth"
        
        response.reset_mock()
        
        # Session cookie should be available site-wide
        manager.set_session_cookie(response, "session_token")
        call_args = response.set_cookie.call_args
        assert call_args[1]["path"] == "/"