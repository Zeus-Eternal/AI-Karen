# AI-Karen Engine - Quick Reference Guide

## System at a Glance

| Component | Count | Status |
|-----------|-------|--------|
| **Service Modules** | 167 | Production |
| **API Endpoints** | 75 | Production |
| **Core Orchestrators** | 5 | Production |
| **Memory Systems** | 4 | Unifying (Phase 1) |
| **LLM Providers** | 7 | All Active |
| **Database Backends** | 4 | All Active |
| **Advanced Reasoning** | 5 types | Production |

---

## 5 Core Orchestrators

### 1. LLM Orchestrator
- **File**: `llm_orchestrator.py` (1,700+ lines)
- **Purpose**: Zero-trust LLM routing with cryptographic validation
- **Key**: Hardware-isolated execution, circuit breakers, 8-concurrent limit
- **Timeout**: 60 seconds
- **Uses**: HMAC-SHA256 model signing, CPU affinity

### 2. Chat Orchestrator
- **File**: `chat/chat_orchestrator.py` (2,300+ lines)
- **Purpose**: Message processing with NLP integration
- **Components**: spaCy, DistilBERT, memory processor, tool integration
- **Retry**: Max 3 attempts, exponential backoff to 60s
- **Handles**: Files, multimedia, code execution, streaming

### 3. CORTEX Dispatch
- **File**: `core/cortex/dispatch.py`
- **Purpose**: Central intent/command dispatcher
- **Flow**: Intent → Memory → Plugin/Predictor → Action → Memory Write
- **RBAC**: Validates plugin permissions (Phase 2)
- **Memory**: Recalls max 10 items per query

### 4. LLM Router
- **File**: `integrations/llm_router.py` (3,200+ lines)
- **Purpose**: Policy-based intelligent routing
- **Strategy**: Privacy → llama.cpp, Interactive → vLLM, Flexible → Transformers
- **Fallback**: User pref → defaults → local → degraded
- **Profiling**: Tracks latency, cost, availability

### 5. Agent Orchestrator
- **File**: `agents/agent_orchestrator.py`
- **Purpose**: Multi-agent orchestration
- **Components**: Planner, execution pipeline, audit logger
- **Mode**: Sequential or parallel execution

---

## Memory Architecture (4 Systems Unifying)

### Current Status: Phase 1 - Foundation
- ✅ Unified types defined
- ✅ Unified protocols defined
- ✅ Backward compatibility maintained
- 🔄 Phase 2-4: Migration in progress
- 📋 Phase 5-6: New features (consolidation, integration)

### Memory Types
```
MemoryType: Episodic | Semantic | Procedural
MemoryNamespace: ShortTerm | LongTerm | Persistent | Ephemeral
MemoryStatus: Active | Consolidating | Archived | Expired
MemoryPriority: Critical | High | Medium | Low | Minimal
```

### 4 Systems Being Unified
1. **Original Memory** - manager.py, AG-UI integration
2. **RecallManager** - recalls/, specialized retrieval
3. **NeuroVault** - neuro_vault/, tri-partite neural memory
4. **NeuroRecall** - neuro_recall/, hierarchical agents

### Storage Backends
- **PostgreSQL**: Conversation memory, JSON/vector support
- **Redis**: Cache, session state, recent context
- **Milvus**: Vector search, embeddings, semantic lookup
- **DuckDB**: Analytics, historical patterns, aggregations

---

## Chat Runtime API (Recently Refactored)

### Endpoints
```
POST /api/chat/runtime          # Non-streaming
POST /api/chat/runtime/stream   # Streaming (SSE)
```

### Configuration
```
MAX_MESSAGE_LENGTH = 10,000 characters
MAX_TOKENS_DEFAULT = 4,096
STREAM_TIMEOUT = 30 seconds
RATE_LIMIT = 10 requests per 60 seconds
FALLBACK_ENABLED = true
```

### Recent Improvements (Nov 12, 2025)
- ✅ Integrated StructuredLogger
- ✅ Added MetricsService
- ✅ Production observability wiring
- ✅ Enhanced error handling
- ✅ Streaming with timeout management
- ✅ Rate limiting integration
- ✅ Tool service integration

---

## LLM Providers (7 Total)

| Provider | Type | Features |
|----------|------|----------|
| LlamaCppProvider | Local | CPU/GPU, streaming, privacy |
| OpenAIProvider | Cloud | GPT-4, embeddings, vision |
| GeminiProvider | Cloud | Multimodal, streaming |
| DeepseekProvider | Cloud | Reasoning models |
| HuggingFaceProvider | Cloud | Text gen, embeddings |
| CopilotKitProvider | Cloud | CopilotKit integration |
| FallbackProvider | Meta | Error recovery |

