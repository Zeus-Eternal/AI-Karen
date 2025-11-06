"use client";

/**
 * Resource Alert Manager
 *
 * Manage and configure resource alerts and thresholds for extensions
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertTriangle,
  Bell,
  BellOff,
  Settings,
  RefreshCw,
  Trash2,
  Plus,
  CheckCircle,
  XCircle,
  Clock,
  Cpu,
  Database,
  Wifi,
  HardDrive
} from 'lucide-react';

export interface AlertRule {
  id: string;
  name: string;
  resourceType: 'cpu' | 'memory' | 'network' | 'storage';
  threshold: number;
  severity: 'warning' | 'critical';
  enabled: boolean;
  extensionId?: string;
  extensionName?: string;
  notificationChannels: ('email' | 'webhook' | 'ui')[];
  cooldownMinutes: number;
}

export interface AlertHistory {
  id: string;
  ruleId: string;
  ruleName: string;
  extensionId: string;
  extensionName: string;
  resourceType: 'cpu' | 'memory' | 'network' | 'storage';
  value: number;
  threshold: number;
  severity: 'warning' | 'critical';
  timestamp: string;
  acknowledged: boolean;
  resolvedAt?: string;
}

export interface ResourceAlertManagerProps {
  refreshInterval?: number;
}

export default function ResourceAlertManager({
  refreshInterval = 10000
}: ResourceAlertManagerProps) {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [history, setHistory] = useState<AlertHistory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('rules');
  const [showNewRuleForm, setShowNewRuleForm] = useState(false);

  const loadAlertsData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/alerts');
      if (response.ok) {
        const data = await response.json();
        setRules(data.rules);
        setHistory(data.history);
      } else {
        // Mock data
        const mockRules: AlertRule[] = [
          {
            id: 'rule-1',
            name: 'High CPU Usage',
            resourceType: 'cpu',
            threshold: 80,
            severity: 'critical',
            enabled: true,
            notificationChannels: ['ui', 'email'],
            cooldownMinutes: 15
          },
          {
            id: 'rule-2',
            name: 'Memory Warning',
            resourceType: 'memory',
            threshold: 500,
            severity: 'warning',
            enabled: true,
            extensionId: 'analytics-dashboard',
            extensionName: 'Analytics Dashboard',
            notificationChannels: ['ui'],
            cooldownMinutes: 30
          },
          {
            id: 'rule-3',
            name: 'Network Threshold',
            resourceType: 'network',
            threshold: 100,
            severity: 'warning',
            enabled: false,
            notificationChannels: ['ui', 'webhook'],
            cooldownMinutes: 10
          }
        ];

        const mockHistory: AlertHistory[] = [
          {
            id: 'alert-1',
            ruleId: 'rule-1',
            ruleName: 'High CPU Usage',
            extensionId: 'automation-engine',
            extensionName: 'Automation Engine',
            resourceType: 'cpu',
            value: 85,
            threshold: 80,
            severity: 'critical',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            acknowledged: true,
            resolvedAt: new Date(Date.now() - 1800000).toISOString()
          },
          {
            id: 'alert-2',
            ruleId: 'rule-2',
            ruleName: 'Memory Warning',
            extensionId: 'analytics-dashboard',
            extensionName: 'Analytics Dashboard',
            resourceType: 'memory',
            value: 520,
            threshold: 500,
            severity: 'warning',
            timestamp: new Date(Date.now() - 1200000).toISOString(),
            acknowledged: false
          }
        ];

        setRules(mockRules);
        setHistory(mockHistory);
      }
    } catch (error) {
      console.error('Failed to load alerts data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlertsData();
    const interval = setInterval(loadAlertsData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const toggleRule = (ruleId: string, enabled: boolean) => {
    setRules(prev =>
      prev.map(rule =>
        rule.id === ruleId ? { ...rule, enabled } : rule
      )
    );
  };

  const deleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
  };

  const acknowledgeAlert = (alertId: string) => {
    setHistory(prev =>
      prev.map(alert =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    );
  };

  const resolveAlert = (alertId: string) => {
    setHistory(prev =>
      prev.map(alert =>
        alert.id === alertId
          ? { ...alert, acknowledged: true, resolvedAt: new Date().toISOString() }
          : alert
      )
    );
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'cpu':
        return <Cpu className="h-4 w-4" />;
      case 'memory':
        return <Database className="h-4 w-4" />;
      case 'network':
        return <Wifi className="h-4 w-4" />;
      case 'storage':
        return <HardDrive className="h-4 w-4" />;
      default:
        return <Settings className="h-4 w-4" />;
    }
  };

  const activeAlerts = history.filter(alert => !alert.resolvedAt);
  const resolvedAlerts = history.filter(alert => alert.resolvedAt);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Resource Alert Manager
            </div>
            <Button onClick={loadAlertsData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Configure alerts and manage resource threshold notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Active Rules</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {rules.filter(r => r.enabled).length}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Active Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {activeAlerts.length}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Unacknowledged</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {history.filter(h => !h.acknowledged).length}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Resolved Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-600">
                  {resolvedAlerts.filter(a => {
                    const today = new Date().setHours(0, 0, 0, 0);
                    return a.resolvedAt && new Date(a.resolvedAt).getTime() >= today;
                  }).length}
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="rules">
                <Settings className="h-4 w-4 mr-2" />
                Alert Rules
              </TabsTrigger>
              <TabsTrigger value="active">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Active ({activeAlerts.length})
              </TabsTrigger>
              <TabsTrigger value="history">
                <Clock className="h-4 w-4 mr-2" />
                History
              </TabsTrigger>
            </TabsList>

            {/* Alert Rules Tab */}
            <TabsContent value="rules" className="space-y-4">
              <div className="flex justify-end">
                <Button onClick={() => setShowNewRuleForm(!showNewRuleForm)} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Rule
                </Button>
              </div>

              <ScrollArea className="h-[500px]">
                <div className="space-y-3 pr-4">
                  {rules.map((rule) => (
                    <Card key={rule.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              {getResourceIcon(rule.resourceType)}
                              <h4 className="font-medium">{rule.name}</h4>
                              <Badge variant={rule.severity === 'critical' ? 'destructive' : 'secondary'}>
                                {rule.severity}
                              </Badge>
                              {rule.enabled ? (
                                <Bell className="h-4 w-4 text-green-600" />
                              ) : (
                                <BellOff className="h-4 w-4 text-gray-400" />
                              )}
                            </div>
                            <div className="grid md:grid-cols-3 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Resource:</span>
                                <span className="ml-2 capitalize">{rule.resourceType}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Threshold:</span>
                                <span className="ml-2 font-medium">
                                  {rule.threshold}
                                  {rule.resourceType === 'cpu' ? '%' : 'MB'}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Cooldown:</span>
                                <span className="ml-2">{rule.cooldownMinutes}m</span>
                              </div>
                            </div>
                            {rule.extensionName && (
                              <p className="text-sm text-muted-foreground mt-2">
                                Extension: {rule.extensionName}
                              </p>
                            )}
                            <div className="flex gap-1 mt-2">
                              {rule.notificationChannels.map(channel => (
                                <Badge key={channel} variant="outline" className="text-xs capitalize">
                                  {channel}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={rule.enabled}
                              onCheckedChange={(enabled) => toggleRule(rule.id, enabled)}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => deleteRule(rule.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Active Alerts Tab */}
            <TabsContent value="active" className="space-y-4">
              <ScrollArea className="h-[500px]">
                <div className="space-y-3 pr-4">
                  {activeAlerts.map((alert) => (
                    <Card key={alert.id} className={!alert.acknowledged ? 'border-orange-200 bg-orange-50' : ''}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {getResourceIcon(alert.resourceType)}
                              <h4 className="font-medium">{alert.ruleName}</h4>
                              <Badge variant={alert.severity === 'critical' ? 'destructive' : 'default'}>
                                {alert.severity}
                              </Badge>
                              {alert.acknowledged ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : (
                                <AlertTriangle className="h-4 w-4 text-orange-600" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              {alert.extensionName}: {alert.resourceType.toUpperCase()} at {alert.value}
                              {alert.resourceType === 'cpu' ? '%' : 'MB'} (threshold: {alert.threshold}
                              {alert.resourceType === 'cpu' ? '%' : 'MB'})
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(alert.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {!alert.acknowledged && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => acknowledgeAlert(alert.id)}
                              >
                                Acknowledge
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => resolveAlert(alert.id)}
                            >
                              Resolve
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {activeAlerts.length === 0 && (
                    <div className="text-center py-12">
                      <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                      <h3 className="text-lg font-medium mb-2">No Active Alerts</h3>
                      <p className="text-muted-foreground">All systems operating normally</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history" className="space-y-4">
              <ScrollArea className="h-[500px]">
                <div className="space-y-3 pr-4">
                  {history.map((alert) => (
                    <Card key={alert.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {getResourceIcon(alert.resourceType)}
                              <h4 className="font-medium">{alert.ruleName}</h4>
                              <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                                {alert.severity}
                              </Badge>
                              {alert.resolvedAt ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : (
                                <XCircle className="h-4 w-4 text-orange-600" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-1">
                              {alert.extensionName}: {alert.resourceType.toUpperCase()} at {alert.value}
                              {alert.resourceType === 'cpu' ? '%' : 'MB'}
                            </p>
                            <div className="grid md:grid-cols-2 gap-2 text-xs text-muted-foreground">
                              <div>Triggered: {new Date(alert.timestamp).toLocaleString()}</div>
                              {alert.resolvedAt && (
                                <div>Resolved: {new Date(alert.resolvedAt).toLocaleString()}</div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { ResourceAlertManager };
export type { ResourceAlertManagerProps, AlertRule, AlertHistory };
