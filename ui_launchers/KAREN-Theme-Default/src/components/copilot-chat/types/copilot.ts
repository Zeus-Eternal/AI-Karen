// Frontend types for Copilot UI components and state management
// These types define the frontend-facing data structures used by React components

// Import backend types for convenience
import {
  CopilotAction,
  CopilotWorkflowSummary,
  CopilotArtifactSummary,
  CopilotMemoryOps,
  LNMInfo,
  PluginManifest,
  SecurityContext
} from '../../../ai/copilot/types/backend';

// Re-export backend types for convenience
export type {
  CopilotAction,
  CopilotWorkflowSummary,
  CopilotArtifactSummary,
  CopilotMemoryOps,
  LNMInfo,
  PluginManifest,
  SecurityContext
} from '../../../ai/copilot/types/backend';

// UI State Management Types
export interface CopilotState {
  messages: CopilotMessage[];
  isLoading: boolean;
  error: CopilotError | null;
  actions: CopilotAction[];
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
    suggestions?: CopilotSuggestion[];
    actions?: CopilotAction[];
    workflows?: CopilotWorkflowSummary[];
    artifacts?: CopilotArtifactSummary[];
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

// Enhanced Context Types
export interface EnhancedContext {
  // User context
  user: {
    profile: UserProfile;
    preferences: UserPreferences;
    expertise: ExpertiseLevel;
    history: UserHistory;
    currentTask?: CurrentTask;
  };
  
  // Conversation context
  conversation: {
    messages: CopilotMessage[];
    semantics: ConversationSemantics;
    topics: Topic[];
    intent: ConversationIntent;
    complexity: ComplexityLevel;
  };
  
  // System context
  system: {
    capabilities: SystemCapabilities;
    currentView: CurrentView;
    availableActions: AvailableActions[];
    performance: SystemPerformance;
  };
  
  // External context
  external: {
    documents: ExternalDocument[];
    apis: ExternalAPI[];
    integrations: Integration[];
    realTimeData: RealTimeData;
  };
  
  // Semantic context
  semantic: {
    entities: Entity[];
    relationships: Relationship[];
    knowledgeGraph: KnowledgeGraph;
    embeddings: Embedding[];
  };
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  roles: string[];
  expertiseLevel: ExpertiseLevel;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  fontSize: 'small' | 'medium' | 'large';
  language: string;
  timezone: string;
  notifications: boolean;
  privacy: PrivacySettings;
}

export interface PrivacySettings {
  dataCollection: boolean;
  personalizedResponses: boolean;
  shareAnalytics: boolean;
  rememberHistory: boolean;
}

export interface UserHistory {
  recentConversations: ConversationSummary[];
  commonIntents: IntentCount[];
  preferredActions: ActionCount[];
  skillLevel: SkillAssessment;
}

export interface ConversationSummary {
  id: string;
  title: string;
  timestamp: Date;
  messageCount: number;
  topics: string[];
}

export interface IntentCount {
  intent: string;
  count: number;
}

export interface ActionCount {
  action: string;
  count: number;
}

export interface SkillAssessment {
  technical: number; // 0-100
  creative: number; // 0-100
  analytical: number; // 0-100
  communication: number; // 0-100
}

export interface CurrentTask {
  id: string;
  type: 'coding' | 'writing' | 'analysis' | 'planning' | 'debugging';
  description: string;
  startTime: Date;
  progress: number; // 0-100
  relatedArtifacts?: string[];
  relatedWorkflows?: string[];
}

export interface ConversationSemantics {
  sentiment: 'positive' | 'neutral' | 'negative';
  urgency: 'low' | 'medium' | 'high' | 'critical';
  complexity: 'simple' | 'moderate' | 'complex';
  domain: string[];
  keywords: string[];
}

export interface Topic {
  id: string;
  label: string;
  confidence: number; // 0-1
  relatedTopics: string[];
}

export interface ConversationIntent {
  primary: string;
  secondary?: string;
  confidence: number; // 0-1
  entities: Entity[];
}

export interface ComplexityLevel {
  level: 'basic' | 'intermediate' | 'advanced' | 'expert';
  factors: string[];
  score: number; // 0-100
}

export interface SystemCapabilities {
  modalities: ('text' | 'code' | 'image' | 'audio')[];
  plugins: string[];
  actions: string[];
  workflows: string[];
  artifacts: string[];
  memoryTiers: ('short-term' | 'long-term' | 'persistent' | 'echo-core')[];
}

export interface CurrentView {
  id: string;
  type: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins';
  focus: string;
  context: string;
}

export interface AvailableActions {
  id: string;
  name: string;
  description: string;
  category: string;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

export interface SystemPerformance {
  cpu: number; // 0-100
  memory: number; // 0-100
  network: number; // 0-100
  responseTime: number; // ms
}

export interface ExternalDocument {
  id: string;
  title: string;
  type: 'documentation' | 'code' | 'reference' | 'example';
  source: string;
  relevance: number; // 0-1
  lastAccessed: Date;
}

export interface ExternalAPI {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  authType: 'none' | 'api-key' | 'oauth' | 'bearer';
  rateLimit?: {
    requests: number;
    window: string;
  };
}

export interface Integration {
  id: string;
  name: string;
  type: 'plugin' | 'service' | 'data-source';
  status: 'connected' | 'disconnected' | 'error';
  lastUsed: Date;
}

export interface RealTimeData {
  sources: DataSource[];
  lastUpdate: Date;
  freshness: 'fresh' | 'stale' | 'outdated';
}

export interface DataSource {
  id: string;
  name: string;
  type: 'feed' | 'stream' | 'poll';
  status: 'active' | 'inactive' | 'error';
}

export interface Entity {
  id: string;
  label: string;
  type: 'person' | 'place' | 'organization' | 'concept' | 'event';
  confidence: number; // 0-1
  mentions: number;
  context: string;
}

export interface Relationship {
  from: string; // entity id
  to: string; // entity id
  type: 'related' | 'depends-on' | 'part-of' | 'similar-to';
  strength: number; // 0-1
  context: string;
}

export interface KnowledgeGraph {
  nodes: Entity[];
  edges: Relationship[];
  metadata: {
    lastUpdate: Date;
    nodeCount: number;
    edgeCount: number;
  };
}

export interface Embedding {
  id: string;
  vector: number[];
  metadata: Record<string, unknown>;
  timestamp: Date;
}

// Copilot Suggestions Types
export interface CopilotSuggestion {
  id: string;
  type: 'action' | 'response' | 'workflow' | 'artifact' | 'setting';
  title: string;
  description: string;
  confidence: number; // 0-1
  priority: 'low' | 'medium' | 'high';
  data?: {
    id?: string;
    type?: 'code' | 'test' | 'documentation' | 'analysis';
    [key: string]: unknown;
  }; // Additional data specific to suggestion type
}

// Component Props Types
export interface CopilotChatInterfaceProps {
  initialState?: Partial<CopilotState>;
  backendConfig: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  };
  expertiseLevel?: ExpertiseLevel;
  className?: string;
}

export interface IntelligentAssistantProps {
  suggestions: CopilotSuggestion[];
  onSelectSuggestion: (suggestion: CopilotSuggestion) => void;
  className?: string;
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
  setBackendConfig: (config: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  }) => void;
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
  setBackendConfig: (config: {
    baseUrl: string;
    apiKey?: string;
    userId: string;
    sessionId: string;
  }) => void;
}

