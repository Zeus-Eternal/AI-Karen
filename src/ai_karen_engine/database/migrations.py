"""Database migration manager with Alembic integration."""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text, MetaData, inspect

from .models import Base, Tenant
from .client import MultiTenantPostgresClient


logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations for multi-tenant architecture."""
    
    def __init__(self, database_url: Optional[str] = None, migrations_dir: Optional[str] = None):
        """Initialize migration manager.
        
        Args:
            database_url: PostgreSQL connection URL
            migrations_dir: Directory for migration files
        """
        self.database_url = database_url or self._build_database_url()
        self.migrations_dir = migrations_dir or os.path.join(os.getcwd(), "migrations")
        self.client = MultiTenantPostgresClient(database_url)
        
        # Ensure migrations directory exists
        Path(self.migrations_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize Alembic configuration
        self.alembic_cfg = self._create_alembic_config()
    
    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database = os.getenv("POSTGRES_DB", "ai_karen")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _create_alembic_config(self) -> Config:
        """Create Alembic configuration."""
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", self.migrations_dir)
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
        alembic_cfg.set_main_option("file_template", "%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s")
        
        return alembic_cfg
    
    def initialize_alembic(self) -> bool:
        """Initialize Alembic in the migrations directory.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Check if already initialized
            if os.path.exists(os.path.join(self.migrations_dir, "alembic.ini")):
                logger.info("Alembic already initialized")
                return True
            
            # Initialize Alembic
            command.init(self.alembic_cfg, self.migrations_dir)
            
            # Create custom env.py for multi-tenant support
            self._create_custom_env_py()
            
            logger.info(f"Alembic initialized in {self.migrations_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Alembic: {e}")
            return False
    
    def _create_custom_env_py(self):
        """Create custom env.py for multi-tenant migrations."""
        env_py_content = '''"""Multi-tenant Alembic environment."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.ai_karen_engine.database.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        env_py_path = os.path.join(self.migrations_dir, "env.py")
        with open(env_py_path, "w") as f:
            f.write(env_py_content)
    
    def create_initial_migration(self) -> bool:
        """Create initial migration for shared tables.
        
        Returns:
            True if migration was created successfully
        """
        try:
            # Create initial migration
            command.revision(
                self.alembic_cfg,
                message="Initial migration - shared tables",
                autogenerate=True
            )
            
            logger.info("Initial migration created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create initial migration: {e}")
            return False
    
    def run_migrations(self, revision: str = "head") -> bool:
        """Run database migrations.
        
        Args:
            revision: Target revision (default: head)
            
        Returns:
            True if migrations ran successfully
        """
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"Migrations upgraded to {revision}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False
    
    def rollback_migration(self, revision: str) -> bool:
        """Rollback to a specific migration.
        
        Args:
            revision: Target revision to rollback to
            
        Returns:
            True if rollback was successful
        """
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Rolled back to revision {revision}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            return False
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history.
        
        Returns:
            List of migration records
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            
            with self.client.sync_engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                
            history = []
            for revision in script.walk_revisions():
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "message": revision.doc,
                    "is_current": revision.revision == current_rev
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def create_tenant_migration(self, message: str) -> bool:
        """Create a new migration for tenant-specific changes.
        
        Args:
            message: Migration message
            
        Returns:
            True if migration was created successfully
        """
        try:
            command.revision(
                self.alembic_cfg,
                message=message,
                autogenerate=True
            )
            
            logger.info(f"Tenant migration created: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tenant migration: {e}")
            return False
    
    def setup_tenant_database(self, tenant_id: str, tenant_name: str, tenant_slug: str) -> bool:
        """Set up database for a new tenant.
        
        Args:
            tenant_id: Tenant UUID
            tenant_name: Tenant name
            tenant_slug: Tenant slug
            
        Returns:
            True if setup was successful
        """
        try:
            # Create tenant record in shared table
            with self.client.get_sync_session() as session:
                tenant = Tenant(
                    id=uuid.UUID(tenant_id),
                    name=tenant_name,
                    slug=tenant_slug,
                    subscription_tier="basic"
                )
                session.add(tenant)
                session.commit()
            
            # Create tenant schema and tables
            success = self.client.create_tenant_schema(tenant_id)
            if not success:
                # Rollback tenant creation
                with self.client.get_sync_session() as session:
                    tenant = session.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
                    if tenant:
                        session.delete(tenant)
                        session.commit()
                return False
            
            logger.info(f"Tenant database setup completed for {tenant_slug}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup tenant database: {e}")
            return False
    
    def teardown_tenant_database(self, tenant_id: str) -> bool:
        """Teardown database for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if teardown was successful
        """
        try:
            # Drop tenant schema
            success = self.client.drop_tenant_schema(tenant_id)
            if not success:
                return False
            
            # Remove tenant record from shared table
            with self.client.get_sync_session() as session:
                tenant = session.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
                if tenant:
                    session.delete(tenant)
                    session.commit()
            
            logger.info(f"Tenant database teardown completed for {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to teardown tenant database: {e}")
            return False
    
    def validate_tenant_schema(self, tenant_id: str) -> Dict[str, Any]:
        """Validate tenant schema integrity.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Validation results
        """
        results = {
            "tenant_id": tenant_id,
            "schema_exists": False,
            "tables_exist": {},
            "indexes_exist": {},
            "errors": []
        }
        
        try:
            # Check if schema exists
            results["schema_exists"] = self.client.tenant_schema_exists(tenant_id)
            
            if not results["schema_exists"]:
                results["errors"].append("Tenant schema does not exist")
                return results
            
            schema_name = self.client.get_tenant_schema_name(tenant_id)
            
            # Check tables
            expected_tables = ["conversations", "memory_entries", "plugin_executions", "audit_logs"]
            
            with self.client.sync_engine.connect() as conn:
                inspector = inspect(conn)
                existing_tables = inspector.get_table_names(schema=schema_name)
                
                for table in expected_tables:
                    exists = table in existing_tables
                    results["tables_exist"][table] = exists
                    if not exists:
                        results["errors"].append(f"Table {table} does not exist in schema {schema_name}")
                
                # Check indexes for existing tables
                for table in expected_tables:
                    if table in existing_tables:
                        indexes = inspector.get_indexes(table, schema=schema_name)
                        results["indexes_exist"][table] = len(indexes)
            
        except Exception as e:
            results["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"Failed to validate tenant schema: {e}")
        
        return results
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get overall database status.
        
        Returns:
            Database status information
        """
        status = {
            "database_url": self.database_url.split("@")[-1],  # Hide credentials
            "migrations_dir": self.migrations_dir,
            "alembic_initialized": False,
            "current_revision": None,
            "pending_migrations": 0,
            "tenant_count": 0,
            "health": "unknown"
        }
        
        try:
            # Check Alembic initialization
            status["alembic_initialized"] = os.path.exists(os.path.join(self.migrations_dir, "alembic.ini"))
            
            # Get current revision
            if status["alembic_initialized"]:
                with self.client.sync_engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    status["current_revision"] = context.get_current_revision()
            
            # Get tenant count
            with self.client.get_sync_session() as session:
                status["tenant_count"] = session.query(Tenant).count()
            
            # Health check
            health_result = self.client.health_check()
            status["health"] = health_result["status"]
            
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Failed to get database status: {e}")
        
        return status