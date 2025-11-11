"use client";

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { VerticalSeparator } from "./utils/vertical-separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  AlertCircle,
  AlertTriangle,
  Bell,
  BellOff,
  CheckCircle,
  Eye,
  EyeOff,
  Info,
  Play,
  RefreshCw,
  Shield,
  XCircle,
  Zap,
} from "lucide-react";

import type { PluginInfo } from "@/types/plugins";

/**
 * Plugin Health Monitor Component
 *
 * Monitors plugin health with automatic error detection and recovery.
 * Based on requirements: 5.4, 10.3
 */

export type HealthStatus = "passing" | "warning" | "failing" | "unknown";
export type EventType =
  | "check_passed"
  | "check_failed"
  | "recovery_attempted"
  | "recovery_succeeded"
  | "recovery_failed"
  | "alert_triggered";
export type Severity = "info" | "warning" | "error" | "critical";

export interface HealthCheck {
  id: string;
  name: string;
  description: string;
  status: HealthStatus;
  lastCheck: Date;
  nextCheck: Date;
  interval: number; // seconds
  enabled: boolean;
  critical: boolean;
  details?: {
    message: string;
    data?: Record<string, unknown>;
    suggestions?: string[];
  };
}

export interface HealthEvent {
  id: string;
  timestamp: Date;
  type: EventType;
  checkId: string;
  message: string;
  severity: Severity;
  metadata?: Record<string, unknown>;
}

export type RecoveryType = "restart" | "reset_config" | "clear_cache" | "reconnect" | "custom";

export interface RecoveryAction {
  id: string;
  name: string;
  description: string;
  type: RecoveryType;
  enabled: boolean;
  automatic: boolean;
  conditions: string[];
  lastExecuted?: Date;
  successRate: number; // 0-100
}

export interface PluginHealthMonitorProps {
  plugin: PluginInfo;
  onRestart?: () => Promise<void>;
  onReconfigure?: () => Promise<void>;
  onDisable?: () => Promise<void>;
}

