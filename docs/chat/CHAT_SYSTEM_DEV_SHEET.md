# Kari Chat System — Dev Sheet

**Version:** 1.0.0
**Date:** 2025-11-08
**Scope:** Production alignment for `src/ai_karen_engine/chat/`

---

## 🎯 Overview

This document defines the **production-grade architecture** for Kari's conversational runtime using the existing chat modules. No new structure — this sheet defines what each piece is responsible for, how they interlock, and what must be true for production.

**Module Structure:**
```
chat/
├── __init__.py
├── chat_hub.py
├── chat_orchestrator.py
├── code_execution_service.py
├── context_integrator.py
├── conversation_models.py
├── conversation_search_service.py
├── dependencies.py
├── enhanced_conversation_manager.py
├── factory.py
├── file_attachment_service.py
├── hook_enabled_file_service.py
├── instruction_processor.py
├── memory_processor.py
├── multimedia_service.py
├── production_memory.py
├── stream_processor.py
├── summarizer.py
├── tool_integration_service.py
└── websocket_gateway.py
```

---

## 1. Core Execution Flow

**Canonical pipeline for every message (must be implemented via existing modules):**

```
1. websocket_gateway.py
   ↓
2. chat_hub.py
   ↓
3. instruction_processor.py
   ↓
4. context_integrator.py + memory_processor.py + production_memory.py
   ↓
5. chat_orchestrator.py + factory.py + conversation_models.py
   ↓
6. tool_integration_service.py + code_execution_service.py +
   file_attachment_service.py + multimedia_service.py
   ↓
7. stream_processor.py
   ↓
8. summarizer.py + enhanced_conversation_manager.py
   ↓
9. Persist + index via production_memory.py and conversation_search_service.py
```

**This is the ONLY supported production flow. Shortcuts go away.**

---

## 2. Module Responsibilities (Hard Contracts)

Each file has a clear, enforced role. Team must ensure no cross-responsibility leaks.

### `websocket_gateway.py`

**Role:** Real-time ingress/egress

**Responsibilities:**
- Accepts WebSocket connections (UI, API clients)
- Authenticates (JWT/session) before forwarding messages
- Attaches `correlation_id` and `user_context` to each message
- Forwards to `chat_hub` only, never directly to orchestrator or tools
- Emits connection / message metrics

**Production Requirements:**
- ✅ Reject unauthenticated connections
- ✅ Enforce max message size
- ✅ Rate limit per user/tenant
- ✅ No business logic beyond auth and routing

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-1-websocket_gatewaypy)

---

### `chat_hub.py`

**Role:** Central router for all chat events

**Responsibilities:**
- Receives normalized message events from `websocket_gateway`
- Routes to:
  * `instruction_processor` (for command/system-style inputs)
  * `chat_orchestrator` (for plain user messages)
- Handles typing indicators, presence, simple acks
- All downstream calls must include `correlation_id`

**Production Requirements:**
- ✅ No business logic beyond routing and basic validation
- ✅ All errors must be traced and never swallowed
- ✅ Emit routing decision metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-2-chat_hubpy)

---

### `instruction_processor.py`

**Role:** Command / meta-instruction brain

**Responsibilities:**
- Detects and parses:
  * `/commands`, configuration changes, mode switches
  * System directives, persona changes, routing hints
- Normalizes into internal instruction model defined in `conversation_models.py`
- Passes enriched request to `chat_orchestrator`

**Production Requirements:**
- ✅ No direct tool calls
- ✅ No direct DB access
- ✅ All structural changes to conversation state must go through `enhanced_conversation_manager`
- ✅ RBAC enforcement for privileged commands

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-3-instruction_processorpy)

---

### `conversation_models.py`

**Role:** Shared typed contracts

**Responsibilities:**
- Defines:
  * `Conversation`, `Message`, `TurnContext`
  * Enums for message types, roles, sources
  * Any DTOs used by orchestrator, tools, memory
- Single source of truth for shapes passed between modules

**Production Requirements:**
- ✅ Backward compatible evolution
- ✅ No business logic; model + validation only
- ✅ Pydantic validation for all models

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-4-conversation_modelspy)

---

### `context_integrator.py`

**Role:** Assemble effective context window

**Responsibilities:**
- Consumes:
  * Current message
  * Recent conversation history
  * Results from `memory_processor` and `production_memory`
- Applies:
  * Ranking
  * Truncation
  * Deduplication
  * Relevance filters
- Outputs final context bundle for `chat_orchestrator`

**Production Requirements:**
- ✅ Deterministic selection rules
- ✅ Tunable token budget (config-driven)
- ✅ No raw DB queries; use `production_memory` / `memory_processor` / search service
- ✅ Emit context metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-5-context_integratorpy)

