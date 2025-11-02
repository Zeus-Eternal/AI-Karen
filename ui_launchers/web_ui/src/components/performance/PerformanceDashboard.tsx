/**
 * Performance Dashboard Component
 * 
 * Displays real-time performance metrics and optimization recommendations
 * for HTTP connection pooling, caching, and database query optimization.
 * 
 * Requirements: 1.4, 4.4
 */
'use client';
import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { PerformanceUtils } from '../../lib/performance';
interface PerformanceMetrics {
  connectionPool: {
    totalConnections: number;
    activeConnections: number;
    connectionReuse: number;
    averageConnectionTime: number;
  };
  responseCache: {
    hitRate: number;
    totalEntries: number;
    memoryUsage: number;
    compressionRatio: number;
  };
  queryOptimizer: {
    totalQueries: number;
    cacheHits: number;
    averageQueryTime: number;
    slowQueries: number;
  };
  overall: {
    requestThroughput: number;
    averageResponseTime: number;
    errorRate: number;
    uptime: number;
  };
  timestamp: string;
  error?: string;
}
export function PerformanceDashboard() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const fetchMetrics = async () => {
    try {
      const metricsData = PerformanceUtils.getComprehensiveMetrics();
      const recommendationsData = PerformanceUtils.getPerformanceRecommendations();
      setMetrics(metricsData);
      setRecommendations(recommendationsData);
    } catch (error) {
      setMetrics({
        connectionPool: { totalConnections: 0, activeConnections: 0, connectionReuse: 0, averageConnectionTime: 0 },
        responseCache: { hitRate: 0, totalEntries: 0, memoryUsage: 0, compressionRatio: 0 },
        queryOptimizer: { totalQueries: 0, cacheHits: 0, averageQueryTime: 0, slowQueries: 0 },
        overall: { requestThroughput: 0, averageResponseTime: 0, errorRate: 0, uptime: 0 },
        timestamp: new Date().toISOString(),
        error: 'Failed to load metrics',
      });
    } finally {
      setIsLoading(false);
    }
  };
  const handleAutoOptimize = () => {
    PerformanceUtils.autoOptimizeAll();
    fetchMetrics(); // Refresh metrics after optimization
  };
  const handleClearCaches = () => {
    const success = PerformanceUtils.clearAllCaches();
    if (success) {
      fetchMetrics(); // Refresh metrics after clearing caches
    }
  };
  useEffect(() => {
    fetchMetrics();
  }, []);
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  };
  const getPerformanceStatus = (value: number, thresholds: { good: number; warning: number }): 'good' | 'warning' | 'error' => {
    if (value <= thresholds.good) return 'good';
    if (value <= thresholds.warning) return 'warning';
    return 'error';
  };
  const getStatusColor = (status: 'good' | 'warning' | 'error'): string => {
    switch (status) {
      case 'good': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
    }
  };
  if (isLoading) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in PerformanceDashboard</div>}>
      <div className="p-6 sm:p-4 md:p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  if (!metrics) {
    return (
      <div className="p-6 sm:p-4 md:p-6">
        <div className="text-center text-gray-500">
          Failed to load performance metrics
        </div>
      </div>
    );
  }
  return (
    <div className="p-6 space-y-6 sm:p-4 md:p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Performance Dashboard</h1>
          <p className="text-gray-600">
            Real-time performance metrics and optimization insights
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            variant="outline"
            onClick={() = aria-label="Button"> setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
          >
            {autoRefresh ? 'Auto-refresh On' : 'Auto-refresh Off'}
          </Button>
          <button variant="outline" onClick={fetchMetrics} aria-label="Button">
            Refresh
          </Button>
          <button variant="outline" onClick={handleAutoOptimize} aria-label="Button">
            Auto-optimize
          </Button>
          <button variant="outline" onClick={handleClearCaches} aria-label="Button">
            Clear Caches
          </Button>
        </div>
      </div>
      {/* Error Display */}
      {metrics.error && (
        <Card className="p-4 bg-red-50 border-red-200 sm:p-4 md:p-6">
          <div className="text-red-800">
            <strong>Error:</strong> {metrics.error}
          </div>
        </Card>
      )}
      {/* Overall Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 sm:p-4 md:p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Request Throughput</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.overall.requestThroughput.toFixed(1)}
              </p>
              <p className="text-xs text-gray-500 sm:text-sm md:text-base">requests/sec</p>
            </div>
            <Badge className={getStatusColor(getPerformanceStatus(metrics.overall.requestThroughput, { good: 10, warning: 5 }))}>
              {metrics.overall.requestThroughput > 10 ? 'Excellent' : 
               metrics.overall.requestThroughput > 5 ? 'Good' : 'Low'}
            </Badge>
          </div>
        </Card>
        <Card className="p-4 sm:p-4 md:p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.overall.averageResponseTime.toFixed(0)}
              </p>
              <p className="text-xs text-gray-500 sm:text-sm md:text-base">ms</p>
            </div>
            <Badge className={getStatusColor(getPerformanceStatus(metrics.overall.averageResponseTime, { good: 500, warning: 1000 }))}>
              {metrics.overall.averageResponseTime < 500 ? 'Fast' : 
               metrics.overall.averageResponseTime < 1000 ? 'Good' : 'Slow'}
            </Badge>
          </div>
        </Card>
        <Card className="p-4 sm:p-4 md:p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Error Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {(metrics.overall.errorRate * 100).toFixed(1)}
              </p>
              <p className="text-xs text-gray-500 sm:text-sm md:text-base">%</p>
            </div>
            <Badge className={getStatusColor(getPerformanceStatus(metrics.overall.errorRate * 100, { good: 1, warning: 5 }))}>
              {metrics.overall.errorRate < 0.01 ? 'Excellent' : 
               metrics.overall.errorRate < 0.05 ? 'Good' : 'High'}
            </Badge>
          </div>
        </Card>
        <Card className="p-4 sm:p-4 md:p-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Uptime</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatDuration(metrics.overall.uptime)}
              </p>
              <p className="text-xs text-gray-500 sm:text-sm md:text-base">duration</p>
            </div>
            <Badge className="bg-green-100 text-green-800">
              Running
            </Badge>
          </div>
        </Card>
      </div>
      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Connection Pool Metrics */}
        <Card className="p-6 sm:p-4 md:p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Pool</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Total Connections</span>
              <span className="font-medium">{metrics.connectionPool.totalConnections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Active Connections</span>
              <span className="font-medium">{metrics.connectionPool.activeConnections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Connection Reuse</span>
              <span className="font-medium">{metrics.connectionPool.connectionReuse}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Avg Connection Time</span>
              <span className="font-medium">{metrics.connectionPool.averageConnectionTime.toFixed(0)}ms</span>
            </div>
          </div>
        </Card>
        {/* Response Cache Metrics */}
        <Card className="p-6 sm:p-4 md:p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Response Cache</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Hit Rate</span>
              <span className="font-medium">{(metrics.responseCache.hitRate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Total Entries</span>
              <span className="font-medium">{metrics.responseCache.totalEntries}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Memory Usage</span>
              <span className="font-medium">{formatBytes(metrics.responseCache.memoryUsage)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Compression Ratio</span>
              <span className="font-medium">{(metrics.responseCache.compressionRatio * 100).toFixed(1)}%</span>
            </div>
          </div>
        </Card>
        {/* Query Optimizer Metrics */}
        <Card className="p-6 sm:p-4 md:p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Optimizer</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Total Queries</span>
              <span className="font-medium">{metrics.queryOptimizer.totalQueries}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Cache Hits</span>
              <span className="font-medium">{metrics.queryOptimizer.cacheHits}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Avg Query Time</span>
              <span className="font-medium">{metrics.queryOptimizer.averageQueryTime.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 md:text-base lg:text-lg">Slow Queries</span>
              <span className="font-medium">{metrics.queryOptimizer.slowQueries}</span>
            </div>
          </div>
        </Card>
      </div>
      {/* Performance Recommendations */}
      {recommendations.length > 0 && (
        <Card className="p-6 sm:p-4 md:p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Recommendations</h3>
          <div className="space-y-2">
            {recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0 sm:w-auto md:w-full"></div>
                <p className="text-sm text-gray-700 md:text-base lg:text-lg">{recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
      {/* Timestamp */}
      {metrics.timestamp && (
        <div className="text-xs text-gray-500 text-center sm:text-sm md:text-base">
          Last updated: {new Date(metrics.timestamp).toLocaleString()}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
