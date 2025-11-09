"""
Multi-Database Configuration System.

This module provides support for multiple database types:
- MySQL (default)
- NoSQL (MongoDB)
- Firestore (Google Cloud)

Allows runtime selection of database backend based on configuration.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types."""
    MYSQL = "mysql"
    MONGODB = "mongodb"
    FIRESTORE = "firestore"
    POSTGRESQL = "postgresql"  # Legacy support


@dataclass
class MySQLConfig:
    """MySQL-specific configuration."""

    # Connection parameters
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "ai_karen"

    # Connection pool
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # MySQL-specific options
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_disabled: bool = False

    # Connection string override
    url: Optional[str] = None

    def build_connection_url(self) -> str:
        """Build MySQL connection URL."""
        if self.url:
            return self.url

        # URL-encode password to handle special characters
        password_encoded = quote_plus(self.password)

        # Build base URL
        url = f"mysql+pymysql://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.database}"

        # Add parameters
        params = []
        params.append(f"charset={self.charset}")

        if self.ssl_ca and not self.ssl_disabled:
            params.append(f"ssl_ca={self.ssl_ca}")
        if self.ssl_cert and not self.ssl_disabled:
            params.append(f"ssl_cert={self.ssl_cert}")
        if self.ssl_key and not self.ssl_disabled:
            params.append(f"ssl_key={self.ssl_key}")

        if params:
            url += "?" + "&".join(params)

        return url

    def build_async_connection_url(self) -> str:
        """Build async MySQL connection URL using aiomysql."""
        url = self.build_connection_url()
        return url.replace("mysql+pymysql://", "mysql+aiomysql://")

    def get_engine_options(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine options."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": False,
        }


@dataclass
class MongoDBConfig:
    """MongoDB (NoSQL) configuration."""

    # Connection parameters
    host: str = "localhost"
    port: int = 27017
    user: Optional[str] = None
    password: Optional[str] = None
    database: str = "ai_karen"

    # MongoDB-specific options
    auth_source: str = "admin"
    replica_set: Optional[str] = None
    ssl: bool = False
    ssl_ca_certs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None

    # Connection pool
    max_pool_size: int = 100
    min_pool_size: int = 10
    max_idle_time_ms: int = 45000

    # Timeouts
    server_selection_timeout_ms: int = 30000
    connect_timeout_ms: int = 10000
    socket_timeout_ms: int = 45000

    # Connection string override
    url: Optional[str] = None

    def build_connection_url(self) -> str:
        """Build MongoDB connection URL."""
        if self.url:
            return self.url

        # Build authentication part
        auth_part = ""
        if self.user and self.password:
            password_encoded = quote_plus(self.password)
            auth_part = f"{self.user}:{password_encoded}@"

        # Build base URL
        url = f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"

        # Add parameters
        params = []
        if self.user:
            params.append(f"authSource={self.auth_source}")
        if self.replica_set:
            params.append(f"replicaSet={self.replica_set}")
        if self.ssl:
            params.append("ssl=true")
            if self.ssl_ca_certs:
                params.append(f"ssl_ca_certs={self.ssl_ca_certs}")
            if self.ssl_certfile:
                params.append(f"ssl_certfile={self.ssl_certfile}")

        params.append(f"maxPoolSize={self.max_pool_size}")
        params.append(f"minPoolSize={self.min_pool_size}")
        params.append(f"maxIdleTimeMS={self.max_idle_time_ms}")
        params.append(f"serverSelectionTimeoutMS={self.server_selection_timeout_ms}")
        params.append(f"connectTimeoutMS={self.connect_timeout_ms}")
        params.append(f"socketTimeoutMS={self.socket_timeout_ms}")

        if params:
            url += "?" + "&".join(params)

        return url

    def get_client_options(self) -> Dict[str, Any]:
        """Get PyMongo client options."""
        options = {
            "maxPoolSize": self.max_pool_size,
            "minPoolSize": self.min_pool_size,
            "maxIdleTimeMS": self.max_idle_time_ms,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "socketTimeoutMS": self.socket_timeout_ms,
        }

        if self.user and self.password:
            options["username"] = self.user
            options["password"] = self.password
            options["authSource"] = self.auth_source

        if self.replica_set:
            options["replicaSet"] = self.replica_set

        if self.ssl:
            options["ssl"] = True
            if self.ssl_ca_certs:
                options["ssl_ca_certs"] = self.ssl_ca_certs
            if self.ssl_certfile:
                options["ssl_certfile"] = self.ssl_certfile
            if self.ssl_keyfile:
                options["ssl_keyfile"] = self.ssl_keyfile

        return options