---

### `memory_processor.py`

**Role:** Glue between runtime chat and memory subsystems

**Responsibilities:**
- Calls:
  * Short-term / session buffer
  * Long-term embeddings (e.g., Milvus via memory layer)
  * Domain memories
- Returns candidate memory items with scores

**Production Requirements:**
- ✅ No direct user-facing formatting
- ✅ No writes to persistent stores; delegates to `production_memory`
- ✅ Emit retrieval metrics by source

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-6-memory_processorpy)

---

### `production_memory.py`

**Role:** Production-safe memory facade

**Responsibilities:**
- Writing conversation events
- Storing message metadata
- Triggering embedding jobs
- Calling NeuroRecall / NeuroVault interfaces

**Production Requirements:**
- ✅ ACID-safe writes
- ✅ Idempotent on retries
- ✅ No complex joins embedded in chat flow; use prepared queries / views
- ✅ Schema alignment with Postgres / vector DB

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-7-production_memorypy)

---

### `chat_orchestrator.py`

**Role:** The brain of the chat runtime

**Responsibilities:**
- Receives:
  * User message
  * Instructions
  * Integrated context from `context_integrator`
- Decides:
  * Which model (via `factory` / `conversation_models`)
  * Whether to use tools (`tool_integration_service`)
  * Whether to stream (`stream_processor`)
- Coordinates:
  * Reasoning steps
  * Memory read/write decisions
  * Final response routing

**Production Requirements:**
- ✅ All decisions logged with `correlation_id`
- ✅ No direct WebSocket or DB logic
- ✅ Clean separation: orchestrates, doesn't execute side-effects
- ✅ Emit orchestration metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-8-chat_orchestratorpy)

---

### `factory.py`

**Role:** Model & provider selection

**Responsibilities:**
- Abstracts:
  * Local models
  * Remote providers
  * Special modes (analysis, summarization, code, etc.)
- Controlled via configuration and RBAC

**Production Requirements:**
- ✅ No hard-coded API keys
- ✅ Deterministic routing rules
- ✅ Safe fallbacks if provider fails
- ✅ Emit model selection metrics

---

### `tool_integration_service.py`

**Role:** Tool / plugin gateway

**Responsibilities:**
- Safe invocation of:
  * Search tools
  * External APIs
  * Kari capsules
  * System utilities
- Validates:
  * Permissions (RBAC)
  * Rate limits
  * Allowed tool list

**Production Requirements:**
- ✅ No arbitrary eval/exec
- ✅ All tool calls auditable
- ✅ Adhere to capsule & plugin security policies
- ✅ Emit tool call metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-9-tool_integration_servicepy)

---

### `code_execution_service.py`

**Role:** Confined code execution

**Responsibilities:**
- For code explanations, test runs, etc.
- Must run:
  * Sandboxed
  * Resource-limited
  * With strict whitelists

**Production Requirements:**
- ✅ Absolutely no raw OS-level side-effects outside sandbox
- ✅ Configurable enable/disable per environment & role
- ✅ Audit all code execution

---

### `file_attachment_service.py` / `hook_enabled_file_service.py`

**Role:** File intake and post-processing

**Responsibilities:**
- Validate, store, index user files
- `hook_enabled_file_service`:
  * Allows extension points (e.g., auto-summary, extract content, run scanners)

**Production Requirements:**
- ✅ Virus scan / content policy hooks
- ✅ Size/type limits
- ✅ Clear linkage to conversation and user
- ✅ No direct filesystem access from chat flow

---

### `multimedia_service.py`

**Role:** Non-text input/output handling

**Responsibilities:**
- Image/audio/video attachments and model queries
- Produces normalized text/metadata back into main flow

**Production Requirements:**
- ✅ Respect same auth + logging
- ✅ No external calls without config+RBAC
- ✅ Emit multimedia processing metrics

---

### `stream_processor.py`

**Role:** Streaming output management

**Responsibilities:**
- Handles partial token streaming to client
- Integrates with orchestrator and WebSocket

**Production Requirements:**
- ✅ Must preserve ordering and correlation IDs
- ✅ Gracefully handle provider interruptions
- ✅ No leaking internal reasoning tokens unless explicitly configured
- ✅ Emit streaming metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-10-stream_processorpy)

---

### `summarizer.py`

**Role:** Conversation summarization

**Responsibilities:**
- Builds rolling / episodic summaries:
  * For memory compaction
  * Quick context reconstruction
  * Search indexing

