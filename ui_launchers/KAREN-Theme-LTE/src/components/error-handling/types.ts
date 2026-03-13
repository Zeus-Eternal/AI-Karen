/**
 * Error Handling Types for CoPilot Frontend
 * 
 * This module provides TypeScript types for comprehensive error handling,
 * recovery mechanisms, and user-friendly error display.
 */

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
  FATAL = 'fatal'
}

export enum ErrorCategory {
  NETWORK = 'network',
  CONNECTIVITY = 'connectivity',
  API_FAILURE = 'api_failure',
  SYSTEM = 'system',
  INFRASTRUCTURE = 'infrastructure',
  DATABASE = 'database',
  FILE_SYSTEM = 'file_system',
  APPLICATION = 'application',
  BUSINESS_LOGIC = 'business_logic',
  VALIDATION = 'validation',
  SECURITY = 'security',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  AI_PROCESSING = 'ai_processing',
  MODEL_UNAVAILABLE = 'model_unavailable',
  LLM_PROVIDER = 'llm_provider',
  UI_COMPONENT = 'ui_component',
  USER_INPUT = 'user_input',
  PERFORMANCE = 'performance',
  RESOURCE_EXHAUSTION = 'resource_exhaustion',
  TIMEOUT = 'timeout',
  CONFIGURATION = 'configuration',
  DEPLOYMENT = 'deployment',
  EXTERNAL_SERVICE = 'external_service',
  THIRD_PARTY = 'third_party',
  UNKNOWN = 'unknown'
}

export enum ErrorType {
  CONNECTION_ERROR = 'connection_error',
  TIMEOUT_ERROR = 'timeout_error',
  RATE_LIMIT_ERROR = 'rate_limit_error',
  DNS_ERROR = 'dns_error',
  MEMORY_ERROR = 'memory_error',
  DISK_SPACE_ERROR = 'disk_space_error',
  PERMISSION_ERROR = 'permission_error',
  PROCESS_ERROR = 'process_error',
  VALIDATION_ERROR = 'validation_error',
  LOGIC_ERROR = 'logic_error',
  DEPENDENCY_ERROR = 'dependency_error',
  MODEL_LOADING_ERROR = 'model_loading_error',
  INFERENCE_ERROR = 'inference_error',
  CONTEXT_TOO_LARGE = 'context_too_large',
  TOKEN_LIMIT_EXCEEDED = 'token_limit_exceeded',
  CONNECTION_POOL_ERROR = 'connection_pool_error',
  QUERY_ERROR = 'query_error',
  TRANSACTION_ERROR = 'transaction_error',
  RENDER_ERROR = 'render_error',
  COMPONENT_ERROR = 'component_error',
  STATE_ERROR = 'state_error'
}

export interface ErrorInfo {
  id: string;
  type: ErrorType;
  category: ErrorCategory;
  severity: ErrorSeverity;
  title: string;
  message: string;
  technicalDetails?: string;
  resolutionSteps: string[];
  retryPossible: boolean;
  userActionRequired: boolean;
  timestamp: string;
  context?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  stackTrace?: string;
  component?: string;
  operation?: string;
  requestId?: string;
  userId?: string;
  sessionId?: string;
}

export interface RecoveryAction {
  id: string;
  strategy: string;
  description: string;
  priority: number;
  maxAttempts: number;
  timeout: number;
  requiresUserInput: boolean;
  metadata?: Record<string, unknown>;
}

export interface RecoveryAttempt {
  action: RecoveryAction;
  attemptNumber: number;
  startTime: string;
  endTime?: string;
  status: 'pending' | 'in_progress' | 'success' | 'failed' | 'partial' | 'abandoned';
  result?: unknown;
  error?: string | undefined | null; // Allow both null and undefined for compatibility
  metadata?: Record<string, unknown>;
}

export interface RecoveryResult {
  finalStatus: 'pending' | 'in_progress' | 'success' | 'failed' | 'partial' | 'abandoned';
  successfulAction?: RecoveryAction;
  failedActions: RecoveryAttempt[];
  successfulActions: RecoveryAttempt[];
  totalDuration: number;
  finalResult?: unknown;
  finalError?: string;
  metadata?: Record<string, unknown>;
}

