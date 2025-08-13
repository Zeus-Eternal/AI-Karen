"""
Database migration utilities for consolidating authentication storage.

This module provides utilities for migrating authentication data from SQLite
to PostgreSQL, ensuring data consistency and proper foreign key relationships.
"""

from ai_karen_engine.database.migration.backup_manager import BackupManager
from ai_karen_engine.database.migration.consolidation_migrator import (
    DatabaseConsolidationMigrator,
)
from ai_karen_engine.database.migration.migration_validator import MigrationValidator
from ai_karen_engine.database.migration.postgres_schema import PostgreSQLAuthSchema

__all__ = [
    "DatabaseConsolidationMigrator",
    "MigrationValidator",
    "PostgreSQLAuthSchema",
    "BackupManager",
]
