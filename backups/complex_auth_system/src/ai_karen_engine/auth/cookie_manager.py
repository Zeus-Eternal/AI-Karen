"""
Secure session cookie management utilities for authentication.

This module provides comprehensive cookie management with security best practices,
environment-based configuration, and support for both access and refresh tokens.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Response, Request
from ai_karen_engine.auth.config import AuthConfig


class CookieConfig:
    """Cookie configuration with environment-based security settings."""
    
    def __init__(self, auth_config: Optional[AuthConfig] = None):
        """Initialize cookie configuration from auth config or environment."""
        self.auth_config = auth_config or AuthConfig.from_env()
        
        # Environment detection
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.is_production = self.environment in ("production", "prod")
        self.is_development = self.environment in ("development", "dev", "local")
        
        # Cookie names
        self.refresh_token_cookie = os.getenv(
            "AUTH_REFRESH_TOKEN_COOKIE_NAME", 
            "kari_refresh_token"
        )
        self.session_cookie = self.auth_config.session.cookie_name
        
        # Security flags with environment-based defaults
        self.secure = self._get_secure_flag()
        self.httponly = self.auth_config.session.cookie_httponly
        self.samesite = self._get_samesite_flag()
        
        # Expiry settings
        self.refresh_token_max_age = int(
            self.auth_config.jwt.refresh_token_expiry.total_seconds()
        )
        self.session_max_age = int(
            self.auth_config.session.session_timeout.total_seconds()
        )
    
    def _get_secure_flag(self) -> bool:
        """Determine secure flag based on environment and configuration."""
        # Explicit configuration takes precedence
        explicit_secure = os.getenv("AUTH_SESSION_COOKIE_SECURE")
        if explicit_secure is not None:
            return explicit_secure.lower() in ("true", "1", "yes", "on")
        
        # Check if we're running on HTTPS
        https_enabled = os.getenv("HTTPS_ENABLED", "false").lower() in ("true", "1", "yes", "on")
        
        # In development, only use secure cookies if HTTPS is enabled
        if self.is_development:
            return https_enabled
        
        # In production, default to True (should be using HTTPS)
        return self.is_production
    
    def _get_samesite_flag(self) -> str:
        """Determine SameSite flag based on environment and configuration."""
        configured_samesite = self.auth_config.session.cookie_samesite.lower()
        
        # Validate SameSite value
        valid_samesite = ["strict", "lax", "none"]
        if configured_samesite not in valid_samesite:
            # Default to 'lax' for compatibility
            return "lax"
        
        # In development, use 'lax' for easier testing
        if self.is_development and configured_samesite == "strict":
            return "lax"
        
        return configured_samesite


class SessionCookieManager:
    """Secure session cookie management with token rotation support."""
    
    def __init__(self, auth_config: Optional[AuthConfig] = None):
        """Initialize cookie manager with configuration."""
        self.config = CookieConfig(auth_config)
    
    def set_refresh_token_cookie(
        self, 
        response: Response, 
        refresh_token: str,
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        Set secure refresh token cookie with proper security flags.
        
        Args:
            response: FastAPI response object
            refresh_token: JWT refresh token to store
            expires_at: Optional expiry datetime (defaults to config max_age)
        """
        max_age = self.config.refresh_token_max_age
        if expires_at:
            max_age = int((expires_at - datetime.utcnow()).total_seconds())
            max_age = max(0, max_age)  # Ensure non-negative
        
        response.set_cookie(
            key=self.config.refresh_token_cookie,
            value=refresh_token,
            max_age=max_age,
            httponly=self.config.httponly,
            secure=self.config.secure,
            samesite=self.config.samesite,
            path="/"  # Make accessible from all routes for session persistence
        )
    
    def set_session_cookie(
        self, 
        response: Response, 
        session_token: str,
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        Set session cookie for backward compatibility.
        
        Args:
            response: FastAPI response object
            session_token: Session token to store
            expires_at: Optional expiry datetime
        """
        max_age = self.config.session_max_age
        if expires_at:
            max_age = int((expires_at - datetime.utcnow()).total_seconds())
            max_age = max(0, max_age)
        
        response.set_cookie(
            key=self.config.session_cookie,
            value=session_token,
            max_age=max_age,
            httponly=self.config.httponly,
            secure=self.config.secure,
            samesite=self.config.samesite,
            path="/"
        )
    
    def get_refresh_token(self, request: Request) -> Optional[str]:
        """
        Extract refresh token from request cookies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Refresh token if present, None otherwise
        """
        return request.cookies.get(self.config.refresh_token_cookie)
    
    def get_session_token(self, request: Request) -> Optional[str]:
        """
        Extract session token from request cookies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Session token if present, None otherwise
        """
        return request.cookies.get(self.config.session_cookie)
    
    def clear_refresh_token_cookie(self, response: Response) -> None:
        """
        Clear refresh token cookie by setting it to expire immediately.
        
        Args:
            response: FastAPI response object
        """
        response.set_cookie(
            key=self.config.refresh_token_cookie,
            value="",
            max_age=0,
            httponly=self.config.httponly,
            secure=self.config.secure,
            samesite=self.config.samesite,
            path="/"
        )
    
    def clear_session_cookie(self, response: Response) -> None:
        """
        Clear session cookie by setting it to expire immediately.
        
        Args:
            response: FastAPI response object
        """
        response.set_cookie(
            key=self.config.session_cookie,
            value="",
            max_age=0,
            httponly=self.config.httponly,
            secure=self.config.secure,
            samesite=self.config.samesite,
            path="/"
        )
    
    def clear_all_auth_cookies(self, response: Response) -> None:
        """
        Clear all authentication-related cookies.
        
        Args:
            response: FastAPI response object
        """
        self.clear_refresh_token_cookie(response)
        self.clear_session_cookie(response)
    
    def get_cookie_security_info(self) -> Dict[str, Any]:
        """
        Get current cookie security configuration for debugging/monitoring.
        
        Returns:
            Dictionary with current security settings
        """
        return {
            "environment": self.config.environment,
            "is_production": self.config.is_production,
            "secure": self.config.secure,
            "httponly": self.config.httponly,
            "samesite": self.config.samesite,
            "refresh_token_cookie": self.config.refresh_token_cookie,
            "session_cookie": self.config.session_cookie,
            "refresh_token_max_age": self.config.refresh_token_max_age,
            "session_max_age": self.config.session_max_age
        }
    
    def validate_cookie_security(self) -> Dict[str, Any]:
        """
        Validate current cookie security configuration.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        issues = []
        recommendations = []
        
        # Check production security
        if self.config.is_production:
            if not self.config.secure:
                issues.append("Secure flag should be True in production")
                recommendations.append("Set AUTH_SESSION_COOKIE_SECURE=true")
            
            if not self.config.httponly:
                issues.append("HttpOnly flag should be True for security")
                recommendations.append("Set AUTH_SESSION_COOKIE_HTTPONLY=true")
            
            if self.config.samesite == "none":
                issues.append("SameSite=None requires careful CSRF protection")
                recommendations.append("Consider using 'lax' or 'strict' for better security")
        
        # Check development settings
        if self.config.is_development:
            if self.config.secure and not os.getenv("HTTPS_ENABLED"):
                issues.append("Secure flag may prevent cookies in HTTP development")
                recommendations.append("Set AUTH_SESSION_COOKIE_SECURE=false for HTTP development")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "current_config": self.get_cookie_security_info()
        }


# Global cookie manager instance
_cookie_manager: Optional[SessionCookieManager] = None


def get_cookie_manager(auth_config: Optional[AuthConfig] = None) -> SessionCookieManager:
    """
    Get global cookie manager instance.
    
    Args:
        auth_config: Optional auth configuration (uses default if None)
        
    Returns:
        SessionCookieManager instance
    """
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = SessionCookieManager(auth_config)
    return _cookie_manager


def reset_cookie_manager() -> None:
    """Reset global cookie manager instance (useful for testing)."""
    global _cookie_manager
    _cookie_manager = None