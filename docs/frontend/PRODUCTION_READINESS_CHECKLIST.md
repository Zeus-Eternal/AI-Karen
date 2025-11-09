# KAREN-Theme-Default Production Readiness Checklist

**Version:** 1.0.0
**Purpose:** Final verification before production deployment
**Target:** Development team

---

## 🎯 Executive Summary

This checklist ensures **KAREN-Theme-Default** is properly wired to `ai_karen_engine` backend and ready for production deployment. Every box must be checked before go-live.

**Verification Principle:**
> If it's not verified, it's not production-ready.

---

## 1️⃣ Endpoint Configuration

### Single Source of Truth

- [ ] **All URLs in `src/lib/endpoint-config.ts`**
  - Verify: No hardcoded URLs in service files
  - Check: `grep -r "http://localhost" src/services/`
  - Must return: No results (except in test files)

- [ ] **Environment variables configured**
  ```bash
  # Verify these are set:
  echo $NEXT_PUBLIC_KAREN_API_BASE
  echo $NEXT_PUBLIC_KAREN_WS_BASE
  echo $NEXT_PUBLIC_KAREN_AUTH_ISSUER
  ```
  - Production: Must use HTTPS/WSS
  - Staging: Must use staging endpoints
  - Dev: Can use HTTP/WS localhost

- [ ] **Endpoint validation on load**
  - Check: `endpoint-config.ts` throws error if vars missing
  - Test: Start app without env vars → should fail fast

- [ ] **All services use ENDPOINTS constant**
  ```typescript
  // Verify in each service file:
  import { ENDPOINTS } from '@/lib/endpoint-config';
  // NOT: const url = 'http://...';
  ```

---

## 2️⃣ Authentication & Session Management

### JWT Integration

- [ ] **Login flow connected to backend**
  - Endpoint: `ENDPOINTS.auth.login`
  - Maps to: Backend auth service
  - Test: Login with valid credentials → receive JWT
  - Test: Login with invalid credentials → error

- [ ] **Token storage is secure**
  - Check: NO use of `localStorage.setItem('token', ...)`
  - Verify: Tokens in memory or HTTP-only cookies only
  - Location: `lib/auth/token-storage.ts`

- [ ] **Token refresh working**
  - Endpoint: `ENDPOINTS.auth.refresh`
  - Test: Expired token → auto-refresh → continue
  - Test: Invalid refresh token → force re-login

- [ ] **Logout clears session**
  - Check: All tokens cleared
  - Check: WebSocket connections closed
  - Check: User redirected to login

### RBAC Enforcement

- [ ] **Roles match backend definitions**
  ```typescript
  // Verify roles in lib/rbac/permissions.ts match:
  // - capsules/schemas.py (required_roles)
  // - chat RBAC roles
  // - backend auth service roles
  ```

- [ ] **PermissionGate used for privileged UI**
  - Check: Admin panels wrapped in PermissionGate
  - Check: Tool access wrapped in PermissionGate
  - Check: Config changes wrapped in PermissionGate

- [ ] **Frontend RBAC is presentation-only**
  - Verify: All actual security enforcement in backend
  - Test: Bypass frontend check → backend denies (403)

---

## 3️⃣ Chat System Integration

### WebSocket Connection

- [ ] **WebSocket URL correct**
  - Source: `ENDPOINTS.chat.websocket`
  - Protocol: `wss://` in production, `ws://` in dev
  - Test: Connection established successfully

- [ ] **Authentication on connect**
  - Check: JWT token sent in WebSocket URL or headers
  - Maps to: `chat/websocket_gateway.py` authentication
  - Test: Invalid token → connection rejected

- [ ] **Correlation IDs propagate**
  - Check: Every message has correlation_id
  - Verify: Correlation ID returned in responses
  - Test: Track single message through logs using ID

### Message Format

- [ ] **Message schema matches backend**
  ```typescript
  // Frontend ChatMessage interface must match:
  // - chat/conversation_models.py Message class

  interface ChatMessage {
    id: string;
    conversation_id: string;
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    timestamp: string;  // ISO format
    metadata?: Record<string, any>;
  }
  ```

