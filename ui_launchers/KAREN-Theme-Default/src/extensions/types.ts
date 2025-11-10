/** Core types for the hierarchical extension management system */

// Base extension interface
export interface ExtensionBase {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  category: string;
  icon?: string;
  tags?: string[];
  dependencies?: string[];
  createdAt: string;
  updatedAt: string;
}

// Resource usage tracking
export interface ResourceUsage {
  cpu: number; // percentage
  memory: number; // MB
  network: number; // KB/s
  storage: number; // MB
  responseTime?: number; // ms
}

// Health status
export interface HealthStatus {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  message?: string;
  lastCheck: string;
  uptime?: number;
}

// Lifecycle information
export interface LifecycleInfo {
  status: 'installed' | 'enabled' | 'disabled' | 'updating' | 'error';
  installDate: string;
  lastUpdate?: string;
  updateAvailable?: boolean;
}

// Authentication configuration
export interface AuthConfig {
  type: 'api_key' | 'oauth' | 'none';
  required: boolean;
  configured: boolean;
  fields?: AuthField[];
}

export interface AuthField {
  key: string;
  label: string;
  type: 'text' | 'password' | 'url';
  required: boolean;
  placeholder?: string;
}

// Endpoint configuration
export interface EndpointConfig {
  base_url: string;
  endpoints: Record<string, string>;
  timeout?: number;
  retries?: number;
}

// Extension setting
export interface ExtensionSetting {
  key: string;
  label: string;
  description?: string;
  type: 'number' | 'string' | 'boolean' | 'select' | 'multiselect';
  value: any;
  defaultValue: any;
  validation?: {
    min?: number;
    max?: number;
    step?: number;
    required?: boolean;
    options?: { value: any; label: string }[];
    pattern?: string;
  };
  group?: string;
}

// Extension control
export interface ExtensionControl {
  key: string;
  label: string;
  description?: string;
  type: 'button' | 'toggle' | 'slider';
  action: string;
  params?: Record<string, any>;
  confirmation?: {
    title: string;
    message: string;
    destructive?: boolean;
  };
}

// Model metrics
export interface ModelMetrics {
  requests: number;
  errors: number;
  avgResponseTime: number;
  lastUsed?: string;
  tokensUsed?: number;
  cost?: number;
}

// Extension Plugin (from plugin_marketplace)
export interface ExtensionPlugin extends ExtensionBase {
  type: "plugin";
  pluginType: "core" | "community" | "enterprise" | "experimental";
  providers: ExtensionProvider[];
  permissions: string[];
  resources: ResourceUsage;
  lifecycle: LifecycleInfo;
  marketplace?: {
    rating: number;
    downloads: number;
    verified: boolean;
    price?: number;
  };
}

// Extension Provider (LLM, Voice, Video, Service)
export interface ExtensionProvider extends ExtensionBase {
  type: "provider";
  providerType: "llm" | "voice" | "video" | "service";
  models: ExtensionModel[];
  authentication: AuthConfig;
  endpoints: EndpointConfig;
  health: HealthStatus;
  rateLimits?: {
    requests_per_minute: number;
    tokens_per_minute?: number;
  };
}

// Extension Model/Service
export interface ExtensionModel extends ExtensionBase {
  type: "model";
  modelType: string;
  capabilities: string[];
  settings: ExtensionSetting[];
  controls: ExtensionControl[];
  metrics: ModelMetrics;
  contextWindow?: number;
  maxTokens?: number;
  pricing?: {
    input_tokens: number;
    output_tokens: number;
    currency: string;
  };
}

// LLM-specific types
export interface LLMProvider extends ExtensionProvider {
  providerType: "llm";
  models: LLMModel[];
}

export interface LLMModel extends ExtensionModel {
  modelType: "chat" | "completion" | "embedding";
  capabilities: ("text-generation" | "code-generation" | "reasoning")[];
  contextWindow: number;
  maxTokens: number;
}

// Voice-specific types
export interface VoiceProvider extends ExtensionProvider {
  providerType: "voice";
  models: VoiceModel[];
  supportedLanguages: string[];
  audioFormats: string[];
}

