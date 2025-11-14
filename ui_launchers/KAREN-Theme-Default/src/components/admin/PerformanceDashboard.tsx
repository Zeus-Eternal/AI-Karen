/**
 * Performance Dashboard Component (Production Hardened)
 *
 * Displays performance metrics and monitoring data for admin operations:
 * - Local in-memory performance report (client runtime)
 * - Server-side aggregated report via /api/admin/performance/report
 * - Cache statistics from AdminCacheManager
 *
 * Requirements: 7.3, 7.5
 */

"use client";

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { useRole } from "@/hooks/useRole";
import { AdminCacheManager } from "@/lib/cache/admin-cache";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Local/Server performance utilities (expected to exist in your codebase)
import {
  adminPerformanceMonitor,
  PerformanceReporter,
} from "@/lib/performance/admin-performance-monitor";

import type { PerformanceReport, CacheStats } from "@/types/admin";

export interface PerformanceDashboardProps {
  className?: string;
}

export type ExportFormat = "json" | "csv";

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={cn("animate-pulse", className)}>
      <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 rounded" />
        ))}
      </div>
      <div className="h-64 bg-gray-200 rounded" />
    </div>
  );
}

export function PerformanceDashboard({ className = "" }: PerformanceDashboardProps) {
  const { hasPermission } = useRole();

  const [report, setReport] = useState<PerformanceReport | null>(null);
  const [cacheStats, setCacheStats] = useState<Record<string, CacheStats>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const refreshIntervalMs = 30_000;
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const totalCachedItems = useMemo(() => {
    try {
      return Object.values(cacheStats).reduce((sum, stat) => sum + (stat?.size ?? 0), 0);
    } catch {
      return 0;
    }
  }, [cacheStats]);

  const fetchServerReport = useCallback(async (signal?: AbortSignal) => {
    const res = await fetch("/api/admin/performance/report?include_db_stats=true", {
      method: "GET",
      signal,
      headers: { "accept": "application/json" },
    });
    if (!res.ok) return null;
    const payload = await res.json();
    return payload?.success ? (payload.data as PerformanceReport) : null;
  }, []);

  const loadPerformanceData = useCallback(async () => {
    setError(null);
    try {
      // 1) Local instantaneous report
      const localReport = PerformanceReporter.generateReport();
      setReport(localReport);

      // 2) Cache stats
      const stats = AdminCacheManager.getAllStats();
      setCacheStats(stats);

      // 3) Attempt to merge server-side report (preferred if available)
      const controller = new AbortController();
      const serverData = await fetchServerReport(controller.signal);
      if (serverData) setReport(serverData);
    } catch (e: unknown) {
      const err = e instanceof Error ? e : new Error("Failed to load performance data");
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchServerReport]);

  // Initial load + auto refresh
  useEffect(() => {
    loadPerformanceData();
    if (autoRefresh) {
      if (refreshTimer.current) clearInterval(refreshTimer.current);
      refreshTimer.current = setInterval(loadPerformanceData, refreshIntervalMs);
    }
    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current);
    };
  }, [autoRefresh, loadPerformanceData]);

  const clearMetrics = useCallback(async () => {
    try {
      await fetch("/api/admin/performance/report", { method: "DELETE" });
    } catch {
      // server clear may not exist in some envs; proceed with local clears
    }
    try {
      adminPerformanceMonitor.clearAllMetrics?.();
    } catch {
      // ignore if not implemented in certain builds
    }
    try {
      AdminCacheManager.clearAll();
    } catch {
      // ignore
    }
    await loadPerformanceData();
  }, [loadPerformanceData]);

  const exportReport = useCallback(async (format: ExportFormat) => {
    try {
      const res = await fetch(`/api/admin/performance/report?format=${format}`, {
        method: "GET",
      });
      if (!res.ok) {
        setError(`Failed to export report (${format})`);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `performance-report.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to export report");
    }
  }, []);

  // RBAC Gate (render a friendly block but keep component stable)
  if (!hasPermission("system.config.read")) {
    return (
      <ErrorBoundary>
        <div className={cn("bg-red-50 border border-red-200 rounded-lg p-6", className)}>
          <p className="text-red-800">
            You don&apos;t have permission to view performance data.
          </p>
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className={cn("bg-white shadow rounded-lg", className)}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Performance Dashboard</h3>
              <p className="text-sm text-gray-500">
                {report ? `Last updated: ${new Date(report.timestamp).toLocaleString()}` : "No data available"}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <label className="flex items-center text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  aria-label="Toggle auto refresh"
                />
                Auto-refresh
              </label>
              <Button
                onClick={loadPerformanceData}
                className="px-3 py-1 text-sm md:text-base"
                aria-label="Refresh performance data"
              >
                Refresh
              </Button>
              <Button
                variant="destructive"
                onClick={clearMetrics}
                className="px-3 py-1 text-sm md:text-base"
                aria-label="Clear metrics"
              >
                Clear
              </Button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <Skeleton />
          ) : error ? (
            <div className="text-red-600 text-center">
              <p className="font-medium">Error loading performance data</p>
              <p className="text-sm mt-1">{error}</p>
              <Button
                onClick={loadPerformanceData}
                className="mt-3 px-4 py-2"
                aria-label="Retry loading performance data"
              >
                Retry
              </Button>
            </div>
          ) : report ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {report.summary.totalMetrics}
                  </div>
                  <div className="text-sm text-blue-800">Total Metrics</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {Math.round(report.summary.avgResponseTime)}ms
                  </div>
                  <div className="text-sm text-green-800">Avg Response Time</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {(report.database?.slowQueries ?? 0) + (report.api?.slowRequests ?? 0)}
                  </div>
                  <div className="text-sm text-yellow-800">Slow Operations</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{totalCachedItems}</div>
                  <div className="text-sm text-purple-800">Cached Items</div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Database Performance */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Database Performance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Query Count:</span>
                      <span className="font-medium">{report.database.queryCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Query Time:</span>
                      <span className="font-medium">{report.database.avgQueryTime.toFixed(2)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Slow Queries:</span>
                      <span
                        className={cn(
                          "font-medium",
                          report.database.slowQueries > 0 ? "text-red-600" : "text-green-600",
                        )}
                      >
                        {report.database.slowQueries}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>P95 Query Time:</span>
                      <span className="font-medium">{report.database.p95QueryTime.toFixed(2)}ms</span>
                    </div>
                  </div>
                </div>

                {/* API Performance */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">API Performance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Request Count:</span>
                      <span className="font-medium">{report.api.requestCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Response Time:</span>
                      <span className="font-medium">{report.api.avgResponseTime.toFixed(2)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Slow Requests:</span>
                      <span
                        className={cn(
                          "font-medium",
                          report.api.slowRequests > 0 ? "text-red-600" : "text-green-600",
                        )}
                      >
                        {report.api.slowRequests}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>P95 Response Time:</span>
                      <span className="font-medium">{report.api.p95ResponseTime.toFixed(2)}ms</span>
                    </div>
                  </div>
                </div>

                {/* Component Performance */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Component Performance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Render Count:</span>
                      <span className="font-medium">{report.components.renderCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Render Time:</span>
                      <span className="font-medium">{report.components.avgRenderTime.toFixed(2)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Slow Renders:</span>
                      <span
                        className={cn(
                          "font-medium",
                          report.components.slowRenders > 0 ? "text-red-600" : "text-green-600",
                        )}
                      >
                        {report.components.slowRenders}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>P95 Render Time:</span>
                      <span className="font-medium">{report.components.p95RenderTime.toFixed(2)}ms</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Cache Statistics */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Cache Statistics</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {Object.entries(cacheStats).map(([cacheType, stats]) => (
                    <div key={cacheType} className="bg-gray-50 p-3 rounded-lg">
                      <div className="text-sm font-medium text-gray-900 capitalize mb-2">
                        {cacheType.replace(/([A-Z])/g, " $1").trim()}
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div className="flex justify-between">
                          <span>Size:</span>
                          <span>
                            {stats.size}/{stats.maxSize}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Hit Rate:</span>
                          <span>{(stats.hitRate * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>TTL:</span>
                          <span>{(stats.ttl / 1000).toFixed(0)}s</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              {Array.isArray(report.recommendations) && report.recommendations.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Performance Recommendations</h4>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <ul className="space-y-2">
                      {report.recommendations.map((recommendation, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-yellow-600 mr-2">•</span>
                          <span className="text-yellow-800 text-sm">{recommendation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Export Options */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-500" />
                <div className="flex space-x-2">
                  <Button
                    onClick={() => exportReport("json")}
                    className="px-3 py-1 text-sm"
                    aria-label="Export report as JSON"
                  >
                    Export JSON
                  </Button>
                  <Button
                    onClick={() => exportReport("csv")}
                    className="px-3 py-1 text-sm"
                    aria-label="Export report as CSV"
                  >
                    Export CSV
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No performance data available</p>
              <Button
                onClick={loadPerformanceData}
                className="mt-3 px-4 py-2"
                aria-label="Load performance data"
              >
                Load Data
              </Button>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
