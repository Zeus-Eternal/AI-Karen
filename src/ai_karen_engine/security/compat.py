"""
DEPRECATED: This module is deprecated and will be removed.

All authentication functionality has been consolidated into the unified
AuthService in ai_karen_engine.auth. Please update your imports:

OLD:
    from ai_karen_engine.security.compat import get_auth_service
    service = get_auth_service()

NEW:
    from ai_karen_engine.auth import get_auth_service
    service = await get_auth_service()

The new unified AuthService provides:
- Better async/await support
- Comprehensive configuration system
- Enhanced security features
- Intelligence-based authentication
- Unified error handling
- Better testing and maintainability

For migration help, see the auth service documentation.
"""

import warnings

# Emit a clear deprecation warning when this module is imported
warnings.warn(
    "ai_karen_engine.security.compat is deprecated. "
    "Use ai_karen_engine.auth instead. "
    "See module docstring for migration instructions.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from the new auth module for immediate compatibility
# This allows existing imports to work while showing the deprecation warning
try:
    from ai_karen_engine.auth import (
        AuthService,
        get_auth_service,
        get_production_auth_service,
    )
    
    # Note: These are async functions, so direct usage will fail
    # This is intentional to force users to update their code
    
except ImportError:
    # If the new auth module isn't available, provide stub functions
    # that raise clear errors
    def get_auth_service():
        raise ImportError(
            "The new unified auth service is not available. "
            "Please ensure ai_karen_engine.auth is properly installed."
        )
    
    def get_production_auth_service():
        raise ImportError(
            "The new unified auth service is not available. "
            "Please ensure ai_karen_engine.auth is properly installed."
        )
    
    class AuthService:
        def __init__(self):
            raise ImportError(
                "The new unified auth service is not available. "
                "Please ensure ai_karen_engine.auth is properly installed."
            )


# Legacy function names for compatibility (will fail when called due to async)
get_demo_auth_service = get_production_auth_service  # Same as production for now


__all__ = [
    "AuthService",
    "get_auth_service",
    "get_production_auth_service", 
    "get_demo_auth_service",
]
