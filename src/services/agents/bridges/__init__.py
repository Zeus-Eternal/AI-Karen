"""
Agent Bridges for System Integration

This package contains bridges for integrating the agent system with other components:
- Karen-LangChain bridge
- Karen-DeepAgents bridge
"""

# Import key classes and functions from karen_langchain_bridge.py (when it exists)
try:
    from .karen_langchain_bridge import KarenLangChainBridge
except ImportError:
    KarenLangChainBridge = None

# Import key classes and functions from karen_deepagents_bridge.py (when it exists)
try:
    from .karen_deepagents_bridge import KarenDeepAgentsBridge
except ImportError:
    KarenDeepAgentsBridge = None

# Define __all__ to control what gets imported with "from src.services.agents.bridges import *"
__all__ = [
    # From karen_langchain_bridge
    "KarenLangChainBridge",
    
    # From karen_deepagents_bridge
    "KarenDeepAgentsBridge",
]