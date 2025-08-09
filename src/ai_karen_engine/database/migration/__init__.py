"""
Database migration utilities for consolidating authentication storage.

This module provides utilities for migrating authentication data from SQLite
to PostgreSQL, ensuring data consistency and proper foreign key relationships.
"""

from .consolidation_migrator import DatabaseConsolidationMigrator
from .migration_validator import MigrationValidator
from .postgres_schema import PostgreSQLAuthSchema
from .backup_manager import BackupManager

__all__ = [
    "DatabaseConsolidationMigrator",
    "MigrationValidator", 
    "PostgreSQLAuthSchema",
    "BackupManager"
]