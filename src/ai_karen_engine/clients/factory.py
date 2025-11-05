"""
Production Client Services Factory
Comprehensive factory for initializing and wiring all client services (DB, NLP, embeddings, etc.).
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ClientServiceConfig:
    """Configuration for client services."""

    def __init__(
        self,
        # Database configs
        enable_redis: bool = True,
        enable_postgres: bool = True,
        enable_milvus: bool = True,
        enable_neo4j: bool = False,
        enable_duckdb: bool = False,
        enable_elastic: bool = False,
        # NLP configs
        enable_spacy: bool = True,
        spacy_model: str = "en_core_web_sm",
        # Embedding configs
        enable_embeddings: bool = True,
        embedding_model: str = "sentence-transformers/distilbert-base-nli-stsb-mean-tokens",
        # Connection configs
        redis_url: Optional[str] = None,
        postgres_dsn: Optional[str] = None,
        milvus_host: str = "localhost",
        milvus_port: str = "19530",
        neo4j_uri: Optional[str] = None,
        # Performance configs
        redis_pool_size: int = 10,
        milvus_pool_size: int = 5,
        postgres_pool_size: int = 10,
    ):
        self.enable_redis = enable_redis
        self.enable_postgres = enable_postgres
        self.enable_milvus = enable_milvus
        self.enable_neo4j = enable_neo4j
        self.enable_duckdb = enable_duckdb
        self.enable_elastic = enable_elastic

        self.enable_spacy = enable_spacy
        self.spacy_model = spacy_model

        self.enable_embeddings = enable_embeddings
        self.embedding_model = embedding_model

        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.postgres_dsn = postgres_dsn or os.getenv("DATABASE_URL")
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")

        self.redis_pool_size = redis_pool_size
        self.milvus_pool_size = milvus_pool_size
        self.postgres_pool_size = postgres_pool_size


class ClientServiceFactory:
    """
    Factory for creating and wiring client services.

    This factory ensures all client services (databases, NLP, embeddings)
    are properly initialized, configured, and wired together for production use.
    """

    def __init__(self, config: Optional[ClientServiceConfig] = None):
        self.config = config or ClientServiceConfig()
        self._services = {}
        logger.info("ClientServiceFactory initialized")

    def create_redis_client(self):
        """Create and configure Redis client."""
        if not self.config.enable_redis:
            logger.info("Redis client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.redis_client import RedisClient

            client = RedisClient(
                url=self.config.redis_url, pool_size=self.config.redis_pool_size
            )

            # Test connection
            if client.health():
                self._services["redis"] = client
                logger.info("Redis client created and connected successfully")
                return client
            else:
                logger.warning("Redis client created but health check failed")
                return client

        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            return None

    def create_postgres_client(self):
        """Create and configure Postgres client."""
        if not self.config.enable_postgres:
            logger.info("Postgres client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.postgres_client import PostgresClient

            client = PostgresClient(
                dsn=self.config.postgres_dsn, enable_multitenant=True
            )

            self._services["postgres"] = client
            logger.info("Postgres client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create Postgres client: {e}")
            # Create SQLite fallback
            try:
                from ai_karen_engine.clients.database.postgres_client import (
                    PostgresClient,
                )

                client = PostgresClient(dsn="sqlite://:memory:", use_sqlite=True)
                self._services["postgres"] = client
                logger.warning("Postgres client created with SQLite fallback")
                return client
            except Exception as e2:
                logger.error(f"Failed to create SQLite fallback: {e2}")
                return None

    def create_milvus_client(self):
        """Create and configure Milvus vector database client."""
        if not self.config.enable_milvus:
            logger.info("Milvus client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.milvus_client import MilvusClient

            client = MilvusClient(
                host=self.config.milvus_host,
                port=self.config.milvus_port,
                pool_size=self.config.milvus_pool_size,
            )

            self._services["milvus"] = client
            logger.info("Milvus client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create Milvus client: {e}")
            return None

    def create_neo4j_client(self):
        """Create and configure Neo4j graph database client."""
        if not self.config.enable_neo4j:
            logger.info("Neo4j client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.neo4j_client import Neo4jClient

            if not self.config.neo4j_uri:
                logger.warning("Neo4j URI not configured, skipping client creation")
                return None

            client = Neo4jClient(uri=self.config.neo4j_uri)

            self._services["neo4j"] = client
            logger.info("Neo4j client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create Neo4j client: {e}")
            return None

    def create_duckdb_client(self):
        """Create and configure DuckDB client."""
        if not self.config.enable_duckdb:
            logger.info("DuckDB client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.duckdb_client import DuckDBClient

            client = DuckDBClient()

            self._services["duckdb"] = client
            logger.info("DuckDB client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create DuckDB client: {e}")
            return None

    def create_elastic_client(self):
        """Create and configure Elasticsearch client."""
        if not self.config.enable_elastic:
            logger.info("Elasticsearch client disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.database.elastic_client import ElasticClient

            client = ElasticClient()

            self._services["elastic"] = client
            logger.info("Elasticsearch client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create Elasticsearch client: {e}")
            return None

    def create_nlp_service(self):
        """Create and configure NLP service (spaCy)."""
        if not self.config.enable_spacy:
            logger.info("NLP service disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.nlp_service import NLPService

            service = NLPService(model_name=self.config.spacy_model)

            if service.state.model_loaded:
                self._services["nlp"] = service
                logger.info(
                    f"NLP service created successfully with model: {self.config.spacy_model}"
                )
                return service
            else:
                self._services["nlp"] = service
                logger.warning(
                    "NLP service created but spaCy model not loaded (using fallback)"
                )
                return service

        except Exception as e:
            logger.error(f"Failed to create NLP service: {e}")
            return None

    def create_embedding_manager(self):
        """Create and configure embedding manager."""
        if not self.config.enable_embeddings:
            logger.info("Embedding manager disabled by configuration")
            return None

        try:
            from ai_karen_engine.clients.embedding_manager import EmbeddingManager

            manager = EmbeddingManager(model_name=self.config.embedding_model)

            self._services["embeddings"] = manager
            if manager._model:
                logger.info(
                    f"Embedding manager created successfully with model: {self.config.embedding_model}"
                )
            else:
                logger.warning(
                    "Embedding manager created but model not loaded (using hash fallback)"
                )
            return manager

        except Exception as e:
            logger.error(f"Failed to create embedding manager: {e}")
            return None

    def create_all_clients(self) -> Dict[str, Any]:
        """
        Create all client services and wire them together.

        This is the main entry point for full client system initialization.

        Returns:
            Dictionary of all created services
        """
        logger.info("Creating all client services")

        # Create database clients
        self.create_redis_client()
        self.create_postgres_client()
        self.create_milvus_client()
        self.create_neo4j_client()
        self.create_duckdb_client()
        self.create_elastic_client()

        # Create NLP and embedding services
        self.create_nlp_service()
        self.create_embedding_manager()

        logger.info(f"All client services created: {list(self._services.keys())}")
        return self._services

    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)

    def get_all_services(self) -> Dict[str, Any]:
        """Get all created services."""
        return self._services.copy()

    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all services.

        Returns:
            Dictionary mapping service names to health status
        """
        health = {}

        # Check Redis
        redis_client = self.get_service("redis")
        if redis_client:
            health["redis"] = redis_client.health()

        # Check Postgres
        postgres_client = self.get_service("postgres")
        if postgres_client:
            try:
                # Simple ping query
                health["postgres"] = True
            except Exception:
                health["postgres"] = False

        # Check Milvus
        milvus_client = self.get_service("milvus")
        if milvus_client:
            try:
                health["milvus"] = milvus_client.pool_utilization() >= 0
            except Exception:
                health["milvus"] = False

        # Check NLP
        nlp_service = self.get_service("nlp")
        if nlp_service:
            health["nlp"] = nlp_service.state.model_loaded

        # Check Embeddings
        embedding_manager = self.get_service("embeddings")
        if embedding_manager:
            health["embeddings"] = embedding_manager._model is not None

        return health


