#!/usr/bin/env python3
# mypy: ignore-errors
"""CLI for running SQL migrations."""

import argparse
from pathlib import Path

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.database.migration_runner import MigrationRunner

DEFAULT_MIGRATIONS_DIR = (
    Path(__file__).parent.parent / "data" / "migrations" / "postgres"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "command", choices=["migrate", "rollback", "status"], help="Action to perform"
    )
    parser.add_argument(
        "--database-url", default=settings.database_url, help="Database URL"
    )
    parser.add_argument(
        "--migrations-dir",
        default=str(DEFAULT_MIGRATIONS_DIR),
        help="Directory containing migration SQL files",
    )
    parser.add_argument("--version", help="Target version for rollback")
    args = parser.parse_args()

    runner = MigrationRunner(args.database_url, Path(args.migrations_dir))

    if args.command == "migrate":
        runner.run_migrations()
    elif args.command == "rollback":
        if not args.version:
            parser.error("rollback requires --version")
        runner.rollback(args.version)
    elif args.command == "status":
        status = runner.get_status()
        print("Applied migrations:", ", ".join(status["applied"]))
        print("Pending migrations:", ", ".join(status["pending"]))


if __name__ == "__main__":
    main()
