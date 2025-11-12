/**
 * Extension Debugger Component
 *
 * Comprehensive debugging and diagnostic tools for extensions including
 * logs, metrics, performance monitoring, and troubleshooting utilities.
 */
"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
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
  RefreshCw,
  Square,
  Play,
  FileText,
  BarChart3,
  Activity,
  Bug,
  AlertTriangle,
  Info,
  Download,
  Trash2,
  Search,
  Copy,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Terminal,
  Settings,
  ExternalLink,
} from "lucide-react";
type LogLevel = "warning" | "error" | "info" | "debug";

interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  metadata?: Record<string, unknown>;
  stackTrace?: string;
}

type LogFilterLevel = LogLevel | "all";

interface LogFilter {
  level: LogFilterLevel;
  search: string;
  source: "all" | string;
}
interface MetricData {
  timestamp: string;
  cpu: number;
  memory: number;
  network: number;
  requests: number;
  errors: number;
  responseTime: number;
}
interface PerformanceProfile {
  function: string;
  calls: number;
  totalTime: number;
  avgTime: number;
  maxTime: number;
  minTime: number;
}
interface ExtensionDebuggerProps {
  extensionId: string;
  extensionName: string;
  className?: string;
}
export function ExtensionDebugger({
  extensionId,
  extensionName,
  className,
}: ExtensionDebuggerProps) {
  const [activeTab, setActiveTab] = useState("logs");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [performanceProfile, setPerformanceProfile] = useState<
    PerformanceProfile[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [logFilter, setLogFilter] = useState<LogFilter>({
    level: "all",
    search: "",
    source: "all",
  });

  const loadDebuggingData = useCallback(async () => {
    setLoading(true);
    try {
      // Simulate loading debugging data
      await new Promise((resolve) => setTimeout(resolve, 1000));
      //
      const sampleLogs: LogEntry[] = [
        {
          id: "1",
          timestamp: new Date(Date.now() - 5000).toISOString(),
          level: "info",
          message: "Extension initialized successfully",
          source: "core",
        },
        {
          id: "2",
          timestamp: new Date(Date.now() - 4000).toISOString(),
          level: "debug",
          message: "Loading configuration from /config/settings.json",
          source: "config",
          metadata: { configPath: "/config/settings.json", size: 1024 },
        },
        {
          id: "3",
          timestamp: new Date(Date.now() - 3000).toISOString(),
          level: "warning",
          message: "API rate limit approaching (80% of quota used)",
          source: "api",
          metadata: { quota: 1000, used: 800, remaining: 200 },
        },
        {
          id: "4",
          timestamp: new Date(Date.now() - 2000).toISOString(),
          level: "error",
          message: "Failed to connect to external service",
          source: "network",
          metadata: { url: "https://api.example.com", statusCode: 503 },
          stackTrace:
            "Error: Connection timeout\n  at fetch (/extension/api.js:45:12)\n  at processRequest (/extension/handler.js:23:8)",
        },
        {
          id: "5",
          timestamp: new Date(Date.now() - 1000).toISOString(),
          level: "info",
          message: "Background task completed successfully",
          source: "tasks",
          metadata: {
            taskId: "daily-sync",
            duration: 2.5,
            recordsProcessed: 150,
          },
        },
      ];
      // Sample metrics data
      const sampleMetrics = Array.from({ length: 30 }, (_, i) => ({
        timestamp: new Date(Date.now() - (29 - i) * 60000).toISOString(),
        cpu: Math.random() * 50 + 10,
        memory: Math.random() * 200 + 100,
        network: Math.random() * 1000 + 100,
        requests: Math.floor(Math.random() * 50 + 10),
        errors: Math.floor(Math.random() * 5),
        responseTime: Math.random() * 500 + 100,
      }));
      // Sample performance profile
      const sampleProfile: PerformanceProfile[] = [
        {
          function: "processRequest",
          calls: 1250,
          totalTime: 15.6,
          avgTime: 12.5,
          maxTime: 45.2,
          minTime: 2.1,
        },
        {
          function: "validateInput",
          calls: 1250,
          totalTime: 3.2,
          avgTime: 2.6,
          maxTime: 8.1,
          minTime: 0.5,
        },
        {
          function: "fetchData",
          calls: 890,
          totalTime: 22.1,
          avgTime: 24.8,
          maxTime: 120.5,
          minTime: 5.2,
        },
        {
          function: "renderResponse",
          calls: 1180,
          totalTime: 8.9,
          avgTime: 7.5,
          maxTime: 25.3,
          minTime: 1.2,
        },
      ];
      setLogs(
        sampleLogs.map((entry) => ({
          ...entry,
          id: `${extensionId}-${entry.id}`,
          message: `[${extensionId}] ${entry.message}`,
        }))
      );
      setMetrics(
        sampleMetrics.map((metric) => ({
          ...metric,
          name: `${metric.name} (${extensionId})`,
        }))
      );
      setPerformanceProfile(sampleProfile);
    } catch (error) {
      console.error("Failed to load debugging data:", error);
    } finally {
      setLoading(false);
    }
  }, [extensionId]);

  // Load debugging data
  useEffect(() => {
    loadDebuggingData();
  }, [loadDebuggingData]);

  const updateLogFilter = useCallback((update: Partial<LogFilter>) => {
    setLogFilter((prev) => ({ ...prev, ...update }));
  }, []);
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (logFilter.level !== "all" && log.level !== logFilter.level)
        return false;
      if (logFilter.source !== "all" && log.source !== logFilter.source)
        return false;
      if (
        logFilter.search &&
        !log.message.toLowerCase().includes(logFilter.search.toLowerCase())
      )
        return false;
      return true;
    });
  }, [logs, logFilter]);
  const logSources = useMemo(() => {
    const sources = new Set(logs.map((log) => log.source));
    return Array.from(sources);
  }, [logs]);
  const handleExportLogs = useCallback(() => {
    const logData = filteredLogs.map((log) => ({
      timestamp: log.timestamp,
      level: log.level,
      source: log.source,
      message: log.message,
      metadata: log.metadata,
      stackTrace: log.stackTrace,
    }));
    const blob = new Blob([JSON.stringify(logData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${extensionId}-logs-${
      new Date().toISOString().split("T")[0]
    }.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [filteredLogs, extensionId]);
  const handleClearLogs = useCallback(() => {
    setLogs([]);
  }, []);
  const toggleStreaming = useCallback(() => {
    setStreaming((prev) => !prev);
    // In real implementation, this would start/stop log streaming
  }, []);
  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4 " />
          <p className="text-gray-600">Loading debugging tools...</p>
        </div>
      </div>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Extension Debugger
          </h1>
          <p className="text-gray-600 mt-1">
            Debug and monitor {extensionName}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={toggleStreaming}
            className={`flex items-center gap-2 ${
              streaming ? "text-red-600" : "text-green-600"
            }`}
          >
            {streaming ? (
              <Square className="h-4 w-4 " />
            ) : (
              <Play className="h-4 w-4 " />
            )}
            {streaming ? "Stop" : "Start"} Live Monitoring
          </Button>
          <Button
            variant="outline"
            onClick={loadDebuggingData}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4 " />
          </Button>
        </div>
      </div>
      {/* Debug Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="logs">
            <FileText className="h-4 w-4 mr-2 " />
            Logs ({filteredLogs.length})
          </TabsTrigger>
          <TabsTrigger value="metrics">
            <BarChart3 className="h-4 w-4 mr-2 " />
          </TabsTrigger>
          <TabsTrigger value="performance">
            <Activity className="h-4 w-4 mr-2 " />
          </TabsTrigger>
          <TabsTrigger value="diagnostics">
            <Bug className="h-4 w-4 mr-2 " />
          </TabsTrigger>
        </TabsList>
        <TabsContent value="logs" className="space-y-4">
          <LogsPanel
            logs={filteredLogs}
            filter={logFilter}
            sources={logSources}
            streaming={streaming}
            onFilterChange={updateLogFilter}
            onExport={handleExportLogs}
            onClear={handleClearLogs}
          />
        </TabsContent>
        <TabsContent value="metrics" className="space-y-4">
          <MetricsPanel metrics={metrics} />
        </TabsContent>
        <TabsContent value="performance" className="space-y-4">
          <PerformancePanel profile={performanceProfile} />
        </TabsContent>
        <TabsContent value="diagnostics" className="space-y-4">
          <DiagnosticsPanel extensionId={extensionId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
interface LogsPanelProps {
  logs: LogEntry[];
  filter: LogFilter;
  sources: string[];
  streaming: boolean;
  onFilterChange: (update: Partial<LogFilter>) => void;
  onExport: () => void;
  onClear: () => void;
}
function LogsPanel({
  logs,
  filter,
  sources,
  streaming,
  onFilterChange,
  onExport,
  onClear,
}: LogsPanelProps) {

  return (
    <div className="space-y-4">
      {/* Log Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Log Viewer</CardTitle>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={onExport}>
                <Download className="h-3 w-3 mr-1" />
                Export
              </Button>
              <Button size="sm" variant="outline" onClick={onClear}>
                <Trash2 className="h-3 w-3 mr-1" />
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 " />
              <input
                type="text"
                placeholder="Search logs..."
                value={filter.search}
                onChange={(e) =>
                  onFilterChange({ search: e.target.value })
                }
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={filter.level}
              onChange={(e) =>
                onFilterChange({ level: e.target.value as LogFilterLevel })
              }
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
            <select
              value={filter.source}
              onChange={(e) =>
                onFilterChange({ source: e.target.value })
              }
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Sources</option>
              {sources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>
          {streaming && (
            <div className="mt-3 flex items-center gap-2 text-sm text-green-600 md:text-base lg:text-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Live streaming enabled
            </div>
          )}
        </CardContent>
      </Card>
      {/* Log Entries */}
      <Card>
        <CardContent className="p-0 sm:p-4 md:p-6">
          <div className="max-h-96 overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4 " />
                <p>No log entries found</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {logs.map((log) => (
                  <LogEntry key={log.id} log={log} />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
function LogEntry({ log }: { log: LogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const getLevelColor = (level: LogLevel) => {
    switch (level) {
      case "error":
        return "bg-red-100 text-red-800";
      case "warning":
        return "bg-yellow-100 text-yellow-800";
      case "info":
        return "bg-blue-100 text-blue-800";
      case "debug":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };
  return (
    <div className="p-4 hover:bg-gray-50 sm:p-4 md:p-6">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          <Badge className={getLevelColor(log.level)}>{log.level}</Badge>
        </div>
        <div className="flex-1 min-w-0 ">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-mono text-gray-500 md:text-base lg:text-lg">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <Badge
              variant="outline"
              className="text-xs sm:text-sm md:text-base"
            >
              {log.source}
            </Badge>
          </div>
          <p className="text-sm text-gray-900 mb-2 md:text-base lg:text-lg">
            {log.message}
          </p>
          {(log.metadata || log.stackTrace) && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setExpanded(!expanded)}
              className="text-xs sm:text-sm md:text-base"
            >
              {expanded ? "Hide" : "Show"} Details
            </Button>
          )}
          {expanded && (
            <div className="mt-3 space-y-2">
              {log.metadata && (
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-1 sm:text-sm md:text-base">
                    Metadata:
                  </h5>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto sm:text-sm md:text-base">
                    {JSON.stringify(log.metadata, null, 2)}
                  </pre>
                </div>
              )}
              {log.stackTrace && (
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-1 sm:text-sm md:text-base">
                    Stack Trace:
                  </h5>
                  <pre className="text-xs bg-red-50 p-2 rounded overflow-x-auto text-red-800 sm:text-sm md:text-base">
                    {log.stackTrace}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() =>
            navigator.clipboard.writeText(JSON.stringify(log, null, 2))
          }
        >
          <Copy className="h-3 w-3 " />
        </Button>
      </div>
    </div>
  );
}
function MetricsPanel({ metrics }: { metrics: MetricData[] }) {
  const latestMetrics = metrics[metrics.length - 1];
  return (
    <div className="space-y-6">
      {/* Current Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics?.cpu.toFixed(1)}%
            </div>
            <div className="flex items-center mt-1">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1 " />
              <span className="text-xs text-green-600 sm:text-sm md:text-base">
                Normal
              </span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(latestMetrics?.memory || 0)}MB
            </div>
            <div className="flex items-center mt-1">
              <TrendingUp className="h-3 w-3 text-yellow-500 mr-1 " />
              <span className="text-xs text-yellow-600 sm:text-sm md:text-base">
                Moderate
              </span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Network
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(latestMetrics?.network || 0)} KB/s
            </div>
            <div className="flex items-center mt-1">
              <TrendingDown className="h-3 w-3 text-green-500 mr-1 " />
              <span className="text-xs text-green-600 sm:text-sm md:text-base">
                Low
              </span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics?.requests || 0}
            </div>
            <div className="flex items-center mt-1">
              <TrendingUp className="h-3 w-3 text-blue-500 mr-1 " />
              <span className="text-xs text-blue-600 sm:text-sm md:text-base">
                Active
              </span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics?.errors || 0}
            </div>
            <div className="flex items-center mt-1">
              <CheckCircle className="h-3 w-3 text-green-500 mr-1 " />
              <span className="text-xs text-green-600 sm:text-sm md:text-base">
                Good
              </span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Response Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(latestMetrics?.responseTime || 0)}ms
            </div>
            <div className="flex items-center mt-1">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1 " />
              <span className="text-xs text-green-600 sm:text-sm md:text-base">
                Fast
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Metrics Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
          <CardDescription>
            Resource usage over the last 30 minutes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4 " />
              <p className="text-gray-600">
                Metrics chart would be rendered here
              </p>
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
function PerformancePanel({ profile }: { profile: PerformanceProfile[] }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Function Performance Profile</CardTitle>
          <CardDescription>
            Performance breakdown by function calls
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm md:text-base lg:text-lg">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Function</th>
                  <th className="text-right py-2">Calls</th>
                  <th className="text-right py-2">Total Time (s)</th>
                  <th className="text-right py-2">Avg Time (ms)</th>
                  <th className="text-right py-2">Max Time (ms)</th>
                  <th className="text-right py-2">Min Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                {profile.map((func, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-2 font-mono text-blue-600">
                      {func.function}
                    </td>
                    <td className="text-right py-2">
                      {func.calls.toLocaleString()}
                    </td>
                    <td className="text-right py-2">
                      {func.totalTime.toFixed(2)}
                    </td>
                    <td className="text-right py-2">
                      {func.avgTime.toFixed(2)}
                    </td>
                    <td className="text-right py-2 text-red-600">
                      {func.maxTime.toFixed(2)}
                    </td>
                    <td className="text-right py-2 text-green-600">
                      {func.minTime.toFixed(2)}
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
function DiagnosticsPanel({ extensionId }: { extensionId: string }) {
  type DiagnosticCategory = "health" | "dependencies" | "permissions" | "configuration" | "connectivity";
  type DiagnosticStatus =
    | "healthy"
    | "ok"
    | "granted"
    | "valid"
    | "connected"
    | "warning"
    | "missing"
    | "denied"
    | "invalid"
    | "disconnected";

  type DiagnosticsState = Record<DiagnosticCategory, DiagnosticStatus>;

  const [diagnostics, setDiagnostics] = useState<DiagnosticsState>({
    health: "healthy",
    dependencies: "ok",
    permissions: "granted",
    configuration: "valid",
    connectivity: "connected",
  });

  const runDiagnostics = useCallback(async () => {
    // Simulate running diagnostics
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setDiagnostics({
      health: Math.random() > 0.2 ? "healthy" : "warning",
      dependencies: Math.random() > 0.1 ? "ok" : "missing",
      permissions: Math.random() > 0.05 ? "granted" : "denied",
      configuration: Math.random() > 0.1 ? "valid" : "invalid",
      connectivity: Math.random() > 0.15 ? "connected" : "disconnected",
    });
  }, []);
  const getStatusColor = (status: DiagnosticStatus) => {
    switch (status) {
      case "healthy":
      case "ok":
      case "granted":
      case "valid":
      case "connected":
        return "text-green-600 bg-green-100";
      case "warning":
        return "text-yellow-600 bg-yellow-100";
      case "missing":
      case "denied":
      case "invalid":
      case "disconnected":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };
  const getStatusIcon = (status: DiagnosticStatus) => {
    switch (status) {
      case "healthy":
      case "ok":
      case "granted":
      case "valid":
      case "connected":
        return <CheckCircle className="h-4 w-4 " />;
      case "warning":
        return <AlertTriangle className="h-4 w-4 " />;
      case "missing":
      case "denied":
      case "invalid":
      case "disconnected":
        return <AlertTriangle className="h-4 w-4 " />;
      default:
        return <Info className="h-4 w-4 " />;
    }
  };
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System Diagnostics</CardTitle>
              <CardDescription>
                Check extension health and configuration for {extensionId}
              </CardDescription>
            </div>
            <Button onClick={runDiagnostics}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Run Diagnostics
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(diagnostics).map(([check, status]) => (
              <div
                key={check}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg sm:p-4 md:p-6"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-1 rounded ${getStatusColor(status)}`}>
                    {getStatusIcon(status)}
                  </div>
                  <div>
                    <h4 className="font-medium capitalize">
                      {check.replace("_", " ")}
                    </h4>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                      {check === "health" && "Overall extension health status"}
                      {check === "dependencies" &&
                        "Required dependencies and plugins"}
                      {check === "permissions" &&
                        "System permissions and access rights"}
                      {check === "configuration" &&
                        "Extension configuration validity"}
                      {check === "connectivity" &&
                        "Network connectivity and API access"}
                    </p>
                  </div>
                </div>
                <Badge className={getStatusColor(status)}>{status}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common debugging and troubleshooting actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start">
              <Terminal className="h-4 w-4 mr-2" />
              Open Console
            </Button>
            <Button variant="outline" className="justify-start">
              <Settings className="h-4 w-4 mr-2" />
              Reset Config
            </Button>
            <Button variant="outline" className="justify-start">
              <RefreshCw className="h-4 w-4 mr-2" />
              Restart Extension
            </Button>
            <Button variant="outline" className="justify-start">
              <ExternalLink className="h-4 w-4 mr-2" />
              View Documentation
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
