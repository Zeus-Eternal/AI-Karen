"""Simplified migration manager using consolidated SQL schema."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import Tenant

logger = logging.getLogger(__name__)

# Single consolidated migration file
SCHEMA_MIGRATIONS: List[str] = ["001_agui_chat_core.sql"]


class MigrationManager:
    """Manage database schema using a single consolidated SQL migration."""

    def __init__(
        self, database_url: Optional[str] = None, migrations_dir: Optional[str] = None
    ):
        self.database_url = database_url or self._build_database_url()
        self.migrations_dir = migrations_dir or os.path.join(
            os.path.dirname(__file__), "migrations"
        )
        self.client = MultiTenantPostgresClient(self.database_url)
        self.migration_files = SCHEMA_MIGRATIONS

    def _build_database_url(self) -> str:
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database = os.getenv("POSTGRES_DB", "ai_karen")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    # ------------------------------------------------------------------
    # Compatibility stubs for previous Alembic-based interface
    # ------------------------------------------------------------------
    def initialize_alembic(self) -> bool:
        """Alembic is no longer used; migrations are plain SQL files."""
        logger.info("Alembic not used - using consolidated SQL migrations")
        return True

    def create_initial_migration(self) -> bool:
        """Initial migration is provided as a static SQL file."""
        logger.info("Initial migration already consolidated")
        return True

    # ------------------------------------------------------------------
    # Migration operations
    # ------------------------------------------------------------------
    def run_migrations(self, revision: str = "head") -> bool:
        """Apply the consolidated SQL migration to the database."""
        try:
            with self.client.engine.begin() as conn:
                for filename in self.migration_files:
                    path = Path(self.migrations_dir) / filename
                    sql = path.read_text()
                    conn.execute(text(sql))
            logger.info("Applied consolidated schema migration")
            return True
        except Exception as e:  # pragma: no cover - database errors
            logger.error(f"Failed to run migrations: {e}")
            return False

    def rollback_migration(self, revision: str) -> bool:
        """Rollback is not supported with consolidated migrations."""
        logger.warning("Rollback not supported for consolidated migrations")
        return False

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Return the revision history for the consolidated schema."""
        return [
            {
                "revision": "001",
                "down_revision": None,
                "message": "agui_chat_core",
                "is_current": True,
            }
        ]

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def get_database_status(self) -> Dict[str, Any]:
        """Get basic database status information."""
        status = {
            "database_url": self.database_url.split("@")[-1],
            "migrations_dir": self.migrations_dir,
            "alembic_initialized": True,
            "current_revision": "001",
            "pending_migrations": 0,
            "tenant_count": 0,
            "health": "unknown",
        }

        try:  # pragma: no cover - requires database
            with self.client.get_sync_session() as session:
                status["tenant_count"] = session.query(Tenant).count()

            health_result = self.client.health_check()
            status["health"] = health_result["status"]
        except Exception as e:  # pragma: no cover - database errors
            status["error"] = str(e)
            logger.error(f"Failed to get database status: {e}")

        return status


__all__ = ["MigrationManager", "SCHEMA_MIGRATIONS"]

