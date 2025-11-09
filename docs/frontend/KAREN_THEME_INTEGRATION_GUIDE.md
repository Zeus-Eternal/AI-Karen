# KAREN-Theme-Default Production Integration Guide

**Version:** 1.0.0
**Date:** 2025-11-08
**Scope:** Production wiring of UI to `ai_karen_engine` backend

---

## 🎯 Overview

**KAREN-Theme-Default** is the canonical production UI shell for Kari AI. This document defines the **exact integration contract** between the frontend theme and the backend engine (`ai_karen_engine`).

**Core Principle:**
> The theme is a **view layer only**. All intelligence, orchestration, and security enforcement happens in the backend. The UI collects input, displays output, and enforces RBAC at the presentation layer only.

---

## 1. Architecture Alignment

### Backend Systems (What UI Connects To)

```
┌─────────────────────────────────────────────┐
│        KAREN-Theme-Default (UI)              │
│  - Next.js frontend                          │
│  - WebSocket client                          │
│  - API client library                        │
└──────────────┬──────────────────────────────┘
               │ HTTP/WebSocket
               ▼
┌─────────────────────────────────────────────┐
│      ai_karen_engine (Backend)              │
├─────────────────────────────────────────────┤
│  Chat System                                │
│  ├── websocket_gateway.py                   │
│  ├── chat_hub.py                            │
│  └── chat_orchestrator.py                   │
├─────────────────────────────────────────────┤
│  Capsule System                             │
│  ├── registry.py                            │
│  └── orchestrator.py                        │
├─────────────────────────────────────────────┤
│  Memory / NeuroVault                        │
│  ├── production_memory.py                   │
│  └── neuro_vault/*                          │
├─────────────────────────────────────────────┤
│  CORTEX & Reasoning                         │
│  ├── dispatch.py                            │
│  └── reasoning/*                            │
└─────────────────────────────────────────────┘
```

---

## 2. Endpoint Configuration (Single Source of Truth)

### Required: `src/lib/endpoint-config.ts`

**This file is the ONLY place that defines backend URLs.**

```typescript
// src/lib/endpoint-config.ts
export const KAREN_API_BASE = process.env.NEXT_PUBLIC_KAREN_API_BASE!;
export const KAREN_WS_BASE = process.env.NEXT_PUBLIC_KAREN_WS_BASE!;
export const KAREN_AUTH_ISSUER = process.env.NEXT_PUBLIC_KAREN_AUTH_ISSUER!;

// Validation on load
if (!KAREN_API_BASE) {
  throw new Error("NEXT_PUBLIC_KAREN_API_BASE is required");
}
if (!KAREN_WS_BASE) {
  throw new Error("NEXT_PUBLIC_KAREN_WS_BASE is required");
}

// API endpoints
export const ENDPOINTS = {
  // Auth
  auth: {
    login: `${KAREN_API_BASE}/auth/login`,
    logout: `${KAREN_API_BASE}/auth/logout`,
    refresh: `${KAREN_API_BASE}/auth/refresh`,
    validate: `${KAREN_API_BASE}/auth/validate`,
  },

  // Chat
  chat: {
    conversations: `${KAREN_API_BASE}/chat/conversations`,
    messages: `${KAREN_API_BASE}/chat/messages`,
    websocket: `${KAREN_WS_BASE}/chat/stream`,
  },

  // Memory
  memory: {
    recall: `${KAREN_API_BASE}/memory/recall`,
    store: `${KAREN_API_BASE}/memory/store`,
    search: `${KAREN_API_BASE}/memory/search`,
  },

  // NeuroVault
  neurovault: {
    facts: `${KAREN_API_BASE}/neurovault/facts`,
    concepts: `${KAREN_API_BASE}/neurovault/concepts`,
  },

  // Capsules / Extensions
  capsules: {
    list: `${KAREN_API_BASE}/capsules`,
    execute: `${KAREN_API_BASE}/capsules/execute`,
    status: `${KAREN_API_BASE}/capsules/status`,
  },

  // Models
  models: {
    list: `${KAREN_API_BASE}/models`,
    select: `${KAREN_API_BASE}/models/select`,
  },

  // Admin
  admin: {
    users: `${KAREN_API_BASE}/admin/users`,
    settings: `${KAREN_API_BASE}/admin/settings`,
    audit: `${KAREN_API_BASE}/admin/audit`,
  },

  // Monitoring
  monitoring: {
    metrics: `${KAREN_API_BASE}/monitoring/metrics`,
    health: `${KAREN_API_BASE}/monitoring/health`,
  },
} as const;

export default ENDPOINTS;
```

