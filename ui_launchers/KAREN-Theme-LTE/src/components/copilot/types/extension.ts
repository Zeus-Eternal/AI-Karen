/**
 * Extension types and interfaces for CoPilot Architecture
 */

type ExtensionService = Record<string, unknown>;
type ExtensionDataMap = Record<string, unknown>;

/**
 * Extension interface that all CoPilot extensions must implement
 */
export interface CoPilotExtension {
  /** Unique identifier for the extension */
  id: string;
  
  /** Display name for the extension */
  name: string;
  
  /** Extension version */
  version: string;
  
  /** Extension description */
  description: string;
  
  /** Extension author */
  author: string;
  
  /** Extension category */
  category: ExtensionCategory;
  
  /** Extension capabilities */
  capabilities: ExtensionCapability[];
  
  /** Extension initialization function */
  initialize(context: ExtensionContext): Promise<void>;
  
  /** Extension execution function */
  execute(request: ExtensionRequest): Promise<ExtensionResponse>;
  
  /** Optional cleanup function */
  cleanup?(): Promise<void>;
  
  /** Optional function to get extension status */
  getStatus?(): ExtensionStatus;
}

/**
 * Extension categories
 */
export enum ExtensionCategory {
  CHAT = 'chat',
  AGENT = 'agent',
  TASK = 'task',
  UI = 'ui',
  INTEGRATION = 'integration',
  PRODUCTIVITY = 'productivity',
  DEVELOPMENT = 'development',
  ANALYTICS = 'analytics',
  SECURITY = 'security',
  EXPERIMENTAL = 'experimental'
}

/**
 * Extension capabilities
 */
export enum ExtensionCapability {
  /** Can modify chat messages */
  CHAT_MODIFICATION = 'chat_modification',
  
  /** Can add UI components */
  UI_COMPONENTS = 'ui_components',
  
  /** Can create and manage tasks */
  TASK_MANAGEMENT = 'task_management',
  
  /** Can access agent services */
  AGENT_ACCESS = 'agent_access',
  
  /** Can integrate with external services */
  EXTERNAL_INTEGRATION = 'external_integration',
  
  /** Can access memory services */
  MEMORY_ACCESS = 'memory_access',
  
  /** Can process voice input */
  VOICE_PROCESSING = 'voice_processing',
  
  /** Can provide theme customization */
  THEME_CUSTOMIZATION = 'theme_customization'
}

/**
 * Extension context provided during initialization
 */
export interface ExtensionContext {
  /** Access to agent service */
  agentService: ExtensionService;
  
  /** Access to UI service */
  uiService: ExtensionService;
  
  /** Access to theme service */
  themeService: ExtensionService;
  
  /** Access to memory service */
  memoryService: ExtensionService;
  
  /** Access to conversation service */
  conversationService: ExtensionService;
  
  /** Access to task service */
  taskService: ExtensionService;
  
  /** Access to voice service */
  voiceService: ExtensionService;
  
  /** Extension configuration */
  config: ExtensionConfig;
  
  /** Logger for the extension */
  logger: ExtensionLogger;
}

/**
 * Extension configuration
 */
export interface ExtensionConfig {
  /** Extension-specific settings */
  settings: ExtensionDataMap;
  
  /** Global configuration */
  global: ExtensionDataMap;
  
  /** User preferences */
  userPreferences: ExtensionDataMap;
  
  /** Tenant configuration */
  tenant: ExtensionDataMap;
}

/**
 * Extension logger interface
 */
export interface ExtensionLogger {
  /** Log a debug message */
  debug(message: string, ...args: unknown[]): void;
  
  /** Log an info message */
  info(message: string, ...args: unknown[]): void;
  
  /** Log a warning message */
  warn(message: string, ...args: unknown[]): void;
  
  /** Log an error message */
  error(message: string, ...args: unknown[]): void;
}

/**
 * Extension request structure
 */
