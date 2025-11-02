/**
 * Model Usage Analytics Component
 * Historical performance trends and optimization suggestions
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Clock, 
  Users, 
  DollarSign,
  Activity,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  Calendar,
  Target,
  Zap
} from 'lucide-react';
import { ModelUsageAnalytics as UsageAnalyticsType, OptimizationRecommendation, TimeRange } from '@/types/providers';
import { useToast } from '@/hooks/use-toast';
interface ModelUsageAnalyticsProps {
  modelId: string;
  modelName: string;
  className?: string;
}
interface ChartData {
  timestamp: Date;
  value: number;
  label?: string;
}
const ModelUsageAnalytics: React.FC<ModelUsageAnalyticsProps> = ({
  modelId,
  modelName,
  className
}) => {
  const { toast } = useToast();
  const [analytics, setAnalytics] = useState<UsageAnalyticsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d' | '90d'>('7d');
  const [selectedMetric, setSelectedMetric] = useState<'usage' | 'performance' | 'cost'>('usage');
  useEffect(() => {
    loadAnalytics();
  }, [modelId, timeRange]);
  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/models/${modelId}/analytics?timeRange=${timeRange}`);
      if (!response.ok) throw new Error('Failed to load analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load usage analytics',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(amount);
  };
  const getTrendIcon = (trend: 'increasing' | 'stable' | 'decreasing' | 'improving' | 'degrading') => {
    switch (trend) {
      case 'increasing':
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />;
      case 'decreasing':
      case 'degrading':
        return <TrendingDown className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };
  const getTrendColor = (trend: 'increasing' | 'stable' | 'decreasing' | 'improving' | 'degrading', isGoodWhenIncreasing: boolean = true) => {
    if (trend === 'stable') return 'text-gray-600';
    const isPositive = (trend === 'increasing' || trend === 'improving') === isGoodWhenIncreasing;
    return isPositive ? 'text-green-600' : 'text-red-600';
  };
  const RecommendationCard: React.FC<{ recommendation: OptimizationRecommendation }> = ({ recommendation }) => {
    const getPriorityColor = (priority: string) => {
      switch (priority) {
        case 'critical': return 'bg-red-100 text-red-800 border-red-200';
        case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
        case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        default: return 'bg-blue-100 text-blue-800 border-blue-200';
      }
    };
    const getTypeIcon = (type: string) => {
      switch (type) {
        case 'cost': return <DollarSign className="w-4 h-4 sm:w-auto md:w-full" />;
        case 'performance': return <Zap className="w-4 h-4 sm:w-auto md:w-full" />;
        case 'reliability': return <CheckCircle className="w-4 h-4 sm:w-auto md:w-full" />;
        default: return <Target className="w-4 h-4 sm:w-auto md:w-full" />;
      }
    };
    return (
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {getTypeIcon(recommendation.type)}
              <CardTitle className="text-base">{recommendation.title}</CardTitle>
            </div>
            <Badge className={getPriorityColor(recommendation.priority)}>
              {recommendation.priority}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-gray-600 md:text-base lg:text-lg">{recommendation.description}</p>
          {/* Impact Estimate */}
          <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
            {recommendation.impact.costSavings && (
              <div className="text-center">
                <div className="text-lg font-semibold text-green-600">
                  {formatCurrency(recommendation.impact.costSavings)}
                </div>
                <div className="text-xs text-gray-600 sm:text-sm md:text-base">Potential Savings</div>
              </div>
            )}
            {recommendation.impact.performanceImprovement && (
              <div className="text-center">
                <div className="text-lg font-semibold text-blue-600">
                  +{(recommendation.impact.performanceImprovement * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600 sm:text-sm md:text-base">Performance Gain</div>
              </div>
            )}
          </div>
          {/* Implementation Guide */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
              <span className="font-medium">Implementation</span>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {recommendation.implementation.difficulty}
                </Badge>
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {recommendation.implementation.estimatedTime}h
                </Badge>
              </div>
            </div>
            <div className="text-xs text-gray-600 sm:text-sm md:text-base">
              <div className="font-medium mb-1">Steps:</div>
              <ol className="list-decimal list-inside space-y-1">
                {recommendation.implementation.steps.slice(0, 3).map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
                {recommendation.implementation.steps.length > 3 && (
                  <li className="text-gray-500">+{recommendation.implementation.steps.length - 3} more steps</li>
                )}
              </ol>
            </div>
          </div>
          {/* Confidence */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium md:text-base lg:text-lg">Confidence</span>
            <div className="flex items-center gap-2">
              <Progress value={recommendation.impact.confidence * 100} className="w-16 h-2 sm:w-auto md:w-full" />
              <span className="text-sm md:text-base lg:text-lg">{(recommendation.impact.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <BarChart3 className="w-8 h-8 animate-pulse mx-auto text-blue-500 sm:w-auto md:w-full" />
            <div>Loading analytics...</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  if (!analytics) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <AlertTriangle className="w-8 h-8 mx-auto text-gray-400 mb-2 sm:w-auto md:w-full" />
          <div className="text-gray-600">No analytics data available</div>
          <button onClick={loadAnalytics} className="mt-4" variant="outline" aria-label="Button">
            Retry
          </Button>
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
                Usage Analytics - {modelName}
              </CardTitle>
              <CardDescription>
                Performance insights and optimization recommendations
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
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
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Requests</p>
                <p className="text-2xl font-bold">{formatNumber(analytics.usage.totalRequests)}</p>
              </div>
              <div className="flex items-center gap-1">
                {getTrendIcon(analytics.trends.usageTrend)}
                <span className={`text-sm ${getTrendColor(analytics.trends.usageTrend)}`}>
                  {analytics.trends.usageTrend}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Unique Users</p>
                <p className="text-2xl font-bold">{formatNumber(analytics.usage.uniqueUsers)}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500 sm:w-auto md:w-full" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Avg Latency</p>
                <p className="text-2xl font-bold">{analytics.performance.averageLatency.toFixed(0)}ms</p>
              </div>
              <div className="flex items-center gap-1">
                {getTrendIcon(analytics.trends.performanceTrend)}
                <span className={`text-sm ${getTrendColor(analytics.trends.performanceTrend, false)}`}>
                  {analytics.trends.performanceTrend}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Cost</p>
                <p className="text-2xl font-bold">{formatCurrency(analytics.costs.totalCost)}</p>
              </div>
              <div className="flex items-center gap-1">
                {getTrendIcon(analytics.trends.costTrend)}
                <span className={`text-sm ${getTrendColor(analytics.trends.costTrend, false)}`}>
                  {analytics.trends.costTrend}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Detailed Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedMetric} onValueChange={(value: any) => setSelectedMetric(value)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="usage">Usage Patterns</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="cost">Cost Analysis</TabsTrigger>
            </TabsList>
            <TabsContent value="usage" className="space-y-4">
              {/* Usage by Hour */}
              <div className="space-y-2">
                <h4 className="font-medium">Usage by Hour</h4>
                <div className="grid grid-cols-24 gap-1">
                  {analytics.usage.usageByHour.map((usage, hour) => (
                    <div
                      key={hour}
                      className="h-8 bg-blue-100 rounded flex items-end justify-center text-xs sm:text-sm md:text-base"
                      style={{ 
                        backgroundColor: `rgba(59, 130, 246, ${Math.max(0.1, usage / Math.max(...analytics.usage.usageByHour))})` 
                      }}
                      title={`${hour}:00 - ${usage} requests`}
                    >
                      {hour}
                    </div>
                  ))}
                </div>
              </div>
              {/* Task Distribution */}
              <div className="space-y-2">
                <h4 className="font-medium">Task Distribution</h4>
                <div className="space-y-2">
                  {Object.entries(analytics.usage.taskDistribution)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([task, count]) => {
                      const percentage = (count / analytics.usage.totalRequests) * 100;
                      return (
                        <div key={task} className="flex items-center gap-3">
                          <div className="w-24 text-sm font-medium truncate sm:w-auto md:w-full">{task}</div>
                          <div className="flex-1">
                            <Progress value={percentage} className="h-2" />
                          </div>
                          <div className="w-16 text-sm text-right sm:w-auto md:w-full">
                            {formatNumber(count)} ({percentage.toFixed(1)}%)
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
              {/* Peak Usage */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Peak Concurrency</div>
                  <div className="text-xl font-bold">{analytics.usage.peakConcurrency}</div>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                  <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Avg Requests/User</div>
                  <div className="text-xl font-bold">{analytics.usage.averageRequestsPerUser.toFixed(1)}</div>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="performance" className="space-y-4">
              {/* Latency Distribution */}
              <div className="space-y-2">
                <h4 className="font-medium">Latency Distribution</h4>
                <div className="space-y-2">
                  {analytics.performance.latencyDistribution.buckets.map((bucket, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-24 text-sm sm:w-auto md:w-full">
                        {bucket.min}-{bucket.max}ms
                      </div>
                      <div className="flex-1">
                        <Progress value={bucket.percentage} className="h-2" />
                      </div>
                      <div className="w-16 text-sm text-right sm:w-auto md:w-full">
                        {bucket.percentage.toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {/* Quality Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium">Quality Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">User Satisfaction</span>
                      <span className="font-medium">{(analytics.performance.qualityMetrics.userSatisfaction * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={analytics.performance.qualityMetrics.userSatisfaction * 100} className="h-2" />
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Task Success Rate</span>
                      <span className="font-medium">{(analytics.performance.qualityMetrics.taskSuccessRate * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={analytics.performance.qualityMetrics.taskSuccessRate * 100} className="h-2" />
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">Reliability</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Output Quality</span>
                      <span className="font-medium">{(analytics.performance.qualityMetrics.outputQuality * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={analytics.performance.qualityMetrics.outputQuality * 100} className="h-2" />
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Consistency</span>
                      <span className="font-medium">{(analytics.performance.qualityMetrics.consistencyScore * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={analytics.performance.qualityMetrics.consistencyScore * 100} className="h-2" />
                  </div>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="cost" className="space-y-4">
              {/* Cost Breakdown */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium">Cost Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Cost per Request</span>
                      <span className="font-medium">{formatCurrency(analytics.costs.costPerRequest)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Cost per User</span>
                      <span className="font-medium">{formatCurrency(analytics.costs.costPerUser)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Projected Monthly</span>
                      <span className="font-medium">{formatCurrency(analytics.costs.projectedMonthlyCost)}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">Budget Status</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Budget Utilization</span>
                      <span className="font-medium">{(analytics.costs.budgetUtilization * 100).toFixed(1)}%</span>
                    </div>
                    <Progress 
                      value={analytics.costs.budgetUtilization * 100} 
                      className={`h-2 ${analytics.costs.budgetUtilization > 0.8 ? 'bg-red-100' : 'bg-green-100'}`}
                    />
                    {analytics.costs.budgetUtilization > 0.8 && (
                      <div className="text-xs text-red-600 flex items-center gap-1 sm:text-sm md:text-base">
                        <AlertTriangle className="w-3 h-3 sm:w-auto md:w-full" />
                        Approaching budget limit
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      {/* Optimization Recommendations */}
      {analytics.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 sm:w-auto md:w-full" />
              Optimization Recommendations
            </CardTitle>
            <CardDescription>
              AI-generated suggestions to improve performance and reduce costs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {analytics.recommendations.slice(0, 4).map((recommendation, idx) => (
                <RecommendationCard key={idx} recommendation={recommendation} />
              ))}
            </div>
            {analytics.recommendations.length > 4 && (
              <div className="text-center mt-4">
                <button variant="outline" aria-label="Button">
                  View All {analytics.recommendations.length} Recommendations
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      {/* Seasonal Patterns */}
      {analytics.trends.seasonalPatterns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 sm:w-auto md:w-full" />
              Usage Patterns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {analytics.trends.seasonalPatterns.map((pattern, idx) => (
                <div key={idx} className="p-3 border rounded-lg sm:p-4 md:p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{pattern.pattern}</span>
                    <Badge variant="outline">
                      {(pattern.strength * 100).toFixed(0)}% strength
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 md:text-base lg:text-lg">{pattern.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
export default ModelUsageAnalytics;