- [ ] **Streaming integration working**
  - Maps to: `chat/stream_processor.py`
  - Test: Send message → receive stream chunks
  - Test: Stream error handling (connection drop)

### Chat Orchestrator Integration

- [ ] **Message send uses orchestrator**
  - Endpoint: `ENDPOINTS.chat.messages`
  - Maps to: `chat/chat_hub.py` → `chat/chat_orchestrator.py`
  - NO client-side LLM calls
  - NO client-side prompt assembly

- [ ] **Mode selection passed to backend**
  ```typescript
  // Frontend sends mode, backend uses it:
  {
    content: "user message",
    mode: "analysis",  // Backend decides what this means
    allow_tools: true,
    allow_memory: true
  }
  ```

- [ ] **No client-side prompt hacking**
  - Check: NO system prompt construction in UI code
  - Verify: UI collects user input only
  - Backend builds all prompts

---

## 4️⃣ Memory & NeuroVault Integration

### Memory Service

- [ ] **Recall uses backend**
  - Endpoint: `ENDPOINTS.memory.recall`
  - Maps to: `memory/manager.py` recall_context
  - Test: Query → relevant memories returned

- [ ] **Search uses backend**
  - Endpoint: `ENDPOINTS.memory.search`
  - Maps to: `chat/conversation_search_service.py`
  - Test: Search past conversations → results

- [ ] **No client-side memory mutations**
  - Check: All writes go through backend API
  - Verify: No direct IndexedDB/localStorage for memories
  - Maps to: `chat/production_memory.py`

### NeuroVault Access

- [ ] **Facts and concepts via API**
  - Endpoints: `ENDPOINTS.neurovault.*`
  - Maps to: `neuro_vault/*` backend modules
  - Test: Fetch facts → data returned

- [ ] **Display only, no mutations**
  - UI displays NeuroVault data
  - All edits go through backend with audit

---

## 5️⃣ Capsule/Extension Integration

### Registry Integration

- [ ] **List capsules from backend**
  - Endpoint: `ENDPOINTS.capsules.list`
  - Maps to: `capsules/registry.py` list_capsules
  - Test: Fetch list → all capsules returned

- [ ] **Capsule metadata accurate**
  ```typescript
  // Verify CapsuleInfo matches backend:
  interface CapsuleInfo {
    id: string;           // matches manifest.yaml id
    name: string;         // matches manifest.yaml name
    version: string;      // matches manifest.yaml version
    type: string;         // matches CapsuleType enum
    capabilities: string[];
    required_roles: string[];
    status: 'active' | 'inactive' | 'error';
  }
  ```

### Execution Integration

- [ ] **Execute via orchestrator**
  - Endpoint: `ENDPOINTS.capsules.execute`
  - Maps to: `capsules/orchestrator.py` execute_capsule
  - Via: `chat/tool_integration_service.py` invoke_capsule_as_tool

- [ ] **RBAC enforced**
  - Check: UI validates user has required_roles
  - Check: Backend also validates (defense in depth)
  - Test: Unauthorized user → backend returns 403

- [ ] **Status monitoring**
  - Endpoint: `ENDPOINTS.capsules.status`
  - Maps to: `capsules/initialization.py` get_system_status
  - Test: Fetch status → metrics returned

---

## 6️⃣ Model Selection Integration

### Model Registry

- [ ] **List models from backend**
  - Endpoint: `ENDPOINTS.models.list`
  - Maps to: Backend model registry
  - Test: Fetch models → available models returned

- [ ] **Model selection via backend**
  - NO client-side model calls
  - UI sends preference, backend decides
  - Maps to: `chat/factory.py` model selection

- [ ] **Fallback handling**
  - Test: Primary model unavailable → backend falls back
  - UI displays fallback was used

---

## 7️⃣ Security Verification

### Content Sanitization

- [ ] **All user content sanitized**
  - Component: `SanitizedMarkdown` for chat messages
  - Component: `SecureLink` for URLs
  - Check: No direct `dangerouslySetInnerHTML` without sanitization

