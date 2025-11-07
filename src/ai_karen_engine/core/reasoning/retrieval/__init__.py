"""
Retrieval Adapters Module

Provides abstraction layers for vector stores and retrieval systems.

Components:
- SRRetriever: Protocol for SR retrieval adapters
- SRCompositeRetriever: Chain multiple retrievers
- VectorStore: Protocol for vector store backends
- MilvusClientAdapter: Adapter for Milvus client
- LlamaIndexVectorAdapter: Adapter for LlamaIndex
"""

from ai_karen_engine.core.reasoning.retrieval.adapters import (
    SRRetriever,
    SRCompositeRetriever,
)
from ai_karen_engine.core.reasoning.retrieval.vector_stores import (
    VectorStore,
    Result,
    MilvusClientAdapter,
    LlamaIndexVectorAdapter,
    StoreInfo,
)

__all__ = [
    "SRRetriever",
    "SRCompositeRetriever",
    "VectorStore",
    "Result",
    "MilvusClientAdapter",
    "LlamaIndexVectorAdapter",
    "StoreInfo",
]
