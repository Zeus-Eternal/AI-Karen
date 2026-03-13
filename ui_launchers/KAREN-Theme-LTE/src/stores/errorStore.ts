/**
 * Error Store Implementation for AI-Karen Production Chat System
 * Provides comprehensive error state management using Zustand.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';

// Import error types
import {
  ErrorInfo,
  ErrorCategory,
  ErrorSeverity,
  RecoveryResult,
  RecoveryAttempt,
  ErrorNotification,
  ErrorMetrics
} from '../components/error-handling/types';

// Define ErrorSettings interface since it's not in types.ts
export interface ErrorSettings {
  enableAutoRetry: boolean;
  enableAutoRecovery: boolean;
  maxRetryAttempts: number;
  retryDelay: number;
  enableErrorReporting: boolean;
  enableNotifications: boolean;
  persistErrors: boolean;
  enableMetrics: boolean;
  enableAnalytics: boolean;
  retentionDays: number;
  maxHistorySize: number;
  notificationTimeout: number;
  debugMode: boolean;
}

// Error state interface
interface ErrorState {
  errors: ErrorInfo[];
  activeError: ErrorInfo | null;
  errorHistory: ErrorInfo[];
  notifications: ErrorNotification[];
  recoveryAttempts: RecoveryAttempt[];
  metrics: ErrorMetrics;
  settings: ErrorSettings;
}

// Error store actions interface
interface ErrorStoreActions {
  // Error management
  addError: (error: ErrorInfo) => void;
  removeError: (errorId: string) => void;
  clearErrors: () => void;
  setActiveError: (error: ErrorInfo | null) => void;
  
  // Notification management
  addNotification: (notification: ErrorNotification) => void;
  removeNotification: (notificationId: string) => void;
  markNotificationRead: (notificationId: string) => void;
  clearNotifications: () => void;
  
  // Recovery management
  addRecoveryAttempt: (attempt: RecoveryAttempt) => void;
  updateRecoveryAttempt: (attemptId: string, status: string, result?: RecoveryResult, error?: string) => void;
  clearRecoveryAttempts: () => void;
  
  // Metrics management
  updateMetrics: (metricsUpdate: Partial<ErrorMetrics>) => void;
  resetMetrics: () => void;
  
  // Settings management
  updateSettings: (settingsUpdate: Partial<ErrorSettings>) => void;
  loadSettings: () => void;
  resetSettings: () => void;
  
  // Utility methods
  exportErrorData: () => string;
  importErrorData: (data: string) => boolean;
}

// Default error settings
const defaultSettings: ErrorSettings = {
  enableAutoRetry: true,
  enableAutoRecovery: true,
  maxRetryAttempts: 3,
  retryDelay: 1000,
  enableErrorReporting: true,
  enableNotifications: true,
  persistErrors: true,
  enableMetrics: true,
  enableAnalytics: true,
  retentionDays: 30,
  maxHistorySize: 1000,
  notificationTimeout: 5000,
  debugMode: false
};

// Default error metrics
const defaultMetrics: ErrorMetrics = {
  totalErrors: 0,
  errorsByCategory: {
    [ErrorCategory.NETWORK]: 0,
    [ErrorCategory.CONNECTIVITY]: 0,
    [ErrorCategory.API_FAILURE]: 0,
    [ErrorCategory.SYSTEM]: 0,
    [ErrorCategory.INFRASTRUCTURE]: 0,
    [ErrorCategory.DATABASE]: 0,
    [ErrorCategory.FILE_SYSTEM]: 0,
    [ErrorCategory.APPLICATION]: 0,
    [ErrorCategory.BUSINESS_LOGIC]: 0,
    [ErrorCategory.VALIDATION]: 0,
    [ErrorCategory.SECURITY]: 0,
    [ErrorCategory.AUTHENTICATION]: 0,
    [ErrorCategory.AUTHORIZATION]: 0,
    [ErrorCategory.AI_PROCESSING]: 0,
    [ErrorCategory.MODEL_UNAVAILABLE]: 0,
    [ErrorCategory.LLM_PROVIDER]: 0,
    [ErrorCategory.UI_COMPONENT]: 0,
    [ErrorCategory.USER_INPUT]: 0,
    [ErrorCategory.PERFORMANCE]: 0,
    [ErrorCategory.RESOURCE_EXHAUSTION]: 0,
    [ErrorCategory.TIMEOUT]: 0,
    [ErrorCategory.CONFIGURATION]: 0,
    [ErrorCategory.DEPLOYMENT]: 0,
    [ErrorCategory.EXTERNAL_SERVICE]: 0,
    [ErrorCategory.THIRD_PARTY]: 0,
    [ErrorCategory.UNKNOWN]: 0
  },
  errorsBySeverity: {
    [ErrorSeverity.LOW]: 0,
    [ErrorSeverity.MEDIUM]: 0,
    [ErrorSeverity.HIGH]: 0,
    [ErrorSeverity.CRITICAL]: 0,
    [ErrorSeverity.FATAL]: 0
  },
  errorsByComponent: {},
  errorsByOperation: {},
  errorsLastHour: 0,
  errorsLast24h: 0,
  errorsLastWeek: 0,
  errorRatePerMinute: 0,
  errorRatePerHour: 0,
  uniqueErrorTypes: 0,
  recurringErrors: 0,
  cascadingErrors: 0
};

// Create error store with persistence and state management
const useErrorStore = create<ErrorState & ErrorStoreActions>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        // Initial state
        errors: [],
        activeError: null,
        errorHistory: [],
        notifications: [],
        recoveryAttempts: [],
        metrics: defaultMetrics,
        settings: defaultSettings,
        
        // Error management actions
        addError: (error: ErrorInfo) => {
          set((state) => {
            state.errors.push(error);
            state.errorHistory.push(error);
            state.metrics.totalErrors +=1;
            state.metrics.errorsByCategory[error.category] +=1;
            state.metrics.errorsBySeverity[error.severity] +=1;
            
            // Update component errors
            if (error.component) {
              state.metrics.errorsByComponent[error.component] = 
                (state.metrics.errorsByComponent[error.component] || 0) +1;
            }
            
            // Update operation errors
            if (error.operation) {
              state.metrics.errorsByOperation[error.operation] = 
                (state.metrics.errorsByOperation[error.operation] || 0) +1;
            }
            
            // Update active error if new error is more severe
            if (!state.activeError || error.severity > state.activeError.severity) {
              state.activeError = error;
            }
          });
        },
        
        removeError: (errorId: string) => {
          set((state) => {
            state.errors = state.errors.filter((error: ErrorInfo) => error.id !== errorId);
            if (state.activeError?.id === errorId) {
              state.activeError = state.errors.length > 0 ? state.errors[state.errors.length -1] : null;
            }
          });
        },
        
        clearErrors: () => {
          set((state) => {
            state.errors = [];
            state.activeError = null;
          });
        },
        
        setActiveError: (error: ErrorInfo | null) => {
          set((state) => {
            state.activeError = error;
          });
        },
        
        // Notification management actions
        addNotification: (notification: ErrorNotification) => {
          set((state) => {
            state.notifications.push(notification);
            
            // Auto-hide notification if specified
            if (notification.autoHide && notification.autoHide > 0) {
              setTimeout(() => {
                get().removeNotification(notification.id);
              }, notification.autoHide);
            }
          });
        },
        
        removeNotification: (notificationId: string) => {
          set((state) => {
            state.notifications = state.notifications.filter(
              (notification: ErrorNotification) => notification.id !== notificationId
            );
          });
        },
        
        markNotificationRead: (notificationId: string) => {
          set((state) => {
            const notification = state.notifications.find((n: ErrorNotification) => n.id === notificationId);
            if (notification) {
              notification.read = true;
            }
          });
        },
        
        clearNotifications: () => {
          set((state) => {
            state.notifications = [];
          });
        },
        
        // Recovery management actions
        addRecoveryAttempt: (attempt: RecoveryAttempt) => {
          set((state) => {
            state.recoveryAttempts.push(attempt);
          });
        },
        
        updateRecoveryAttempt: (attemptId: string, status: string, result?: RecoveryResult, error?: string) => {
          set((state) => {
            const attempt = state.recoveryAttempts.find((a: RecoveryAttempt) => a.action.id === attemptId);
            if (attempt) {
              attempt.status = status as RecoveryAttempt['status'];
              attempt.endTime = new Date().toISOString();
              attempt.result = result;
              attempt.error = error;
            }
          });
        },
        
        clearRecoveryAttempts: () => {
          set((state) => {
            state.recoveryAttempts = [];
          });
        },
        
        // Metrics management actions
        updateMetrics: (metricsUpdate: Partial<ErrorMetrics>) => {
          set((state) => {
            Object.assign(state.metrics, metricsUpdate);
          });
        },
        
        resetMetrics: () => {
          set((state) => {
            state.metrics = { ...defaultMetrics };
          });
        },
        
        // Settings management actions
        updateSettings: (settingsUpdate: Partial<ErrorSettings>) => {
          set((state) => {
            Object.assign(state.settings, settingsUpdate);
          });
        },
        
        loadSettings: () => {
          // Load settings from localStorage or API
          try {
            const savedSettings = localStorage.getItem('karen-error-settings');
            if (savedSettings) {
              const parsedSettings = JSON.parse(savedSettings);
              set((state) => {
                Object.assign(state.settings, parsedSettings);
              });
            }
          } catch (error) {
            console.error('Failed to load error settings:', error);
          }
        },
        
        resetSettings: () => {
          set((state) => {
            state.settings = { ...defaultSettings };
          });
        },
        
        // Utility methods
        exportErrorData: () => {
          const state = get();
          const exportData = {
            errors: state.errors,
            errorHistory: state.errorHistory,
            recoveryAttempts: state.recoveryAttempts,
            metrics: state.metrics,
            settings: state.settings,
            exportDate: new Date().toISOString()
          };
          return JSON.stringify(exportData, null, 2);
        },
        
        importErrorData: (data: string) => {
          try {
            const importData = JSON.parse(data);
            set((state) => {
              if (importData.errors) state.errors = importData.errors;
              if (importData.errorHistory) state.errorHistory = importData.errorHistory;
              if (importData.recoveryAttempts) state.recoveryAttempts = importData.recoveryAttempts;
              if (importData.metrics) state.metrics = { ...defaultMetrics, ...importData.metrics };
              if (importData.settings) state.settings = { ...defaultSettings, ...importData.settings };
            });
            return true;
          } catch (error) {
            console.error('Failed to import error data:', error);
            return false;
          }
        }
      })),
      {
        name: 'karen-error-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          errorHistory: state.errorHistory,
          recoveryAttempts: state.recoveryAttempts,
          metrics: state.metrics,
          settings: state.settings
        })
      }
    )
  )
);

// Selectors for specific state slices
export const useErrors = () => useErrorStore((state) => state.errors);
export const useActiveError = () => useErrorStore((state) => state.activeError);
export const useErrorHistory = () => useErrorStore((state) => state.errorHistory);
export const useNotifications = () => useErrorStore((state) => state.notifications);
export const useRecoveryAttempts = () => useErrorStore((state) => state.recoveryAttempts);
export const useErrorMetrics = () => useErrorStore((state) => state.metrics);
export const useErrorSettings = () => useErrorStore((state) => state.settings);

// Selectors for actions
export const useErrorActions = () => useErrorStore((state) => ({
  addError: state.addError,
  removeError: state.removeError,
  clearErrors: state.clearErrors,
  setActiveError: state.setActiveError
}));

export const useNotificationActions = () => useErrorStore((state) => ({
  addNotification: state.addNotification,
  removeNotification: state.removeNotification,
  markNotificationRead: state.markNotificationRead,
  clearNotifications: state.clearNotifications
}));

export const useRecoveryActions = () => useErrorStore((state) => ({
  addRecoveryAttempt: state.addRecoveryAttempt,
  updateRecoveryAttempt: state.updateRecoveryAttempt,
  clearRecoveryAttempts: state.clearRecoveryAttempts
}));

export const useMetricsActions = () => useErrorStore((state) => ({
  updateMetrics: state.updateMetrics,
  resetMetrics: state.resetMetrics
}));

export const useSettingsActions = () => useErrorStore((state) => ({
  updateSettings: state.updateSettings,
  loadSettings: state.loadSettings,
  resetSettings: state.resetSettings
}));

// Utility hooks
export const useErrorById = (errorId: string) => useErrorStore(
  (state) => state.errors.find((error: ErrorInfo) => error.id === errorId)
);

export const useErrorsByCategory = (category: ErrorCategory) => useErrorStore(
  (state) => state.errors.filter((error: ErrorInfo) => error.category === category)
);

export const useErrorsBySeverity = (severity: ErrorSeverity) => useErrorStore(
  (state) => state.errors.filter((error: ErrorInfo) => error.severity === severity)
);

export const useNotificationById = (notificationId: string) => useErrorStore(
  (state) => state.notifications.find((notification: ErrorNotification) => notification.id === notificationId)
);

export const useUnreadNotifications = () => useErrorStore(
  (state) => state.notifications.filter((notification: ErrorNotification) => !notification.read)
);

export const useRecentErrors = (limit: number = 10) => useErrorStore(
  (state) => state.errors.slice(-limit)
);

export const useRecentRecoveryAttempts = (limit: number = 10) => useErrorStore(
  (state) => state.recoveryAttempts.slice(-limit)
);

// Computed selectors
export const useErrorStats = () => useErrorStore((state) => ({
  totalErrors: state.metrics.totalErrors,
  totalRecoveries: state.recoveryAttempts.length,
  successRate: state.recoveryAttempts.length > 0 
    ? (state.recoveryAttempts.filter((a: RecoveryAttempt) => a.status === 'success').length / state.recoveryAttempts.length) * 100 
    : 0,
  criticalErrors: state.metrics.errorsBySeverity[ErrorSeverity.CRITICAL],
  fatalErrors: state.metrics.errorsBySeverity[ErrorSeverity.FATAL]
}));

export default useErrorStore;

// UI Store compatibility functions for use-error-recovery.ts
export const useUIStore = () => {
  const addError = useErrorStore((state) => state.addError);
  const clearErrors = useErrorStore((state) => state.clearErrors);
  
  return {
    setError: (message: string) => {
      const error: ErrorInfo = {
        id: Date.now().toString(),
        type: 'component_error' as ErrorInfo['type'],
        category: ErrorCategory.UI_COMPONENT,
        severity: ErrorSeverity.MEDIUM,
        title: 'UI Error',
        message,
        technicalDetails: message,
        resolutionSteps: [],
        retryPossible: true,
        userActionRequired: false,
        timestamp: new Date().toISOString(),
      };
      addError(error);
    },
    clearError: () => {
      clearErrors();
    }
  };
};

// Helper function to create error info (not a React hook)
export const createErrorInfo = (message: string, key?: string): ErrorInfo => {
  return {
    id: key ? `${key}-${Date.now()}` : Date.now().toString(),
    type: 'component_error' as ErrorInfo['type'],
    category: ErrorCategory.UI_COMPONENT,
    severity: ErrorSeverity.MEDIUM,
    title: 'UI Error',
    message,
    technicalDetails: message,
    resolutionSteps: [],
    retryPossible: true,
    userActionRequired: false,
    timestamp: new Date().toISOString(),
  };
};
