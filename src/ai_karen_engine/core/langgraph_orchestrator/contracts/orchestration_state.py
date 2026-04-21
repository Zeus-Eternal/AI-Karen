from typing import (
    Dict,
    Any,
    List,
    Optional,
    TypedDict,
)
from langchain_core.messages import BaseMessage

class LangGraphOrchestrationState(TypedDict):
    """Typed state for the orchestration graph"""

    # Input/Output
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    tenant_id: Optional[str]

    # Authentication & Authorization
    auth_status: Optional[str]  # "authenticated", "failed", "pending"
    user_permissions: Optional[Dict[str, Any]]
    auth_context: Optional[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]]

    # Safety & Guardrails
    safety_status: Optional[str]  # "safe", "unsafe", "review_required"
    safety_flags: Optional[List[str]]
    safety_evaluation: Optional[Dict[str, Any]]

    # Memory & Context
    memory_context: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]]

    # Intent & Planning
    detected_intent: Optional[str]
    intent_confidence: Optional[float]
    execution_plan: Optional[Dict[str, Any]]
    intent_analysis: Optional[Dict[str, Any]]

    # Routing & Execution
    selected_provider: Optional[str]
    selected_model: Optional[str]
    routing_reason: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    tool_execution_metadata: Optional[Dict[str, Any]]

    # Response Generation
    response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]

    # Salvaged from Legacy ChatOrchestrator
    structured_content: Optional[Dict[str, Any]]
    actions: Optional[List[Dict[str, Any]]]
    telemetry: Optional[Dict[str, Any]]
    formatting_payload: Optional[Dict[str, Any]]
    formatted_response: Optional[str]

    # Human-in-the-loop
    requires_approval: Optional[bool]
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    approval_reason: Optional[str]

    # Error Handling
    errors: List[str]
    warnings: List[str]

    # Streaming Support
    streaming_enabled: Optional[bool]
    stream_chunks: Optional[List[str]]
    request_config: Optional[Dict[str, Any]]

    # Medusa Extensions
    agent_trace: Optional[List[str]]
    medusa_status: Optional[str]
