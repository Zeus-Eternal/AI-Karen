"use client";

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  TrendingUp,
  MessageSquare,
  Clock,
  Zap,
  DollarSign,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ChatAnalyticsData {
  totalMessages: number;
  totalTokens: number;
  averageLatency: number;
  totalCost: number;
  messagesByDay?: { date: string; count: number }[];
  tokensByDay?: { date: string; count: number }[];
  latencyByDay?: { date: string; average: number }[];
}

export interface ChatAnalyticsChartProps {
  data: ChatAnalyticsData;
  className?: string;
}

function ChatAnalyticsChartComponent({
  data,
  className,
}: ChatAnalyticsChartProps) {
  const stats = [
    {
      label: 'Total Messages',
      value: data.totalMessages.toLocaleString(),
      icon: MessageSquare,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    },
    {
      label: 'Total Tokens',
      value: data.totalTokens.toLocaleString(),
      icon: Zap,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
    },
    {
      label: 'Avg Latency',
      value: `${data.averageLatency.toFixed(0)}ms`,
      icon: Clock,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
    },
    {
      label: 'Total Cost',
      value: `$${data.totalCost.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
    },
  ];

  const renderSimpleChart = (dataPoints?: { date: string; count?: number; average?: number }[]) => {
    if (!dataPoints || dataPoints.length === 0) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-400">
          No data available
        </div>
      );
    }

    const maxValue = Math.max(...dataPoints.map(d => d.count || d.average || 0));

    return (
      <div className="flex items-end justify-between gap-2 h-48 px-4">
        {dataPoints.slice(-7).map((point, index) => {
          const value = point.count || point.average || 0;
          const height = (value / maxValue) * 100;

          return (
            <div key={index} className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full flex items-end justify-center" style={{ height: '160px' }}>
                <div
                  className="w-full bg-blue-500 rounded-t-md transition-all hover:bg-blue-600"
                  style={{ height: `${height}%`, minHeight: value > 0 ? '4px' : '0' }}
                  title={`${point.date}: ${value}`}
                />
              </div>
              <span className="text-xs text-gray-500 truncate w-full text-center">
                {new Date(point.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        <h3 className="text-lg font-semibold">Analytics</h3>
        <Badge variant="secondary">
          <TrendingUp className="h-3 w-3 mr-1" />
          Overview
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
                <div className={cn('p-2 rounded-lg', stat.bgColor)}>
                  <Icon className={cn('h-4 w-4', stat.color)} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Trends</CardTitle>
          <CardDescription>Your chat activity over the last 7 days</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="messages" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="messages">Messages</TabsTrigger>
              <TabsTrigger value="tokens">Tokens</TabsTrigger>
              <TabsTrigger value="latency">Latency</TabsTrigger>
            </TabsList>

            <TabsContent value="messages" className="mt-4">
              {renderSimpleChart(data.messagesByDay)}
            </TabsContent>

            <TabsContent value="tokens" className="mt-4">
              {renderSimpleChart(data.tokensByDay)}
            </TabsContent>

            <TabsContent value="latency" className="mt-4">
              {renderSimpleChart(data.latencyByDay)}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { ChatAnalyticsChartComponent as ChatAnalyticsChart };
export default ChatAnalyticsChartComponent;
