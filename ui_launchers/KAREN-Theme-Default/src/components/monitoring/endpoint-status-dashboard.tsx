// ui_launchers/KAREN-Theme-Default/src/components/monitoring/endpoint-status-dashboard.tsx
"use client";

import React, { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { webUIConfig } from "@/lib/config";

// Health / Diagnostics providers
import {
  getHealthMonitor,
  type HealthMetrics,
  type Alert as HealthAlert,
} from "@/lib/health-monitor";
import {
  getDiagnosticLogger,
  type DiagnosticInfo,
} from "@/lib/diagnostics";
import {
  getNetworkDiagnostics,
  type ComprehensiveNetworkReport,
} from "@/lib/network-diagnostics";

// Icons
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Copy,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  Globe,
  Pause,
  Play,
  RefreshCw,
  Server,
  Shield,
  XCircle,
} from "lucide-react";

export interface EndpointStatusDashboardProps {
  className?: string;
}

export function EndpointStatusDashboard({ className }: EndpointStatusDashboardProps) {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [diagnosticLogs, setDiagnosticLogs] = useState<DiagnosticInfo[]>([]);
  const [networkReport, setNetworkReport] = useState<ComprehensiveNetworkReport | null>(null);

  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isRunningDiagnostics, setIsRunningDiagnostics] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>("");

  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("");
  const [customEndpoint, setCustomEndpoint] = useState<string>("");

  const [showDetailedLogs, setShowDetailedLogs] = useState(false);
  const [logFilter, setLogFilter] = useState<"all" | "error" | "network" | "cors">("all");

  // ----------------------------- Effects: subscribe to health + logs -----------------------------
  useEffect(() => {
    const healthMonitor = getHealthMonitor();
    const diagnosticLogger = getDiagnosticLogger();

    // Bootstrap current state
    try {
      setMetrics(healthMonitor.getMetrics());
      setDiagnosticLogs(diagnosticLogger.getLogs(50));
      setIsMonitoring(healthMonitor.getStatus().isMonitoring);
    } catch {
      // providers may throw if uninitialized; UI will still render
    }

    // Subscriptions
    const unsubscribeMetrics = healthMonitor.onMetricsUpdate((newMetrics) => {
      setMetrics(newMetrics);
      setLastUpdate(new Date().toLocaleTimeString());
    });

    const unsubscribeLogs = diagnosticLogger.onLog((newLog) => {
      setDiagnosticLogs((prev) => [newLog, ...prev.slice(0, 49)]);
    });

    // Ensure monitoring is active
    if (!healthMonitor.getStatus().isMonitoring) {
      healthMonitor.start();
      setIsMonitoring(true);
    }

    return () => {
      try {
        unsubscribeMetrics?.();
        unsubscribeLogs?.();
      } catch {
        // noop
      }
    };
  }, []);

  // ----------------------------- Handlers -----------------------------
  const handleToggleMonitoring = () => {
    const healthMonitor = getHealthMonitor();
    if (isMonitoring) {
      healthMonitor.stop();
      setIsMonitoring(false);
    } else {
      healthMonitor.start();
      setIsMonitoring(true);
    }
  };

  const handleRunComprehensiveDiagnostics = async () => {
    setIsRunningDiagnostics(true);
    try {
      const networkDiagnostics = getNetworkDiagnostics();
      const report = await networkDiagnostics.runComprehensiveTest();
      setNetworkReport(report);
    } catch {
      // Optional: toast or error banner
    } finally {
      setIsRunningDiagnostics(false);
    }
  };

  const handleTestCustomEndpoint = async () => {
    if (!customEndpoint.trim()) return;
    setIsRunningDiagnostics(true);
    try {
      const networkDiagnostics = getNetworkDiagnostics();
      await networkDiagnostics.testEndpointDetailed(customEndpoint.trim());
    } catch {
      // Optional: toast
    } finally {
      setIsRunningDiagnostics(false);
    }
  };

  const handleExportDiagnostics = () => {
    const diagnosticLogger = getDiagnosticLogger();
    const exportData = diagnosticLogger.exportLogs();
    const blob = new Blob([exportData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `karen-diagnostics-${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyEndpointUrl = (endpoint: string) => {
    navigator.clipboard?.writeText(endpoint);
  };

  // ----------------------------- Helpers -----------------------------
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "degraded":
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getLogIcon = (category: string) => {
    switch (category) {
      case "network":
        return <Globe className="h-4 w-4" />;
      case "cors":
      case "auth":
        return <Shield className="h-4 w-4" />;
      case "api":
        return <Server className="h-4 w-4" />;
      case "health":
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const filteredLogs = useMemo(() => {
    return diagnosticLogs.filter((log) => {
      if (logFilter === "all") return true;
      if (logFilter === "error") return log.level === "error";
      return log.category === logFilter;
    });
  }, [diagnosticLogs, logFilter]);

  // ----------------------------- Loading guard -----------------------------
  if (!metrics) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="text-center">
          <RefreshCw className="mx-auto mb-2 h-8 w-8 animate-spin" />
          <p>Loading endpoint status...</p>
        </div>
      </div>
    );
  }

  // Normalize endpoints shape
  const endpointsEntries = Object.entries(metrics.endpoints ?? {});

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Endpoint Status Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time connectivity monitoring and network diagnostics
            {lastUpdate ? ` · Updated ${lastUpdate}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isMonitoring ? "default" : "secondary"}>
            {isMonitoring ? "Monitoring Active" : "Monitoring Stopped"}
          </Badge>
          <Button variant="outline" size="sm" onClick={handleToggleMonitoring} aria-label="Toggle monitoring">
            {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span className="ml-2">{isMonitoring ? "Stop" : "Start"}</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunComprehensiveDiagnostics}
            disabled={isRunningDiagnostics}
            aria-label="Run comprehensive diagnostics"
          >
            {isRunningDiagnostics ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Activity className="h-4 w-4" />
            )}
            <span className="ml-2">Run Diagnostics</span>
          </Button>
        </div>
      </div>

      {/* Configuration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Backend Configuration
          </CardTitle>
          <CardDescription>Active environment and fallback endpoints</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
            <div>
              <Label className="text-muted-foreground">Backend URL</Label>
              <div className="mt-1 flex items-center gap-2">
                <code className="rounded bg-muted px-2 py-1 text-xs sm:text-sm md:text-base">
                  {webUIConfig.backendUrl}
                </code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopyEndpointUrl(webUIConfig.backendUrl)}
                  aria-label="Copy backend URL"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground">Environment</Label>
              <div className="mt-1">
                <Badge variant="outline">{webUIConfig.environment}</Badge>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground">Network Mode</Label>
              <div className="mt-1">
                <Badge variant="outline">{webUIConfig.networkMode}</Badge>
              </div>
            </div>
          </div>

          {webUIConfig.fallbackBackendUrls?.length > 0 && (
            <div className="mt-4">
              <Label className="text-muted-foreground">Fallback URLs</Label>
              <div className="mt-1 flex flex-wrap gap-2">
                {webUIConfig.fallbackBackendUrls.map((url, index) => (
                  <div key={index} className="flex items-center gap-1">
                    <code className="rounded bg-muted px-2 py-1 text-xs sm:text-sm md:text-base">
                      {url}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyEndpointUrl(url)}
                      aria-label="Copy fallback URL"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Network Report Summary */}
      {networkReport && (
        <Alert>
          <Activity className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>
                Comprehensive diagnostics completed:{" "}
                {networkReport.summary.passedTests}/{networkReport.summary.totalTests} tests passed
              </span>
              <Badge
                variant={
                  networkReport.overallStatus === "healthy"
                    ? "default"
                    : networkReport.overallStatus === "degraded"
                    ? "secondary"
                    : "destructive"
                }
              >
                {networkReport.overallStatus}
              </Badge>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs defaultValue="endpoints" className="w-full">
        <TabsList>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="diagnostics">
            Diagnostics
            {filteredLogs.some((l) => l.level === "error") && (
              <Badge variant="destructive" className="ml-2">
                {filteredLogs.filter((l) => l.level === "error").length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="testing">Manual Testing</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Endpoints */}
        <TabsContent value="endpoints" className="space-y-4">
          <div className="grid gap-4">
            {endpointsEntries.map(([endpoint, result]) => (
              <Card
                key={endpoint}
                className={cn(selectedEndpoint === endpoint && "ring-2 ring-primary")}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
                      {getStatusIcon(result.status)}
                      {endpoint}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant={result.status === "healthy" ? "default" : "destructive"}>
                        {result.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setSelectedEndpoint((s) => (s === endpoint ? "" : endpoint))
                        }
                        aria-label={
                          selectedEndpoint === endpoint ? "Hide details" : "Show details"
                        }
                      >
                        {selectedEndpoint === endpoint ? (
                          <EyeOff className="h-3 w-3" />
                        ) : (
                          <Eye className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                    <div>
                      <span className="text-muted-foreground">Response Time:</span>
                      <div className="mt-1 font-mono">
                        {result.responseTime}ms
                        <Progress
                          value={Math.min((result.responseTime / 5000) * 100, 100)}
                          className="mt-1 h-1"
                        />
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Last Check:</span>
                      <div className="mt-1">
                        {new Date(result.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <div className="mt-1">
                        <Badge variant={result.status === "healthy" ? "default" : "destructive"}>
                          {result.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyEndpointUrl(endpoint)}
                        aria-label="Copy endpoint"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(endpoint, "_blank")}
                        aria-label="Open endpoint in new tab"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>

                  {selectedEndpoint === endpoint && (
                    <div className="mt-4 space-y-2">
                      {result.error && (
                        <div className="rounded border-l-4 border-red-500 bg-red-50 p-3 sm:p-4 md:p-6">
                          <div className="text-sm font-medium text-red-800 md:text-base lg:text-lg">
                            Error Details
                          </div>
                          <div className="mt-1 text-sm text-red-700 md:text-base lg:text-lg">
                            {result.error}
                          </div>
                        </div>
                      )}
                      {result.details && (
                        <div className="rounded bg-gray-50 p-3 sm:p-4 md:p-6">
                          <div className="mb-2 text-sm font-medium md:text-base lg:text-lg">
                            Response Details
                          </div>
                          <pre className="text-xs sm:text-sm md:text-base overflow-auto">
                            {JSON.stringify(result.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Diagnostics */}
        <TabsContent value="diagnostics" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Label>Filter:</Label>
              <select
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value as any)}
                className="rounded border px-3 py-1 text-sm md:text-base lg:text-lg"
              >
                <option value="all">All Logs</option>
                <option value="error">Errors Only</option>
                <option value="network">Network</option>
                <option value="cors">CORS</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetailedLogs((s) => !s)}
                aria-label={showDetailedLogs ? "Hide details" : "Show details"}
              >
                {showDetailedLogs ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                <span className="ml-2">{showDetailedLogs ? "Hide Details" : "Show Details"}</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportDiagnostics}
                aria-label="Export diagnostics"
              >
                <Download className="h-4 w-4" />
                <span className="ml-2">Export</span>
              </Button>
            </div>
          </div>

          <div className="max-h-96 space-y-2 overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <Activity className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                    <p className="text-muted-foreground">No diagnostic logs found</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              filteredLogs.map((log, index) => (
                <Card
                  key={index}
                  className={
                    log.level === "error"
                      ? "border-red-200 bg-red-50"
                      : log.level === "warn"
                      ? "border-yellow-200 bg-yellow-50"
                      : "border-gray-200"
                  }
                >
                  <CardContent className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex flex-1 items-start gap-2">
                        {getLogIcon(log.category)}
                        <div className="flex-1">
                          <div className="mb-1 flex items-center gap-2">
                            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                              {log.category}
                            </Badge>
                            <Badge
                              variant={
                                log.level === "error"
                                  ? "destructive"
                                  : log.level === "warn"
                                  ? "secondary"
                                  : "default"
                              }
                              className="text-xs sm:text-sm md:text-base"
                            >
                              {log.level}
                            </Badge>
                            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            {log.duration && (
                              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                {log.duration}ms
                              </span>
                            )}
                          </div>

                          <p className="text-sm md:text-base lg:text-lg">{log.message}</p>

                          {log.endpoint && (
                            <code className="rounded bg-muted px-1 py-0.5 text-xs sm:text-sm md:text-base">
                              {log.endpoint}
                            </code>
                          )}

                          {showDetailedLogs && (
                            <div className="mt-2 space-y-2">
                              {log.error && (
                                <div className="rounded bg-red-100 p-2 text-xs text-red-600 sm:text-sm md:text-base">
                                  <strong>Error:</strong>{" "}
                                  {log.error instanceof Error ? log.error.message : String(log.error)}
                                </div>
                              )}

                              {log.details && (
                                <details className="text-xs sm:text-sm md:text-base">
                                  <summary className="cursor-pointer text-muted-foreground">
                                    Details
                                  </summary>
                                  <pre className="mt-1 overflow-auto rounded bg-muted p-2 sm:p-4 md:p-6">
                                    {JSON.stringify(log.details, null, 2)}
                                  </pre>
                                </details>
                              )}

                              {log.troubleshooting && (
                                <div className="rounded bg-blue-50 p-2 text-xs sm:text-sm md:text-base">
                                  <div className="mb-1 font-medium">Troubleshooting:</div>
                                  <div className="space-y-1">
                                    <div>
                                      <strong>Possible Causes:</strong>
                                      <ul className="ml-2 list-inside list-disc">
                                        {log.troubleshooting.possibleCauses.map((cause, i) => (
                                          <li key={i}>{cause}</li>
                                        ))}
                                      </ul>
                                    </div>
                                    <div>
                                      <strong>Suggested Fixes:</strong>
                                      <ul className="ml-2 list-inside list-disc">
                                        {log.troubleshooting.suggestedFixes.map((fix, i) => (
                                          <li key={i}>{fix}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* Manual Testing */}
        <TabsContent value="testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Endpoint Testing</CardTitle>
              <CardDescription>Test custom endpoints or re-test existing ones manually</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <input
                  placeholder="Enter endpoint URL (e.g., /api/health or full URL)"
                  value={customEndpoint}
                  onChange={(e) => setCustomEndpoint(e.target.value)}
                  className="flex-1 rounded border px-3 py-2"
                />
                <Button
                  onClick={handleTestCustomEndpoint}
                  disabled={!customEndpoint.trim() || isRunningDiagnostics}
                  aria-label="Run manual test"
                >
                  {isRunningDiagnostics ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                {["/api/health", "/api/auth/status", "/api/ai/conversation-processing", "/api/memory/query"].map(
                  (endpoint) => (
                    <Button
                      key={endpoint}
                      variant="outline"
                      size="sm"
                      onClick={() => setCustomEndpoint(endpoint)}
                    >
                      {endpoint}
                    </Button>
                  )
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports */}
        <TabsContent value="reports" className="space-y-4">
          {networkReport ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Network Diagnostic Report</CardTitle>
                  <CardDescription>
                    Generated on {new Date(networkReport.timestamp).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{networkReport.summary.totalTests}</div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        Total Tests
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {networkReport.summary.passedTests}
                      </div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Passed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {networkReport.summary.failedTests}
                      </div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Failed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {networkReport.summary.averageResponseTime.toFixed(0)}ms
                      </div>
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        Avg Response
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium">Recommendations:</h4>
                    <ul className="list-inside list-disc space-y-1 text-sm md:text-base lg:text-lg">
                      {networkReport.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2">
                {networkReport.testResults.map((result, index) => (
                  <Card key={index}>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.success ? "healthy" : "error")}
                          <div>
                            <div className="font-medium">{result.test.name}</div>
                            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {result.test.description}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={result.success ? "default" : "destructive"}>
                            {result.success ? "Pass" : "Fail"}
                          </Badge>
                          <div className="mt-1 text-sm text-muted-foreground md:text-base lg:text-lg">
                            {result.diagnostic.responseTime}ms
                          </div>
                        </div>
                      </div>

                      {!!result.recommendations?.length && (
                        <div className="mt-2 rounded bg-yellow-50 p-2 sm:p-4 md:p-6">
                          <div className="mb-1 text-sm font-medium md:text-base lg:text-lg">
                            Recommendations:
                          </div>
                          <ul className="list-inside list-disc space-y-1 text-sm md:text-base lg:text-lg">
                            {result.recommendations.map((rec, i) => (
                              <li key={i}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <Activity className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                  <p className="mb-4 text-muted-foreground">No diagnostic report available</p>
                  <Button
                    onClick={handleRunComprehensiveDiagnostics}
                    disabled={isRunningDiagnostics}
                    aria-label="Run diagnostics"
                  >
                    {isRunningDiagnostics ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Activity className="mr-2 h-4 w-4" />
                    )}
                    Run Diagnostics
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default EndpointStatusDashboard;
