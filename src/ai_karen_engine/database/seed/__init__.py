"""Bootstrap seed helpers for authentication tables."""

# mypy: ignore-errors

from ai_karen_engine.database.seed.auth_seed import seed_default_auth
from ai_karen_engine.database.seed.rbac_seed import seed_default_roles

__all__ = ["seed_default_auth", "seed_default_roles"]
