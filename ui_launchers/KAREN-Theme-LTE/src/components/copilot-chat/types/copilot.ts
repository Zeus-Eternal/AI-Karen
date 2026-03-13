/**
 * Copilot Types
 * Type definitions for Copilot functionality
 */

export interface CopilotState {
  messages: CopilotMessage[];
  isLoading: boolean;
  error: string | null;
  actions: CopilotAction[];
  workflows: CopilotWorkflow[];
  artifacts: CopilotArtifact[];
  memoryOps: Record<string, unknown>;
  activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins';
  inputModality: 'text' | 'code' | 'image' | 'audio';
  availableLNMs: LNMInfo[];
  activeLNM: LNMInfo | null;
  availablePlugins: PluginManifest[];
  securityContext: SecurityContext;
  uiConfig: {
    theme: 'auto' | 'light' | 'dark';
    fontSize: 'small' | 'medium' | 'large';
    showTimestamps: boolean;
    showMemoryOps: boolean;
    showDebugInfo: boolean;
    maxMessageHistory: number;
    enableAnimations: boolean;
    enableSoundEffects: boolean;
    enableKeyboardShortcuts: boolean;
    autoScroll: boolean;
    markdownSupport: boolean;
    codeHighlighting: boolean;
    imagePreview: boolean;
  };
}

export interface CopilotMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    modality?: 'text' | 'code' | 'image' | 'audio';
    intent?: string;
    confidence?: number;
    suggestions?: CopilotSuggestion[];
    actions?: CopilotAction[];
    workflows?: CopilotWorkflow[];
    artifacts?: CopilotArtifact[];
  };
}

export interface CopilotAction {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  category?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotWorkflow {
  id: string;
  title: string;
  description?: string;
  steps?: string[];
  estimatedTime?: number;
  pluginId?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotArtifact {
  id: string;
  title: string;
  type: 'text' | 'code' | 'image' | 'audio' | 'other';
  description?: string;
  content?: unknown;
  pluginId?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotSuggestion {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  action?: string;
}

export interface LNMInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  version?: string;
  size?: number;
  isActive?: boolean;
  isPersonal?: boolean;
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author?: string;
  enabled: boolean;
  capabilities: string[];
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
  config?: {
    parameters?: PluginParameter[];
  };
}

export interface PluginParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  defaultValue?: unknown;
}

export interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'medium' | 'high' | 'critical';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}
