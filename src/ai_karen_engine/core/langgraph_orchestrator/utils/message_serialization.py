from typing import Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

def message_to_history_entry(message: BaseMessage) -> Dict[str, Any]:
    """Convert LangChain messages into serialisable history entries."""

    role = "system"
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"

    return {
        "role": role,
        "content": getattr(message, "content", str(message)),
        "type": message.__class__.__name__,
    }
