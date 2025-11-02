/**
 * Extension Monitoring Dashboard Component
 * 
 * React component for displaying extension authentication metrics,
 * service health monitoring, and performance data.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Server,
  Shield,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';

interface AuthMetrics {
  total_requests: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  token_refresh_count: number;
  average_response_time: number;
  last_updated: string;
}

interface ServiceHealthMetrics {
  healthy_services: number;
  total_services: number;
  health_percentage: number;
  services: Record<string, {
    status: string;
    error_count: number;
    average_response_time: number;
    last_check: string;
  }>;
  last_updated: string;
}

interface ApiPerformanceMetrics {
  total_requests: number;
  error_count: number;
  error_rate: number;
  average_response_time: number;
  percentiles: {
    p50: number;
    p95: number;
    p99: number;
  };
  endpoints: Record<string, {
    request_count: number;
    error_count: number;
    error_rate: number;
    average_response_time: number;
    last_request: string | null;
  }>;
  last_updated: string;
}

interface ActiveAlert {
  id: string;
  name: string;
  description: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  triggered_at: string;
  trigger_count: number;
}

interface DashboardData {
  timestamp: string;
  monitoring_active: boolean;
  authentication: AuthMetrics;
  service_health: ServiceHealthMetrics;
  api_performance: ApiPerformanceMetrics;
  active_alerts: ActiveAlert[];
  alert_history: any[];
}

const ExtensionMonitoringDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await fetch('/api/monitoring/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchDashboardData]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'destructive';
      case 'error':
        return 'destructive';
      case 'warning':
        return 'default';
      case 'info':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'error':
        return <XCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'info':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading monitoring data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Dashboard</AlertTitle>
        <AlertDescription>
          {error}
          <Button
            variant="outline"
            size="sm"
            className="ml-2"
            onClick={fetchDashboardData}
          >
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>No Data Available</AlertTitle>
        <AlertDescription>
          No monitoring data is currently available.
        </AlertDescription>
      </Alert>
    );
  }

  const { authentication, service_health, api_performance, active_alerts } = dashboardData;

  // Prepare chart data
  const authChartData = [
    { name: 'Success', value: authentication.success_count, color: '#10b981' },
    { name: 'Failure', value: authentication.failure_count, color: '#ef4444' },
  ];

  const serviceStatusData = Object.entries(service_health.services).map(([name, service]) => ({
    name,
    status: service.status,
    response_time: service.average_response_time,
    error_count: service.error_count,
  }));

  const endpointPerformanceData = Object.entries(api_performance.endpoints)
    .slice(0, 10) // Show top 10 endpoints
    .map(([endpoint, data]) => ({
      endpoint: endpoint.length > 30 ? endpoint.substring(0, 30) + '...' : endpoint,
      requests: data.request_count,
      errors: data.error_count,
      avg_time: data.average_response_time,
    }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Extension Monitoring Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor extension authentication, service health, and performance
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={dashboardData.monitoring_active ? 'default' : 'secondary'}>
            {dashboardData.monitoring_active ? 'Active' : 'Inactive'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDashboardData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            Auto Refresh
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {active_alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-yellow-500" />
              Active Alerts ({active_alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {active_alerts.map((alert) => (
                <Alert key={alert.id} variant={getSeverityColor(alert.severity) as any}>
                  <div className="flex items-center">
                    {getSeverityIcon(alert.severity)}
                    <div className="ml-2 flex-1">
                      <AlertTitle>{alert.name}</AlertTitle>
                      <AlertDescription>
                        {alert.description}
                        <div className="text-xs text-muted-foreground mt-1">
                          Triggered: {formatTimestamp(alert.triggered_at)} 
                          {alert.trigger_count > 1 && ` (${alert.trigger_count} times)`}
                        </div>
                      </AlertDescription>
                    </div>
                  </div>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auth Success Rate</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{authentication.success_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {authentication.total_requests} total requests
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Service Health</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{service_health.health_percentage.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {service_health.healthy_services}/{service_health.total_services} services healthy
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Error Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{api_performance.error_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {api_performance.total_requests} total requests
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(api_performance.average_response_time * 1000).toFixed(0)}ms
            </div>
            <p className="text-xs text-muted-foreground">
              P95: {(api_performance.percentiles.p95 * 1000).toFixed(0)}ms
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics Tabs */}
      <Tabs defaultValue="authentication" className="space-y-4">
        <TabsList>
          <TabsTrigger value="authentication">Authentication</TabsTrigger>
          <TabsTrigger value="health">Service Health</TabsTrigger>
          <TabsTrigger value="performance">API Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="authentication" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Authentication Success/Failure</CardTitle>
                <CardDescription>
                  Distribution of authentication attempts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={authChartData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, value, percent }) => 
                        `${name}: ${value} (${(percent * 100).toFixed(1)}%)`
                      }
                    >
                      {authChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Authentication Metrics</CardTitle>
                <CardDescription>
                  Detailed authentication statistics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Requests:</span>
                    <span className="font-medium">{authentication.total_requests}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Success Count:</span>
                    <span className="font-medium text-green-600">{authentication.success_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failure Count:</span>
                    <span className="font-medium text-red-600">{authentication.failure_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Token Refreshes:</span>
                    <span className="font-medium">{authentication.token_refresh_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Response Time:</span>
                    <span className="font-medium">
                      {(authentication.average_response_time * 1000).toFixed(0)}ms
                    </span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Last Updated:</span>
                    <span>{formatTimestamp(authentication.last_updated)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Status</CardTitle>
              <CardDescription>
                Current status of all monitored services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {serviceStatusData.map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        service.status === 'healthy' ? 'bg-green-500' :
                        service.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <span className="font-medium">{service.name}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>Errors: {service.error_count}</span>
                      <span>Avg: {(service.response_time * 1000).toFixed(0)}ms</span>
                      <Badge variant={
                        service.status === 'healthy' ? 'default' :
                        service.status === 'degraded' ? 'secondary' : 'destructive'
                      }>
                        {service.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Endpoint Performance</CardTitle>
                <CardDescription>
                  Request count and response times by endpoint
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={endpointPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="endpoint" 
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="requests" fill="#3b82f6" name="Requests" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time Percentiles</CardTitle>
                <CardDescription>
                  API response time distribution
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>P50 (Median):</span>
                    <span className="font-medium">
                      {(api_performance.percentiles.p50 * 1000).toFixed(0)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>P95:</span>
                    <span className="font-medium">
                      {(api_performance.percentiles.p95 * 1000).toFixed(0)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>P99:</span>
                    <span className="font-medium">
                      {(api_performance.percentiles.p99 * 1000).toFixed(0)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average:</span>
                    <span className="font-medium">
                      {(api_performance.average_response_time * 1000).toFixed(0)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Error Rate:</span>
                    <span className={`font-medium ${
                      api_performance.error_rate > 5 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {api_performance.error_rate.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExtensionMonitoringDashboard;