"use client";

import React, { useEffect, useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Clock, 
  Cpu, 
  HardDrive, 
  TrendingUp, 
  TrendingDown, 
  Zap,
  DollarSign,
  Shield,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  PerformanceMetrics, 
  Provider, 
  TimeRange, 
  UsePerformanceMetricsResult 
} from './types';
import { 
  useCurrentMetrics, 
  useProviders, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime, formatFileSize } from '@/lib/utils';

interface PerformanceMetricsDashboardProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
  defaultTimeRange?: TimeRange;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  icon?: React.ReactNode;
  status?: 'good' | 'warning' | 'critical';
  description?: string;
  className?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  icon,
  status = 'good',
  description,
  className,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'good': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4" />;
      case 'down': return <TrendingDown className="h-4 w-4" />;
      default: return null;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline space-x-2">
          <div className={cn("text-2xl font-bold", getStatusColor())}>
            {value}
          </div>
          {unit && (
            <span className="text-sm text-muted-foreground">{unit}</span>
          )}
        </div>
        {(trend || trendValue) && (
          <div className="flex items-center space-x-1 mt-1">
            {getTrendIcon()}
            <span className={cn("text-xs", getTrendColor())}>
              {trendValue && `${trendValue}%`}
            </span>
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};

export const PerformanceMetricsDashboard: React.FC<PerformanceMetricsDashboardProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
  defaultTimeRange,
}) => {
  const metrics = useCurrentMetrics();
  const providers = useProviders();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();

  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>(
    defaultTimeRange || {
      start: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
      end: new Date(),
    }
  );
  const [selectedMetric, setSelectedMetric] = useState<string>('latency');

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      actions.fetchMetrics(selectedProvider !== 'all' ? selectedProvider : undefined, timeRange);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [selectedProvider, timeRange, refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    actions.fetchMetrics(selectedProvider !== 'all' ? selectedProvider : undefined, timeRange);
    actions.fetchProviders();
  }, []);

  // Filter metrics based on selected provider
  const filteredMetrics = useMemo(() => {
    if (selectedProvider === 'all') return metrics;
    return metrics.filter(m => m.providerId === selectedProvider);
  }, [metrics, selectedProvider]);

  // Process chart data
  const chartData = useMemo(() => {
    return filteredMetrics.map(metric => ({
      timestamp: metric.timestamp,
      latency: metric.latency.mean,
      p95: metric.latency.p95,
      p99: metric.latency.p99,
      throughput: metric.throughput.requestsPerSecond,
      errorRate: metric.errors.errorRate,
      cpu: metric.resources.cpu,
      memory: metric.resources.memory,
      successRate: metric.reliability.successRate,
      costPerRequest: metric.cost.costPerRequest,
      userSatisfaction: metric.quality.userSatisfaction,
    })).sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }, [filteredMetrics]);

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    if (chartData.length === 0) return null;

    const latest = chartData[chartData.length - 1];
    const previous = chartData.length > 1 ? chartData[chartData.length - 2] : latest;

    if (!latest || !previous) return null;

    return {
      avgLatency: latest.latency,
      p95Latency: latest.p95,
      throughput: latest.throughput,
      errorRate: latest.errorRate,
      cpuUsage: latest.cpu,
      memoryUsage: latest.memory,
      successRate: latest.successRate,
      costPerRequest: latest.costPerRequest,
      userSatisfaction: latest.userSatisfaction,
      latencyTrend: latest.latency > previous.latency ? ('up' as const) : ('down' as const),
      throughputTrend: latest.throughput > previous.throughput ? ('up' as const) : ('down' as const),
      errorRateTrend: latest.errorRate > previous.errorRate ? ('up' as const) : ('down' as const),
    };
  }, [chartData]);

  const handleRefresh = () => {
    actions.fetchMetrics(selectedProvider !== 'all' ? selectedProvider : undefined, timeRange);
  };

  const handleExport = () => {
    actions.exportMetrics(selectedProvider !== 'all' ? selectedProvider : undefined, timeRange);
  };

  if (loading && !metrics.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading performance metrics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading metrics</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!summaryMetrics) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <p className="text-muted-foreground">No performance data available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {providers.map(provider => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedMetric} onValueChange={setSelectedMetric}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select metric" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="latency">Latency</SelectItem>
                <SelectItem value="throughput">Throughput</SelectItem>
                <SelectItem value="errors">Error Rate</SelectItem>
                <SelectItem value="resources">Resource Usage</SelectItem>
                <SelectItem value="reliability">Reliability</SelectItem>
                <SelectItem value="cost">Cost</SelectItem>
                <SelectItem value="quality">Quality</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              Export
            </Button>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Average Latency"
          value={summaryMetrics.avgLatency.toFixed(0)}
          unit="ms"
          trend={summaryMetrics.latencyTrend}
          icon={<Clock className="h-4 w-4 text-muted-foreground" />}
          status={summaryMetrics.avgLatency > 5000 ? 'critical' : summaryMetrics.avgLatency > 2000 ? 'warning' : 'good'}
          description="Lower is better"
        />

        <MetricCard
          title="Throughput"
          value={summaryMetrics.throughput.toFixed(1)}
          unit="req/s"
          trend={summaryMetrics.throughputTrend}
          icon={<Activity className="h-4 w-4 text-muted-foreground" />}
          status="good"
          description="Higher is better"
        />

        <MetricCard
          title="Error Rate"
          value={summaryMetrics.errorRate.toFixed(2)}
          unit="%"
          trend={summaryMetrics.errorRateTrend}
          icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
          status={summaryMetrics.errorRate > 5 ? 'critical' : summaryMetrics.errorRate > 2 ? 'warning' : 'good'}
          description="Lower is better"
        />

        <MetricCard
          title="Success Rate"
          value={summaryMetrics.successRate.toFixed(1)}
          unit="%"
          icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />}
          status={summaryMetrics.successRate < 95 ? 'critical' : summaryMetrics.successRate < 98 ? 'warning' : 'good'}
          description="Higher is better"
        />
      </div>

      {/* Charts */}
      <Tabs defaultValue="latency" value={selectedMetric} onValueChange={setSelectedMetric}>
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-7">
          <TabsTrigger value="latency">Latency</TabsTrigger>
          <TabsTrigger value="throughput">Throughput</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="reliability" className="hidden lg:flex">Reliability</TabsTrigger>
          <TabsTrigger value="cost" className="hidden lg:flex">Cost</TabsTrigger>
          <TabsTrigger value="quality" className="hidden lg:flex">Quality</TabsTrigger>
        </TabsList>

        <TabsContent value="latency" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Response Time Trends</CardTitle>
              <CardDescription>
                Latency metrics over the selected time period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(2)}ms`,
                      name === 'latency' ? 'Average' : name === 'p95' ? 'P95' : 'P99'
                    ]}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="latency" 
                    stroke="#8884d8" 
                    name="Average"
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="p95" 
                    stroke="#82ca9d" 
                    name="P95"
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="p99" 
                    stroke="#ffc658" 
                    name="P99"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="throughput" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Throughput Metrics</CardTitle>
              <CardDescription>
                Request throughput over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(1)} req/s`, 'Throughput']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="throughput" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Error Rate</CardTitle>
              <CardDescription>
                Error rate percentage over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Error Rate']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="errorRate" 
                    stroke="#ff7300" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>CPU Usage</CardTitle>
                <CardDescription>
                  CPU utilization percentage
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="cpu" 
                      stroke="#8884d8" 
                      fill="#8884d8" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Memory Usage</CardTitle>
                <CardDescription>
                  Memory utilization in MB
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                      formatter={(value: number) => [`${formatFileSize(value * 1024 * 1024)}`, 'Memory']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="memory" 
                      stroke="#82ca9d" 
                      fill="#82ca9d" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reliability" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Success Rate</CardTitle>
              <CardDescription>
                Request success rate percentage over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis domain={[90, 100]} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Success Rate']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="successRate" 
                    stroke="#00c49f" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cost" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost per Request</CardTitle>
              <CardDescription>
                Cost efficiency metrics over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`$${value.toFixed(4)}`, 'Cost/Request']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="costPerRequest" 
                    stroke="#ff7300" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Satisfaction</CardTitle>
              <CardDescription>
                Quality metrics and user satisfaction scores
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis domain={[0, 5]} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [`${value.toFixed(2)}`, 'Satisfaction']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="userSatisfaction" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {formatRelativeTime(lastUpdated)}
        </div>
      )}
    </div>
  );
};

export default PerformanceMetricsDashboard;