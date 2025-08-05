"""
Enhanced Memory System with AG-UI Integration
Provides memory management with modern data visualization and AI-powered enhancements.
"""

from .manager import (
    recall_context,
    update_memory,
    flush_duckdb_to_postgres,
    get_metrics,
    _METRICS,
    init_memory
)

from .ag_ui_manager import (
    AGUIMemoryManager,
    MemoryGridRow,
    MemoryNetworkNode,
    MemoryNetworkEdge,
    MemoryAnalytics
)

from .session_buffer import SessionBuffer

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
    "MemoryAnalytics"
]