"""
Enhanced Memory System with AG-UI Integration
Provides memory management with modern data visualization and AI-powered enhancements.
"""

from ai_karen_engine.core.memory.ag_ui_manager import (
    AGUIMemoryManager,
    MemoryAnalytics,
    MemoryGridRow,
    MemoryNetworkEdge,
    MemoryNetworkNode,
)
from ai_karen_engine.core.memory.manager import (
    _METRICS,
    flush_duckdb_to_postgres,
    get_metrics,
    init_memory,
    recall_context,
    update_memory,
)
from ai_karen_engine.core.memory.session_buffer import SessionBuffer
from ai_karen_engine.core.memory.np_memory import (
    load_jsonl,
    extract_pairs,
    embed_texts,
    retrieve
)

__all__ = [
    # Original memory system
    "recall_context",
    "update_memory",
    "flush_duckdb_to_postgres",
    "get_metrics",
    "_METRICS",
    "init_memory",
    "SessionBuffer",
    # AG-UI enhanced memory system
    "AGUIMemoryManager",
    "MemoryGridRow",
    "MemoryNetworkNode",
    "MemoryNetworkEdge",
    "MemoryAnalytics",
    # Neuro-recall memory utilities
    "load_jsonl",
    "extract_pairs", 
    "embed_texts",
    "retrieve"
]
