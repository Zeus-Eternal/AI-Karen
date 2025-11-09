# Kari Chat System Flow Contract

**Version:** 1.0.0
**Date:** 2025-11-08
**Scope:** Production-grade function signatures and payload schemas for `src/ai_karen_engine/chat/`

---

## 🎯 Contract Overview

This document defines the **exact interfaces** between all chat system modules. Every function signature, payload schema, and error format is specified here to ensure compatibility without guesswork.

**Contract Principles:**
- ✅ All payloads are type-safe (TypedDict/Pydantic)
- ✅ All functions carry `correlation_id`
- ✅ All errors are structured envelopes
- ✅ All async functions return `Awaitable`
- ✅ All metrics emit on entry/exit

---

## 📦 Module 1: `websocket_gateway.py`

### Ingress Contract

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class WebSocketMessage:
    """Incoming WebSocket message"""
    type: str  # "message", "command", "presence", "typing"
    content: str
    user_id: str
    session_id: str
    tenant_id: Optional[str]
    metadata: Dict[str, Any]
    timestamp: float

async def handle_websocket_connection(
    websocket: WebSocket,
    user_token: str
) -> None:
    """
    Main WebSocket connection handler.

    Args:
        websocket: WebSocket connection object
        user_token: JWT token for authentication

    Raises:
        AuthenticationError: If token invalid
        RateLimitError: If user exceeds rate limit

    Emits:
        kari_chat_connections_total
        kari_chat_active_sessions
    """
    pass

async def authenticate_websocket(
    token: str
) -> Dict[str, Any]:
    """
    Validate JWT and extract user context.

    Args:
        token: JWT token string

    Returns:
        {
            "user_id": str,
            "tenant_id": str,
            "roles": List[str],
            "session_id": str,
            "expires_at": int
        }

    Raises:
        AuthenticationError: If validation fails
    """
    pass

