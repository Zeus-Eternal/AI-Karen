# Kari Copilot-First Unified Chat Surface (CORTEX Frontline UI)

## Overview

This document outlines the implementation plan for a Copilot-First Unified Chat Surface that serves as the frontline UI for KAREN's CORTEX (intent + routing + reasoning) engine. This implementation positions Copilot not as a UI helper, but as the UI gateway to the entire KAREN engine, including MemoryManager/NeuroVault, Prompt-First Plugin Engine, and other core systems.

## Vision: Copilot as CORTEX Frontline UI

Our vision is to create a chat interface where Copilot serves as the frontline embodiment of:

* **CORTEX** (intent + routing + reasoning)
* **MemoryManager / NeuroVault** (Redis + Milvus + DuckDB + Postgres + EchoCore)
* **Prompt-First Plugin Engine** (manifest + prompt + handler)

The UI will be a thin, intelligent layer that exposes the power of these backend systems through a cohesive, adaptive interface.

## Architecture: Frontend-Backend Contract

### Core Principle: UI as Gateway, Not Brain

The frontend Copilot components will not implement business logic or reasoning. Instead, they will:

1. **Collect Context**: Gather UI state, user inputs, and system context
2. **Gateway to Backend**: Send structured requests to KAREN's CORTEX engine
3. **Render Responses**: Display the intelligent responses from the backend
4. **Facilitate Interactions**: Enable user interactions that trigger backend workflows

### Backend Contract: CopilotGateway

