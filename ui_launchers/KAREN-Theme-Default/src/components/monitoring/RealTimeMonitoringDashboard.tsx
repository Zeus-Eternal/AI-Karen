// ui_launchers/KAREN-Theme-Default/src/components/monitoring/RealTimeMonitoringDashboard.tsx
"use client";

/**
 * Real-time monitoring dashboard component
 * - One-glance overall health + component status
 * - Mocked generator by default; wire actual sources later
 * - Safe ErrorBoundary wrapper, SSR-safe guards, and clean intervals
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  ErrorBoundary,
  type ErrorFallbackProps,
} from "@/components/error-handling/ErrorBoundary";

import type { SystemHealth, MonitoringConfig } from "./types";
import { ConnectionStatusIndicator } from "./ConnectionStatusIndicator";
import { PerformanceMetricsDisplay } from "./PerformanceMetricsDisplay";
import { ErrorRateDisplay } from "./ErrorRateDisplay";
import { AuthenticationMetricsDisplay } from "./AuthenticationMetricsDisplay";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { connectivityLogger, performanceTracker } from "@/lib/logging";

export interface RealTimeMonitoringDashboardProps {
  config?: Partial<MonitoringConfig>;
  className?: string;
  onHealthChange?: (health: SystemHealth) => void;
}

const MonitoringDashboardFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
  error,
  errorId,
  retryCount,
  errorInfo: _errorInfo,
}) => (
  <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4" role="alert">
    <p className="font-semibold">Something went wrong in RealTimeMonitoringDashboard</p>
    <p className="text-sm text-muted-foreground">
      {error.message}
      {errorId ? ` (ref: ${errorId})` : ""}
    </p>
    <Button variant="outline" size="sm" className="mt-2" onClick={resetError}>
      Retry attempt {retryCount + 1}
    </Button>
  </div>
);

export const RealTimeMonitoringDashboard: React.FC<
  RealTimeMonitoringDashboardProps
> = ({ config = {}, className = "", onHealthChange }) => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const defaultConfig: MonitoringConfig = useMemo(
    () => ({
      refreshInterval: 30_000, // 30 seconds
      enableRealTimeUpdates: true,
      showDetailedMetrics: true,
      alertThresholds: {
        responseTime: 5000,
        errorRate: 5,
        authFailureRate: 15,
      },
      ...config,
    }),
    [config]
  );

  // --- Mock data generator (replace with real fetchers/wss sources later)
  const generateMockSystemHealth = useCallback((): SystemHealth => {
    const now = new Date();
    const performanceStats =
      performanceTracker?.getPerformanceStats?.() ?? { count: 0 };

    const baseResponseTime = 800 + Math.random() * 400; // 800–1200ms
    const errorRate = Math.random() * 3; // 0–3%
    const authSuccessRate = 95 + Math.random() * 4; // 95–99%

    return {
      overall:
        errorRate < 1 && baseResponseTime < 2000 && authSuccessRate > 95
          ? "healthy"
          : errorRate < 5 && baseResponseTime < 5000 && authSuccessRate > 85
          ? "degraded"
          : "critical",
      components: {
        backend: {
          isConnected: Math.random() > 0.05,
          lastCheck: new Date(now.getTime() - Math.random() * 60_000),
          responseTime: baseResponseTime,
          endpoint: "http://localhost:8000",
          status:
            baseResponseTime < 2000
              ? "healthy"
              : baseResponseTime < 5000
              ? "degraded"
              : "failed",
          errorCount: Math.floor(Math.random() * 10),
          successCount: Math.floor(Math.random() * 100) + 50,
        },
        database: {
          isConnected: Math.random() > 0.02,
          lastCheck: new Date(now.getTime() - Math.random() * 30_000),
          responseTime: baseResponseTime * 0.6,
          endpoint: "postgresql://localhost:5432",
          status:
            baseResponseTime < 1500
              ? "healthy"
              : baseResponseTime < 3000
              ? "degraded"
              : "failed",
          errorCount: Math.floor(Math.random() * 5),
          successCount: Math.floor(Math.random() * 200) + 100,
        },
        authentication: {
          isConnected: Math.random() > 0.01,
          lastCheck: new Date(now.getTime() - Math.random() * 45_000),
          responseTime: baseResponseTime * 1.2,
          endpoint: "/api/auth",
          status:
            authSuccessRate > 95 ? "healthy" : authSuccessRate > 85 ? "degraded" : "failed",
          errorCount: Math.floor(Math.random() * 8),
          successCount: Math.floor(Math.random() * 80) + 40,
        },
      },
      performance: {
        averageResponseTime: baseResponseTime,
        p95ResponseTime: baseResponseTime * 1.5,
        p99ResponseTime: baseResponseTime * 2.2,
        requestCount:
          performanceStats.count || Math.floor(Math.random() * 1000) + 500,
        errorRate: errorRate,
        throughput: 2.5 + Math.random() * 2, // rps (mock)
        timeRange: "Last 1 hour",
      },
      errors: {
        totalErrors: Math.floor(Math.random() * 50) + 10,
        errorRate: errorRate,
        errorsByType: {
          "Network Timeout": Math.floor(Math.random() * 15) + 5,
          "Authentication Failed": Math.floor(Math.random() * 10) + 2,
          "Database Connection": Math.floor(Math.random() * 8) + 1,
          "Validation Error": Math.floor(Math.random() * 12) + 3,
          "Server Error": Math.floor(Math.random() * 6) + 1,
        },
        recentErrors: Array.from(
          { length: Math.floor(Math.random() * 10) + 5 },
          (_, i) => ({
            timestamp: new Date(now.getTime() - Math.random() * 3_600_000),
            type: ["Network Timeout", "Authentication Failed", "Database Connection"][
              Math.floor(Math.random() * 3)
            ],
            message: `Error message ${i + 1}`,
            correlationId: `corr_${Math.random().toString(36).slice(2, 11)}`,
          })
        ),
      },
      authentication: {
        totalAttempts: Math.floor(Math.random() * 200) + 100,
        successfulAttempts: Math.floor(authSuccessRate * 2),
        failedAttempts: Math.floor((100 - authSuccessRate) * 2),
        successRate: authSuccessRate,
        averageAuthTime: baseResponseTime * 0.8,
        recentFailures: Array.from(
          { length: Math.floor(Math.random() * 8) + 2 },
          (_, i) => ({
            timestamp: new Date(now.getTime() - Math.random() * 7_200_000),
            reason: [
              "Invalid credentials",
              "Account locked",
              "Session expired",
              "Network timeout",
            ][Math.floor(Math.random() * 4)],
            email: Math.random() > 0.5 ? `user${i}@example.com` : undefined,
          })
        ),
      },
      lastUpdated: now,
    };
  }, []);

  // --- Fetcher (mocked; replace with API/WSS fetch as needed)
  const fetchSystemHealth = useCallback(async () => {
    try {
      setIsLoading(true);

      // TODO: Replace with real fetch (REST/WSS); keep try/catch
      const health = generateMockSystemHealth();

      setSystemHealth(health);
      setLastUpdate(new Date());
      onHealthChange?.(health);

      connectivityLogger?.logConnectivity?.("debug", "System health check completed", {
        url: "/api/health",
        method: "GET",
        statusCode: 200,
      });
    } catch (error) {
      connectivityLogger?.logError?.(
        "Failed to fetch system health",
        error as Error,
        "connectivity"
      );
    } finally {
      setIsLoading(false);
    }
  }, [generateMockSystemHealth, onHealthChange]);

  // --- Auto-refresh interval
  useEffect(() => {
    fetchSystemHealth(); // prime immediately

    if (autoRefresh && defaultConfig.enableRealTimeUpdates) {
      const id = setInterval(fetchSystemHealth, defaultConfig.refreshInterval);
      return () => clearInterval(id);
    }
    return;
  }, [fetchSystemHealth, autoRefresh, defaultConfig.enableRealTimeUpdates, defaultConfig.refreshInterval]);

  const getOverallStatusBadge = (status: SystemHealth["overall"]): BadgeProps["variant"] => {
    switch (status) {
      case "healthy":
        return "default";
      case "degraded":
        return "secondary";
      case "critical":
        return "destructive";
      default:
        return "outline";
    }
  };

  const statusDot = (status: SystemHealth["overall"]) =>
    status === "healthy"
      ? "bg-green-500"
      : status === "degraded"
      ? "bg-yellow-500"
      : status === "critical"
      ? "bg-red-500"
      : "bg-gray-400";

  const LoadingView = (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardContent className="p-6 sm:p-4 md:p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <span className="ml-2 text-muted-foreground">Loading system health...</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const EmptyView = (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardContent className="p-6 sm:p-4 md:p-6">
          <div className="text-center text-muted-foreground">
            No health data available yet.
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <ErrorBoundary fallback={MonitoringDashboardFallback}>
      {isLoading && !systemHealth ? (
        LoadingView
      ) : !systemHealth ? (
        EmptyView
      ) : (
        <div className={`space-y-6 ${className}`}>
          {/* Overall System Status */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <span className="text-xl font-bold">System Health Dashboard</span>
                <div className="flex items-center space-x-3">
                  <Badge
                    variant={getOverallStatusBadge(systemHealth.overall)}
                    className="text-sm md:text-base lg:text-lg"
                  >
                    {systemHealth.overall.toUpperCase()}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchSystemHealth}
                    disabled={isLoading}
                    className="text-xs sm:text-sm md:text-base"
                    aria-label="Refresh system health"
                  >
                    {isLoading ? "Refreshing..." : "Refresh"}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setAutoRefresh((v) => !v)}
                    className={`text-xs ${autoRefresh ? "text-blue-600" : "text-muted-foreground"}`}
                    aria-pressed={autoRefresh}
                    aria-label="Toggle auto-refresh"
                  >
                    Auto-refresh {autoRefresh ? "ON" : "OFF"}
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${statusDot(systemHealth.overall)}`} />
                  <span className="text-lg font-semibold">
                    System is {systemHealth.overall}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Component Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ConnectionStatusIndicator
              status={systemHealth.components.backend}
              title="Backend API"
              showDetails={defaultConfig.showDetailedMetrics}
            />
            <ConnectionStatusIndicator
              status={systemHealth.components.database}
              title="Database"
              showDetails={defaultConfig.showDetailedMetrics}
            />
            <ConnectionStatusIndicator
              status={systemHealth.components.authentication}
              title="Authentication"
              showDetails={defaultConfig.showDetailedMetrics}
            />
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PerformanceMetricsDisplay
              metrics={systemHealth.performance}
              showTrends={defaultConfig.showDetailedMetrics}
            />
            <ErrorRateDisplay
              errorMetrics={systemHealth.errors}
              showRecentErrors={defaultConfig.showDetailedMetrics}
            />
          </div>

          {/* Authentication Metrics */}
          <AuthenticationMetricsDisplay
            metrics={systemHealth.authentication}
            showRecentFailures={defaultConfig.showDetailedMetrics}
          />
        </div>
      )}
    </ErrorBoundary>
  );
};

export default RealTimeMonitoringDashboard;