// Event Types
export type CopilotEvent = 
  | { type: 'message_sent'; payload: { message: string; modality: 'text' | 'code' | 'image' | 'audio' } }
  | { type: 'message_received'; payload: { message: CopilotMessage } }
  | { type: 'response_received'; payload: { response: unknown } }
  | { type: 'action_executed'; payload: { action: CopilotAction; result: unknown } }
  | { type: 'workflow_executed'; payload: { workflow: CopilotWorkflowSummary; result: unknown } }
  | { type: 'artifact_opened'; payload: { artifact: CopilotArtifactSummary; content: string } }
  | { type: 'panel_changed'; payload: { panel: 'chat' | 'memory' | 'workflows' | 'artifacts' | 'plugins' } }
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
  | { type: 'engine_initialized'; payload: { context: EnhancedContext } }
  | { type: 'error_occurred'; payload: { error: CopilotError } };

// UI Adaptation Types
export type ExpertiseLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

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

// Processing Strategy Types
export interface ProcessingStrategy {
  type: 'creative' | 'analytical' | 'workflow' | 'conversational' | 'default';
  confidence: number; // 0-1
  reasoning: string;
}

// Input Enrichment Types
export interface EnrichedInput {
  original: string;
  modality: 'text' | 'code' | 'image' | 'audio';
  semantics: {
    intent: string;
    entities: Entity[];
    sentiment: 'positive' | 'neutral' | 'negative';
    urgency: 'low' | 'medium' | 'high' | 'critical';
  };
  userContext: {
    expertise: ExpertiseLevel;
    preferences: UserPreferences;
    history: UserHistory;
  };
  conversationContext: {
    recentMessages: CopilotMessage[];
    currentTopic: string;
    complexity: ComplexityLevel;
  };
  systemContext: {
    capabilities: SystemCapabilities;
    performance: SystemPerformance;
  };
}

// Response Enhancement Types
export interface EnhancedResponse {
  message: string;
  intent: string;
  confidence: number;
  suggestions: CopilotSuggestion[];
  actions: CopilotAction[];
  workflows: CopilotWorkflowSummary[];
  artifacts: CopilotArtifactSummary[];
  memoryOps?: CopilotMemoryOps;
}

/**
 * Intelligence Feature
 */
export interface IntelligenceFeature {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  priority: number;
}

/**
 * Copilot Workflow
 */
export interface CopilotWorkflow {
  id: string;
  title: string;
  description: string;
  steps: string[];
  estimatedTime: string;
  complexity: 'basic' | 'intermediate' | 'advanced' | 'expert';
  metadata: Record<string, unknown>;
}

/**
 * Copilot Artifact
 */
export interface CopilotArtifact {
  id: string;
  title: string;
  description: string;
  type: 'code' | 'documentation' | 'analysis' | 'test' | 'other';
  content: string;
  language: string;
  metadata: Record<string, unknown>;
}

/**
 * Copilot Plugin
 */
export interface CopilotPlugin {
  id: string;
  name: string;
  description: string;
  version: string;
  enabled: boolean;
  dependencies?: string[];
  config?: Record<string, unknown>;
}