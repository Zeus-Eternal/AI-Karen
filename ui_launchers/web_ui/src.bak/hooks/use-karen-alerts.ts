/**
 * React Hook for Karen's Alert System
 * 
 * Provides easy access to the AlertManager service with React integration
 */

import { useEffect, useState, useCallback } from 'react';
import { alertManager } from '@/services/alertManager';
import type {
  KarenAlert,
  AlertSettings,
  AlertHistory,
  AlertMetrics,
  AlertResult,
} from '@/types/karen-alerts';

/**
 * Hook state interface
 */
interface UseKarenAlertsState {
  activeAlerts: KarenAlert[];
  queuedAlerts: KarenAlert[];
  settings: AlertSettings;
  history: AlertHistory;
  metrics: AlertMetrics;
  isInitialized: boolean;
}

/**
 * Hook return interface
 */
interface UseKarenAlertsReturn extends UseKarenAlertsState {
  // Alert methods
  showAlert: (alertData: Omit<KarenAlert, 'id' | 'timestamp'>) => Promise<AlertResult>;
  showSuccess: (title: string, message: string, options?: Partial<KarenAlert>) => Promise<AlertResult>;
  showError: (title: string, message: string, options?: Partial<KarenAlert>) => Promise<AlertResult>;
  showWarning: (title: string, message: string, options?: Partial<KarenAlert>) => Promise<AlertResult>;
  showInfo: (title: string, message: string, options?: Partial<KarenAlert>) => Promise<AlertResult>;
  
  // Management methods
  dismissAlert: (alertId: string) => Promise<AlertResult>;
  dismissAllAlerts: () => Promise<AlertResult[]>;
  clearQueue: () => void;
  
  // Settings methods
  updateSettings: (newSettings: Partial<AlertSettings>) => Promise<AlertResult>;
  
  // Utility methods
  refresh: () => void;
}

/**
 * Custom hook for using Karen's alert system
 */
export function useKarenAlerts(): UseKarenAlertsReturn {
  const [state, setState] = useState<UseKarenAlertsState>({
    activeAlerts: [],
    queuedAlerts: [],
    settings: alertManager.getSettings(),
    history: alertManager.getHistory(),
    metrics: alertManager.getMetrics(),
    isInitialized: false,
  });

  // Refresh state from AlertManager
  const refresh = useCallback(() => {
    setState({
      activeAlerts: alertManager.getActiveAlerts(),
      queuedAlerts: alertManager.getQueuedAlerts(),
      settings: alertManager.getSettings(),
      history: alertManager.getHistory(),
      metrics: alertManager.getMetrics(),
      isInitialized: true,
    });
  }, []);

  // Initialize and set up event listeners
  useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        await alertManager.initialize();
        if (mounted) {
          refresh();
        }
      } catch (error) {
        console.error('Failed to initialize AlertManager in hook:', error);
      }
    };

    initialize();

    // Set up event listeners
    const unsubscribeAlertShown = alertManager.addEventListener('alert-shown', () => {
      if (mounted) refresh();
    });

    const unsubscribeAlertDismissed = alertManager.addEventListener('alert-dismissed', () => {
      if (mounted) refresh();
    });

    const unsubscribeSettingsUpdated = alertManager.addEventListener('settings-updated', () => {
      if (mounted) refresh();
    });

    const unsubscribeActionClicked = alertManager.addEventListener('alert-action-clicked', () => {
      if (mounted) refresh();
    });

    return () => {
      mounted = false;
      unsubscribeAlertShown();
      unsubscribeAlertDismissed();
      unsubscribeSettingsUpdated();
      unsubscribeActionClicked();
    };
  }, [refresh]);

  // Wrapped methods that refresh state after operations
  const showAlert = useCallback(async (alertData: Omit<KarenAlert, 'id' | 'timestamp'>) => {
    const result = await alertManager.showAlert(alertData);
    refresh();
    return result;
  }, [refresh]);

  const showSuccess = useCallback(async (title: string, message: string, options?: Partial<KarenAlert>) => {
    const result = await alertManager.showSuccess(title, message, options);
    refresh();
    return result;
  }, [refresh]);

  const showError = useCallback(async (title: string, message: string, options?: Partial<KarenAlert>) => {
    const result = await alertManager.showError(title, message, options);
    refresh();
    return result;
  }, [refresh]);

  const showWarning = useCallback(async (title: string, message: string, options?: Partial<KarenAlert>) => {
    const result = await alertManager.showWarning(title, message, options);
    refresh();
    return result;
  }, [refresh]);

  const showInfo = useCallback(async (title: string, message: string, options?: Partial<KarenAlert>) => {
    const result = await alertManager.showInfo(title, message, options);
    refresh();
    return result;
  }, [refresh]);

  const dismissAlert = useCallback(async (alertId: string) => {
    const result = await alertManager.dismissAlert(alertId);
    refresh();
    return result;
  }, [refresh]);

  const dismissAllAlerts = useCallback(async () => {
    const results = await alertManager.dismissAllAlerts();
    refresh();
    return results;
  }, [refresh]);

  const clearQueue = useCallback(() => {
    alertManager.clearQueue();
    refresh();
  }, [refresh]);

  const updateSettings = useCallback(async (newSettings: Partial<AlertSettings>) => {
    const result = await alertManager.updateSettings(newSettings);
    refresh();
    return result;
  }, [refresh]);

  return {
    ...state,
    showAlert,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissAlert,
    dismissAllAlerts,
    clearQueue,
    updateSettings,
    refresh,
  };
}

/**
 * Simplified hook for basic alert operations
 */
export function useSimpleAlerts() {
  const { showSuccess, showError, showWarning, showInfo } = useKarenAlerts();

  return {
    success: showSuccess,
    error: showError,
    warning: showWarning,
    info: showInfo,
  };
}