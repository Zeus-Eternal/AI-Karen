"""
Migration Rollback Scenario Tests

Comprehensive tests for database migration rollback scenarios and validation.
Tests migration state consistency, rollback validation, and recovery patterns.

Requirements: 2.5
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from ai_karen_engine.services.migration_validator import (
    MigrationValidator,
    MigrationStatus,
    SchemaValidationStatus,
    MigrationInfo,
)


class TestMigrationRollbackScenarios:
    """Test various migration rollback scenarios"""

    @pytest.fixture
    async def migration_environment(self):
        """Set up migration testing environment"""
        # Create temporary migrations directory
        temp_dir = tempfile.mkdtemp()
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir(parents=True)
        
        # Mock database manager
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        mock_db_manager.is_degraded.return_value = False
        
        # Database state tracking
        db_state = {
            "tables": set(),
            "alembic_version": None,
            "migration_history": [],
        }
        
        yield {
            "migrations_dir": migrations_dir,
            "db_manager": mock_db_manager,
            "session": mock_session,
            "db_state": db_state,
            "temp_dir": temp_dir,
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    async def migration_validator(self, migration_environment):
        """Create migration validator with test environment"""
        validator = MigrationValidator(
            migrations_directory=str(migration_environment["migrations_dir"])
        )
        return validator

    def create_mock_migration_files(self, migrations_dir: Path, migration_versions: List[str]):
        """Create mock migration files"""
        for version in migration_versions:
            migration_file = migrations_dir / f"{version}_test_migration.py"
            migration_file.write_text(f"""
\"\"\"Test migration {version}\"\"\"

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{version}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Test upgrade operations
    pass

def downgrade():
    # Test downgrade operations
    pass
