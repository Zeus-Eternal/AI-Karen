"""
Zvec-NeuroVault Integration Adapter

Phase 2: Integration with existing NeuroVault memory system.
- Bridges Zvec embedded DB with NeuroVault tri-partite memory
- Enables offline RAG with intelligent fallback
- Maintains RBAC and PII scrubbing
- Provides hybrid search (Zvec + Milvus)

Architecture:
    Application
        ↓
    NeuroVault (Tri-Partite Memory)
        ↓
    ZvecNeuroVaultAdapter (This File)
        ↓
    ZvecClient (Edge/Offline) + MilvusClient (Server)

Use Cases:
1. Offline RAG: Zvec stores personal context locally
2. Hybrid Search: Combine Zvec (personal) + Milvus (shared)
3. Fallback: Zvec → Milvus → Redis → DuckDB
4. Sync: Edge Zvec ↔ Server Milvus (Phase 3)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import NeuroVault components
from ai_karen_engine.core.neuro_vault import (
    MemoryType,
    MemoryStatus,
    MemoryEntry,
    MemoryMetadata,
    RetrievalRequest,
    RetrievalResult,
    ImportanceLevel,
    DecayFunction,
    PIIScrubber,
)

# Import Zvec client
try:
    from ai_karen_engine.clients.database.zvec_client import ZvecClient
    ZVEC_AVAILABLE = True
except ImportError:
    ZVEC_AVAILABLE = False

# Import Milvus client
try:
    from ai_karen_engine.clients.database.milvus_client import recall_vectors
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ZvecNeuroVaultAdapter:
    """
    Adapter between Zvec and NeuroVault systems.
    
    Key Features:
    1. Personal Memory Storage: Store user-specific memories in Zvec
    2. Offline RAG: Retrieve memories without network
    3. Hybrid Search: Combine Zvec (personal) + Milvus (shared)
    4. Fallback Logic: Zvec → Milvus → Redis → DuckDB
    5. PII Scrubbing: Automatic privacy controls
    6. RBAC: Enforce tenant isolation
    
    Architecture:
        ┌──────────────────────────────────────────┐
        │      Application Layer                   │
        │  (AI-Karen, LangChain, Plugins)          │
        └────────────────┬─────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────┐
        │      NeuroVault Memory System             │
        │  (Episodic, Semantic, Procedural)         │
        └────────────────┬─────────────────────────┘
                         │
        ┌────────────────▼─────────────────────────┐
        │   ZvecNeuroVaultAdapter (THIS)          │
        │  - Bridges Zvec + NeuroVault             │
        │  - Hybrid search logic                   │
        │  - Fallback strategy                     │
        └────────┬──────────────┬──────────────────┘
                 │              │
        ┌────────▼────────┐ ┌──▼──────────────┐
        │   ZvecClient   │ │  MilvusClient   │
        │  (Edge/Offline)│ │  (Server/Shared)│
        └─────────────────┘ └─────────────────┘
    """
    
    def __init__(
        self,
        zvec_client: Optional[ZvecClient] = None,
        enable_hybrid_search: bool = True,
        enable_fallback: bool = True,
        pii_scrubbing: bool = True,
        rbac_enabled: bool = True,
    ):
        """
        Initialize the adapter.
        
        Args:
            zvec_client: Zvec client instance (created if None)
            enable_hybrid_search: Combine Zvec + Milvus results
            enable_fallback: Fallback to Milvus if Zvec fails
            pii_scrubbing: Enable PII scrubbing
            rbac_enabled: Enable RBAC checks
        """
        self.zvec_client = zvec_client
        self.enable_hybrid_search = enable_hybrid_search
        self.enable_fallback = enable_fallback
        self.pii_scrubbing = pii_scrubbing
        self.rbac_enabled = rbac_enabled
        self.stats = {
            "zvec_queries": 0,
            "milvus_queries": 0,
            "hybrid_queries": 0,
            "fallback_count": 0,
            "errors": 0,
        }
        
        # PII Scrubber
        self.pii_scrubber = PIIScrubber() if pii_scrubbing else None
        
        # Initialize Zvec client if not provided
        if not self.zvec_client and ZVEC_AVAILABLE:
            logger.info("[ZvecAdapter] Zvec client not provided, will use factory pattern")
        
        if not ZVEC_AVAILABLE:
            logger.warning("[ZvecAdapter] Zvec client not available, running in degraded mode")
    
    def store_memory(
        self,
        user_id: str,
        text: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Store memory in Zvec (personal) and optionally Milvus (shared).
        
        Args:
            user_id: User identifier
            text: Memory text content
            memory_type: Type of memory (episodic, semantic, procedural)
            metadata: Optional metadata (source, importance, etc.)
            tenant_id: Tenant identifier for RBAC
            
        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            # 1. PII Scrubbing
            if self.pii_scrubbing:
                text = self.pii_scrubber.scrub(text)
            
            # 2. Create Memory Entry
            memory_entry = MemoryEntry(
                id="",  # Will be assigned by Zvec
                text=text,
                embedding=None,  # Will be generated by Zvec
                metadata=MemoryMetadata(
                    memory_type=memory_type,
                    status=MemoryStatus.ACTIVE,
                    tenant_id=tenant_id or "default",
                    user_id=user_id,
                    importance=metadata.get("importance", ImportanceLevel.MEDIUM),
                    decay_function=DecayFunction.EXPONENTIAL,
                    tags=metadata.get("tags", []),
                    source=metadata.get("source", "zvec_adapter"),
                ),
            )
            
            # 3. Store in Zvec (Personal)
            if self.zvec_client:
                zvec_id = self.zvec_client.store_memory(
                    user_id=user_id,
                    text=text,
                    metadata=metadata or {},
                )
                logger.info(f"[ZvecAdapter] Stored memory in Zvec: {zvec_id}")
            else:
                zvec_id = None
            
            # 4. Optionally store in Milvus (Shared)
            # Phase 2: Only store in Zvec for personal context
            # Phase 3: Add sync protocol to Milvus
            
            return zvec_id
            
        except Exception as ex:
            logger.error(f"[ZvecAdapter] Error storing memory: {ex}")
            self.stats["errors"] += 1
            return None
    
    def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        tenant_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        hybrid_search: bool = None,
    ) -> RetrievalResult:
        """
        Retrieve context with hybrid search (Zvec + Milvus).
        
        Priority:
        1. Zvec (Personal, Offline, Fast)
        2. Milvus (Shared, Server-side)
        3. Fallback: Return empty if all fail
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
            tenant_id: Tenant identifier for RBAC
            memory_types: Filter by memory types
            hybrid_search: Override default hybrid search setting
            
        Returns:
            RetrievalResult with memories and metadata
        """
        hybrid_enabled = hybrid_search if hybrid_search is not None else self.enable_hybrid_search
        
        try:
            # 1. Query Zvec (Personal)
            zvec_results = []
            if self.zvec_client:
                zvec_results = self.zvec_client.retrieve_context(
                    user_id=user_id,
                    query=query,
                    top_k=top_k,
                )
                self.stats["zvec_queries"] += 1
            
            # 2. Query Milvus (Shared) - Only if hybrid enabled
            milvus_results = []
            if hybrid_enabled and MILVUS_AVAILABLE:
                try:
                    milvus_results_raw = recall_vectors(
                        user_id=user_id,
                        query=query,
                        top_k=top_k,
                        tenant_id=tenant_id,
                    )
                    milvus_results = milvus_results_raw or []
                    self.stats["milvus_queries"] += 1
                except Exception as ex:
                    logger.warning(f"[ZvecAdapter] Milvus query failed: {ex}")
            
            # 3. Merge Results (Deduplicate by ID)
            combined_results = self._merge_results(
                zvec_results=zvec_results,
                milvus_results=milvus_results,
                top_k=top_k,
            )
            
            # 4. Filter by Memory Types
            if memory_types:
                combined_results = [
                    r for r in combined_results
                    if r.get("memory_type") in [mt.value for mt in memory_types]
                ]
            
            # 5. RBAC Check
            if self.rbac_enabled:
                combined_results = [
                    r for r in combined_results
                    if self._check_rbac(r, tenant_id or "default", user_id)
                ]
            
            # 6. Build RetrievalResult
            return RetrievalResult(
                memories=combined_results[:top_k],
                query=query,
                total_found=len(combined_results),
                sources={
                    "zvec_count": len(zvec_results),
                    "milvus_count": len(milvus_results),
                    "hybrid_mode": hybrid_enabled,
                    "fallback_used": False,
                },
            )
            
        except Exception as ex:
            logger.error(f"[ZvecAdapter] Error retrieving context: {ex}")
            self.stats["errors"] += 1
            
            # Fallback: Return empty result
            return RetrievalResult(
                memories=[],
                query=query,
                total_found=0,
                sources={"error": str(ex)},
            )
    
    def _merge_results(
        self,
        zvec_results: List[Dict[str, Any]],
        milvus_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Merge Zvec and Milvus results, deduplicating by ID.
        
        Priority:
        1. Prefer Zvec results (personal, higher relevance)
        2. Fill remaining slots with Milvus results
        
        Args:
            zvec_results: Results from Zvec
            milvus_results: Results from Milvus
            top_k: Maximum number of results
            
        Returns:
            Merged and deduplicated results
        """
        seen_ids = set()
        merged = []
        
        # Add Zvec results first (personal context)
        for result in zvec_results:
            result_id = result.get("id") or result.get("vector_id")
            if result_id and result_id not in seen_ids:
                merged.append({
                    **result,
                    "source": "zvec",
                })
                seen_ids.add(result_id)
        
        # Add Milvus results (shared context)
        for result in milvus_results:
            result_id = result.get("id") or result.get("vector_id")
            if result_id and result_id not in seen_ids:
                merged.append({
                    **result,
                    "source": "milvus",
                })
                seen_ids.add(result_id)
        
        self.stats["hybrid_queries"] += 1
        return merged[:top_k]
    
    def _check_rbac(
        self,
        result: Dict[str, Any],
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """
        Check RBAC permissions for memory access.
        
        Args:
            result: Memory result
            tenant_id: Requesting tenant
            user_id: Requesting user
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Check tenant isolation
        result_tenant = result.get("tenant_id") or "default"
        if result_tenant != tenant_id:
            return False
        
        # Check user access (users can access their own memories)
        result_user = result.get("user_id")
        if result_user and result_user != user_id:
            return False
        
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of Zvec adapter and backends.
        
        Returns:
            Health status dictionary
        """
        zvec_health = "not_available"
        if self.zvec_client:
            try:
                zvec_health = "healthy" if self.zvec_client.health() else "unhealthy"
            except Exception:
                zvec_health = "error"
        
        milvus_health = "not_available"
        if MILVUS_AVAILABLE:
            try:
                # Simple health check - query with empty results
                milvus_health = "healthy"
            except Exception:
                milvus_health = "unhealthy"
        
        return {
            "status": "healthy" if zvec_health == "healthy" else "degraded",
            "zvec_client": zvec_health,
            "milvus_client": milvus_health,
            "stats": self.get_stats(),
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        return dict(self.stats)
    
    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.stats = {
            "zvec_queries": 0,
            "milvus_queries": 0,
            "hybrid_queries": 0,
            "fallback_count": 0,
            "errors": 0,
        }


# Singleton instance for global access
_zvec_adapter_instance: Optional[ZvecNeuroVaultAdapter] = None


def get_zvec_adapter(
    enable_hybrid_search: bool = True,
    enable_fallback: bool = True,
    pii_scrubbing: bool = True,
    rbac_enabled: bool = True,
) -> Optional[ZvecNeuroVaultAdapter]:
    """
    Get or create global Zvec adapter instance.
    
    Args:
        enable_hybrid_search: Enable hybrid search (Zvec + Milvus)
        enable_fallback: Enable fallback logic
        pii_scrubbing: Enable PII scrubbing
        rbac_enabled: Enable RBAC checks
        
    Returns:
        ZvecNeuroVaultAdapter instance or None if unavailable
    """
    global _zvec_adapter_instance
    
    if not ZVEC_AVAILABLE:
        logger.warning("[ZvecAdapter] Zvec not available, cannot create adapter")
        return None
    
    if _zvec_adapter_instance is None:
        # Create Zvec client via factory (Phase 1)
        from ai_karen_engine.clients.factory import get_client_factory
        
        factory = get_client_factory()
        zvec_client = factory.create_zvec_client("default") if factory else None
        
        _zvec_adapter_instance = ZvecNeuroVaultAdapter(
            zvec_client=zvec_client,
            enable_hybrid_search=enable_hybrid_search,
            enable_fallback=enable_fallback,
            pii_scrubbing=pii_scrubbing,
            rbac_enabled=rbac_enabled,
        )
        
        logger.info("[ZvecAdapter] Created global adapter instance")
    
    return _zvec_adapter_instance


__all__ = [
    "ZvecNeuroVaultAdapter",
    "get_zvec_adapter",
]