export interface ExtensionRequest<TPayload = unknown, TMetadata extends ExtensionDataMap = ExtensionDataMap> {
  /** Request type */
  type: ExtensionRequestType;
  
  /** Request ID for tracking */
  id: string;
  
  /** Request payload */
  payload: TPayload;
  
  /** Request metadata */
  metadata: TMetadata;
  
  /** User context */
  userContext: UserContext;
  
  /** Session context */
  sessionContext: SessionContext;
}

/**
 * Extension request types
 */
export enum ExtensionRequestType {
  /** Execute a command */
  EXECUTE = 'execute',
  
  /** Get information */
  GET_INFO = 'get_info',
  
  /** Update configuration */
  UPDATE_CONFIG = 'update_config',
  
  /** Process data */
  PROCESS_DATA = 'process_data',
  
  /** Render UI component */
  RENDER_UI = 'render_ui',
  
  /** Handle event */
  HANDLE_EVENT = 'handle_event'
}

/**
 * User context
 */
export interface UserContext {
  /** User ID */
  userId: string;
  
  /** User roles */
  roles: string[];
  
  /** User permissions */
  permissions: string[];
  
  /** User preferences */
  preferences: ExtensionDataMap;
}

/**
 * Session context
 */
export interface SessionContext {
  /** Session ID */
  sessionId: string;
  
  /** Conversation ID if applicable */
  conversationId?: string;
  
  /** Agent ID if applicable */
  agentId?: string;
  
  /** Task ID if applicable */
  taskId?: string;
}

/**
 * Extension response structure
 */
export interface ExtensionResponse<TData = unknown, TMetadata extends ExtensionDataMap = ExtensionDataMap> {
  /** Response ID matching the request ID */
  id: string;
  
  /** Response status */
  status: ExtensionResponseStatus;
  
  /** Response data */
  data?: TData;
  
  /** Response error if applicable */
  error?: ExtensionError;
  
  /** Response metadata */
  metadata?: TMetadata;
}

/**
 * Extension response status
 */
export enum ExtensionResponseStatus {
  /** Request was successful */
  SUCCESS = 'success',
  
  /** Request failed */
  ERROR = 'error',
  
  /** Request is still processing */
  PENDING = 'pending',
  
  /** Request was cancelled */
  CANCELLED = 'cancelled'
}

/**
 * Extension error structure
 */
export interface ExtensionError<TDetails = unknown> {
  /** Error code */
  code: ExtensionErrorCode;
  
  /** Error message */
  message: string;
  
  /** Error details */
  details?: TDetails;
  
  /** Stack trace if available */
  stack?: string;
}

/**
 * Extension error codes
 */
export enum ExtensionErrorCode {
  /** General error */
  GENERAL_ERROR = 'general_error',
  
  /** Invalid request */
  INVALID_REQUEST = 'invalid_request',
  
  /** Permission denied */
  PERMISSION_DENIED = 'permission_denied',
  
  /** Resource not found */
  NOT_FOUND = 'not_found',
  
  /** Validation error */
  VALIDATION_ERROR = 'validation_error',
  
  /** Execution error */
  EXECUTION_ERROR = 'execution_error',
  
  /** Timeout error */
  TIMEOUT_ERROR = 'timeout_error',
  
  /** Configuration error */
  CONFIGURATION_ERROR = 'configuration_error'
}

/**
 * Extension status
 */
export interface ExtensionStatus {
  /** Whether the extension is enabled */
  enabled: boolean;
  
  /** Whether the extension is initialized */
  initialized: boolean;
  
  /** Extension health status */
  health: ExtensionHealthStatus;
  
  /** Extension metrics */
  metrics: ExtensionMetrics;
  
  /** Last error if any */
  lastError?: ExtensionError;
}

/**
 * Extension health status
 */
export enum ExtensionHealthStatus {
  /** Extension is healthy */
  HEALTHY = 'healthy',
  
  /** Extension has warnings */
  WARNING = 'warning',
  
