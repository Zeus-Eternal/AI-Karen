"""
Graph-based Reasoning Module

Provides graph structures for reasoning and knowledge representation.

Components:
- CapsuleGraph: Lightweight directed graph for capsule reasoning
- ReasoningGraph: High-level reasoning graph with ICE integration
"""

from ai_karen_engine.core.reasoning.graph.capsule import (
    CapsuleGraph,
    Node,
    Edge,
)
from ai_karen_engine.core.reasoning.graph.reasoning import (
    ReasoningGraph,
)

__all__ = [
    "CapsuleGraph",
    "Node",
    "Edge",
    "ReasoningGraph",
]