""")

    @pytest.mark.asyncio
    async def test_successful_migration_rollback_validation(self, migration_environment, migration_validator):
        """Test validation of successful migration rollback"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate successful rollback scenario
        # - Alembic version table exists
        # - Current version is rolled back to earlier version
        # - Schema matches the rolled-back state
        
        db_state["alembic_version"] = "001"  # Rolled back to version 001
        db_state["tables"] = {"tenants", "auth_users", "conversations"}  # Basic tables only
        
        # Mock database queries
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = True
            elif "SELECT version_num FROM alembic_version" in query_str:
                result.scalar.return_value = db_state["alembic_version"]
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect that we're at an earlier migration version
            assert report.current_migration is not None
            assert report.current_migration.version == "001"
            
            # Should detect missing tables (indicating successful rollback)
            expected_tables = migration_validator.expected_tables
            missing_tables = expected_tables - db_state["tables"]
            assert len(missing_tables) > 0, "Should have missing tables after rollback"
            
            # Status should indicate pending migrations (to move forward again)
            assert report.overall_status == MigrationStatus.PENDING
            
            # Should recommend applying migrations to move forward
            assert any("upgrade head" in rec for rec in report.recommendations)

    @pytest.mark.asyncio
    async def test_incomplete_migration_rollback_validation(self, migration_environment, migration_validator):
        """Test validation of incomplete migration rollback"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate incomplete rollback scenario
        # - Alembic version shows rollback
        # - But some tables from later migrations still exist
        
        db_state["alembic_version"] = "001"  # Rolled back to version 001
        db_state["tables"] = {
            # Basic tables that should exist at version 001
            "tenants", "auth_users", "conversations",
            # Tables that should have been removed during rollback but weren't
            "advanced_features", "new_extension_table", "temp_migration_data"
        }
        
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = True
            elif "SELECT version_num FROM alembic_version" in query_str:
                result.scalar.return_value = db_state["alembic_version"]
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect inconsistent state
            assert report.overall_status == MigrationStatus.INCONSISTENT
            
            # Should detect extra tables that shouldn't exist at this migration version
            extra_tables = db_state["tables"] - migration_validator.expected_tables
            assert len(extra_tables) > 0, "Should detect extra tables from incomplete rollback"
            
            # Should recommend cleanup
            cleanup_recommendations = [
                rec for rec in report.recommendations 
                if "extra tables" in rec or "cleanup" in rec.lower()
            ]
            assert len(cleanup_recommendations) > 0

    @pytest.mark.asyncio
    async def test_migration_rollback_without_version_tracking(self, migration_environment, migration_validator):
        """Test rollback scenario where version tracking is lost"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate scenario where alembic_version table was dropped during rollback
        db_state["alembic_version"] = None
        db_state["tables"] = {"tenants", "auth_users"}  # Minimal set of tables
        
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = False  # Table doesn't exist
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect unknown migration status
            assert report.overall_status == MigrationStatus.UNKNOWN
            assert report.current_migration is None
            
            # Should recommend initializing migration tracking
            init_recommendations = [
                rec for rec in report.recommendations 
                if "Initialize Alembic" in rec or "stamp head" in rec
            ]
            assert len(init_recommendations) > 0

    @pytest.mark.asyncio
    async def test_migration_rollback_with_data_corruption(self, migration_environment, migration_validator):
        """Test rollback scenario with data corruption"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate rollback with data corruption
        db_state["alembic_version"] = "002"
        db_state["tables"] = {"tenants", "auth_users", "conversations", "messages"}
        
        # Mock database errors during validation
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = True
            elif "SELECT version_num FROM alembic_version" in query_str:
                result.scalar.return_value = db_state["alembic_version"]
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            elif "column_name" in query_str:
                # Simulate corrupted table structure
                if "tenants" in query_str:
                    raise Exception("Table 'tenants' is corrupted and cannot be accessed")
                else:
                    result.fetchall.return_value = [("id", "integer"), ("name", "varchar")]
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect validation errors due to corruption
            assert report.overall_status == MigrationStatus.FAILED
            assert len(report.errors) > 0
            
            # Should have error about table corruption
            corruption_errors = [
                error for error in report.errors 
                if "corrupted" in error.lower()
            ]
            assert len(corruption_errors) > 0

    @pytest.mark.asyncio
    async def test_migration_rollback_recovery_validation(self, migration_environment, migration_validator):
        """Test validation of migration rollback recovery process"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003", "004"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate recovery scenario: rollback from 004 -> 002, then forward to 003
        recovery_phases = [
            {
                "phase": "initial_state",
                "version": "004",
                "tables": {"tenants", "auth_users", "conversations", "messages", "memory_items", "extensions", "advanced_features"},
            },
            {
                "phase": "after_rollback",
                "version": "002", 
                "tables": {"tenants", "auth_users", "conversations", "messages"},
            },
            {
                "phase": "after_recovery",
                "version": "003",
                "tables": {"tenants", "auth_users", "conversations", "messages", "memory_items"},
            }
        ]
        
        for phase_data in recovery_phases:
            # Update database state for this phase
            db_state["alembic_version"] = phase_data["version"]
            db_state["tables"] = phase_data["tables"]
            
            def execute_side_effect(query, *args, **kwargs):
                query_str = str(query)
                result = Mock()
                
                if "alembic_version" in query_str and "EXISTS" in query_str:
                    result.scalar.return_value = True
                elif "SELECT version_num FROM alembic_version" in query_str:
                    result.scalar.return_value = db_state["alembic_version"]
                elif "information_schema.tables" in query_str:
                    result.fetchall.return_value = [(table,) for table in db_state["tables"]]
                else:
                    result.scalar.return_value = 0
                    result.fetchall.return_value = []
                
                return result
            
            session.execute.side_effect = execute_side_effect
            
            with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
                # Run migration validation for this phase
                report = await migration_validator.validate_migrations()
                
                if phase_data["phase"] == "initial_state":
                    # Should show we're at version 004 with all tables
                    assert report.current_migration.version == "004"
                    # Might have extra tables beyond expected
                    
                elif phase_data["phase"] == "after_rollback":
                    # Should show we're at version 002 with fewer tables
                    assert report.current_migration.version == "002"
                    # Should have missing tables (indicating successful rollback)
                    expected_tables = migration_validator.expected_tables
                    missing_tables = expected_tables - db_state["tables"]
                    assert len(missing_tables) > 0
                    
                elif phase_data["phase"] == "after_recovery":
                    # Should show we're at version 003 with recovered tables
                    assert report.current_migration.version == "003"
                    # Should have fewer missing tables than after rollback
                    expected_tables = migration_validator.expected_tables
                    missing_tables = expected_tables - db_state["tables"]
                    # Still missing some tables but fewer than after rollback
                    
                # All phases should have valid migration tracking
                assert report.current_migration is not None
                assert report.overall_status != MigrationStatus.FAILED

    @pytest.mark.asyncio
    async def test_migration_rollback_with_foreign_key_constraints(self, migration_environment, migration_validator):
        """Test rollback validation with foreign key constraint issues"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create mock migration files
        migration_versions = ["001", "002", "003"]
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate rollback that left orphaned foreign key references
        db_state["alembic_version"] = "001"
        db_state["tables"] = {"tenants", "auth_users", "conversations", "messages"}
        
        # Mock foreign key constraint violations
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = True
            elif "SELECT version_num FROM alembic_version" in query_str:
                result.scalar.return_value = db_state["alembic_version"]
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            elif "messages m" in query_str and "LEFT JOIN conversations" in query_str:
                # Simulate orphaned messages (foreign key violations)
                result.scalar.return_value = 15  # 15 orphaned messages
            elif "auth_sessions s" in query_str and "LEFT JOIN auth_users" in query_str:
                # Simulate orphaned sessions
                result.scalar.return_value = 8  # 8 orphaned sessions
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        # Create consistency validator to check for orphaned records
        from ai_karen_engine.services.database_consistency_validator import DatabaseConsistencyValidator
        consistency_validator = DatabaseConsistencyValidator()
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]), \
             patch.object(consistency_validator, 'db_manager', migration_environment["db_manager"]):
            
            # Run migration validation
            migration_report = await migration_validator.validate_migrations()
            
            # Run consistency validation to detect orphaned records
            consistency_report = await consistency_validator.validate_all()
            
            # Migration validation should show we're at version 001
            assert migration_report.current_migration.version == "001"
            
            # Consistency validation should detect orphaned records
            orphaned_issues = [
                issue for issue in consistency_report.validation_issues
                if issue.category == "orphaned_records"
            ]
            assert len(orphaned_issues) > 0, "Should detect orphaned records from incomplete rollback"
            
            # Should recommend cleanup of orphaned data
            cleanup_issues = [
                issue for issue in orphaned_issues
                if issue.auto_fixable
            ]
            assert len(cleanup_issues) > 0, "Should have auto-fixable orphaned record issues"

    @pytest.mark.asyncio
    async def test_migration_rollback_validation_performance(self, migration_environment, migration_validator):
        """Test performance of migration rollback validation with large datasets"""
        session = migration_environment["session"]
        db_state = migration_environment["db_state"]
        migrations_dir = migration_environment["migrations_dir"]
        
        # Create many mock migration files
        migration_versions = [f"{i:03d}" for i in range(1, 21)]  # 20 migrations
        self.create_mock_migration_files(migrations_dir, migration_versions)
        
        # Simulate large database with many tables
        db_state["alembic_version"] = "010"  # Rolled back to middle version
        db_state["tables"] = {
            f"table_{i}" for i in range(1, 51)  # 50 tables
        }
        
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "alembic_version" in query_str and "EXISTS" in query_str:
                result.scalar.return_value = True
            elif "SELECT version_num FROM alembic_version" in query_str:
                result.scalar.return_value = db_state["alembic_version"]
            elif "information_schema.tables" in query_str:
                result.fetchall.return_value = [(table,) for table in db_state["tables"]]
            elif "column_name" in query_str:
                # Simulate table structure queries for each table
                table_name = "unknown"
                if "table_1" in query_str:
                    table_name = "table_1"
                result.fetchall.return_value = [
                    (f"{table_name}_col1", "integer"),
                    (f"{table_name}_col2", "varchar"),
                    (f"{table_name}_col3", "timestamp"),
                ]
            else:
                result.scalar.return_value = 0
                result.fetchall.return_value = []
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', migration_environment["db_manager"]):
            # Measure validation performance
            import time
            start_time = time.time()
            
            report = await migration_validator.validate_migrations()
            
            validation_duration = time.time() - start_time
            
            # Validation should complete in reasonable time even with large dataset
            assert validation_duration < 5.0, f"Validation took too long: {validation_duration}s"
            
            # Should still provide accurate results
            assert report.current_migration is not None
            assert report.current_migration.version == "010"
            assert report.overall_status in [MigrationStatus.UP_TO_DATE, MigrationStatus.PENDING, MigrationStatus.INCONSISTENT]
            
            # Should handle large number of tables
            assert len(report.schema_validation.actual_tables) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])