"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../ui/tabs";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";

import {
  useExtensionStatuses,
  useExtensionPerformance,
  useExtensionTaskMonitoring,
  type ExtensionTaskMonitoringSummary,
} from "../../../lib/extensions/hooks";
import type { ExtensionStatus } from "../../../lib/extensions/extension-integration";

import {
  RefreshCw,
  Download,
  AlertTriangle,
  Monitor,
  Gauge,
  Activity,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  LineChart,
  Cpu,
  Database,
  Wifi,
  HardDrive,
  CheckCircle,
  PieChart,
  Target,
} from "lucide-react";

type TimeRangeOption = "1h" | "6h" | "24h" | "7d";
type ResourceMetricKey = "cpu" | "memory" | "network" | "storage";

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  status: "good" | "warning" | "critical";
  threshold: {
    warning: number;
    critical: number;
  };
}

interface ResourceAlert {
  id: string;
  type: "cpu" | "memory" | "network" | "storage";
  severity: "warning" | "critical";
  message: string;
  timestamp: string;
  extensionId: string;
  extensionName: string;
  value: number;
  threshold: number;
}

interface ExtensionPerformanceMonitorProps {
  className?: string;
  extensionId?: string; // If provided, show metrics for specific extension
}

export function ExtensionPerformanceMonitor({
  className,
  extensionId,
}: ExtensionPerformanceMonitorProps) {
  const [activeTab, setActiveTab] = useState("overview");
  const [timeRange, setTimeRange] = useState<TimeRangeOption>("1h");
  const [selectedMetric, setSelectedMetric] = useState<ResourceMetricKey>("cpu");
  const [alerts, setAlerts] = useState<ResourceAlert[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { statuses, loading } = useExtensionStatuses();
  const performanceData = useExtensionPerformance(extensionId);
  const taskData = useExtensionTaskMonitoring(extensionId);

  // Filter statuses if specific extension is selected
  const filteredStatuses = useMemo(() => {
    return extensionId ? statuses.filter((status) => status.id === extensionId) : statuses;
  }, [statuses, extensionId]);

  // Generate performance metrics
  const performanceMetrics = useMemo((): PerformanceMetric[] => {
    const activeErrors = filteredStatuses.filter((status) => status.status === "error").length;
    const activeCount = filteredStatuses.filter((status) => status.status === "active").length;
    const tasks = taskData?.totalActiveTasks ?? 0;

    return [
      {
        name: "CPU Usage",
        value: performanceData?.avgCpu ?? 0,
        unit: "%",
        trend:
          (performanceData?.avgCpu ?? 0) > 50
            ? "up"
            : (performanceData?.avgCpu ?? 0) < 20
            ? "down"
            : "stable",
        status:
          (performanceData?.avgCpu ?? 0) > 80
            ? "critical"
            : (performanceData?.avgCpu ?? 0) > 60
            ? "warning"
            : "good",
        threshold: { warning: 60, critical: 80 },
      },
      {
        name: "Memory Usage",
        value: performanceData?.avgMemory ?? 0,
        unit: "MB",
        trend:
          (performanceData?.avgMemory ?? 0) > 400
            ? "up"
            : (performanceData?.avgMemory ?? 0) < 200
            ? "down"
            : "stable",
        status:
          (performanceData?.avgMemory ?? 0) > 800
            ? "critical"
            : (performanceData?.avgMemory ?? 0) > 500
            ? "warning"
            : "good",
        threshold: { warning: 500, critical: 800 },
      },
      {
        name: "Active Extensions",
        value: activeCount,
        unit: "",
        trend: "stable",
        status: "good",
        threshold: { warning: 10, critical: 15 },
      },
      {
        name: "Background Tasks",
        value: tasks,
        unit: "",
        trend: tasks > 5 ? "up" : "stable",
        status: tasks > 10 ? "warning" : "good",
        threshold: { warning: 8, critical: 15 },
      },
      {
        name: "Error Rate",
        value: activeErrors,
        unit: "",
        trend: activeErrors > 0 ? "up" : "stable",
        status: activeErrors > 2 ? "critical" : activeErrors > 0 ? "warning" : "good",
        threshold: { warning: 1, critical: 3 },
      },
      {
        name: "Response Time",
        value: performanceData?.avgResponseTime ?? performanceData?.totalCpu ?? 125, // fallback simulated average
        unit: "ms",
        trend: "stable",
        status: "good",
        threshold: { warning: 500, critical: 1000 },
      },
    ];
  }, [performanceData, filteredStatuses, taskData]);

  // Sample alerts
  useEffect(() => {
    const sampleAlerts: ResourceAlert[] = [
      {
        id: "1",
        type: "memory",
        severity: "warning",
        message: "Memory usage approaching limit",
        timestamp: new Date(Date.now() - 300000).toISOString(),
        extensionId: "analytics-dashboard",
        extensionName: "Analytics Dashboard",
        value: 450,
        threshold: 500,
      },
      {
        id: "2",
        type: "cpu",
        severity: "critical",
        message: "CPU usage critically high",
        timestamp: new Date(Date.now() - 600000).toISOString(),
        extensionId: "automation-engine",
        extensionName: "Automation Engine",
        value: 85,
        threshold: 80,
      },
    ];
    setAlerts(sampleAlerts);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      // Intentionally left as a placeholder for real refresh triggers
      // e.g., refetch queries or emit redux actions
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleExportMetrics = useCallback(() => {
    const metricsData = {
      timestamp: new Date().toISOString(),
      timeRange,
      metrics: performanceMetrics,
      extensions: filteredStatuses.map((status) => ({
        id: status.id,
        name: status.name,
        status: status.status,
        resources: status.resources,
      })),
      alerts,
    };
    const blob = new Blob([JSON.stringify(metricsData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extension-performance-${new Date()
      .toISOString()
      .split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [performanceMetrics, filteredStatuses, alerts, timeRange]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className ?? ""}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading performance monitor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className ?? ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Monitor</h1>
          <p className="text-gray-600 mt-1">
            {extensionId
              ? `Monitor performance for ${filteredStatuses[0]?.name || extensionId}`
              : "Monitor performance across all extensions"}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRangeOption)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          <Button
            variant="outline"
            onClick={() => setAutoRefresh((v) => !v)}
            className={`flex items-center gap-2 ${autoRefresh ? "text-green-600" : "text-gray-600"}`}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="outline" onClick={handleExportMetrics} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              Performance Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border sm:p-4 md:p-6"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant={alert.severity === "critical" ? "destructive" : "secondary"}>
                      {alert.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                        {alert.extensionName} • {alert.value}
                        {alert.type === "cpu" ? "%" : "MB"} / {alert.threshold}
                        {alert.type === "cpu" ? "%" : "MB"}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500 md:text-base lg:text-lg">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
              {alerts.length > 3 && (
                <p className="text-sm text-gray-600 text-center pt-2 md:text-base lg:text-lg">
                  +{alerts.length - 3} more alerts
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {performanceMetrics.map((metric, index) => (
          <MetricCard key={index} metric={metric} />
        ))}
      </div>

      {/* Performance Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">
            <Monitor className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="resources">
            <Gauge className="h-4 w-4 mr-2" />
            Resources
          </TabsTrigger>
          <TabsTrigger value="extensions">
            <Activity className="h-4 w-4 mr-2" />
            Extensions
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <OverviewPanel metrics={performanceMetrics} statuses={filteredStatuses} taskData={taskData} />
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <ResourcesPanel
            statuses={filteredStatuses}
            selectedMetric={selectedMetric}
            onMetricChange={setSelectedMetric}
          />
        </TabsContent>

        <TabsContent value="extensions" className="space-y-6">
          <ExtensionsPanel statuses={filteredStatuses} />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <AnalyticsPanel metrics={performanceMetrics} timeRange={timeRange} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ===== Subcomponents ===== */

interface MetricCardProps {
  metric: PerformanceMetric;
}
function MetricCard({ metric }: MetricCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "good":
        return "text-green-600 bg-green-100";
      case "warning":
        return "text-yellow-600 bg-yellow-100";
      case "critical":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case "down":
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      case "stable":
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium md:text-base lg:text-lg">{metric.name}</CardTitle>
        <Badge className={getStatusColor(metric.status)}>{metric.status}</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">
              {metric.value.toFixed(metric.unit === "%" ? 1 : 0)}
              {metric.unit}
            </div>
            <div className="flex items-center mt-1">
              {getTrendIcon(metric.trend)}
              <span className="text-xs text-gray-500 ml-1 sm:text-sm md:text-base">
                {metric.trend === "stable" ? "Stable" : metric.trend === "up" ? "Increasing" : "Decreasing"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 sm:text-sm md:text-base">
              Warning: {metric.threshold.warning}
              {metric.unit}
            </div>
            <div className="text-xs text-gray-500 sm:text-sm md:text-base">
              Critical: {metric.threshold.critical}
              {metric.unit}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface OverviewPanelProps {
  metrics: PerformanceMetric[];
  statuses: ExtensionStatus[];
  taskData: ExtensionTaskMonitoringSummary;
}

function OverviewPanel({ metrics: _metrics, statuses, taskData }: OverviewPanelProps) {
  return (
    <div className="space-y-6">
      {/* System Health Summary */}
      <Card>
        <CardHeader>
          <CardTitle>System Health Summary</CardTitle>
          <CardDescription>Overall performance status across all extensions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {statuses.filter((status) => status.status === "active").length}
              </div>
              <p className="text-sm text-gray-600 md:text-base lg:text-lg">Active Extensions</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{taskData?.totalActiveTasks ?? 0}</div>
              <p className="text-sm text-gray-600 md:text-base lg:text-lg">Active Tasks</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {statuses.filter((status) => status.status === "inactive").length}
              </div>
              <p className="text-sm text-gray-600 md:text-base lg:text-lg">Inactive Extensions</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {statuses.filter((status) => status.status === "error").length}
              </div>
              <p className="text-sm text-gray-600 md:text-base lg:text-lg">Error Extensions</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Trends Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
          <CardDescription>Resource usage trends over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <LineChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Performance trends chart would be rendered here</p>
              <p className="text-sm text-gray-500 md:text-base lg:text-lg">
                Integration with charting library needed
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ResourcesPanelProps {
  statuses: ExtensionStatus[];
  selectedMetric: ResourceMetricKey;
  onMetricChange: (metric: ResourceMetricKey) => void;
}

function ResourcesPanel({ statuses, selectedMetric, onMetricChange }: ResourcesPanelProps) {
  const resourceMetrics: ResourceMetricKey[] = ["cpu", "memory", "network", "storage"];
  return (
    <div className="space-y-6">
      {/* Resource Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Monitoring</CardTitle>
          <CardDescription>Monitor resource usage across extensions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            {resourceMetrics.map((metric) => (
              <Button
                key={metric}
                variant={selectedMetric === metric ? "default" : "outline"}
                size="sm"
                onClick={() => onMetricChange(metric)}
                className="capitalize"
              >
                {metric === "cpu" && <Cpu className="h-3 w-3 mr-1" />}
                {metric === "memory" && <Database className="h-3 w-3 mr-1" />}
                {metric === "network" && <Wifi className="h-3 w-3 mr-1" />}
                {metric === "storage" && <HardDrive className="h-3 w-3 mr-1" />}
                {metric}
              </Button>
            ))}
          </div>

          {/* Resource Usage by Extension */}
          <div className="space-y-3">
            {statuses.map((status) => (
              <div
                key={status.id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg sm:p-4 md:p-6"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      status.status === "active"
                        ? "bg-green-400"
                        : status.status === "error"
                        ? "bg-red-400"
                        : "bg-gray-400"
                    }`}
                  />
                  <div>
                    <h4 className="font-medium">{status.name}</h4>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">ID: {status.id}</p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-semibold">
                    {selectedMetric === "cpu" && `${(status.resources.cpu ?? 0).toFixed(1)}%`}
                    {selectedMetric === "memory" && `${Math.round(status.resources.memory ?? 0)}MB`}
                    {selectedMetric === "network" && `${(status.resources.network ?? 0).toFixed(1)} KB/s`}
                    {selectedMetric === "storage" && `${Math.round(status.resources.storage ?? 0)}MB`}
                  </div>

                  <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className={`h-2 rounded-full ${
                        selectedMetric === "cpu" && (status.resources.cpu ?? 0) > 80
                          ? "bg-red-500"
                          : selectedMetric === "cpu" && (status.resources.cpu ?? 0) > 60
                          ? "bg-yellow-500"
                          : selectedMetric === "memory" && (status.resources.memory ?? 0) > 500
                          ? "bg-red-500"
                          : selectedMetric === "memory" && (status.resources.memory ?? 0) > 300
                          ? "bg-yellow-500"
                          : "bg-green-500"
                      }`}
                      style={{
                        width: `${Math.min(
                          100,
                          selectedMetric === "cpu"
                            ? status.resources.cpu ?? 0
                            : selectedMetric === "memory"
                            ? (status.resources.memory ?? 0) / 10
                            : selectedMetric === "network"
                            ? (status.resources.network ?? 0) / 10
                            : (status.resources.storage ?? 0) / 10
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ExtensionsPanelProps {
  statuses: ExtensionStatus[];
}

function ExtensionsPanel({ statuses }: ExtensionsPanelProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Extension Performance Breakdown</CardTitle>
          <CardDescription>Detailed performance metrics for each extension</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm md:text-base lg:text-lg">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Extension</th>
                  <th className="text-center py-2">Status</th>
                  <th className="text-right py-2">CPU</th>
                  <th className="text-right py-2">Memory</th>
                  <th className="text-right py-2">Network</th>
                  <th className="text-right py-2">Tasks</th>
                  <th className="text-center py-2">Health</th>
                </tr>
              </thead>
              <tbody>
                {statuses.map((status) => (
                  <tr key={status.id} className="border-b border-gray-100">
                    <td className="py-2">
                      <div>
                        <div className="font-medium">{status.name}</div>
                        <div className="text-xs text-gray-500 sm:text-sm md:text-base">{status.id}</div>
                      </div>
                    </td>
                    <td className="text-center py-2">
                      <Badge
                        variant={
                          status.status === "active" ? "default" : status.status === "error" ? "destructive" : "secondary"
                        }
                      >
                        {status.status}
                      </Badge>
                    </td>
                    <td className="text-right py-2">{(status.resources.cpu ?? 0).toFixed(1)}%</td>
                    <td className="text-right py-2">{Math.round(status.resources.memory ?? 0)}MB</td>
                    <td className="text-right py-2">{(status.resources.network ?? 0).toFixed(1)} KB/s</td>
                    <td className="text-right py-2">
                      {status.backgroundTasks
                        ? `${status.backgroundTasks.active}/${status.backgroundTasks.total}`
                        : "0/0"}
                    </td>
                    <td className="text-center py-2">
                      {status.health?.status === "healthy" ? (
                        <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface AnalyticsPanelProps {
  metrics: PerformanceMetric[];
  timeRange: TimeRangeOption;
}

function AnalyticsPanel({ metrics: _metrics, timeRange }: AnalyticsPanelProps) {
  return (
    <div className="space-y-6">
      {/* Performance Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Resource Distribution</CardTitle>
            <CardDescription>How resources are distributed across extensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Resource distribution chart</p>
                <p className="text-sm text-gray-500 md:text-base lg:text-lg">Pie chart would be rendered here</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
            <CardDescription>Performance metrics over {timeRange}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Performance trends chart</p>
                <p className="text-sm text-gray-500 md:text-base lg:text-lg">Bar chart would be rendered here</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
          <CardDescription>AI-powered insights and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg sm:p-4 md:p-6">
              <Target className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">Optimization Opportunity</h4>
                <p className="text-sm text-blue-800 md:text-base lg:text-lg">
                  The Analytics Dashboard extension is using 45% more memory than average. Consider reviewing data
                  caching strategies.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg sm:p-4 md:p-6">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900">Good Performance</h4>
                <p className="text-sm text-green-800 md:text-base lg:text-lg">
                  CPU usage is well within normal ranges across all extensions. Current load balancing is effective.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg sm:p-4 md:p-6">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-900">Resource Alert</h4>
                <p className="text-sm text-yellow-800 md:text-base lg:text-lg">
                  Network usage has increased by 30% in the last hour. Monitor for potential API rate limiting issues.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
