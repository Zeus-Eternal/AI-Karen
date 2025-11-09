from __future__ import annotations

"""
Client library exports.

Production-ready clients for:
- Database: Redis, Postgres, Milvus, Neo4j, DuckDB, Elasticsearch
- NLP: spaCy-based text processing
- Embeddings: DistilBERT semantic embeddings
- Extensions: External API integrations
"""

# Core clients
from ai_karen_engine.clients.embedding_manager import EmbeddingManager
from ai_karen_engine.clients.extension_api_client import ExtensionAPIClient
from ai_karen_engine.clients.nlp_service import NLPService

# Factory for centralized client initialization
from ai_karen_engine.clients.factory import (
    ClientServiceConfig,
    ClientServiceFactory,
    get_client_service_factory,
    get_redis_client,
    get_postgres_client,
    get_milvus_client,
    get_nlp_service,
    get_embedding_manager,
)

# Database clients (for explicit imports)
from ai_karen_engine.clients import database

__all__ = [
    # Core clients
    "ExtensionAPIClient",
    "EmbeddingManager",
    "NLPService",
    # Factory
    "ClientServiceConfig",
    "ClientServiceFactory",
    "get_client_service_factory",
    # Factory convenience functions
    "get_redis_client",
    "get_postgres_client",
    "get_milvus_client",
    "get_nlp_service",
    "get_embedding_manager",
    # Database module
    "database",
]