- [ ] **XSS prevention**
  - Test: Send `<script>alert('xss')</script>` → sanitized
  - Test: Send malicious markdown → sanitized

### Token Security

- [ ] **No localStorage for tokens**
  ```bash
  # Must return no results:
  grep -r "localStorage.setItem.*token" src/
  ```

- [ ] **No console.log of tokens**
  ```bash
  # Must return no results:
  grep -r "console.log.*token" src/
  ```

- [ ] **HTTPS enforced in production**
  - Check: `next.config.js` or reverse proxy config
  - Check: Strict-Transport-Security header

### CSP Headers

- [ ] **Content Security Policy configured**
  ```javascript
  // next.config.js or middleware
  {
    'Content-Security-Policy':
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-eval'; " +
      "style-src 'self' 'unsafe-inline'; " +
      "connect-src 'self' https://api.kari.ai wss://ws.kari.ai;"
  }
  ```

### Audit Logging

- [ ] **Admin actions logged**
  - Uses: `lib/audit/audit-logger.ts`
  - Backend receives audit events
  - Test: Admin action → audit log created

---

## 8️⃣ Observability Integration

### Correlation IDs

- [ ] **Generated for all requests**
  - Check: `lib/correlation-id.ts` used
  - Verify: Every API call has X-Correlation-ID header
  - Verify: WebSocket messages include correlation_id

- [ ] **Propagate through stack**
  - Test: Send message → check backend logs → same correlation_id
  - Test: Error occurs → correlation_id in error report

### Performance Monitoring

- [ ] **Events tracked**
  - Service: `performance-monitor.ts`
  - Events:
    - chat_message_sent
    - chat_stream_started/completed
    - tool_invoked
    - auth_login_success/failure
  - Endpoint: `ENDPOINTS.monitoring.metrics`

- [ ] **Metrics include metadata**
  ```typescript
  {
    event_type: 'chat_message_sent',
    correlation_id: '...',
    duration_ms: 234,
    metadata: {
      client_version: '1.0.0',
      user_id: '...' // hashed
    }
  }
  ```

### Error Tracking

- [ ] **Errors reported to backend**
  - Service: `lib/error-tracking.ts`
  - Includes: correlation_id, stack trace, user_id
  - Test: Trigger error → appears in monitoring

- [ ] **User-friendly error messages**
  - NO raw stack traces to users
  - Correlation ID shown for support

---

## 9️⃣ Testing Coverage

### Endpoint Connectivity Tests

- [ ] **Health check test passing**
  ```typescript
  // __tests__/integration/endpoint-connectivity.test.ts
  test('backend health endpoint', async () => {
    const response = await fetch(ENDPOINTS.monitoring.health);
    expect(response.ok).toBe(true);
  });
  ```

- [ ] **All endpoints reachable**
  - Test each endpoint in `ENDPOINTS` object
  - Verify 404s for invalid paths
  - Verify 401s for unauthenticated requests

### RBAC Tests

- [ ] **Permission checks working**
  ```typescript
  // __tests__/rbac/permissions.test.ts
  test('hasPermission with correct roles', () => {
    expect(hasPermission(['chat.user'], 'chat.user')).toBe(true);
  });

  test('hasPermission without required roles', () => {
    expect(hasPermission(['chat.user'], 'system.admin')).toBe(false);
  });
  ```

### Chat Integration Tests

- [ ] **Message send/receive**
  - Test: Send message → receive response
  - Test: Streaming → chunks arrive in order

- [ ] **WebSocket lifecycle**
  - Test: Connect → send → receive → disconnect
  - Test: Reconnect on connection drop

### Memory Tests

- [ ] **Recall integration**
  - Test: Query → memories returned
  - Test: No results → empty array (not error)

- [ ] **Search integration**
  - Test: Search query → results ranked by relevance

### Accessibility Tests

- [ ] **A11y test suite passing**
  ```bash
  npm test __tests__/accessibility/
  ```

- [ ] **Keyboard navigation**
  - Test: Tab through chat interface
  - Test: Enter to send message
  - Test: Escape to close modals

---

