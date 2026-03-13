"use client";

import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  RadarChart,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
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
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  DollarSign,
  Shield,
  Clock,
  Target,
  Users,
  XCircle,
  Star,
  Award
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  ProviderPerformance,
  TimeRange
} from './types';
import { 
  useProviderPerformance, 
  useActions, 
  useLoading, 
  useError,
  useLastUpdated 
} from './store/performanceAdaptiveRoutingStore';
import { formatRelativeTime } from '@/lib/utils';

interface ProviderComparisonProps {
  className?: string;
  showControls?: boolean;
  refreshInterval?: number;
  defaultTimeRange?: TimeRange;
  defaultProviders?: string[];
}

interface ProviderCardProps {
  provider: ProviderPerformance;
  isSelected?: boolean;
  className?: string;
}

const ProviderCard: React.FC<ProviderCardProps> = ({
  provider,
  isSelected = false,
  className,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'inactive': return 'text-gray-600';
      case 'degraded': return 'text-yellow-600';
      case 'maintenance': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100';
      case 'inactive': return 'bg-gray-100';
      case 'degraded': return 'bg-yellow-100';
      case 'maintenance': return 'bg-orange-100';
      default: return 'bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'declining': return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'stable': return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
      default: return null;
    }
  };

  const getPerformanceColor = (value: number, higherIsBetter: boolean) => {
    if (higherIsBetter) {
      if (value >= 90) return 'text-green-600';
      if (value >= 75) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      if (value <= 10) return 'text-green-600';
      if (value <= 50) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${(cost * 1000).toFixed(2)}¢`;
    return `$${cost.toFixed(4)}`;
  };

  return (
    <Card className={cn(
      "relative overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg",
      isSelected && "ring-2 ring-blue-500",
      className
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-sm font-medium">{provider.providerId}</CardTitle>
          <Badge variant={isSelected ? "default" : "outline"} className={cn(getStatusBg(provider.status || 'inactive'), getStatusColor(provider.status || 'inactive'))}>
            {provider.status || 'Unknown'}
          </Badge>
        </div>
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          Last seen: {provider.lastUpdated ? formatRelativeTime(provider.lastUpdated) : 'Never'}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Response Time</span>
            </div>
            <div className={cn("text-2xl font-bold", getPerformanceColor(provider.averageResponseTime, false))}>
              {formatResponseTime(provider.averageResponseTime)}
            </div>
            <div className="flex items-center space-x-1">
              {getTrendIcon(provider.trend)}
              <span className="text-xs text-muted-foreground">
                {provider.trend === 'improving' ? 'Improving' : provider.trend === 'declining' ? 'Declining' : 'Stable'}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Target className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Success Rate</span>
            </div>
            <div className={cn("text-2xl font-bold", getPerformanceColor(provider.successRate, true))}>
              {provider.successRate.toFixed(1)}%
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Cost Efficiency</span>
            </div>
            <div className={cn("text-2xl font-bold", getPerformanceColor(provider.costEfficiency, true))}>
              {formatCost(provider.costEfficiency)}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Reliability</span>
            </div>
            <div className={cn("text-2xl font-bold", getPerformanceColor(provider.reliabilityScore, true))}>
              {provider.reliabilityScore.toFixed(1)}
            </div>
          </div>
        </div>

        {/* User Satisfaction */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">User Satisfaction</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex">
              {[...Array(5)].map((_, index) => (
                <Star
                  key={index}
                  className={cn(
                    "h-4 w-4",
                    index < Math.floor(provider.userSatisfaction) ? "text-yellow-400 fill-yellow-400" : "text-gray-300 fill-gray-300"
                  )}
                />
              ))}
            </div>
            <span className="text-lg font-semibold ml-2">
              {provider.userSatisfaction.toFixed(1)}/5.0
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  className,
  showControls = true,
  refreshInterval = 30000,
  defaultProviders = [],
}) => {
  const providerPerformance = useProviderPerformance();
  const actions = useActions();
  const loading = useLoading();
  const error = useError();
  const lastUpdated = useLastUpdated();
  const hasFetchedInitialData = useRef(false);

  const [selectedProviders, setSelectedProviders] = useState<string[]>(defaultProviders);
  const [selectedMetric, setSelectedMetric] = useState<string>('overview');

  // Auto-refresh effect
  useEffect(() => {
    const interval = setInterval(() => {
      if (selectedProviders.length > 0) {
        // actions.compareProviders(selectedProviders);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [selectedProviders, refreshInterval, actions]);

  // Initial data fetch
  useEffect(() => {
    if (hasFetchedInitialData.current) {
      return;
    }

    hasFetchedInitialData.current = true;
    actions.fetchProviders();
    if (selectedProviders.length > 0) {
      // actions.compareProviders(selectedProviders);
    }
  }, [actions, selectedProviders.length]);

  // Convert provider performance to array
  const providerArray = useMemo(() => {
    return Object.values(providerPerformance).map((performance) => ({
      ...performance,
    }));
  }, [providerPerformance]);

  // Filter providers based on selection
  const filteredProviders = useMemo(() => {
    if (selectedProviders.length === 0) return providerArray;
    return providerArray.filter(p => selectedProviders.includes(p.providerId));
  }, [providerArray, selectedProviders]);

  // Process radar chart data
  const radarData = useMemo(() => {
    const maxValues = {
      'Response Time': 5000, // 5 seconds max
      'Success Rate': 100,
      'Cost Efficiency': 100,
      'Reliability': 100,
      'User Satisfaction': 5,
    };

    return filteredProviders.map(provider => {
      const normalizedResponseTime = Math.max(0, 100 - (provider.averageResponseTime / maxValues['Response Time']) * 100);
      const normalizedSuccessRate = provider.successRate;
      const normalizedCostEfficiency = provider.costEfficiency;
      const normalizedReliability = provider.reliabilityScore;
      const normalizedUserSatisfaction = (provider.userSatisfaction / 5) * 100;

      return {
        provider: provider.providerId,
        'Response Time': normalizedResponseTime,
        'Success Rate': normalizedSuccessRate,
        'Cost Efficiency': normalizedCostEfficiency,
        'Reliability': normalizedReliability,
        'User Satisfaction': normalizedUserSatisfaction,
      };
    });
  }, [filteredProviders]);

  // Process comparison chart data
  const comparisonData = useMemo(() => {
    return filteredProviders.map(provider => ({
      name: provider.providerId,
      responseTime: provider.averageResponseTime,
      successRate: provider.successRate,
      costEfficiency: provider.costEfficiency,
      reliability: provider.reliabilityScore,
      userSatisfaction: provider.userSatisfaction,
      overallScore: (provider.successRate + provider.costEfficiency + provider.reliabilityScore + provider.userSatisfaction) / 4,
    }));
  }, [filteredProviders]);

  const handleRefresh = () => {
    if (selectedProviders.length > 0) {
      // actions.compareProviders(selectedProviders);
    }
    actions.fetchProviders();
  };

  const handleExport = () => {
    const data = JSON.stringify(filteredProviders, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `provider-comparison-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSelectAll = () => {
    setSelectedProviders(providerArray.map(p => p.providerId));
  };

  const handleClearSelection = () => {
    setSelectedProviders([]);
  };

  if (loading && !providerArray.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading provider performance data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading provider performance</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!providerArray.length) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <p className="text-muted-foreground">No provider performance data available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleSelectAll}
                disabled={selectedProviders.length === providerArray.length}
              >
                Select All
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleClearSelection}
                disabled={selectedProviders.length === 0}
              >
                Clear Selection
              </Button>
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
          
          <Badge variant="outline" className="ml-auto">
            {selectedProviders.length} of {providerArray.length} selected
          </Badge>
        </div>
      )}

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {filteredProviders.map(provider => (
          <ProviderCard
            key={provider.providerId}
            provider={provider}
            isSelected={selectedProviders.includes(provider.providerId)}
          />
        ))}
      </div>

      {/* Comparison Charts */}
      {filteredProviders.length > 1 && (
        <Tabs defaultValue="overview" value={selectedMetric} onValueChange={setSelectedMetric}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="radar">Radar Chart</TabsTrigger>
            <TabsTrigger value="comparison">Detailed Comparison</TabsTrigger>
            <TabsTrigger value="trends">Performance Trends</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Overall Performance Scores</CardTitle>
                  <CardDescription>
                    Combined performance metrics comparison
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip 
                        formatter={(value: number, name: string) => [
                          value.toFixed(2),
                          name === 'overallScore' ? 'Overall Score' : name
                        ]}
                      />
                      <Bar dataKey="overallScore" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Key Metrics Comparison</CardTitle>
                  <CardDescription>
                    Side-by-side comparison of key performance indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { metric: 'Response Time', key: 'averageResponseTime', unit: 'ms', lowerIsBetter: true },
                      { metric: 'Success Rate', key: 'successRate', unit: '%', lowerIsBetter: false },
                      { metric: 'Cost Efficiency', key: 'costEfficiency', unit: '$', lowerIsBetter: true },
                      { metric: 'Reliability', key: 'reliabilityScore', unit: '', lowerIsBetter: false },
                      { metric: 'User Satisfaction', key: 'userSatisfaction', unit: '/5.0', lowerIsBetter: false },
                    ].map(({ metric, key, unit, lowerIsBetter }) => (
                      <div key={metric} className="space-y-2">
                        <div className="text-sm font-medium">{metric}</div>
                        <div className="space-y-2">
                          {filteredProviders.map(provider => {
                            const value = provider[key as keyof ProviderPerformance] as number;
                            const isBest = lowerIsBetter
                              ? filteredProviders.every(p => (p[key as keyof ProviderPerformance] as number) >= value)
                              : filteredProviders.every(p => (p[key as keyof ProviderPerformance] as number) <= value);
                            
                            return (
                              <div key={provider.providerId} className="flex items-center justify-between">
                                <span className="text-sm font-medium">{provider.providerId}</span>
                                <div className="flex items-center space-x-2">
                                  <span className={cn(
                                    "text-lg font-semibold",
                                    isBest ? "text-green-600" : "text-muted-foreground"
                                  )}>
                                    {value.toFixed(2)}{unit}
                                  </span>
                                  {isBest && (
                                    <Award className="h-4 w-4 text-yellow-500" />
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="radar" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Radar</CardTitle>
                <CardDescription>
                  Multi-dimensional comparison of provider performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      dataKey="Response Time"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Radar
                      dataKey="Success Rate"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                    <Radar
                      dataKey="Cost Efficiency"
                      stroke="#ffc658"
                      fill="#ffc658"
                      fillOpacity={0.6}
                    />
                    <Radar
                      dataKey="Reliability"
                      stroke="#ff7300"
                      fill="#ff7300"
                      fillOpacity={0.6}
                    />
                    <Radar
                      dataKey="User Satisfaction"
                      stroke="#00c49f"
                      fill="#00c49f"
                      fillOpacity={0.6}
                    />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="comparison" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Detailed Performance Comparison</CardTitle>
                <CardDescription>
                  Comprehensive comparison across all metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number, name: string) => [value.toFixed(2), name]}
                    />
                    <Legend />
                    <Bar dataKey="responseTime" fill="#ff7300" name="Response Time" />
                    <Bar dataKey="successRate" fill="#00c49f" name="Success Rate" />
                    <Bar dataKey="costEfficiency" fill="#ffc658" name="Cost Efficiency" />
                    <Bar dataKey="reliability" fill="#82ca9d" name="Reliability" />
                    <Bar dataKey="userSatisfaction" fill="#8884d8" name="User Satisfaction" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {filteredProviders.map(provider => (
                <Card key={provider.providerId}>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4" />
                      {provider.providerId} Performance Trends
                    </CardTitle>
                    <CardDescription>
                      Performance trends over time
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground mb-4">
                      Trend: {provider.trend} ({provider.trend === 'improving' ? 'Improving' : provider.trend === 'declining' ? 'Declining' : 'Stable'})
                    </div>
                    <div className="h-32 flex items-center justify-center text-muted-foreground">
                      <BarChart3 className="h-8 w-8" />
                      <p>Performance trend chart would be displayed here</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {formatRelativeTime(lastUpdated)}
        </div>
      )}
    </div>
  );
};

export default ProviderComparison;
