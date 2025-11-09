"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Activity, Clock, TrendingUp, Zap } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  PERFORMANCE_THRESHOLDS,
  type CustomMetric,
  type PerformanceSummary,
  usePerformanceMonitor,
} from "@/utils/performance-monitor";

export interface PerformanceDashboardProps {
  className?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const WEB_VITALS: Array<{
  key: keyof PerformanceSummary["webVitals"];
  label: string;
  unit: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}> = [
  { key: "LCP", label: "Largest Contentful Paint", unit: "ms", icon: Activity },
  { key: "FID", label: "First Input Delay", unit: "ms", icon: Clock },
  { key: "CLS", label: "Cumulative Layout Shift", unit: "", icon: TrendingUp },
  { key: "FCP", label: "First Contentful Paint", unit: "ms", icon: Zap },
];

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  className,
  showDetails = true,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const { isMonitoring, metrics, getPerformanceSummary } = usePerformanceMonitor();
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);

  useEffect(() => {
    const update = () => setSummary(getPerformanceSummary());
    update();

    if (!autoRefresh) {
      return;
    }

    const interval = window.setInterval(update, refreshInterval);
    return () => window.clearInterval(interval);
  }, [autoRefresh, getPerformanceSummary, refreshInterval]);

  const recentMetrics = useMemo<CustomMetric[]>(() => {
    return Array.from(metrics.values())
      .flat()
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 5);
  }, [metrics]);

  if (!isMonitoring || !summary) {
    return (
      <Card className={cn("p-6", className)}>
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Activity className="h-4 w-4" />
          <span>Performance monitoring is not active.</span>
        </div>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      <section>
        <header className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Web vitals</h2>
          </div>
        </header>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {WEB_VITALS.map(({ key, label, unit, icon: Icon }) => {
            const value = summary.webVitals[key];
            const thresholds = PERFORMANCE_THRESHOLDS[key as keyof typeof PERFORMANCE_THRESHOLDS];
            let status: "good" | "needs-improvement" | "poor" = "good";
            if (value != null && thresholds) {
              if (value > thresholds.poor) status = "poor";
              else if (value > thresholds.good) status = "needs-improvement";
            }

            const colors: Record<typeof status, string> = {
              good: "border-green-200 bg-green-50 text-green-900",
              "needs-improvement": "border-amber-200 bg-amber-50 text-amber-900",
              poor: "border-red-200 bg-red-50 text-red-900",
            };

            return (
              <Card key={key} className={cn("border", colors[status])}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium uppercase tracking-wide">{key}</CardTitle>
                  <Icon className="h-4 w-4" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold">
                      {value != null ? `${Math.round(value)}${unit}` : "N/A"}
                    </p>
                    <p className="text-sm text-muted-foreground">{label}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {showDetails && (
        <section className="space-y-4">
          <div>
            <h3 className="text-md font-semibold">Custom metrics</h3>
            {summary.customMetrics && Object.keys(summary.customMetrics).length > 0 ? (
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {Object.entries(summary.customMetrics).map(([name, info]) => (
                  <Card key={name}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold">{name}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-1 text-sm text-muted-foreground">
                      <p>Average: {Math.round(info.avg)}ms</p>
                      <p>p95: {Math.round(info.p95)}ms</p>
                      <p>Samples: {info.count}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No custom metrics recorded yet.</p>
            )}
          </div>

          <Separator />

          <div>
            <h3 className="text-md font-semibold">Recent events</h3>
            {recentMetrics.length > 0 ? (
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                {recentMetrics.map((metric) => (
                  <li key={`${metric.name}-${metric.timestamp}`} className="flex justify-between">
                    <span>{metric.name}</span>
                    <span>{Math.round(metric.value)}ms</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No recent metrics captured.</p>
            )}
          </div>
        </section>
      )}
    </div>
  );
};

export default PerformanceDashboard;
