// Frontend types for Copilot UI components and state management
// These types define the frontend-facing data structures used by React components

import {
  CopilotAction,
  CopilotWorkflowSummary,
  CopilotArtifactSummary,
  CopilotMemoryOps,
  LNMInfo,
  PluginManifest,
  SecurityContext
} from './backend';

// Import the new Copilot-first types
import { CopilotSuggestion } from '../../../components/copilot-chat/types/copilot';

// Re-export backend types for convenience
export type {
  CopilotAction,
  CopilotWorkflowSummary,
  CopilotArtifactSummary,
  CopilotMemoryOps,
  LNMInfo,
  PluginManifest,
  SecurityContext
} from './backend';

// UI State Management Types
export interface CopilotState {
  messages: CopilotMessage[];
  isLoading: boolean;
  error: CopilotError | null;
  actions: CopilotAction[];
  suggestions: CopilotSuggestion[];
  workflows: CopilotWorkflowSummary[];
  artifacts: CopilotArtifactSummary[];
  memoryOps: CopilotMemoryOps | null;
  activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins';
  inputModality: 'text' | 'code' | 'image' | 'audio';
  availableLNMs: LNMInfo[];
  activeLNM: LNMInfo | null;
  availablePlugins: PluginManifest[];
  securityContext: SecurityContext;
  uiConfig: CopilotUIConfig;
}

export interface CopilotMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    modality?: 'text' | 'code' | 'image' | 'audio';
    pluginId?: string;
    artifactId?: string;
    workflowId?: string;
    intent?: string;
    confidence?: number;
    memoryOps?: CopilotMemoryOps;
  };
}

export interface CopilotError {
  id: string;
  message: string;
  severity: 'warning' | 'error' | 'critical';
  timestamp: Date;
  details?: unknown;
  retryable: boolean;
}

// UI Configuration Types
export interface CopilotUIConfig {
  theme: 'light' | 'dark' | 'auto';
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
}

