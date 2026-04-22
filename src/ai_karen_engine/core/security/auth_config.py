"""
Centralized Authentication Configuration for AI-Karen Production System.

This module provides a single source of truth for authentication settings,
development modes, and security configurations. All auth bypass and development
mode checks should go through this module instead of scattered getenv() calls.
"""

import os
from typing import Dict, Any, Optional


class AuthConfig:
    """Centralized authentication configuration."""

    # Environment settings
    _environment: str = os.getenv(
        "ENVIRONMENT", os.getenv("KARI_ENV", "production")
    ).lower()
    _auth_bypass: bool = os.getenv("KARI_AUTH_BYPASS", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    _dev_mode: bool = os.getenv("AUTH_DEV_MODE", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    @classmethod
    def is_production(cls) -> bool:
        """Check if we're running in production mode."""
        return cls._environment in ["production", "prod"]

    @classmethod
    def is_development(cls) -> bool:
        """Check if we're running in development mode."""
        return cls._environment in ["development", "dev", "local"]

    @classmethod
    def is_auth_bypass_enabled(cls) -> bool:
        """Check if authentication bypass is enabled."""
        return cls._auth_bypass

    @classmethod
    def is_dev_mode_enabled(cls) -> bool:
        """Check if development mode is enabled."""
        return cls._dev_mode

    @classmethod
    def should_bypass_auth(cls) -> bool:
        """Determine if authentication should be bypassed.

        Always bypass if KARI_AUTH_BYPASS is explicitly enabled,
        regardless of environment (for development and testing).
        In production, can still bypass if KARI_AUTH_BYPASS is true.
        """
        # Check if KARI_AUTH_BYPASS is explicitly enabled
        if cls.is_auth_bypass_enabled():
            return True

        # In development, also allow bypass if dev mode is enabled
        if cls.is_development() and cls.is_dev_mode_enabled():
            return True

        return False

    @classmethod
    def get_dev_user_context(cls) -> Dict[str, Any]:
        """Get the development user context for bypass scenarios."""
        return {
            "user_id": "dev-user",
            "email": "dev-user@karen.ai",
            "full_name": "Development User",
            "roles": ["admin", "user"],
            "is_active": True,
            "tenant_id": "default",
            "authenticated": True,
            "preferences": {},
            "is_dev_bypass": True,
        }

    @classmethod
    def get_environment_info(cls) -> Dict[str, Any]:
        """Get environment configuration info for debugging."""
        return {
            "environment": cls._environment,
            "is_production": cls.is_production(),
            "is_development": cls.is_development(),
            "auth_bypass_enabled": cls.is_auth_bypass_enabled(),
            "dev_mode_enabled": cls.is_dev_mode_enabled(),
            "should_bypass_auth": cls.should_bypass_auth(),
        }


# Global instance
auth_config = AuthConfig()
