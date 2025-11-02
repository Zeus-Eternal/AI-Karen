"use client";

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { } from 'lucide-react';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { format, subDays, subHours } from 'date-fns';
export interface EnhancedAnalyticsData {
  timestamp: string;
  messageCount: number;
  responseTime: number;
  userSatisfaction: number;
  aiInsights: number;
  tokenUsage: number;
  llmProvider: string;
  userId?: string;
  messageId?: string;
  confidence?: number;
}
export interface AnalyticsStats {
  totalConversations: number;
  totalMessages: number;
  avgResponseTime: number;
  avgSatisfaction: number;
  totalInsights: number;
  activeUsers: number;
  topLlmProviders: Array<{ provider: string; count: number }>;
}
interface AnalyticsChartProps {
  data?: EnhancedAnalyticsData[];
  stats?: AnalyticsStats;
  timeframe?: '1h' | '24h' | '7d' | '30d';
  onTimeframeChange?: (timeframe: string) => void;
  onRefresh?: () => Promise<void>;
  className?: string;
}
type ChartType = 'line' | 'bar' | 'area' | 'scatter' | 'pie';
type MetricType = 'messages' | 'responseTime' | 'satisfaction' | 'insights' | 'tokens' | 'providers';
type ViewMode = 'overview' | 'detailed' | 'comparison';
export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({
  data = [],
  stats,
  timeframe = '24h',
  onTimeframeChange,
  onRefresh,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChartHook } = useHooks();
  const { toast } = useToast();
  const [chartType, setChartType] = useState<ChartType>('line');
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('messages');
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  // Process and enhance data
  const processedData = useMemo(() => {
    if (data.length === 0) return [];
    // Convert timestamp strings to Date objects and sort
    const sortedData = data
      .map(item => ({
        ...item,
        timestamp: new Date(item.timestamp),
        formattedTime: format(new Date(item.timestamp), 
          timeframe === '1h' ? 'HH:mm' : 
          timeframe === '24h' ? 'HH:mm' : 
          'MMM dd'
        )
      }))
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    // Filter by selected providers if any
    if (selectedProviders.length > 0) {
      return sortedData.filter(item => selectedProviders.includes(item.llmProvider));
    }
    return sortedData;
  }, [data, timeframe, selectedProviders]);
  // Chart configuration based on selected metric and type
  const chartOptions: AgChartOptions = useMemo(() => {
    if (processedData.length === 0) {
      return {
        data: [],
        title: { text: 'No data available' },
        background: { fill: 'transparent' }
      };
    }
    const baseOptions: AgChartOptions = {
      data: processedData,
      theme: 'ag-default',
      background: { fill: 'transparent' },
      padding: { top: 20, right: 20, bottom: 40, left: 60 },
      legend: { enabled: true, position: 'bottom' }
    };
    // Configure series based on metric and chart type
    switch (selectedMetric) {
      case 'messages':
        if (chartType === 'pie') {
          return {
            ...baseOptions,
            title: { text: 'Message Volume Distribution' },
            series: [
              {
                // Pie chart configuration
                type: 'pie',
                angleKey: 'messageCount',
                labelKey: 'formattedTime',
              } as any,
            ],
          } as AgChartOptions;
        }
        return {
          ...baseOptions,
          title: { text: 'Message Volume Over Time' },
          series: [
            {
              type: chartType,
              xKey: 'formattedTime',
              yKey: 'messageCount',
              yName: 'Messages',
              stroke: '#3b82f6',
              fill: chartType === 'area' ? '#3b82f680' : '#3b82f6',
            } as any,
          ],
          axes: [
            { type: 'category', position: 'bottom', title: { text: 'Time' } },
            { type: 'number', position: 'left', title: { text: 'Message Count' } },
          ],
        } as AgChartOptions;
      case 'responseTime':
        return {
          ...baseOptions,
          title: { text: 'Response Time Trends' },
          series: [{
            type: chartType === 'pie' ? 'line' : chartType, // Pie doesn't make sense for response time
            xKey: 'formattedTime',
            yKey: 'responseTime',
            yName: 'Response Time (ms)',
            stroke: '#f59e0b',
            fill: chartType === 'area' ? '#f59e0b80' : '#f59e0b'
          }],
          axes: [
            { type: 'category', position: 'bottom', title: { text: 'Time' } },
            { type: 'number', position: 'left', title: { text: 'Response Time (ms)' } }
          ]
        };
      case 'satisfaction':
        return {
          ...baseOptions,
          title: { text: 'User Satisfaction Scores' },
          series: [{
            type: chartType === 'pie' ? 'line' : chartType,
            xKey: 'formattedTime',
            yKey: 'userSatisfaction',
            yName: 'Satisfaction (1-5)',
            stroke: '#10b981',
            fill: chartType === 'area' ? '#10b98180' : '#10b981'
          }],
          axes: [
            { type: 'category', position: 'bottom', title: { text: 'Time' } },
            { type: 'number', position: 'left', title: { text: 'Satisfaction Score' }, min: 0, max: 5 }
          ]
        };
      case 'providers':
        // Group data by provider for pie chart
        const providerData = processedData.reduce((acc, item) => {
          const provider = item.llmProvider;
          acc[provider] = (acc[provider] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        const providerChartData = Object.entries(providerData).map(([provider, count]) => ({
          provider,
          count,
          percentage: (count / processedData.length * 100).toFixed(1)
        }));
        return {
          ...(baseOptions as any),
          data: providerChartData,
          title: { text: 'LLM Provider Usage Distribution' },
          series: [
            {
              type: 'pie',
              angleKey: 'count',
              labelKey: 'provider',
              label: {
                enabled: true,
                formatter: ({ datum }: any) => `${datum.provider}: ${datum.percentage}%`
              }
            } as any,
          ],
        } as unknown as AgChartOptions;
      case 'tokens':
        return {
          ...baseOptions,
          title: { text: 'Token Usage Over Time' },
          series: [{
            type: chartType === 'pie' ? 'line' : chartType,
            xKey: 'formattedTime',
            yKey: 'tokenUsage',
            yName: 'Token Usage',
            stroke: '#ef4444',
            fill: chartType === 'area' ? '#ef444480' : '#ef4444'
          }],
          axes: [
            { type: 'category', position: 'bottom', title: { text: 'Time' } },
            { type: 'number', position: 'left', title: { text: 'Tokens Used' } }
          ]
        };
      default:
        return baseOptions;
    }
  }, [processedData, chartType, selectedMetric]);
  // Register analytics hooks
  useEffect(() => {
    const hookIds: string[] = [];
    hookIds.push(registerChartHook('enhancedAnalytics', 'dataLoad', async (params) => {
      return { success: true, dataPoints: processedData.length };
    }));
    hookIds.push(registerChartHook('enhancedAnalytics', 'metricChange', async (params) => {
      return { success: true, newMetric: selectedMetric };
    }));
    return () => {
      // Cleanup hooks
    };
  }, [registerChartHook, processedData.length, selectedMetric]);
  // Handle chart events
  const handleChartReady = useCallback(async () => {
    await triggerHooks('chart_enhancedAnalytics_dataLoad', {
      chartId: 'enhancedAnalytics',
      dataPoints: processedData.length,
      metric: selectedMetric,
      timeframe,
      viewMode
    }, { userId: user?.userId });
  }, [triggerHooks, processedData.length, selectedMetric, timeframe, viewMode, user?.userId]);
  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    setIsLoading(true);
    try {
      await onRefresh();
      toast({
        title: 'Analytics Refreshed',
        description: 'Analytics data has been updated successfully.'

    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Refresh Failed',
        description: 'Failed to refresh analytics data. Please try again.'

    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, toast]);
  // Trigger a ready hook when the chart context changes significantly
  useEffect(() => {
    void handleChartReady();
  }, [handleChartReady]);
  // Calculate trend indicators
  const trendData = useMemo(() => {
    if (processedData.length < 2) return null;
    const latest = processedData[processedData.length - 1];
    const previous = processedData[processedData.length - 2];
    const calculateChange = (current: number, prev: number) => {
      if (!prev) return 0;
      return ((current - prev) / prev) * 100;
    };
    return {
      messageChange: calculateChange(latest.messageCount, previous.messageCount),
      responseTimeChange: calculateChange(latest.responseTime, previous.responseTime),
      satisfactionChange: calculateChange(latest.userSatisfaction, previous.userSatisfaction),
      insightsChange: calculateChange(latest.aiInsights, previous.aiInsights)
    };
  }, [processedData]);
  const StatCard = ({ 
    icon: Icon, 
    title, 
    value, 
    change, 
    suffix = '', 
    trend = 'neutral' 
  }: {
    icon: any;
    title: string;
    value: number | string;
    change?: number;
    suffix?: string;
    trend?: 'up' | 'down' | 'neutral';
  }) => (
    <div className="flex items-center space-x-3 p-4 bg-muted/50 rounded-lg border sm:p-4 md:p-6">
      <div className="p-3 bg-primary/10 rounded-lg sm:p-4 md:p-6">
        <Icon className="h-5 w-5 text-primary " />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">{title}</p>
        <div className="flex items-center space-x-2">
          <span className="text-xl font-bold">{value}{suffix}</span>
          {change !== undefined && (
            <Badge 
              variant={change >= 0 ? 'default' : 'destructive'} 
              className="text-xs sm:text-sm md:text-base"
            >
              {change >= 0 ? <TrendingUp className="h-3 w-3 mr-1 " /> : <TrendingDown className="h-3 w-3 mr-1 " />}
              {Math.abs(change).toFixed(1)}%
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 " />
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
             >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            <StatCard
              icon={MessageSquare}
              title="Total Messages"
              value={stats.totalMessages}
              change={trendData?.messageChange}
            />
            <StatCard
              icon={Clock}
              title="Avg Response Time"
              value={Math.round(stats.avgResponseTime)}
              suffix="ms"
              change={trendData?.responseTimeChange}
            />
            <StatCard
              icon={Activity}
              title="Avg Satisfaction"
              value={stats.avgSatisfaction.toFixed(1)}
              suffix="/5"
              change={trendData?.satisfactionChange}
            />
            <StatCard
              icon={Users}
              title="Active Users"
              value={stats.activeUsers}
            />
          </div>
        )}
        {/* Controls */}
        <div className="flex items-center justify-between mt-6">
          <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as ViewMode)}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="detailed">Detailed</TabsTrigger>
              <TabsTrigger value="comparison">Comparison</TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex items-center gap-2">
            <select value={selectedMetric} onValueChange={(value) = aria-label="Select option"> setSelectedMetric(value as MetricType)}>
              <selectTrigger className="w-40 " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="messages" aria-label="Select option">Messages</SelectItem>
                <selectItem value="responseTime" aria-label="Select option">Response Time</SelectItem>
                <selectItem value="satisfaction" aria-label="Select option">Satisfaction</SelectItem>
                <selectItem value="insights" aria-label="Select option">AI Insights</SelectItem>
                <selectItem value="tokens" aria-label="Select option">Token Usage</SelectItem>
                <selectItem value="providers" aria-label="Select option">LLM Providers</SelectItem>
              </SelectContent>
            </Select>
            <select value={chartType} onValueChange={(value) = aria-label="Select option"> setChartType(value as ChartType)}>
              <selectTrigger className="w-32 " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="line" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <LineChart className="h-4 w-4 " />
                  </div>
                </SelectItem>
                <selectItem value="bar" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 " />
                  </div>
                </SelectItem>
                <selectItem value="area" aria-label="Select option">Area</SelectItem>
                {/* Column maps to bar in Ag Charts; omit separate option */}
                <selectItem value="pie" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <PieChart className="h-4 w-4 " />
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <select value={timeframe} onValueChange={onTimeframeChange} aria-label="Select option">
              <selectTrigger className="w-24 " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="1h" aria-label="Select option">1H</SelectItem>
                <selectItem value="24h" aria-label="Select option">24H</SelectItem>
                <selectItem value="7d" aria-label="Select option">7D</SelectItem>
                <selectItem value="30d" aria-label="Select option">30D</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <Tabs value={viewMode} className="w-full">
          <TabsContent value="overview" className="mt-0">
            <div className="h-[500px] w-full p-6 sm:p-4 md:p-6">
              <AgCharts options={chartOptions} />
            </div>
          </TabsContent>
          <TabsContent value="detailed" className="mt-0">
            <div className="p-6 sm:p-4 md:p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-[400px]">
                  <AgCharts
                    options={{
                      ...chartOptions,
                      title: { text: 'Primary Metric' }
                    }}
                  />
                </div>
                <div className="h-[400px]">
                  <AgCharts
                    options={{
                      data: processedData,
                      theme: 'ag-default',
                      background: { fill: 'transparent' },
                      title: { text: 'Secondary Analysis' },
                      series: [
                        {
                          type: 'line',
                          xKey: 'formattedTime',
                          yKey: 'userSatisfaction',
                          yName: 'Satisfaction',
                          stroke: '#10b981',
                        } as any,
                      ],
                      axes: [
                        { type: 'category', position: 'bottom', title: { text: 'Time' } },
                        { type: 'number', position: 'left', title: { text: 'Satisfaction' } },
                      ],
                    } as AgChartOptions}
                  />
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="comparison" className="mt-0">
            <div className="h-[500px] w-full p-6 sm:p-4 md:p-6">
              <AgCharts
                options={{
                  data: processedData,
                  theme: 'ag-default',
                  background: { fill: 'transparent' },
                  title: { text: 'Multi-Metric Comparison' },
                  series: [
                    {
                      type: 'line',
                      xKey: 'formattedTime',
                      yKey: 'messageCount',
                      yName: 'Messages',
                      stroke: '#3b82f6',
                    } as any,
                    {
                      type: 'line',
                      xKey: 'formattedTime',
                      yKey: 'aiInsights',
                      yName: 'AI Insights',
                      stroke: '#8b5cf6',
                    } as any,
                  ],
                  axes: [
                    { type: 'category', position: 'bottom', title: { text: 'Time' } },
                    { type: 'number', position: 'left', title: { text: 'Value' } },
                  ],
                } as AgChartOptions}
              />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