```typescript
// src/components/copilot-chat/services/copilotGateway.ts

export interface CopilotBackendConfig {
  baseUrl: string;
  apiKey?: string;               // for non-local deployments / org RBAC
  correlationId?: string;
  userId: string;
  sessionId: string;
}

export interface CopilotBackendRequest {
  input: {
    text: string;
    modality: 'text' | 'code' | 'image' | 'audio';
  };
  uiContext: {
    viewId: string;
    interfaceMode: string;
    activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts';
  };
  systemContext: {
    client: 'web' | 'desktop' | 'mobile';
    capabilities: string[];
  };
  // This MUST mirror Kari's Prompt-First Integration Framework:
  intentHints?: string[];
  pluginHints?: string[];
}

export interface CopilotBackendResponse {
  message: string;
  intent: string;
  confidence: number;
  actions: CopilotAction[];
  workflows?: CopilotWorkflowSummary[];
  artifacts?: CopilotArtifactSummary[];
  memoryOps?: {
    reads: number;
    writes: number;
  };
  debug?: {
    traceId?: string;
    model?: string;
    latencyMs?: number;
  };
}

export class CopilotGateway {
  constructor(private config: CopilotBackendConfig) {}

  async send(request: CopilotBackendRequest): Promise<CopilotBackendResponse> {
    const res = await fetch(`${this.config.baseUrl}/api/copilot/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey ? { Authorization: `Bearer ${this.config.apiKey}` } : {}),
        ...(this.config.correlationId ? { 'X-Correlation-ID': this.config.correlationId } : {}),
        'X-Kari-User-ID': this.config.userId,
        'X-Kari-Session-ID': this.config.sessionId,
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      throw new Error(`Copilot backend error: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as CopilotBackendResponse;
  }
}
```

## Directory Structure

```
src/
  ai/
    copilot/                     # UI + engine contract
      core/
        CopilotEngine.tsx        # FE orchestrator (talks to backend only)
        AdaptiveInterface.tsx      # UI adaptation based on backend response
        ContextBridge.tsx        # maps UI context -> backend EnhancedContext
      services/
        copilotGateway.ts        # 🔺 bridge to FastAPI / chat runtime
        uiTelemetryClient.ts     # sends Prometheus-friendly events
      hooks/
        useCopilot.ts
        useCopilotSuggestions.ts
      types/
        copilot.ts
        backend.ts

  components/
    copilot-chat/
      CopilotChatInterface.tsx   # main shell
      IntelligentAssistant.tsx    # renders backend-suggested actions
      WorkflowAutomation.tsx      # renders backend-provided workflows
      ArtifactSystem.tsx         # renders backend-generated artifacts
      ContextualToolbar.tsx      # toolbar based on backend context
      MultiModalInput.tsx        # input that captures multiple modalities
      MemoryPanel.tsx           # UI for memory management
      PluginDiscovery.tsx        # UI for plugin discovery
      LNMSelector.tsx           # UI for LNM selection

backend/
  ai_karen_engine/
    chat/
      chat_orchestrator.py
      context_integrator.py
      tool_integration_service.py
      memory_processor.py
      production_memory.py
      stream_processor.py
    plugins/
      # prompt-first plugin folders
    memory/
      memory_manager.py
      neurovault_bridge.py
    observability/
      prometheus_metrics.py
      audit_logger.py
```

## Implementation Phases

### Phase 1: Copilot Gateway and Backend Contract (2 days)

**Goals:**
- Create the CopilotGateway service for backend communication
- Define the contract between frontend and KAREN's CORTEX engine
- Implement basic request/response handling

**Tasks:**
1. Create `CopilotGateway` service with backend contract
2. Define TypeScript interfaces for request/response types
3. Implement error handling and retry logic
4. Add telemetry and correlation ID support

**Key Files:**
- `src/ai/copilot/services/copilotGateway.ts`
- `src/ai/copilot/types/backend.ts`
- `src/ai/copilot/types/copilot.ts`

### Phase 2: Core Copilot Engine (3 days)

**Goals:**
- Create the CopilotEngine as a frontend orchestrator
- Implement ContextBridge to map UI context to backend format
- Create the main CopilotChatInterface shell

**Tasks:**
1. Create `CopilotEngine` as frontend orchestrator
2. Implement `ContextBridge` for UI-to-backend context mapping
3. Create main `CopilotChatInterface` shell component
4. Add error boundaries and loading states

**Key Files:**
- `src/ai/copilot/core/CopilotEngine.tsx`
- `src/ai/copilot/core/ContextBridge.tsx`
- `src/components/copilot-chat/CopilotChatInterface.tsx`

### Phase 3: Intelligent Assistant UI (3 days)

**Goals:**
- Create UI components that render backend-suggested actions
- Implement context-aware suggestions from backend
- Add plugin-aware action display

**Tasks:**
1. Create `IntelligentAssistant` component
2. Implement context-aware suggestion display
3. Add plugin-aware action rendering
4. Integrate with CopilotEngine

**Key Files:**
- `src/components/copilot-chat/IntelligentAssistant.tsx`
- `src/ai/copilot/hooks/useCopilotSuggestions.ts`
- `src/components/copilot-chat/ContextualToolbar.tsx`

### Phase 4: Memory Management UI (2 days)

**Goals:**
- Create UI for managing memory tiers (short-term, long-term, persistent)
- Implement memory pinning and forgetting
- Add LNM selection UI

**Tasks:**
1. Create `MemoryPanel` component
2. Implement memory tier controls
3. Add LNM selection interface
4. Integrate with backend memory operations

**Key Files:**
- `src/components/copilot-chat/MemoryPanel.tsx`
- `src/components/copilot-chat/LNMSelector.tsx`
- `src/ai/copilot/hooks/useCopilotMemory.ts`

### Phase 5: Workflow Automation UI (2 days)

**Goals:**
- Create UI for backend-provided workflows
- Implement workflow execution interface
- Add workflow discovery and triggering

**Tasks:**
1. Create `WorkflowAutomation` component
2. Implement workflow execution UI
3. Add workflow discovery interface
4. Integrate with backend workflow endpoints

**Key Files:**
- `src/components/copilot-chat/WorkflowAutomation.tsx`
- `src/ai/copilot/hooks/useCopilotWorkflows.ts`

### Phase 6: Artifact System UI (2 days)

**Goals:**
- Create UI for backend-generated artifacts
- Implement artifact preview and version control
- Add collaborative features

**Tasks:**
1. Create `ArtifactSystem` component
2. Implement artifact preview interface
3. Add version control and collaboration
4. Integrate with backend artifact endpoints

**Key Files:**
- `src/components/copilot-chat/ArtifactSystem.tsx`
- `src/ai/copilot/hooks/useCopilotArtifacts.ts`

### Phase 7: Plugin Discovery UI (2 days)

**Goals:**
- Create UI for plugin discovery and management
- Implement plugin installation and configuration
- Add plugin marketplace interface

**Tasks:**
1. Create `PluginDiscovery` component
2. Implement plugin installation UI
3. Add plugin configuration interface
4. Integrate with backend plugin endpoints

**Key Files:**
- `src/components/copilot-chat/PluginDiscovery.tsx`
- `src/ai/copilot/hooks/useCopilotPlugins.ts`

### Phase 8: Adaptive Interface System (2 days)

**Goals:**
- Create interface that adapts based on backend suggestions
- Implement policy-based UI adaptation
- Add user expertise level adjustments

**Tasks:**
1. Create `AdaptiveInterface` component
2. Implement policy-based UI adaptation
3. Add user expertise level adjustments
4. Integrate with backend adaptation endpoints

**Key Files:**
- `src/ai/copilot/core/AdaptiveInterface.tsx`
- `src/ai/copilot/hooks/useAdaptiveInterface.ts`

### Phase 9: Multi-Modal Input (2 days)

**Goals:**
- Create input component that supports multiple modalities
- Implement text, code, image, and audio input
- Add modality switching and preview

**Tasks:**
1. Create `MultiModalInput` component
2. Implement multi-modality support
3. Add modality switching and preview
4. Integrate with backend input endpoints

**Key Files:**
- `src/components/copilot-chat/MultiModalInput.tsx`
- `src/ai/copilot/hooks/useMultiModalInput.ts`

### Phase 10: Integration and Polish (3 days)

**Goals:**
- Integrate all components into main interface
- Implement performance optimizations
- Add comprehensive testing
- Create documentation

**Tasks:**
1. Finalize `CopilotChatInterface` integration
2. Implement performance optimizations
3. Add comprehensive testing
4. Create documentation and examples

**Key Files:**
- `src/components/copilot-chat/CopilotChatInterface.tsx` (final)
- `src/components/copilot-chat/README.md`
- `src/components/copilot-chat/__tests__/` (all test files)

## Key Implementation Details

### Prompt-First Integration

The frontend will support KAREN's Prompt-First Plugin Engine by:

1. **Plugin-Aware Actions**: All actions will reference backend plugins
2. **Intent Hints**: UI will send intent hints to backend for better routing
3. **Plugin Hints**: UI will suggest relevant plugins based on context

```typescript
const sendToCopilot = async (input: string) => {
  const request: CopilotBackendRequest = {
    input: {
      text: input,
      modality: 'text',
    },
    uiContext: {
      viewId: currentView,
      interfaceMode: getInterfaceMode(),
      activePanel: getActivePanel(),
    },
    systemContext: {
      client: 'web',
      capabilities: getSystemCapabilities(),
    },
    intentHints: getIntentHints(input),
    pluginHints: getPluginHints(input),
  };
  
  const response = await copilotGateway.send(request);
  // Render response
};
```

### Memory Tier Integration

The UI will expose KAREN's multi-tier memory system:

1. **Short-Term (Redis)**: Current conversation context
2. **Long-Term (Milvus+DuckDB)**: Semantic search and retrieval
3. **Persistent (Postgres+Milvus)**: Long-term storage
4. **EchoCore Shadow/Vault**: Admin/power-user mode access

```typescript
interface MemoryPanelProps {
  shortTerm: ShortTermMemory[];
  longTerm: LongTermMemory[];
  persistent: PersistentMemory[];
  echoCore?: EchoCoreMemory; // Only for admin/power users
  onMemoryAction: (action: MemoryAction) => void;
}
```

### LNM (Local Neural Model) Integration

The UI will support LNM selection and usage:

1. **Model Selection**: Choose between global and personal models
2. **Usage Indication**: Show which model is being used
3. **Comparison Mode**: Compare responses between models

```typescript
interface LNMSelectorProps {
  globalModel: ModelInfo;
  personalModel?: ModelInfo;
  activeModel: 'global' | 'personal';
  onModelChange: (model: 'global' | 'personal') => void;
  onCompare?: () => void;
}
```

### RBAC and Security Integration

The UI will respect KAREN's security model:

1. **Role-Based Actions**: Show/hide actions based on user roles
2. **Safe vs Evil Mode**: Adjust UI based on security mode
3. **Sensitive Context Redaction**: Handle sensitive data appropriately

```typescript
interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'aggressive' | 'evil';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}
```

### Observability Integration

The UI will send telemetry to KAREN's observability systems:

1. **UI Telemetry**: Send user interaction events
2. **Performance Metrics**: Track UI performance
3. **Error Reporting**: Report UI errors with context

```typescript
class UITelemetryClient {
  trackEvent(event: string, properties?: Record<string, unknown>): void {
    // Send to Prometheus-friendly endpoint
  }
  
  trackError(error: Error, context?: Record<string, unknown>): void {
    // Send to error tracking endpoint
  }
  
  trackPerformance(metric: string, value: number): void {
    // Send to metrics endpoint
  }
}
```

## Testing Strategy

### Frontend Testing

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Contract Tests**: Test backend contract compliance
4. **E2E Tests**: Test full user scenarios

### Backend Integration Testing

1. **Contract Tests**: Ensure frontend requests match backend expectations
2. **Error Scenarios**: Test handling of backend errors
3. **Performance Tests**: Test with various latency profiles

### Security Testing

1. **RBAC Testing**: Verify role-based UI behavior
2. **Redaction Testing**: Verify sensitive data handling
3. **Mode Testing**: Verify safe/aggressive/evil mode behavior

## Success Metrics

The Copilot-First Unified Chat Surface will be measured by:

1. **Backend Integration**: 100% of backend features exposed through UI
2. **User Engagement**: Increased interaction with advanced features
3. **Task Completion**: Improved completion rates for complex tasks
4. **Plugin Usage**: Increased usage of prompt-first plugins
5. **Memory Interaction**: User engagement with memory tiers
6. **Performance**: Sub-100ms response times for all UI interactions

## Conclusion

This Copilot-First Unified Chat Surface will serve as the frontline UI for KAREN's CORTEX engine, exposing the power of MemoryManager/NeuroVault, Prompt-First Plugin Engine, and other core systems through a cohesive, adaptive interface.

By positioning Copilot as the UI gateway rather than a separate intelligence layer, we ensure that all smart behavior comes from KAREN's backend systems, while the frontend focuses on providing an intuitive, responsive user experience.

The key to success will be maintaining clear boundaries between frontend UI concerns and backend intelligence, ensuring that the frontend serves as an effective window into KAREN's powerful capabilities.