export interface VoiceModel extends ExtensionModel {
  modelType: "tts" | "stt" | "voice-cloning";
  voice: {
    name: string;
    language: string;
    gender: "male" | "female" | "neutral";
    accent?: string;
    quality: "low" | "medium" | "high" | "premium";
  };
  samples?: AudioSample[];
}

export interface AudioSample {
  url: string;
  text: string;
  duration: number;
}

// Video-specific types
export interface VideoProvider extends ExtensionProvider {
  providerType: "video";
  models: VideoModel[];
  supportedFormats: string[];
  maxResolution: string;
}

export interface VideoModel extends ExtensionModel {
  modelType: "generation" | "analysis" | "processing";
  supportedResolutions: string[];
  maxDuration?: number;
}

// System Extension types (from /extensions folder)
export interface SystemExtension extends ExtensionBase {
  type: "system_extension";
  extensionType: 
    | "analytics"
    | "automation" 
    | "communication"
    | "development"
    | "integration"
    | "productivity"
    | "security"
    | "experimental";
  manifest: ExtensionManifest;
  status: "active" | "inactive" | "error" | "loading";
  health: HealthStatus;
  capabilities: ExtensionCapabilities;
  resources: ResourceUsage;
  api?: APIEndpoints;
  ui?: UIComponents;
  backgroundTasks?: BackgroundTask[];
}

export interface ExtensionManifest {
  name: string;
  version: string;
  display_name: string;
  description: string;
  author: string;
  license: string;
  category: string;
  tags: string[];
  api_version: string;
  kari_min_version: string;
  capabilities: ExtensionCapabilities;
  dependencies: ExtensionDependencies;
  permissions: ExtensionPermissions;
  resources: ResourceLimits;
  ui?: UIConfiguration;
  api?: APIConfiguration;
  background_tasks?: BackgroundTaskConfiguration[];
  marketplace?: MarketplaceInfo;
}

export interface ExtensionCapabilities {
  provides_ui: boolean;
  provides_api: boolean;
  provides_background_tasks: boolean;
  provides_webhooks: boolean;
  provides_mcp_tools: boolean;
}

export interface ExtensionDependencies {
  system: string[];
  extensions: string[];
  plugins: string[];
}

export interface ExtensionPermissions {
  filesystem: string[];
  network: string[];
  system: string[];
  data: string[];
}

export interface ResourceLimits {
  max_memory: number;
  max_cpu: number;
  max_storage: number;
  max_network: number;
}

export interface UIConfiguration {
  components: string[];
  routes: string[];
  menu_items: UIMenuItem[];
}

export interface UIMenuItem {
  id: string;
  label: string;
  icon?: string;
  route: string;
  permissions?: string[];
}

export interface APIConfiguration {
  endpoints: APIEndpoint[];
  middleware: string[];
  rate_limits: RateLimit[];
}

export interface APIEndpoint {
  path: string;
  method: string;
  handler: string;
  permissions?: string[];
}

export interface RateLimit {
  endpoint: string;
  requests_per_minute: number;
  burst: number;
}

export interface BackgroundTaskConfiguration {
  name: string;
  schedule: string;
  handler: string;
  enabled: boolean;
}

export interface MarketplaceInfo {
  published: boolean;
  rating: number;
  downloads: number;
  price?: number;
  license_type: string;
}

export interface APIEndpoints {
  base_url: string;
  endpoints: Record<string, string>;
}

export interface UIComponents {
  sidebar_items: UIMenuItem[];
  dashboard_widgets: DashboardWidget[];
  settings_panels: SettingsPanel[];
}

export interface DashboardWidget {
  id: string;
  title: string;
  component: string;
  size: "small" | "medium" | "large";
  permissions?: string[];
}

export interface SettingsPanel {
  id: string;
  title: string;
  component: string;
  category: string;
  permissions?: string[];
}

export interface BackgroundTask {
  id: string;
  name: string;
  status: "running" | "stopped" | "error";
  last_run?: string;
  next_run?: string;
  error_message?: string;
}