export enum NotificationType {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
  FATAL = 'fatal',
  SUCCESS = 'success',
  // Additional notification types for compatibility
  SYSTEM = 'system',
  NEW_MESSAGE = 'new_message',
  MENTION = 'mention',
  REPLY = 'reply'
}

export interface ErrorNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: NotificationAction[];
  metadata?: Record<string, unknown>;
  autoHide?: number;
  persistent?: boolean;
}

export interface NotificationAction {
  id: string;
  label: string;
  action: () => void | Promise<void>;
  primary?: boolean;
  destructive?: boolean;
}

export interface ErrorReport {
  id: string;
  errorId: string;
  userId?: string;
  sessionId?: string;
  component?: string;
  operation?: string;
  errorInfo: ErrorInfo;
  userFeedback?: string;
  userEmail?: string;
  timestamp: string;
  status: 'pending' | 'submitted' | 'acknowledged' | 'resolved';
  metadata?: Record<string, unknown>;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  componentStack: string[];
  retryCount: number;
  isRecovering: boolean;
  recoveryAttempts: RecoveryAttempt[];
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  jitter: boolean;
  strategy: 'exponential_backoff' | 'linear_backoff' | 'fixed_delay' | 'fibonacci_backoff' | 'adaptive';
  retryCondition?: (error: Error) => boolean;
  onSuccess?: (result: unknown) => void;
  onRetry?: (error: Error, attempt: number) => void;
  onMaxRetriesReached?: (error: Error) => void;
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  timeout: number;
  halfOpenMaxCalls: number;
  policy: 'failure_count' | 'failure_rate' | 'consecutive_failures' | 'hybrid';
  failureRateThreshold?: number;
  consecutiveFailureThreshold?: number;
  minSamples?: number;
  autoReset?: boolean;
}

export interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half_open';
  failureCount: number;
  lastFailureTime?: string;
  lastSuccessTime?: string;
  halfOpenCalls: number;
}

export interface ErrorHandlingConfig {
  enableRetry: boolean;
  enableCircuitBreaker: boolean;
  enableRecovery: boolean;
  enableMonitoring: boolean;
  enableContext: boolean;
  enableNotifications: boolean;
  enableReporting: boolean;
  defaultMaxRetries: number;
  defaultTimeout: number;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  apiEndpoint?: string;
  notificationChannels?: string[];
  retryConfig?: Partial<RetryConfig>;
  circuitBreakerConfig?: Partial<CircuitBreakerConfig>;
}

export interface ErrorContext {
  id: string;
  errorId: string;
  timestamp: string;
  classification?: ErrorInfo;
  entries: Record<string, ContextEntry>;
  parentContextId?: string;
  childContextIds: string[];
  scope: 'request' | 'session' | 'component' | 'system' | 'global';
  component?: string;
  operation?: string;
  userId?: string;
  sessionId?: string;
  requestId?: string;
  systemInfo?: Record<string, unknown>;
  environmentInfo?: Record<string, unknown>;
}

export interface ContextEntry {
  key: string;
  value: unknown;
  contextType: 'user_data' | 'request_data' | 'system_state' | 'component_state' | 'business_data' | 'temporary' | 'persistent';
  scope: 'request' | 'session' | 'component' | 'system' | 'global';
  timestamp: string;
  ttl?: number;
  metadata?: Record<string, unknown>;
}

export interface ErrorMetrics {
  totalErrors: number;
  errorsByCategory: Record<ErrorCategory, number>;
  errorsBySeverity: Record<ErrorSeverity, number>;
  errorsByComponent: Record<string, number>;
  errorsByOperation: Record<string, number>;
  errorsLastHour: number;
  errorsLast24h: number;
  errorsLastWeek: number;
  errorRatePerMinute: number;
  errorRatePerHour: number;
  uniqueErrorTypes: number;
  recurringErrors: number;
  cascadingErrors: number;
}

