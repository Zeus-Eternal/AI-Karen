// Backend contract types for Copilot integration with KAREN's CORTEX engine
// These types define the contract between frontend UI and backend systems

export interface CopilotBackendConfig {
  baseUrl: string;
  apiKey?: string;               // for non-local deployments / org RBAC
  correlationId?: string;
  userId: string;
  sessionId: string;
}

export interface CopilotInput {
  text: string;
  modality: 'text' | 'code' | 'image' | 'audio';
}

export interface CopilotUIContext {
  viewId: string;
  interfaceMode: string;
  activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts';
}

export interface CopilotSystemContext {
  client: 'web' | 'desktop' | 'mobile';
  capabilities: string[];
}

export interface CopilotBackendRequest {
  input: CopilotInput;
  uiContext: CopilotUIContext;
  systemContext: CopilotSystemContext;
  // This MUST mirror Kari's Prompt-First Integration Framework:
  intentHints?: string[];
  pluginHints?: string[];
}

export interface CopilotAction {
  id: string;
  title: string;
  description: string;
  pluginId: string;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
  requiresConfirmation?: boolean;
  config?: Record<string, unknown>;
}

export interface CopilotWorkflowSummary {
  id: string;
  name: string;
  description: string;
  pluginId: string;
  steps: string[];
  estimatedTime: number;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

export interface CopilotArtifactSummary {
  id: string;
  title: string;
  type: 'code' | 'documentation' | 'analysis' | 'test';
  description: string;
  pluginId: string;
  preview?: string;
  version?: number;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

export interface CopilotMemoryOps {
  reads: number;
  writes: number;
  tier: 'short-term' | 'long-term' | 'persistent' | 'echo-core';
}

export interface CopilotDebugInfo {
  traceId?: string;
  model?: string;
  latencyMs?: number;
  memoryUsage?: {
    shortTerm: number;
    longTerm: number;
    persistent: number;
    echoCore?: number;
  };
  pluginExecution?: {
    pluginId: string;
    executionTime: number;
    success: boolean;
  };
}

export interface CopilotBackendResponse {
  message: string;
  intent: string;
  confidence: number;
  actions: CopilotAction[];
  workflows?: CopilotWorkflowSummary[];
  artifacts?: CopilotArtifactSummary[];
  memoryOps?: CopilotMemoryOps;
  debug?: CopilotDebugInfo;
}

// Memory-related types for integration with KAREN's MemoryManager/NeuroVault
export interface MemoryQuery {
  text: string;
  tier?: 'short-term' | 'long-term' | 'persistent' | 'echo-core';
  limit?: number;
  filters?: {
    dateRange?: {
      start: Date;
      end: Date;
    };
    tags?: string[];
    type?: 'conversation' | 'document' | 'code' | 'analysis';
  };
}

export interface MemoryResult {
  id: string;
  content: string;
  type: 'conversation' | 'document' | 'code' | 'analysis';
  tier: 'short-term' | 'long-term' | 'persistent' | 'echo-core';
  timestamp: Date;
  relevanceScore: number;
  metadata?: Record<string, unknown>;
}

export interface MemoryOperation {
  id: string;
  content: string;
  type: 'conversation' | 'document' | 'code' | 'analysis';
  tier: 'short-term' | 'long-term' | 'persistent' | 'echo-core';
  tags?: string[];
  metadata?: Record<string, unknown>;
}

// Plugin-related types for integration with KAREN's Prompt-First Plugin Engine
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  capabilities: string[];
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
  config?: {
    parameters: Array<{
      name: string;
      type: string;
      description: string;
      required: boolean;
      defaultValue?: unknown;
    }>;
  };
}

export interface PluginExecutionRequest {
  pluginId: string;
  action: string;
  parameters?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface PluginExecutionResponse {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTime: number;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

// LNM (Local Neural Model) related types
export interface LNMInfo {
  id: string;
  name: string;
  description: string;
  version: string;
  size: number;
  capabilities: string[];
  isPersonal: boolean;
  isActive: boolean;
}

export interface LNMSelectionRequest {
  modelId: string;
  context?: {
    conversationId?: string;
    taskType?: string;
  };
}

export interface LNMSelectionResponse {
  success: boolean;
  model?: LNMInfo;
  error?: string;
}

// Security and RBAC related types
export interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'aggressive' | 'evil';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}

// UI Telemetry types for observability
export interface UITelemetryEvent {
  eventName: string;
  properties?: Record<string, unknown>;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
}

export interface PerformanceMetric {
  metricName: string;
  value: number;
  unit?: string;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
}

export interface ErrorReport {
  error: Error;
  context?: Record<string, unknown>;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
  componentStack?: string;
}