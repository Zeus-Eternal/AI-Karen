// ui_launchers/KAREN-Theme-Default/src/components/monitoring/ExtensionMonitoringDashboard.tsx
"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ErrorBoundary,
  type ErrorFallbackProps,
} from "@/components/error-handling/ErrorBoundary";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";

import {
  RefreshCw,
  XCircle,
  AlertTriangle,
  CheckCircle,
  Activity,
  Shield,
  Server,
  TrendingUp,
  Clock,
} from "lucide-react";

export interface AuthMetrics {
  total_requests: number;
  success_count: number;
  failure_count: number;
  success_rate: number; // percent
  token_refresh_count: number;
  average_response_time: number; // seconds
  last_updated: string; // iso
}

export interface ServiceHealthItem {
  status: "healthy" | "degraded" | "down" | string;
  error_count: number;
  average_response_time: number; // seconds
  last_check: string; // iso
}

export interface ServiceHealthMetrics {
  healthy_services: number;
  total_services: number;
  health_percentage: number; // percent
  services: Record<string, ServiceHealthItem>;
  last_updated: string;
}

export interface EndpointPerfItem {
  request_count: number;
  error_count: number;
  error_rate: number; // percent
  average_response_time: number; // seconds
  last_request: string | null;
}

export interface ApiPerformanceMetrics {
  total_requests: number;
  error_count: number;
  error_rate: number; // percent
  average_response_time: number; // seconds
  percentiles: { p50: number; p95: number; p99: number }; // seconds
  endpoints: Record<string, EndpointPerfItem>;
  last_updated: string;
}

export type Severity = "info" | "warning" | "error" | "critical";

export interface ActiveAlert {
  id: string;
  name: string;
  description: string;
  severity: Severity;
  triggered_at: string; // iso
  trigger_count: number;
}

export interface DashboardData {
  timestamp: string;
  monitoring_active: boolean;
  authentication: AuthMetrics;
  service_health: ServiceHealthMetrics;
  api_performance: ApiPerformanceMetrics;
  active_alerts: ActiveAlert[];
  alert_history: unknown[];
}

