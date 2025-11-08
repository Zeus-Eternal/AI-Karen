# KAREN-Theme-Default Documentation Index

**Production UI Integration**

---

## 📚 Documentation Overview

This directory contains production specifications for integrating **KAREN-Theme-Default** (the UI/frontend) with the `ai_karen_engine` backend.

**Core Principle:**
> The theme is the canonical production UI shell — RBAC-aware, capsule-ready, observability-saturated, and strictly aligned with CORTEX, Memory, Reasoning, NeuroVault, and Chat.

---

## 🎯 Quick Navigation

**New to frontend integration?** Start here:

1. **[Integration Guide](KAREN_THEME_INTEGRATION_GUIDE.md)** - Complete wiring specification
2. **[Production Checklist](PRODUCTION_READINESS_CHECKLIST.md)** - 78-point verification

**Backend documentation:**
3. **[Chat System](/docs/chat/)** - Backend chat contracts
4. **[Capsule System](/docs/capsules/)** - Backend skill framework

---

## 📖 Documentation Files

### 1. KAREN Theme Integration Guide
**Location:** `KAREN_THEME_INTEGRATION_GUIDE.md`
**Purpose:** Complete integration specification
**Length:** ~8,000 words

**Contains:**
- Architecture alignment
- Endpoint configuration (single source of truth)
- Service-level integration contracts:
  * Chat Service → `chat/chat_orchestrator.py`
  * WebSocket Service → `chat/websocket_gateway.py`
  * Memory Service → `memory/manager.py`
  * Extension Service → `capsules/orchestrator.py`
- Authentication & RBAC integration
- Prompt-first discipline (no client-side prompts!)
- Security requirements (token storage, sanitization, RBAC)
- Observability integration (correlation IDs, metrics, errors)
- Testing integration
- Deployment configuration

**Audience:** All developers, architects

---

### 2. Production Readiness Checklist
**Location:** `PRODUCTION_READINESS_CHECKLIST.md`
**Purpose:** Final verification before deployment
**Length:** ~3,000 words

**Contains:**
- 78 verification checkboxes across 11 sections:
  1. Endpoint Configuration (4 checks)
  2. Authentication & RBAC (10 checks)
  3. Chat Integration (9 checks)
  4. Memory Integration (6 checks)
  5. Capsule Integration (6 checks)
  6. Model Integration (3 checks)
  7. Security (8 checks)
  8. Observability (7 checks)
  9. Testing (12 checks)
  10. Deployment (7 checks)
  11. Sign-Off (6 checks)
- Team sign-off form
- Deployment clearance tracker

**Audience:** QA engineers, team leads, DevOps

---

## 🏗️ Integration Architecture

### Frontend ↔ Backend Flow

```
┌──────────────────────────────────────┐
│   KAREN-Theme-Default (Next.js)      │
│                                      │
│  Components:                         │
│  ├── Chat Interface                  │
│  ├── Memory Browser                  │
│  ├── Extension Manager               │
│  ├── Admin Panel                     │
│  └── Security Settings               │
│                                      │
│  Services:                           │
│  ├── chatService.ts                  │
│  ├── websocket-service.ts            │
│  ├── memoryService.ts                │
│  ├── extensionService.ts             │
│  └── authService.ts                  │
└────────────┬─────────────────────────┘
             │ HTTP/WebSocket
             │ (via endpoint-config.ts)
             ▼
┌──────────────────────────────────────┐
│   ai_karen_engine (Python)           │
│                                      │
│  Chat System:                        │
│  ├── websocket_gateway.py            │
│  ├── chat_hub.py                     │
│  ├── chat_orchestrator.py            │
│  └── stream_processor.py             │
│                                      │
│  Capsule System:                     │
│  ├── registry.py                     │
│  ├── orchestrator.py                 │
│  └── 13 skill types                  │
│                                      │
│  Memory/NeuroVault:                  │
│  ├── production_memory.py            │
│  ├── neuro_vault/*                   │
│  └── conversation_search_service.py  │
│                                      │
│  CORTEX & Reasoning:                 │
│  ├── dispatch.py                     │
│  └── reasoning/*                     │
└──────────────────────────────────────┘
```

---

## 🔗 Integration Points

### 1. Chat System

**Frontend:**
- `src/components/chat/*`
- `src/services/chatService.ts`
- `src/services/websocket-service.ts`

