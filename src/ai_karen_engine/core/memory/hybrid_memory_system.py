"""
HybridMemorySystem: Combines DuckDB (structured) + Zvec (unstructured vectors)

This system provides:
- Structured data storage in DuckDB (user profiles, analytics, history)
- Vector semantic search in Zvec (personal context, offline RAG)
- Unified interface for memory operations
- Multi-user support with per-user database isolation

Architecture:
    DuckDB (Structured)          Zvec (Unstructured)
    ├─ User Profiles              ├─ Personal Context
    ├─ Analytics                 ├─ Chat History (vectors)
    ├─ History Tracking          ├─ Offline Documents
    └─ Long-term Memory         └─ Semantic Search

Example:
    from ai_karen_engine.core.memory.hybrid_memory_system import HybridMemorySystem
    from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
    from ai_karen_engine.clients.database.zvec_client import ZvecClient
    
    system = HybridMemorySystem()
    system.initialize(
        duckdb_client=DuckDBClient(),
        zvec_client=ZvecClient(db_path="~/.ai-karen/users/{user_id}/zvec.db")
    )
    
    # Store memory (unified interface)
    system.store_memory(
        user_id="user_123",
        text="I prefer Python over JavaScript",
        metadata={"source": "preferences"}
    )
    
    # Retrieve context (hybrid search)
    context = system.retrieve_context(
        user_id="user_123",
        query="programming languages",
        top_k=10
    )
"""

import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pathlib import Path

try:
    from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False
    DuckDBClient = None  # type: ignore

try:
    from ai_karen_engine.clients.database.zvec_client import ZvecClient
    HAS_ZVEC = True
except ImportError:
    HAS_ZVEC = False
    ZvecClient = None  # type: ignore

logger = logging.getLogger(__name__)


