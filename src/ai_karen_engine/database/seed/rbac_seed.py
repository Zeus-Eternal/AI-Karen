"""Seed default roles and permissions."""

# mypy: ignore-errors

import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from ai_karen_engine.database.models import Role, RolePermission

DEFAULT_ROLES: Dict[str, List[str]] = {
    "admin": ["*"],
    "user": ["chat:read", "chat:write"],
}


def seed_default_roles(session: Session, tenant_id: str = "default") -> None:
    """Seed default roles and associated permissions if missing."""
    for name, permissions in DEFAULT_ROLES.items():
        role = session.query(Role).filter_by(tenant_id=tenant_id, name=name).first()
        if not role:
            role = Role(
                role_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=name,
                description=f"{name} role",
            )
            session.add(role)
            session.flush()
        existing = {rp.permission for rp in role.permissions}
        for perm in permissions:
            if perm not in existing:
                session.add(
                    RolePermission(role_id=role.role_id, permission=perm, scope="*")
                )
    session.commit()
