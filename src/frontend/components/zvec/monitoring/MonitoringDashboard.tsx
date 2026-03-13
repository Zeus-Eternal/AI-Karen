/**
 * MonitoringDashboard Component
 * 
 * Real-time monitoring dashboard for Zvec integration.
 * Displays RAG performance, sync metrics, concurrency, and system health.
 * Updates every 5 seconds with latest metrics.
 * 
 * @phase 4
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Database, 
  Users, 
  HardDrive, 
  Cpu, 
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react';

interface RAGMetrics {
  latency: {
    min: number;
    max: number;
    mean: number;
    p50: number;
    p95: number;
    p99: number;
  };
  total_queries: number;
  queries_per_second: number;
}

interface SyncMetrics {
  latency: {
    p50: number;
    p95: number;
    p99: number;
  };
  total_syncs: number;
  syncs_per_minute: number;
  vectors_synced: number;
  success_rate: number;
  failure_rate: number;
}

interface ConcurrencyMetrics {
  active_users: number;
  total_connections: number;
  conflicts_total: number;
}

interface SystemMetrics {
  memory: {
    rss_bytes: number;
    percent: number;
  };
  cpu: {
    percent: number;
  };
  uptime_seconds: number;
}

interface HealthStatus {
  overall_status: 'healthy' | 'warning' | 'error' | 'critical';
  active_alerts: Array<{
    severity: string;
    metric_name: string;
    message: string;
    current_value: number;
    threshold: number;
    timestamp: number;
  }>;
  alert_count: number;
  uptime_seconds: number;
}

interface DashboardData {
  rag: RAGMetrics;
  sync: SyncMetrics;
  concurrency: ConcurrencyMetrics;
  system: SystemMetrics;
  health: HealthStatus;
  timestamp: number;
}

interface MonitoringDashboardProps {
  refreshInterval?: number; // milliseconds
  className?: string;
}

export const MonitoringDashboard: React.FC<MonitoringDashboardProps> = ({
  refreshInterval = 5000,
  className = '',
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  /**
   * Fetch monitoring data from backend
   */
  const fetchMonitoringData = async () => {
    try {
      const response = await fetch('/api/zvec/monitoring/metrics');
      if (!response.ok) throw new Error('Failed to fetch monitoring data');
      
      const data = await response.json();
      setDashboardData(data);
      setLastUpdate(new Date());
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      setIsLoading(false);
    }
  };

  // Poll for updates
  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  /**
   * Get health status icon and color
   */
  const getHealthStatusBadge = () => {
    if (!dashboardData) return null;
    
    const { health } = dashboardData;
    switch (health.overall_status) {
      case 'healthy':
        return (
          <Badge className="bg-green-500 hover:bg-green-600">
            <CheckCircle className="h-3 w-3 mr-1" />
            Healthy
          </Badge>
        );
      case 'warning':
        return (
          <Badge className="bg-yellow-500 hover:bg-yellow-600">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Warning
          </Badge>
        );
      case 'error':
        return (
          <Badge className="bg-orange-500 hover:bg-orange-600">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Error
          </Badge>
        );
      case 'critical':
        return (
          <Badge className="bg-red-500 hover:bg-red-600">
            <XCircle className="h-3 w-3 mr-1" />
            Critical
          </Badge>
        );
    }
  };

  /**
   * Format bytes to human readable
   */
  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  /**
   * Format uptime to human readable
   */
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Activity className="h-6 w-6 animate-pulse text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading monitoring data...</span>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Failed to load monitoring data
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Zvec Monitoring Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {getHealthStatusBadge()}
          {dashboardData.health.alert_count > 0 && (
            <Badge variant="outline">
              {dashboardData.health.alert_count} Active Alerts
            </Badge>
          )}
        </div>
      </div>

      {/* Alerts Section */}
      {dashboardData.health.active_alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-orange-900">
              <AlertTriangle className="h-4 w-4 inline mr-2" />
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {dashboardData.health.active_alerts.map((alert, idx) => (
              <div key={idx} className="p-3 bg-white rounded border border-orange-200">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{alert.metric_name}</span>
                  <Badge variant="outline" className="text-xs">
                    {alert.severity}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">{alert.message}</p>
                <div className="text-xs text-orange-700 mt-1">
                  Current: {alert.current_value} / Threshold: {alert.threshold}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* RAG Performance */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAG Latency (p95)</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.rag.latency.p95.toFixed(1)} ms
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Mean: {dashboardData.rag.latency.mean.toFixed(1)} ms
            </p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs">
                <span>p99</span>
                <span>{dashboardData.rag.latency.p99.toFixed(1)} ms</span>
              </div>
              <Progress value={dashboardData.rag.latency.p95} max={100} className="h-1" />
            </div>
            <div className="mt-2 pt-2 border-t text-xs text-muted-foreground">
              {dashboardData.rag.queries_per_second.toFixed(1)} queries/sec
            </div>
          </CardContent>
        </Card>

        {/* Sync Performance */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sync Success Rate</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.sync.success_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {dashboardData.sync.vectors_synced.toLocaleString()} vectors synced
            </p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs">
                <span>Success Rate</span>
                <span>{dashboardData.sync.failure_rate.toFixed(1)}% failed</span>
              </div>
              <Progress 
                value={dashboardData.sync.success_rate} 
                className="h-1"
              />
            </div>
            <div className="mt-2 pt-2 border-t text-xs text-muted-foreground">
              {dashboardData.sync.syncs_per_minute.toFixed(1)} syncs/min
            </div>
          </CardContent>
        </Card>

        {/* Concurrency */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.concurrency.active_users}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {dashboardData.concurrency.total_connections} total connections
            </p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs">
                <span>Capacity</span>
                <span>{(dashboardData.concurrency.active_users / 1000 * 100).toFixed(0)}%</span>
              </div>
              <Progress 
                value={dashboardData.concurrency.active_users} 
                max={1000} 
                className="h-1"
              />
            </div>
            <div className="mt-2 pt-2 border-t text-xs text-muted-foreground">
              {dashboardData.concurrency.conflicts_total} conflicts
            </div>
          </CardContent>
        </Card>

        {/* System Health */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatUptime(dashboardData.system.uptime_seconds)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Uptime
            </p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1">
                  <HardDrive className="h-3 w-3" />
                  Memory
                </span>
                <span>{dashboardData.system.memory.percent.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1">
                  <Cpu className="h-3 w-3" />
                  CPU
                </span>
                <span>{dashboardData.system.cpu.percent.toFixed(1)}%</span>
              </div>
            </div>
            <div className="mt-2 pt-2 border-t text-xs text-muted-foreground">
              {formatBytes(dashboardData.system.memory.rss_bytes)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* RAG Metrics */}
            <div className="space-y-2">
              <h3 className="font-medium">RAG Performance</h3>
              <div className="space-y-1 text-muted-foreground">
                <div className="flex justify-between">
                  <span>Total Queries</span>
                  <span className="font-medium">{dashboardData.rag.total_queries.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Queries/Second</span>
                  <span className="font-medium">{dashboardData.rag.queries_per_second.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Latency (p50)</span>
                  <span className="font-medium">{dashboardData.rag.latency.p50.toFixed(2)} ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Latency (p99)</span>
                  <span className="font-medium">{dashboardData.rag.latency.p99.toFixed(2)} ms</span>
                </div>
              </div>
            </div>

            {/* Sync Metrics */}
            <div className="space-y-2">
              <h3 className="font-medium">Sync Performance</h3>
              <div className="space-y-1 text-muted-foreground">
                <div className="flex justify-between">
                  <span>Total Syncs</span>
                  <span className="font-medium">{dashboardData.sync.total_syncs.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Syncs/Minute</span>
                  <span className="font-medium">{dashboardData.sync.syncs_per_minute.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Failure Rate</span>
                  <span className="font-medium">{dashboardData.sync.failure_rate.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Sync Latency (p95)</span>
                  <span className="font-medium">{dashboardData.sync.latency.p95.toFixed(2)} ms</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Example Usage:
 * 
 * ```tsx
 * <MonitoringDashboard
 *   refreshInterval={5000}
 *   className="w-full"
 * />
 * ```
 */
