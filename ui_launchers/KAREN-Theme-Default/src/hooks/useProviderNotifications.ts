"use client";
import { useState, useEffect, useCallback } from 'react';
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from '@/lib/karen-backend';
export interface ProviderNotification {
  id: string;
  type: 'status_change' | 'fallback' | 'recovery' | 'system_health' | 'performance' | 'error' | 'maintenance';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  provider?: string;
  timestamp: string;
  read: boolean;
  dismissed: boolean;
  actions?: Array<{
    id: string;
    label: string;
    action: 'retry' | 'configure' | 'dismiss' | 'view_details';
    variant?: 'default' | 'destructive' | 'outline';
  }>;
  metadata?: Record<string, unknown>;
}
export interface NotificationSettings {
  provider_status_changes: boolean;
  fallback_notifications: boolean;
  recovery_notifications: boolean;
  system_health_alerts: boolean;
  performance_alerts: boolean;
  error_notifications: boolean;
  maintenance_notifications: boolean;
}
export interface UseProviderNotificationsOptions {
  realTimeUpdates?: boolean;
  autoToast?: boolean;
  maxNotifications?: number;
}
export function useProviderNotifications(options: UseProviderNotificationsOptions = {}) {
  const {
    realTimeUpdates = true,
    autoToast = true,
    maxNotifications = 50
  } = options;
  const [notifications, setNotifications] = useState<ProviderNotification[]>([]);
  const [settings, setSettings] = useState<NotificationSettings>({
    provider_status_changes: true,
    fallback_notifications: true,
    recovery_notifications: true,
    system_health_alerts: true,
    performance_alerts: false,
    error_notifications: true,
    maintenance_notifications: true
  });

  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const { toast } = useToast();
  const backend = getKarenBackend();

  const logNotificationError = useCallback((message: string, error: unknown) => {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(message, error);
    }
  }, []);
  const loadNotifications = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<ProviderNotification[]>('/api/providers/notifications');
      setNotifications(response || []);
    } catch (error: unknown) {
      logNotificationError('Failed to load provider notifications', error);
      // Use mock data for development
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, [backend, logNotificationError]);
  const loadSettings = useCallback(async () => {
    try {
      // Try to load from backend first
      const response = await backend.makeRequestPublic<NotificationSettings>('/api/providers/notifications/settings');
      if (response) {
        setSettings(response);
        return;
      }
    } catch (error: unknown) {
      logNotificationError('Failed to load provider notification settings from backend', error);
    }
    // Fallback to localStorage
    try {
      const savedSettings = localStorage.getItem('provider_notification_settings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error: unknown) {
      logNotificationError('Failed to load provider notification settings from localStorage', error);
    }
  }, [backend, logNotificationError]);
  const saveSettings = useCallback(async (newSettings: NotificationSettings) => {
    try {
      // Try to save to backend first
      await backend.makeRequestPublic('/api/providers/notifications/settings', {
        method: 'POST',
        body: JSON.stringify(newSettings)
      });
    } catch (error: unknown) {
      logNotificationError('Failed to save provider notification settings to backend', error);
    }
    // Always save to localStorage as backup
    try {
      localStorage.setItem('provider_notification_settings', JSON.stringify(newSettings));
    } catch (error: unknown) {
      logNotificationError('Failed to persist provider notification settings locally', error);
    }
    setSettings(newSettings);
  }, [backend, logNotificationError]);
  const addNotification = useCallback((notification: ProviderNotification) => {
    setNotifications(prev => {
      // Check if notification type is enabled
      const settingKey = `${notification.type}_notifications` as keyof NotificationSettings;
      if (settingKey in settings && !settings[settingKey]) {
        return prev; // Don't add if disabled
      }
      // Avoid duplicates
      if (prev.some(n => n.id === notification.id)) {
        return prev;
      }
      // Add notification and limit total count
      const updated = [notification, ...prev].slice(0, maxNotifications);
      // Show toast for high priority notifications
      if (autoToast && (notification.priority === 'high' || notification.priority === 'critical')) {
        toast({
          title: notification.title,
          description: notification.message,
          variant: notification.priority === 'critical' ? 'destructive' : 'default',
        });
      }
      return updated;
    });
  }, [settings, maxNotifications, autoToast, toast]);
  // Load initial notifications and settings
  useEffect(() => {
    loadNotifications();
    loadSettings();
  }, [loadNotifications, loadSettings]);
  // Set up real-time updates
  useEffect(() => {
    if (!realTimeUpdates) return;
    let eventSource: EventSource | null = null;
    let pollInterval: NodeJS.Timeout | null = null;
    const setupRealTimeUpdates = async () => {
      try {
        // Try to establish SSE connection first
        eventSource = new EventSource('/api/providers/notifications/stream');
        eventSource.onopen = () => {
          setConnected(true);
        };
        eventSource.onmessage = (event) => {
          try {
            const notification: ProviderNotification = JSON.parse(event.data);
            addNotification(notification);
          } catch (error: unknown) {
            logNotificationError('Failed to parse provider notification event', error);
          }
        };
        eventSource.onerror = () => {
          setConnected(false);
          // Fallback to polling
          if (!pollInterval) {
            pollInterval = setInterval(() => {
              loadNotifications();
            }, 30000); // Poll every 30 seconds
          }
        };
      } catch (error: unknown) {
        logNotificationError('Failed to establish real-time provider notifications, falling back to polling', error);
        // Fallback to polling
        pollInterval = setInterval(() => {
          loadNotifications();
        }, 30000);
      }
    };
    setupRealTimeUpdates();
    return () => {
      if (eventSource) {
        eventSource.close();
      }
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [realTimeUpdates, loadNotifications, addNotification, logNotificationError]);
  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
    // Update backend
    backend.makeRequestPublic(`/api/providers/notifications/${notificationId}/read`, {
      method: 'POST'
    }).catch((error) => {
      logNotificationError(`Failed to mark provider notification ${notificationId} as read`, error);
    });
  }, [backend, logNotificationError]);
  const dismissNotification = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, dismissed: true } : n)
    );
    // Update backend
    backend.makeRequestPublic(`/api/providers/notifications/${notificationId}/dismiss`, {
      method: 'POST'
    }).catch((error) => {
      logNotificationError(`Failed to dismiss provider notification ${notificationId}`, error);
    });
  }, [backend, logNotificationError]);
  const clearAllNotifications = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, dismissed: true })));
    // Update backend
    backend.makeRequestPublic('/api/providers/notifications/clear-all', {
      method: 'POST'
    }).catch((error) => {
      logNotificationError('Failed to clear provider notifications', error);
    });
  }, [backend, logNotificationError]);
  const createNotification = useCallback((
    type: ProviderNotification['type'],
    title: string,
    message: string,
    options: Partial<Omit<ProviderNotification, 'id' | 'type' | 'title' | 'message' | 'timestamp' | 'read' | 'dismissed'>> = {}
  ) => {
    const notification: ProviderNotification = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      title,
      message,
      priority: options.priority || 'medium',
      timestamp: new Date().toISOString(),
      read: false,
      dismissed: false,
      ...options
    };
    addNotification(notification);
    return notification;
  }, [addNotification]);
  // Notification helpers for common scenarios
  const notifyProviderStatusChange = useCallback((provider: string, status: 'healthy' | 'unhealthy' | 'degraded', previousStatus?: string) => {
    const isRecovery = previousStatus === 'unhealthy' && status === 'healthy';
    const isDegradation = previousStatus === 'healthy' && (status === 'unhealthy' || status === 'degraded');
    let title: string;
    let message: string;
    let priority: ProviderNotification['priority'] = 'medium';
    if (isRecovery) {
      title = `${provider} Provider Recovered`;
      message = `${provider} provider has recovered and is now available for requests.`;
      priority = 'medium';
    } else if (isDegradation) {
      title = `${provider} Provider ${status === 'unhealthy' ? 'Failed' : 'Degraded'}`;
      message = `${provider} provider is now ${status}. Requests may be routed to fallback providers.`;
      priority = status === 'unhealthy' ? 'high' : 'medium';
    } else {
      title = `${provider} Status Changed`;
      message = `${provider} provider status changed to ${status}.`;
    }
    return createNotification(isRecovery ? 'recovery' : 'status_change', title, message, {
      provider,
      priority,
      actions: [
        { id: 'test', label: 'Test Provider', action: 'retry' },
        { id: 'configure', label: 'Configure', action: 'configure' },
        { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
      ]
    });
  }, [createNotification]);
  const notifyFallback = useCallback((primaryProvider: string, fallbackProvider: string, reason?: string) => {
    return createNotification('fallback', 'Fallback Provider Active', 
      `Primary provider (${primaryProvider}) is unavailable. Requests are being routed to ${fallbackProvider}.${reason ? ` Reason: ${reason}` : ''}`, {
      provider: primaryProvider,
      priority: 'high',
      actions: [
        { id: 'check_primary', label: 'Check Primary', action: 'retry' },
        { id: 'configure', label: 'Configure', action: 'configure' },
        { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
      ],
      metadata: { primary_provider: primaryProvider, fallback_provider: fallbackProvider, reason }
    });
  }, [createNotification]);
  const notifySystemHealth = useCallback((failedProviders: string[], healthyProviders: string[], degradedMode: boolean = false) => {
    const title = degradedMode ? 'System in Degraded Mode' : 'Multiple Providers Failing';
    const message = `System health alert: ${failedProviders.length} out of ${failedProviders.length + healthyProviders.length} providers are currently unavailable.${degradedMode ? ' System is running in degraded mode.' : ''}`;
    return createNotification('system_health', title, message, {
      priority: 'critical',
      actions: [
        { id: 'view_details', label: 'View Details', action: 'view_details' },
        { id: 'retry_all', label: 'Retry All', action: 'retry' },
        { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
      ],
      metadata: { failed_providers: failedProviders, healthy_providers: healthyProviders, degraded_mode: degradedMode }
    });
  }, [createNotification]);
  const notifyError = useCallback((provider: string, error: string, errorType?: string) => {
    return createNotification('error', `${provider} Error`, error, {
      provider,
      priority: 'high',
      actions: [
        { id: 'retry', label: 'Retry', action: 'retry' },
        { id: 'view_details', label: 'View Details', action: 'view_details' },
        { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
      ],
      metadata: { error_type: errorType }
    });
  }, [createNotification]);
  // Computed values
  const activeNotifications = notifications.filter(n => !n.dismissed);
  const unreadCount = activeNotifications.filter(n => !n.read).length;
  const criticalCount = activeNotifications.filter(n => n.priority === 'critical').length;
  return {
    // State
    notifications: activeNotifications,
    settings,
    loading,
    connected,
    unreadCount,
    criticalCount,
    // Actions
    markAsRead,
    dismissNotification,
    clearAllNotifications,
    saveSettings,
    addNotification,
    createNotification,
    // Helpers
    notifyProviderStatusChange,
    notifyFallback,
    notifySystemHealth,
    notifyError,
    // Refresh
    refresh: loadNotifications
  };
}

export default useProviderNotifications;