@dataclass
class FirestoreConfig:
    """Google Cloud Firestore configuration."""

    # GCP project configuration
    project_id: str = ""

    # Authentication
    credentials_path: Optional[str] = None  # Path to service account JSON
    credentials_json: Optional[str] = None  # JSON string of credentials

    # Firestore-specific options
    database_id: str = "(default)"  # Firestore database ID

    # Emulator support (for local development)
    use_emulator: bool = False
    emulator_host: str = "localhost"
    emulator_port: int = 8080

    # Collection name prefix
    collection_prefix: str = ""

    # Timeouts
    timeout: float = 60.0

    def validate(self) -> List[str]:
        """Validate Firestore configuration."""
        errors = []

        if not self.project_id:
            errors.append("Firestore project_id is required")

        if not self.use_emulator:
            if not self.credentials_path and not self.credentials_json:
                errors.append("Either credentials_path or credentials_json must be provided for Firestore")

            if self.credentials_path and not os.path.exists(self.credentials_path):
                errors.append(f"Firestore credentials file not found: {self.credentials_path}")

        return errors

    def get_client_options(self) -> Dict[str, Any]:
        """Get Firestore client options."""
        options = {
            "project": self.project_id,
            "database": self.database_id,
        }

        if self.credentials_path:
            options["credentials_path"] = self.credentials_path
        elif self.credentials_json:
            options["credentials_json"] = self.credentials_json

        return options

    def setup_emulator(self) -> None:
        """Set up Firestore emulator environment variables."""
        if self.use_emulator:
            os.environ["FIRESTORE_EMULATOR_HOST"] = f"{self.emulator_host}:{self.emulator_port}"
            logger.info(f"Firestore emulator configured at {self.emulator_host}:{self.emulator_port}")


