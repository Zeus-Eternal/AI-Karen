"""Lightweight SQL migration runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from sqlalchemy import create_engine, text

# mypy: ignore-errors




@dataclass
class MigrationRunner:
    """Apply plain SQL migrations in order."""

    database_url: str
    migrations_dir: Path

    def _ensure_table(self, conn) -> None:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

    def _applied(self, conn) -> List[str]:
        self._ensure_table(conn)
        result = conn.execute(
            text("SELECT version FROM schema_migrations ORDER BY version")
        )
        return [row[0] for row in result.fetchall()]

    def run_migrations(self) -> None:
        engine = create_engine(self.database_url)
        with engine.begin() as conn:
            applied = set(self._applied(conn))
            for path in sorted(self.migrations_dir.glob("*.sql")):
                version = path.stem
                if version in applied:
                    continue
                sql = path.read_text()
                conn.execute(text(sql))
                conn.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                    {"v": version},
                )

    def rollback(self, version: str) -> None:
        engine = create_engine(self.database_url)
        rollback_file = self.migrations_dir / f"{version}_rollback.sql"
        if not rollback_file.exists():
            raise FileNotFoundError(f"No rollback file for {version}")
        with engine.begin() as conn:
            sql = rollback_file.read_text()
            conn.execute(text(sql))
            conn.execute(
                text("DELETE FROM schema_migrations WHERE version = :v"),
                {"v": version},
            )

    def get_status(self) -> Dict[str, List[str]]:
        engine = create_engine(self.database_url)
        with engine.begin() as conn:
            applied = self._applied(conn)
        all_versions = [p.stem for p in sorted(self.migrations_dir.glob("*.sql"))]
        pending = [v for v in all_versions if v not in applied]
        return {"applied": applied, "pending": pending}


__all__ = ["MigrationRunner"]
