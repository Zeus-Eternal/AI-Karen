// ui_launchers/KAREN-Theme-Default/src/components/monitoring/monitoring-status.tsx
"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { useMonitoring } from "@/hooks/use-monitoring";

import {
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";

interface MonitoringStatusProps {
  className?: string;
  /** When false, shows only the compact pill (no popover) */
  showDetails?: boolean;
}

export function MonitoringStatus({ className = "", showDetails = true }: MonitoringStatusProps) {
  const { health, performance, utils } = useMonitoring();

  const overallStatus = utils.getOverallStatus();
  const unacknowledgedAlerts = utils.getUnacknowledgedHealthAlerts();
  const criticalAlerts = utils.getCriticalHealthAlerts();

  const getStatusIcon = () => {
    switch (overallStatus) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "degraded":
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case "error":
      case "critical":
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (): "default" | "secondary" | "destructive" | "outline" => {
    switch (overallStatus) {
      case "healthy":
        return "default";
      case "degraded":
        return "secondary";
      case "error":
      case "critical":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getStatusText = () => {
    switch (overallStatus) {
      case "healthy":
        return "Healthy";
      case "degraded":
        return "Degraded";
      case "error":
        return "Error";
      case "critical":
        return "Critical";
      default:
        return "Unknown";
    }
  };

  // Compact display only (no popover)
  if (!showDetails) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {getStatusIcon()}
        <Badge variant={getStatusBadgeVariant()}>{getStatusText()}</Badge>
        {unacknowledgedAlerts.length > 0 && (
          <Badge variant="destructive" className="text-xs">
            {unacknowledgedAlerts.length}
          </Badge>
        )}
      </div>
    );
  }

  // Full popover with quick stats
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={`gap-2 ${className}`}
          aria-label="Show monitoring status details"
        >
          {getStatusIcon()}
          <Badge variant={getStatusBadgeVariant()}>{getStatusText()}</Badge>
          {unacknowledgedAlerts.length > 0 && (
            <Badge variant="destructive" className="text-xs">
              {unacknowledgedAlerts.length}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">API Status</h4>
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <Badge variant={getStatusBadgeVariant()}>{getStatusText()}</Badge>
            </div>
          </div>

          {/* Health / Performance */}
          {health?.metrics && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Error Rate</div>
                    <div className="text-muted-foreground">
                      {(health.metrics.errorRate * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Response Time</div>
                    <div className="text-muted-foreground">
                      {health.metrics.averageResponseTime.toFixed(0)}ms
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-sm">
                <div className="font-medium mb-1">Requests</div>
                <div className="text-muted-foreground">
                  {health.metrics.totalRequests} total, {health.metrics.failedRequests} failed
                </div>
              </div>

              {performance?.stats && (
                <div className="text-sm">
                  <div className="font-medium mb-1">Performance</div>
                  <div className="text-muted-foreground">
                    P95: {performance.stats.p95ResponseTime.toFixed(0)}ms, P99:{" "}
                    {performance.stats.p99ResponseTime.toFixed(0)}ms
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Critical alerts */}
          {criticalAlerts.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 font-medium text-red-600">
                <AlertTriangle className="h-4 w-4" />
                {criticalAlerts.length} Critical Alert{criticalAlerts.length !== 1 ? "s" : ""}
              </div>

              {criticalAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className="rounded border-l-2 border-red-500 bg-red-50 p-2 text-sm"
                >
                  <div className="font-medium">{alert.message}</div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}

              {criticalAlerts.length > 3 && (
                <div className="text-xs text-muted-foreground">
                  +{criticalAlerts.length - 3} more critical alerts
                </div>
              )}
            </div>
          )}

          {/* Non-critical, unacknowledged alerts */}
          {unacknowledgedAlerts.length > 0 && criticalAlerts.length === 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 font-medium text-yellow-600">
                <AlertTriangle className="h-4 w-4" />
                {unacknowledgedAlerts.length} Unacknowledged Alert
                {unacknowledgedAlerts.length !== 1 ? "s" : ""}
              </div>

              {unacknowledgedAlerts.slice(0, 2).map((alert) => (
                <div
                  key={alert.id}
                  className="rounded border-l-2 border-yellow-500 bg-yellow-50 p-2 text-sm"
                >
                  <div className="font-medium">{alert.message}</div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Footer */}
          {health?.metrics && (
            <div className="border-t pt-2 text-xs text-muted-foreground">
              Last updated: {new Date(health.metrics.lastHealthCheck).toLocaleTimeString()}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default MonitoringStatus;
