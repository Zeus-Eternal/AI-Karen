"""Seed data for authentication tables."""

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy.orm import Session

from ai_karen_engine.database.models.auth_models import AuthUser, AuthProvider


def seed_default_auth(session: Session) -> None:
    """Insert default auth provider and admin user if missing."""
    if not session.query(AuthProvider).filter_by(provider_id="local").first():
        provider = AuthProvider(
            provider_id="local",
            type="local",
            config={},
            metadata={},
        )
        session.add(provider)

    if not session.query(AuthUser).filter_by(email="admin@karen.ai").first():
        admin = AuthUser(
            user_id=str(uuid.uuid4()),
            email="admin@karen.ai",
            full_name="Admin User",
            password_hash="change-me",
            is_active=True,
            is_verified=True,
            roles=["admin", "user"],
            tenant_id="default",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(admin)

    session.commit()
