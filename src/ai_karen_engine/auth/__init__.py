"""Compatibility authentication interfaces for Kari AI.

This module restores the public interfaces that earlier versions of the
platform expected from :mod:`ai_karen_engine.auth`.  The core
authentication implementation now lives under :mod:`src.auth`, so we
expose thin adapters that delegate to the production services while
maintaining a stable import path for the rest of the code base.
"""

from .exceptions import (
    AuthError,
    UserAlreadyExistsError,
    UserNotFoundError,
    RateLimitExceededError,
    SecurityError,
)
from .models import UserData
from .rbac_middleware import (
    Permission,
    Role,
    RBACManager,
    check_admin_access,
    check_data_access,
    check_model_access,
    check_scheduler_access,
    check_scope,
    check_training_access,
    get_rbac_manager,
    require_permission,
    require_scopes,
)
from .session import get_current_user
from .cookie_manager import get_cookie_manager

__all__ = [
    "AuthError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "RateLimitExceededError",
    "SecurityError",
    "UserData",
    "Permission",
    "Role",
    "RBACManager",
    "get_rbac_manager",
    "require_permission",
    "require_scopes",
    "check_training_access",
    "check_data_access",
    "check_admin_access",
    "check_model_access",
    "check_scheduler_access",
    "check_scope",
    "get_current_user",
    "get_cookie_manager",
]