// Agent-specific extensions
export interface AgentExtension extends SystemExtension {
  extensionType: "automation";
  agentType: "autonomous" | "workflow" | "task" | "monitoring";
  agentConfig: {
    triggers: AgentTrigger[];
    actions: AgentAction[];
    conditions: AgentCondition[];
    schedule?: string;
    enabled: boolean;
  };
  performance: {
    executions: number;
    success_rate: number;
    avg_execution_time: number;
    last_execution: string;
  };
}

export interface AgentTrigger {
  type: "event" | "schedule" | "webhook" | "manual";
  config: any;
  enabled: boolean;
}

export interface AgentAction {
  type: "plugin_execution" | "api_call" | "notification" | "data_operation";
  config: any;
  order: number;
}

export interface AgentCondition {
  type: "time" | "data" | "system" | "custom";
  config: any;
  operator: "and" | "or" | "not";
}

// Automation-specific extensions
export interface AutomationExtension extends SystemExtension {
  extensionType: "automation";
  automationType: "workflow" | "rpa" | "integration" | "monitoring";
  workflow: {
    steps: WorkflowStep[];
    variables: WorkflowVariable[];
    error_handling: ErrorHandlingConfig;
    enabled: boolean;
  };
  execution: {
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    avg_duration: number;
    last_run: string;
  };
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: "action" | "condition" | "loop" | "parallel";
  config: any;
  next_steps: string[];
  error_handling?: string;
}

export interface WorkflowVariable {
  name: string;
  type: "string" | "number" | "boolean" | "object";
  value: any;
  description?: string;
}

export interface ErrorHandlingConfig {
  on_error: "stop" | "continue" | "retry";
  max_retries?: number;
  retry_delay?: number;
  fallback_action?: string;
}

export type ExtensionTaskExecutionStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed';

export interface ExtensionTaskHistoryEntry {
  execution_id: string;
  task_name: string;
  status: ExtensionTaskExecutionStatus;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error?: string;
  result?: unknown;
}

// Navigation types
export type ExtensionCategory = 'Plugins' | 'Extensions';

export type NavigationLevel = "category" | "submenu" | "items" | "settings";

export interface NavigationState {
  currentCategory: ExtensionCategory;
  currentLevel: NavigationLevel;

  // For Plugins category
  selectedPluginProvider?: string; // llm, voice, video, service
  selectedProviderItem?: string; // specific provider instance
  selectedModel?: string; // specific model/service

  // For Extensions category
  selectedExtensionSubmenu?: "agents" | "automations" | "system";
  selectedExtensionCategory?: string; // analytics, communication, etc.
  selectedExtensionItem?: string; // specific extension instance

  breadcrumb: BreadcrumbItem[];
  canGoBack: boolean;
}

export interface BreadcrumbItem {
  level: NavigationLevel;
  category?: ExtensionCategory;
  id?: string;
  name: string;
  icon?: string;
}

/** Identifier and label for navigation items */
export interface BaseNavigationItem {
  id: string;
  name: string;
  description?: string;
  icon?: string;
}

/** State stored in ExtensionContext */
export interface ExtensionState {
  currentCategory: ExtensionCategory;
  breadcrumbs: BreadcrumbItem[];
  level: number;
  navigation: NavigationState;
  loading: boolean;
  error: string | null;
  events: ExtensionEvent[];
}

// Extension events
export interface ExtensionEvent {
  id: string;
  type: "install" | "uninstall" | "enable" | "disable" | "configure" | "error";
  extensionId: string;
  timestamp: string;
  message: string;
  data?: any;
}

// Error types
export interface ExtensionError {
  type: "network" | "authentication" | "validation" | "permission" | "resource";
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  recoverable: boolean;
}

/** Actions that mutate ExtensionState */
export type ExtensionAction =
  | { type: 'SET_CATEGORY'; category: ExtensionCategory }
  | { type: 'PUSH_BREADCRUMB'; item: BreadcrumbItem }
  | { type: 'POP_BREADCRUMB' }
  | { type: 'RESET_BREADCRUMBS' }
  | { type: 'GO_BACK' }
  | { type: 'SET_LEVEL'; level: number }
  | { type: 'SET_NAVIGATION'; navigation: Partial<NavigationState> }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'ADD_EVENT'; event: ExtensionEvent }
  | { type: 'CLEAR_EVENTS' };