### Environment Variables

```bash
# .env.production
NEXT_PUBLIC_KAREN_API_BASE=https://api.kari.ai
NEXT_PUBLIC_KAREN_WS_BASE=wss://ws.kari.ai
NEXT_PUBLIC_KAREN_AUTH_ISSUER=https://auth.kari.ai
NEXT_PUBLIC_ENVIRONMENT=production

# .env.staging
NEXT_PUBLIC_KAREN_API_BASE=https://api.staging.kari.ai
NEXT_PUBLIC_KAREN_WS_BASE=wss://ws.staging.kari.ai
NEXT_PUBLIC_KAREN_AUTH_ISSUER=https://auth.staging.kari.ai
NEXT_PUBLIC_ENVIRONMENT=staging

# .env.local (development)
NEXT_PUBLIC_KAREN_API_BASE=http://localhost:8000
NEXT_PUBLIC_KAREN_WS_BASE=ws://localhost:8000
NEXT_PUBLIC_KAREN_AUTH_ISSUER=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

---

## 3. Service-Level Integration Contracts

### 3.1 Chat Service (`services/chatService.ts`)

**Purpose:** Interface to backend chat system

**Must Use:**
- `ENDPOINTS.chat.*` for all HTTP calls
- `ENDPOINTS.chat.websocket` for streaming
- `enhanced-api-client.ts` for API calls
- Correlation ID on every request

**Contract:**

```typescript
// services/chatService.ts
import { ENDPOINTS } from '@/lib/endpoint-config';
import { apiClient } from '@/lib/enhanced-api-client';
import { generateCorrelationId } from '@/lib/correlation-id';

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SendMessageRequest {
  conversation_id?: string;
  content: string;
  mode?: string;
  allow_tools?: boolean;
  allow_memory?: boolean;
}

export interface SendMessageResponse {
  message: ChatMessage;
  correlation_id: string;
}

export const chatService = {
  /**
   * Send message to backend chat orchestrator.
   *
   * Backend maps to:
   * - chat/websocket_gateway.py (for streaming)
   * - chat/chat_hub.py (routing)
   * - chat/chat_orchestrator.py (orchestration)
   */
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    const correlationId = generateCorrelationId();

    const response = await apiClient.post<SendMessageResponse>(
      ENDPOINTS.chat.messages,
      request,
      {
        headers: {
          'X-Correlation-ID': correlationId,
        },
      }
    );

    return response;
  },

  /**
   * Get conversation history.
   *
   * Backend maps to:
   * - chat/enhanced_conversation_manager.py
   * - chat/production_memory.py
   */
  async getConversation(conversationId: string): Promise<ChatMessage[]> {
    const response = await apiClient.get<ChatMessage[]>(
      `${ENDPOINTS.chat.conversations}/${conversationId}/messages`
    );

    return response;
  },

  /**
   * Create new conversation.
   */
  async createConversation(metadata?: Record<string, any>) {
    const response = await apiClient.post(
      ENDPOINTS.chat.conversations,
      { metadata }
    );

    return response;
  },
};
```

### 3.2 WebSocket Service (`services/websocket-service.ts`)

**Purpose:** Real-time streaming from backend

**Must Use:**
- `ENDPOINTS.chat.websocket` for WebSocket URL
- JWT token for authentication
- Correlation ID for all messages

**Contract:**

```typescript
// services/websocket-service.ts
import { ENDPOINTS } from '@/lib/endpoint-config';

export interface WebSocketMessage {
  type: 'stream_chunk' | 'error' | 'complete' | 'typing';
  content?: string;
  correlation_id: string;
  metadata?: Record<string, any>;
}

export class KariWebSocketClient {
  private ws: WebSocket | null = null;
  private token: string;
  private correlationId: string;

  constructor(token: string, correlationId: string) {
    this.token = token;
    this.correlationId = correlationId;
  }

