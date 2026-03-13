"""
Agent Adapters for External Frameworks

This package contains adapters for integrating with external agent frameworks:
- LangChain adapter
- DeepAgents adapter
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

# Import key classes and functions from deepagents_adapter.py (when it exists)
try:
    from .deepagents_adapter import (
        DeepAgentsAdapter,
        DeepAgentsAgentType
    )
except ImportError:
    DeepAgentsAdapter = None
    DeepAgentsAgentType = None

# Define __all__ to control what gets imported with "from src.services.agents.adapters import *"
__all__ = [
    # From langchain_adapter
    "LangChainAdapter",
    "LangChainAgentType",
    
    # From deepagents_adapter
    "DeepAgentsAdapter",
    "DeepAgentsAgentType",
]