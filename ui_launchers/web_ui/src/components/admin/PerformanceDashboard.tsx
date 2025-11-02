/**
 * Performance Dashboard Component
 * 
 * Displays performance metrics and monitoring data for admin operations
 * including database queries, API responses, and component render times.
 * 
 * Requirements: 7.3, 7.5
 */
"use client";

import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { useRole } from '@/hooks/useRole';
import { AdminCacheManager } from '@/lib/cache/admin-cache';

  adminPerformanceMonitor,
import { } from '@/lib/performance/admin-performance-monitor';
import type { PerformanceReport, CacheStats } from '@/types/admin';
interface PerformanceDashboardProps {
  className?: string;
}
export function PerformanceDashboard({ className = '' }: PerformanceDashboardProps) {
  const { hasPermission } = useRole();
  const [report, setReport] = useState<PerformanceReport | null>(null);
  const [cacheStats, setCacheStats] = useState<Record<string, CacheStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  // Load performance data
  const loadPerformanceData = async () => {
    try {
      setError(null);
      // Get local performance report
      const localReport = PerformanceReporter.generateReport();
      setReport(localReport);
      // Get cache statistics
      const stats = AdminCacheManager.getAllStats();
      setCacheStats(stats);
      // Try to get server-side performance data
      try {
        const response = await fetch('/api/admin/performance/report?include_db_stats=true');
        if (response.ok) {
          const serverData = await response.json();
          if (serverData.success) {
            setReport(serverData.data);
          }
        }
      } catch (serverError) {
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };
  // Auto-refresh effect
  useEffect(() => {
    loadPerformanceData();
    if (autoRefresh) {
      const interval = setInterval(loadPerformanceData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);
  const clearMetrics = async () => {
    try {
      await fetch('/api/admin/performance/report', { method: 'DELETE' });
      adminPerformanceMonitor.clearAllMetrics();
      AdminCacheManager.clearAll();
      await loadPerformanceData();
    } catch (err) {
      setError('Failed to clear metrics');
    }
  };
  const exportReport = async (format: 'json' | 'csv') => {
    try {
      const response = await fetch(`/api/admin/performance/report?format=${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance-report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError('Failed to export report');
    }
  };
  if (!hasPermission('system.config.read')) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in PerformanceDashboard</div>}>
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 sm:p-4 md:p-6">
        <p className="text-red-800">You don't have permission to view performance data.</p>
      </div>
    );
  }
  if (loading) {
    return (
      <div className={`bg-white shadow rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 "></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className={`bg-white shadow rounded-lg p-6 ${className}`}>
        <div className="text-red-600 text-center">
          <p className="font-medium">Error loading performance data</p>
          <p className="text-sm mt-1 md:text-base lg:text-lg">{error}</p>
          <button
            onClick={loadPerformanceData}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
           aria-label="Button">
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Performance Dashboard</h3>
            <p className="text-sm text-gray-500 md:text-base lg:text-lg">
              {report ? `Last updated: ${new Date(report.timestamp).toLocaleString()}` : 'No data available'}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <label className="flex items-center text-sm text-gray-600 md:text-base lg:text-lg">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Auto-refresh
            </label>
            <button
              onClick={loadPerformanceData}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 md:text-base lg:text-lg"
             aria-label="Button">
            </button>
            <button
              onClick={clearMetrics}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 md:text-base lg:text-lg"
             aria-label="Button">
            </button>
          </div>
        </div>
      </div>
      <div className="p-6 sm:p-4 md:p-6">
        {report ? (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-blue-600">
                  {report.summary.totalMetrics}
                </div>
                <div className="text-sm text-blue-800 md:text-base lg:text-lg">Total Metrics</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-green-600">
                  {report.summary.avgResponseTime.toFixed(0)}ms
                </div>
                <div className="text-sm text-green-800 md:text-base lg:text-lg">Avg Response Time</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-yellow-600">
                  {report.database.slowQueries + report.api.slowRequests}
                </div>
                <div className="text-sm text-yellow-800 md:text-base lg:text-lg">Slow Operations</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg sm:p-4 md:p-6">
                <div className="text-2xl font-bold text-purple-600">
                  {Object.values(cacheStats).reduce((sum, stat) => sum + stat.size, 0)}
                </div>
                <div className="text-sm text-purple-800 md:text-base lg:text-lg">Cached Items</div>
              </div>
            </div>
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Database Performance */}
              <div className="bg-gray-50 p-4 rounded-lg sm:p-4 md:p-6">
                <h4 className="font-medium text-gray-900 mb-3">Database Performance</h4>
                <div className="space-y-2 text-sm md:text-base lg:text-lg">
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
                    <span className={`font-medium ${report.database.slowQueries > 0 ? 'text-red-600' : 'text-green-600'}`}>
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
              <div className="bg-gray-50 p-4 rounded-lg sm:p-4 md:p-6">
                <h4 className="font-medium text-gray-900 mb-3">API Performance</h4>
                <div className="space-y-2 text-sm md:text-base lg:text-lg">
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
                    <span className={`font-medium ${report.api.slowRequests > 0 ? 'text-red-600' : 'text-green-600'}`}>
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
              <div className="bg-gray-50 p-4 rounded-lg sm:p-4 md:p-6">
                <h4 className="font-medium text-gray-900 mb-3">Component Performance</h4>
                <div className="space-y-2 text-sm md:text-base lg:text-lg">
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
                    <span className={`font-medium ${report.components.slowRenders > 0 ? 'text-red-600' : 'text-green-600'}`}>
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
                  <div key={cacheType} className="bg-gray-50 p-3 rounded-lg sm:p-4 md:p-6">
                    <div className="text-sm font-medium text-gray-900 capitalize mb-2 md:text-base lg:text-lg">
                      {cacheType.replace(/([A-Z])/g, ' $1').trim()}
                    </div>
                    <div className="space-y-1 text-xs text-gray-600 sm:text-sm md:text-base">
                      <div className="flex justify-between">
                        <span>Size:</span>
                        <span>{stats.size}/{stats.maxSize}</span>
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
            {report.recommendations.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Performance Recommendations</h4>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 sm:p-4 md:p-6">
                  <ul className="space-y-2">
                    {report.recommendations.map((recommendation, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-yellow-600 mr-2">•</span>
                        <span className="text-yellow-800 text-sm md:text-base lg:text-lg">{recommendation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            {/* Export Options */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-500 md:text-base lg:text-lg">
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => exportReport('json')}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 md:text-base lg:text-lg"
                >
                </button>
                <button
                  onClick={() => exportReport('csv')}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 md:text-base lg:text-lg"
                >
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No performance data available</p>
            <button
              onClick={loadPerformanceData}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
             aria-label="Button">
            </button>
          </div>
        )}
      </div>
    </div>
    </ErrorBoundary>
  );
}