  /**
   * Connect to backend WebSocket gateway.
   *
   * Backend maps to:
   * - chat/websocket_gateway.py (authentication + streaming)
   * - chat/stream_processor.py (token streaming)
   */
  connect(onMessage: (msg: WebSocketMessage) => void): void {
    // Append token and correlation ID to WebSocket URL
    const url = `${ENDPOINTS.chat.websocket}?token=${this.token}&correlation_id=${this.correlationId}`;

    this.ws = new WebSocket(url);

    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      onMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      onMessage({
        type: 'error',
        content: 'WebSocket connection failed',
        correlation_id: this.correlationId,
      });
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] Connection closed');
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### 3.3 Memory Service (`services/memoryService.ts`)

**Purpose:** Interface to NeuroVault and memory systems

**Contract:**

```typescript
// services/memoryService.ts
import { ENDPOINTS } from '@/lib/endpoint-config';
import { apiClient } from '@/lib/enhanced-api-client';

export interface MemoryRecall {
  content: string;
  source: 'short_term' | 'long_term' | 'vault';
  score: number;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export const memoryService = {
  /**
   * Recall relevant memories.
   *
   * Backend maps to:
   * - memory/manager.py (recall_context)
   * - neuro_vault/* (vault queries)
   */
  async recall(query: string, options?: {
    top_k?: number;
    sources?: string[];
  }): Promise<MemoryRecall[]> {
    const response = await apiClient.post<MemoryRecall[]>(
      ENDPOINTS.memory.recall,
      { query, ...options }
    );

    return response;
  },

  /**
   * Search memories.
   *
   * Backend maps to:
   * - chat/conversation_search_service.py
   */
  async search(query: string, filters?: Record<string, any>) {
    const response = await apiClient.post(
      ENDPOINTS.memory.search,
      { query, filters }
    );

    return response;
  },
};
```

### 3.4 Extension Service (`services/extensionService.ts`)

**Purpose:** Interface to capsule/plugin system

**Contract:**

```typescript
// services/extensionService.ts
import { ENDPOINTS } from '@/lib/endpoint-config';
import { apiClient } from '@/lib/enhanced-api-client';

export interface CapsuleInfo {
  id: string;
  name: string;
  version: string;
  type: string;
  capabilities: string[];
  required_roles: string[];
  status: 'active' | 'inactive' | 'error';
}

export const extensionService = {
  /**
   * List available capsules.
   *
   * Backend maps to:
   * - capsules/registry.py (list_capsules)
   */
  async listCapsules(): Promise<CapsuleInfo[]> {
    const response = await apiClient.get<CapsuleInfo[]>(
      ENDPOINTS.capsules.list
    );

    return response;
  },

  /**
   * Execute capsule.
   *
   * Backend maps to:
   * - capsules/orchestrator.py (execute_capsule)
   * - Via tool_integration_service in chat
   */
  async executeCapsule(
    capsuleId: string,
    request: Record<string, any>,
    correlationId: string
  ) {
    const response = await apiClient.post(
      ENDPOINTS.capsules.execute,
      { capsule_id: capsuleId, request },
      {
        headers: {
          'X-Correlation-ID': correlationId,
        },
      }
    );

    return response;
  },

  /**
   * Get capsule system status.
   *
   * Backend maps to:
   * - capsules/initialization.py (get_system_status)
   */
  async getStatus() {
    const response = await apiClient.get(ENDPOINTS.capsules.status);
    return response;
  },
};
```

---

## 4. Authentication & RBAC Integration

### 4.1 Auth Service (`lib/auth/authService.ts`)

**Purpose:** JWT authentication with backend

**Contract:**

```typescript
// lib/auth/authService.ts
import { ENDPOINTS } from '@/lib/endpoint-config';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    roles: string[];
    tenant_id?: string;
  };
}

export const authService = {
  /**
   * Login and receive JWT.
   *
   * Backend maps to:
   * - auth service (JWT issuance)
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(ENDPOINTS.auth.login, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    return response.json();
  },

  /**
   * Validate JWT token.
   */
  async validateToken(token: string): Promise<boolean> {
    try {
      const response = await fetch(ENDPOINTS.auth.validate, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      return response.ok;
    } catch {
      return false;
    }
  },

  /**
   * Refresh access token.
   */
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await fetch(ENDPOINTS.auth.refresh, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    return response.json();
  },
};
```

### 4.2 RBAC Enforcement

**Frontend RBAC is PRESENTATION ONLY. Backend enforces security.**

```typescript
// lib/rbac/permissions.ts

/**
 * RBAC roles that match backend.
 *
 * Backend roles defined in:
 * - capsules/schemas.py (required_roles)
 * - chat system RBAC (chat.*, admin.*)
 */
export const ROLES = {
  // Chat permissions
  CHAT_USER: 'chat.user',
  CHAT_TOOLS_SEARCH: 'chat.tools.search',
  CHAT_TOOLS_CODE: 'chat.tools.code',
  CHAT_MODE_SWITCH: 'chat.mode.switch',
  CHAT_CONFIG_EDIT: 'chat.config.edit',
  CHAT_PERSONA_CHANGE: 'chat.persona.change',
  CHAT_ADMIN: 'chat.admin',

  // System permissions
  SYSTEM_ADMIN: 'system.admin',
  SUPER_ADMIN: 'super_admin',

  // Capsule permissions
  CAPSULE_DEVOPS: 'capsule.devops',
  CAPSULE_SECURITY: 'capsule.security',
  CAPSULE_MEMORY: 'capsule.memory',

  // Evil mode
  EVIL_MODE: 'evil_mode',
} as const;

/**
 * Check if user has required roles.
 *
 * This is UI-only validation. Backend MUST enforce.
 */
export function hasPermission(
  userRoles: string[],
  requiredRoles: string | string[]
): boolean {
  const required = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  return required.every((role) => userRoles.includes(role));
}
```

**Component Usage:**

```typescript
// components/rbac/PermissionGate.tsx
import { hasPermission } from '@/lib/rbac/permissions';
import { useAuth } from '@/providers/auth-provider';

interface PermissionGateProps {
  requiredRoles: string | string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({ requiredRoles, children, fallback }: PermissionGateProps) {
  const { user } = useAuth();

  if (!user || !hasPermission(user.roles, requiredRoles)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
```

---

## 5. Prompt-First Discipline

**CRITICAL: The UI NEVER fabricates prompts or system instructions.**

### What UI Collects

```typescript
// UI collects user intent, not prompts
interface UserInput {
  // User's message
  content: string;

  // Mode selection (UI toggle)
  mode: 'chat' | 'analysis' | 'creative' | 'technical' | 'devops';

  // Feature toggles (UI checkboxes)
  allow_tools: boolean;
  allow_memory: boolean;
  allow_code_execution: boolean;

  // Context (from UI state)
  conversation_id: string;
  correlation_id: string;

  // Metadata (NOT system prompts)
  metadata: {
    client_version: string;
    user_preferences: Record<string, any>;
  };
}
```

### What Backend Does

```python
# Backend (chat/chat_orchestrator.py) builds prompts:

def orchestrate_turn(turn_context: TurnContext):
    # Backend assembles:
    # 1. System instructions based on mode
    # 2. Context from memory
    # 3. Tool availability
    # 4. Model selection
    # 5. Prompt rendering

    # UI never sees this
    prompt = render_prompt(...)
    result = llm.generate_text(prompt, ...)
    return result
```

### UI Anti-Patterns to Avoid

❌ **BAD:**
```typescript
// DON'T DO THIS
const systemPrompt = `You are Kari, an AI assistant. ${userInstructions}...`;
const response = await openai.chat.completions.create({
  messages: [
    { role: 'system', content: systemPrompt },  // UI building prompts
    { role: 'user', content: userMessage },
  ],
});
```

✅ **GOOD:**
```typescript
// DO THIS
const response = await chatService.sendMessage({
  content: userMessage,
  mode: selectedMode,
  allow_tools: toolsEnabled,
});
// Backend builds all prompts
```

---

## 6. Security Requirements

### 6.1 Token Storage

**NEVER use localStorage for tokens.**

```typescript
// lib/auth/token-storage.ts

/**
 * Secure token storage.
 *
 * Options (in order of preference):
 * 1. HTTP-only cookies (backend sets)
 * 2. In-memory storage (this implementation)
 * 3. Session storage (fallback, less secure than in-memory)
 */
class TokenStorage {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  clear(): void {
    this.accessToken = null;
    this.refreshToken = null;
  }
}

export const tokenStorage = new TokenStorage();
```

### 6.2 Content Sanitization

**All untrusted content must be sanitized.**

```typescript
// components/shared/SanitizedMarkdown.tsx
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface SanitizedMarkdownProps {
  content: string;
  className?: string;
}

export function SanitizedMarkdown({ content, className }: SanitizedMarkdownProps) {
  const html = marked.parse(content);
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'a'],
    ALLOWED_ATTR: ['href', 'class'],
  });

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: clean }}
    />
  );
}
```

### 6.3 RBAC Guards

**All privileged UI must check permissions.**

```typescript
// components/admin/AdminPanel.tsx
import { PermissionGate } from '@/components/rbac/PermissionGate';
import { ROLES } from '@/lib/rbac/permissions';

export function AdminPanel() {
  return (
    <PermissionGate
      requiredRoles={[ROLES.SYSTEM_ADMIN, ROLES.SUPER_ADMIN]}
      fallback={<div>Access denied</div>}
    >
      <div>
        {/* Admin UI */}
      </div>
    </PermissionGate>
  );
}
```

---

## 7. Observability Integration

### 7.1 Correlation IDs

**Every request must have a correlation ID.**

```typescript
// lib/correlation-id.ts
import { v4 as uuidv4 } from 'uuid';

export function generateCorrelationId(): string {
  return uuidv4();
}

export function getCorrelationIdFromResponse(
  response: Response
): string | null {
  return response.headers.get('X-Correlation-ID');
}
```

### 7.2 Performance Monitoring

```typescript
// services/performance-monitor.ts
import { ENDPOINTS } from '@/lib/endpoint-config';

interface PerformanceEvent {
  event_type: string;
  correlation_id: string;
  duration_ms?: number;
  metadata?: Record<string, any>;
}

export const performanceMonitor = {
  /**
   * Track frontend performance events.
   *
   * Emits to backend monitoring endpoint.
   */
  async track(event: PerformanceEvent): Promise<void> {
    try {
      await fetch(ENDPOINTS.monitoring.metrics, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...event,
          timestamp: Date.now(),
          client_version: process.env.NEXT_PUBLIC_VERSION,
        }),
      });
    } catch (error) {
      console.error('[Performance] Failed to track event:', error);
    }
  },

  /**
   * Track chat message performance.
   */
  trackChatMessage(correlationId: string, durationMs: number): void {
    this.track({
      event_type: 'chat_message_sent',
      correlation_id: correlationId,
      duration_ms: durationMs,
    });
  },

  /**
   * Track tool invocation.
   */
  trackToolInvocation(toolId: string, correlationId: string, durationMs: number): void {
    this.track({
      event_type: 'tool_invoked',
      correlation_id: correlationId,
      duration_ms: durationMs,
      metadata: { tool_id: toolId },
    });
  },
};
```

### 7.3 Error Tracking

```typescript
// lib/error-tracking.ts

export interface ErrorEvent {
  type: string;
  message: string;
  correlation_id?: string;
  stack?: string;
  user_id?: string;
}

export const errorTracking = {
  /**
   * Report error to backend or external service.
   */
  report(error: Error, correlationId?: string, metadata?: Record<string, any>): void {
    const errorEvent: ErrorEvent = {
      type: error.name,
      message: error.message,
      stack: error.stack,
      correlation_id: correlationId,
    };

    console.error('[Error]', errorEvent);

    // Send to backend or Sentry/etc
    // (Implementation depends on monitoring setup)
  },
};
```

---

## 8. Testing Integration

### 8.1 API Connectivity Tests

```typescript
// __tests__/integration/endpoint-connectivity.test.ts
import { ENDPOINTS } from '@/lib/endpoint-config';

describe('Backend Connectivity', () => {
  it('should connect to backend health endpoint', async () => {
    const response = await fetch(ENDPOINTS.monitoring.health);
    expect(response.ok).toBe(true);
  });

  it('should have valid WebSocket endpoint', () => {
    expect(ENDPOINTS.chat.websocket).toMatch(/^wss?:\/\//);
  });

  it('should have all required endpoints defined', () => {
    expect(ENDPOINTS.auth.login).toBeDefined();
    expect(ENDPOINTS.chat.messages).toBeDefined();
    expect(ENDPOINTS.memory.recall).toBeDefined();
    expect(ENDPOINTS.capsules.list).toBeDefined();
  });
});
```

### 8.2 RBAC Tests

```typescript
// __tests__/rbac/permissions.test.ts
import { hasPermission, ROLES } from '@/lib/rbac/permissions';

describe('RBAC Permissions', () => {
  it('should grant access with correct roles', () => {
    const userRoles = [ROLES.CHAT_USER, ROLES.CHAT_TOOLS_SEARCH];
    expect(hasPermission(userRoles, ROLES.CHAT_USER)).toBe(true);
  });

  it('should deny access without required roles', () => {
    const userRoles = [ROLES.CHAT_USER];
    expect(hasPermission(userRoles, ROLES.SYSTEM_ADMIN)).toBe(false);
  });

  it('should require all roles when multiple specified', () => {
    const userRoles = [ROLES.CHAT_USER];
    expect(hasPermission(userRoles, [ROLES.CHAT_USER, ROLES.SYSTEM_ADMIN])).toBe(false);
  });
});
```

---

## 9. Deployment Configuration

### 9.1 Docker Configuration

```dockerfile
# Dockerfile.production
FROM node:20-alpine AS base

WORKDIR /app

# Dependencies
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Build
COPY . .
RUN npm run build

# Production
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=base /app/public ./public
COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

### 9.2 Environment Variables Checklist

```bash
# Required for production
NEXT_PUBLIC_KAREN_API_BASE=        # Backend API URL
NEXT_PUBLIC_KAREN_WS_BASE=         # WebSocket URL
NEXT_PUBLIC_KAREN_AUTH_ISSUER=     # Auth issuer URL
NEXT_PUBLIC_ENVIRONMENT=           # prod/staging/dev

# Optional
NEXT_PUBLIC_VERSION=               # App version (from package.json)
NEXT_PUBLIC_SENTRY_DSN=            # Error tracking
NEXT_PUBLIC_ANALYTICS_ID=          # Analytics
```

---

## 10. Production Readiness Checklist

### ✅ Configuration
- [ ] All API endpoints in `endpoint-config.ts`
- [ ] No hardcoded URLs in service files
- [ ] Environment variables set for target environment
- [ ] WebSocket URL uses correct protocol (wss:// in prod)

### ✅ Authentication
- [ ] JWT validation with backend
- [ ] Token storage secure (no localStorage)
- [ ] Refresh token flow working
- [ ] Logout clears tokens

### ✅ RBAC
- [ ] Roles match backend definitions
- [ ] `PermissionGate` used for privileged UI
- [ ] Frontend RBAC is presentation-only
- [ ] Backend enforces all security

### ✅ Chat Integration
- [ ] WebSocket connects to `chat/websocket_gateway.py`
- [ ] Message format matches backend `Message` model
- [ ] Streaming works end-to-end
- [ ] Correlation IDs propagate

### ✅ Memory Integration
- [ ] Recall uses backend `memory/manager.py`
- [ ] Search uses `conversation_search_service.py`
- [ ] No client-side memory mutations

### ✅ Capsule Integration
- [ ] List capsules from `capsules/registry.py`
- [ ] Execute via `capsules/orchestrator.py`
- [ ] RBAC enforced for capsule access
- [ ] Status monitoring works

### ✅ Security
- [ ] All content sanitized (`SanitizedMarkdown`)
- [ ] CSP headers configured
- [ ] HTTPS enforced in production
- [ ] No sensitive data in logs

### ✅ Observability
- [ ] Correlation IDs on all requests
- [ ] Performance events tracked
- [ ] Errors reported
- [ ] Health checks configured

### ✅ Testing
- [ ] Endpoint connectivity tests passing
- [ ] RBAC tests passing
- [ ] Chat integration tests passing
- [ ] Accessibility tests passing

### ✅ Deployment
- [ ] Docker build succeeds
- [ ] Health check endpoint working
- [ ] No dev dependencies in production
- [ ] Static assets cached

---

## 📞 Support & Resources

**Backend Documentation:**
- Chat System: `/docs/chat/`
- Capsule System: `/docs/capsules/`

**Frontend Code:**
- Configuration: `/src/lib/endpoint-config.ts`
- Services: `/src/services/`
- Components: `/src/components/`

**Testing:**
- Integration tests: `/__tests__/integration/`
- RBAC tests: `/__tests__/rbac/`

---

**Integration Guide Version:** 1.0.0
**Status:** ✅ Production Specification
**Last Updated:** 2025-11-08
