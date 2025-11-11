// ui_launchers/KAREN-Theme-Default/src/components/performance/PerformanceAlertSystem.tsx
"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertTriangle,
  Bell,
  Settings as SettingsIcon,
  Trash2,
  Clock,
  CheckCircle,
  X,
} from "lucide-react";

// ---- Domain Types ----------------------------------------------------------

export type AlertLevel = "warning" | "critical";

export type PerformanceAlert = MonitorPerformanceAlert;

export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  threshold: number;
  type: AlertLevel;
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

export interface PerformanceAlertSystemProps {
  onAlert?: (alert: PerformanceAlert) => void;
}

// ---- Monitor Service (typed import) ----------------------------------------
// Expected API:
//  - performanceMonitor.getAlerts(limit?: number): PerformanceAlert[]
//  - performanceMonitor.onAlert(cb: (a: PerformanceAlert) => void): () => void
//  - (optional) performanceMonitor.metrics() ...
import {
  performanceMonitor,
  type PerformanceAlert as MonitorPerformanceAlert,
} from "@/services/performance-monitor";

// ---- Helpers ---------------------------------------------------------------

const METRIC_NAME: Record<string, string> = {
  lcp: "Largest Contentful Paint",
  fid: "First Input Delay",
  cls: "Cumulative Layout Shift",
  fcp: "First Contentful Paint",
  ttfb: "Time to First Byte",
  "page-load": "Page Load Time",
  "memory-usage": "Memory Usage",
  "api-call": "API Call Duration",
};

const getMetricDisplayName = (metric: string) => METRIC_NAME[metric] ?? metric;

const formatTimestamp = (ts: number) =>
  new Date(ts).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

// ---- Component -------------------------------------------------------------

