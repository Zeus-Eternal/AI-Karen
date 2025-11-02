/**
 * Model Metrics Dashboard
 * Usage statistics, cost analysis, and performance trends
 */
import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Clock, 
  Activity, 
  Users,
  AlertTriangle,
  CheckCircle,
  Zap,
  Target,
  RefreshCw,
  Download,
  Calendar,
  Filter,
  Eye,
  Settings
} from 'lucide-react';
import { BudgetAlert, ModelWarmupConfig } from '@/types/providers';
import { useToast } from '@/hooks/use-toast';
interface ModelMetricsDashboardProps {
  className?: string;
}
interface ModelMetrics {
  modelId: string;
  modelName: string;
  provider: string;
  timeRange: string;
  usage: {
    totalRequests: number;
    uniqueUsers: number;
    averageRequestsPerUser: number;
    requestsOverTime: DataPoint[];
    usageByProvider: Record<string, number>;
    topUsers: UserUsage[];
  };
  performance: {
    averageLatency: number;
    p95Latency: number;
    p99Latency: number;
    throughput: number;
    errorRate: number;
    latencyTrend: DataPoint[];
    throughputTrend: DataPoint[];
    errorTrend: DataPoint[];
  };
  costs: {
    totalCost: number;
    costPerRequest: number;
    costPerUser: number;
    costTrend: DataPoint[];
    costByProvider: Record<string, number>;
    projectedMonthlyCost: number;
    budgetUtilization: number;
  };
  warmup: ModelWarmupConfig;
  benchmarks: BenchmarkResult[];
}
interface DataPoint {
  timestamp: Date;
  value: number;
  label?: string;
}
interface UserUsage {
  userId: string;
  username: string;
  requestCount: number;
  cost: number;
  lastUsed: Date;
}
interface BenchmarkResult {
  id: string;
  name: string;
  score: number;
  percentile: number;
  date: Date;
  status: 'completed' | 'running' | 'failed';
}
const ModelMetricsDashboard: React.FC<ModelMetricsDashboardProps> = ({ className }) => {
  const { toast } = useToast();
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d' | '90d'>('7d');
  const [loading, setLoading] = useState(true);
  const [budgetAlerts, setBudgetAlerts] = useState<BudgetAlert[]>([]);
  const [runningBenchmarks, setRunningBenchmarks] = useState<Set<string>>(new Set());
  useEffect(() => {
    loadMetrics();
    loadBudgetAlerts();
  }, [selectedModel, timeRange]);
  const loadMetrics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        timeRange,
        ...(selectedModel !== 'all' && { modelId: selectedModel })
      });
      const response = await fetch(`/api/models/metrics?${params}`);
      if (!response.ok) throw new Error('Failed to load metrics');
      const data = await response.json();
      setMetrics(data.metrics || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load model metrics',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };
  const loadBudgetAlerts = async () => {
    try {
      const response = await fetch('/api/models/budget-alerts');
      if (!response.ok) throw new Error('Failed to load budget alerts');
      const data = await response.json();
      setBudgetAlerts(data.alerts || []);
    } catch (error) {
    }
  };
  const runBenchmark = async (modelId: string, benchmarkSuite: string) => {
    setRunningBenchmarks(prev => new Set([...prev, `${modelId}-${benchmarkSuite}`]));
    try {
      const response = await fetch('/api/models/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelId, benchmarkSuite })
      });
      if (!response.ok) throw new Error('Failed to start benchmark');
      toast({
        title: 'Benchmark Started',
        description: `Running ${benchmarkSuite} benchmark for model`,
      });
      // Refresh metrics after a delay to show updated benchmark results
      setTimeout(() => {
        loadMetrics();
        setRunningBenchmarks(prev => {
          const newSet = new Set(prev);
          newSet.delete(`${modelId}-${benchmarkSuite}`);
          return newSet;
        });
      }, 5000);
    } catch (error) {
      toast({
        title: 'Benchmark Error',
        description: 'Failed to start benchmark',
        variant: 'destructive'
      });
      setRunningBenchmarks(prev => {
        const newSet = new Set(prev);
        newSet.delete(`${modelId}-${benchmarkSuite}`);
        return newSet;
      });
    }
  };
  const updateWarmupConfig = async (modelId: string, config: Partial<ModelWarmupConfig>) => {
    try {
      const response = await fetch(`/api/models/${modelId}/warmup`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) throw new Error('Failed to update warmup config');
      toast({
        title: 'Warmup Updated',
        description: 'Model warmup configuration has been updated',
      });
      loadMetrics();
    } catch (error) {
      toast({
        title: 'Update Error',
        description: 'Failed to update warmup configuration',
        variant: 'destructive'
      });
    }
  };
  const exportMetrics = () => {
    const data = {
      metrics,
      timeRange,
      selectedModel,
      exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model-metrics-${timeRange}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast({
      title: 'Metrics Exported',
      description: 'Model metrics data has been exported'
    });
  };
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(amount);
  };
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };
  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />;
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />;
    return <Activity className="w-4 h-4 text-gray-600 sm:w-auto md:w-full" />;
  };
  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600 sm:w-auto md:w-full" />;
      default:
        return <CheckCircle className="w-4 h-4 text-blue-600 sm:w-auto md:w-full" />;
    }
  };
  const aggregatedMetrics = metrics.length > 0 ? {
    totalRequests: metrics.reduce((sum, m) => sum + m.usage.totalRequests, 0),
    totalCost: metrics.reduce((sum, m) => sum + m.costs.totalCost, 0),
    averageLatency: metrics.reduce((sum, m) => sum + m.performance.averageLatency, 0) / metrics.length,
    averageErrorRate: metrics.reduce((sum, m) => sum + m.performance.errorRate, 0) / metrics.length,
    totalUsers: new Set(metrics.flatMap(m => m.usage.topUsers.map(u => u.userId))).size
  } : null;
  if (loading) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in ModelMetricsDashboard</div>}>
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <BarChart3 className="w-8 h-8 animate-pulse mx-auto text-blue-500 sm:w-auto md:w-full" />
            <div>Loading model metrics...</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 sm:w-auto md:w-full" />
                Model Performance & Cost Dashboard
              </CardTitle>
              <CardDescription>
                Monitor usage, performance, and costs across all models
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <select value={selectedModel} onValueChange={setSelectedModel} aria-label="Select option">
                <selectTrigger className="w-48 sm:w-auto md:w-full" aria-label="Select option">
                  <selectValue placeholder="Select model" />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="all" aria-label="Select option">All Models</SelectItem>
                  {metrics.map(metric => (
                    <selectItem key={metric.modelId} value={metric.modelId} aria-label="Select option">
                      {metric.modelName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <select value={timeRange} onValueChange={(value: any) = aria-label="Select option"> setTimeRange(value)}>
                <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="1h" aria-label="Select option">Last Hour</SelectItem>
                  <selectItem value="24h" aria-label="Select option">Last 24h</SelectItem>
                  <selectItem value="7d" aria-label="Select option">Last 7 days</SelectItem>
                  <selectItem value="30d" aria-label="Select option">Last 30 days</SelectItem>
                  <selectItem value="90d" aria-label="Select option">Last 90 days</SelectItem>
                </SelectContent>
              </Select>
              <button variant="outline" onClick={exportMetrics} aria-label="Button">
                <Download className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                Export
              </Button>
              <button variant="outline" onClick={loadMetrics} aria-label="Button">
                <RefreshCw className="w-4 h-4 sm:w-auto md:w-full" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Budget Alerts */}
      {budgetAlerts.length > 0 && (
        <div className="space-y-3">
          {budgetAlerts.slice(0, 3).map(alert => (
            <Alert key={alert.id} className={`border-l-4 ${
              alert.severity === 'critical' ? 'border-l-red-500' : 
              alert.severity === 'warning' ? 'border-l-yellow-500' : 
              'border-l-blue-500'
            }`}>
              <div className="flex items-start gap-3">
                {getAlertIcon(alert.severity)}
                <div className="flex-1">
                  <div className="font-medium">{alert.title}</div>
                  <AlertDescription className="mt-1">
                    {alert.message}
                  </AlertDescription>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-600 md:text-base lg:text-lg">
                    <span>Current: {formatCurrency(alert.currentSpend)}</span>
                    <span>Threshold: {formatCurrency(alert.threshold)}</span>
                    {alert.projectedSpend && (
                      <span>Projected: {formatCurrency(alert.projectedSpend)}</span>
                    )}
                  </div>
                </div>
                <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                  {alert.severity}
                </Badge>
              </div>
            </Alert>
          ))}
        </div>
      )}
      {/* Overview Metrics */}
      {aggregatedMetrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Requests</p>
                  <p className="text-2xl font-bold">{formatNumber(aggregatedMetrics.totalRequests)}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(aggregatedMetrics.totalCost)}</p>
                </div>
                <DollarSign className="w-8 h-8 text-green-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Avg Latency</p>
                  <p className="text-2xl font-bold">{aggregatedMetrics.averageLatency.toFixed(0)}ms</p>
                </div>
                <Clock className="w-8 h-8 text-orange-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Error Rate</p>
                  <p className="text-2xl font-bold">{(aggregatedMetrics.averageErrorRate * 100).toFixed(2)}%</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Active Users</p>
                  <p className="text-2xl font-bold">{aggregatedMetrics.totalUsers}</p>
                </div>
                <Users className="w-8 h-8 text-purple-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Model-specific Metrics */}
      <div className="grid gap-6 lg:grid-cols-2">
        {metrics.map(metric => (
          <Card key={metric.modelId}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{metric.modelName}</CardTitle>
                  <CardDescription>{metric.provider}</CardDescription>
                </div>
                <Badge variant="outline">{metric.timeRange}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="usage">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="usage">Usage</TabsTrigger>
                  <TabsTrigger value="performance">Performance</TabsTrigger>
                  <TabsTrigger value="cost">Cost</TabsTrigger>
                  <TabsTrigger value="warmup">Warmup</TabsTrigger>
                </TabsList>
                <TabsContent value="usage" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{formatNumber(metric.usage.totalRequests)}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Total Requests</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{metric.usage.uniqueUsers}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Unique Users</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Top Users</h4>
                    <div className="space-y-2">
                      {metric.usage.topUsers.slice(0, 3).map(user => (
                        <div key={user.userId} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                          <span>{user.username}</span>
                          <div className="flex items-center gap-2">
                            <span>{user.requestCount} requests</span>
                            <span>{formatCurrency(user.cost)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="performance" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{metric.performance.averageLatency.toFixed(0)}ms</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Avg Latency</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{metric.performance.throughput.toFixed(1)}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Req/sec</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{metric.performance.p95Latency.toFixed(0)}ms</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">P95 Latency</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{(metric.performance.errorRate * 100).toFixed(2)}%</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Error Rate</div>
                    </div>
                  </div>
                  {/* Benchmarks */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">Benchmarks</h4>
                      <button
                        size="sm"
                        variant="outline"
                        onClick={() = aria-label="Button"> runBenchmark(metric.modelId, 'standard')}
                        disabled={runningBenchmarks.has(`${metric.modelId}-standard`)}
                      >
                        {runningBenchmarks.has(`${metric.modelId}-standard`) ? (
                          <RefreshCw className="w-3 h-3 mr-1 animate-spin sm:w-auto md:w-full" />
                        ) : (
                          <Target className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                        )}
                        Run Benchmark
                      </Button>
                    </div>
                    <div className="space-y-2">
                      {metric.benchmarks.slice(0, 3).map(benchmark => (
                        <div key={benchmark.id} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                          <span>{benchmark.name}</span>
                          <div className="flex items-center gap-2">
                            <span>{benchmark.score.toFixed(1)}</span>
                            <Badge variant={benchmark.status === 'completed' ? 'default' : 'secondary'}>
                              {benchmark.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="cost" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{formatCurrency(metric.costs.totalCost)}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Total Cost</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                      <div className="text-2xl font-bold">{formatCurrency(metric.costs.costPerRequest)}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">Per Request</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Budget Status</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Budget Utilization</span>
                        <span>{(metric.costs.budgetUtilization * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={metric.costs.budgetUtilization * 100} className="h-2" />
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Projected Monthly</span>
                        <span>{formatCurrency(metric.costs.projectedMonthlyCost)}</span>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="warmup" className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium md:text-base lg:text-lg">Enable Warmup</span>
                      <button
                        size="sm"
                        variant={metric.warmup.enabled ? "default" : "outline"}
                        onClick={() = aria-label="Button"> updateWarmupConfig(metric.modelId, { 
                          enabled: !metric.warmup.enabled 
                        })}
                      >
                        {metric.warmup.enabled ? 'Enabled' : 'Disabled'}
                      </Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium md:text-base lg:text-lg">Preload on Startup</span>
                      <button
                        size="sm"
                        variant={metric.warmup.preloadOnStartup ? "default" : "outline"}
                        onClick={() = aria-label="Button"> updateWarmupConfig(metric.modelId, { 
                          preloadOnStartup: !metric.warmup.preloadOnStartup 
                        })}
                        disabled={!metric.warmup.enabled}
                      >
                        {metric.warmup.preloadOnStartup ? 'Yes' : 'No'}
                      </Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium md:text-base lg:text-lg">Keep Warm</span>
                      <button
                        size="sm"
                        variant={metric.warmup.keepWarm ? "default" : "outline"}
                        onClick={() = aria-label="Button"> updateWarmupConfig(metric.modelId, { 
                          keepWarm: !metric.warmup.keepWarm 
                        })}
                        disabled={!metric.warmup.enabled}
                      >
                        {metric.warmup.keepWarm ? 'Yes' : 'No'}
                      </Button>
                    </div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                      <div>Cooldown Delay: {metric.warmup.cooldownDelay}s</div>
                      <div>Priority: {metric.warmup.resourceLimits.priority}</div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        ))}
      </div>
      {metrics.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400 sm:w-auto md:w-full" />
            <h3 className="text-lg font-medium mb-2">No Metrics Available</h3>
            <p className="text-gray-600">
              No model usage data found for the selected time range
            </p>
          </CardContent>
        </Card>
      )}
    </div>
    </ErrorBoundary>
  );
};
export default ModelMetricsDashboard;