### Fallback Triggers
- Provider unavailable
- Latency > 1.2s (p95)
- Error rate threshold
- Rate limiting (429)

---

## 10 Service Categories (167 Total Modules)

| Category | Count | Examples |
|----------|-------|----------|
| Memory Services | 10+ | unified, integrated, optimized, enhanced |
| Model Management | 15+ | discovery, library, validation, router |
| Database Services | 10+ | connection, health, consistency, cache |
| NLP Services | 3 | service manager, spaCy, DistilBERT |
| Cache & Performance | 10+ | smart cache, production cache, metrics |
| Error Handling | 10+ | aggregation, recovery, response |
| Analytics & Audit | 15+ | analytics service, audit logging |
| Integrations | 20+ | providers, compatibility, webhooks |
| Utilities | 60+ | conversion, transformation, helpers |
| Specialized | 12+ | persona, tenant, privacy, training |

---

## API Routes by Category (75 Total)

| Category | Count | Key Endpoints |
|----------|-------|---|
| Chat & Conversation | 3 | chat_runtime, conversation, websocket |
| AI & Model | 6 | ai, ai_orchestrator, llm, intelligent_model |
| Memory & Knowledge | 3 | memory, knowledge, reasoning |
| System & Admin | 4 | health, system, admin, degraded_mode |
| Advanced | 40+ | plugin, extensions, tools, analytics, performance |
| Training & Tools | 15+ | training, basic_training, advanced_training |
| Utilities | 4 | events, hooks, profiles, settings |

---

## Advanced Features

### Soft Reasoning Engine
- **Research**: "Soft Reasoning: Navigating Solution Spaces in LLMs"
- **Components**: Perturbation, optimization, verification
- **Benefits**: Better accuracy with 6% token usage
- **Methods**: Gaussian, directional, adaptive, diverse, hybrid

### Other Reasoning Types
- **Causal**: Pearl's hierarchy (observational, interventional, counterfactual)
- **Graph**: CapsuleGraph for reasoning paths
- **Retrieval**: Vector store adapters
- **Synthesis**: ICE integration

### Graceful Degradation (4 Levels)
1. Level 1: Full functionality
2. Level 2: Limited providers
3. Level 3: Local models only
4. Level 4: Minimal responses

---

## Database Architecture

### Multi-Tenant Design
- **Isolation**: Schema/row-level separation
- **Pooling**: 20 connections, 30 overflow
- **Recycling**: 3600 second pool recycle
- **Timeout**: 30 second connection timeout

### Core Managers
- **Client**: Connection management
- **Memory Manager**: Store/retrieve/search memory
- **Conversation Manager**: Lifecycle, messages, export
- **Tenant Manager**: Provisioning, resources, isolation
- **Migration Manager**: Schema versioning, rollback

---

## Observability & Monitoring

### Metrics
- `kari_model_operations_total`: Operation counts
- `kari_model_operation_duration_seconds`: Timing
- `kari_model_download_bytes_total`: Volume
- `kari_model_storage_usage_bytes`: Storage

### Structured Logging
- **Format**: JSON
- **Categories**: API, Database, AI, System, Business
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Features**: Correlation tracking, metadata support

### Health Checks
- Provider availability
- Response latency
- Error rates
- Success rate
- Model-specific health

---

## Production Configuration

### Environment Variables (Key)
```env
ENVIRONMENT=production
ENABLE_STREAMING=true
ENABLE_FALLBACK=true
ENABLE_MEMORY=true
MAX_MESSAGE_LENGTH=10000
MAX_TOKENS_DEFAULT=4096
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
MAX_CONCURRENT_REQUESTS=50
ENABLE_STRUCTURED_LOGGING=true
ENABLE_PROMETHEUS=true
CIRCUIT_BREAKER_ENABLED=true
GRACEFUL_DEGRADATION_ENABLED=true
```

### Feature Flags
- Streaming support
- Fallback mechanisms
- Memory integration
- Metrics collection
- Structured logging
- Prometheus export
- Circuit breaking
- Graceful degradation

---

## Production Readiness Status

### ✅ Production-Ready
- Chat runtime API
- Memory architecture (Phase 1)
- Database multi-tenant support
- LLM provider fallback
- Observability infrastructure
- Security (zero-trust, RBAC, audit logging)

### ⚠️ In Progress / Partial
- Frontend error handling (77% complete)
- Plugin system (needs mock API replacement)
- Service error logging (67% complete)
- Advanced reasoning integration

### 📋 Planned / Future
- Memory consolidation (Phase 5)
- Cognitive integration (Phase 6)
- Complete service catalog documentation
- Extended API reference

---