@dataclass
class MultiDatabaseConfig:
    """
    Multi-database configuration supporting MySQL, MongoDB, and Firestore.
    MySQL is the default database type.
    """

    # Database type selection
    db_type: DatabaseType = DatabaseType.MYSQL

    # Type-specific configurations
    mysql_config: Optional[MySQLConfig] = None
    mongodb_config: Optional[MongoDBConfig] = None
    firestore_config: Optional[FirestoreConfig] = None

    # Common options
    debug: bool = False

    # Validation results
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize configuration based on database type."""
        # Create default configs if not provided
        if self.db_type == DatabaseType.MYSQL and not self.mysql_config:
            self.mysql_config = MySQLConfig()
        elif self.db_type == DatabaseType.MONGODB and not self.mongodb_config:
            self.mongodb_config = MongoDBConfig()
        elif self.db_type == DatabaseType.FIRESTORE and not self.firestore_config:
            self.firestore_config = FirestoreConfig()

        self._validate()

    def _validate(self) -> None:
        """Validate the configuration."""
        self.validation_errors.clear()
        self.validation_warnings.clear()

        # Validate based on database type
        if self.db_type == DatabaseType.MYSQL:
            if not self.mysql_config:
                self.validation_errors.append("MySQL configuration is required when db_type is MySQL")
            else:
                # Validate MySQL config
                if not self.mysql_config.database:
                    self.validation_errors.append("MySQL database name is required")
                if not self.mysql_config.user:
                    self.validation_errors.append("MySQL user is required")
                if not self.mysql_config.password:
                    self.validation_warnings.append("MySQL password is empty")

        elif self.db_type == DatabaseType.MONGODB:
            if not self.mongodb_config:
                self.validation_errors.append("MongoDB configuration is required when db_type is MongoDB")
            else:
                # Validate MongoDB config
                if not self.mongodb_config.database:
                    self.validation_errors.append("MongoDB database name is required")

        elif self.db_type == DatabaseType.FIRESTORE:
            if not self.firestore_config:
                self.validation_errors.append("Firestore configuration is required when db_type is Firestore")
            else:
                # Validate Firestore config
                errors = self.firestore_config.validate()
                self.validation_errors.extend(errors)

    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return len(self.validation_errors) == 0

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "valid": self.is_valid(),
            "errors": self.validation_errors.copy(),
            "warnings": self.validation_warnings.copy(),
            "error_count": len(self.validation_errors),
            "warning_count": len(self.validation_warnings),
        }

    def get_active_config(self) -> Any:
        """Get the active database configuration based on db_type."""
        if self.db_type == DatabaseType.MYSQL:
            return self.mysql_config
        elif self.db_type == DatabaseType.MONGODB:
            return self.mongodb_config
        elif self.db_type == DatabaseType.FIRESTORE:
            return self.firestore_config
        return None

    def get_connection_info(self) -> Dict[str, Any]:
        """Get sanitized connection information for logging."""
        info = {
            "db_type": self.db_type.value,
            "debug": self.debug,
            "validation_status": "valid" if self.is_valid() else "invalid",
        }

        active_config = self.get_active_config()
        if self.db_type == DatabaseType.MYSQL and self.mysql_config:
            info["mysql"] = {
                "host": self.mysql_config.host,
                "port": self.mysql_config.port,
                "user": self.mysql_config.user,
                "database": self.mysql_config.database,
                "charset": self.mysql_config.charset,
                "pool_size": self.mysql_config.pool_size,
            }
        elif self.db_type == DatabaseType.MONGODB and self.mongodb_config:
            info["mongodb"] = {
                "host": self.mongodb_config.host,
                "port": self.mongodb_config.port,
                "database": self.mongodb_config.database,
                "max_pool_size": self.mongodb_config.max_pool_size,
            }
        elif self.db_type == DatabaseType.FIRESTORE and self.firestore_config:
            info["firestore"] = {
                "project_id": self.firestore_config.project_id,
                "database_id": self.firestore_config.database_id,
                "use_emulator": self.firestore_config.use_emulator,
            }

        return info


class MultiDatabaseConfigLoader:
    """Loads multi-database configuration from environment variables."""

    @classmethod
    def load_from_environment(cls) -> MultiDatabaseConfig:
        """
        Load database configuration from environment variables.

        Environment variables:
        - DB_TYPE: Database type (mysql, mongodb, firestore) - defaults to 'mysql'
        - For MySQL: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_URL
        - For MongoDB: MONGO_HOST, MONGO_PORT, MONGO_USER, MONGO_PASSWORD, MONGO_DATABASE, MONGO_URL
        - For Firestore: FIRESTORE_PROJECT_ID, FIRESTORE_CREDENTIALS_PATH, FIRESTORE_CREDENTIALS_JSON

        Returns:
            MultiDatabaseConfig instance
        """
        # Determine database type (default to MySQL)
        db_type_str = os.getenv("DB_TYPE", "mysql").lower()
        try:
            db_type = DatabaseType(db_type_str)
        except ValueError:
            logger.warning(f"Invalid DB_TYPE '{db_type_str}', defaulting to MySQL")
            db_type = DatabaseType.MYSQL

        # Load type-specific configuration
        mysql_config = None
        mongodb_config = None
        firestore_config = None

        if db_type == DatabaseType.MYSQL:
            mysql_config = cls._load_mysql_config()
        elif db_type == DatabaseType.MONGODB:
            mongodb_config = cls._load_mongodb_config()
        elif db_type == DatabaseType.FIRESTORE:
            firestore_config = cls._load_firestore_config()

        # Create configuration
        config = MultiDatabaseConfig(
            db_type=db_type,
            mysql_config=mysql_config,
            mongodb_config=mongodb_config,
            firestore_config=firestore_config,
            debug=os.getenv("DB_DEBUG", "false").lower() in ["true", "1", "yes"],
        )

        # Log configuration
        logger.info(f"Multi-database configuration loaded: {config.get_connection_info()}")

        # Log validation results
        validation = config.get_validation_summary()
        if validation["errors"]:
            logger.error(f"Configuration errors: {validation['errors']}")
        if validation["warnings"]:
            logger.warning(f"Configuration warnings: {validation['warnings']}")

        return config

    @classmethod
    def _load_mysql_config(cls) -> MySQLConfig:
        """Load MySQL configuration from environment."""
        return MySQLConfig(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "ai_karen"),
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("MYSQL_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("MYSQL_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("MYSQL_POOL_RECYCLE", "3600")),
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            ssl_ca=os.getenv("MYSQL_SSL_CA"),
            ssl_cert=os.getenv("MYSQL_SSL_CERT"),
            ssl_key=os.getenv("MYSQL_SSL_KEY"),
            ssl_disabled=os.getenv("MYSQL_SSL_DISABLED", "false").lower() in ["true", "1"],
            url=os.getenv("MYSQL_URL"),
        )

    @classmethod
    def _load_mongodb_config(cls) -> MongoDBConfig:
        """Load MongoDB configuration from environment."""
        return MongoDBConfig(
            host=os.getenv("MONGO_HOST", "localhost"),
            port=int(os.getenv("MONGO_PORT", "27017")),
            user=os.getenv("MONGO_USER"),
            password=os.getenv("MONGO_PASSWORD"),
            database=os.getenv("MONGO_DATABASE", "ai_karen"),
            auth_source=os.getenv("MONGO_AUTH_SOURCE", "admin"),
            replica_set=os.getenv("MONGO_REPLICA_SET"),
            ssl=os.getenv("MONGO_SSL", "false").lower() in ["true", "1"],
            ssl_ca_certs=os.getenv("MONGO_SSL_CA_CERTS"),
            max_pool_size=int(os.getenv("MONGO_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGO_MIN_POOL_SIZE", "10")),
            url=os.getenv("MONGO_URL"),
        )

    @classmethod
    def _load_firestore_config(cls) -> FirestoreConfig:
        """Load Firestore configuration from environment."""
        config = FirestoreConfig(
            project_id=os.getenv("FIRESTORE_PROJECT_ID", ""),
            credentials_path=os.getenv("FIRESTORE_CREDENTIALS_PATH"),
            credentials_json=os.getenv("FIRESTORE_CREDENTIALS_JSON"),
            database_id=os.getenv("FIRESTORE_DATABASE_ID", "(default)"),
            use_emulator=os.getenv("FIRESTORE_USE_EMULATOR", "false").lower() in ["true", "1"],
            emulator_host=os.getenv("FIRESTORE_EMULATOR_HOST", "localhost"),
            emulator_port=int(os.getenv("FIRESTORE_EMULATOR_PORT", "8080")),
            collection_prefix=os.getenv("FIRESTORE_COLLECTION_PREFIX", ""),
            timeout=float(os.getenv("FIRESTORE_TIMEOUT", "60.0")),
        )

        # Setup emulator if enabled
        if config.use_emulator:
            config.setup_emulator()

        return config


def load_multi_database_config() -> MultiDatabaseConfig:
    """
    Convenience function to load multi-database configuration.

    Returns:
        MultiDatabaseConfig instance with MySQL as default
    """
    return MultiDatabaseConfigLoader.load_from_environment()