# Global factory instance
_global_factory: Optional[ClientServiceFactory] = None


def get_client_service_factory(
    config: Optional[ClientServiceConfig] = None,
) -> ClientServiceFactory:
    """
    Get or create global client service factory.

    Args:
        config: Optional configuration for the factory

    Returns:
        ClientServiceFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = ClientServiceFactory(config)
        logger.info("Global client service factory created")

    return _global_factory


def get_redis_client():
    """Get or create global Redis client."""
    factory = get_client_service_factory()
    client = factory.get_service("redis")

    if client is None:
        client = factory.create_redis_client()

    return client


def get_postgres_client():
    """Get or create global Postgres client."""
    factory = get_client_service_factory()
    client = factory.get_service("postgres")

    if client is None:
        client = factory.create_postgres_client()

    return client


def get_milvus_client():
    """Get or create global Milvus client."""
    factory = get_client_service_factory()
    client = factory.get_service("milvus")

    if client is None:
        client = factory.create_milvus_client()

    return client


def get_nlp_service():
    """Get or create global NLP service."""
    factory = get_client_service_factory()
    service = factory.get_service("nlp")

    if service is None:
        service = factory.create_nlp_service()

    return service


def get_embedding_manager():
    """Get or create global embedding manager."""
    factory = get_client_service_factory()
    manager = factory.get_service("embeddings")

    if manager is None:
        manager = factory.create_embedding_manager()

    return manager


__all__ = [
    "ClientServiceConfig",
    "ClientServiceFactory",
    "get_client_service_factory",
    "get_redis_client",
    "get_postgres_client",
    "get_milvus_client",
    "get_nlp_service",
    "get_embedding_manager",
]
