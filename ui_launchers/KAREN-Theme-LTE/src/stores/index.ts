/**
 * Stores Index
 * Central exports for all Zustand stores
 */

// Export individual stores
export { useChatStore, useChatMessages, useChatLoading, useChatInput, useChatRecording, useVoiceSettings, useChatActions, getMessageById, getMessagesByRole, getLastMessage, getConversationStats } from './chatStore';
export { usePerformanceStore, usePerformanceMetrics, usePerformanceMonitoring, useCoreWebVitals, usePerformanceScores, useResourceUsage, usePerformanceSettings, usePerformanceActions, getMetricRating, calculatePerformanceScore } from './performanceStore';
export {
  useErrors,
  useActiveError,
  useErrorHistory,
  useNotifications,
  useRecoveryAttempts,
  useErrorMetrics,
  useErrorSettings,
  useErrorActions,
  useNotificationActions,
  useRecoveryActions,
  useMetricsActions,
  useSettingsActions,
  useErrorById,
  useErrorsByCategory,
  useErrorsBySeverity,
  useNotificationById,
  useUnreadNotifications,
  useRecentErrors,
  useRecentRecoveryAttempts,
  useErrorStats,
  useUIStore
} from './errorStore';

// Export store types
export type { ChatState } from './chatStore';
export type { PerformanceState, PerformanceReport } from './performanceStore';

// Re-export for convenience
export { create } from 'zustand';
export { devtools, persist } from 'zustand/middleware';