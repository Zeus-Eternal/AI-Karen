"use client";
import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useToast } from "@/hooks/use-toast";
import {
  Bell,
  BellOff,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
  Settings,
  Activity,
  Zap,
  Shield,
  RefreshCw,
  Clock
} from 'lucide-react';
interface NotificationSettings {
  provider_status_changes: boolean;
  fallback_notifications: boolean;
  recovery_notifications: boolean;
  system_health_alerts: boolean;
  performance_alerts: boolean;
  error_notifications: boolean;
  maintenance_notifications: boolean;
}
interface ProviderNotification {
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
  metadata?: Record<string, any>;
}
interface ProviderNotificationSystemProps {
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
      toast({
        title: "Save Failed",
        description: "Could not save notification settings.",
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
      return <AlertCircle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
    }
    switch (type) {
      case 'status_change':
        return <Activity className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />;
      case 'fallback':
        return <AlertTriangle className="h-4 w-4 text-yellow-600 sm:w-auto md:w-full" />;
      case 'recovery':
        return <CheckCircle2 className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'system_health':
        return <Shield className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
      case 'performance':
        return <Zap className="h-4 w-4 text-orange-600 sm:w-auto md:w-full" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
      case 'maintenance':
        return <Settings className="h-4 w-4 text-gray-600 sm:w-auto md:w-full" />;
      default:
        return <Info className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />;
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
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary sm:w-auto md:w-full" />
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Loading notifications...</p>
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
              <Bell className="h-5 w-5 sm:w-auto md:w-full" />
              <CardTitle>Provider Notifications</CardTitle>
              {unreadCount > 0 && (
                <Badge variant="destructive" className="text-xs sm:text-sm md:text-base">
                  {unreadCount} new
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                variant="outline"
                size="sm"
                onClick={() = aria-label="Button"> setShowSettings(!showSettings)}
              >
                <Settings className="h-4 w-4 sm:w-auto md:w-full" />
              </Button>
              {activeNotifications.length > 0 && (
                <button
                  variant="outline"
                  size="sm"
                  onClick={clearAllNotifications}
                 aria-label="Button">
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
              Configure which types of notifications you want to receive
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(settings).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <Label htmlFor={key} className="text-sm capitalize md:text-base lg:text-lg">
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
                <BellOff className="h-8 w-8 mx-auto text-muted-foreground sm:w-auto md:w-full" />
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No notifications</p>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
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
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            {notification.provider}
                          </Badge>
                        )}
                      </div>
                      <CardDescription className="text-sm md:text-base lg:text-lg">
                        {notification.message}
                      </CardDescription>
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground sm:text-sm md:text-base">
                        <Clock className="h-3 w-3 sm:w-auto md:w-full" />
                        <span>{new Date(notification.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    variant="ghost"
                    size="sm"
                    onClick={() = aria-label="Button"> dismissNotification(notification.id)}
                  >
                    <X className="h-4 w-4 sm:w-auto md:w-full" />
                  </Button>
                </div>
              </CardHeader>
              {/* Actions */}
              {notification.actions && notification.actions.length > 0 && (
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-2">
                    {notification.actions.map((action) => (
                      <button
                        key={action.id}
                        variant={action.variant || 'default'}
                        size="sm"
                        onClick={() = aria-label="Button"> handleNotificationAction(notification.id, action.id)}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              )}
              {/* Metadata */}
              {notification.metadata && (
                <CardContent className="pt-0">
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {notification.type === 'fallback' && notification.metadata.fallback_provider && (
                      <p>Using fallback: {notification.metadata.fallback_provider}</p>
                    )}
                    {notification.type === 'system_health' && notification.metadata.failed_providers && (
                      <p>Failed providers: {notification.metadata.failed_providers.join(', ')}</p>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>
      {/* System Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-4 w-4 sm:w-auto md:w-full" />
            System Status Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="p-3 bg-green-50 rounded-lg sm:p-4 md:p-6">
              <div className="text-lg font-semibold text-green-600">
                {notifications.filter(n => n.type === 'recovery' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Recoveries</div>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg sm:p-4 md:p-6">
              <div className="text-lg font-semibold text-yellow-600">
                {notifications.filter(n => n.type === 'fallback' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Fallbacks</div>
            </div>
            <div className="p-3 bg-red-50 rounded-lg sm:p-4 md:p-6">
              <div className="text-lg font-semibold text-red-600">
                {notifications.filter(n => n.priority === 'critical' && !n.dismissed).length}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Critical</div>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg sm:p-4 md:p-6">
              <div className="text-lg font-semibold text-blue-600">
                {activeNotifications.length}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Total Active</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
export default ProviderNotificationSystem;
