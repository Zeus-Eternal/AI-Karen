'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Activity, Clock, MessageSquare, Zap } from 'lucide-react';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { format, subDays, subHours } from 'date-fns';
import { safeDebug } from '@/lib/safe-console';
export interface ChatAnalyticsData {
  timestamp: Date;
  messageCount: number;
  responseTime: number;
  userSatisfaction: number;
  aiInsights: number;
  tokenUsage: number;
  llmProvider: string;
}
interface ChatAnalyticsChartProps {
  data?: ChatAnalyticsData[];
  timeframe?: '1h' | '24h' | '7d' | '30d';
  onTimeframeChange?: (timeframe: string) => void;
  className?: string;
}
type ChartType = 'line' | 'bar' | 'area' | 'scatter';
type MetricType = 'messages' | 'responseTime' | 'satisfaction' | 'insights' | 'tokens';
export const ChatAnalyticsChart: React.FC<ChatAnalyticsChartProps> = ({
  data = [],
  timeframe = '24h',
  onTimeframeChange,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChartHook } = useHooks();
  const [chartType, setChartType] = useState<ChartType>('line');
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('messages');
  const [isLoading, setIsLoading] = useState(false);
  // Generate  if none provided
  const chartData = useMemo(() => {
    if (data.length > 0) return data;
    // Generate  based on timeframe
    const now = new Date();
    const [] = [];
    const intervals = timeframe === '1h' ? 12 : timeframe === '24h' ? 24 : timeframe === '7d' ? 7 : 30;
    for (let i = intervals; i >= 0; i--) {
      const timestamp = timeframe === '1h' 
        ? subHours(now, i * 0.5) 
        : timeframe === '24h'
        ? subHours(now, i)
        : subDays(now, i);
      .push({
        timestamp,
        messageCount: Math.floor(Math.random() * 50) + 10,
        responseTime: Math.random() * 2000 + 500,
        userSatisfaction: Math.random() * 2 + 3, // 3-5 scale
        aiInsights: Math.floor(Math.random() * 10) + 1,
        tokenUsage: Math.floor(Math.random() * 1000) + 200,
        llmProvider: ['llama-cpp', 'openai', 'anthropic'][Math.floor(Math.random() * 3)]
      });
    }
    return ;
  }, [data, timeframe]);
  // Chart configuration based on selected metric
  const chartOptions: AgChartOptions = useMemo(() => {
    const baseOptions: AgChartOptions = {
      data: chartData.map(item => ({
        ...item,
        timestamp: format(item.timestamp, timeframe === '1h' ? 'HH:mm' : timeframe === '24h' ? 'HH:mm' : 'MMM dd')
      })),
      theme: 'ag-default',
      background: {
        fill: 'transparent'
      },
      padding: {
        top: 20,
        right: 20,
        bottom: 40,
        left: 60
      }
    };
    const getSeriesConfig = () => {
      switch (selectedMetric) {
        case 'messages':
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'messageCount',
            yName: 'Messages',
            stroke: '#3b82f6',
            fill: chartType === 'area' ? '#3b82f680' : '#3b82f6'
          };
        case 'responseTime':
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'responseTime',
            yName: 'Response Time (ms)',
            stroke: '#f59e0b',
            fill: chartType === 'area' ? '#f59e0b80' : '#f59e0b'
          };
        case 'satisfaction':
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'userSatisfaction',
            yName: 'Satisfaction (1-5)',
            stroke: '#10b981',
            fill: chartType === 'area' ? '#10b98180' : '#10b981'
          };
        case 'insights':
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'aiInsights',
            yName: 'AI Insights',
            stroke: '#8b5cf6',
            fill: chartType === 'area' ? '#8b5cf680' : '#8b5cf6'
          };
        case 'tokens':
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'tokenUsage',
            yName: 'Token Usage',
            stroke: '#ef4444',
            fill: chartType === 'area' ? '#ef444480' : '#ef4444'
          };
        default:
          return {
            type: chartType,
            xKey: 'timestamp',
            yKey: 'messageCount',
            yName: 'Messages',
            stroke: '#3b82f6',
            fill: chartType === 'area' ? '#3b82f680' : '#3b82f6'
          };
      }
    };
    return {
      ...baseOptions,
      series: [getSeriesConfig()],
      axes: [
        {
          type: 'category',
          position: 'bottom',
          title: {
            text: 'Time'
          }
        },
        {
          type: 'number',
          position: 'left',
          title: {
            text: getSeriesConfig().yName
          }
        }
      ],
      legend: {
        enabled: false
      }
    };
  }, [chartData, chartType, selectedMetric, timeframe]);
  // Register chart hooks on mount
  useEffect(() => {
    const hookIds: string[] = [];
    // Register data load hook
    hookIds.push(registerChartHook('chatAnalytics', 'dataLoad', async (params) => {
      safeDebug('Chat analytics chart data loaded:', params);
      return { success: true, dataPoints: chartData.length };
    }));
    // Register series click hook
    hookIds.push(registerChartHook('chatAnalytics', 'seriesClick', async (params) => {
      safeDebug('Chart series clicked:', params);
      return { success: true, clickedData: params };
    }));
    return () => {
      // Cleanup hooks on unmount
      hookIds.forEach(id => {
        // Note: unregisterHook would be called here in a real implementation
      });
    };
  }, [registerChartHook, chartData.length]);
  // Handle chart events
  const handleChartReady = useCallback(async () => {
    await triggerHooks('chart_chatAnalytics_dataLoad', {
      chartId: 'chatAnalytics',
      dataPoints: chartData.length,
      metric: selectedMetric,
      timeframe
    }, { userId: user?.userId });
  }, [triggerHooks, chartData.length, selectedMetric, timeframe, user?.userId]);
  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    if (chartData.length === 0) return null;
    const latest = chartData[chartData.length - 1];
    const previous = chartData[chartData.length - 2];
    const totalMessages = chartData.reduce((sum, item) => sum + item.messageCount, 0);
    const avgResponseTime = chartData.reduce((sum, item) => sum + item.responseTime, 0) / chartData.length;
    const avgSatisfaction = chartData.reduce((sum, item) => sum + item.userSatisfaction, 0) / chartData.length;
    const totalInsights = chartData.reduce((sum, item) => sum + item.aiInsights, 0);
    const getChange = (current: number, prev: number) => {
      if (!prev) return 0;
      return ((current - prev) / prev) * 100;
    };
    return {
      totalMessages,
      avgResponseTime: Math.round(avgResponseTime),
      avgSatisfaction: Math.round(avgSatisfaction * 10) / 10,
      totalInsights,
      messageChange: previous ? getChange(latest.messageCount, previous.messageCount) : 0,
      responseTimeChange: previous ? getChange(latest.responseTime, previous.responseTime) : 0,
      satisfactionChange: previous ? getChange(latest.userSatisfaction, previous.userSatisfaction) : 0,
      insightsChange: previous ? getChange(latest.aiInsights, previous.aiInsights) : 0
    };
  }, [chartData]);
  const StatCard = ({ icon: Icon, title, value, change, suffix = '' }: {
    icon: any;
    title: string;
    value: number | string;
    change?: number;
    suffix?: string;
  }) => (
    <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
      <div className="p-2 bg-primary/10 rounded-lg sm:p-4 md:p-6">
        <Icon className="h-4 w-4 text-primary sm:w-auto md:w-full" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">{title}</p>
        <div className="flex items-center space-x-2">
          <span className="text-lg font-semibold">{value}{suffix}</span>
          {change !== undefined && (
            <Badge variant={change >= 0 ? 'default' : 'destructive'} className="text-xs sm:text-sm md:text-base">
              {change >= 0 ? <TrendingUp className="h-3 w-3 mr-1 sm:w-auto md:w-full" /> : <TrendingDown className="h-3 w-3 mr-1 sm:w-auto md:w-full" />}
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
          <CardTitle className="text-lg font-semibold">
            Chat Analytics
          </CardTitle>
          <div className="flex items-center gap-2">
            <select value={selectedMetric} onValueChange={(value) = aria-label="Select option"> setSelectedMetric(value as MetricType)}>
              <selectTrigger className="w-40 sm:w-auto md:w-full" aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="messages" aria-label="Select option">Messages</SelectItem>
                <selectItem value="responseTime" aria-label="Select option">Response Time</SelectItem>
                <selectItem value="satisfaction" aria-label="Select option">Satisfaction</SelectItem>
                <selectItem value="insights" aria-label="Select option">AI Insights</SelectItem>
                <selectItem value="tokens" aria-label="Select option">Token Usage</SelectItem>
              </SelectContent>
            </Select>
            <select value={chartType} onValueChange={(value) = aria-label="Select option"> setChartType(value as ChartType)}>
              <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="line" aria-label="Select option">Line</SelectItem>
                <selectItem value="bar" aria-label="Select option">Bar</SelectItem>
                <selectItem value="area" aria-label="Select option">Area</SelectItem>
                <selectItem value="scatter" aria-label="Select option">Scatter</SelectItem>
              </SelectContent>
            </Select>
            <select value={timeframe} onValueChange={onTimeframeChange} aria-label="Select option">
              <selectTrigger className="w-24 sm:w-auto md:w-full" aria-label="Select option">
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
        {summaryStats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
            <StatCard
              icon={MessageSquare}
              title="Total Messages"
              value={summaryStats.totalMessages}
              change={summaryStats.messageChange}
            />
            <StatCard
              icon={Clock}
              title="Avg Response Time"
              value={summaryStats.avgResponseTime}
              suffix="ms"
              change={summaryStats.responseTimeChange}
            />
            <StatCard
              icon={Activity}
              title="Avg Satisfaction"
              value={summaryStats.avgSatisfaction}
              suffix="/5"
              change={summaryStats.satisfactionChange}
            />
            <StatCard
              icon={Zap}
              title="AI Insights"
              value={summaryStats.totalInsights}
              change={summaryStats.insightsChange}
            />
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="h-[400px] w-full p-4 sm:p-4 md:p-6">
          <AgCharts
            options={chartOptions}
          />
        </div>
      </CardContent>
    </Card>
  );
};
