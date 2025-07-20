"""
Operation MirrorSnap: Advanced Memory Integration Service
Dual-embedding NeuroVault with context-aware reranking
"""

import os
import json
import time
import hashlib
import hmac
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import requests
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class MemoryEvent:
    """Memory event with full context tracking"""
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class PluginMemoryEvent:
    """Plugin/tool invocation memory with outcome tracking"""
    plugin_name: str
    action: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    user_context: Dict[str, Any]
    timestamp: datetime
    execution_time: float
    error_message: Optional[str] = None


class NeuroVaultMemoryService:
    """
    Operation MirrorSnap: Dual-Embedding Memory System
    - Fast candidate recall (Stage 1)
    - Context-aware reranking (Stage 2)
    - Full observability and self-tuning
    """
    
    def __init__(self):
        self.api_url = os.getenv("KARI_API_URL", "http://localhost:8001")
        self.signing_key = os.getenv("KARI_MEMORY_SIGNING_KEY", "mirrorsnap-sovereign-key")
        self.session = requests.Session()
        
        # Memory stores
        self.memory_events: List[MemoryEvent] = []
        self.plugin_events: List[PluginMemoryEvent] = []
        
        # Metrics tracking
        self.metrics = {
            "recall_latency": [],
            "rerank_latency": [],
            "memory_hits": 0,
            "memory_misses": 0,
            "plugin_invocations": 0,
            "plugin_failures": 0,
            "context_alignments": 0
        }
    
    def _sign_memory_event(self, event: MemoryEvent) -> str:
        """Cryptographic signature for memory integrity"""
        payload = f"{event.id}|{event.content}|{event.timestamp.isoformat()}"
        return hmac.new(
            self.signing_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def store_memory(self, content: str, metadata: Dict[str, Any], 
                    context: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Store memory with dual-embedding and context tracking"""
        start_time = time.time()
        
        # Generate unique ID
        memory_id = hashlib.sha256(
            f"{content}{time.time()}{user_id}".encode()
        ).hexdigest()[:16]
        
        # Create memory event
        event = MemoryEvent(
            id=memory_id,
            content=content,
            embedding=None,  # Will be populated by embedding service
            metadata=metadata,
            context=context,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=context.get("session_id")
        )
        
        # Store in memory
        self.memory_events.append(event)
        
        # Track metrics
        storage_time = time.time() - start_time
        self.metrics["recall_latency"].append(storage_time)
        
        return memory_id
    
    def recall_memory(self, query: str, context: Dict[str, Any], 
                     limit: int = 10) -> List[MemoryEvent]:
        """
        Dual-stage memory recall:
        Stage 1: Fast candidate retrieval
        Stage 2: Context-aware reranking
        """
        start_time = time.time()
        
        # Stage 1: Fast candidate recall (simplified for demo)
        candidates = []
        query_lower = query.lower()
        
        for event in self.memory_events:
            if query_lower in event.content.lower():
                # Simple relevance scoring (would use embeddings in production)
                relevance = self._calculate_relevance(query, event, context)
                event.relevance_score = relevance
                candidates.append(event)
        
        stage1_time = time.time() - start_time
        
        # Stage 2: Context-aware reranking
        rerank_start = time.time()
        
        # Rerank based on context, recency, and access patterns
        candidates.sort(key=lambda x: (
            x.relevance_score * 0.4 +  # Content relevance
            self._context_similarity(x.context, context) * 0.3 +  # Context match
            self._recency_score(x.timestamp) * 0.2 +  # Recency
            min(x.access_count / 10, 1.0) * 0.1  # Access frequency
        ), reverse=True)
        
        rerank_time = time.time() - rerank_start
        
        # Update metrics
        self.metrics["recall_latency"].append(stage1_time)
        self.metrics["rerank_latency"].append(rerank_time)
        
        if candidates:
            self.metrics["memory_hits"] += 1
        else:
            self.metrics["memory_misses"] += 1
        
        # Update access tracking
        for event in candidates[:limit]:
            event.access_count += 1
            event.last_accessed = datetime.now()
        
        return candidates[:limit]
    
    def log_plugin_invocation(self, plugin_name: str, action: str, 
                            parameters: Dict[str, Any], result: Any,
                            success: bool, user_context: Dict[str, Any],
                            execution_time: float, error_message: Optional[str] = None):
        """Log plugin/tool invocation for memory linkage"""
        event = PluginMemoryEvent(
            plugin_name=plugin_name,
            action=action,
            parameters=parameters,
            result=result,
            success=success,
            user_context=user_context,
            timestamp=datetime.now(),
            execution_time=execution_time,
            error_message=error_message
        )
        
        self.plugin_events.append(event)
        self.metrics["plugin_invocations"] += 1
        
        if not success:
            self.metrics["plugin_failures"] += 1
        
        # Store plugin result as memory for future reference
        if success and result:
            self.store_memory(
                content=f"Plugin {plugin_name} executed {action} with result: {str(result)[:500]}",
                metadata={
                    "type": "plugin_result",
                    "plugin": plugin_name,
                    "action": action,
                    "success": success,
                    "execution_time": execution_time
                },
                context=user_context,
                user_id=user_context.get("user_id")
            )
    
    def _calculate_relevance(self, query: str, event: MemoryEvent, context: Dict[str, Any]) -> float:
        """Calculate content relevance score"""
        # Simple keyword matching (would use embeddings in production)
        query_words = set(query.lower().split())
        content_words = set(event.content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
    
    def _context_similarity(self, event_context: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Calculate context similarity score"""
        if not event_context or not query_context:
            return 0.0
        
        # Simple context matching
        matches = 0
        total = 0
        
        for key in query_context:
            if key in event_context:
                total += 1
                if event_context[key] == query_context[key]:
                    matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _recency_score(self, timestamp: datetime) -> float:
        """Calculate recency score (more recent = higher score)"""
        now = datetime.now()
        age_hours = (now - timestamp).total_seconds() / 3600
        
        # Exponential decay: score decreases with age
        return np.exp(-age_hours / 24)  # Half-life of 24 hours
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get comprehensive memory system metrics"""
        return {
            "total_memories": len(self.memory_events),
            "total_plugin_events": len(self.plugin_events),
            "avg_recall_latency": np.mean(self.metrics["recall_latency"]) if self.metrics["recall_latency"] else 0,
            "avg_rerank_latency": np.mean(self.metrics["rerank_latency"]) if self.metrics["rerank_latency"] else 0,
            "memory_hit_rate": self.metrics["memory_hits"] / max(self.metrics["memory_hits"] + self.metrics["memory_misses"], 1),
            "plugin_success_rate": (self.metrics["plugin_invocations"] - self.metrics["plugin_failures"]) / max(self.metrics["plugin_invocations"], 1),
            "context_alignment_score": self.metrics["context_alignments"] / max(len(self.memory_events), 1)
        }
    
    def get_recent_plugin_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plugin activity for monitoring"""
        recent_events = sorted(self.plugin_events, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [asdict(event) for event in recent_events]
    
    def search_memories_by_context(self, context_filter: Dict[str, Any], limit: int = 20) -> List[MemoryEvent]:
        """Search memories by context metadata"""
        matches = []
        
        for event in self.memory_events:
            match_score = self._context_similarity(event.context, context_filter)
            if match_score > 0.5:  # Threshold for context match
                event.relevance_score = match_score
                matches.append(event)
        
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:limit]


# Create singleton instance
memory_service = NeuroVaultMemoryService()