export const PluginHealthMonitor: React.FC<PluginHealthMonitorProps> = ({
  plugin,
  onRestart,
  onReconfigure,
  onDisable,
}) => {
  const [monitoring, setMonitoring] = useState(true);
  const [autoRecovery, setAutoRecovery] = useState(true);
  const [notifications, setNotifications] = useState(true);
  const [showDetails, setShowDetails] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState<"1h" | "24h" | "7d">("24h");

  // Mock health checks data
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([
    {
      id: "connectivity",
      name: "API Connectivity",
      description: "Check if plugin can connect to external APIs",
      status: "passing",
      lastCheck: new Date(Date.now() - 2 * 60 * 1000),
      nextCheck: new Date(Date.now() + 3 * 60 * 1000),
      interval: 300,
      enabled: true,
      critical: true,
      details: {
        message: "All API endpoints responding normally",
        data: { responseTime: 245, statusCode: 200 },
      },
    },
    {
      id: "dependencies",
      name: "Dependencies",
      description: "Verify all required dependencies are available",
      status: "passing",
      lastCheck: new Date(Date.now() - 5 * 60 * 1000),
      nextCheck: new Date(Date.now() + 10 * 60 * 1000),
      interval: 900,
      enabled: true,
      critical: true,
      details: {
        message: "All dependencies satisfied",
        data: { missingCount: 0, totalCount: 3 },
      },
    },
    {
      id: "configuration",
      name: "Configuration",
      description: "Validate plugin configuration settings",
      status: "warning",
      lastCheck: new Date(Date.now() - 1 * 60 * 1000),
      nextCheck: new Date(Date.now() + 14 * 60 * 1000),
      interval: 900,
      enabled: true,
      critical: false,
      details: {
        message: "API key will expire in 7 days",
        data: { expiryDate: "2024-02-15", daysRemaining: 7 },
        suggestions: ["Renew API key before expiration", "Set up automatic key rotation"],
      },
    },
    {
      id: "performance",
      name: "Performance",
      description: "Monitor execution time and resource usage",
      status: "passing",
      lastCheck: new Date(Date.now() - 30 * 1000),
      nextCheck: new Date(Date.now() + 30 * 1000),
      interval: 60,
      enabled: true,
      critical: false,
      details: {
        message: "Performance within acceptable limits",
        data: { avgExecutionTime: 245, memoryUsage: 15.2, cpuUsage: 0.5 },
      },
    },
    {
      id: "permissions",
      name: "Permissions",
      description: "Verify plugin has required permissions",
      status: "passing",
      lastCheck: new Date(Date.now() - 10 * 60 * 1000),
      nextCheck: new Date(Date.now() + 50 * 60 * 1000),
      interval: 3600,
      enabled: true,
      critical: true,
      details: {
        message: "All required permissions granted",
        data: { grantedCount: 3, requiredCount: 3 },
      },
    },
  ]);

  // Mock health events
  const [healthEvents, setHealthEvents] = useState<HealthEvent[]>([
    {
      id: "event-1",
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      type: "check_failed",
      checkId: "configuration",
      message: "Configuration check detected API key expiring soon",
      severity: "warning",
      metadata: { expiryDate: "2024-02-15" },
    },
    {
      id: "event-2",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      type: "check_passed",
      checkId: "connectivity",
      message: "API connectivity check passed",
      severity: "info",
      metadata: { responseTime: 245 },
    },
    {
      id: "event-3",
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      type: "recovery_attempted",
      checkId: "connectivity",
      message: "Attempted to reconnect to API after timeout",
      severity: "warning",
      metadata: { action: "reconnect", attempt: 1 },
    },
    {
      id: "event-4",
      timestamp: new Date(Date.now() - 46 * 60 * 1000),
      type: "recovery_succeeded",
      checkId: "connectivity",
      message: "Successfully reconnected to API",
      severity: "info",
      metadata: { action: "reconnect", duration: 2.3 },
    },
  ]);

  // Mock recovery actions
  const [recoveryActions, setRecoveryActions] = useState<RecoveryAction[]>([
    {
      id: "restart",
      name: "Restart Plugin",
      description: "Restart the plugin to recover from errors",
      type: "restart",
      enabled: true,
      automatic: true,
      conditions: ["connectivity.failing", "performance.critical"],
      lastExecuted: new Date(Date.now() - 2 * 60 * 60 * 1000),
      successRate: 85,
    },
    {
      id: "reconnect",
      name: "Reconnect APIs",
      description: "Attempt to reconnect to external APIs",
      type: "reconnect",
      enabled: true,
      automatic: true,
      conditions: ["connectivity.failing"],
      lastExecuted: new Date(Date.now() - 46 * 60 * 1000),
      successRate: 92,
    },
    {
      id: "clear_cache",
      name: "Clear Cache",
      description: "Clear plugin cache to resolve data issues",
      type: "clear_cache",
      enabled: true,
      automatic: false,
      conditions: ["performance.degraded"],
      successRate: 78,
    },
    {
      id: "reset_config",
      name: "Reset Configuration",
      description: "Reset plugin configuration to defaults",
      type: "reset_config",
      enabled: false,
      automatic: false,
      conditions: ["configuration.invalid"],
      successRate: 95,
    },
  ]);

  const [isRunningRecovery, setIsRunningRecovery] = useState(false);

  // Calculate overall health status
  const overallHealth: "healthy" | "warning" | "critical" = useMemo(() => {
    const criticalChecks = healthChecks.filter((c) => c.critical && c.enabled);
    const failingCritical = criticalChecks.some((c) => c.status === "failing");
    if (failingCritical) return "critical";

    const warningCritical = criticalChecks.some((c) => c.status === "warning");
    if (warningCritical) return "warning";

    const enabledChecks = healthChecks.filter((c) => c.enabled);
    if (enabledChecks.some((c) => c.status === "failing")) return "warning";
    if (enabledChecks.some((c) => c.status === "warning")) return "warning";
    return "healthy";
  }, [healthChecks]);

  const handleRunRecoveryAction = async (actionId: string) => {
    setIsRunningRecovery(true);
    try {
      const action = recoveryActions.find((a) => a.id === actionId);
      if (!action) return;

      // Simulate recovery action
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Add attempted event
      const attempted: HealthEvent = {
        id: `event-${Date.now()}`,
        timestamp: new Date(),
        type: "recovery_attempted",
        checkId: "manual",
        message: `Manually executed recovery action: ${action.name}`,
        severity: "info",
        metadata: { action: actionId, manual: true },
      };
      setHealthEvents((prev) => [attempted, ...prev]);

      // Update last executed
      setRecoveryActions((prev) =>
        prev.map((a) => (a.id === actionId ? { ...a, lastExecuted: new Date() } : a)),
      );

      // Simulate outcome
      const success = Math.random() > 0.2;
      const result: HealthEvent = {
        id: `event-${Date.now() + 1}`,
        timestamp: new Date(),
        type: success ? "recovery_succeeded" : "recovery_failed",
        checkId: "manual",
        message: success
          ? `Recovery action ${action.name} completed successfully`
          : `Recovery action ${action.name} failed`,
        severity: success ? "info" : "error",
        metadata: { action: actionId, manual: true, success },
      };
      setHealthEvents((prev) => [result, ...prev]);
    } finally {
      setIsRunningRecovery(false);
    }
  };

  const handleToggleCheck = (checkId: string) => {
    setHealthChecks((prev) =>
      prev.map((c) => (c.id === checkId ? { ...c, enabled: !c.enabled } : c)),
    );
  };

  const handleToggleRecoveryAction = (actionId: string) => {
    setRecoveryActions((prev) =>
      prev.map((a) => (a.id === actionId ? { ...a, enabled: !a.enabled } : a)),
    );
  };

  const getStatusIcon = (status: HealthStatus) => {
    switch (status) {
      case "passing":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case "failing":
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getEventIcon = (type: EventType) => {
    switch (type) {
      case "check_passed":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "check_failed":
        return <XCircle className="w-4 h-4 text-red-600" />;
      case "recovery_attempted":
        return <RefreshCw className="w-4 h-4 text-blue-600" />;
      case "recovery_succeeded":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "recovery_failed":
        return <XCircle className="w-4 h-4 text-red-600" />;
      case "alert_triggered":
        return <Bell className="w-4 h-4 text-orange-600" />;
      default:
        return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Health Monitor</h2>
          <p className="text-muted-foreground">Monitor and manage {plugin.name} health status</p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Switch id="monitoring" checked={monitoring} onCheckedChange={setMonitoring} />
            <Label htmlFor="monitoring" className="text-sm md:text-base lg:text-lg">
              {monitoring ? "Monitoring On" : "Monitoring Off"}
            </Label>
          </div>

            <VerticalSeparator className="h-6" />

          <Button variant="outline" size="sm" onClick={() => setNotifications(!notifications)}>
            {notifications ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
          </Button>

          <Button variant="outline" size="sm" onClick={() => setShowDetails(!showDetails)}>
            {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Overall Health Status */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  overallHealth === "healthy"
                    ? "bg-green-100 text-green-600"
                    : overallHealth === "warning"
                    ? "bg-yellow-100 text-yellow-600"
                    : "bg-red-100 text-red-600"
                }`}
              >
                {overallHealth === "healthy" ? (
                  <CheckCircle className="w-6 h-6" />
                ) : overallHealth === "warning" ? (
                  <AlertTriangle className="w-6 h-6" />
                ) : (
                  <XCircle className="w-6 h-6" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-semibold capitalize">{overallHealth}</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  {healthChecks.filter((c) => c.enabled && c.status === "passing").length} of{" "}
                  {healthChecks.filter((c) => c.enabled).length} checks passing
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge variant={overallHealth === "healthy" ? "default" : "destructive"}>
                {monitoring ? "Monitoring Active" : "Monitoring Paused"}
              </Badge>

              {autoRecovery && (
                <Badge variant="outline">
                  <Shield className="w-3 h-3 mr-1" />
                  Auto Recovery
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="checks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="checks">Health Checks</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="recovery">Recovery</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Checks */}
        <TabsContent value="checks" className="space-y-4">
          <div className="grid gap-4">
            {healthChecks.map((check) => (
              <Card key={check.id}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {getStatusIcon(check.status)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{check.name}</h4>
                          {check.critical && (
                            <Badge variant="destructive" className="text-xs sm:text-sm md:text-base">
                              Critical
                            </Badge>
                          )}
                          {!check.enabled && (
                            <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                              Disabled
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                          {check.description}
                        </p>

                        {showDetails && check.details && (
                          <div className="mt-2 p-2 bg-muted/50 rounded text-sm md:text-base lg:text-lg">
                            <p>{check.details.message}</p>
                            {check.details.suggestions?.length ? (
                              <div className="mt-2">
                                <p className="font-medium text-xs sm:text-sm md:text-base">Suggestions:</p>
                                <ul className="list-disc list-inside text-xs mt-1 space-y-1 sm:text-sm md:text-base">
                                  {check.details.suggestions.map((s, i) => (
                                    <li key={i}>{s}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : null}
                          </div>
                        )}

                        <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-muted-foreground sm:text-sm md:text-base">
                          <span>Last check: {check.lastCheck.toLocaleString()}</span>
                          <span>Next check: {check.nextCheck.toLocaleString()}</span>
                          <span>Interval: {check.interval}s</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Switch
                        checked={check.enabled}
                        onCheckedChange={() => handleToggleCheck(check.id)}
                        className="scale-75"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Events */}
        <TabsContent value="events" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Health Events</h3>

            <Select value={selectedTimeRange} onValueChange={(v: "1h" | "24h" | "7d") => setSelectedTimeRange(v)}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardContent className="p-0 sm:p-4 md:p-6">
              <ScrollArea className="h-96">
                <div className="p-4 space-y-3 sm:p-4 md:p-6">
                  {healthEvents.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-start gap-3 p-3 border rounded-lg sm:p-4 md:p-6"
                    >
                      {getEventIcon(event.type)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium md:text-base lg:text-lg">{event.message}</p>
                          <Badge
                            variant={
                              event.severity === "critical"
                                ? "destructive"
                                : event.severity === "error"
                                ? "destructive"
                                : event.severity === "warning"
                                ? "default"
                                : "secondary"
                            }
                            className="text-xs sm:text-sm md:text-base"
                          >
                            {event.severity}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap items-center gap-4 mt-1 text-xs text-muted-foreground sm:text-sm md:text-base">
                          <span>{event.timestamp.toLocaleString()}</span>
                          <span className="capitalize">{event.type.replace("_", " ")}</span>
                          {event.metadata && Object.keys(event.metadata).length > 0 && (
                            <span>
                              {Object.entries(event.metadata)
                                .map(([k, v]) => `${k}: ${String(v)}`)
                                .join(", ")}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recovery */}
        <TabsContent value="recovery" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Recovery Actions</h3>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Configure automated/manual actions when checks fail.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Switch id="auto-recovery" checked={autoRecovery} onCheckedChange={setAutoRecovery} />
              <Label htmlFor="auto-recovery" className="text-sm md:text-base lg:text-lg">
                Auto Recovery
              </Label>
            </div>
          </div>

          <div className="grid gap-4">
            {recoveryActions.map((action) => (
              <Card key={action.id}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{action.name}</h4>
                        {action.automatic && (
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            <Zap className="w-3 h-3 mr-1" />
                            Automatic
                          </Badge>
                        )}
                        <Badge
                          variant={action.successRate > 80 ? "default" : "secondary"}
                          className="text-xs sm:text-sm md:text-base"
                        >
                          {action.successRate}% success
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                        {action.description}
                      </p>

                      <div className="mt-2">
                        <p className="text-xs font-medium sm:text-sm md:text-base">Triggers:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {action.conditions.map((condition, index) => (
                            <Badge key={index} variant="outline" className="text-xs sm:text-sm md:text-base">
                              {condition}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      {action.lastExecuted && (
                        <p className="text-xs text-muted-foreground mt-2 sm:text-sm md:text-base">
                          Last executed: {action.lastExecuted.toLocaleString()}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <Switch
                        checked={action.enabled}
                        onCheckedChange={() => handleToggleRecoveryAction(action.id)}
                        className="scale-75"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRunRecoveryAction(action.id)}
                        disabled={!action.enabled || isRunningRecovery}
                        aria-label={`Run ${action.name}`}
                      >
                        {isRunningRecovery ? (
                          <RefreshCw className="w-3 h-3 animate-spin" />
                        ) : (
                          <Play className="w-3 h-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Monitoring Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="enable-monitoring">Enable Health Monitoring</Label>
                </div>
                <Switch
                  id="enable-monitoring"
                  checked={monitoring}
                  onCheckedChange={setMonitoring}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="enable-notifications">Enable Notifications</Label>
                </div>
                <Switch
                  id="enable-notifications"
                  checked={notifications}
                  onCheckedChange={setNotifications}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="enable-auto-recovery">Enable Auto Recovery</Label>
                </div>
                <Switch
                  id="enable-auto-recovery"
                  checked={autoRecovery}
                  onCheckedChange={setAutoRecovery}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Alert Thresholds</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm md:text-base lg:text-lg">Response Time Threshold</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={75} className="flex-1" />
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">1000ms</span>
                  </div>
                </div>

                <div>
                  <Label className="text-sm md:text-base lg:text-lg">Error Rate Threshold</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={50} className="flex-1" />
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">5%</span>
                  </div>
                </div>

                <div>
                  <Label className="text-sm md:text-base lg:text-lg">Memory Usage Threshold</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={80} className="flex-1" />
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">100MB</span>
                  </div>
                </div>

                <div>
                  <Label className="text-sm md:text-base lg:text-lg">CPU Usage Threshold</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={60} className="flex-1" />
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">10%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