class HybridMemorySystem:
    """
    Hybrid memory system combining DuckDB (structured) + Zvec (vectors).
    
    Provides unified interface for:
    - Structured data (profiles, analytics, history)
    - Unstructured data (chat history, preferences, documents)
    - Hybrid search (SQL + vector similarity)
    - Offline RAG capability
    """
    
    def __init__(
        self,
        duckdb_client: Optional[DuckDBClient] = None,
        zvec_client: Optional[ZvecClient] = None,
        enable_duckdb: bool = True,
        enable_zvec: bool = True,
        embedding_model: Optional[Any] = None
    ):
        """
        Initialize hybrid memory system.
        
        Args:
            duckdb_client: DuckDB client instance (optional, lazy init)
            zvec_client: Zvec client instance (optional, lazy init)
            enable_duckdb: Enable DuckDB (structured data)
            enable_zvec: Enable Zvec (vector search)
            embedding_model: Embedding model for Zvec (required for vector ops)
        """
        # Clients
        self.duckdb_client = duckdb_client
        self.zvec_client = zvec_client
        
        # Configuration
        self.enable_duckdb = enable_duckdb and HAS_DUCKDB
        self.enable_zvec = enable_zvec and HAS_ZVEC
        self.embedding_model = embedding_model
        
        # State
        self._initialized = False
        
        # Validation
        if self.enable_zvec and not embedding_model:
            logger.warning(
                "Zvec enabled but no embedding_model provided. "
                "Vector operations will fail."
            )
    
    def initialize(
        self,
        duckdb_client: Optional[DuckDBClient] = None,
        zvec_client: Optional[ZvecClient] = None,
        embedding_model: Optional[Any] = None
    ):
        """
        Initialize the hybrid memory system.
        
        Args:
            duckdb_client: DuckDB client instance
            zvec_client: Zvec client instance
            embedding_model: Embedding model for Zvec
        """
        if duckdb_client:
            self.duckdb_client = duckdb_client
            self.enable_duckdb = True
        
        if zvec_client:
            self.zvec_client = zvec_client
            self.enable_zvec = True
        
        if embedding_model:
            self.embedding_model = embedding_model
        
        # Initialize clients
        if self.enable_duckdb and self.duckdb_client:
            self.duckdb_client._ensure_initialized()
        
        if self.enable_zvec and self.zvec_client:
            self.zvec_client._ensure_initialized()
        
        self._initialized = True
        logger.info("HybridMemorySystem initialized")
    
    def _ensure_initialized(self):
        """Ensure system is initialized"""
        if not self._initialized:
            raise RuntimeError(
                "HybridMemorySystem not initialized. Call initialize() first."
            )
    
    # ═══════════════════════════════════════════════════════════════════
    # UNIFIED MEMORY OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def store_memory(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        store_in_duckdb: bool = True,
        store_in_zvec: bool = True
    ) -> Dict[str, Any]:
        """
        Store memory in both DuckDB (structured) and Zvec (vector).
        
        Args:
            user_id: User identifier
            text: Text content
            metadata: Additional metadata
            embedding: Pre-computed embedding (optional)
            store_in_duckdb: Store in DuckDB (structured)
            store_in_zvec: Store in Zvec (vector)
        
        Returns:
            Dict with {duckdb_id, zvec_id, success}
        """
        self._ensure_initialized()
        
        result = {
            "user_id": user_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "duckdb_id": None,
            "zvec_id": None,
            "success": False
        }
        
        # Store in DuckDB (structured)
        if store_in_duckdb and self.enable_duckdb and self.duckdb_client:
            try:
                # Store in profile history
                self.duckdb_client.update_profile(
                    user_id=user_id,
                    field="last_memory",
                    value=text
                )
                
                result["duckdb_id"] = f"{user_id}_{datetime.now().timestamp()}"
                logger.debug(f"Stored in DuckDB: {result['duckdb_id']}")
                
            except Exception as e:
                logger.error(f"Failed to store in DuckDB: {e}")
        
        # Store in Zvec (vector)
        if store_in_zvec and self.enable_zvec and self.zvec_client:
            try:
                # Generate embedding if not provided
                if not embedding and self.embedding_model:
                    embedding = self.embedding_model.embed_query(text)
                
                if embedding:
                    zvec_id = self.zvec_client.insert_memory(
                        user_id=user_id,
                        text=text,
                        embedding=embedding,
                        metadata=metadata
                    )
                    result["zvec_id"] = zvec_id
                    logger.debug(f"Stored in Zvec: {zvec_id}")
            
            except Exception as e:
                logger.error(f"Failed to store in Zvec: {e}")
        
        result["success"] = (result["duckdb_id"] is not None) or (result["zvec_id"] is not None)
        return result
    
    def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        search_duckdb: bool = True,
        search_zvec: bool = True,
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve context using hybrid search (DuckDB + Zvec).
        
        Args:
            user_id: User identifier
            query: Query text
            top_k: Number of results
            search_duckdb: Search DuckDB (structured)
            search_zvec: Search Zvec (semantic)
            embedding: Pre-computed query embedding (optional)
        
        Returns:
            Dict with {structured_results, semantic_results, combined}
        """
        self._ensure_initialized()
        
        results = {
            "user_id": user_id,
            "query": query,
            "structured_results": [],   # DuckDB results
            "semantic_results": [],      # Zvec results
            "combined": []               # Merged results
        }
        
        # Search DuckDB (structured)
        if search_duckdb and self.enable_duckdb and self.duckdb_client:
            try:
                profile = self.duckdb_client.get_profile(user_id)
                
                # Get recent history
                history = self.duckdb_client.get_profile_history(
                    user_id=user_id,
                    limit=10
                ) if hasattr(self.duckdb_client, 'get_profile_history') else []
                
                results["structured_results"] = {
                    "profile": profile,
                    "recent_history": history
                }
                
                logger.debug(f"DuckDB returned {len(history)} history records")
                
            except Exception as e:
                logger.error(f"DuckDB search failed: {e}")
        
        # Search Zvec (semantic)
        if search_zvec and self.enable_zvec and self.zvec_client:
            try:
                # Generate embedding if not provided
                if not embedding and self.embedding_model:
                    embedding = self.embedding_model.embed_query(query)
                
                if embedding:
                    semantic_results = self.zvec_client.semantic_search(
                        user_id=user_id,
                        query_embedding=embedding,
                        top_k=top_k
                    )
                    results["semantic_results"] = semantic_results
                    logger.debug(f"Zvec returned {len(semantic_results)} results")
            
            except Exception as e:
                logger.error(f"Zvec search failed: {e}")
        
        # Combine results
        results["combined"] = self._merge_results(
            results["structured_results"],
            results["semantic_results"]
        )
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════
    # DUCKDB-SPECIFIC OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from DuckDB"""
        self._ensure_initialized()
        
        if not self.enable_duckdb or not self.duckdb_client:
            return None
        
        try:
            return self.duckdb_client.get_profile(user_id)
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def update_user_profile(
        self,
        user_id: str,
        field: str,
        value: Any
    ) -> bool:
        """Update user profile in DuckDB"""
        self._ensure_initialized()
        
        if not self.enable_duckdb or not self.duckdb_client:
            return False
        
        try:
            self.duckdb_client.update_profile(user_id, field, value)
            return True
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════
    # ZVEC-SPECIFIC OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def semantic_search(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search using Zvec only"""
        self._ensure_initialized()
        
        if not self.enable_zvec or not self.zvec_client:
            return []
        
        # Generate embedding if not provided
        if not embedding and self.embedding_model:
            embedding = self.embedding_model.embed_query(query)
        
        if not embedding:
            return []
        
        try:
            return self.zvec_client.semantic_search(
                user_id=user_id,
                query_embedding=embedding,
                top_k=top_k
            )
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def insert_document(
        self,
        user_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert document with chunks for offline RAG"""
        self._ensure_initialized()
        
        if not self.enable_zvec or not self.zvec_client:
            return []
        
        try:
            return self.zvec_client.insert_document(
                user_id=user_id,
                doc_id=doc_id,
                chunks=chunks
            )
        except Exception as e:
            logger.error(f"Failed to insert document: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def _merge_results(
        self,
        structured_results: Dict[str, Any],
        semantic_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge DuckDB and Zvec results"""
        # Simple merge: semantic results + structured profile
        merged = []
        
        # Add semantic results
        for result in semantic_results:
            merged.append({
                "type": "semantic",
                "score": result.get("score", 0.0),
                "data": result
            })
        
        # Add structured results (if available)
        if isinstance(structured_results, dict):
            profile = structured_results.get("profile")
            if profile:
                merged.append({
                    "type": "structured",
                    "score": 0.0,
                    "data": profile
                })
        
        # Sort by score (descending)
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for user"""
        self._ensure_initialized()
        
        stats = {
            "user_id": user_id,
            "duckdb_enabled": self.enable_duckdb,
            "zvec_enabled": self.enable_zvec,
            "duckdb_stats": {},
            "zvec_stats": {}
        }
        
        # DuckDB stats
        if self.enable_duckdb and self.duckdb_client:
            stats["duckdb_stats"] = {
                "profile_exists": self.duckdb_client.get_profile(user_id) is not None
            }
        
        # Zvec stats
        if self.enable_zvec and self.zvec_client:
            stats["zvec_stats"] = self.zvec_client.get_memory_stats(user_id)
        
        return stats
    
    def health(self) -> Dict[str, bool]:
        """Health check for both systems"""
        return {
            "duckdb_healthy": (
                self.enable_duckdb and
                self.duckdb_client and
                self.duckdb_client.health() if hasattr(self.duckdb_client, 'health') else True
            ),
            "zvec_healthy": (
                self.enable_zvec and
                self.zvec_client and
                self.zvec_client.health()
            ),
            "initialized": self._initialized
        }
    
    def close(self):
        """Close connections"""
        if self.duckdb_client and hasattr(self.duckdb_client, 'close'):
            self.duckdb_client.close()
        
        if self.zvec_client and hasattr(self.zvec_client, 'close'):
            self.zvec_client.close()
        
        logger.info("HybridMemorySystem closed")