## Key Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Max Concurrent | 8-50 | Configurable per component |
| Request Timeout | 60s | LLM; 30s streaming |
| Retry Attempts | 3 | Max, exponential backoff |
| Fallback Timeout | 5s | Provider fallback |
| Cache TTL | 3600s | Typical session/data |
| Rate Limit | 10/60s | Per user/session |
| Memory Recall | 10 items | Per query max |
| Storage Backends | 4 | All active |

---

## Recent Changes (Nov 12, 2025)

### Chat Runtime Refactoring
- ✅ Production observability wiring
- ✅ StructuredLogger integration
- ✅ MetricsService integration
- ✅ Enhanced error handling
- ✅ Streaming support
- ✅ Rate limiting
- ✅ Tool service integration

### Documentation
- ✅ Chat Runtime Frontend Integration Guide
- ✅ Streaming API documentation
- ✅ Configuration management guide
- ✅ Error handling patterns

### Configuration
- ✅ .env.production file
- ✅ Feature flags
- ✅ Memory backends config
- ✅ Observability settings

---

## Critical Files Reference

### Core Orchestrators
- `llm_orchestrator.py` - LLM routing (1,700 lines)
- `chat/chat_orchestrator.py` - Chat processing (2,300 lines)
- `core/cortex/dispatch.py` - Intent dispatch
- `integrations/llm_router.py` - Intelligent routing (3,200 lines)
- `agents/agent_orchestrator.py` - Agent orchestration

### Memory Systems
- `core/memory/types.py` - Unified types
- `core/memory/protocols.py` - Unified protocols
- `core/memory/manager.py` - Original memory
- `core/neuro_vault/neuro_vault.py` - Tri-partite memory
- `services/unified_memory_service.py` - Unified interface

### Chat & Streaming
- `api_routes/chat_runtime.py` - Chat API (production)
- `chat/websocket_gateway.py` - WebSocket streaming
- `chat/memory_processor.py` - Memory integration (2,000 lines)
- `chat/context_integrator.py` - Context assembly

### Database & Storage
- `database/client.py` - Multi-tenant client
- `database/memory_manager.py` - Memory storage
- `database/conversation_manager.py` - Conversation lifecycle
- `database/tenant_manager.py` - Tenant management

### Integrations & Health
- `integrations/llm_registry.py` - Provider registration
- `integrations/health_monitor.py` - Health monitoring
- `integrations/fallback_manager.py` - Fallback strategies
- `integrations/error_recovery.py` - Error recovery

### Observability
- `services/structured_logging_service.py` - Structured logs
- `services/metrics_service.py` - Prometheus metrics
- `monitoring/model_orchestrator_metrics.py` - Model metrics
- `monitoring/model_orchestrator_tracing.py` - Tracing

---

## Useful Commands

### View Architecture
```bash
# See full structure
find src/ai_karen_engine -maxdepth 1 -type d | sort

# Count files by category
find src/ai_karen_engine/services -type f -name "*.py" | wc -l  # 167
find src/ai_karen_engine/api_routes -type f -name "*.py" | wc -l  # 75

# Check recent changes
git log --all --format="%h %ai %s" --name-only | head -50
```

### Testing
```bash
# Run core tests
pytest tests/core/

# Run specific component tests
pytest tests/unit/services/test_memory_service.py

# Run integration tests
pytest tests/integration/
```

### Documentation
```bash
# View architecture overview
cat docs/AI_KAREN_ARCHITECTURE_OVERVIEW.md

# View chat runtime integration
cat docs/CHAT_RUNTIME_FRONTEND_INTEGRATION.md

# View memory system
cat src/ai_karen_engine/core/memory/README.md

# View reasoning system
cat src/ai_karen_engine/core/reasoning/README.md
```

---

## Next Steps for Documentation

1. **Create Service Catalog** - Detail all 167 services
2. **Write API Reference** - OpenAPI/Swagger for 75 endpoints
3. **Add Deployment Guide** - Production deployment steps
4. **Build Monitoring Guide** - Prometheus, logging, alerts
5. **Document Agents** - 4 core agent types
6. **Plugin Development** - Plugin creation guide
7. **Extension Development** - Marketplace integration
8. **Integration Guides** - External system integrations

---

## Key Takeaways

The AI-Karen Engine is a **mature, production-grade platform** featuring:

- **Sophisticated orchestration** with 5 major orchestrators
- **Unified memory** consolidating 4 separate systems
- **Advanced reasoning** (soft, causal, graph-based)
- **Comprehensive observability** (metrics, logging, tracing)
- **Resilient architecture** (fallbacks, degradation, recovery)
- **Enterprise security** (zero-trust, RBAC, audit trails)
- **Multi-tenant support** with 4 database backends
- **7 LLM providers** with health monitoring

**Primary focus**: Complete frontend hardening and service logging before full production launch.

