// ui_launchers/KAREN-Theme-Default/src/components/monitoring/endpoint-status-indicator.tsx
"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  TrendingUp,
  Zap,
  ExternalLink,
  RefreshCw,
} from "lucide-react";

/**
 * Endpoint Status Indicator Component
 * Compact status indicator for endpoint connectivity with real-time updates
 */

// Health monitor + diagnostics (expected shapes shown below for reference)
// - getHealthMonitor(): returns an object with:
//   - getMetrics(): HealthMetrics
//   - getStatus(): { isMonitoring: boolean }
//   - onMetricsUpdate(cb: (m: HealthMetrics) => void): () => void
// - getDiagnosticLogger(): returns an object with:
//   - getLogs(limit?: number, category?: string): Array<{ level: string; category: string; timestamp: string }>
//   - onLog(cb: (log: { level: string; category: string; timestamp: string }) => void): () => void
import { getHealthMonitor, type HealthMetrics } from "@/lib/health-monitor";
import { getDiagnosticLogger } from "@/lib/diagnostics";

type MonitorSnapshot = {
  monitor: ReturnType<typeof getHealthMonitor> | null;
  logger: ReturnType<typeof getDiagnosticLogger> | null;
  metrics: HealthMetrics | null;
  isMonitoring: boolean;
  lastUpdate: string;
  recentErrors: number;
};

const resolveInitialSnapshot = (): MonitorSnapshot => {
  const monitor = getHealthMonitor?.() ?? null;
  const logger = getDiagnosticLogger?.() ?? null;

  if (!monitor || !logger) {
    return {
      monitor,
      logger,
      metrics: null,
      isMonitoring: false,
      lastUpdate: "",
      recentErrors: 0,
    };
  }

  let initialMetrics: HealthMetrics | null = null;
  try {
    initialMetrics = monitor.getMetrics?.() ?? null;
  } catch {
    initialMetrics = null;
  }

  let monitoring = false;
  try {
    monitoring = !!monitor.getStatus?.().isMonitoring;
  } catch {
    monitoring = false;
  }

  return {
    monitor,
    logger,
    metrics: initialMetrics,
    isMonitoring: monitoring,
    lastUpdate: "",
    recentErrors: 0,
  };
};

export interface EndpointStatusIndicatorProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function EndpointStatusIndicator({
  className = "",
  showDetails = true,
  compact = false,
}: EndpointStatusIndicatorProps) {
  const initialSnapshot = useMemo(resolveInitialSnapshot, []);
  const monitorRef = useRef<MonitorSnapshot["monitor"]>(initialSnapshot.monitor);
  const loggerRef = useRef<MonitorSnapshot["logger"]>(initialSnapshot.logger);

  const [metrics, setMetrics] = useState<HealthMetrics | null>(
    () => initialSnapshot.metrics
  );
  const [isMonitoring, setIsMonitoring] = useState<boolean>(
    () => initialSnapshot.isMonitoring
  );
  const [lastUpdate, setLastUpdate] = useState<string>(
    () => initialSnapshot.lastUpdate
  );
  const [recentErrors, setRecentErrors] = useState<number>(
    () => initialSnapshot.recentErrors
  );

  useEffect(() => {
    if (!monitorRef.current || !loggerRef.current) {
      monitorRef.current = getHealthMonitor?.() ?? null;
      loggerRef.current = getDiagnosticLogger?.() ?? null;
    }

    const monitor = monitorRef.current;
    const logger = loggerRef.current;

    if (!monitor || !logger) {
      return undefined;
    }

    try {
      setIsMonitoring(!!monitor.getStatus?.().isMonitoring);
    } catch {
      // noop
    }

    const errorTimers: number[] = [];

    const unsubscribeMetrics =
      monitor.onMetricsUpdate?.((newMetrics: HealthMetrics) => {
        setMetrics(newMetrics);
        setLastUpdate(new Date().toLocaleTimeString());

        try {
          setIsMonitoring(!!monitor.getStatus?.().isMonitoring);
        } catch {
          // noop
        }
      }) ?? (() => {});

    const timers = new Set<ReturnType<typeof setTimeout>>();

    const unsubscribeLogs =
      logger.onLog?.((newLog: { level?: string; category?: string } | null) => {
        if (newLog?.level === "error" && newLog?.category === "network") {
          setRecentErrors((prev) => prev + 1);
          const timeoutId = window.setTimeout(() => {
            setRecentErrors((prev) => Math.max(0, prev - 1));
            timers.delete(timeoutId);
          }, 5 * 60 * 1000);
          errorTimers.push(timeoutId);
        }
      }) ?? (() => {});

    return () => {
      try {
        unsubscribeMetrics();
        unsubscribeLogs();
      } catch {
        // noop
      }

      errorTimers.forEach((timeoutId) => {
        window.clearTimeout(timeoutId);
      });
    };
  }, []);

  const getOverallStatus = (): "healthy" | "degraded" | "error" | "unknown" => {
    if (!metrics) return "unknown";

    const endpoints = metrics.endpoints ?? {};
    const hasErrors = Object.values(endpoints).some(
      (e: Event) => e?.status === "error"
    );
    if (hasErrors) return "error";

    const errorRate = Number(metrics.errorRate ?? 0);
    if (errorRate > 0.1) return "error";
    if (errorRate > 0.05) return "degraded";

    const art = Number(metrics.averageResponseTime ?? 0);
    if (art > 10000) return "error";
    if (art > 5000) return "degraded";

    return "healthy";
  };

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

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "healthy":
        return "default" as const;
      case "degraded":
        return "secondary" as const;
      case "error":
        return "destructive" as const;
      default:
        return "outline" as const;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "healthy":
        return "Healthy";
      case "degraded":
        return "Degraded";
      case "error":
        return "Error";
      default:
        return "Unknown";
    }
  };

  const formatUptime = (uptimeMs: number) => {
    const seconds = Math.floor((uptimeMs || 0) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m`;
    return `${seconds}s`;
  };

  const overallStatus = getOverallStatus();
  const healthyEndpoints = metrics
    ? Object.values(metrics.endpoints ?? {}).filter(
        (e: Event) => e?.status === "healthy"
      ).length
    : 0;
  const totalEndpoints = metrics
    ? Object.keys(metrics.endpoints ?? {}).length
    : 0;

  // Compact pill (icon + optional error count)
  if (compact) {
    return (
      <div className={`flex items-center gap-1 ${className}`}>
        {getStatusIcon(overallStatus)}
        {recentErrors > 0 && (
          <Badge variant="destructive" className="text-[10px] px-1 py-0 h-4">
            {recentErrors}
          </Badge>
        )}
      </div>
    );
  }

  // Minimal (no popover details)
  if (!showDetails) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {getStatusIcon(overallStatus)}
        <Badge variant={getStatusBadgeVariant(overallStatus)}>
          {getStatusText(overallStatus)}
        </Badge>
        {recentErrors > 0 && (
          <Badge variant="destructive" className="text-[10px] sm:text-xs md:text-sm">
            {recentErrors}
          </Badge>
        )}
      </div>
    );
  }

  // Full popover with quick stats and endpoint list
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className={`gap-2 ${className}`}>
          {getStatusIcon(overallStatus)}
          <Badge variant={getStatusBadgeVariant(overallStatus)}>
            {getStatusText(overallStatus)}
          </Badge>
          {recentErrors > 0 && (
            <Badge variant="destructive" className="text-[10px] sm:text-xs md:text-sm">
              {recentErrors}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Endpoint Status</h4>
            <div className="flex items-center gap-2">
              {getStatusIcon(overallStatus)}
              <Badge variant={getStatusBadgeVariant(overallStatus)}>
                {getStatusText(overallStatus)}
              </Badge>
            </div>
          </div>

          {/* Loading state */}
          {!metrics && (
            <div className="flex items-center justify-center py-4">
              <div className="text-center">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Loading status...
                </p>
              </div>
            </div>
          )}

          {/* Metrics body */}
          {metrics && (
            <div className="space-y-3">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Error Rate</div>
                    <div className="text-muted-foreground">
                      {(Number(metrics.errorRate ?? 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Response Time</div>
                    <div className="text-muted-foreground">
                      {Number(metrics.averageResponseTime ?? 0).toFixed(0)}ms
                    </div>
                  </div>
                </div>
              </div>

              {/* Endpoint Summary */}
              <div className="text-sm">
                <div className="font-medium mb-2">
                  Endpoints ({healthyEndpoints}/{totalEndpoints} healthy)
                </div>
                <Progress
                  value={
                    totalEndpoints > 0
                      ? (healthyEndpoints / totalEndpoints) * 100
                      : 0
                  }
                  className="h-2"
                />
              </div>

              {/* Individual Endpoints */}
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {Object.entries(metrics.endpoints ?? {}).map(
                  ([endpoint, result]: unknown) => (
                    <div
                      key={endpoint}
                      className="flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {getStatusIcon(result?.status ?? "unknown")}
                        <span className="truncate" title={endpoint}>
                          {endpoint.split("/").pop() || endpoint}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span>{Number(result?.responseTime ?? 0)}ms</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-4 w-4 p-0"
                          onClick={() => {
                            try {
                              window.open(endpoint, "_blank", "noopener,noreferrer");
                            } catch {
                              // noop
                            }
                          }}
                          aria-label={`Open ${endpoint}`}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  )
                )}
              </div>

              {/* Recent Activity */}
              <div className="text-sm">
                <div className="font-medium mb-1">Activity</div>
                <div className="text-muted-foreground space-y-1">
                  <div className="flex justify-between">
                    <span>Total Requests:</span>
                    <span>{Number(metrics.totalRequests ?? 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Errors:</span>
                    <span className={recentErrors > 0 ? "text-red-600" : ""}>
                      {recentErrors}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uptime:</span>
                    <span>{formatUptime(Number(metrics.uptime ?? 0))}</span>
                  </div>
                </div>
              </div>

              {/* Monitoring Status */}
              <div className="flex items-center justify-between text-sm pt-2 border-t">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isMonitoring ? "bg-green-500" : "bg-gray-400"
                    }`}
                  />
                  <span className="text-muted-foreground">
                    {isMonitoring ? "Monitoring Active" : "Monitoring Stopped"}
                  </span>
                </div>
                {lastUpdate && (
                  <span className="text-muted-foreground text-xs">
                    {lastUpdate}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default EndpointStatusIndicator;
