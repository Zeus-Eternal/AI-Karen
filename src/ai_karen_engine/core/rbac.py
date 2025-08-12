"""RBAC utilities exposed via core module."""

from ai_karen_engine.middleware.rbac import (
    check_scope,
    check_scopes,
    require_scopes,
)

__all__ = ["check_scope", "check_scopes", "require_scopes"]