**Backend:**
- `chat/websocket_gateway.py` - WebSocket connections
- `chat/chat_hub.py` - Message routing
- `chat/chat_orchestrator.py` - Orchestration
- `chat/stream_processor.py` - Token streaming

**Contract:** [Chat Flow Contract](/docs/chat/CHAT_FLOW_CONTRACT.md)

---

### 2. Memory & NeuroVault

**Frontend:**
- `src/components/memory/*`
- `src/services/memoryService.ts`

**Backend:**
- `memory/manager.py` - Memory operations
- `neuro_vault/*` - Fact storage
- `chat/conversation_search_service.py` - Search

**Contract:** [Memory Integration](KAREN_THEME_INTEGRATION_GUIDE.md#memory-service)

---

### 3. Capsules/Extensions

**Frontend:**
- `src/components/extensions/*`
- `src/services/extensionService.ts`

**Backend:**
- `capsules/registry.py` - Capsule discovery
- `capsules/orchestrator.py` - Execution
- `chat/tool_integration_service.py` - Tool bridge

**Contract:** [Extension Integration](KAREN_THEME_INTEGRATION_GUIDE.md#extension-service)

---

### 4. Authentication & RBAC

**Frontend:**
- `src/lib/auth/*`
- `src/lib/rbac/permissions.ts`
- `src/components/rbac/PermissionGate.tsx`

**Backend:**
- Auth service - JWT issuance
- RBAC service - Permission checks
- Capsule security - Role enforcement

**Contract:** [Auth Integration](KAREN_THEME_INTEGRATION_GUIDE.md#authentication--rbac-integration)

---

## 🔒 Security Alignment

### Frontend Security (Presentation Layer)

- ✅ **Token Storage:** In-memory only (NO localStorage)
- ✅ **Content Sanitization:** All user content via `SanitizedMarkdown`
- ✅ **RBAC Guards:** `PermissionGate` for privileged UI
- ✅ **CSP Headers:** Configured in `next.config.js`
- ✅ **HTTPS:** Enforced in production

### Backend Security (Enforcement Layer)

- ✅ **JWT Validation:** All requests authenticated
- ✅ **RBAC Enforcement:** All privileged operations checked
- ✅ **Input Sanitization:** Multi-layer (XSS, SQL, shell)
- ✅ **Audit Logging:** All sensitive operations logged
- ✅ **Circuit Breakers:** Failure isolation

**Security Documentation:**
- Frontend: [Security Requirements](KAREN_THEME_INTEGRATION_GUIDE.md#6-security-requirements)
- Backend Chat: [Chat Security](/docs/chat/CHAT_SYSTEM_DEV_SHEET.md#31-auth--rbac)
- Backend Capsules: [Capsule Security](/docs/capsules/ARCHITECTURE.md#security-architecture)

---

## 📊 Observability

### Frontend Metrics

**Emitted Events:**
```typescript
- chat_message_sent
- chat_stream_started
- chat_stream_completed
- tool_invoked
- auth_login_success
- auth_login_failure
- admin_action
```

**Metadata Included:**
- `correlation_id` (every request)
- `client_version`
- `user_id` (hashed)
- `duration_ms`

### Backend Metrics

**Prometheus:**
```
kari_chat_requests_total
kari_chat_active_sessions
kari_chat_latency_seconds
kari_chat_tool_calls_total
kari_capsule_executions_total
```

**Integration:**
- Frontend: [Observability Integration](KAREN_THEME_INTEGRATION_GUIDE.md#7-observability-integration)
- Backend: [Chat Observability](/docs/chat/CHAT_SYSTEM_DEV_SHEET.md#32-observability)

---

## 🧪 Testing

### Required Test Suites

**Frontend Tests:**
```bash
__tests__/auth/*                    # Auth flow tests
__tests__/chat/*                    # Chat integration
__tests__/rbac/*                    # Permission checks
__tests__/extensions/*              # Capsule integration
__tests__/accessibility/*           # A11y compliance
__tests__/integration/*             # End-to-end
```

**Integration Tests:**
- Endpoint connectivity
- WebSocket streaming
- RBAC enforcement
- Error handling
- Performance

**Coverage Targets:**
- Auth: 90%+
- Chat: 85%+
- RBAC: 95%+
- Integration: 80%+

**Testing Documentation:**
- [Integration Guide Tests](KAREN_THEME_INTEGRATION_GUIDE.md#8-testing-integration)
- [Checklist Tests](PRODUCTION_READINESS_CHECKLIST.md#9️⃣-testing-coverage)

---

## 🚀 Deployment

### Environment Configuration

**Production:**
```bash
NEXT_PUBLIC_KAREN_API_BASE=https://api.kari.ai
NEXT_PUBLIC_KAREN_WS_BASE=wss://ws.kari.ai
NEXT_PUBLIC_ENVIRONMENT=production
```

**Staging:**
```bash
NEXT_PUBLIC_KAREN_API_BASE=https://api.staging.kari.ai
NEXT_PUBLIC_KAREN_WS_BASE=wss://ws.staging.kari.ai
NEXT_PUBLIC_ENVIRONMENT=staging
```

**Development:**
```bash
NEXT_PUBLIC_KAREN_API_BASE=http://localhost:8000
NEXT_PUBLIC_KAREN_WS_BASE=ws://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### Docker Deployment

```bash
# Build production image
docker build -f Dockerfile.production -t karen-theme:prod .

# Run with environment
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_KAREN_API_BASE=https://api.kari.ai \
  -e NEXT_PUBLIC_KAREN_WS_BASE=wss://ws.kari.ai \
  karen-theme:prod
```

**Deployment Documentation:**
- [Deployment Config](KAREN_THEME_INTEGRATION_GUIDE.md#9-deployment-configuration)
- [Deployment Verification](PRODUCTION_READINESS_CHECKLIST.md#🔟-deployment-verification)

---

## ✅ Production Readiness

### Pre-Deployment Checklist

**78 verification points across:**
1. ✅ Endpoint Configuration (4)
2. ✅ Authentication & RBAC (10)
3. ✅ Chat Integration (9)
4. ✅ Memory Integration (6)
5. ✅ Capsule Integration (6)
6. ✅ Model Integration (3)
7. ✅ Security (8)
8. ✅ Observability (7)
9. ✅ Testing (12)
10. ✅ Deployment (7)
11. ✅ Sign-Off (6)

**Full Checklist:** [PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md)

---

## 📞 Support & Resources

**Frontend Code:**
- KAREN-Theme-Default repository
- Configuration: `/src/lib/endpoint-config.ts`
- Services: `/src/services/`

**Backend Documentation:**
- Chat System: `/docs/chat/`
- Capsule System: `/docs/capsules/`

**Support:**
- Architecture: Zeus - Chief Architect
- GitHub Issues: Project issues

---

## 🎯 Quick Reference

### Endpoint Configuration

```typescript
// src/lib/endpoint-config.ts
import { ENDPOINTS } from '@/lib/endpoint-config';

// Use everywhere:
ENDPOINTS.chat.messages
ENDPOINTS.chat.websocket
ENDPOINTS.memory.recall
ENDPOINTS.capsules.execute
```

### Chat Integration

```typescript
import { chatService } from '@/services/chatService';

// Send message
await chatService.sendMessage({
  content: "Hello Kari",
  mode: "chat",
  allow_tools: true,
});
```

### WebSocket Streaming

```typescript
import { KariWebSocketClient } from '@/services/websocket-service';

const ws = new KariWebSocketClient(token, correlationId);
ws.connect((message) => {
  if (message.type === 'stream_chunk') {
    // Handle chunk
  }
});
```

### RBAC Check

```typescript
import { PermissionGate } from '@/components/rbac/PermissionGate';
import { ROLES } from '@/lib/rbac/permissions';

<PermissionGate requiredRoles={ROLES.SYSTEM_ADMIN}>
  <AdminPanel />
</PermissionGate>
```

---

## 🏆 Summary

**KAREN-Theme-Default** is the production UI shell for Kari AI, properly wired to:

- ✅ **Chat System** (18 backend modules)
- ✅ **Capsule System** (13 skill types)
- ✅ **Memory/NeuroVault** (vector + relational storage)
- ✅ **CORTEX & Reasoning** (intent resolution + orchestration)
- ✅ **Authentication & RBAC** (JWT + role-based access)
- ✅ **Observability** (correlation IDs + metrics + logging)

**Key Principles:**
1. **Single source of truth** for endpoints (`endpoint-config.ts`)
2. **Prompt-first discipline** (no client-side prompts)
3. **Security at every layer** (presentation + enforcement)
4. **Full observability** (correlation IDs everywhere)
5. **Complete testing** (78-point checklist)

**Status:** ✅ Production Specification Complete

---

**Built with ❤️ by Zeus | Frontend Integration v1.0.0 | Production Ready ✅**