**Production Requirements:**
- ✅ Deterministic formats
- ✅ Compatible with `conversation_search_service` and memory schema
- ✅ Emit summarization metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-11-summarizerpy)

---

### `enhanced_conversation_manager.py`

**Role:** High-level state manager

**Responsibilities:**
- Owns:
  * Pinned messages
  * System instructions
  * Mode flags
  * Participants
  * Context snapshots
- Interface between orchestrator and storage

**Production Requirements:**
- ✅ Single source of truth about conversation configuration
- ✅ All updates logged
- ✅ RBAC enforcement for state changes

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-12-enhanced_conversation_managerpy)

---

### `conversation_search_service.py`

**Role:** Retrieval over past conversations

**Responsibilities:**
- Uses:
  * Fulltext / vector search indexes
  * Summaries from `summarizer`
- Returns candidates for:
  * `context_integrator`
  * Analytics

**Production Requirements:**
- ✅ No direct model calls
- ✅ Uses index-friendly projections
- ✅ Emit search metrics

**Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#module-13-conversation_search_servicepy)

---

### `dependencies.py`

**Role:** Wiring / DI

**Responsibilities:**
- Central place to construct:
  * Orchestrator
  * Services
  * Providers

**Production Requirements:**
- ✅ No logic beyond wiring
- ✅ Environment-driven configuration
- ✅ Clear initialization sequence

---

## 3. Cross-Cutting Production Requirements

### 3.1 Auth & RBAC

**Requirements:**
- ✅ All entrypoints: validate JWT/session
- ✅ Role-aware behaviors:
  * Admin features (debug, devops) disabled unless permitted
- ✅ No module bypasses security:
  * Security is enforced at gateway + hub + specific service level

**RBAC Roles:**
```
chat.user              # Basic chat access
chat.tools.search      # Search tools access
chat.tools.code        # Code execution access
chat.mode.switch       # Mode switching
chat.config.edit       # Configuration changes
chat.persona.change    # Persona changes
chat.admin             # Admin features
```

---

### 3.2 Observability

**Metrics (Prometheus):**
```
kari_chat_requests_total
kari_chat_active_sessions
kari_chat_latency_seconds (p50/p95)
kari_chat_tool_calls_total
kari_chat_errors_total
kari_chat_tokens_streamed_total
kari_chat_memory_writes_total
kari_chat_context_tokens_total
```

**Logs:**
- ✅ Every request path carries `correlation_id`
- ✅ Key events: intent detection, recall success/fail, tool use, provider selection, timeouts
- ✅ Structured logging (JSON format)
- ✅ No sensitive data in logs

**Tracing:**
- ✅ Correlation ID propagates through entire stack
- ✅ Trace storage (optional: Jaeger, Zipkin)

---

### 3.3 Error Handling

**Requirements:**
- ✅ No raw exceptions to clients
- ✅ Use structured error envelopes:
  * `type`, `message`, `retryable`, `correlation_id`
- ✅ Orchestrator owns fallback strategy:
  * Retry providers
  * Degrade features (no tools, minimal context)
  * Graceful apology when all else fails