export interface ErrorPattern {
  id: string;
  type: 'spike' | 'trend' | 'correlation' | 'recurring' | 'cascade' | 'threshold' | 'anomaly';
  description: string;
  confidence: number;
  firstSeen: string;
  lastSeen: string;
  affectedComponents: string[];
  errorCount: number;
  severity: ErrorSeverity;
  metadata?: Record<string, unknown>;
}

export interface ErrorAlert {
  id: string;
  level: NotificationType;
  title: string;
  message: string;
  pattern?: ErrorPattern;
  events: ErrorInfo[];
  timestamp: string;
  metadata?: Record<string, unknown>;
}

// Event types for error handling
export interface ErrorEvent {
  type: 'error_occurred' | 'error_recovered' | 'error_boundary_triggered' | 'circuit_breaker_opened' | 'circuit_breaker_closed' | 'retry_attempted' | 'retry_succeeded' | 'retry_failed' | 'degradation_triggered' | 'recovery_completed';
  timestamp: string;
  data: unknown;
}

// Hook types for React integration
export interface UseErrorHandlerReturn {
  error: ErrorInfo | null;
  setError: (error: ErrorInfo | null) => void;
  clearError: () => void;
  retry: () => Promise<void>;
  recover: () => Promise<void>;
  report: (feedback?: string) => Promise<void>;
  isLoading: boolean;
  isRecovering: boolean;
  retryCount: number;
  recoveryAttempts: RecoveryAttempt[];
}

export interface UseErrorBoundaryReturn {
  error: ErrorInfo | null;
  reset: () => void;
  retry: () => Promise<void>;
  recover: () => Promise<void>;
  componentStack: string[];
  retryCount: number;
  isRecovering: boolean;
  recoveryAttempts: RecoveryAttempt[];
}

export interface UseRetryReturn {
  execute: <T>(operation: () => Promise<T>) => Promise<T>;
  reset: () => void;
  retryCount: number;
  isRetrying: boolean;
  lastError: Error | null;
  config: RetryConfig;
}

export interface UseCircuitBreakerReturn {
  execute: <T>(operation: () => Promise<T>) => Promise<T>;
  state: CircuitBreakerState;
  reset: () => void;
  isOpen: boolean;
  isHalfOpen: boolean;
  isClosed: boolean;
  config: CircuitBreakerConfig;
}

// Component props interfaces
export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{
    error: Error;
    errorInfo: ErrorInfo | null;
    onRetry: () => Promise<void>;
    onRecovery: () => Promise<void>;
    onReport: (feedback?: string) => Promise<void>;
    retryCount: number;
    maxRetries: number;
    isRecovering: boolean;
    componentStack: string[];
    reset: () => void;
  }>;
  onError?: (errorInfo: ErrorInfo, error: Error, componentStack: string[]) => void;
  onRetry?: (error: ErrorInfo, attempt: number) => void;
  onRecovery?: (error: ErrorInfo, result: RecoveryResult) => void;
  maxRetries?: number;
  retryDelay?: number;
  enableLogging?: boolean;
  enableReporting?: boolean;
  component?: string;
}

export interface ErrorDisplayProps {
  error: ErrorInfo;
  onClose?: () => void;
  onRetry?: () => Promise<void>;
  onReport?: () => Promise<void>;
  showDetails?: boolean;
  showStackTrace?: boolean;
  compact?: boolean;
  variant?: 'default' | 'modal' | 'toast' | 'inline';
  className?: string;
}

export interface ErrorNotificationProps {
  notification: ErrorNotification;
  onClose?: (id: string) => void;
  onAction?: (action: NotificationAction) => void;
  autoHide?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export interface ErrorRecoveryProps {
  error: ErrorInfo;
  onRecovery?: (result: RecoveryResult) => void;
  onCancel?: () => void;
  availableActions?: RecoveryAction[];
  showProgress?: boolean;
  autoRecover?: boolean;
  maxAutoAttempts?: number;
  className?: string;
}

export interface ErrorReportingProps {
  error?: ErrorInfo;
  onSubmit?: (report: ErrorReport) => Promise<void>;
  onCancel?: () => void;
  includeUserFeedback?: boolean;
  includeSystemInfo?: boolean;
  autoSubmit?: boolean;
  className?: string;
}
