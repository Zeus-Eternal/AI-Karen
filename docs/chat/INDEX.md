# Kari Chat System Documentation Index

**Production-Grade Conversational Runtime**

---

## 📚 Documentation Overview

This directory contains production specifications for Kari AI's chat system — the real-time conversational runtime that orchestrates message flow, context integration, tool execution, and memory persistence.

---

## 🎯 Quick Navigation

**New to chat system?** Start here:

1. **[Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md)** - Architecture and module responsibilities
2. **[Flow Contract](CHAT_FLOW_CONTRACT.md)** - Function signatures and payload schemas

**Ready to integrate?** Check:

3. **[Capsule Integration Guide](/docs/capsules/SKILL_INTEGRATION_GUIDE.md)** - Link chat to capsule skills

---

## 📖 Documentation Files

### 1. Chat System Dev Sheet
**Location:** `CHAT_SYSTEM_DEV_SHEET.md`
**Purpose:** Production architecture specification
**Length:** ~4,500 words

**Contains:**
- Core execution flow (9-step pipeline)
- Module responsibilities (18 modules)
- Hard contracts for each component
- Cross-cutting requirements (auth, observability, errors)
- Memory and context rules
- Testing and CI requirements
- Go-live checklist
- Capsule system integration
- Performance targets
- Security requirements
- Disaster recovery

**Audience:** Team leads, architects, all developers

---

### 2. Chat Flow Contract
**Location:** `CHAT_FLOW_CONTRACT.md`
**Purpose:** Exact function signatures and payload schemas
**Length:** ~6,000 words

**Contains:**
- Function signatures for all 13+ modules
- Pydantic model definitions
- JSON payload schemas
- Error envelope contracts
- Streaming contracts
- Metrics contracts
- Testing contracts
- Go-live verification checklist

**Audience:** Implementation developers, QA engineers

---

## 🏗️ System Architecture

### Core Execution Pipeline

```
WebSocket → Hub → Instruction Processor →
Context Integrator + Memory →
Orchestrator + Factory →
Tools + Code + Files + Multimedia →
Stream Processor →
Summarizer + Conversation Manager →
Persist + Index
```

**Total Modules:** 18
**Integration Points:** Capsule system, NeuroVault, LLM providers

---

## 📦 Module Reference

