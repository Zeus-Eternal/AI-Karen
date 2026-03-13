"use client";

import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  AlertTriangle,
  Clock,
  Download,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  TimeRange
} from './types';
import { 
  useAnalytics, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime } from '@/lib/utils';

interface RoutingAnalyticsProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
  defaultTimeRange?: TimeRange;
}

interface AnalyticsCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  icon?: React.ReactNode;
  description?: string;
  className?: string;
}

const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  icon,
  description,
  className,
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'stable': return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
      default: return null;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      case 'stable': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon}
        </div>
        {trend && (
          <div className="flex items-center space-x-1">
            {getTrendIcon()}
            <span className={cn("text-xs", getTrendColor())}>
              {trendValue && `${trendValue}%`}
            </span>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline space-x-2">
          <div className="text-2xl font-bold">{value}</div>
          {unit && (
            <span className="text-sm text-muted-foreground">{unit}</span>
          )}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};

export const RoutingAnalyticsComponent: React.FC<RoutingAnalyticsProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
}) => {
  const analytics = useAnalytics();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();
  const hasFetchedInitialData = useRef(false);

  const [selectedPeriod, setSelectedPeriod] = useState<string>('day');
  const [selectedMetric, setSelectedMetric] = useState<string>('overview');

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      actions.fetchAnalytics(selectedPeriod);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [selectedPeriod, refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    if (hasFetchedInitialData.current) {
      return;
    }

    hasFetchedInitialData.current = true;
    actions.fetchAnalytics(selectedPeriod);
  }, [actions, selectedPeriod]);

  // Process analytics data
  const currentAnalytics = useMemo(() => {
    return analytics.find(a => a.period === selectedPeriod) || analytics[0];
  }, [analytics, selectedPeriod]);

  // Process chart data
  const trendData = useMemo(() => {
    if (!currentAnalytics) return [];
    
    return currentAnalytics.performanceTrends.map(trend => ({
      metric: trend.metric,
      direction: trend.direction,
      change: trend.change,
      period: trend.period,
      significance: trend.significance,
      timestamp: new Date(trend.period),
    }));
  }, [currentAnalytics]);

  const anomalyData = useMemo(() => {
    if (!currentAnalytics) return [];
    
    return currentAnalytics.anomalies.map(anomaly => ({
      id: anomaly.id,
      type: anomaly.type,
      severity: anomaly.severity,
      description: anomaly.description,
      detectedAt: anomaly.detectedAt,
      affectedProviders: anomaly.affectedProviders.length,
      impact: anomaly.impact,
      status: anomaly.resolvedAt ? 'resolved' : 'active',
      resolved: !!anomaly.resolvedAt,
      resolution: anomaly.resolution,
    }));
  }, [currentAnalytics]);

  const providerUsageData = useMemo(() => {
    if (!currentAnalytics) return [];
    
    return Object.entries(currentAnalytics.providerUsage).map(([providerId, usage]) => ({
      name: providerId,
      usage,
      fill: providerId === 'primary' ? '#8884d8' : 
             providerId === 'fallback' ? '#82ca9d' : 
             providerId === 'specialized' ? '#ffc658' : '#ff7300',
    }));
  }, [currentAnalytics]);

  const strategyEffectivenessData = useMemo(() => {
    if (!currentAnalytics) return [];
    
    return Object.entries(currentAnalytics.strategyEffectiveness).map(([strategy, effectiveness]) => ({
      strategy,
      effectiveness,
      fill: strategy === 'performance-based' ? '#00c49f' : 
             strategy === 'cost-based' ? '#ff7300' : 
             strategy === 'reliability-based' ? '#8884d8' : '#82ca9d',
    }));
  }, [currentAnalytics]);

  const handleRefresh = () => {
    actions.fetchAnalytics(selectedPeriod);
  };

  const handleExport = () => {
    actions.exportAnalytics(selectedPeriod);
  };

  if (loading && !analytics.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading routing analytics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading routing analytics</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!currentAnalytics) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <p className="text-muted-foreground">No routing analytics data available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hour">Last Hour</SelectItem>
                <SelectItem value="day">Last 24 Hours</SelectItem>
                <SelectItem value="week">Last Week</SelectItem>
                <SelectItem value="month">Last Month</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedMetric} onValueChange={setSelectedMetric}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Select metric" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="overview">Overview</SelectItem>
                <SelectItem value="trends">Performance Trends</SelectItem>
                <SelectItem value="usage">Provider Usage</SelectItem>
                <SelectItem value="effectiveness">Strategy Effectiveness</SelectItem>
                <SelectItem value="anomalies">Anomalies</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      )}

      {/* Overview Cards */}
      <Tabs defaultValue="overview" value={selectedMetric} onValueChange={setSelectedMetric}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Performance Trends</TabsTrigger>
          <TabsTrigger value="usage">Provider Usage</TabsTrigger>
          <TabsTrigger value="effectiveness">Strategy Effectiveness</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <AnalyticsCard
              title="Total Requests"
              value={currentAnalytics.totalRequests.toLocaleString()}
              icon={<Activity className="h-4 w-4 text-muted-foreground" />}
              description="Requests in selected period"
            />

            <AnalyticsCard
              title="Successful Requests"
              value={currentAnalytics.successfulRequests.toLocaleString()}
              unit={`${((currentAnalytics.successfulRequests / currentAnalytics.totalRequests) * 100).toFixed(1)}%`}
              icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />}
              description="Successfully completed requests"
            />

            <AnalyticsCard
              title="Failed Requests"
              value={currentAnalytics.failedRequests.toLocaleString()}
              unit={`${((currentAnalytics.failedRequests / currentAnalytics.totalRequests) * 100).toFixed(1)}%`}
              icon={<XCircle className="h-4 w-4 text-muted-foreground" />}
              description="Failed or timed-out requests"
            />

            <AnalyticsCard
              title="Average Response Time"
              value={currentAnalytics.averageResponseTime.toFixed(0)}
              unit="ms"
              icon={<Clock className="h-4 w-4 text-muted-foreground" />}
              description="Average time to complete requests"
            />
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>
                Performance metric trends over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number, name: string) => [
                      value.toFixed(2),
                      name
                    ]}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="change" 
                    stroke="#8884d8" 
                    name="Change %"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Provider Usage Distribution</CardTitle>
                <CardDescription>
                  Number of requests handled by each provider
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={providerUsageData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      dataKey="usage"
                      label={(entry) => `${entry.name}: ${entry.usage}`}
                    >
                      {providerUsageData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Strategy Usage</CardTitle>
                <CardDescription>
                  Effectiveness of different routing strategies
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={strategyEffectivenessData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="strategy" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number, name: string) => [value.toFixed(1), name]}
                    />
                    <Legend />
                    <Bar dataKey="effectiveness" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="effectiveness" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Effectiveness Analysis</CardTitle>
              <CardDescription>
                Detailed breakdown of strategy performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(currentAnalytics.strategyEffectiveness).map(([strategy, effectiveness]) => (
                  <div key={strategy} className="flex items-center justify-between p-3 bg-muted/50 rounded">
                    <div>
                      <div className="font-medium">{strategy}</div>
                      <div className="text-sm text-muted-foreground capitalize">
                        {strategy.replace('-', ' ')} strategy
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">{effectiveness.toFixed(1)}%</div>
                      <div className="text-sm text-muted-foreground">effectiveness</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Detected Anomalies</CardTitle>
              <CardDescription>
                Performance anomalies and issues detected in the selected period
              </CardDescription>
            </CardHeader>
            <CardContent>
              {anomalyData.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-yellow-500" />
                  <p>No anomalies detected</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {anomalyData.map(anomaly => (
                    <div key={anomaly.id} className={cn(
                      "p-4 rounded-lg border",
                      anomaly.severity === 'critical' ? "border-red-200 bg-red-50" :
                      anomaly.severity === 'high' ? "border-orange-200 bg-orange-50" :
                      "border-yellow-200 bg-yellow-50"
                    )}>
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <Badge variant={anomaly.severity === 'critical' ? 'destructive' : 'outline'}>
                              {anomaly.severity}
                            </Badge>
                            <span className="text-sm font-medium">{anomaly.type}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatRelativeTime(anomaly.detectedAt)}
                          </div>
                        </div>
                        <p className="text-sm">{anomaly.description}</p>
                        <div className="text-xs text-muted-foreground">
                          Impact: {anomaly.impact} | Affected providers: {anomaly.affectedProviders}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={anomaly.resolved ? 'default' : 'outline'}>
                          {anomaly.resolved ? 'Resolved' : 'Active'}
                        </Badge>
                        {anomaly.resolution && (
                          <span className="text-xs text-muted-foreground ml-2">
                            {anomaly.resolution}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
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

export default RoutingAnalyticsComponent;