const fetchDashboard = async (signal?: AbortSignal): Promise<DashboardData> => {
  const res = await fetch("/api/monitoring/dashboard", { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
};

const formatTimestamp = (timestamp: string) => new Date(timestamp).toLocaleString();
const formatMs = (seconds: number) => `${Math.max(0, seconds * 1000).toFixed(0)}ms`;

const getSeverityVariant = (severity: Severity): "default" | "destructive" => {
  switch (severity) {
    case "critical":
    case "error":
      return "destructive";
    default:
      return "default";
  }
};

type AlertComponentProps = React.ComponentPropsWithoutRef<"div"> & {
  variant?: "default" | "destructive";
};
const AlertBox = Alert as React.ComponentType<AlertComponentProps>;

const SeverityIcon: React.FC<{ severity: Severity; className?: string }> = ({ severity, className }) => {
  switch (severity) {
    case "critical":
    case "error":
      return <XCircle className={className ?? "h-4 w-4"} />;
    case "warning":
      return <AlertTriangle className={className ?? "h-4 w-4"} />;
    case "info":
      return <CheckCircle className={className ?? "h-4 w-4"} />;
    default:
      return <Activity className={className ?? "h-4 w-4"} />;
  }
};

const truncate = (s: string, n = 30) => (s.length > n ? `${s.slice(0, n)}…` : s);

const ExtensionMonitoringDashboardInner: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30_000); // 30s

  const fetchDashboardData = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const data = await fetchDashboard(signal);
      if (signal?.aborted) return;
      setDashboardData(data);
      setFetchError(null);
    } catch (err) {
      if (signal?.aborted) return;
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      setFetchError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void fetchDashboardData(controller.signal);
    return () => controller.abort();
  }, [fetchDashboardData]);

  const handleRefresh = useCallback(() => {
    void fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = window.setInterval(() => {
      void fetchDashboardData();
    }, refreshInterval);
    return () => window.clearInterval(id);
  }, [autoRefresh, refreshInterval, fetchDashboardData]);

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading monitoring data…</span>
      </div>
    );
  }

  if (fetchError) {
    return (
      <AlertBox variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Dashboard</AlertTitle>
        <AlertDescription className="flex items-center gap-2">
          {fetchError}
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Retry
          </Button>
        </AlertDescription>
      </AlertBox>
    );
  }

  if (!dashboardData) {
    return (
      <AlertBox>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>No Data Available</AlertTitle>
        <AlertDescription>No monitoring data is currently available.</AlertDescription>
      </AlertBox>
    );
  }

  const { authentication, service_health, api_performance, active_alerts } = dashboardData;

  // Chart data
  const authChartData = [
    { name: "Success", value: authentication.success_count, color: "#10b981" },
    { name: "Failure", value: authentication.failure_count, color: "#ef4444" },
  ];

  const serviceStatusData = Object.entries(service_health.services).map(([name, svc]) => ({
    name,
    status: svc.status,
    response_time: svc.average_response_time,
    error_count: svc.error_count,
  }));

  const endpointPerformanceData = Object.entries(api_performance.endpoints)
    .sort(([, a], [, b]) => b.request_count - a.request_count)
    .slice(0, 10)
    .map(([endpoint, data]) => ({
      endpoint: truncate(endpoint, 40),
      requests: data.request_count,
      errors: data.error_count,
      avg_time: data.average_response_time,
    }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Extension Monitoring Dashboard</h1>
          <p className="text-muted-foreground">
            Authentication, service health, and API performance—continuously harvested.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={dashboardData.monitoring_active ? "default" : "secondary"}>
            {dashboardData.monitoring_active ? "Active" : "Inactive"}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
            aria-label="Refresh monitoring data"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh((v) => !v)}
            aria-pressed={autoRefresh}
            aria-label="Toggle auto-refresh"
          >
            {autoRefresh ? "Auto-Refresh: On" : "Auto-Refresh: Off"}
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {active_alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-yellow-500" />
              Active Alerts ({active_alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {active_alerts.map((alert) => (
                <AlertBox key={alert.id} variant={getSeverityVariant(alert.severity)}>
                  <div className="flex items-center">
                    <SeverityIcon severity={alert.severity} className="h-4 w-4" />
                    <div className="ml-2 flex-1">
                      <AlertTitle>{alert.name}</AlertTitle>
                      <AlertDescription>
                        {alert.description}
                        <div className="text-xs text-muted-foreground mt-1">
                          Triggered: {formatTimestamp(alert.triggered_at)}
                          {alert.trigger_count > 1 ? ` (${alert.trigger_count} times)` : ""}
                        </div>
                      </AlertDescription>
                    </div>
                  </div>
                </AlertBox>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auth Success Rate</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{authentication.success_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">{authentication.total_requests} total requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Service Health</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{service_health.health_percentage.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {service_health.healthy_services}/{service_health.total_services} services healthy
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Error Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{api_performance.error_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">{api_performance.total_requests} total requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatMs(api_performance.average_response_time)}</div>
            <p className="text-xs text-muted-foreground">P95: {formatMs(api_performance.percentiles.p95)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <Tabs defaultValue="authentication" className="space-y-4">
        <TabsList>
          <TabsTrigger value="authentication">Authentication</TabsTrigger>
          <TabsTrigger value="health">Service Health</TabsTrigger>
          <TabsTrigger value="performance">API Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="authentication" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Authentication Success/Failure</CardTitle>
                <CardDescription>Distribution of request outcomes.</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={authChartData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                    >
                      {authChartData.map((entry, i) => (
                        <Cell key={`cell-${i}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Authentication Metrics</CardTitle>
                <CardDescription>Rollups with timing and refreshes.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Total Requests:</span>
                    <span className="font-medium">{authentication.total_requests}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Success Count:</span>
                    <span className="font-medium text-green-600">{authentication.success_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failure Count:</span>
                    <span className="font-medium text-red-600">{authentication.failure_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Token Refreshes:</span>
                    <span className="font-medium">{authentication.token_refresh_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Response Time:</span>
                    <span className="font-medium">{formatMs(authentication.average_response_time)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Last Updated:</span>
                    <span>{formatTimestamp(authentication.last_updated)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Status</CardTitle>
              <CardDescription>Real-time checks across extension services.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {serviceStatusData.map((svc) => (
                  <div key={svc.name} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center gap-3">
                      <span
                        className={`w-3 h-3 rounded-full ${
                          svc.status === "healthy"
                            ? "bg-green-500"
                            : svc.status === "degraded"
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                      />
                      <span className="font-medium">{svc.name}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Errors: {svc.error_count}</span>
                      <span>Avg: {formatMs(svc.response_time)}</span>
                      <Badge
                        variant={
                          svc.status === "healthy" ? "default" : svc.status === "degraded" ? "secondary" : "destructive"
                        }
                      >
                        {svc.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Endpoint Performance</CardTitle>
                <CardDescription>Top 10 endpoints by request volume.</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={endpointPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="endpoint" angle={-30} textAnchor="end" height={80} interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="requests" name="Requests" fill="#3b82f6" />
                    <Bar dataKey="errors" name="Errors" fill="#ef4444" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time Percentiles</CardTitle>
                <CardDescription>Latency distribution and error rate.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>P50 (Median):</span>
                    <span className="font-medium">{formatMs(api_performance.percentiles.p50)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>P95:</span>
                    <span className="font-medium">{formatMs(api_performance.percentiles.p95)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>P99:</span>
                    <span className="font-medium">{formatMs(api_performance.percentiles.p99)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average:</span>
                    <span className="font-medium">{formatMs(api_performance.average_response_time)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Error Rate:</span>
                    <span
                      className={`font-medium ${
                        api_performance.error_rate > 5 ? "text-red-600" : "text-green-600"
                      }`}
                    >
                      {api_performance.error_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Last updated: {formatTimestamp(api_performance.last_updated)}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ExtensionMonitoringFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
  error,
  errorId,
  retryCount,
  errorInfo: _errorInfo,
}) => (
  <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4" role="alert">
    <p className="font-semibold">Something went wrong in ExtensionMonitoringDashboard</p>
    <p className="text-sm text-muted-foreground">
      {error.message}
      {errorId ? ` (ref: ${errorId})` : ""}
    </p>
    <Button variant="outline" size="sm" className="mt-2" onClick={resetError}>
      Retry attempt {retryCount + 1}
    </Button>
  </div>
);

const ExtensionMonitoringDashboard: React.FC = () => {
  return (
    <ErrorBoundary fallback={ExtensionMonitoringFallback}>
      <ExtensionMonitoringDashboardInner />
    </ErrorBoundary>
  );
};

export default ExtensionMonitoringDashboard;
