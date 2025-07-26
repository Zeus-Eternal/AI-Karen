"""Multi-tenant PostgreSQL client with schema-per-tenant architecture."""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

try:
    import asyncpg
    from sqlalchemy import create_engine, text, MetaData, inspect
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError, DisconnectionError
    _ASYNC_AVAILABLE = True
except ImportError:
    asyncpg = None
    create_async_engine = None
    AsyncSession = None
    async_sessionmaker = None
    SQLAlchemyError = Exception
    OperationalError = Exception
    DatabaseError = Exception
    DisconnectionError = Exception
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
from ai_karen_engine.database.config import (
    DatabaseConfig,
    load_database_config,
    DatabaseConfigurationError
)


logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""
    
    def __init__(self, message: str, error_type: str = "unknown", original_error: Exception = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error


class ConnectionRetryManager:
    """Manages connection retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, operation, operation_name: str = "database operation"):
        """Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            operation_name: Name of the operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            DatabaseConnectionError: If all retries are exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)
                
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries} retry attempts failed for {operation_name}")
                    raise DatabaseConnectionError(
                        f"Failed to execute {operation_name} after {self.max_retries} retries: {str(e)}",
                        error_type=error_type,
                        original_error=e
                    )
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed for {operation_name} "
                    f"({error_type}): {str(e)}. Retrying in {delay:.1f}s..."
                )
                
                # Only retry for certain error types
                if not self._should_retry(error_type):
                    logger.error(f"Error type '{error_type}' is not retryable, aborting")
                    raise DatabaseConnectionError(
                        f"Non-retryable error in {operation_name}: {str(e)}",
                        error_type=error_type,
                        original_error=e
                    )
                
                time.sleep(delay)
        
        # This should never be reached, but just in case
        raise DatabaseConnectionError(
            f"Unexpected error in retry logic for {operation_name}",
            original_error=last_error
        )
    
    def _classify_error(self, error: Exception) -> str:
        """Classify the type of database error.
        
        Args:
            error: Exception to classify
            
        Returns:
            Error type string
        """
        error_str = str(error).lower()
        
        # Authentication errors
        if any(phrase in error_str for phrase in [
            "password authentication failed",
            "authentication failed",
            "invalid authorization",
            "access denied"
        ]):
            return "authentication"
        
        # Connection errors
        if any(phrase in error_str for phrase in [
            "connection refused",
            "could not connect",
            "connection timed out",
            "network is unreachable",
            "no route to host"
        ]):
            return "connection"
        
        # Database not found
        if any(phrase in error_str for phrase in [
            "database does not exist",
            "database not found",
            "unknown database"
        ]):
            return "database_not_found"
        
        # Permission errors
        if any(phrase in error_str for phrase in [
            "permission denied",
            "insufficient privileges",
            "access denied"
        ]):
            return "permission"
        
        # Pool exhaustion
        if any(phrase in error_str for phrase in [
            "pool limit",
            "connection pool",
            "too many connections"
        ]):
            return "pool_exhausted"
        
        # Timeout errors
        if any(phrase in error_str for phrase in [
            "timeout",
            "timed out"
        ]):
            return "timeout"
        
        # SQL errors (syntax, constraint violations, etc.)
        if isinstance(error, (SQLAlchemyError, DatabaseError)):
            if isinstance(error, OperationalError):
                return "operational"
            elif isinstance(error, DisconnectionError):
                return "disconnection"
            else:
                return "sql_error"
        
        return "unknown"
    
    def _should_retry(self, error_type: str) -> bool:
        """Determine if an error type should be retried.
        
        Args:
            error_type: Error type string
            
        Returns:
            True if the error should be retried
        """
        # Retryable errors
        retryable_errors = {
            "connection",
            "timeout", 
            "pool_exhausted",
            "disconnection",
            "operational"
        }
        
        # Non-retryable errors
        non_retryable_errors = {
            "authentication",
            "database_not_found",
            "permission",
            "sql_error"
        }
        
        if error_type in retryable_errors:
            return True
        elif error_type in non_retryable_errors:
            return False
        else:
            # For unknown errors, be conservative and retry
            return True


