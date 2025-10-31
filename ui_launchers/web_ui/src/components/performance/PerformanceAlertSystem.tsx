/**
 * Performance Alert System
 * Manages threshold-based notifications and escalation procedures
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  AlertTriangle, 
  Bell, 
  BellOff, 
  CheckCircle, 
  Clock, 
  Mail, 
  MessageSquare, 
  Settings, 
  Trash2,
  X
} from 'lucide-react';
import { 
  performanceMonitor, 
  PerformanceAlert, 
  PerformanceThresholds 
} from '@/services/performance-monitor';

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  threshold: number;
  type: 'warning' | 'critical';
  enabled: boolean;
  notifications: {
    email: boolean;
    push: boolean;
    slack: boolean;
  };
  escalation: {
    enabled: boolean;
    delay: number; // minutes
    recipients: string[];
  };
}

interface PerformanceAlertSystemProps {
  onAlert?: (alert: PerformanceAlert) => void;
}

export const PerformanceAlertSystem: React.FC<PerformanceAlertSystemProps> = ({
  onAlert,
}) => {
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [newRule, setNewRule] = useState<Partial<AlertRule>>({
    name: '',
    metric: 'lcp',
    threshold: 2500,
    type: 'warning',
    enabled: true,
    notifications: {
      email: false,
      push: true,
      slack: false,
    },
    escalation: {
      enabled: false,
      delay: 15,
      recipients: [],
    },
  });

  // Load alerts and rules
  useEffect(() => {
    const loadData = () => {
      setAlerts(performanceMonitor.getAlerts(50));
    };

    loadData();
    const interval = setInterval(loadData, 5000);

    // Subscribe to new alerts
    const unsubscribe = performanceMonitor.onAlert((alert) => {
      setAlerts(prev => [alert, ...prev.slice(0, 49)]);
      
      // Check if alert matches any rules
      const matchingRule = alertRules.find(rule => 
        rule.enabled && 
        rule.metric === alert.metric && 
        rule.type === alert.type
      );

      if (matchingRule) {
        handleAlertNotification(alert, matchingRule);
      }

      onAlert?.(alert);
    });

    // Load default alert rules
    setAlertRules([
      {
        id: '1',
        name: 'LCP Critical',
        metric: 'lcp',
        threshold: 4000,
        type: 'critical',
        enabled: true,
        notifications: { email: true, push: true, slack: false },
        escalation: { enabled: true, delay: 5, recipients: ['admin@example.com'] },
      },
      {
        id: '2',
        name: 'Memory Usage High',
        metric: 'memory-usage',
        threshold: 85,
        type: 'warning',
        enabled: true,
        notifications: { email: false, push: true, slack: true },
        escalation: { enabled: false, delay: 15, recipients: [] },
      },
      {
        id: '3',
        name: 'FID Poor',
        metric: 'fid',
        threshold: 300,
        type: 'critical',
        enabled: true,
        notifications: { email: true, push: true, slack: true },
        escalation: { enabled: true, delay: 10, recipients: ['dev-team@example.com'] },
      },
    ]);

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [alertRules, onAlert]);

  const handleAlertNotification = async (alert: PerformanceAlert, rule: AlertRule) => {
    // Simulate notification sending
    console.log(`Sending notifications for alert: ${alert.message}`);
    
    if (rule.notifications.push) {
      // Send push notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`Performance ${alert.type}`, {
          body: alert.message,
          icon: '/favicon.ico',
        });
      }
    }

    if (rule.notifications.email) {
      // Send email notification (would integrate with email service)
      console.log('Sending email notification');
    }

    if (rule.notifications.slack) {
      // Send Slack notification (would integrate with Slack API)
      console.log('Sending Slack notification');
    }

    // Handle escalation
    if (rule.escalation.enabled) {
      setTimeout(() => {
        console.log(`Escalating alert to: ${rule.escalation.recipients.join(', ')}`);
      }, rule.escalation.delay * 60 * 1000);
    }
  };

  const addAlertRule = () => {
    if (!newRule.name || !newRule.metric || !newRule.threshold) return;

    const rule: AlertRule = {
      id: Date.now().toString(),
      name: newRule.name,
      metric: newRule.metric,
      threshold: newRule.threshold,
      type: newRule.type || 'warning',
      enabled: newRule.enabled ?? true,
      notifications: newRule.notifications || {
        email: false,
        push: true,
        slack: false,
      },
      escalation: newRule.escalation || {
        enabled: false,
        delay: 15,
        recipients: [],
      },
    };

    setAlertRules(prev => [...prev, rule]);
    setNewRule({
      name: '',
      metric: 'lcp',
      threshold: 2500,
      type: 'warning',
      enabled: true,
      notifications: { email: false, push: true, slack: false },
      escalation: { enabled: false, delay: 15, recipients: [] },
    });
  };

  const updateAlertRule = (id: string, updates: Partial<AlertRule>) => {
    setAlertRules(prev => prev.map(rule => 
      rule.id === id ? { ...rule, ...updates } : rule
    ));
  };

  const deleteAlertRule = (id: string) => {
    setAlertRules(prev => prev.filter(rule => rule.id !== id));
  };

  const dismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  const getAlertIcon = (type: 'warning' | 'critical') => {
    return type === 'critical' ? (
      <AlertTriangle className="h-4 w-4 text-red-500" />
    ) : (
      <AlertTriangle className="h-4 w-4 text-yellow-500" />
    );
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const getMetricDisplayName = (metric: string) => {
    const names: Record<string, string> = {
      'lcp': 'Largest Contentful Paint',
      'fid': 'First Input Delay',
      'cls': 'Cumulative Layout Shift',
      'fcp': 'First Contentful Paint',
      'ttfb': 'Time to First Byte',
      'page-load': 'Page Load Time',
      'memory-usage': 'Memory Usage',
      'api-call': 'API Call Duration',
    };
    return names[metric] || metric;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">Performance Alerts</h3>
          <p className="text-muted-foreground">
            Monitor and manage performance alerts and notifications
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={requestNotificationPermission}>
            <Bell className="h-4 w-4 mr-2" />
            Enable Notifications
          </Button>
          <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Settings className="h-4 w-4 mr-2" />
                Configure Rules
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Alert Rules Configuration</DialogTitle>
                <DialogDescription>
                  Configure performance alert rules and notification settings
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-6">
                {/* Add New Rule */}
                <Card>
                  <CardHeader>
                    <CardTitle>Add New Alert Rule</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="rule-name">Rule Name</Label>
                        <Input
                          id="rule-name"
                          value={newRule.name || ''}
                          onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="Enter rule name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="rule-metric">Metric</Label>
                        <select
                          id="rule-metric"
                          className="w-full p-2 border rounded-md"
                          value={newRule.metric || 'lcp'}
                          onChange={(e) => setNewRule(prev => ({ ...prev, metric: e.target.value }))}
                        >
                          <option value="lcp">Largest Contentful Paint</option>
                          <option value="fid">First Input Delay</option>
                          <option value="cls">Cumulative Layout Shift</option>
                          <option value="fcp">First Contentful Paint</option>
                          <option value="ttfb">Time to First Byte</option>
                          <option value="page-load">Page Load Time</option>
                          <option value="memory-usage">Memory Usage</option>
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="rule-threshold">Threshold</Label>
                        <Input
                          id="rule-threshold"
                          type="number"
                          value={newRule.threshold || 0}
                          onChange={(e) => setNewRule(prev => ({ ...prev, threshold: Number(e.target.value) }))}
                        />
                      </div>
                      <div>
                        <Label htmlFor="rule-type">Alert Type</Label>
                        <select
                          id="rule-type"
                          className="w-full p-2 border rounded-md"
                          value={newRule.type || 'warning'}
                          onChange={(e) => setNewRule(prev => ({ ...prev, type: e.target.value as 'warning' | 'critical' }))}
                        >
                          <option value="warning">Warning</option>
                          <option value="critical">Critical</option>
                        </select>
                      </div>
                    </div>
                    <Button onClick={addAlertRule} className="w-full">
                      Add Rule
                    </Button>
                  </CardContent>
                </Card>

                {/* Existing Rules */}
                <div className="space-y-2">
                  <h4 className="font-medium">Existing Rules</h4>
                  <ScrollArea className="h-64">
                    {alertRules.map((rule) => (
                      <Card key={rule.id} className="mb-2">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center space-x-2">
                                <h5 className="font-medium">{rule.name}</h5>
                                <Badge variant={rule.type === 'critical' ? 'destructive' : 'secondary'}>
                                  {rule.type}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {getMetricDisplayName(rule.metric)} > {rule.threshold}
                              </p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Switch
                                checked={rule.enabled}
                                onCheckedChange={(enabled) => updateAlertRule(rule.id, { enabled })}
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => deleteAlertRule(rule.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </ScrollArea>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Alert Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
            <p className="text-xs text-muted-foreground">
              {alerts.filter(a => a.type === 'critical').length} critical, {alerts.filter(a => a.type === 'warning').length} warnings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alert Rules</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alertRules.length}</div>
            <p className="text-xs text-muted-foreground">
              {alertRules.filter(r => r.enabled).length} enabled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Alert</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.length > 0 ? formatTimestamp(alerts[0].timestamp).split(' ')[1] : 'None'}
            </div>
            <p className="text-xs text-muted-foreground">
              {alerts.length > 0 ? formatTimestamp(alerts[0].timestamp).split(' ')[0] : 'No recent alerts'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alert List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>
                Performance alerts and notifications
              </CardDescription>
            </div>
            {alerts.length > 0 && (
              <Button variant="outline" onClick={clearAllAlerts}>
                Clear All
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium">No Active Alerts</h3>
              <p className="text-muted-foreground">
                Your application is performing well!
              </p>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <Alert key={alert.id} variant={alert.type === 'critical' ? 'destructive' : 'default'}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2">
                        {getAlertIcon(alert.type)}
                        <div>
                          <AlertTitle className="flex items-center space-x-2">
                            <span>{getMetricDisplayName(alert.metric)}</span>
                            <Badge variant={alert.type === 'critical' ? 'destructive' : 'secondary'}>
                              {alert.type}
                            </Badge>
                          </AlertTitle>
                          <AlertDescription>
                            {alert.message}
                            <br />
                            <span className="text-xs text-muted-foreground">
                              {formatTimestamp(alert.timestamp)}
                            </span>
                          </AlertDescription>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => dismissAlert(alert.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </Alert>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};