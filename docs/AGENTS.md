# **AI-Karen Agent Architecture & Documentation**

*Production-Ready Multi-Agent Orchestration System*

**Last Updated**: November 12, 2025
**Status**: Production v1.0

---

## 🎯 **Mission: Enterprise-Grade AI Orchestration**

AI-Karen is a production-ready, modular AI platform with sophisticated multi-agent orchestration, unified memory systems, and enterprise-grade observability. Every component is designed for scalability, reliability, and maintainability.

---

## 1. **Core Architecture Principle**

* **All core runtime logic, services, and integrations live under `src/ai_karen_engine/` as independent, importable modules.**
* **UI launchers live under `/ui_launchers/` (web_ui, desktop_ui, admin_ui)—strictly separated from backend.**
* **Production-ready with 167 service modules, 75 API endpoints, and comprehensive observability.**
* **All imports are absolute: `from ai_karen_engine.<module> import ...`**

---

## 2. **Current Production Architecture**

### Core Orchestrators (5 Major Systems)

| Orchestrator | File | Purpose | Key Features |
| ------------ | ---- | ------- | ------------ |
| **LLM Orchestrator** | `llm_orchestrator.py` (1,700+ lines) | Zero-trust LLM routing with cryptographic validation | HMAC-SHA256 signing, hardware isolation, circuit breakers, 8-concurrent limit |
| **Chat Orchestrator** | `chat/chat_orchestrator.py` (2,300+ lines) | Message processing with NLP integration | spaCy + DistilBERT, retry logic, memory processor, tool integration |
| **CORTEX Dispatch** | `core/cortex/dispatch.py` | Central intent/command dispatcher | Intent resolution, memory recall (max 10), RBAC validation |
| **LLM Router** | `integrations/llm_router.py` (3,200+ lines) | Policy-based intelligent routing | Privacy-aware routing, 4-level fallback, performance profiling |
| **Agent Orchestrator** | `agents/agent_orchestrator.py` | Multi-agent orchestration | Planner, execution pipeline, audit logger |

### Agent Components

| Component Type | Description | Location | Status |
| -------------- | ----------- | -------- | ------ |
| **Core Agents** | Orchestration, planning, execution, audit | `src/ai_karen_engine/agents/` | ✅ Production |
| **Memory Systems** | 4 unified systems (Original, RecallManager, NeuroVault, NeuroRecall) | `src/ai_karen_engine/core/memory/` | ✅ Phase 1 Complete |
| **Reasoning Engines** | Soft reasoning, causal, graph-based | `src/ai_karen_engine/core/reasoning/` | ✅ Production |
| **Chat Services** | 20+ chat-related services | `src/ai_karen_engine/chat/` | ✅ Production |
| **LLM Integrations** | 7 providers with health monitoring | `src/ai_karen_engine/integrations/` | ✅ Production |
| **Database Layer** | Multi-tenant support (PostgreSQL, Redis, Milvus, DuckDB) | `src/ai_karen_engine/database/` | ✅ Production |

---

## 3. **Production Directory Structure (Current)**

```
AI-Karen/
├── src/ai_karen_engine/
│   ├── agents/              # Agent orchestration (4 core agents)
│   ├── api_routes/          # 75 REST API endpoints
│   ├── chat/                # Chat orchestration & streaming (20 modules)
│   ├── clients/             # External service integrations
│   ├── core/                # Core infrastructure (50+ modules)
│   │   ├── cortex/          # CORTEX dispatch & intent routing
│   │   ├── memory/          # Unified memory system (Phase 1)
│   │   ├── neuro_vault/     # Tri-partite neural memory
│   │   ├── neuro_recall/    # Hierarchical recall agents
│   │   ├── reasoning/       # Soft, causal, graph-based reasoning
│   │   ├── services/        # Service infrastructure & DI
│   │   ├── logging/         # Structured logging
│   │   └── gateway/         # FastAPI gateway
│   ├── database/            # Multi-tenant data layer (8 modules)
│   ├── integrations/        # LLM providers & health (40+ modules)
│   ├── services/            # Business logic (167 modules)
│   ├── monitoring/          # Observability & metrics (5 modules)
│   ├── plugins/             # Plugin execution & management
│   ├── extensions/          # Extension system & marketplace
│   ├── models/              # Data models & schemas
│   ├── tools/               # Tool definitions
│   └── config/              # Configuration management
├── ui_launchers/
│   ├── KAREN-Theme-Default/ # Next.js web UI (production)
│   ├── desktop_ui/          # Desktop application
│   └── admin_ui/            # Admin interface
├── docs/                    # Comprehensive documentation
│   ├── AI_KAREN_ARCHITECTURE_OVERVIEW.md  # Full technical reference
│   ├── QUICK_REFERENCE.md                 # Quick lookup guide
│   └── AGENTS.md                          # This file
├── .env.production          # Production configuration
└── docker-compose.yml       # Container orchestration
```

---

## 4. **Agent Orchestration Patterns**

### Multi-Agent Workflow

```
User Request
    ↓
[CORTEX Dispatch] → Intent resolution
    ↓
[Memory Recall] → Context retrieval (max 10 items)
    ↓
[Agent Orchestrator]
    ├→ [Planner Agent] → Strategic planning
    ├→ [Execution Agent] → Task execution
    └→ [Audit Agent] → Logging & compliance
    ↓
[Chat Orchestrator] → Message processing
    ├→ [NLP Services] → spaCy + DistilBERT
    ├→ [Tool Integration] → Execute tools
    └→ [LLM Router] → Select optimal model
        ↓
    [LLM Orchestrator] → Zero-trust execution
        ↓
    [Memory Update] → Store results
        ↓
    Response to User
```

