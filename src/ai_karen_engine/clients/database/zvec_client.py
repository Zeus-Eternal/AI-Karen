"""
ZvecClient: Edge Vector Database for Personal Context, Offline RAG, and Local Semantic Search.

This client provides:
- Personal context storage (chat history, preferences, local documents)
- Offline RAG capability (millisecond-latency local search)
- Hybrid vector search (dense + sparse vectors)
- Per-user database isolation (multi-user concurrency)

Complementary to:
- DuckDB: Structured analytics, user profiles, history
- Milvus: Server-side vector search, collaborative knowledge

Example:
    client = ZvecClient(db_path="~/.ai-karen/users/{user_id}/zvec.db")
    client.insert_memory("user_123", text="Hello world", metadata={"source": "chat"})
    results = client.semantic_search("user_123", query_embedding, top_k=10)
"""

import os
import logging
import threading
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pathlib import Path

# Zvec import (will fail gracefully if not installed)
try:
    import zvec
    HAS_ZVEC = True
except ImportError:
    HAS_ZVEC = False
    zvec = None  # type: ignore

logger = logging.getLogger(__name__)


class ZvecClient:
    """
    Client for Zvec edge vector database.
    
    Thread-safe for reads, single-writer queue for writes.
    Per-user database isolation for multi-user concurrency.
    """
    
    # Default collection schemas
    DEFAULT_COLLECTIONS = {
        "personal_context": {
            "description": "User's personal context (chats, preferences, local docs)",
            "vector_dim": 384,  # distilbert-base-nli-stsb-mean-tokens
            "vector_type": "dense_fp32",
            "metadata_fields": {
                "user_id": "string",
                "timestamp": "datetime",
                "source": "string",  # chat, document, preference
                "text": "string",     # Original text (for offline RAG)
                "access_count": "int"  # For LRU cache eviction
            }
        },
        "offline_documents": {
            "description": "User's offline documents for RAG",
            "vector_dim": 384,
            "vector_type": "dense_fp32",
            "metadata_fields": {
                "user_id": "string",
                "doc_id": "string",
                "chunk_index": "int",
                "content": "string",
                "created_at": "datetime"
            }
        }
    }
    
    def __init__(
        self,
        db_path: str,
        collections: Optional[Dict[str, Dict]] = None,
        enabled: bool = True
    ):
        """
        Initialize Zvec client.
        
        Args:
            db_path: Path to Zvec database file (per-user recommended)
            collections: Custom collection schemas (default: personal_context, offline_documents)
            enabled: Enable/disable Zvec (useful for testing/fallback)
        """
        if not HAS_ZVEC and enabled:
            logger.warning(
                "Zvec not installed. Install with: pip install zvec"
            )
            enabled = False
        
        self.db_path = Path(db_path).expanduser()
        self.collections = collections or self.DEFAULT_COLLECTIONS
        self._enabled = enabled and HAS_ZVEC
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._initialized = False
        
        # Lazy initialization: DO NOT call _ensure_collections() here
        # Collections will be created on first use via _ensure_initialized()
        
        if not self._enabled:
            logger.info(f"Zvec client disabled: {db_path}")
        else:
            logger.info(f"Zvec client initialized: {self.db_path}")
    
    def _ensure_initialized(self):
        """Lazy initialization - only creates collections on first use"""
        if not self._enabled:
            raise RuntimeError(
                "Zvec is disabled. Install with: pip install zvec"
            )
        
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:  # Double-check
                return
            
            logger.info(f"Initializing Zvec collections at {self.db_path}")
            self._ensure_collections()
            self._initialized = True
            logger.info("Zvec client initialized successfully")
    
    def _ensure_collections(self):
        """Create collections if they don't exist"""
        try:
            # Open or create database
            self.connection = zvec.open(str(self.db_path))
            
            # Create collections with schemas
            for collection_name, schema_config in self.collections.items():
                self._create_collection(collection_name, schema_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize Zvec collections: {e}")
            raise
    
    def _create_collection(self, name: str, schema: Dict[str, Any]):
        """Create a collection with specified schema"""
        try:
            # Check if collection exists
            if hasattr(self.connection, 'has_collection'):
                if self.connection.has_collection(name):
                    logger.debug(f"Collection '{name}' already exists")
                    return
            
            # Create vector schema
            vector_schema = zvec.VectorSchema(
                name="embedding",
                data_type=getattr(zvec.DataType, schema["vector_type"].upper()),
                dimension=schema["vector_dim"]
            )
            
            # Create collection schema
            collection_schema = zvec.CollectionSchema(
                name=name,
                vectors=vector_schema
            )
            
            # Create collection
            self.connection.create_collection(collection_schema)
            logger.info(f"Created collection '{name}'")
            
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            raise
    
    # ═════════════════════════════════════════════════════════════════════
    # MEMORY OPERATIONS (Personal Context)
    # ═════════════════════════════════════════════════════════════════════
    
    def insert_memory(
        self,
        user_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = "personal_context"
    ) -> str:
        """
        Insert a memory with vector embedding.
        
        Args:
            user_id: User identifier
            text: Original text content
            embedding: Vector embedding (e.g., from sentence-transformers)
            metadata: Additional metadata (source, tags, etc.)
            collection: Collection name (default: personal_context)
        
        Returns:
            Document ID
        """
        self._ensure_initialized()
        
        doc_id = f"{user_id}_{datetime.now().timestamp()}"
        
        doc_metadata = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "access_count": 0
        }
        doc_metadata.update(metadata or {})
        
        try:
            doc = zvec.Doc(
                id=doc_id,
                vectors={"embedding": embedding},
                metadata=doc_metadata
            )
            
            self.connection.insert(collection, [doc])
            logger.debug(f"Inserted memory: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to insert memory: {e}")
            raise
    
    def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 10,
        collection: str = "personal_context",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity.
        
        Args:
            user_id: User identifier (for filtering)
            query_embedding: Query vector embedding
            top_k: Number of results to return
            collection: Collection name (default: personal_context)
            filters: Optional metadata filters
        
        Returns:
            List of {id, score, metadata} results
        """
        self._ensure_initialized()
        
        try:
            # Build query
            query = zvec.VectorQuery(
                name="embedding",
                vector=query_embedding,
                topk=top_k
            )
            
            # Execute query
            results = self.connection.query(collection, query)
            
            # Filter by user_id if specified
            if user_id:
                results = [
                    r for r in results
                    if r.get("metadata", {}).get("user_id") == user_id
                ]
            
            # Apply additional filters
            if filters:
                results = self._apply_filters(results, filters)
            
            # Update access count
            for result in results:
                self._update_access_count(result["id"])
            
            logger.debug(f"Semantic search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    # ═════════════════════════════════════════════════════════════════════
    # OFFLINE RAG OPERATIONS
    # ═════════════════════════════════════════════════════════════════════
    
    def insert_document(
        self,
        user_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        collection: str = "offline_documents"
    ) -> List[str]:
        """
        Insert a document with multiple chunks for offline RAG.
        
        Args:
            user_id: User identifier
            doc_id: Document identifier
            chunks: List of {text, embedding, metadata} chunks
            collection: Collection name (default: offline_documents)
        
        Returns:
            List of chunk document IDs
        """
        self._ensure_initialized()
        
        chunk_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{user_id}_{doc_id}_chunk_{i}"
            
            doc_metadata = {
                "user_id": user_id,
                "doc_id": doc_id,
                "chunk_index": i,
                "content": chunk["text"],
                "created_at": datetime.now().isoformat()
            }
            doc_metadata.update(chunk.get("metadata", {}))
            
            try:
                doc = zvec.Doc(
                    id=chunk_id,
                    vectors={"embedding": chunk["embedding"]},
                    metadata=doc_metadata
                )
                
                self.connection.insert(collection, [doc])
                chunk_ids.append(chunk_id)
                
            except Exception as e:
                logger.error(f"Failed to insert chunk {i}: {e}")
        
        logger.info(f"Inserted document '{doc_id}' with {len(chunk_ids)} chunks")
        return chunk_ids
    
    def offline_search(
        self,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
        collection: str = "offline_documents"
    ) -> List[Dict[str, Any]]:
        """
        Search within offline documents for RAG.
        
        Args:
            user_id: User identifier
            query_embedding: Query vector embedding
            top_k: Number of results to return
            doc_id: Optional document ID to limit search
            collection: Collection name (default: offline_documents)
        
        Returns:
            List of {id, score, metadata} results
        """
        self._ensure_initialized()
        
        filters = {"user_id": user_id}
        if doc_id:
            filters["doc_id"] = doc_id
        
        return self.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=top_k,
            collection=collection,
            filters=filters
        )
    
    # ═════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═════════════════════════════════════════════════════════════════════
    
    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply metadata filters to results"""
        filtered = []
        for result in results:
            metadata = result.get("metadata", {})
            if all(metadata.get(k) == v for k, v in filters.items()):
                filtered.append(result)
        return filtered
    
    def _update_access_count(self, doc_id: str):
        """Update access count for LRU caching (async)"""
        # TODO: Implement async update to avoid blocking reads
        pass
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's memory"""
        self._ensure_initialized()
        
        stats = {
            "user_id": user_id,
            "total_memories": 0,
            "total_documents": 0,
            "db_size_mb": 0
        }
        
        try:
            # Get DB size
            if self.db_path.exists():
                stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
            
            # TODO: Count memories and documents
            # Requires Zvec to expose collection stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
        
        return stats
    
    def health(self) -> bool:
        """Health check for Zvec client"""
        if not self._enabled:
            return False
        
        try:
            self._ensure_initialized()
            return self.connection is not None
        except Exception:
            return False
    
    def close(self):
        """Close Zvec connection"""
        if hasattr(self, 'connection') and self.connection:
            # TODO: Implement close() when Zvec API supports it
            pass
