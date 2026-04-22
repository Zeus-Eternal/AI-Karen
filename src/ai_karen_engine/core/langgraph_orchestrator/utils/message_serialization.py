from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


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


def history_entry_to_message(entry: Dict[str, Any]) -> BaseMessage:
    """Convert history entry back to LangChain message"""
    role = entry.get("role", "system")
    content = entry.get("content", "")

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    else:
        return SystemMessage(content=content)


def serialize_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """Serialize list of LangChain messages"""
    return [message_to_history_entry(msg) for msg in messages]


def deserialize_messages(serialized: List[Dict[str, Any]]) -> List[BaseMessage]:
    """Deserialize list of history entries back to LangChain messages"""
    return [history_entry_to_message(entry) for entry in serialized]


def extract_last_user_content(messages: List[BaseMessage]) -> Optional[str]:
    """Extract content from the last user message"""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return None


def extract_last_assistant_content(messages: List[BaseMessage]) -> Optional[str]:
    """Extract content from the last assistant message"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return msg.content
    return None