## 🔟 Deployment Verification

### Docker Build

- [ ] **Production build succeeds**
  ```bash
  docker build -f Dockerfile.production -t karen-theme:prod .
  ```

- [ ] **Image size reasonable**
  - Check: `docker images karen-theme:prod`
  - Target: < 500MB

- [ ] **Health check works**
  ```bash
  docker run -p 3000:3000 karen-theme:prod
  curl http://localhost:3000/api/health
  # Should return 200 OK
  ```

### Environment Configuration

- [ ] **No dev env vars in production**
  ```bash
  # Production .env must NOT have:
  NEXT_PUBLIC_KAREN_API_BASE=http://localhost:8000  # BAD

  # Must have:
  NEXT_PUBLIC_KAREN_API_BASE=https://api.kari.ai   # GOOD
  ```

- [ ] **All required vars set**
  ```bash
  # Check .env.production has:
  NEXT_PUBLIC_KAREN_API_BASE=
  NEXT_PUBLIC_KAREN_WS_BASE=
  NEXT_PUBLIC_KAREN_AUTH_ISSUER=
  NEXT_PUBLIC_ENVIRONMENT=production
  ```

### Static Asset Caching

- [ ] **Cache headers configured**
  ```javascript
  // next.config.js
  {
    headers: [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }
        ]
      }
    ]
  }
  ```

---

## 1️⃣1️⃣ Final Sign-Off

### Documentation

- [ ] **Integration guide reviewed**
  - Location: `/docs/frontend/KAREN_THEME_INTEGRATION_GUIDE.md`
  - Team understands endpoint contracts
  - Team understands security requirements

- [ ] **Backend contracts understood**
  - Chat system: `/docs/chat/CHAT_FLOW_CONTRACT.md`
  - Capsules: `/docs/capsules/`
  - Team knows what backend expects

### Code Review

- [ ] **No hardcoded secrets**
  ```bash
  # Must return no results:
  grep -r "password.*=.*\"" src/
  grep -r "api_key.*=.*\"" src/
  grep -r "secret.*=.*\"" src/
  ```

- [ ] **No debug code**
  ```bash
  # Must return no results (except test files):
  grep -r "console.log" src/
  grep -r "debugger" src/
  ```

- [ ] **All TODOs resolved**
  ```bash
  # Check for unresolved TODOs:
  grep -r "TODO" src/
  # All should be assigned or closed
  ```

### Team Sign-Off

**Each team member must verify their area:**

- [ ] **Frontend Lead:** All UI components wired correctly
- [ ] **Backend Lead:** All API contracts verified
- [ ] **Security Lead:** All security requirements met
- [ ] **QA Lead:** All tests passing
- [ ] **DevOps Lead:** Deployment configuration verified

---

## ✅ Production Deployment Clearance

**This checklist must be 100% complete before production deployment.**

| Section | Boxes | Checked | Status |
|---------|-------|---------|--------|
| 1. Endpoint Configuration | 4 | ___ | ⬜ |
| 2. Authentication & RBAC | 10 | ___ | ⬜ |
| 3. Chat Integration | 9 | ___ | ⬜ |
| 4. Memory Integration | 6 | ___ | ⬜ |
| 5. Capsule Integration | 6 | ___ | ⬜ |
| 6. Model Integration | 3 | ___ | ⬜ |
| 7. Security | 8 | ___ | ⬜ |
| 8. Observability | 7 | ___ | ⬜ |
| 9. Testing | 12 | ___ | ⬜ |
| 10. Deployment | 7 | ___ | ⬜ |
| 11. Sign-Off | 6 | ___ | ⬜ |
| **TOTAL** | **78** | **___** | ⬜ |

**Deployment Approved By:**
- Name: ________________
- Role: ________________
- Date: ________________
- Signature: ________________

---

## 📞 Support

**Questions:** Zeus - Chief Architect
**Documentation:** `/docs/frontend/`
**Related:** `/docs/chat/`, `/docs/capsules/`

---

**Checklist Version:** 1.0.0
**Last Updated:** 2025-11-08
**Status:** ✅ Ready for Use