// Component Props Types
export interface CopilotChatInterfaceProps {
  state: CopilotState;
  onSendMessage: (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => void;
  onExecuteAction: (action: CopilotAction) => void;
  onExecuteWorkflow: (workflow: CopilotWorkflowSummary) => void;
  onOpenArtifact: (artifact: CopilotArtifactSummary) => void;
  onChangePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts') => void;
  onChangeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  onSelectLNM: (lnm: LNMInfo) => void;
  onTogglePlugin: (plugin: PluginManifest, enabled: boolean) => void;
  onUpdateUIConfig: (config: Partial<CopilotUIConfig>) => void;
  onClearError: (errorId: string) => void;
  onRetry: (lastMessageId: string) => void;
  onDismissAction: (actionId: string) => void;
  onDismissWorkflow: (workflowId: string) => void;
  onDismissArtifact: (artifactId: string) => void;
}

export interface CopilotMessageListProps {
  messages: CopilotMessage[];
  isLoading: boolean;
  autoScroll: boolean;
  showTimestamps: boolean;
  showMemoryOps: boolean;
  showDebugInfo: boolean;
  markdownSupport: boolean;
  codeHighlighting: boolean;
  imagePreview: boolean;
  onRetry?: (messageId: string) => void;
  onOpenArtifact?: (artifactId: string) => void;
  onExecuteAction?: (action: CopilotAction) => void;
}

export interface CopilotInputAreaProps {
  inputModality: 'text' | 'code' | 'image' | 'audio';
  isLoading: boolean;
  availableLNMs: LNMInfo[];
  activeLNM: LNMInfo | null;
  onSendMessage: (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => void;
  onChangeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  onSelectLNM: (lnm: LNMInfo) => void;
  onAttachFile?: (file: File) => void;
  onRecordAudio?: () => void;
  onCaptureImage?: () => void;
}

export interface CopilotActionsPanelProps {
  actions: CopilotAction[];
  onExecuteAction: (action: CopilotAction) => void;
  onDismissAction: (actionId: string) => void;
  securityContext: SecurityContext;
}

export interface CopilotWorkflowsPanelProps {
  workflows: CopilotWorkflowSummary[];
  onExecuteWorkflow: (workflow: CopilotWorkflowSummary) => void;
  onDismissWorkflow: (workflowId: string) => void;
  securityContext: SecurityContext;
}

export interface CopilotArtifactsPanelProps {
  artifacts: CopilotArtifactSummary[];
  onOpenArtifact: (artifact: CopilotArtifactSummary) => void;
  onDismissArtifact: (artifactId: string) => void;
  securityContext: SecurityContext;
}

export interface CopilotMemoryPanelProps {
  messages: CopilotMessage[];
  memoryOps: CopilotMemoryOps | null;
  onQueryMemory: (query: string) => void;
  onPinMemory: (messageId: string) => void;
  onForgetMemory: (messageId: string) => void;
  securityContext: SecurityContext;
}

export interface CopilotSettingsPanelProps {
  config: CopilotUIConfig;
  availableLNMs: LNMInfo[];
  activeLNM: LNMInfo | null;
  availablePlugins: PluginManifest[];
  securityContext: SecurityContext;
  onUpdateConfig: (config: Partial<CopilotUIConfig>) => void;
  onSelectLNM: (lnm: LNMInfo) => void;
  onTogglePlugin: (plugin: PluginManifest, enabled: boolean) => void;
}

export interface CopilotErrorDisplayProps {
  error: CopilotError;
  onClearError: (errorId: string) => void;
  onRetry?: () => void;
}

// Hook Types
export interface UseCopilotStateProps {
  initialState?: Partial<CopilotState>;
  backendConfig: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
}

export interface UseCopilotStateReturn {
  state: CopilotState;
  sendMessage: (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => Promise<void>;
  executeAction: (action: CopilotAction) => Promise<void>;
  executeWorkflow: (workflow: CopilotWorkflowSummary) => Promise<void>;
  openArtifact: (artifact: CopilotArtifactSummary) => Promise<void>;
  changePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') => void;
  changeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  selectLNM: (lnm: LNMInfo) => Promise<void>;
  togglePlugin: (plugin: PluginManifest, enabled: boolean) => Promise<void>;
  updateUIConfig: (config: Partial<CopilotUIConfig>) => void;
  clearError: (errorId: string) => void;
  retry: (lastMessageId: string) => Promise<void>;
  dismissAction: (actionId: string) => void;
  dismissWorkflow: (workflowId: string) => void;
  dismissArtifact: (artifactId: string) => void;
  refreshState: () => Promise<void>;
}

// Context Types
export interface CopilotContextValue {
  state: CopilotState;
  sendMessage: (message: string, modality?: 'text' | 'code' | 'image' | 'audio') => Promise<void>;
  executeAction: (action: CopilotAction) => Promise<void>;
  executeWorkflow: (workflow: CopilotWorkflowSummary) => Promise<void>;
  openArtifact: (artifact: CopilotArtifactSummary) => Promise<void>;
  changePanel: (panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins') => void;
  changeModality: (modality: 'text' | 'code' | 'image' | 'audio') => void;
  selectLNM: (lnm: LNMInfo) => Promise<void>;
  togglePlugin: (plugin: PluginManifest, enabled: boolean) => Promise<void>;
  updateUIConfig: (config: Partial<CopilotUIConfig>) => void;
  clearError: (errorId: string) => void;
  retry: (lastMessageId: string) => Promise<void>;
  dismissAction: (actionId: string) => void;
  dismissWorkflow: (workflowId: string) => void;
  dismissArtifact: (artifactId: string) => void;
  refreshState: () => Promise<void>;
}

// Event Types
export type CopilotEvent = 
  | { type: 'message_sent'; payload: { message: string; modality: 'text' | 'code' | 'image' | 'audio' } }
  | { type: 'message_received'; payload: { message: CopilotMessage } }
  | { type: 'action_executed'; payload: { action: CopilotAction } }
  | { type: 'workflow_executed'; payload: { workflow: CopilotWorkflowSummary } }
  | { type: 'artifact_opened'; payload: { artifact: CopilotArtifactSummary } }
  | { type: 'panel_changed'; payload: { panel: 'chat' | 'memory' | 'workflows' | 'artifacts' } }
  | { type: 'modality_changed'; payload: { modality: 'text' | 'code' | 'image' | 'audio' } }
  | { type: 'lnm_selected'; payload: { lnm: LNMInfo } }
  | { type: 'plugin_toggled'; payload: { plugin: PluginManifest; enabled: boolean } }
  | { type: 'ui_config_updated'; payload: { config: Partial<CopilotUIConfig> } }
  | { type: 'error_cleared'; payload: { errorId: string } }
  | { type: 'retry_triggered'; payload: { messageId: string } }
  | { type: 'action_dismissed'; payload: { actionId: string } }
  | { type: 'workflow_dismissed'; payload: { workflowId: string } }
  | { type: 'artifact_dismissed'; payload: { artifactId: string } }
  | { type: 'state_refreshed' }
  | { type: 'error_occurred'; payload: { error: CopilotError } };

// UI Adaptation Types
export type UserExpertiseLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export interface UIAdaptationPolicy {
  name: string;
  description: string;
  simplifiedUI: boolean;
  guidedMode: boolean;
  showAdvancedFeatures: boolean;
  showDebugInfo: boolean;
  showMemoryOps: boolean;
  maxMessageHistory: number;
  enableAnimations: boolean;
  enableSoundEffects: boolean;
  enableKeyboardShortcuts: boolean;
  autoScroll: boolean;
  markdownSupport: boolean;
  codeHighlighting: boolean;
  imagePreview: boolean;
}