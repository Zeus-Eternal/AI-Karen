"""
Production Database Client
SQLAlchemy database connection management with async support
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
import asyncio

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.database.models import Base
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseClient:
    """Production database client with connection pooling and async support"""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with production settings"""
        
        try:
            # Create synchronous engine with connection pooling
            self.engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
                echo=settings.debug,  # Log SQL queries in debug mode
            )
            
            # Create async engine
            async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
            self.async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.debug,
            )
            
            # Create session factories
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.async_engine,
                class_=AsyncSession
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup"""
        
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async database not initialized")
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def async_health_check(self) -> bool:
        """Check database connectivity asynchronously"""
        
        try:
            async with self.get_async_session() as session:
                await session.execute("SELECT 1")
            return True
            
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return False
    
    def get_tenant_schema_name(self, tenant_id: str) -> str:
        """Get schema name for tenant (for multi-tenant support)"""
        return f"tenant_{tenant_id}"
    
    async def create_tables_async(self):
        """Create all database tables asynchronously"""
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully (async)")
            
        except Exception as e:
            logger.error(f"Failed to create database tables (async): {e}")
            raise


# Multi-tenant database client class
class MultiTenantPostgresClient(DatabaseClient):
    """Multi-tenant PostgreSQL client with async support"""
    pass

# Global database client instance
db_client = DatabaseClient()


# Convenience functions
def get_db_session() -> Session:
    """Get a new database session"""
    return db_client.get_session()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    with db_client.session_scope() as session:
        yield session


def create_database_tables():
    """Create all database tables"""
    db_client.create_tables()


def drop_database_tables():
    """Drop all database tables"""
    db_client.drop_tables()


def check_database_health() -> bool:
    """Check database health"""
    return db_client.health_check()