| Module | Role | Contract |
|--------|------|----------|
| `websocket_gateway.py` | Real-time ingress/egress | [Contract](CHAT_FLOW_CONTRACT.md#module-1-websocket_gatewaypy) |
| `chat_hub.py` | Central router | [Contract](CHAT_FLOW_CONTRACT.md#module-2-chat_hubpy) |
| `instruction_processor.py` | Command brain | [Contract](CHAT_FLOW_CONTRACT.md#module-3-instruction_processorpy) |
| `conversation_models.py` | Shared contracts | [Contract](CHAT_FLOW_CONTRACT.md#module-4-conversation_modelspy) |
| `context_integrator.py` | Context assembly | [Contract](CHAT_FLOW_CONTRACT.md#module-5-context_integratorpy) |
| `memory_processor.py` | Memory glue | [Contract](CHAT_FLOW_CONTRACT.md#module-6-memory_processorpy) |
| `production_memory.py` | Memory facade | [Contract](CHAT_FLOW_CONTRACT.md#module-7-production_memorypy) |
| `chat_orchestrator.py` | Brain | [Contract](CHAT_FLOW_CONTRACT.md#module-8-chat_orchestratorpy) |
| `factory.py` | Model selection | [Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md#factorypy) |
| `tool_integration_service.py` | Tool gateway | [Contract](CHAT_FLOW_CONTRACT.md#module-9-tool_integration_servicepy) |
| `code_execution_service.py` | Sandboxed execution | [Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md#code_execution_servicepy) |
| `file_attachment_service.py` | File handling | [Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md#file_attachment_servicepy) |
| `multimedia_service.py` | Media handling | [Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md#multimedia_servicepy) |
| `stream_processor.py` | Streaming output | [Contract](CHAT_FLOW_CONTRACT.md#module-10-stream_processorpy) |
| `summarizer.py` | Summarization | [Contract](CHAT_FLOW_CONTRACT.md#module-11-summarizerpy) |
| `enhanced_conversation_manager.py` | State manager | [Contract](CHAT_FLOW_CONTRACT.md#module-12-enhanced_conversation_managerpy) |
| `conversation_search_service.py` | Search | [Contract](CHAT_FLOW_CONTRACT.md#module-13-conversation_search_servicepy) |
| `dependencies.py` | Wiring/DI | [Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md#dependenciespy) |

---

## 🔗 Integration with Capsule System

The chat system integrates with the capsule skill injection framework through `tool_integration_service.py`:

**Capsule Tools Available:**
- `capsule.web_researcher` - Web research
- `capsule.semantic_retriever` - Advanced memory search
- `capsule.sentiment_forecaster` - Sentiment prediction
- `capsule.self_reflector` - Metacognitive analysis
- `capsule.story_generator` - Creative content
- `capsule.task_executor` - Autonomous execution

**Integration Pattern:**
```python
from ai_karen_engine.capsules import get_capsule_orchestrator

async def invoke_capsule_as_tool(capsule_id, request, user_ctx, correlation_id):
    orchestrator = get_capsule_orchestrator()
    result = await orchestrator.execute_capsule(...)
    return ToolResult(...)
```

**Documentation:**
- [Capsule System Overview](/docs/capsules/INDEX.md)
- [Skill Integration Guide](/docs/capsules/SKILL_INTEGRATION_GUIDE.md)
- [Capsule-Tool Bridge](CHAT_FLOW_CONTRACT.md#integration-with-capsule-system)

---

## 🔒 Security

**8-Layer Zero-Trust:**
1. JWT validation (websocket_gateway)
2. RBAC enforcement (all services)
3. Input sanitization (all entry points)
4. Tool whitelisting (tool_integration_service)
5. Rate limiting (websocket_gateway, tools)
6. Audit logging (all operations)
7. Sandboxing (code_execution_service)
8. Circuit breaking (orchestrator)

**RBAC Roles:**
```
chat.user              # Basic access
chat.tools.search      # Search tools
chat.tools.code        # Code execution
chat.mode.switch       # Mode switching
chat.config.edit       # Configuration
chat.persona.change    # Persona changes
chat.admin             # Admin features
```

**Security Documentation:**
- [Dev Sheet Security](CHAT_SYSTEM_DEV_SHEET.md#31-auth--rbac)
- [Error Handling](CHAT_FLOW_CONTRACT.md#error-envelope-contract)

---

## 📊 Observability

**Prometheus Metrics:**
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

**Logging:**
- Correlation ID tracking (all requests)
- Structured JSON logs
- Key events logged (intent, recall, tools, errors)
- No sensitive data

**Documentation:**
- [Observability Requirements](CHAT_SYSTEM_DEV_SHEET.md#32-observability)
- [Metrics Contract](CHAT_FLOW_CONTRACT.md#metrics-contract)

---

## 🧪 Testing

**Required Test Categories:**

1. **Flow Tests** - End-to-end message flow
2. **RBAC Tests** - Authorization enforcement
3. **Memory Tests** - Context integration and persistence
4. **Regression Tests** - No architectural violations
5. **Resilience Tests** - Graceful degradation

**Documentation:**
- [Testing Requirements](CHAT_SYSTEM_DEV_SHEET.md#5-testing--ci-requirements)
- [Testing Contract](CHAT_FLOW_CONTRACT.md#testing-contract)

---

## ✅ Go-Live Checklist

**Pre-Production:**
- [ ] WebSocket auth validated
- [ ] Chat hub routing verified
- [ ] Orchestrator as single brain
- [ ] RBAC enforcement on tools/code
- [ ] Production memory connected
- [ ] Search service working
- [ ] Streaming stable under load
- [ ] Metrics emitting correctly
- [ ] Logs include correlation IDs
- [ ] Contracts verified

**Production:**
- [ ] Prometheus dashboards configured
- [ ] Alerting rules active
- [ ] Error tracking integrated
- [ ] Rate limits configured
- [ ] Backup/restore tested
- [ ] Disaster recovery documented
- [ ] Performance benchmarks met

**Full Checklist:** [Dev Sheet Go-Live](CHAT_SYSTEM_DEV_SHEET.md#6-go-live-checklist-chat-specific)

---

## 🎯 Performance Targets

| Metric | Target |
|--------|--------|
| WebSocket Connection | < 100ms |
| Message Routing | < 50ms |
| Context Integration | < 200ms |
| Orchestration | < 500ms |
| Streaming First Token | < 1s |
| Memory Write | < 100ms |
| Search | < 300ms |

**Load Targets:**
- 100 concurrent connections
- 1000 messages/minute
- 10 tool calls/second
- p95 latency < 2s

**Full Targets:** [Dev Sheet Performance](CHAT_SYSTEM_DEV_SHEET.md#8-performance-targets)

---

## 🎓 Learning Path

### For Chat Developers

1. Read **[Dev Sheet](CHAT_SYSTEM_DEV_SHEET.md)** (2 hours)
2. Review **[Flow Contract](CHAT_FLOW_CONTRACT.md)** (1 hour)
3. Study your module's contract (30 min)
4. Review integration tests (1 hour)
5. Implement and test (varies)

**Total time:** ~4.5 hours to productive development

### For Integration Developers

1. Review **[Capsule Integration](CHAT_FLOW_CONTRACT.md#integration-with-capsule-system)** (30 min)
2. Read **[Skill Integration Guide](/docs/capsules/SKILL_INTEGRATION_GUIDE.md)** (1 hour)
3. Study tool invocation pattern (30 min)
4. Implement capsule-tool bridge (2 hours)

**Total time:** ~4 hours to capsule integration

---

## 📞 Support & Resources

**Code Location:**
- `/src/ai_karen_engine/chat/`

**Documentation:**
- `/docs/chat/` (this directory)

**Related Systems:**
- Capsule Framework: `/docs/capsules/`
- NeuroVault: `/docs/memory/`
- LLM Integration: `/docs/integrations/`

**Support:**
- Architecture: Zeus - Chief Architect
- GitHub Issues: [AI-Karen/issues](https://github.com/Zeus-Eternal/AI-Karen/issues)

---

## 🏆 Summary

The Kari Chat System is a **production-grade conversational runtime** with:

- ✅ 18 specialized modules with clear contracts
- ✅ Zero-trust security (8 layers)
- ✅ Full observability (metrics + logging + tracing)
- ✅ Capsule system integration (13 skill types)
- ✅ Performance targets defined
- ✅ Disaster recovery plans
- ✅ Comprehensive test requirements

**Key Features:**
- Real-time WebSocket communication
- Context-aware responses (memory + search)
- Tool/capsule integration
- Streaming output
- Multi-model support
- RBAC enforcement
- Graceful degradation

**Use Cases:**
- Interactive chat
- Command processing
- Tool invocation
- Code execution
- File/media handling
- Multi-turn conversations
- Context-aware assistance

---

**Built with ❤️ by Zeus | Chat System v1.0.0 | Production Ready ✅**
