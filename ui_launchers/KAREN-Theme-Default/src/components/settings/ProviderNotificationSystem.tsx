"use client";

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from "@/hooks/use-toast";

import { 
  Bell, 
  Settings, 
  X, 
  BellOff, 
  Clock, 
  RefreshCw,
  AlertCircle,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Shield,
  Zap,
  Info
} from 'lucide-react';

export interface NotificationSettings {
  provider_status_changes: boolean;
  fallback_notifications: boolean;
  recovery_notifications: boolean;
  system_health_alerts: boolean;
  performance_alerts: boolean;
  error_notifications: boolean;
  maintenance_notifications: boolean;
}

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null;
};

const getMetadataString = (
  metadata: Record<string, unknown> | undefined,
  key: string
): string | undefined => {
  if (!metadata) {
    return undefined;
  }
  const value = metadata[key];
  return typeof value === 'string' ? value : undefined;
};

const getMetadataStringArray = (
  metadata: Record<string, unknown> | undefined,
  key: string
): string[] => {
  if (!metadata) {
    return [];
  }
  const value = metadata[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string');
};

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

export interface ProviderNotificationSystemProps {
  onNotificationAction?: (notificationId: string, actionId: string) => void;
  realTimeUpdates?: boolean;
}

export function ProviderNotificationSystem({
  onNotificationAction,
  realTimeUpdates = true
}: ProviderNotificationSystemProps) {
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
  const [showSettings, setShowSettings] = useState(false);
  const { toast } = useToast();

  // Load notifications and settings
  useEffect(() => {
    loadNotifications();
    loadSettings();
  }, []);

  // Real-time updates via WebSocket or polling
  useEffect(() => {
    if (!realTimeUpdates) return;
    const interval = setInterval(() => {
      loadNotifications();
    }, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [realTimeUpdates]);

  const loadNotifications = async () => {
    try {
      // Mock data - in real implementation, this would come from the backend
      const mockNotifications: ProviderNotification[] = [
        {
          id: '1',
          type: 'status_change',
          priority: 'medium',
          title: 'OpenAI Provider Available',
          message: 'OpenAI provider has recovered and is now available for requests.',
          provider: 'openai',
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          read: false,
          dismissed: false,
          actions: [
            { id: 'test', label: 'Test Provider', action: 'retry' },
            { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
          ]
        },
        {
          id: '2',
          type: 'fallback',
          priority: 'high',
          title: 'Fallback to Local Provider',
          message: 'Primary provider (Gemini) is unavailable. Requests are being routed to local provider.',
          provider: 'gemini',
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          read: false,
          dismissed: false,
          actions: [
            { id: 'check_primary', label: 'Check Primary', action: 'retry' },
            { id: 'configure', label: 'Configure', action: 'configure' },
            { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
          ],
          metadata: { fallback_provider: 'local', primary_provider: 'gemini' }
        },
        {
          id: '3',
          type: 'system_health',
          priority: 'critical',
          title: 'Multiple Providers Failing',
          message: 'System health alert: 3 out of 5 providers are currently unavailable. System is running in degraded mode.',
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          read: true,
          dismissed: false,
          actions: [
            { id: 'view_details', label: 'View Details', action: 'view_details' },
            { id: 'retry_all', label: 'Retry All', action: 'retry' },
            { id: 'dismiss', label: 'Dismiss', action: 'dismiss', variant: 'outline' }
          ],
          metadata: { failed_providers: ['deepseek', 'anthropic', 'cohere'], healthy_providers: ['openai', 'local'] }
        }
      ];
      setNotifications(mockNotifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      // Load from localStorage or backend
      const savedSettings = localStorage.getItem('provider_notification_settings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = useCallback(async (newSettings: NotificationSettings) => {
    try {
      localStorage.setItem('provider_notification_settings', JSON.stringify(newSettings));
      setSettings(newSettings);
      toast({
        title: "Settings Saved",
        description: "Notification preferences have been updated.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : undefined;
      toast({
        title: "Save Failed",
        description: message || "Could not save notification settings.",
        variant: "destructive",
      });
    }
  }, [toast]);

  const markAsRead = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
  };

  const dismissNotification = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, dismissed: true } : n)
    );
  };

  const renderNotificationMetadata = (notification: ProviderNotification) => {
    const metadata = isRecord(notification.metadata) ? notification.metadata : undefined;
    if (!metadata) {
      return null;
    }
    const fallbackProvider = getMetadataString(metadata, 'fallback_provider');
    const failedProviders = getMetadataStringArray(metadata, 'failed_providers');
    if (!fallbackProvider && failedProviders.length === 0) {
      return null;
    }
    return (
      <CardContent className="pt-0">
        <div className="text-xs text-muted-foreground">
          {notification.type === 'fallback' && fallbackProvider && (
            <p>Using fallback: {fallbackProvider}</p>
          )}
          {notification.type === 'system_health' && failedProviders.length > 0 && (
            <p>Failed providers: {failedProviders.join(', ')}</p>
          )}
        </div>
      </CardContent>
    );
  };

  const handleNotificationAction = (notificationId: string, actionId: string) => {
    const notification = notifications.find(n => n.id === notificationId);
    if (!notification) return;

    const action = notification.actions?.find(a => a.id === actionId);
    if (!action) return;

    switch (action.action) {
      case 'dismiss':
        dismissNotification(notificationId);
        break;
      case 'retry':
        // Handle retry action
        onNotificationAction?.(notificationId, actionId);
        markAsRead(notificationId);
        break;
      case 'configure':
        // Handle configure action
        onNotificationAction?.(notificationId, actionId);
        markAsRead(notificationId);
        break;
      case 'view_details':
        // Handle view details action
        onNotificationAction?.(notificationId, actionId);
        markAsRead(notificationId);
        break;
    }
  };

  const clearAllNotifications = () => {
    setNotifications(prev => prev.map(n => ({ ...n, dismissed: true })));
    toast({
      title: "Notifications Cleared",
      description: "All notifications have been dismissed.",
    });
  };

  const getNotificationIcon = (type: string, priority: string) => {
    if (priority === 'critical') {
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    }
    switch (type) {
      case 'status_change':
        return <Activity className="h-4 w-4 text-blue-600" />;
      case 'fallback':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'recovery':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'system_health':
        return <Shield className="h-4 w-4 text-red-600" />;
      case 'performance':
        return <Zap className="h-4 w-4 text-orange-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'maintenance':
        return <Settings className="h-4 w-4 text-gray-600" />;
      default:
        return <Info className="h-4 w-4 text-blue-600" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const activeNotifications = notifications.filter(n => !n.dismissed);
  const unreadCount = activeNotifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center space-y-2">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground">Loading notifications...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <CardTitle>Provider Notifications</CardTitle>
              {unreadCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {unreadCount} new
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="h-4 w-4" />
              </Button>
              {activeNotifications.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllNotifications}
                >
                  Clear All
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Notification Settings */}
      {showSettings && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Notification Settings</CardTitle>
            <CardDescription>
              Configure which types of provider notifications you want to receive
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(settings).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <Label htmlFor={key} className="text-sm capitalize">
                    {key.replace(/_/g, ' ')}
                  </Label>
                  <Switch
                    id={key}
                    checked={value}
                    onCheckedChange={(checked) => {
                      const newSettings = { ...settings, [key]: checked };
                      saveSettings(newSettings);
                    }}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notifications List */}
      <div className="space-y-3">
        {activeNotifications.length === 0 ? (
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center space-y-2">
                <BellOff className="h-8 w-8 mx-auto text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No notifications</p>
                <p className="text-xs text-muted-foreground">
                  You'll see provider status updates and alerts here
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          activeNotifications.map((notification) => (
            <Card
              key={notification.id}
              className={`transition-all hover:shadow-md ${
                !notification.read ? 'border-primary/50 bg-primary/5' : ''
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getNotificationIcon(notification.type, notification.priority)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <CardTitle className="text-base">{notification.title}</CardTitle>
                        <Badge className={`text-xs ${getPriorityColor(notification.priority)}`}>
                          {notification.priority}
                        </Badge>
                        {notification.provider && (
                          <Badge variant="outline" className="text-xs">
                            {notification.provider}
                          </Badge>
                        )}
                      </div>
                      <CardDescription className="text-sm">
                        {notification.message}
                      </CardDescription>
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{new Date(notification.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => dismissNotification(notification.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              
              {/* Actions */}
              {notification.actions && notification.actions.length > 0 && (
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-2">
                    {notification.actions.map((action) => (
                      <Button
                        key={action.id}
                        variant={action.variant || 'default'}
                        size="sm"
                        onClick={() => handleNotificationAction(notification.id, action.id)}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              )}
              
              {/* Metadata */}
              {renderNotificationMetadata(notification)}
            </Card>
          ))
        )}
      </div>

      {/* System Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-4 w-4" />
            System Status Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="p-3 bg-green-50 rounded-lg">
              <div className="text-lg font-semibold text-green-600">
                {notifications.filter(n => n.type === 'recovery' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground">Recoveries</div>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <div className="text-lg font-semibold text-yellow-600">
                {notifications.filter(n => n.type === 'fallback' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground">Fallbacks</div>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <div className="text-lg font-semibold text-red-600">
                {notifications.filter(n => n.priority === 'critical' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground">Critical</div>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="text-lg font-semibold text-blue-600">
                {activeNotifications.length}
              </div>
              <div className="text-xs text-muted-foreground">Total Active</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ProviderNotificationSystem;