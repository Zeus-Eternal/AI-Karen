"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Activity, Clock, TrendingUp, Zap } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { usePerformanceMonitor, checkPerformanceBudget } from "@/utils/performance-monitor";
import type {
  CustomMetric,
  PerformanceSummary,
  WebVitalsMetric,
} from "@/utils/performance-monitor";

export interface PerformanceDashboardProps {
  className?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

type BudgetRating = ReturnType<typeof checkPerformanceBudget>["rating"];

const STATUS_STYLES: Record<BudgetRating, string> = {
  good: "border-green-200 bg-green-50 text-green-900",
  "needs-improvement": "border-amber-200 bg-amber-50 text-amber-900",
  poor: "border-red-200 bg-red-50 text-red-900",
};

const WEB_VITALS: Array<{
  key: WebVitalsMetric["name"];
  label: string;
  unit: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}> = [
  { key: "LCP", label: "Largest Contentful Paint", unit: "ms", icon: Activity },
  { key: "FID", label: "First Input Delay", unit: "ms", icon: Clock },
  { key: "CLS", label: "Cumulative Layout Shift", unit: "", icon: TrendingUp },
  { key: "FCP", label: "First Contentful Paint", unit: "ms", icon: Zap },
];

const createBudgetCandidate = (name: WebVitalsMetric["name"], value: number): WebVitalsMetric => ({
  name,
  value,
  rating: "good",
  delta: 0,
  id: `${name}-latest`,
  navigationType: "navigate",
});

const formatMetricValue = (value: number | undefined, unit: string) => {
  if (value == null) return "N/A";
  if (!unit) {
    return value.toFixed(2);
  }
  return `${Math.round(value)}${unit}`;
};

const formatThreshold = (value: number, unit: string) =>
  unit ? `${Math.round(value)}${unit}` : value.toFixed(2);

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
            const metric = summary.webVitals[key];
            const value = metric?.value;
            const budget =
              value != null ? checkPerformanceBudget(createBudgetCandidate(key, value)) : null;
            const status: BudgetRating = budget?.rating ?? "good";
            const cardTone =
              value != null ? STATUS_STYLES[status] : "border-muted bg-muted/10 text-muted-foreground";

            return (
              <Card key={key} className={cn("border", cardTone)}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium uppercase tracking-wide">{key}</CardTitle>
                  <Icon className="h-4 w-4" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold">{formatMetricValue(value, unit)}</p>
                    <p className="text-sm text-muted-foreground">{label}</p>
                    <p className="text-xs text-muted-foreground">
                      {budget?.threshold
                        ? `Target ≤ ${formatThreshold(budget.threshold.good, unit)} · Alert ≥ ${formatThreshold(budget.threshold.poor, unit)}`
                        : "No performance budget configured."}
                    </p>
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
