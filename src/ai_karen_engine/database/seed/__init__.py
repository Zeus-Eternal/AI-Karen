"""Bootstrap seed helpers for authentication tables."""

# mypy: ignore-errors

from .auth_seed import seed_default_auth
from .rbac_seed import seed_default_roles

__all__ = ["seed_default_auth", "seed_default_roles"]