**Error Contract:** See [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md#error-envelope-contract)

---

## 4. Memory & Context Rules

**Using `memory_processor` & `production_memory`:**

### Short-term Memory
- Recent turns in-process + Redis
- Session buffer (last N messages)
- Fast access, volatile

### Long-term Memory
- Summaries + embeddings via `production_memory`
- Milvus vector store
- Postgres for structured data
- Persistent, searchable

### Context Builder
`context_integrator` must:
- ✅ Cap token budget (configurable)
- ✅ Prioritize:
  1. Current thread (highest priority)
  2. Relevant past threads (search results)
  3. Vault facts (NeuroVault integration)
  4. Pinned messages (user-defined)
- ✅ Be deterministic and testable
- ✅ Emit context composition metrics

---

## 5. Testing & CI Requirements

**Before release, CI must cover:**

### 1. Flow Tests
- ✅ WebSocket → Hub → Orchestrator → Stream → Persist
- ✅ Command processing → State change → Persist
- ✅ Tool invocation → RBAC → Execution → Result

### 2. RBAC Tests
- ✅ Unauthorized tool/code execution blocked
- ✅ Unauthorized config changes blocked
- ✅ Role inheritance works correctly

### 3. Memory Tests
- ✅ Context integration respects budgets
- ✅ Memory retrieval returns relevant results
- ✅ Memory writes are idempotent

### 4. Regression Tests
- ✅ No module reaches around orchestrator for tools or DB
- ✅ All errors use standard envelope
- ✅ All metrics emit correctly

### 5. Resilience Tests
- ✅ If vector store down → core chat still responds with reduced features
- ✅ If external LLM down → fallback to local model
- ✅ If Redis down → degrade gracefully (no session buffer)

---

## 6. Go-Live Checklist (Chat-Specific)

**Pre-Production:**
- [ ] `websocket_gateway` auth validated
- [ ] `chat_hub` routes all types correctly
- [ ] `chat_orchestrator` is the single brain—no parallel orchestration paths
- [ ] `tool_integration_service` and `code_execution_service` locked behind RBAC
- [ ] `production_memory` connected to real Postgres/vector stack
- [ ] `conversation_search_service` returns relevant history
- [ ] `stream_processor` stable under load
- [ ] Metrics visible and sane for 24–48h in staging
- [ ] All logs include `correlation_id` and no sensitive secrets
- [ ] All modules follow contracts in CHAT_FLOW_CONTRACT.md
- [ ] Integration with capsule system tested

**Production:**
- [ ] Prometheus dashboards configured
- [ ] Alerting rules set up
- [ ] Error tracking integrated (Sentry, etc.)
- [ ] Rate limits configured
- [ ] Backup/restore procedures tested
- [ ] Disaster recovery plan documented
- [ ] Performance benchmarks established

---

## 7. Integration with Capsule System

**Capsule-Tool Bridge:**

```python
# tool_integration_service.py

from ai_karen_engine.capsules import get_capsule_orchestrator

async def invoke_capsule_as_tool(
    capsule_id: str,
    request: Dict[str, Any],
    user_ctx: Dict[str, Any],
    correlation_id: str
) -> ToolResult:
    """
    Invoke capsule through tool interface.

    Links chat system to capsule skill injection framework.
    """
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
```

**Available Capsule Tools:**
- `capsule.web_researcher` - Web research
- `capsule.semantic_retriever` - Advanced memory search
- `capsule.sentiment_forecaster` - Sentiment prediction
- `capsule.self_reflector` - Metacognitive analysis
- `capsule.story_generator` - Creative content
- `capsule.task_executor` - Autonomous execution
- (See [Capsule Skill Integration Guide](/docs/capsules/SKILL_INTEGRATION_GUIDE.md))

---

## 8. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **WebSocket Connection** | < 100ms | Time to establish + auth |
| **Message Routing** | < 50ms | Gateway → Hub → Orchestrator |
| **Context Integration** | < 200ms | Memory retrieval + assembly |
| **Orchestration** | < 500ms | Model selection + execution (non-streaming) |
| **Streaming First Token** | < 1s | Time to first streamed token |
| **Memory Write** | < 100ms | Persist conversation turn |
| **Search** | < 300ms | Full conversation search |

**Load Targets:**
- 100 concurrent WebSocket connections
- 1000 messages/minute
- 10 tool calls/second
- 95th percentile < 2s end-to-end

---

## 9. Security Requirements

### Input Validation
- ✅ All user input sanitized (XSS, SQL injection, shell injection)
- ✅ Message size limits enforced
- ✅ File upload limits enforced
- ✅ Content policy checks

### Authentication
- ✅ JWT validation on every WebSocket connection
- ✅ Token expiration enforced
- ✅ Session management (Redis)
- ✅ Refresh token flow

### Authorization
- ✅ RBAC roles checked for:
  * Tool access
  * Code execution
  * Configuration changes
  * Mode switching
- ✅ Tenant isolation enforced

### Audit
- ✅ All tool calls logged
- ✅ All configuration changes logged
- ✅ All errors logged with correlation ID
- ✅ HMAC-SHA512 signed audit trails (link to capsule security)

---

## 10. Disaster Recovery

### Data Backup
- ✅ Postgres: Daily backups, 30-day retention
- ✅ Milvus: Weekly backups, 90-day retention
- ✅ Redis: Point-in-time recovery

### Failover
- ✅ Multi-region deployment (optional)
- ✅ Read replicas for Postgres
- ✅ LLM provider fallbacks

### Monitoring
- ✅ Uptime checks (every 60s)
- ✅ Error rate alerts (> 5% triggers)
- ✅ Latency alerts (p95 > 5s triggers)
- ✅ Memory usage alerts (> 80% triggers)

---

## 📞 Support

**Architecture:** Zeus - Chief Architect
**Documentation:** `/docs/chat/`
**Contracts:** [CHAT_FLOW_CONTRACT.md](CHAT_FLOW_CONTRACT.md)
**Code:** `/src/ai_karen_engine/chat/`
**Related:** [Capsule System](/docs/capsules/)

---

**Dev Sheet Version:** 1.0.0
**Status:** ✅ Production Specification
**Last Updated:** 2025-11-08
