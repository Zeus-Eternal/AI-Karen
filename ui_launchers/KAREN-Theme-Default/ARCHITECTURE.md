# Kari UI Architecture Charter

## Table of Contents
1. [Overview](#overview)
2. [Canonical Architecture](#canonical-architecture)
3. [Layer Ownership](#layer-ownership)
4. [Integration Contract](#integration-contract)
5. [Backend API Surface](#backend-api-surface)
6. [Client Abstraction](#client-abstraction)
7. [State Management](#state-management)
8. [Component Architecture](#component-architecture)
9. [Security & Monitoring](#security--monitoring)
10. [Development Guidelines](#development-guidelines)

## Overview

This document defines the canonical architecture for the Kari UI application, establishing clear boundaries and responsibilities for each layer of the system. The architecture follows a strict layered approach to ensure maintainability, testability, and scalability.

## Canonical Architecture

The Kari UI follows a strict layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Pages (app/)                           │
├─────────────────────────────────────────────────────────────┤
│                 Providers/Contexts                         │
├─────────────────────────────────────────────────────────────┤
│                      Hooks                                │
├─────────────────────────────────────────────────────────────┤
│                    Services                               │
├─────────────────────────────────────────────────────────────┤
│                      lib/                                  │
├─────────────────────────────────────────────────────────────┤
│                app/api routes                              │
└─────────────────────────────────────────────────────────────┘
```

## Layer Ownership

### `app/` Layer
**Responsibilities:**
- Route entrypoints (`app/page.tsx`, `app/*/page.tsx`)
- App shell and top-level providers (`app/layout.tsx`, `app/providers*.tsx`)
- All backend HTTP handlers (Next.js route handlers)

**Rules:**
- No business logic in route handlers
- Route handlers only validate input, call services, and format responses
- Providers are composed in `app/providers.tsx` or `contexts/AppProviders.tsx`

### `lib/` Layer
**Responsibilities:**
- Pure logic and infrastructure utilities
- API clients, configuration, logging, security
- Model selection, extension core helpers
- No React components or hooks

**Rules:**
- No framework-specific code
- Pure functions and classes only
- No direct UI-related logic

### `services/` Layer
**Responsibilities:**
- Orchestration of business flows (auth, chat, memory, extensions, plugins)
- Calling into `lib/*` and exposing imperative functions
- No JSX

**Rules:**
- Services are singleton instances
- No direct HTTP calls (use lib layer)
- No UI state management

### `hooks/` Layer
**Responsibilities:**
- React hooks that call `services/`
- Provide UI-friendly state and handlers to components
- Encapsulate business logic for React components

**Rules:**
- Hooks only call services, not lib directly
- No JSX in hooks
- Return state and handler functions only

### `contexts/` & `providers/` Layer
**Responsibilities:**
- React context containers (auth, session, theme, etc.)
- Global state management

**Rules:**
- Contexts are composed in `contexts/AppProviders.tsx`
- No business logic in contexts
- Minimal state management only

### `components/` Layer
**Responsibilities:**
- All UI: domain screens, dashboards, layout, shared UI kit
- Presentation logic only

**Rules:**
- No direct HTTP calls
- Components only talk to hooks/contexts
- No business logic

### `store/` Layer
**Responsibilities:**
- Global state management (Zustand)
- Single source of truth for global UI state

**Rules:**
- All stores must be exported from `store/index.ts`
- No duplicate store folders
- Stores should be minimal and focused

### `types/` Layer
**Responsibilities:**
- All shared TypeScript types
- Domain contracts and API DTO definitions

**Rules:**
- No implementation code
- Type definitions only

## Integration Contract

The standard flow must be enforced everywhere:

```
Page → Providers → Hooks → Services → lib → app/api → backend logic
```

No component should directly import `lib/api-client.ts` or `lib/karen-backend.ts`. They must call hooks/services.

## Backend API Surface

The backend API surface is organized as follows:

### Authentication
- `app/api/auth/login`
- `app/api/auth/logout`
- `app/api/auth/me`
- `app/api/auth/register`
- `app/api/auth/validate-session`

### Admin & Users
- `app/api/admin/*`
- `app/api/users/*`

### Chat & Runtime
- `app/api/chat/route`
- `app/api/chat/proxy/route`
- `app/api/chat/runtime/*`
- `app/api/copilot/start/route`

### Conversations
- `app/api/conversations/*`

### Models & Providers
- `app/api/models/*`
- `app/api/providers/discovery/route`
- `app/api/system/config/models/route`

### Extensions & Plugins
- `app/api/extensions/route`
- `app/api/plugins/route`

### Monitoring & QA
- `app/api/health/route`
- `app/api/metrics/route`
- `app/api/qa/*`
- `app/api/analytics/usage/*`
- `app/api/audit/logs/*`

### Security & System
- `app/api/admin/security/*`
- `app/api/admin/system/*`
- `app/api/system/activity-summary/*`
- `app/api/system/config/*`

## Client Abstraction

The canonical HTTP client is `lib/enhanced-api-client.ts`. All services must use this client for API calls.

### Usage Example
```typescript
import { enhancedApiClient } from '@/lib/enhanced-api-client';

// In a service
export class AuthService {
  async login(email: string, password: string): Promise<User> {
    const response = await enhancedApiClient.post('/api/auth/login', { email, password });
    return response.data;
  }
}
```

## State Management

### Global State
- Use Zustand for global state management
- All stores are in `store/` directory
- Stores are exported through `store/index.ts`

### Local State
- Use React hooks for local component state
- Use React contexts for shared state within component trees

### Example Store
```typescript
// store/chatStore.ts
import { create } from 'zustand';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  // ... state
}

interface ChatActions {
  addMessage: (message: Message) => void;
  // ... actions
}

export const useChatStore = create<ChatState & ChatActions>((set) => ({
  // ... implementation
}));
```

## Component Architecture

### Component Types
1. **Page Components** - Route entry points in `app/`
2. **Layout Components** - Structure and navigation in `components/layout/`
3. **Domain Components** - Business logic components in feature folders
4. **UI Components** - Reusable presentation components in `components/ui/`

### Component Rules
- Components must not make direct API calls
- Components must use hooks for business logic
- Components must be testable in isolation

### Example Component
```typescript
// components/chat/ChatInterface.tsx
import { useChatStore } from '@/store';
import { useChatService } from '@/hooks';

export const ChatInterface: React.FC = () => {
  const { messages } = useChatStore();
  const { sendMessage } = useChatService();

  // Component implementation
};
```

## Security & Monitoring

### Security Service
- Centralized in `services/security/index.ts`
- Handles authentication, authorization, RBAC, MFA, IP security
- Uses enhanced-api-client for all security calls

### Monitoring Service
- Centralized in `services/monitoring/index.ts`
- Handles metrics collection and performance reporting
- Uses admin-performance-monitor for metrics

### Security Rules
- All security logic must go through SecurityService
- No direct security API calls in components
- Use RBAC hooks for permission checks

## Development Guidelines

### File Organization
```
src/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   ├── layout.tsx         # Root layout
│   └── providers.tsx      # App providers
├── components/            # React components
│   ├── layout/           # Layout components
│   ├── ui/               # Reusable UI components
│   └── [feature]/        # Feature-specific components
├── contexts/              # React contexts
├── hooks/                 # Custom React hooks
├── lib/                   # Pure logic utilities
├── services/              # Business logic services
├── store/                 # Zustand stores
├── types/                 # TypeScript types
└── utils/                 # Utility functions
```

### Naming Conventions
- Files: `kebab-case.ts` or `kebab-case.tsx`
- Components: `PascalCase`
- Hooks: `useCamelCase`
- Services: `CamelCaseService`
- Stores: `camelCaseStore`
- Types: `PascalCase`

### Import Order
```typescript
// 1. React and framework imports
import React from 'react';
import { NextPage } from 'next';

// 2. Third-party libraries
import { create } from 'zustand';

// 3. Internal imports (absolute paths)
import { useChatStore } from '@/store';
import { ChatService } from '@/services';

// 4. Relative imports
import { LocalComponent } from './LocalComponent';

// 5. Types
import type { Message } from '@/types';
```

### Testing
- All services must have unit tests
- All hooks must have unit tests
- All components must have unit tests
- Integration tests for critical flows
- Test files must be in `__tests__/` directories

### Code Quality
- TypeScript strict mode enabled
- ESLint with accessibility rules
- Prettier for formatting
- No console.log in production code

## Conclusion

This architecture charter establishes a clear, maintainable structure for the Kari UI application. By following these guidelines, we ensure:

1. **Consistency** - All code follows the same patterns
2. **Maintainability** - Clear separation of concerns
3. **Testability** - Each layer can be tested independently
4. **Scalability** - Architecture supports future growth
5. **Developer Experience** - New developers can easily understand the codebase

All team members must adhere to this architecture charter to maintain the quality and consistency of the Kari UI application.