export const PerformanceAlertSystem: React.FC<PerformanceAlertSystemProps> = ({
  onAlert,
}) => {
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const rulesRef = useRef<AlertRule[]>([]);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const [newRule, setNewRule] = useState<Partial<AlertRule>>({
    name: "",
    metric: "lcp",
    threshold: 2500,
    type: "warning",
    enabled: true,
    notifications: { email: false, push: true, slack: false },
    escalation: { enabled: false, delay: 15, recipients: [] },
  });

  // Keep a ref synchronized to avoid stale closures inside listeners/timeouts
  useEffect(() => {
    rulesRef.current = alertRules;
  }, [alertRules]);

  // --- Notifications & Escalation ------------------------------------------

  const handleAlertNotification = useCallback(
    async (alert: PerformanceAlert, rule: AlertRule) => {
      // Push notifications
      if (rule.notifications.push && "Notification" in window) {
        try {
          if (Notification.permission === "granted") {
            new Notification(`Performance ${alert.type.toUpperCase()}`, {
              body: `${getMetricDisplayName(alert.metric)}: ${alert.value} — ${alert.message}`,
              icon: "/favicon.ico",
            });
          }
        } catch {
          // Notifications may be blocked; ignore
        }
      }

      // Email & Slack hooks would call your integrations here.
      // e.g., fetch("/api/notify/email", { method: "POST", body: JSON.stringify({...}) })
      // e.g., fetch("/api/notify/slack", { method: "POST", body: JSON.stringify({...}) })

      // Escalation timer
      if (rule.escalation.enabled && rule.escalation.recipients.length > 0) {
        window.setTimeout(() => {
          // Replace with your escalation webhook
          // navigator.sendBeacon("/api/escalate", JSON.stringify({ alert, rule }));
          // For now, log (observable in dev tools)
          // eslint-disable-next-line no-console
          console.log(
            `[ESCALATE] -> ${rule.escalation.recipients.join(", ")} | ${rule.name} | ${getMetricDisplayName(alert.metric)}=${alert.value}`
          );
        }, rule.escalation.delay * 60 * 1000);
      }
    },
    []
  );

  // Load initial rules (from localStorage if present), and seed defaults
  useEffect(() => {
    try {
      const stored = localStorage.getItem("kari_perf_alert_rules");
      if (stored) {
        const parsed: AlertRule[] = JSON.parse(stored);
        setAlertRules(parsed);
        return;
      }
    } catch {
      // ignore parse errors, fall back to defaults
    }
    setAlertRules([
      {
        id: "rule-lcp-critical",
        name: "LCP Critical",
        metric: "lcp",
        threshold: 4000,
        type: "critical",
        enabled: true,
        notifications: { email: true, push: true, slack: false },
        escalation: { enabled: true, delay: 5, recipients: ["admin@example.com"] },
      },
      {
        id: "rule-mem-high",
        name: "Memory Usage High",
        metric: "memory-usage",
        threshold: 85,
        type: "warning",
        enabled: true,
        notifications: { email: false, push: true, slack: true },
        escalation: { enabled: false, delay: 15, recipients: [] },
      },
      {
        id: "rule-fid-critical",
        name: "FID Poor",
        metric: "fid",
        threshold: 300,
        type: "critical",
        enabled: true,
        notifications: { email: true, push: true, slack: true },
        escalation: { enabled: true, delay: 10, recipients: ["dev-team@example.com"] },
      },
    ]);
  }, []);

  // Persist rules
  useEffect(() => {
    try {
      localStorage.setItem("kari_perf_alert_rules", JSON.stringify(alertRules));
    } catch {
      // ignore storage failures (sandbox/SSR)
    }
  }, [alertRules]);

  const handleAlertNotification = useCallback(
    async (alert: PerformanceAlert, rule: AlertRule) => {
      // Push notifications
      if (rule.notifications.push && "Notification" in window) {
        try {
          if (Notification.permission === "granted") {
            new Notification(`Performance ${alert.type.toUpperCase()}`, {
              body: `${getMetricDisplayName(alert.metric)}: ${alert.value} — ${alert.message}`,
              icon: "/favicon.ico",
            });
          }
        } catch {
          // Notifications may be blocked; ignore
        }
      }

      // Email & Slack hooks would call your integrations here.
      // e.g., fetch("/api/notify/email", { method: "POST", body: JSON.stringify({...}) })
      // e.g., fetch("/api/notify/slack", { method: "POST", body: JSON.stringify({...}) })

      // Escalation timer
      if (rule.escalation.enabled && rule.escalation.recipients.length > 0) {
        window.setTimeout(() => {
          // Replace with your escalation webhook
          // navigator.sendBeacon("/api/escalate", JSON.stringify({ alert, rule }));
          // For now, log (observable in dev tools)
          // eslint-disable-next-line no-console
          console.log(
            `[ESCALATE] -> ${rule.escalation.recipients.join(
              ", "
            )} | ${rule.name} | ${getMetricDisplayName(alert.metric)}=${alert.value}`
          );
        }, rule.escalation.delay * 60 * 1000);
    }
  },
  []
  );

  // Load alerts & subscribe
  useEffect(() => {
    const loadData = () => {
      try {
        setAlerts(performanceMonitor.getAlerts(50));
      } catch {
        // If service not yet ready, keep calm.
      }
    };

    loadData();
    const interval = window.setInterval(loadData, 5000);

    const unsubscribe =
      performanceMonitor.onAlert?.((alert: PerformanceAlert) => {
        setAlerts((prev) => [alert, ...prev.slice(0, 49)]);

        // Threshold-aware rule matching
        const match = rulesRef.current.find(
          (rule) =>
            rule.enabled &&
            rule.metric === alert.metric &&
            rule.type === alert.type &&
            alert.value >= rule.threshold
        );

        if (match) {
          void handleAlertNotification(alert, match);
        }
        onAlert?.(alert);
      }) ?? (() => {});

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [handleAlertNotification, onAlert]);

  // Load alerts & subscribe
  useEffect(() => {
    const loadData = () => {
      try {
        setAlerts(performanceMonitor.getAlerts(50));
      } catch {
        // If service not yet ready, keep calm.
      }
    };

    loadData();
    const interval = window.setInterval(loadData, 5000);

    const unsubscribe =
      performanceMonitor.onAlert?.((alert: PerformanceAlert) => {
        setAlerts((prev) => [alert, ...prev.slice(0, 49)]);

        // Threshold-aware rule matching
        const match = rulesRef.current.find(
          (rule) =>
            rule.enabled &&
            rule.metric === alert.metric &&
            rule.type === alert.type &&
            alert.value >= rule.threshold
        );

        if (match) {
          void handleAlertNotification(alert, match);
        }
        onAlert?.(alert);
      }) ?? (() => {});

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [handleAlertNotification, onAlert]);

  const requestNotificationPermission = useCallback(async () => {
    try {
      if ("Notification" in window && Notification.permission === "default") {
        await Notification.requestPermission();
      }
    } catch {
      // ignore
    }
  }, []);

  // --- Rules CRUD -----------------------------------------------------------

  const addAlertRule = useCallback(() => {
    if (!newRule.name || !newRule.metric || newRule.threshold == null) return;

    const rule: AlertRule = {
      id: `rule-${Date.now()}`,
      name: newRule.name,
      metric: newRule.metric,
      threshold: Number(newRule.threshold),
      type: newRule.type ?? "warning",
      enabled: newRule.enabled ?? true,
      notifications:
        newRule.notifications ?? { email: false, push: true, slack: false },
      escalation:
        newRule.escalation ?? { enabled: false, delay: 15, recipients: [] },
    };
    setAlertRules((prev) => [...prev, rule]);

    setNewRule({
      name: "",
      metric: "lcp",
      threshold: 2500,
      type: "warning",
      enabled: true,
      notifications: { email: false, push: true, slack: false },
      escalation: { enabled: false, delay: 15, recipients: [] },
    });
  }, [newRule]);

  const updateAlertRule = useCallback((id: string, updates: Partial<AlertRule>) => {
    setAlertRules((prev) => prev.map((r) => (r.id === id ? { ...r, ...updates } : r)));
  }, []);

  const deleteAlertRule = useCallback((id: string) => {
    setAlertRules((prev) => prev.filter((r) => r.id !== id));
  }, []);

  // --- Alerts actions -------------------------------------------------------

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  }, []);

  const clearAllAlerts = useCallback(() => setAlerts([]), []);

  // --- UI helpers -----------------------------------------------------------

  type BadgeVariant = NonNullable<BadgeProps["variant"]>;
  const alertBadgeVariant: Record<AlertLevel, BadgeVariant> = {
    critical: "destructive",
    warning: "secondary",
  };

  const alertVariant: Record<AlertLevel, "default" | "destructive"> = {
    critical: "destructive",
    warning: "default",
  };

  type AlertComponentProps = React.ComponentPropsWithoutRef<"div"> & {
    variant?: "default" | "destructive";
  };
  const AlertComponent = Alert as React.ComponentType<AlertComponentProps>;

  const getAlertIcon = (type: AlertLevel) =>
    type === "critical" ? (
      <AlertTriangle className="h-4 w-4 text-red-500" />
    ) : (
      <AlertTriangle className="h-4 w-4 text-yellow-500" />
    );

  const lastAlertTime = alerts[0]?.timestamp ?? null;

  const counts = useMemo(
    () => ({
      total: alerts.length,
      critical: alerts.filter((a) => a.type === "critical").length,
      warning: alerts.filter((a) => a.type === "warning").length,
      rules: alertRules.length,
      rulesEnabled: alertRules.filter((r) => r.enabled).length,
    }),
    [alerts, alertRules]
  );

  // --- Render ---------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">Performance Alerts</h3>
          <p className="text-muted-foreground">
            Threshold-based monitoring with notifications and escalation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={requestNotificationPermission} title="Enable notifications">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </Button>

          <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" title="Configure alert rules">
                <SettingsIcon className="h-4 w-4 mr-2" />
                Configure Rules
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>Alert Rules Configuration</DialogTitle>
                <DialogDescription>
                  Create, enable/disable, and manage threshold rules. Notifications integrate with your email/Slack providers.
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="add" className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="add">Add Rule</TabsTrigger>
                  <TabsTrigger value="manage">Manage Rules</TabsTrigger>
                </TabsList>

                {/* Add Rule */}
                <TabsContent value="add" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Add New Alert Rule</CardTitle>
                      <CardDescription>Define a metric threshold and delivery options.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="rule-name">Rule Name</Label>
                          <Input
                            id="rule-name"
                            value={newRule.name ?? ""}
                            onChange={(e) =>
                              setNewRule((p) => ({ ...p, name: e.target.value }))
                            }
                            placeholder="e.g., API Latency Critical"
                          />
                        </div>

                        <div>
                          <Label htmlFor="rule-metric">Metric</Label>
                          <select
                            id="rule-metric"
                            className="w-full p-2 border rounded-md"
                            value={newRule.metric ?? "lcp"}
                            onChange={(e) =>
                              setNewRule((p) => ({ ...p, metric: e.target.value }))
                            }
                          >
                            <option value="lcp">Largest Contentful Paint</option>
                            <option value="fid">First Input Delay</option>
                            <option value="cls">Cumulative Layout Shift</option>
                            <option value="fcp">First Contentful Paint</option>
                            <option value="ttfb">Time to First Byte</option>
                            <option value="page-load">Page Load Time</option>
                            <option value="memory-usage">Memory Usage</option>
                            <option value="api-call">API Call Duration</option>
                          </select>
                        </div>

                        <div>
                          <Label htmlFor="rule-threshold">Threshold</Label>
                          <Input
                            id="rule-threshold"
                            type="number"
                            value={newRule.threshold ?? 0}
                            onChange={(e) =>
                              setNewRule((p) => ({
                                ...p,
                                threshold: Number(e.target.value),
                              }))
                            }
                            placeholder="e.g., 4000"
                          />
                        </div>

                        <div>
                          <Label htmlFor="rule-type">Alert Type</Label>
                          <select
                            id="rule-type"
                            className="w-full p-2 border rounded-md"
                            value={newRule.type ?? "warning"}
                            onChange={(e) =>
                              setNewRule((p) => ({
                                ...p,
                                type: e.target.value as AlertLevel,
                              }))
                            }
                          >
                            <option value="warning">Warning</option>
                            <option value="critical">Critical</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-3">
                          <Switch
                            id="rule-enabled"
                            checked={newRule.enabled ?? true}
                            onCheckedChange={(enabled) =>
                              setNewRule((p) => ({ ...p, enabled }))
                            }
                          />
                          <Label htmlFor="rule-enabled">Enabled</Label>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>Notifications</Label>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={newRule.notifications?.email ?? false}
                              onCheckedChange={(email) =>
                                setNewRule((p) => ({
                                  ...p,
                                  notifications: {
                                    email,
                                    push: p.notifications?.push ?? true,
                                    slack: p.notifications?.slack ?? false,
                                  },
                                }))
                              }
                            />
                            <span>Email</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={newRule.notifications?.push ?? true}
                              onCheckedChange={(push) =>
                                setNewRule((p) => ({
                                  ...p,
                                  notifications: {
                                    email: p.notifications?.email ?? false,
                                    push,
                                    slack: p.notifications?.slack ?? false,
                                  },
                                }))
                              }
                            />
                            <span>Push</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={newRule.notifications?.slack ?? false}
                              onCheckedChange={(slack) =>
                                setNewRule((p) => ({
                                  ...p,
                                  notifications: {
                                    email: p.notifications?.email ?? false,
                                    push: p.notifications?.push ?? true,
                                    slack,
                                  },
                                }))
                              }
                            />
                            <span>Slack</span>
                          </div>
                        </div>

                        <div className="space-y-2 md:col-span-2">
                          <Label>Escalation</Label>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={newRule.escalation?.enabled ?? false}
                              onCheckedChange={(enabled) =>
                                setNewRule((p) => ({
                                  ...p,
                                  escalation: {
                                    enabled,
                                    delay: p.escalation?.delay ?? 15,
                                    recipients: p.escalation?.recipients ?? [],
                                  },
                                }))
                              }
                            />
                            <span>Enable escalation</span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <Label htmlFor="esc-delay">Delay (min)</Label>
                              <Input
                                id="esc-delay"
                                type="number"
                                value={newRule.escalation?.delay ?? 15}
                                onChange={(e) =>
                                  setNewRule((p) => ({
                                    ...p,
                                    escalation: {
                                      enabled: p.escalation?.enabled ?? false,
                                      delay: Number(e.target.value),
                                      recipients: p.escalation?.recipients ?? [],
                                    },
                                  }))
                                }
                              />
                            </div>
                            <div className="md:col-span-2">
                              <Label htmlFor="esc-recipients">Recipients (comma separated)</Label>
                              <Input
                                id="esc-recipients"
                                placeholder="ops@example.com, oncall@example.com"
                                value={(newRule.escalation?.recipients ?? []).join(", ")}
                                onChange={(e) =>
                                  setNewRule((p) => ({
                                    ...p,
                                    escalation: {
                                      enabled: p.escalation?.enabled ?? false,
                                      delay: p.escalation?.delay ?? 15,
                                      recipients: e.target.value
                                        .split(",")
                                        .map((s) => s.trim())
                                        .filter(Boolean),
                                    },
                                  }))
                                }
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      <Button onClick={addAlertRule} className="w-full">
                        Add Rule
                      </Button>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Manage Rules */}
                <TabsContent value="manage" className="space-y-4">
                  <h4 className="font-medium">Existing Rules</h4>
                  <ScrollArea className="h-64">
                    {alertRules.length === 0 ? (
                      <p className="text-sm text-muted-foreground px-2">No rules defined yet.</p>
                    ) : (
                      alertRules.map((rule) => (
                        <Card key={rule.id} className="mb-2">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h5 className="font-medium">{rule.name}</h5>
                                  <Badge
                                    variant={rule.type === "critical" ? "destructive" : "secondary"}
                                  >
                                    {rule.type}
                                  </Badge>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  {getMetricDisplayName(rule.metric)} ≥ {rule.threshold}
                                </p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Switch
                                  checked={rule.enabled}
                                  onCheckedChange={(enabled) =>
                                    updateAlertRule(rule.id, { enabled })
                                  }
                                />
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => deleteAlertRule(rule.id)}
                                  title="Delete rule"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.total}</div>
            <p className="text-xs text-muted-foreground">
              {counts.critical} critical, {counts.warning} warnings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alert Rules</CardTitle>
            <SettingsIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.rules}</div>
            <p className="text-xs text-muted-foreground">{counts.rulesEnabled} enabled</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Alert</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {lastAlertTime ? formatTimestamp(lastAlertTime).split(", ")[1] : "None"}
            </div>
            <p className="text-xs text-muted-foreground">
              {lastAlertTime ? formatTimestamp(lastAlertTime).split(", ")[0] : "No recent alerts"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>Newest first, capped at 50.</CardDescription>
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
            <div className="text-center py-12">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium">No Active Alerts</h3>
              <p className="text-muted-foreground">Your application is performing well!</p>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <AlertComponent key={alert.id} variant={alertVariant[alert.type]}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        {getAlertIcon(alert.type)}
                        <div>
                          <AlertTitle className="flex items-center gap-2">
                            <span>{getMetricDisplayName(alert.metric)}</span>
                            <Badge variant={alertBadgeVariant[alert.type]}>
                              {alert.type}
                            </Badge>
                            <Badge variant="outline" className="ml-1">
                              {alert.value}
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
                        size="icon"
                        onClick={() => dismissAlert(alert.id)}
                        title="Dismiss"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertComponent>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
