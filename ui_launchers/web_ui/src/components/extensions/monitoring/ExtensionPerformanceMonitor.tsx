/**
 * Extension Performance Monitor Component
 * 
 * Comprehensive performance monitoring dashboard for extensions including
 * real-time metrics, resource usage tracking, and performance analytics.
 */

'use client';

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { 
  useExtensionStatuses, 
  useExtensionPerformance, 
  useExtensionTaskMonitoring 
} from '../../../lib/extensions/hooks';
import { 
  Activity, 
  Zap, 
  Database, 
  Globe, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  BarChart3,
  PieChart,
  LineChart,
  Monitor,
  Cpu,
  HardDrive,
  Wifi,
  Timer,
  Target,
  Gauge,
  Settings,
  Download,
  Filter,
  Calendar,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
  threshold: {
    warning: number;
    critical: number;
  };
}

interface ResourceAlert {
  id: string;
  type: 'cpu' | 'memory' | 'network' | 'storage';
  severity: 'warning' | 'critical';
  message: string;
  timestamp: string;
  extensionId: string;
  extensionName: string;
  value: number;
  threshold: number;
}

interface ExtensionPerformanceMonitorProps {
  className?: string;
  extensionId?: string; // If provided, show metrics for specific extension
}

export default function ExtensionPerformanceMonitor({
  className,
  extensionId
}: ExtensionPerformanceMonitorProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');
  const [selectedMetric, setSelectedMetric] = useState<string>('cpu');
  const [alerts, setAlerts] = useState<ResourceAlert[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { statuses, loading } = useExtensionStatuses();
  const performanceData = useExtensionPerformance(extensionId);
  const taskData = useExtensionTaskMonitoring(extensionId);

  // Filter statuses if specific extension is selected
  const filteredStatuses = useMemo(() => {
    return extensionId 
      ? statuses.filter(s => s.id === extensionId)
      : statuses;
  }, [statuses, extensionId]);

  // Generate performance metrics
  const performanceMetrics = useMemo((): PerformanceMetric[] => {
    return [
      {
        name: 'CPU Usage',
        value: performanceData.avgCpu,
        unit: '%',
        trend: performanceData.avgCpu > 50 ? 'up' : performanceData.avgCpu < 20 ? 'down' : 'stable',
        status: performanceData.avgCpu > 80 ? 'critical' : performanceData.avgCpu > 60 ? 'warning' : 'good',
        threshold: { warning: 60, critical: 80 }
      },
      {
        name: 'Memory Usage',
        value: performanceData.avgMemory,
        unit: 'MB',
        trend: performanceData.avgMemory > 400 ? 'up' : performanceData.avgMemory < 200 ? 'down' : 'stable',
        status: performanceData.avgMemory > 800 ? 'critical' : performanceData.avgMemory > 500 ? 'warning' : 'good',
        threshold: { warning: 500, critical: 800 }
      },
      {
        name: 'Active Extensions',
        value: filteredStatuses.filter(s => s.status === 'active').length,
        unit: '',
        trend: 'stable',
        status: 'good',
        threshold: { warning: 10, critical: 15 }
      },
      {
        name: 'Background Tasks',
        value: taskData.totalActiveTasks,
        unit: '',
        trend: taskData.totalActiveTasks > 5 ? 'up' : 'stable',
        status: taskData.totalActiveTasks > 10 ? 'warning' : 'good',
        threshold: { warning: 8, critical: 15 }
      },
      {
        name: 'Error Rate',
        value: filteredStatuses.filter(s => s.status === 'error').length,
        unit: '',
        trend: filteredStatuses.filter(s => s.status === 'error').length > 0 ? 'up' : 'stable',
        status: filteredStatuses.filter(s => s.status === 'error').length > 2 ? 'critical' : 
               filteredStatuses.filter(s => s.status === 'error').length > 0 ? 'warning' : 'good',
        threshold: { warning: 1, critical: 3 }
      },
      {
        name: 'Response Time',
        value: 125, // Simulated average response time
        unit: 'ms',
        trend: 'stable',
        status: 'good',
        threshold: { warning: 500, critical: 1000 }
      }
    ];
  }, [performanceData, filteredStatuses, taskData]);

  // Generate sample alerts
  useEffect(() => {
    const sampleAlerts: ResourceAlert[] = [
      {
        id: '1',
        type: 'memory',
        severity: 'warning',
        message: 'Memory usage approaching limit',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        extensionId: 'analytics-dashboard',
        extensionName: 'Analytics Dashboard',
        value: 450,
        threshold: 500
      },
      {
        id: '2',
        type: 'cpu',
        severity: 'critical',
        message: 'CPU usage critically high',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        extensionId: 'automation-engine',
        extensionName: 'Automation Engine',
        value: 85,
        threshold: 80
      }
    ];
    setAlerts(sampleAlerts);
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // In real implementation, this would trigger data refresh
      console.log('Auto-refreshing performance data...');
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleExportMetrics = useCallback(() => {
    const metricsData = {
      timestamp: new Date().toISOString(),
      timeRange,
      metrics: performanceMetrics,
      extensions: filteredStatuses.map(s => ({
        id: s.id,
        name: s.name,
        status: s.status,
        resources: s.resources
      })),
      alerts
    };

    const blob = new Blob([JSON.stringify(metricsData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extension-performance-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [performanceMetrics, filteredStatuses, alerts, timeRange]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading performance monitor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Monitor</h1>
          <p className="text-gray-600 mt-1">
            {extensionId 
              ? `Monitor performance for ${filteredStatuses[0]?.name || extensionId}`
              : 'Monitor performance across all extensions'
            }
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          <Button
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 ${autoRefresh ? 'text-green-600' : 'text-gray-600'}`}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button
            variant="outline"
            onClick={handleExportMetrics}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              Performance Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map(alert => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                  <div className="flex items-center gap-3">
                    <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                      {alert.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-sm text-gray-600">
                        {alert.extensionName} • {alert.value}{alert.type === 'cpu' ? '%' : 'MB'} / {alert.threshold}{alert.type === 'cpu' ? '%' : 'MB'}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
              {alerts.length > 3 && (
                <p className="text-sm text-gray-600 text-center pt-2">
                  +{alerts.length - 3} more alerts
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {performanceMetrics.map((metric, index) => (
          <MetricCard key={index} metric={metric} />
        ))}
      </div>

      {/* Performance Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">
            <Monitor className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="resources">
            <Gauge className="h-4 w-4 mr-2" />
            Resources
          </TabsTrigger>
          <TabsTrigger value="extensions">
            <Activity className="h-4 w-4 mr-2" />
            Extensions
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <OverviewPanel 
            metrics={performanceMetrics} 
            statuses={filteredStatuses}
            taskData={taskData}
          />
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <ResourcesPanel 
            statuses={filteredStatuses}
            selectedMetric={selectedMetric}
            onMetricChange={setSelectedMetric}
          />
        </TabsContent>

        <TabsContent value="extensions" className="space-y-6">
          <ExtensionsPanel statuses={filteredStatuses} />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <AnalyticsPanel 
            metrics={performanceMetrics}
            timeRange={timeRange}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface MetricCardProps {
  metric: PerformanceMetric;
}

function MetricCard({ metric }: MetricCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      case 'stable':
        return <Minus className="h-4 w-4 text-gray-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{metric.name}</CardTitle>
        <Badge className={getStatusColor(metric.status)}>
          {metric.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">
              {metric.value.toFixed(metric.unit === '%' ? 1 : 0)}{metric.unit}
            </div>
            <div className="flex items-center mt-1">
              {getTrendIcon(metric.trend)}
              <span className="text-xs text-gray-500 ml-1">
                {metric.trend === 'stable' ? 'Stable' : 
                 metric.trend === 'up' ? 'Increasing' : 'Decreasing'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">
              Warning: {metric.threshold.warning}{metric.unit}
            </div>
            <div className="text-xs text-gray-500">
              Critical: {metric.threshold.critical}{metric.unit}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function OverviewPanel({ metrics, statuses, taskData }: any) {
  return (
    <div className="space-y-6">
      {/* System Health Summary */}
      <Card>
        <CardHeader>
          <CardTitle>System Health Summary</CardTitle>
          <CardDescription>Overall performance status across all extensions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {statuses.filter((s: any) => s.status === 'active').length}
              </div>
              <p className="text-sm text-gray-600">Active Extensions</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {taskData.totalActiveTasks}
              </div>
              <p className="text-sm text-gray-600">Active Tasks</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {statuses.filter((s: any) => s.status === 'inactive').length}
              </div>
              <p className="text-sm text-gray-600">Inactive Extensions</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {statuses.filter((s: any) => s.status === 'error').length}
              </div>
              <p className="text-sm text-gray-600">Error Extensions</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Trends Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
          <CardDescription>Resource usage trends over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <LineChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Performance trends chart would be rendered here</p>
              <p className="text-sm text-gray-500">Integration with charting library needed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ResourcesPanel({ statuses, selectedMetric, onMetricChange }: any) {
  const resourceMetrics = ['cpu', 'memory', 'network', 'storage'];

  return (
    <div className="space-y-6">
      {/* Resource Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Monitoring</CardTitle>
          <CardDescription>Monitor resource usage across extensions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            {resourceMetrics.map(metric => (
              <Button
                key={metric}
                variant={selectedMetric === metric ? 'default' : 'outline'}
                size="sm"
                onClick={() => onMetricChange(metric)}
                className="capitalize"
              >
                {metric === 'cpu' && <Cpu className="h-3 w-3 mr-1" />}
                {metric === 'memory' && <Database className="h-3 w-3 mr-1" />}
                {metric === 'network' && <Wifi className="h-3 w-3 mr-1" />}
                {metric === 'storage' && <HardDrive className="h-3 w-3 mr-1" />}
                {metric}
              </Button>
            ))}
          </div>

          {/* Resource Usage by Extension */}
          <div className="space-y-3">
            {statuses.map((status: any) => (
              <div key={status.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    status.status === 'active' ? 'bg-green-400' :
                    status.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                  }`}></div>
                  <div>
                    <h4 className="font-medium">{status.name}</h4>
                    <p className="text-sm text-gray-600">ID: {status.id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">
                    {selectedMetric === 'cpu' && `${status.resources.cpu.toFixed(1)}%`}
                    {selectedMetric === 'memory' && `${Math.round(status.resources.memory)}MB`}
                    {selectedMetric === 'network' && `${status.resources.network.toFixed(1)} KB/s`}
                    {selectedMetric === 'storage' && `${Math.round(status.resources.storage)}MB`}
                  </div>
                  <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className={`h-2 rounded-full ${
                        selectedMetric === 'cpu' && status.resources.cpu > 80 ? 'bg-red-500' :
                        selectedMetric === 'cpu' && status.resources.cpu > 60 ? 'bg-yellow-500' :
                        selectedMetric === 'memory' && status.resources.memory > 500 ? 'bg-red-500' :
                        selectedMetric === 'memory' && status.resources.memory > 300 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ 
                        width: `${Math.min(100, 
                          selectedMetric === 'cpu' ? status.resources.cpu :
                          selectedMetric === 'memory' ? (status.resources.memory / 10) :
                          selectedMetric === 'network' ? (status.resources.network / 10) :
                          (status.resources.storage / 10)
                        )}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ExtensionsPanel({ statuses }: any) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Extension Performance Breakdown</CardTitle>
          <CardDescription>Detailed performance metrics for each extension</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Extension</th>
                  <th className="text-center py-2">Status</th>
                  <th className="text-right py-2">CPU</th>
                  <th className="text-right py-2">Memory</th>
                  <th className="text-right py-2">Network</th>
                  <th className="text-right py-2">Tasks</th>
                  <th className="text-center py-2">Health</th>
                </tr>
              </thead>
              <tbody>
                {statuses.map((status: any) => (
                  <tr key={status.id} className="border-b border-gray-100">
                    <td className="py-2">
                      <div>
                        <div className="font-medium">{status.name}</div>
                        <div className="text-xs text-gray-500">{status.id}</div>
                      </div>
                    </td>
                    <td className="text-center py-2">
                      <Badge variant={
                        status.status === 'active' ? 'default' :
                        status.status === 'error' ? 'destructive' : 'secondary'
                      }>
                        {status.status}
                      </Badge>
                    </td>
                    <td className="text-right py-2">{status.resources.cpu.toFixed(1)}%</td>
                    <td className="text-right py-2">{Math.round(status.resources.memory)}MB</td>
                    <td className="text-right py-2">{status.resources.network.toFixed(1)} KB/s</td>
                    <td className="text-right py-2">
                      {status.backgroundTasks ? 
                        `${status.backgroundTasks.active}/${status.backgroundTasks.total}` : 
                        '0/0'
                      }
                    </td>
                    <td className="text-center py-2">
                      {status.health.status === 'healthy' ? (
                        <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AnalyticsPanel({ metrics, timeRange }: any) {
  return (
    <div className="space-y-6">
      {/* Performance Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Resource Distribution</CardTitle>
            <CardDescription>How resources are distributed across extensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Resource distribution chart</p>
                <p className="text-sm text-gray-500">Pie chart would be rendered here</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
            <CardDescription>Performance metrics over {timeRange}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Performance trends chart</p>
                <p className="text-sm text-gray-500">Bar chart would be rendered here</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
          <CardDescription>AI-powered insights and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <Target className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">Optimization Opportunity</h4>
                <p className="text-sm text-blue-800">
                  The Analytics Dashboard extension is using 45% more memory than average. 
                  Consider reviewing data caching strategies.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900">Good Performance</h4>
                <p className="text-sm text-green-800">
                  CPU usage is well within normal ranges across all extensions. 
                  Current load balancing is effective.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-900">Resource Alert</h4>
                <p className="text-sm text-yellow-800">
                  Network usage has increased by 30% in the last hour. 
                  Monitor for potential API rate limiting issues.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}