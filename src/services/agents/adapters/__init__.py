"""
Agent Adapters for External Frameworks

This package contains adapters for integrating with external agent frameworks:
- LangChain adapter
- LangGraph adapter
- DeepAgents adapter
- Native adapter
"""

# Import key classes and functions from langchain_adapter.py (when it exists)
try:
    from .langchain_adapter import (
        LangChainAdapter,
        LangChainAgentType
    )
except ImportError:
    LangChainAdapter = None
    LangChainAgentType = None

# Import key classes and functions from langgraph_adapter.py (when it exists)
try:
    from .langgraph_adapter import LangGraphAdapter, LangGraphNodeType
except ImportError:
    LangGraphAdapter = None
    LangGraphNodeType = None

# Import key classes and functions from deepagents_adapter.py (when it exists)
try:
    from .deepagents_adapter import (
        DeepAgentsAdapter,
        DeepAgentsAgentType
    )
except ImportError:
    DeepAgentsAdapter = None
    DeepAgentsAgentType = None

# Import key classes and functions from native_adapter.py (when it exists)
try:
    from .native_adapter import NativeAdapter, NativeExecutionMode
except ImportError:
    NativeAdapter = None
    NativeExecutionMode = None

# Define __all__ to control what gets imported with "from src.services.agents.adapters import *"
__all__ = [
    # From langchain_adapter
    "LangChainAdapter",
    "LangChainAgentType",

    # From langgraph_adapter
    "LangGraphAdapter",
    "LangGraphNodeType",
    
    # From deepagents_adapter
    "DeepAgentsAdapter",
    "DeepAgentsAgentType",

    # From native_adapter
    "NativeAdapter",
    "NativeExecutionMode",
]
