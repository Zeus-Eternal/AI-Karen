"""Multi-tenant PostgreSQL client with schema-per-tenant architecture."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

try:
    import asyncpg
    from sqlalchemy import create_engine, text, MetaData, inspect
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    _ASYNC_AVAILABLE = True
except ImportError:
    asyncpg = None
    create_async_engine = None
    AsyncSession = None
    async_sessionmaker = None
    _ASYNC_AVAILABLE = False

from ai_karen_engine.database.models import (
    Base,
    Tenant,
    User,
    TenantConversation,
    TenantMemoryEntry,
    TenantPluginExecution,
    TenantAuditLog,
)


logger = logging.getLogger(__name__)


class MultiTenantPostgresClient:
    """Enhanced PostgreSQL client with multi-tenant schema support."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ):
        """Initialize the multi-tenant PostgreSQL client.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Pool timeout in seconds
            pool_recycle: Pool recycle time in seconds
        """
        self.database_url = database_url or self._build_database_url()
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        
        # Initialize engines
        self._sync_engine = None
        self._async_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        
        # Cache for tenant schemas
        self._tenant_schemas: Dict[str, bool] = {}
        
        self._initialize_engines()
    
    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database = os.getenv("POSTGRES_DB", "ai_karen")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _initialize_engines(self):
        """Initialize SQLAlchemy engines."""
        # Sync engine
        self._sync_engine = create_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
        )
        
        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            expire_on_commit=False
        )
        
        # Async engine (if available)
        if _ASYNC_AVAILABLE:
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self._async_engine = create_async_engine(
                async_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
            )
            
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
    
    @property
    def sync_engine(self):
        """Get synchronous SQLAlchemy engine."""
        return self._sync_engine
    
    @property
    def async_engine(self):
        """Get asynchronous SQLAlchemy engine."""
        return self._async_engine
    
    def get_sync_session(self):
        """Get synchronous database session."""
        return self._sync_session_factory()
    
    @asynccontextmanager
    async def get_async_session(self):
        """Get asynchronous database session context manager."""
        if not _ASYNC_AVAILABLE or not self._async_session_factory:
            raise RuntimeError("Async support not available")
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def create_shared_tables(self):
        """Create shared tables (tenants, users) in the public schema."""
        try:
            # Create only shared tables
            shared_tables = [Tenant.__table__, User.__table__]
            for table in shared_tables:
                table.create(self._sync_engine, checkfirst=True)
            logger.info("Shared tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create shared tables: {e}")
            raise
    
    def get_tenant_schema_name(self, tenant_id: Union[str, uuid.UUID]) -> str:
        """Get schema name for a tenant."""
        if isinstance(tenant_id, uuid.UUID):
            tenant_id = str(tenant_id)
        # Remove hyphens and use only alphanumeric characters for schema name
        clean_id = tenant_id.replace("-", "")
        return f"tenant_{clean_id}"
    
    def create_tenant_schema(self, tenant_id: Union[str, uuid.UUID]) -> bool:
        """Create schema and tables for a new tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if schema was created successfully
        """
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        try:
            with self._sync_engine.connect() as conn:
                # Create schema
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                
                # Create tenant-specific tables
                tenant_tables = [
                    TenantConversation.__table__,
                    TenantMemoryEntry.__table__,
                    TenantPluginExecution.__table__,
                    TenantAuditLog.__table__
                ]
                
                for table in tenant_tables:
                    # Create table in tenant schema
                    table_sql = str(table.compile(self._sync_engine)).replace(
                        f'CREATE TABLE {table.name}',
                        f'CREATE TABLE IF NOT EXISTS {schema_name}.{table.name}'
                    )
                    conn.execute(text(table_sql))
                
                conn.commit()
                
            # Cache the schema
            self._tenant_schemas[str(tenant_id)] = True
            logger.info(f"Created tenant schema: {schema_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tenant schema {schema_name}: {e}")
            return False
    
    def drop_tenant_schema(self, tenant_id: Union[str, uuid.UUID]) -> bool:
        """Drop schema and all data for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if schema was dropped successfully
        """
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        try:
            with self._sync_engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()
            
            # Remove from cache
            self._tenant_schemas.pop(str(tenant_id), None)
            logger.info(f"Dropped tenant schema: {schema_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop tenant schema {schema_name}: {e}")
            return False
    
    def tenant_schema_exists(self, tenant_id: Union[str, uuid.UUID]) -> bool:
        """Check if tenant schema exists.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if schema exists
        """
        tenant_id_str = str(tenant_id)
        
        # Check cache first
        if tenant_id_str in self._tenant_schemas:
            return self._tenant_schemas[tenant_id_str]
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        try:
            with self._sync_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name)"
                ), {"schema_name": schema_name})
                exists = result.scalar()
                
            # Cache the result
            self._tenant_schemas[tenant_id_str] = exists
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check tenant schema {schema_name}: {e}")
            return False

    def ensure_memory_table(self, tenant_id: Union[str, uuid.UUID]) -> bool:
        """Ensure memory_entries table exists for the tenant."""
        schema_name = self.get_tenant_schema_name(tenant_id)

        try:
            with self._sync_engine.connect() as conn:
                inspector = inspect(conn)
                if "memory_entries" not in inspector.get_table_names(schema=schema_name):
                    logger.warning(
                        f"[FATAL] memory_entries table missing for tenant {tenant_id}; creating"
                    )
                    self.create_tenant_schema(tenant_id)
                else:
                    logger.info(
                        f"memory_entries table confirmed for tenant {tenant_id}"
                    )
            return True
        except Exception as e:
            logger.error(f"Failed to ensure memory table for tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_table_name(self, table_name: str, tenant_id: Union[str, uuid.UUID]) -> str:
        """Get fully qualified table name for tenant.
        
        Args:
            table_name: Base table name
            tenant_id: Tenant UUID
            
        Returns:
            Fully qualified table name with schema
        """
        schema_name = self.get_tenant_schema_name(tenant_id)
        return f"{schema_name}.{table_name}"
    
    def execute_tenant_query(
        self,
        query: str,
        tenant_id: Union[str, uuid.UUID],
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a query in tenant context.
        
        Args:
            query: SQL query
            tenant_id: Tenant UUID
            params: Query parameters
            
        Returns:
            Query result
        """
        if not self.tenant_schema_exists(tenant_id):
            raise ValueError(f"Tenant schema does not exist: {tenant_id}")
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        try:
            with self._sync_engine.connect() as conn:
                # Set search path to tenant schema
                conn.execute(text(f"SET search_path TO {schema_name}, public"))
                result = conn.execute(text(query), params or {})
                conn.commit()
                return result
                
        except Exception as e:
            logger.error(f"Failed to execute tenant query: {e}")
            raise
    
    async def execute_tenant_query_async(
        self,
        query: str,
        tenant_id: Union[str, uuid.UUID],
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a query in tenant context asynchronously.
        
        Args:
            query: SQL query
            tenant_id: Tenant UUID
            params: Query parameters
            
        Returns:
            Query result
        """
        if not _ASYNC_AVAILABLE:
            raise RuntimeError("Async support not available")
        
        if not self.tenant_schema_exists(tenant_id):
            raise ValueError(f"Tenant schema does not exist: {tenant_id}")
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        try:
            async with self._async_engine.connect() as conn:
                # Set search path to tenant schema
                await conn.execute(text(f"SET search_path TO {schema_name}, public"))
                result = await conn.execute(text(query), params or {})
                await conn.commit()
                return result
                
        except Exception as e:
            logger.error(f"Failed to execute async tenant query: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on database connection.
        
        Returns:
            Health check results
        """
        try:
            with self._sync_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                conn.commit()
                
            return {
                "status": "healthy",
                "database_url": self.database_url.split("@")[-1],  # Hide credentials
                "pool_size": self.pool_size,
                "async_available": _ASYNC_AVAILABLE,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_tenant_stats(self, tenant_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Get statistics for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Tenant statistics
        """
        if not self.tenant_schema_exists(tenant_id):
            return {"error": "Tenant schema does not exist"}
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        stats = {}
        
        try:
            with self._sync_engine.connect() as conn:
                # Set search path
                conn.execute(text(f"SET search_path TO {schema_name}, public"))
                
                # Get table counts
                tables = ["conversations", "memory_entries", "plugin_executions", "audit_logs"]
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[f"{table}_count"] = result.scalar()
                
                # Get schema size
                result = conn.execute(text("""
                    SELECT pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint)
                    FROM pg_tables WHERE schemaname = :schema_name
                """), {"schema_name": schema_name})
                stats["schema_size"] = result.scalar()
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            stats["error"] = str(e)
        
        return stats
    
    def close(self):
        """Close database connections."""
        if self._sync_engine:
            self._sync_engine.dispose()
        if self._async_engine:
            asyncio.create_task(self._async_engine.dispose())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()