class MultiTenantPostgresClient:
    """Enhanced PostgreSQL client with multi-tenant schema support."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        config: Optional[DatabaseConfig] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[int] = None,
        pool_recycle: Optional[int] = None
    ):
        """Initialize the multi-tenant PostgreSQL client.
        
        Args:
            database_url: PostgreSQL connection URL (deprecated, use config instead)
            config: DatabaseConfig instance with validated configuration
            pool_size: Connection pool size (overrides config if provided)
            max_overflow: Maximum overflow connections (overrides config if provided)
            pool_timeout: Pool timeout in seconds (overrides config if provided)
            pool_recycle: Pool recycle time in seconds (overrides config if provided)
        """
        # Load configuration if not provided
        if config is None:
            try:
                config = load_database_config()
                logger.info("Database configuration loaded successfully from environment")
            except DatabaseConfigurationError as e:
                logger.error(f"Database configuration error: {e}")
                # Log detailed errors for troubleshooting
                for error in e.errors:
                    logger.error(f"  Configuration error: {error}")
                for warning in e.warnings:
                    logger.warning(f"  Configuration warning: {warning}")
                raise
            except Exception as e:
                logger.error(f"Failed to load database configuration: {e}")
                # Fall back to legacy method if configuration loading fails
                logger.warning("Falling back to legacy environment variable loading")
                config = self._create_fallback_config()
        
        self.config = config
        
        # Use provided URL or build from config
        if database_url:
            logger.warning("database_url parameter is deprecated, use config parameter instead")
            self.database_url = database_url
        else:
            self.database_url = config.build_database_url()
        
        # Use provided pool settings or config defaults
        self.pool_size = pool_size if pool_size is not None else config.pool_size
        self.max_overflow = max_overflow if max_overflow is not None else config.max_overflow
        self.pool_timeout = pool_timeout if pool_timeout is not None else config.pool_timeout
        self.pool_recycle = pool_recycle if pool_recycle is not None else config.pool_recycle
        
        # Initialize engines
        self._sync_engine = None
        self._async_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        
        # Cache for tenant schemas
        self._tenant_schemas: Dict[str, bool] = {}
        
        # Initialize retry manager
        self._retry_manager = ConnectionRetryManager(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        )
        
        # Log sanitized configuration for debugging
        sanitized_config = config.get_sanitized_config()
        logger.info(f"Initializing database client with configuration: {sanitized_config}")
        
        self._initialize_engines()
    
    def _create_fallback_config(self) -> DatabaseConfig:
        """Create fallback configuration using legacy environment variable loading."""
        return DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            database=os.getenv("POSTGRES_DB", "ai_karen"),
            debug_sql=os.getenv("SQL_DEBUG", "false").lower() == "true"
        )
    
    def _build_database_url(self) -> str:
        """Build database URL from validated configuration.
        
        This method is deprecated - use config.build_database_url() instead.
        Kept for backward compatibility.
        
        Returns:
            Database URL string
            
        Raises:
            DatabaseConfigurationError: If configuration is invalid
        """
        logger.warning("_build_database_url() is deprecated, use config.build_database_url() instead")
        
        if hasattr(self, 'config') and self.config:
            return self.config.build_database_url()
        
        # Fallback to legacy method for backward compatibility
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database = os.getenv("POSTGRES_DB", "ai_karen")
        
        # Basic validation
        if not all([host, port, user, database]):
            raise DatabaseConfigurationError("Missing required database configuration parameters")
        
        try:
            port = int(port)
        except ValueError:
            raise DatabaseConfigurationError(f"Invalid port number: {port}")
        
        # Handle special characters in password
        if password:
            password_encoded = password.replace("@", "%40").replace(":", "%3A").replace("/", "%2F")
        else:
            password_encoded = ""
            logger.warning("Database password is empty - this may cause authentication failures")
        
        return f"postgresql://{user}:{password_encoded}@{host}:{port}/{database}"
    
    def _initialize_engines(self):
        """Initialize SQLAlchemy engines with retry logic and comprehensive error handling."""
        def _create_sync_engine():
            """Create synchronous engine with error handling."""
            try:
                engine = create_engine(
                    self.database_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    echo=self.config.debug_sql,
                    # Add connection validation
                    pool_pre_ping=True,
                    # Set reasonable connection timeout
                    connect_args={
                        "connect_timeout": 10,
                        "application_name": "ai_karen_multitenant_client"
                    }
                )
                
                # Test the connection immediately
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    conn.commit()
                
                return engine
                
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to create sync engine ({error_type}): {e}")
                
                # Provide specific error guidance
                if error_type == "authentication":
                    logger.error("Authentication failed. Please check:")
                    logger.error("  - POSTGRES_USER environment variable")
                    logger.error("  - POSTGRES_PASSWORD environment variable")
                    logger.error("  - Database user permissions")
                elif error_type == "connection":
                    logger.error("Connection failed. Please check:")
                    logger.error("  - POSTGRES_HOST environment variable")
                    logger.error("  - POSTGRES_PORT environment variable")
                    logger.error("  - Database server is running")
                    logger.error("  - Network connectivity")
                elif error_type == "database_not_found":
                    logger.error("Database not found. Please check:")
                    logger.error("  - POSTGRES_DB environment variable")
                    logger.error("  - Database exists on the server")
                
                raise DatabaseConnectionError(
                    f"Failed to initialize sync database engine: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        def _create_async_engine():
            """Create asynchronous engine with error handling."""
            if not _ASYNC_AVAILABLE:
                logger.warning("Async database support not available (missing asyncpg)")
                return None
            
            try:
                async_url = self.config.build_async_database_url()
                engine = create_async_engine(
                    async_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    echo=self.config.debug_sql,
                    # Add connection validation
                    pool_pre_ping=True
                )
                
                return engine
                
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to create async engine ({error_type}): {e}")
                
                raise DatabaseConnectionError(
                    f"Failed to initialize async database engine: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        try:
            # Create sync engine with retry logic
            logger.info("Initializing synchronous database engine...")
            self._sync_engine = self._retry_manager.execute_with_retry(
                _create_sync_engine,
                "sync engine initialization"
            )
            
            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine,
                expire_on_commit=False
            )
            
            logger.info(f"Successfully initialized synchronous database engine with pool_size={self.pool_size}")
            
            # Create async engine (if available)
            if _ASYNC_AVAILABLE:
                logger.info("Initializing asynchronous database engine...")
                try:
                    self._async_engine = self._retry_manager.execute_with_retry(
                        _create_async_engine,
                        "async engine initialization"
                    )
                    
                    if self._async_engine:
                        self._async_session_factory = async_sessionmaker(
                            bind=self._async_engine,
                            class_=AsyncSession,
                            expire_on_commit=False
                        )
                        logger.info("Successfully initialized asynchronous database engine")
                    
                except DatabaseConnectionError as e:
                    logger.warning(f"Failed to initialize async engine, continuing with sync only: {e}")
                    self._async_engine = None
                    self._async_session_factory = None
            else:
                logger.info("Async database support not available (missing asyncpg)")
                
        except DatabaseConnectionError:
            # Re-raise database connection errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during engine initialization: {e}")
            raise DatabaseConnectionError(
                f"Unexpected error during database engine initialization: {str(e)}",
                error_type="initialization_error",
                original_error=e
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
        """Create schema and tables for a new tenant with retry logic.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if schema was created successfully
        """
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        def _create_schema():
            """Create the tenant schema with error handling."""
            try:
                with self._sync_engine.connect() as conn:
                    # Create schema
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                    conn.commit()
                    
                    # Create tenant-specific tables using direct SQL approach
                    tenant_table_definitions = {
                        'conversations': '''
                            CREATE TABLE IF NOT EXISTS {schema}.conversations (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                tenant_id UUID NOT NULL,
                                user_id UUID,
                                title VARCHAR(255),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                metadata JSONB DEFAULT '{{}}'::jsonb
                            )
                        ''',
                        'memory_entries': '''
                            CREATE TABLE IF NOT EXISTS {schema}.memory_entries (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                tenant_id UUID NOT NULL,
                                user_id UUID,
                                content TEXT NOT NULL,
                                embedding_vector FLOAT8[],
                                metadata JSONB DEFAULT '{{}}'::jsonb,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                            )
                        ''',
                        'plugin_executions': '''
                            CREATE TABLE IF NOT EXISTS {schema}.plugin_executions (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                tenant_id UUID NOT NULL,
                                user_id UUID,
                                plugin_name VARCHAR(255) NOT NULL,
                                execution_data JSONB DEFAULT '{{}}'::jsonb,
                                status VARCHAR(50) DEFAULT 'pending',
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                completed_at TIMESTAMP WITH TIME ZONE
                            )
                        ''',
                        'audit_logs': '''
                            CREATE TABLE IF NOT EXISTS {schema}.audit_logs (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                tenant_id UUID NOT NULL,
                                user_id UUID,
                                action VARCHAR(255) NOT NULL,
                                resource_type VARCHAR(100),
                                resource_id UUID,
                                details JSONB DEFAULT '{{}}'::jsonb,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                            )
                        '''
                    }
                    
                    for table_name, table_sql in tenant_table_definitions.items():
                        try:
                            formatted_sql = table_sql.format(schema=schema_name).strip()
                            conn.execute(text(formatted_sql))
                            logger.debug(f"Created table {table_name} in schema {schema_name}")
                        except Exception as table_error:
                            logger.error(f"Failed to create table {table_name} in schema {schema_name}: {table_error}")
                            raise
                    
                    conn.commit()
                    
                # Cache the schema
                self._tenant_schemas[str(tenant_id)] = True
                logger.info(f"Created tenant schema: {schema_name}")
                return True
                
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to create tenant schema {schema_name} ({error_type}): {e}")
                
                raise DatabaseConnectionError(
                    f"Failed to create tenant schema {schema_name}: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        try:
            return self._retry_manager.execute_with_retry(
                _create_schema,
                f"tenant schema creation for {tenant_id}"
            )
        except DatabaseConnectionError as e:
            logger.error(f"All retry attempts failed for creating tenant schema {schema_name}: {e}")
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
        """Ensure memory_entries table exists for the tenant with retry logic."""
        schema_name = self.get_tenant_schema_name(tenant_id)

        def _ensure_table():
            """Ensure the memory table exists with error handling."""
            try:
                with self._sync_engine.connect() as conn:
                    inspector = inspect(conn)
                    if "memory_entries" not in inspector.get_table_names(schema=schema_name):
                        logger.warning(
                            f"[FATAL] memory_entries table missing for tenant {tenant_id}; creating"
                        )
                        # Use the enhanced create_tenant_schema method which already has retry logic
                        if not self.create_tenant_schema(tenant_id):
                            raise DatabaseConnectionError(
                                f"Failed to create tenant schema for {tenant_id}",
                                error_type="schema_creation_failed"
                            )
                    else:
                        logger.info(
                            f"memory_entries table confirmed for tenant {tenant_id}"
                        )
                return True
                
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to ensure memory table for tenant {tenant_id} ({error_type}): {e}")
                
                raise DatabaseConnectionError(
                    f"Failed to ensure memory table for tenant {tenant_id}: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )

        try:
            return self._retry_manager.execute_with_retry(
                _ensure_table,
                f"memory table verification for {tenant_id}"
            )
        except DatabaseConnectionError as e:
            logger.error(f"All retry attempts failed for ensuring memory table for tenant {tenant_id}: {e}")
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
        """Execute a query in tenant context with retry logic.
        
        Args:
            query: SQL query
            tenant_id: Tenant UUID
            params: Query parameters
            
        Returns:
            Query result
            
        Raises:
            DatabaseConnectionError: If query execution fails after retries
        """
        if not self.tenant_schema_exists(tenant_id):
            raise ValueError(f"Tenant schema does not exist: {tenant_id}")
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        def _execute_query():
            """Execute the query with error handling."""
            try:
                with self._sync_engine.connect() as conn:
                    # Set search path to tenant schema
                    conn.execute(text(f"SET search_path TO {schema_name}, public"))
                    result = conn.execute(text(query), params or {})
                    conn.commit()
                    return result
                    
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to execute tenant query ({error_type}): {e}")
                
                # Provide context for the error
                logger.error(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
                logger.error(f"Tenant: {tenant_id}")
                logger.error(f"Schema: {schema_name}")
                
                raise DatabaseConnectionError(
                    f"Failed to execute tenant query: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        return self._retry_manager.execute_with_retry(
            _execute_query,
            f"tenant query execution for {tenant_id}"
        )
    
    async def execute_tenant_query_async(
        self,
        query: str,
        tenant_id: Union[str, uuid.UUID],
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a query in tenant context asynchronously with retry logic.
        
        Args:
            query: SQL query
            tenant_id: Tenant UUID
            params: Query parameters
            
        Returns:
            Query result
            
        Raises:
            DatabaseConnectionError: If query execution fails after retries
        """
        if not _ASYNC_AVAILABLE:
            raise RuntimeError("Async support not available")
        
        if not self.tenant_schema_exists(tenant_id):
            raise ValueError(f"Tenant schema does not exist: {tenant_id}")
        
        schema_name = self.get_tenant_schema_name(tenant_id)
        
        async def _execute_async_query():
            """Execute the async query with error handling."""
            try:
                async with self._async_engine.connect() as conn:
                    # Set search path to tenant schema
                    await conn.execute(text(f"SET search_path TO {schema_name}, public"))
                    result = await conn.execute(text(query), params or {})
                    await conn.commit()
                    return result
                    
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Failed to execute async tenant query ({error_type}): {e}")
                
                # Provide context for the error
                logger.error(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
                logger.error(f"Tenant: {tenant_id}")
                logger.error(f"Schema: {schema_name}")
                
                raise DatabaseConnectionError(
                    f"Failed to execute async tenant query: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        # Note: For async operations, we need to handle retry differently
        # For now, we'll use a simple retry without the retry manager
        # since the retry manager is synchronous
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                return await _execute_async_query()
            except DatabaseConnectionError as e:
                if attempt == max_retries:
                    logger.error(f"All {max_retries} async retry attempts failed for tenant query")
                    raise
                
                # Only retry for certain error types
                if not self._retry_manager._should_retry(e.error_type):
                    logger.error(f"Error type '{e.error_type}' is not retryable, aborting async query")
                    raise
                
                delay = min(1.0 * (2 ** attempt), 30.0)
                logger.warning(f"Async attempt {attempt + 1}/{max_retries + 1} failed, retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on database connection with retry logic.
        
        Returns:
            Health check results with detailed status information
        """
        def _perform_health_check():
            """Perform the actual health check with error handling."""
            try:
                start_time = time.time()
                
                with self._sync_engine.connect() as conn:
                    # Basic connectivity test
                    result = conn.execute(text("SELECT 1 as test"))
                    test_value = result.scalar()
                    
                    # Get database version and current time
                    version_result = conn.execute(text("SELECT version()"))
                    db_version = version_result.scalar()
                    
                    time_result = conn.execute(text("SELECT NOW()"))
                    db_time = time_result.scalar()
                    
                    # Get connection pool status
                    pool_status = {
                        "size": self._sync_engine.pool.size(),
                        "checked_in": self._sync_engine.pool.checkedin(),
                        "checked_out": self._sync_engine.pool.checkedout(),
                        "overflow": self._sync_engine.pool.overflow()
                    }
                    
                    # Add invalid count if available (not all pool types have this)
                    try:
                        pool_status["invalid"] = self._sync_engine.pool.invalid()
                    except AttributeError:
                        pool_status["invalid"] = "N/A"
                    
                    conn.commit()
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "database_url": self.database_url.split("@")[-1],  # Hide credentials
                    "response_time_ms": round(response_time * 1000, 2),
                    "database_version": db_version.split()[0:2] if db_version else "unknown",  # First two parts
                    "database_time": db_time.isoformat() if db_time else None,
                    "pool_status": pool_status,
                    "pool_config": {
                        "pool_size": self.pool_size,
                        "max_overflow": self.max_overflow,
                        "pool_timeout": self.pool_timeout,
                        "pool_recycle": self.pool_recycle
                    },
                    "async_available": _ASYNC_AVAILABLE,
                    "config_valid": self.config.is_valid() if hasattr(self, 'config') else True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                error_type = self._retry_manager._classify_error(e)
                logger.error(f"Health check failed ({error_type}): {e}")
                
                raise DatabaseConnectionError(
                    f"Database health check failed: {str(e)}",
                    error_type=error_type,
                    original_error=e
                )
        
        try:
            return self._retry_manager.execute_with_retry(
                _perform_health_check,
                "database health check"
            )
        except DatabaseConnectionError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": e.error_type,
                "database_url": self.database_url.split("@")[-1],  # Hide credentials
                "pool_config": {
                    "pool_size": self.pool_size,
                    "max_overflow": self.max_overflow,
                    "pool_timeout": self.pool_timeout,
                    "pool_recycle": self.pool_recycle
                },
                "async_available": _ASYNC_AVAILABLE,
                "config_valid": self.config.is_valid() if hasattr(self, 'config') else False,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Unexpected error during health check: {str(e)}",
                "error_type": "unexpected",
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