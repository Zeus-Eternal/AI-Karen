"""Tests for the simple migration runner on a blank database."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from ai_karen_engine.database.migration_runner import MigrationRunner

# mypy: ignore-errors





def test_migrations_run_cleanly(tmp_path: Path) -> None:
    """Ensure migrations apply sequentially on a fresh database."""
    db_url = f"sqlite:///{tmp_path/'test.db'}"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Create two simple migrations
    (migrations_dir / "001_create_table.sql").write_text(
        "CREATE TABLE example(id INTEGER PRIMARY KEY, name TEXT);"
    )
    (migrations_dir / "002_insert_row.sql").write_text(
        "INSERT INTO example(name) VALUES ('karen');"
    )

    runner = MigrationRunner(db_url, migrations_dir)
    runner.run_migrations()

    engine = create_engine(db_url)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM example")).scalar()
        assert count == 1
        versions = [
            row[0]
            for row in conn.execute(
                text("SELECT version FROM schema_migrations ORDER BY version")
            )
        ]
        assert versions == ["001_create_table", "002_insert_row"]
