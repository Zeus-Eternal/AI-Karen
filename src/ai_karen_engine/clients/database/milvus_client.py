"""
MilvusClient: Handles all vector memory for Kari via Milvus 2.x (pymilvus).
Persona embeddings, upserts, deletes, recall, cosine similarity.
Updated with async contract compatibility methods and lazy loading for performance.
"""

import queue
import os
import logging
from contextlib import contextmanager
from typing import Optional

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from ai_karen_engine.core.embedding_manager import record_metric

logger = logging.getLogger(__name__)


class MilvusClient:
    def __init__(
        self,
        collection: str = "persona_embeddings",
        dim: int = 384,
        host: str = "localhost",
        port: str = "19530",
        pool_size: int = 5,
    ):
        self.collection_name = collection
        self.dim = dim
        self._host = host
        self._port = port
        self.pool_size = pool_size
        self._pool: Optional[queue.Queue[str]] = None
        self._connected = False

        # Check if vector DB is disabled via environment variable
        self._enabled = os.getenv("KARI_ENABLE_VECTOR_DB", "true").lower() not in ("false", "0", "no")
        if not self._enabled:
            logger.info("Milvus Vector DB disabled via KARI_ENABLE_VECTOR_DB environment variable")

        # Lazy loading: DO NOT connect in __init__
        # Connections will be established on first use via _ensure_connected()

    def _ensure_connected(self) -> None:
        """Lazy connection - only connect when first used"""
        if not self._enabled:
            raise RuntimeError("Milvus Vector DB is disabled. Set KARI_ENABLE_VECTOR_DB=true to enable.")

        if not self._connected:
            logger.info(f"Initializing Milvus connection pool to {self._host}:{self._port}")
            self._connect()
            self._ensure_collection()
            self._connected = True
            logger.info(f"Milvus client connected successfully with {self.pool_size} connections")

    def _connect(self) -> None:
        if self._pool is None:
            self._pool = queue.Queue(maxsize=self.pool_size)

        for i in range(self.pool_size):
            alias = f"{self.collection_name}_conn_{i}"
            connections.connect(alias=alias, host=self._host, port=self._port)
            self._pool.put(alias)

    @contextmanager
    def _using(self):
        self._ensure_connected()  # Lazy connect on first use
        alias = self._pool.get()
        try:
            yield alias
        finally:
            self._pool.put(alias)

    def _ensure_collection(self):
        with self._using() as alias:
            if not utility.has_collection(self.collection_name, using=alias):
                fields = [
                    FieldSchema(
                        name="user_id",
                        dtype=DataType.VARCHAR,
                        is_primary=True,
                        auto_id=False,
                        max_length=64,
                    ),
                    FieldSchema(
                        name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim
                    ),
                ]
                schema = CollectionSchema(fields, description="Persona Embeddings")
                Collection(self.collection_name, schema, using=alias)

    def pool_utilization(self) -> float:
        used = self.pool_size - self._pool.qsize()
        return used / self.pool_size if self.pool_size else 0.0

    def embed_persona(self, profile_dict):
        # Plug in your favorite embedding model (local!)
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        text = f"{profile_dict.get('name','')}. {profile_dict.get('bio','')}. {' '.join(profile_dict.get('tags',[]))}"
        vec = model.encode([text])[0]
        return vec / np.linalg.norm(vec)

    def upsert_persona_embedding(self, user_id, vec):
        entities = [[user_id], [vec]]
        with self._using() as alias:
            col = Collection(self.collection_name, using=alias)
            col.upsert(data=entities)
            record_metric("milvus_pool_utilization", self.pool_utilization())

    def get_reference_embedding(self, user_id):
        expr = f'user_id == "{user_id}"'
        with self._using() as alias:
            col = Collection(self.collection_name, using=alias)
            col.load()
            res = col.query(expr, output_fields=["embedding"])
            record_metric("milvus_pool_utilization", self.pool_utilization())
        if not res:
            return None
        return np.array(res[0]["embedding"])

    def delete_persona_embedding(self, user_id):
        expr = f'user_id == "{user_id}"'
        with self._using() as alias:
            col = Collection(self.collection_name, using=alias)
            col.delete(expr)
            record_metric("milvus_pool_utilization", self.pool_utilization())

    def cosine_similarity(self, vec1, vec2):
        return float(
            np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-7)
        )

    def search_topk(self, query_vec, k=10):
        with self._using() as alias:
            col = Collection(self.collection_name, using=alias)
            col.load()
            res = col.search(
                data=[query_vec],
                anns_field="embedding",
                param={"metric_type": "IP"},
                limit=k,
                output_fields=["user_id"],
            )
            record_metric("milvus_pool_utilization", self.pool_utilization())
        return (
            [(hit.entity.get("user_id"), hit.distance) for hit in res[0]] if res else []
        )

    async def insert(self, collection_name: str = None, data: dict = None, **kwargs):
        """Async wrapper for upsert operations to maintain contract compatibility."""
        try:
            # Use the existing upsert method for compatibility
            if data and "user_id" in data and "embedding" in data:
                self.upsert_persona_embedding(data["user_id"], data["embedding"])
                return data.get("user_id", "unknown")
            else:
                # Fallback for generic insert operations
                entities = []
                if "user_id" in kwargs and "embedding" in kwargs:
                    entities = [[kwargs["user_id"]], [kwargs["embedding"]]]
                    with self._using() as alias:
                        col = Collection(self.collection_name, using=alias)
                        col.upsert(data=entities)
                        record_metric(
                            "milvus_pool_utilization", self.pool_utilization()
                        )
                    return kwargs["user_id"]
                return None
        except Exception as e:
            raise Exception(f"Milvus insert failed: {e}")

    async def search(
        self,
        collection_name: str = None,
        query_vectors: list = None,
        top_k: int = 10,
        metadata_filter: dict = None,
        **kwargs,
    ):
        """Async wrapper for search operations to maintain contract compatibility."""
        try:
            if not query_vectors or len(query_vectors) == 0:
                return []

            query_vec = query_vectors[0]  # Use first query vector

            # Use the existing search method
            results = self.search_topk(query_vec, k=top_k)

            # Convert to expected format
            formatted_results = []
            for user_id, distance in results:
                formatted_results.append(
                    {
                        "id": user_id,
                        "distance": distance,
                        "metadata": {"user_id": user_id},
                    }
                )

            return formatted_results

        except Exception as e:
            # Return empty results instead of failing
            return []

    # Health check
    def health(self):
        """
        Check Milvus health status.
        Returns True if healthy or if not yet connected (lazy mode).
        Only returns False if connection exists but is unhealthy.
        """
        try:
            # If disabled, return False to indicate it's not available
            if not self._enabled:
                return False

            # If not yet connected, return True (healthy = not yet needed)
            # This prevents health checks from triggering lazy connection
            if not self._connected:
                logger.debug("Milvus client not yet connected (lazy mode) - reporting as healthy")
                return True

            # If connected, perform actual health check
            with self._using() as alias:
                col = Collection(self.collection_name, using=alias)
                col.load()
                record_metric("milvus_pool_utilization", self.pool_utilization())
            return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False
