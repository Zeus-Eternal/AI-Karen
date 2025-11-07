"""
Multi-Database Connection Factory.

This module provides connection factories for different database types:
- MySQL (using SQLAlchemy)
- MongoDB (using PyMongo/Motor)
- Firestore (using Google Cloud Firestore)
"""

import logging
from typing import Any, Optional, Dict
from contextlib import contextmanager, asynccontextmanager

from .multi_db_config import (
    MultiDatabaseConfig,
    DatabaseType,
    MySQLConfig,
    MongoDBConfig,
    FirestoreConfig,
)

logger = logging.getLogger(__name__)


class DatabaseConnectionFactory:
    """Factory for creating database connections based on configuration."""

    def __init__(self, config: MultiDatabaseConfig):
        """
        Initialize the factory with configuration.

        Args:
            config: Multi-database configuration
        """
        self.config = config
        self._validate_config()

        # Connection instances (lazy initialization)
        self._mysql_engine = None
        self._mysql_async_engine = None
        self._mongodb_client = None
        self._firestore_client = None

    def _validate_config(self) -> None:
        """Validate configuration before use."""
        if not self.config.is_valid():
            errors = self.config.validation_errors
            raise ValueError(f"Invalid database configuration: {errors}")

    def get_mysql_engine(self, async_mode: bool = False):
        """
        Get MySQL SQLAlchemy engine.

        Args:
            async_mode: Whether to return async engine

        Returns:
            SQLAlchemy Engine instance

        Raises:
            ImportError: If SQLAlchemy is not installed
            ValueError: If MySQL is not configured
        """
        if self.config.db_type != DatabaseType.MYSQL:
            raise ValueError("MySQL is not the configured database type")

        if not self.config.mysql_config:
            raise ValueError("MySQL configuration is missing")

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.ext.asyncio import create_async_engine
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy is required for MySQL connections. "
                "Install with: pip install sqlalchemy pymysql aiomysql"
            ) from e

        mysql_config = self.config.mysql_config

        if async_mode:
            if self._mysql_async_engine is None:
                connection_url = mysql_config.build_async_connection_url()
                engine_options = mysql_config.get_engine_options()

                logger.info(f"Creating async MySQL engine: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}")
                self._mysql_async_engine = create_async_engine(
                    connection_url,
                    **engine_options
                )

            return self._mysql_async_engine
        else:
            if self._mysql_engine is None:
                connection_url = mysql_config.build_connection_url()
                engine_options = mysql_config.get_engine_options()

                logger.info(f"Creating MySQL engine: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}")
                self._mysql_engine = create_engine(
                    connection_url,
                    **engine_options
                )

            return self._mysql_engine

    def get_mongodb_client(self, async_mode: bool = False):
        """
        Get MongoDB client.

        Args:
            async_mode: Whether to return async client (Motor)

        Returns:
            PyMongo MongoClient or Motor AsyncIOMotorClient

        Raises:
            ImportError: If pymongo or motor is not installed
            ValueError: If MongoDB is not configured
        """
        if self.config.db_type != DatabaseType.MONGODB:
            raise ValueError("MongoDB is not the configured database type")

        if not self.config.mongodb_config:
            raise ValueError("MongoDB configuration is missing")

        mongo_config = self.config.mongodb_config

        if async_mode:
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
            except ImportError as e:
                raise ImportError(
                    "Motor is required for async MongoDB connections. "
                    "Install with: pip install motor"
                ) from e

            if self._mongodb_client is None:
                connection_url = mongo_config.build_connection_url()
                client_options = mongo_config.get_client_options()

                logger.info(f"Creating async MongoDB client: {mongo_config.host}:{mongo_config.port}/{mongo_config.database}")
                self._mongodb_client = AsyncIOMotorClient(connection_url, **client_options)

            return self._mongodb_client
        else:
            try:
                from pymongo import MongoClient
            except ImportError as e:
                raise ImportError(
                    "PyMongo is required for MongoDB connections. "
                    "Install with: pip install pymongo"
                ) from e

            if self._mongodb_client is None:
                connection_url = mongo_config.build_connection_url()
                client_options = mongo_config.get_client_options()

                logger.info(f"Creating MongoDB client: {mongo_config.host}:{mongo_config.port}/{mongo_config.database}")
                self._mongodb_client = MongoClient(connection_url, **client_options)

            return self._mongodb_client

    def get_firestore_client(self):
        """
        Get Firestore client.

        Returns:
            Google Cloud Firestore Client

        Raises:
            ImportError: If google-cloud-firestore is not installed
            ValueError: If Firestore is not configured
        """
        if self.config.db_type != DatabaseType.FIRESTORE:
            raise ValueError("Firestore is not the configured database type")

        if not self.config.firestore_config:
            raise ValueError("Firestore configuration is missing")

        try:
            from google.cloud import firestore
        except ImportError as e:
            raise ImportError(
                "google-cloud-firestore is required for Firestore connections. "
                "Install with: pip install google-cloud-firestore"
            ) from e

        if self._firestore_client is None:
            firestore_config = self.config.firestore_config

            # Setup emulator if configured
            firestore_config.setup_emulator()

            client_kwargs = {"project": firestore_config.project_id}

            # Add credentials if provided
            if firestore_config.credentials_path:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    firestore_config.credentials_path
                )
                client_kwargs["credentials"] = credentials
            elif firestore_config.credentials_json:
                import json
                from google.oauth2 import service_account
                credentials_dict = json.loads(firestore_config.credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict
                )
                client_kwargs["credentials"] = credentials

            # Add database ID if not default
            if firestore_config.database_id != "(default)":
                client_kwargs["database"] = firestore_config.database_id

            logger.info(f"Creating Firestore client: project={firestore_config.project_id}, db={firestore_config.database_id}")
            self._firestore_client = firestore.Client(**client_kwargs)

        return self._firestore_client

    def get_database(self):
        """
        Get database instance based on configured type.

        Returns:
            Database instance (engine, client, etc.)
        """
        if self.config.db_type == DatabaseType.MYSQL:
            return self.get_mysql_engine()
        elif self.config.db_type == DatabaseType.MONGODB:
            return self.get_mongodb_client()
        elif self.config.db_type == DatabaseType.FIRESTORE:
            return self.get_firestore_client()
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

    @contextmanager
    def get_session(self):
        """
        Get database session context manager.

        Yields:
            Database session/connection

        Note:
            For MySQL: yields SQLAlchemy Session
            For MongoDB: yields database object
            For Firestore: yields client (no session concept)
        """
        if self.config.db_type == DatabaseType.MYSQL:
            # SQLAlchemy session
            from sqlalchemy.orm import sessionmaker

            engine = self.get_mysql_engine()
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()

            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        elif self.config.db_type == DatabaseType.MONGODB:
            # MongoDB database object
            client = self.get_mongodb_client()
            database = client[self.config.mongodb_config.database]

            try:
                yield database
            finally:
                pass  # No explicit cleanup needed for database object

        elif self.config.db_type == DatabaseType.FIRESTORE:
            # Firestore client
            client = self.get_firestore_client()

            try:
                yield client
            finally:
                pass  # No explicit cleanup needed

        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

    @asynccontextmanager
    async def get_async_session(self):
        """
        Get async database session context manager.

        Yields:
            Async database session/connection

        Note:
            For MySQL: yields async SQLAlchemy Session
            For MongoDB: yields async database object
            For Firestore: not supported (Firestore uses sync client)
        """
        if self.config.db_type == DatabaseType.MYSQL:
            # Async SQLAlchemy session
            from sqlalchemy.ext.asyncio import AsyncSession
            from sqlalchemy.orm import sessionmaker

            engine = self.get_mysql_engine(async_mode=True)
            async_session_maker = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            session = async_session_maker()

            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

        elif self.config.db_type == DatabaseType.MONGODB:
            # Async MongoDB database object
            client = self.get_mongodb_client(async_mode=True)
            database = client[self.config.mongodb_config.database]

            try:
                yield database
            finally:
                pass  # No explicit cleanup needed

        elif self.config.db_type == DatabaseType.FIRESTORE:
            raise NotImplementedError("Firestore does not support async sessions")

        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection.

        Returns:
            Dictionary with test results
        """
        result = {
            "success": False,
            "db_type": self.config.db_type.value,
            "error": None,
            "details": {},
        }

        try:
            if self.config.db_type == DatabaseType.MYSQL:
                result.update(await self._test_mysql_connection())
            elif self.config.db_type == DatabaseType.MONGODB:
                result.update(await self._test_mongodb_connection())
            elif self.config.db_type == DatabaseType.FIRESTORE:
                result.update(await self._test_firestore_connection())

            result["success"] = True
            logger.info(f"Database connection test passed: {self.config.db_type.value}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Database connection test failed: {e}")

        return result

    async def _test_mysql_connection(self) -> Dict[str, Any]:
        """Test MySQL connection."""
        from sqlalchemy import text

        engine = self.get_mysql_engine()
        with engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            database = conn.execute(text("SELECT DATABASE()")).scalar()
            conn.commit()

        return {
            "details": {
                "version": version,
                "database": database,
            }
        }

    async def _test_mongodb_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection."""
        client = self.get_mongodb_client()
        server_info = client.server_info()

        return {
            "details": {
                "version": server_info.get("version"),
                "database": self.config.mongodb_config.database,
            }
        }

    async def _test_firestore_connection(self) -> Dict[str, Any]:
        """Test Firestore connection."""
        client = self.get_firestore_client()

        # Try to list collections (limited to 1 to minimize cost)
        collections = list(client.collections(page_size=1))

        return {
            "details": {
                "project_id": self.config.firestore_config.project_id,
                "database_id": self.config.firestore_config.database_id,
                "accessible": True,
            }
        }

    def close(self) -> None:
        """Close all database connections."""
        if self._mysql_engine:
            self._mysql_engine.dispose()
            logger.info("MySQL engine disposed")

        if self._mysql_async_engine:
            # Async engine disposal needs to be awaited
            import asyncio
            asyncio.create_task(self._mysql_async_engine.dispose())
            logger.info("Async MySQL engine disposal initiated")

        if self._mongodb_client:
            self._mongodb_client.close()
            logger.info("MongoDB client closed")

        if self._firestore_client:
            self._firestore_client.close()
            logger.info("Firestore client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