  /** Extension has errors */
  ERROR = 'error',
  
  /** Extension is not responding */
  UNRESPONSIVE = 'unresponsive'
}

/**
 * Extension metrics
 */
export interface ExtensionMetrics {
  /** Number of requests handled */
  requestCount: number;
  
  /** Number of successful requests */
  successCount: number;
  
  /** Number of failed requests */
  errorCount: number;
  
  /** Average response time in milliseconds */
  averageResponseTime: number;
  
  /** Last execution timestamp */
  lastExecution?: Date;
  
  /** Memory usage in bytes */
  memoryUsage?: number;
  
  /** CPU usage percentage */
  cpuUsage?: number;
}

/**
 * Extension UI component
 */
export interface ExtensionUIComponent {
  /** Component ID */
  id: string;
  
  /** Component type */
  type: ExtensionUIComponentType;
  
  /** Component props */
  props: ExtensionDataMap;
  
  /** Component position */
  position: ExtensionUIComponentPosition;
  
  /** Component visibility */
  visible: boolean;
  
  /** Component order */
  order: number;
}

/**
 * Extension UI component types
 */
export enum ExtensionUIComponentType {
  /** Button component */
  BUTTON = 'button',
  
  /** Menu component */
  MENU = 'menu',
  
  /** Panel component */
  PANEL = 'panel',
  
  /** Modal component */
  MODAL = 'modal',
  
  /** Input component */
  INPUT = 'input',
  
  /** Select component */
  SELECT = 'select',
  
  /** Custom React component */
  REACT_COMPONENT = 'react_component'
}

/**
 * Extension UI component positions
 */
export enum ExtensionUIComponentPosition {
  /** Chat header */
  CHAT_HEADER = 'chat_header',
  
  /** Chat input area */
  CHAT_INPUT_AREA = 'chat_input_area',
  
  /** Message bubble */
  MESSAGE_BUBBLE = 'message_bubble',
  
  /** Sidebar */
  SIDEBAR = 'sidebar',
  
  /** Toolbar */
  TOOLBAR = 'toolbar',
  
  /** Status bar */
  STATUS_BAR = 'status_bar',
  
  /** Floating action button */
  FLOATING_ACTION_BUTTON = 'floating_action_button'
}

/**
 * Extension event
 */
export interface ExtensionEvent<TPayload = unknown> {
  /** Event type */
  type: ExtensionEventType;
  
  /** Event ID */
  id: string;
  
  /** Event source */
  source: string;
  
  /** Event payload */
  payload: TPayload;
  
  /** Event timestamp */
  timestamp: Date;
}

/**
 * Extension event types
 */
export enum ExtensionEventType {
  /** Message sent event */
  MESSAGE_SENT = 'message_sent',
  
  /** Message received event */
  MESSAGE_RECEIVED = 'message_received',
  
  /** Agent selected event */
  AGENT_SELECTED = 'agent_selected',
  
  /** Task created event */
  TASK_CREATED = 'task_created',
  
  /** Task completed event */
  TASK_COMPLETED = 'task_completed',
  
  /** User joined event */
  USER_JOINED = 'user_joined',
  
  /** User left event */
  USER_LEFT = 'user_left',
  
  /** Extension loaded event */
  EXTENSION_LOADED = 'extension_loaded',
  
  /** Extension unloaded event */
  EXTENSION_UNLOADED = 'extension_unloaded'
}

/**
 * Extension hook for React components
 */
export interface ExtensionHook<TArgs extends unknown[] = unknown[], TResult = unknown> {
  /** Hook name */
  name: string;
  
  /** Hook function */
  hook: (...args: TArgs) => TResult;
  
  /** Hook dependencies */
  dependencies?: unknown[];
}

/**
 * Extension context provider for React
 */
export interface ExtensionContextProvider<TValue = unknown> {
  /** Provider name */
  name: string;
  
  /** Context value */
  value: TValue;
  
  /** Child components */
  children: React.ReactNode;
}
