"use client";

import React from "react";
import { Activity, AlertTriangle, Cpu, Database, Gauge, HardDrive, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import type { PluginInfo, PluginMetrics as PluginMetricsType } from "@/types/plugins";

export interface PluginMetricsProps {
  plugin: PluginInfo;
  /** Override metrics when live data is fetched separately */
  metrics?: PluginMetricsType | null;
  /** Trigger a metrics refresh from the parent */
  onRefresh?: () => Promise<void> | void;
  /** External loading flag, falls back to internal state when undefined */
  isRefreshing?: boolean;
}

const numberFormatter = new Intl.NumberFormat();
const percentFormatter = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1, style: "percent" });

const formatNumber = (value?: number | null) => numberFormatter.format(value ?? 0);

const formatPercent = (value?: number | null) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return percentFormatter.format(0);
  }
  return percentFormatter.format(Math.min(Math.max(value, 0), 1));
};

const formatDuration = (seconds?: number | null) => {
  if (!seconds || Number.isNaN(seconds)) {
    return "—";
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 1) {
    return `${seconds.toFixed(0)}s`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 1) {
    return `${minutes}m ${Math.floor(seconds % 60)}s`;
  }
  const days = Math.floor(hours / 24);
  if (days < 1) {
    return `${hours}h ${minutes % 60}m`;
  }
  return `${days}d ${hours % 24}h`;
};

const healthConfig: Record<PluginMetricsType["health"]["status"], { label: string; badgeVariant: "secondary" | "outline" | "destructive" }> = {
  healthy: { label: "Healthy", badgeVariant: "secondary" },
  warning: { label: "Warning", badgeVariant: "outline" },
  critical: { label: "Critical", badgeVariant: "destructive" },
};

export const PluginMetrics: React.FC<PluginMetricsProps> = ({
  plugin,
  metrics: metricsOverride,
  onRefresh,
  isRefreshing,
}) => {
  const [internalRefreshing, setInternalRefreshing] = React.useState(false);
  const metrics = metricsOverride ?? plugin.metrics;
  const refreshInProgress = isRefreshing ?? internalRefreshing;

  const successRate = React.useMemo(() => {
    const errorRate = metrics?.performance?.errorRate ?? 0;
    const rate = Math.max(0, Math.min(1, 1 - errorRate));
    return rate;
  }, [metrics?.performance?.errorRate]);

  const lastExecution = metrics?.performance?.lastExecution ?? null;
  const lastHealthCheck = metrics?.health?.lastHealthCheck ?? null;

  const handleRefresh = React.useCallback(async () => {
    if (!onRefresh) {
      return;
    }

    if (isRefreshing === undefined) {
      setInternalRefreshing(true);
    }

    try {
      await onRefresh();
    } finally {
      if (isRefreshing === undefined) {
        setInternalRefreshing(false);
      }
    }
  }, [isRefreshing, onRefresh]);

  const healthStatus = metrics?.health?.status ?? "warning";
  const healthMeta = healthConfig[healthStatus];

  const issues = Array.isArray(metrics?.health?.issues) ? metrics?.health?.issues : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Operational metrics</h2>
          <p className="text-sm text-muted-foreground">
            Real-time health and performance indicators for {plugin.name}.
          </p>
        </div>
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshInProgress}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshInProgress ? "animate-spin" : ""}`} />
            {refreshInProgress ? "Refreshing" : "Refresh metrics"}
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="space-y-1 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total executions</CardTitle>
            <CardDescription className="text-2xl font-semibold text-foreground">
              {formatNumber(metrics?.performance?.totalExecutions)}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity className="h-4 w-4 text-primary" />
            Last run {lastExecution instanceof Date ? lastExecution.toLocaleString() : "never"}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-1 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Average execution time</CardTitle>
            <CardDescription className="text-2xl font-semibold text-foreground">
              {formatNumber(metrics?.performance?.averageExecutionTime)} ms
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Error rate {formatPercent(metrics?.performance?.errorRate)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-1 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Uptime</CardTitle>
            <CardDescription className="text-2xl font-semibold text-foreground">
              {formatDuration(metrics?.health?.uptime)}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Last health check {lastHealthCheck instanceof Date ? lastHealthCheck.toLocaleString() : "—"}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-1 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success rate</CardTitle>
            <CardDescription className="text-2xl font-semibold text-foreground">
              {formatPercent(successRate)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <Progress value={successRate * 100} />
            <div className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-primary" />
              <span>Consistent execution reliability</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Performance profile</CardTitle>
                <CardDescription>Execution performance metrics aggregated in real time.</CardDescription>
              </div>
              <Badge variant={healthMeta.badgeVariant}>{healthMeta.label}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Throughput</span>
                  <Activity className="h-4 w-4 text-primary" />
                </div>
                <p className="mt-2 text-2xl font-semibold">
                  {formatNumber(metrics?.performance?.totalExecutions)}
                </p>
                <p className="text-xs text-muted-foreground">Total invocations</p>
              </div>

              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Average latency</span>
                  <Gauge className="h-4 w-4 text-primary" />
                </div>
                <p className="mt-2 text-2xl font-semibold">
                  {formatNumber(metrics?.performance?.averageExecutionTime)} ms
                </p>
                <p className="text-xs text-muted-foreground">Moving average</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span>Error rate {formatPercent(metrics?.performance?.errorRate)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-500" />
                <span>
                  Last execution {lastExecution instanceof Date ? lastExecution.toLocaleString() : "no data"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resource utilization</CardTitle>
            <CardDescription>Current resource consumption reported by the runtime.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <ResourceUsage
                label="CPU"
                icon={<Cpu className="h-4 w-4 text-primary" />}
                value={metrics?.resources?.cpuUsage ?? 0}
              />
              <ResourceUsage
                label="Memory"
                icon={<Database className="h-4 w-4 text-primary" />}
                value={metrics?.resources?.memoryUsage ?? 0}
              />
              <ResourceUsage
                label="Disk"
                icon={<HardDrive className="h-4 w-4 text-primary" />}
                value={metrics?.resources?.diskUsage ?? 0}
              />
              <ResourceUsage
                label="Network"
                icon={<Activity className="h-4 w-4 text-primary" />}
                value={metrics?.resources?.networkUsage ?? 0}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Health insights</CardTitle>
          <CardDescription>Latest diagnostic signals and outstanding issues.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {issues.length === 0 ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4 text-emerald-500" />
              No open issues detected.
            </div>
          ) : (
            <ul className="space-y-3 text-sm text-muted-foreground">
              {issues.map((issue, index) => (
                <li key={`${issue}-${index}`} className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-500" />
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

interface ResourceUsageProps {
  label: string;
  icon: React.ReactNode;
  value: number;
}

const ResourceUsage: React.FC<ResourceUsageProps> = ({ label, icon, value }) => {
  const normalized = Number.isFinite(value) ? Math.min(Math.max(value, 0), 100) : 0;

  return (
    <div>
      <div className="flex items-center justify-between text-sm font-medium text-muted-foreground">
        <div className="flex items-center gap-2">
          {icon}
          <span>{label}</span>
        </div>
        <span>{normalized.toFixed(0)}%</span>
      </div>
      <Progress value={normalized} className="mt-2" />
    </div>
  );
};

export default PluginMetrics;