async def forward_to_hub(
    message: WebSocketMessage,
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> None:
    """
    Forward validated message to chat_hub.

    Args:
        message: Validated WebSocket message
        user_ctx: User context from authentication
        correlation_id: UUID for tracing

    Emits:
        kari_chat_messages_forwarded_total
    """
    pass
```

### Payload Schema

```python
# Incoming from client
{
    "type": "message",  # Required: "message" | "command" | "typing" | "presence"
    "content": str,      # Required: message text or command
    "metadata": {        # Optional
        "files": List[str],      # File IDs
        "reply_to": str,         # Message ID being replied to
        "mentions": List[str],   # User IDs mentioned
        "context_override": Dict # Force specific context
    }
}

# Outgoing to client
{
    "type": "response",  # "response" | "error" | "ack" | "typing" | "stream_chunk"
    "content": str,      # Response text or error message
    "correlation_id": str,
    "metadata": {
        "message_id": str,
        "timestamp": float,
        "model_used": str,
        "tools_called": List[str],
        "tokens_used": int
    }
}
```

---

## 📦 Module 2: `chat_hub.py`

### Router Contract

```python
from typing import Literal

MessageType = Literal["message", "command", "presence", "typing"]
RoutingDecision = Literal["orchestrator", "instruction_processor", "discard"]

async def route_message(
    message: WebSocketMessage,
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> RoutingDecision:
    """
    Route incoming message to appropriate handler.

    Args:
        message: Validated WebSocket message
        user_ctx: User authentication context
        correlation_id: Trace ID

    Returns:
        Routing decision string

    Emits:
        kari_chat_routing_decisions_total{destination="..."}
    """
    pass

async def handle_command(
    message: WebSocketMessage,
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> Dict[str, Any]:
    """
    Forward command to instruction_processor.

    Args:
        message: Command message
        user_ctx: User context
        correlation_id: Trace ID

    Returns:
        {
            "type": "command_result",
            "success": bool,
            "result": Any,
            "error": Optional[str]
        }
    """
    pass

async def handle_user_message(
    message: WebSocketMessage,
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> Dict[str, Any]:
    """
    Forward user message to chat_orchestrator.

    Args:
        message: User message
        user_ctx: User context
        correlation_id: Trace ID

    Returns:
        Orchestrator response payload
    """
    pass
```

---

## 📦 Module 3: `instruction_processor.py`

### Command Processing Contract

```python
from typing import Optional
from pydantic import BaseModel

class Instruction(BaseModel):
    """Parsed instruction model"""
    type: str  # "mode_switch" | "config_change" | "system_directive" | "persona_change"
    action: str
    parameters: Dict[str, Any]
    requires_confirmation: bool
    rbac_required: List[str]

async def parse_instruction(
    content: str,
    user_ctx: Dict[str, Any]
) -> Optional[Instruction]:
    """
    Parse command string into structured instruction.

    Args:
        content: Raw command string (e.g., "/set mode analysis")
        user_ctx: User context for permission checks

    Returns:
        Parsed Instruction or None if not a command

    Examples:
        "/set mode analysis" → Instruction(type="mode_switch", action="set_mode", ...)
        "/clear context" → Instruction(type="config_change", action="clear_context", ...)
    """
    pass

async def execute_instruction(
    instruction: Instruction,
    conversation_id: str,
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> Dict[str, Any]:
    """
    Execute parsed instruction.

    Args:
        instruction: Parsed instruction
        conversation_id: Current conversation ID
        user_ctx: User context
        correlation_id: Trace ID

    Returns:
        {
            "success": bool,
            "result": Any,
            "message": str,
            "state_changes": Dict[str, Any]
        }

    Raises:
        PermissionError: If user lacks required RBAC roles
        ValidationError: If instruction invalid
    """
    pass
```

### Instruction Payload Schema

```python
# Command examples
{
    "type": "mode_switch",
    "action": "set_mode",
    "parameters": {
        "mode": "analysis",  # "chat" | "analysis" | "creative" | "technical"
        "temperature": 0.3,
        "model_override": "gpt-4"
    },
    "requires_confirmation": false,
    "rbac_required": ["chat.mode.switch"]
}

{
    "type": "config_change",
    "action": "update_context",
    "parameters": {
        "max_tokens": 4096,
        "include_history": true,
        "memory_depth": "deep"
    },
    "requires_confirmation": false,
    "rbac_required": ["chat.config.edit"]
}

{
    "type": "persona_change",
    "action": "set_persona",
    "parameters": {
        "persona": "technical_expert",
        "tone": "formal",
        "expertise_domains": ["engineering", "architecture"]
    },
    "requires_confirmation": true,
    "rbac_required": ["chat.persona.change"]
}
```

---

## 📦 Module 4: `conversation_models.py`

### Core Models

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    """Single message in conversation"""
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: datetime
    user_id: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Attachments
    files: List[str] = Field(default_factory=list)
    tools_called: List[str] = Field(default_factory=list)

    # Metrics
    tokens_used: Optional[int]
    model_used: Optional[str]

class Conversation(BaseModel):
    """Conversation entity"""
    id: str
    tenant_id: str
    participants: List[str]
    created_at: datetime
    updated_at: datetime

    # Configuration
    mode: str = "chat"
    model: Optional[str]
    system_instructions: Optional[str]

    # State
    pinned_messages: List[str] = Field(default_factory=list)
    context_snapshot: Optional[Dict[str, Any]]

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TurnContext(BaseModel):
    """Context for a single conversation turn"""
    conversation_id: str
    current_message: Message

    # History
    recent_messages: List[Message]
    relevant_history: List[Message] = Field(default_factory=list)

    # Memory
    short_term_context: List[Dict[str, Any]] = Field(default_factory=list)
    long_term_context: List[Dict[str, Any]] = Field(default_factory=list)
    vault_facts: List[Dict[str, Any]] = Field(default_factory=list)

    # Configuration
    max_tokens: int = 4096
    temperature: float = 0.7

    # User context
    user_ctx: Dict[str, Any]
    correlation_id: str
```

---

## 📦 Module 5: `context_integrator.py`

### Context Assembly Contract

```python
from typing import List

async def integrate_context(
    current_message: Message,
    conversation: Conversation,
    user_ctx: Dict[str, Any],
    correlation_id: str,
    max_tokens: int = 4096
) -> TurnContext:
    """
    Assemble effective context window for orchestrator.

    Args:
        current_message: Current user message
        conversation: Conversation state
        user_ctx: User context
        correlation_id: Trace ID
        max_tokens: Token budget

    Returns:
        TurnContext with integrated context

    Process:
        1. Fetch recent messages (last N turns)
        2. Query memory_processor for relevant memories
        3. Query production_memory for vault facts
        4. Rank and truncate to token budget
        5. Deduplicate overlapping content

    Emits:
        kari_chat_context_tokens_total
        kari_chat_context_items_total{source="..."}
    """
    pass

async def rank_context_items(
    items: List[Dict[str, Any]],
    current_message: str,
    max_items: int
) -> List[Dict[str, Any]]:
    """
    Rank and filter context items by relevance.

    Args:
        items: Candidate context items
        current_message: Current message for relevance scoring
        max_items: Maximum items to return

    Returns:
        Ranked and filtered items

    Ranking Criteria:
        1. Exact keyword matches (weight: 1.0)
        2. Semantic similarity (weight: 0.8)
        3. Recency (weight: 0.6)
        4. User-pinned (weight: 2.0)
    """
    pass
```

---

## 📦 Module 6: `memory_processor.py`

### Memory Retrieval Contract

```python
from typing import List, Optional

class MemoryItem(BaseModel):
    """Memory retrieval result"""
    content: str
    source: Literal["short_term", "long_term", "vault", "domain"]
    score: float
    timestamp: Optional[datetime]
    metadata: Dict[str, Any]

async def retrieve_relevant_memories(
    query: str,
    conversation_id: str,
    user_id: str,
    tenant_id: str,
    top_k: int = 10
) -> List[MemoryItem]:
    """
    Retrieve relevant memories for current query.

    Args:
        query: Current message or query
        conversation_id: Conversation context
        user_id: User making query
        tenant_id: Tenant isolation
        top_k: Maximum memories to return

    Returns:
        List of relevant memory items with scores

    Sources:
        - Short-term: Redis session buffer
        - Long-term: Milvus embeddings + Postgres
        - Vault: NeuroVault facts
        - Domain: Specialized knowledge stores

    Emits:
        kari_chat_memory_retrieval_total{source="..."}
        kari_chat_memory_retrieval_latency_seconds{source="..."}
    """
    pass
```

---

## 📦 Module 7: `production_memory.py`

### Memory Write Contract

```python
async def store_conversation_turn(
    message: Message,
    conversation: Conversation,
    response: Optional[Message],
    metadata: Dict[str, Any]
) -> None:
    """
    Persist conversation turn to production storage.

    Args:
        message: User message
        conversation: Conversation context
        response: Assistant response (if any)
        metadata: Turn metadata (tools used, tokens, etc.)

    Process:
        1. Write to Postgres (ACID)
        2. Trigger embedding job (async)
        3. Update search index
        4. Update conversation summary

    Guarantees:
        - Idempotent (can retry safely)
        - ACID transaction for critical data
        - Eventually consistent for embeddings

    Emits:
        kari_chat_memory_writes_total
        kari_chat_memory_write_latency_seconds
    """
    pass

async def trigger_embedding_job(
    message_id: str,
    content: str,
    metadata: Dict[str, Any]
) -> None:
    """
    Queue message for embedding generation.

    Args:
        message_id: Message ID
        content: Message text
        metadata: Context for embedding

    Implementation:
        - Async job queue (Celery/Redis)
        - Batch embeddings for efficiency
        - Store in Milvus with metadata
    """
    pass
```

---

## 📦 Module 8: `chat_orchestrator.py`

### Orchestration Contract

```python
from typing import AsyncIterator

class OrchestratorResponse(BaseModel):
    """Orchestrator output"""
    content: str
    message_id: str
    model_used: str
    tokens_used: int
    tools_called: List[str]
    reasoning_steps: Optional[List[str]]
    metadata: Dict[str, Any]

async def orchestrate_turn(
    turn_context: TurnContext,
    streaming: bool = False
) -> OrchestratorResponse | AsyncIterator[str]:
    """
    Main orchestration logic for conversation turn.

    Args:
        turn_context: Integrated context for turn
        streaming: Enable token streaming

    Returns:
        Complete response or stream iterator

    Process:
        1. Select model via factory
        2. Determine tool requirements
        3. Execute reasoning steps
        4. Call tools if needed (via tool_integration_service)
        5. Generate response
        6. Post-process (safety, formatting)

    Emits:
        kari_chat_orchestration_total
        kari_chat_orchestration_latency_seconds
        kari_chat_model_selections_total{model="..."}
    """
    pass

async def select_model(
    turn_context: TurnContext,
    conversation: Conversation
) -> str:
    """
    Select appropriate model for turn.

    Args:
        turn_context: Turn context
        conversation: Conversation state

    Returns:
        Model identifier

    Selection Logic:
        1. User override (if permitted)
        2. Conversation mode default
        3. Task complexity heuristic
        4. Fallback to default

    Examples:
        mode="analysis", complex_query=True → "gpt-4"
        mode="chat", simple_query=True → "gpt-3.5-turbo"
    """
    pass

async def determine_tool_requirements(
    turn_context: TurnContext
) -> List[str]:
    """
    Analyze if tools are needed for turn.

    Args:
        turn_context: Turn context

    Returns:
        List of tool IDs to invoke

    Detection Heuristics:
        - Code blocks → code_execution_service
        - File mentions → file_attachment_service
        - Search queries → search tools
        - Time/date queries → time tools
    """
    pass
```

---

## 📦 Module 9: `tool_integration_service.py`

### Tool Invocation Contract

```python
class ToolCall(BaseModel):
    """Tool invocation request"""
    tool_id: str
    parameters: Dict[str, Any]
    user_ctx: Dict[str, Any]
    correlation_id: str

class ToolResult(BaseModel):
    """Tool invocation result"""
    tool_id: str
    success: bool
    result: Any
    error: Optional[str]
    metadata: Dict[str, Any]

async def invoke_tool(
    tool_call: ToolCall
) -> ToolResult:
    """
    Invoke tool with safety checks.

    Args:
        tool_call: Tool invocation request

    Returns:
        Tool result

    Safety Checks:
        1. RBAC validation (user has permission)
        2. Rate limit check
        3. Input sanitization
        4. Tool whitelist validation

    Raises:
        PermissionError: Insufficient RBAC roles
        RateLimitError: Rate limit exceeded
        ToolNotFoundError: Tool not registered

    Emits:
        kari_chat_tool_calls_total{tool="..."}
        kari_chat_tool_latency_seconds{tool="..."}
        kari_chat_tool_errors_total{tool="...", error="..."}
    """
    pass

async def validate_tool_permission(
    tool_id: str,
    user_ctx: Dict[str, Any]
) -> bool:
    """
    Validate user has permission for tool.

    Args:
        tool_id: Tool identifier
        user_ctx: User context with roles

    Returns:
        True if permitted

    Raises:
        PermissionError: If not permitted
    """
    pass
```

### Tool Registry Schema

```python
{
    "tool_id": "web_search",
    "name": "Web Search",
    "description": "Search the web for information",
    "required_roles": ["chat.tools.search"],
    "rate_limit": {
        "per_minute": 10,
        "per_hour": 100
    },
    "parameters_schema": {
        "query": {"type": "string", "required": true},
        "max_results": {"type": "integer", "default": 5}
    },
    "handler": "capsule.web_researcher"  # Link to capsule system!
}
```

---

## 📦 Module 10: `stream_processor.py`

### Streaming Contract

```python
from typing import AsyncIterator

async def stream_response(
    model_stream: AsyncIterator[str],
    correlation_id: str,
    websocket: WebSocket
) -> None:
    """
    Stream model tokens to client.

    Args:
        model_stream: Token stream from model
        correlation_id: Trace ID
        websocket: Client WebSocket connection

    Process:
        1. Receive token from model
        2. Wrap in envelope
        3. Send to WebSocket
        4. Track metrics

    Emits:
        kari_chat_tokens_streamed_total
        kari_chat_stream_latency_seconds
    """
    async for token in model_stream:
        await websocket.send_json({
            "type": "stream_chunk",
            "content": token,
            "correlation_id": correlation_id,
            "metadata": {
                "timestamp": time.time()
            }
        })

async def handle_stream_error(
    error: Exception,
    correlation_id: str,
    websocket: WebSocket
) -> None:
    """
    Handle streaming errors gracefully.

    Args:
        error: Exception that occurred
        correlation_id: Trace ID
        websocket: Client connection

    Actions:
        1. Log error with correlation_id
        2. Send error envelope to client
        3. Emit error metric
    """
    pass
```

---

## 📦 Module 11: `summarizer.py`

### Summarization Contract

```python
class ConversationSummary(BaseModel):
    """Conversation summary"""
    conversation_id: str
    summary: str
    key_topics: List[str]
    participant_intents: Dict[str, str]
    created_at: datetime
    message_range: tuple[str, str]  # (first_id, last_id)

async def summarize_conversation(
    conversation_id: str,
    message_ids: Optional[List[str]] = None,
    max_length: int = 500
) -> ConversationSummary:
    """
    Generate conversation summary.

    Args:
        conversation_id: Conversation to summarize
        message_ids: Specific messages (or all if None)
        max_length: Maximum summary length

    Returns:
        Conversation summary

    Use Cases:
        - Memory compaction
        - Search indexing
        - Context reconstruction

    Emits:
        kari_chat_summaries_generated_total
    """
    pass
```

---

## 📦 Module 12: `enhanced_conversation_manager.py`

### State Management Contract

```python
async def get_conversation(
    conversation_id: str,
    user_ctx: Dict[str, Any]
) -> Conversation:
    """
    Retrieve conversation state.

    Args:
        conversation_id: Conversation ID
        user_ctx: User context for access control

    Returns:
        Conversation object

    Raises:
        PermissionError: User not participant
        NotFoundError: Conversation doesn't exist
    """
    pass

async def update_conversation_state(
    conversation_id: str,
    updates: Dict[str, Any],
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> Conversation:
    """
    Update conversation configuration.

    Args:
        conversation_id: Conversation to update
        updates: State changes
        user_ctx: User context
        correlation_id: Trace ID

    Returns:
        Updated conversation

    Allowed Updates:
        - mode: str
        - model: str
        - system_instructions: str
        - pinned_messages: List[str]
        - metadata: Dict

    Emits:
        kari_chat_conversation_updates_total{field="..."}
    """
    pass

async def pin_message(
    conversation_id: str,
    message_id: str,
    user_ctx: Dict[str, Any]
) -> None:
    """
    Pin message to conversation context.

    Args:
        conversation_id: Conversation ID
        message_id: Message to pin
        user_ctx: User context

    Effects:
        - Message always included in context
        - High priority in context_integrator
    """
    pass
```

---

## 📦 Module 13: `conversation_search_service.py`

### Search Contract

```python
from typing import List

class SearchResult(BaseModel):
    """Search result"""
    message_id: str
    conversation_id: str
    content: str
    score: float
    timestamp: datetime
    metadata: Dict[str, Any]

async def search_conversations(
    query: str,
    user_id: str,
    tenant_id: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10
) -> List[SearchResult]:
    """
    Search past conversations.

    Args:
        query: Search query
        user_id: User making search
        tenant_id: Tenant isolation
        filters: Optional filters (date range, conversation_id, etc.)
        top_k: Maximum results

    Returns:
        Ranked search results

    Search Methods:
        1. Fulltext search (Postgres)
        2. Vector search (Milvus)
        3. Hybrid ranking

    Emits:
        kari_chat_searches_total
        kari_chat_search_latency_seconds
    """
    pass
```

---

## 🔗 Integration with Capsule System

### Capsule-Tool Bridge

```python
# tool_integration_service.py integration

async def invoke_capsule_as_tool(
    capsule_id: str,
    request: Dict[str, Any],
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> ToolResult:
    """
    Invoke capsule through tool interface.

    Args:
        capsule_id: Capsule identifier (e.g., "capsule.web_researcher")
        request: Tool request parameters
        user_ctx: User context
        correlation_id: Trace ID

    Returns:
        Tool result wrapping capsule result

    Implementation:
        from ai_karen_engine.capsules import get_capsule_orchestrator

        orchestrator = get_capsule_orchestrator()
        capsule_result = await orchestrator.execute_capsule(
            capsule_id=capsule_id,
            request=request,
            user_ctx=user_ctx,
            correlation_id=correlation_id
        )

        return ToolResult(
            tool_id=capsule_id,
            success=True,
            result=capsule_result.result,
            metadata=capsule_result.metadata
        )
    """
    pass
```

---

## ⚠️ Error Envelope Contract

### Standard Error Format

```python
class ChatError(BaseModel):
    """Standard error envelope"""
    type: str  # "authentication" | "permission" | "validation" | "internal" | "rate_limit"
    message: str
    retryable: bool
    correlation_id: str
    details: Optional[Dict[str, Any]]

# Example errors

AuthenticationError:
{
    "type": "authentication",
    "message": "JWT token invalid or expired",
    "retryable": false,
    "correlation_id": "abc-123",
    "details": {"error_code": "TOKEN_EXPIRED"}
}

RateLimitError:
{
    "type": "rate_limit",
    "message": "Rate limit exceeded for tool: web_search",
    "retryable": true,
    "correlation_id": "abc-123",
    "details": {
        "retry_after": 60,
        "limit": 10,
        "window": "minute"
    }
}

InternalError:
{
    "type": "internal",
    "message": "Orchestration failed due to provider timeout",
    "retryable": true,
    "correlation_id": "abc-123",
    "details": {
        "provider": "openai",
        "timeout": 30
    }
}
```

---

## 📊 Metrics Contract

### Required Metrics

All modules must emit these metrics:

```python
# Request metrics
kari_chat_requests_total{module="...", status="success|error"}
kari_chat_request_latency_seconds{module="..."}

# Component-specific
kari_chat_connections_total
kari_chat_active_sessions
kari_chat_messages_forwarded_total
kari_chat_routing_decisions_total{destination="..."}
kari_chat_context_tokens_total
kari_chat_context_items_total{source="..."}
kari_chat_memory_retrieval_total{source="..."}
kari_chat_memory_writes_total
kari_chat_orchestration_total
kari_chat_model_selections_total{model="..."}
kari_chat_tool_calls_total{tool="..."}
kari_chat_tool_errors_total{tool="...", error="..."}
kari_chat_tokens_streamed_total
kari_chat_summaries_generated_total
kari_chat_searches_total
```

---

## 🧪 Testing Contract

### Required Test Categories

```python
# 1. Flow Tests
async def test_websocket_to_response_flow():
    """End-to-end: WebSocket → Hub → Orchestrator → Stream → Persist"""
    pass

# 2. RBAC Tests
async def test_unauthorized_tool_access():
    """Verify tool access blocked without RBAC roles"""
    pass

# 3. Context Tests
async def test_context_integration_token_budget():
    """Verify context respects token limits"""
    pass

# 4. Error Tests
async def test_provider_failure_graceful_degradation():
    """Verify fallback when LLM provider fails"""
    pass

# 5. Performance Tests
async def test_streaming_under_load():
    """Verify streaming stable with 100 concurrent users"""
    pass
```

---

## 🎯 Go-Live Verification Checklist

Before production deployment, verify:

- [ ] All function signatures match this contract
- [ ] All payloads validate with Pydantic models
- [ ] All errors use standard envelope format
- [ ] All metrics are emitting
- [ ] All async functions are awaitable
- [ ] All database queries are parameterized
- [ ] All WebSocket connections authenticated
- [ ] All tool calls validated for RBAC
- [ ] All streaming errors handled gracefully
- [ ] All correlation IDs propagate through stack

---

## 📞 Support

**Contract Questions:** Zeus - Chief Architect
**Documentation:** `/docs/chat/`
**Code:** `/src/ai_karen_engine/chat/`
**Related:** [Capsule Framework Contracts](/docs/capsules/)

---

**Contract Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** 2025-11-08