### Agent Communication Patterns

**1. Direct Invocation** - Synchronous agent-to-agent calls
**2. Event Bus** - Asynchronous event-driven communication
**3. Memory Sharing** - Shared memory context across agents
**4. Tool Integration** - Agents can invoke tools via tool service

---

## 5. **Memory Architecture (4 Unified Systems)**

### Current Status: Phase 1 Complete

| System | Purpose | Location | Integration |
| ------ | ------- | -------- | ----------- |
| **Original Memory** | AG-UI manager, session buffers | `core/memory/manager.py` | ✅ Unified |
| **RecallManager** | Specialized retrieval patterns | `core/recalls/` | ✅ Unified |
| **NeuroVault** | Tri-partite neural memory | `core/neuro_vault/` | ✅ Unified |
| **NeuroRecall** | Hierarchical agent-based recall | `core/neuro_recall/` | ✅ Unified |

### Unified Types

```python
@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: Optional[List[float]]
    memory_type: MemoryType  # Episodic/Semantic/Procedural
    namespace: MemoryNamespace  # Short/Long/Persistent/Ephemeral
    timestamp: datetime
    importance: float  # 1-10
    confidence: float  # 0-1
```

### Storage Backends

- **PostgreSQL**: Conversation memory, JSON/vector support
- **Redis**: Cache, session state, recent context (3600s TTL)
- **Milvus**: Vector search, semantic similarity
- **DuckDB**: Analytics, historical patterns

---

## 6. **LLM Provider Integration (7 Providers)**

| Provider | Type | Status | Features |
| -------- | ---- | ------ | -------- |
| **LlamaCppProvider** | Local | ✅ Active | CPU/GPU, streaming, privacy-first |
| **OpenAIProvider** | Cloud | ✅ Active | GPT-4, embeddings, vision |
| **GeminiProvider** | Cloud | ✅ Active | Multimodal, streaming |
| **DeepseekProvider** | Cloud | ✅ Active | Reasoning models |
| **HuggingFaceProvider** | Cloud | ✅ Active | Text gen, embeddings |
| **CopilotKitProvider** | Cloud | ✅ Active | CopilotKit integration |
| **FallbackProvider** | Meta | ✅ Active | Error recovery, degradation |

### Fallback Strategy (4 Levels)

1. **User preference** → Preferred model/provider
2. **System defaults** → Configured fallback providers
3. **Local models** → llama.cpp local execution
4. **Degraded mode** → Minimal response capability

---

## 7. **Observability & Monitoring**

### Structured Logging

- **Format**: JSON with correlation tracking
- **Categories**: API, Database, AI, System, Business
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Prometheus Metrics

- `kari_model_operations_total` - Operation counts by type/status
- `kari_model_operation_duration_seconds` - Timing histograms
- `kari_model_storage_usage_bytes` - Storage gauges

### Health Monitoring

- Provider availability checks (30s intervals)
- Circuit breaker pattern
- Response latency tracking (p95)
- Error rate monitoring

---

## 8. **Production Configuration**

### Key Environment Variables

```env
ENVIRONMENT=production
ENABLE_STREAMING=true
ENABLE_FALLBACK=true
ENABLE_MEMORY=true
MAX_MESSAGE_LENGTH=10000
MAX_TOKENS_DEFAULT=4096
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
ENABLE_STRUCTURED_LOGGING=true
ENABLE_PROMETHEUS=true
CIRCUIT_BREAKER_ENABLED=true
GRACEFUL_DEGRADATION_ENABLED=true
```

---

## 9. **Module Development Guidelines**

### Import Rules

* **Always**: `from ai_karen_engine.<module> import ...`
* **Never**: Relative imports or sys.path hacks

### Service Registration

```python
from ai_karen_engine.core.services import ServiceRegistry

registry = ServiceRegistry()
registry.register("my_service", MyService())
```

### Example Agent Import

```python
from ai_karen_engine.agents.agent_orchestrator import AgentOrchestrator
from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
from ai_karen_engine.integrations.llm_router import LLMRouter
from ai_karen_engine.core.memory.unified_memory_service import UnifiedMemoryService
```

---

## 10. **Agent Development Best Practices**

### Security

- Zero-trust model validation with HMAC-SHA256
- RBAC enforcement for plugin execution
- Credential redaction in logs
- Hardware isolation via CPU affinity

### Resilience

- Retry logic with exponential backoff (max 3 attempts)
- Circuit breaker pattern (threshold: 5 failures)
- Graceful degradation (4 levels)
- Timeout management (60s default)

### Performance

- Connection pooling (20 connections, 30 overflow)
- Query caching with Redis
- Async/await architecture
- Max 8-50 concurrent requests (configurable)

---

## 11. **Production Readiness**

### ✅ Production-Ready

- Chat runtime API with streaming
- Memory architecture (Phase 1)
- Database multi-tenant support
- LLM provider fallback
- Observability infrastructure

### ⚠️ In Progress

- Frontend error handling (77% complete)
- Plugin system (needs mock API replacement)
- Service error logging (67% complete)

---

## 12. **Documentation & References**

### Key Documentation Files

- **AI_KAREN_ARCHITECTURE_OVERVIEW.md** - Complete technical reference (1,031 lines)
- **QUICK_REFERENCE.md** - Quick lookup guide (435 lines)
- **AGENTS.md** - This file (agent architecture)

### Statistics

- **167 service modules** across 10 categories
- **75 API endpoints** organized by function
- **5 core orchestrators** for intelligent routing
- **4 memory systems** being unified
- **7 LLM providers** with health monitoring
- **4 database backends** for multi-tenant support

---

## 13. **License**

All modules respect AI-Karen's dual license: **MPL 2.0** + commercial.
