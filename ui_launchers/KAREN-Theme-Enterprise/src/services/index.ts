/**
 * Services Index - Production Grade
 *
 * Centralized export hub for all service modules and types.
 */

// ============================================================================
// Core Services
// ============================================================================

export { auditLogger } from './audit-logger';
export type { Timer as AuditLoggerTimer } from './audit-logger';

export { AuditService } from './auditService';
export type { AuditLogEntry } from './auditService';

export { authService, getAuthService, AuthService, initializeAuthService } from './authService';

export { initializeChatService, ChatService, getChatService } from './chatService';
export type { ProcessMessageOptions, ConversationSession } from './chatService';

export { MemoryService, initializeMemoryService, getMemoryService } from './memoryService';
export type { MemoryStats, MemorySearchOptions, MemoryContext } from './memoryService';

export { getPluginService, PluginService, initializePluginService } from './pluginService';
export type { PluginMetrics, PluginValidationResult, PluginCategory, PluginExecutionOptions } from './pluginService';

// ============================================================================
// Performance Services
// ============================================================================

export { PerformanceMonitor, performanceMonitor } from './performance-monitor';
export type {
  PerformanceMetric,
  PerformanceMetrics,
  PerformanceEvent,
  AlertListener,
  PerformanceThresholds,
  PerformanceAlert,
  WebVitalsMetrics,
  ResourceUsage,
} from './performance-monitor';

export { PerformanceOptimizer, performanceOptimizer } from './performance-optimizer';
export type {
  OptimizationMetrics,
  OptimizationConfig,
  Listener as PerformanceOptimizerListener,
  Priority,
  OptimizationRecommendation,
} from './performance-optimizer';

export { performanceProfiler, PerformanceProfiler } from './performance-profiler';
export type {
  Bottleneck,
  OptimizationSuggestion,
  PerformanceComparison,
  PerformanceProfile,
  Listener as PerformanceProfilerListener,
  PerformanceMetrics as PerformanceProfilerMetrics,
  RegressionTest,
} from './performance-profiler';

// ============================================================================
// WebSocket Services
// ============================================================================

export {
  useEnhancedWebSocket,
  EnhancedWebSocketService,
  enhancedWebSocketService,
  useEnhancedWebSocketSubscription,
} from './enhanced-websocket-service';
export type {
  Timer as EnhancedWebSocketTimer,
  Subscription,
  WebSocketMessage as EnhancedWebSocketMessage,
  QueuedMessage,
  ConnectionMetrics,
  Interval,
  ConnectionState as EnhancedWebSocketConnectionState,
  WebSocketEventType as EnhancedWebSocketEventType,
} from './enhanced-websocket-service';

export {
  useWebSocket,
  useWebSocketSubscription,
  WebSocketService,
  getWebSocketService,
  websocketService,
} from './websocket-service';
export type {
  ConnectionState as LegacyWebSocketConnectionState,
  WebSocketEventType as LegacyWebSocketEventType,
  WebSocketMessage as LegacyWebSocketMessage,
} from './websocket-service';

// ============================================================================
// Extension Services
// ============================================================================

export { extensionService, ExtensionService } from './extensions';
export type { ExtensionInfo } from './extensions';





export { DEFAULT_CACHE_CONFIG } from './extensions/types';
export type { ExtensionAPIRequest, ExtensionInstallRequest, ExtensionAPIResponse, ExtensionControlRequest, ExtensionManifestMetadata, ExtensionRegistryEntry, ExtensionHealthSummary, ExtensionWebSocketEvent, ExtensionCacheConfig, ExtensionRegistrySummaryResponse, ExtensionUpdateRequest, ExtensionQueryParams, ExtensionConfigRequest } from './extensions/types';

// ============================================================================
// Other Services
// ============================================================================

export { initializeActionRegistry, getActionSuggestions, getActionRegistry, ActionRegistry } from './actionMapper';
export type { ActionHandler, ActionResult, SuggestedAction, EventListenerFn } from './actionMapper';

export { alertManager } from './alertManager';
export type { RateLimitTracker, AlertEventType, AlertEventListener } from './alertManager';

export { ErrorRecoveryService } from './error-recovery';

export { ErrorReportingService } from './error-reporting';

export { createUserFriendlyError, getServiceErrorHandler, ServiceErrorHandler, initializeServiceErrorHandler } from './errorHandler';
export type { RetryOptions, ServiceError, ErrorHandlerConfig } from './errorHandler';


export { reasoningService } from './reasoningService';
export type { ReasoningResponse, ReasoningRequest, FetchOptions } from './reasoningService';

export { resourceMonitor, ResourceMonitor } from './resource-monitor';
export type { ScalingRecommendation, CapacityPlan, ResourceThresholds, ResourceMetrics, ResourceAlert } from './resource-monitor';
