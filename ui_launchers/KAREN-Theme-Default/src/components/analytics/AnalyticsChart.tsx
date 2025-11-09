"use client";

import React, { useState, useEffect, useMemo, useCallback, useId } from "react";
import { AgCharts } from "ag-charts-react";
import type { AgChartOptions } from "ag-charts-community";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import {
  BarChart3,
  RefreshCw,
  MessageSquare,
  Clock,
  Activity,
  Users,
  TrendingUp,
  TrendingDown,
  LineChart,
  PieChart,
} from "lucide-react";

import { useHooks } from "@/contexts/HookContext";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

/* --------------------------------- Types --------------------------------- */

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
  timeframe?: "1h" | "24h" | "7d" | "30d";
  onTimeframeChange?: (timeframe: "1h" | "24h" | "7d" | "30d") => void;
  onRefresh?: () => Promise<void>;
  className?: string;
}

type ChartType = "line" | "bar" | "area" | "scatter" | "pie";
type MetricType =
  | "messages"
  | "responseTime"
  | "satisfaction"
  | "insights"
  | "tokens"
  | "providers";
type ViewMode = "overview" | "detailed" | "comparison";

/* ---------------------------- Component Start ---------------------------- */

export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({
  data = [],
  stats,
  timeframe = "24h",
  onTimeframeChange,
  onRefresh,
  className = "",
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChartHook, unregisterHook } = useHooks();
  const { toast } = useToast();

  const [chartType, setChartType] = useState<ChartType>("line");
  const [selectedMetric, setSelectedMetric] = useState<MetricType>("messages");
  const [viewMode, setViewMode] = useState<ViewMode>("overview");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);

  const statusRegionId = useId();

  /* ------------------------------ Data Shaping ------------------------------ */

  const processedData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];

    const sorted = data
      .map((item) => {
        const d = new Date(item.timestamp);
        const formattedTime =
          timeframe === "1h"
            ? format(d, "HH:mm")
            : timeframe === "24h"
            ? format(d, "HH:mm")
            : format(d, "MMM dd");
        return { ...item, timestampDate: d, formattedTime };
      })
      .sort((a, b) => a.timestampDate.getTime() - b.timestampDate.getTime());

    if (selectedProviders.length > 0) {
      return sorted.filter((i) => selectedProviders.includes(i.llmProvider));
    }
    return sorted;
  }, [data, timeframe, selectedProviders]);

  /* ------------------------------ Chart Options ----------------------------- */

  const chartOptions: AgChartOptions = useMemo(() => {
    if (processedData.length === 0) {
      return {
        data: [],
        title: { text: "No data available" },
        background: { fill: "transparent" },
      };
    }

    const base: AgChartOptions = {
      data: processedData as any,
      theme: "ag-default",
      background: { fill: "transparent" },
      padding: { top: 20, right: 20, bottom: 40, left: 60 },
      legend: { enabled: true, position: "bottom" },
    };

    switch (selectedMetric) {
      case "messages":
        if (chartType === "pie") {
          return {
            ...base,
            title: { text: "Message Volume Distribution" },
            series: [
              {
                type: "pie",
                angleKey: "messageCount",
                labelKey: "formattedTime",
              } as any,
            ],
          } as AgChartOptions;
        }
        return {
          ...base,
          title: { text: "Message Volume Over Time" },
          series: [
            {
              type: chartType as any,
              xKey: "formattedTime",
              yKey: "messageCount",
              yName: "Messages",
              stroke: "#3b82f6",
              fill: chartType === "area" ? "#3b82f680" : "#3b82f6",
            } as any,
          ],
          axes: [
            { type: "category", position: "bottom", title: { text: "Time" } },
            { type: "number", position: "left", title: { text: "Message Count" } },
          ],
        };

      case "responseTime":
        return {
          ...base,
          title: { text: "Response Time Trends" },
          series: [
            {
              type: chartType === "pie" ? ("line" as any) : (chartType as any),
              xKey: "formattedTime",
              yKey: "responseTime",
              yName: "Response Time (ms)",
              stroke: "#f59e0b",
              fill: chartType === "area" ? "#f59e0b80" : "#f59e0b",
            } as any,
          ],
          axes: [
            { type: "category", position: "bottom", title: { text: "Time" } },
            { type: "number", position: "left", title: { text: "Response Time (ms)" } },
          ],
        };

      case "satisfaction":
        return {
          ...base,
          title: { text: "User Satisfaction Scores" },
          series: [
            {
              type: chartType === "pie" ? ("line" as any) : (chartType as any),
              xKey: "formattedTime",
              yKey: "userSatisfaction",
              yName: "Satisfaction (1-5)",
              stroke: "#10b981",
              fill: chartType === "area" ? "#10b98180" : "#10b981",
            } as any,
          ],
          axes: [
            { type: "category", position: "bottom", title: { text: "Time" } },
            {
              type: "number",
              position: "left",
              title: { text: "Satisfaction Score" },
              min: 0,
              max: 5,
            },
          ],
        };

      case "providers": {
        const byProvider = processedData.reduce((acc: Record<string, number>, item) => {
          acc[item.llmProvider] = (acc[item.llmProvider] || 0) + 1;
          return acc;
        }, {});
        const providerData = Object.entries(byProvider).map(([provider, count]) => ({
          provider,
          count,
          percentage: ((count / processedData.length) * 100).toFixed(1),
        }));

        return {
          ...base,
          data: providerData as any,
          title: { text: "LLM Provider Usage Distribution" },
          series: [
            {
              type: "pie",
              angleKey: "count",
              labelKey: "provider",
              label: {
                enabled: true,
                formatter: ({ datum }: any) => `${datum.provider}: ${datum.percentage}%`,
              },
            } as any,
          ],
        };
      }

      case "tokens":
        return {
          ...base,
          title: { text: "Token Usage Over Time" },
          series: [
            {
              type: chartType === "pie" ? ("line" as any) : (chartType as any),
              xKey: "formattedTime",
              yKey: "tokenUsage",
              yName: "Token Usage",
              stroke: "#ef4444",
              fill: chartType === "area" ? "#ef444480" : "#ef4444",
            } as any,
          ],
          axes: [
            { type: "category", position: "bottom", title: { text: "Time" } },
            { type: "number", position: "left", title: { text: "Tokens Used" } },
          ],
        };

      case "insights":
        return {
          ...base,
          title: { text: "AI Insights Over Time" },
          series: [
            {
              type: chartType === "pie" ? ("line" as any) : (chartType as any),
              xKey: "formattedTime",
              yKey: "aiInsights",
              yName: "AI Insights",
              stroke: "#8b5cf6",
              fill: chartType === "area" ? "#8b5cf680" : "#8b5cf6",
            } as any,
          ],
          axes: [
            { type: "category", position: "bottom", title: { text: "Time" } },
            { type: "number", position: "left", title: { text: "Count" } },
          ],
        };

      default:
        return base;
    }
  }, [processedData, chartType, selectedMetric]);

  /* ------------------------------ Hook Wiring ------------------------------ */

  useEffect(() => {
    const ids: string[] = [];
    ids.push(
      registerChartHook?.("enhancedAnalytics", "dataLoad", async () => {
        return { success: true, dataPoints: processedData.length };
      }) || ""
    );
    ids.push(
      registerChartHook?.("enhancedAnalytics", "metricChange", async () => {
        return { success: true, newMetric: selectedMetric };
      }) || ""
    );

    return () => {
      // Clean up any registered hooks if API supports it
      if (unregisterHook) {
        ids.filter(Boolean).forEach((id) => unregisterHook(id));
      }
    };
  }, [registerChartHook, unregisterHook, processedData.length, selectedMetric]);

  const handleChartReady = useCallback(async () => {
    await triggerHooks?.(
      "chart_enhancedAnalytics_dataLoad",
      {
        chartId: "enhancedAnalytics",
        dataPoints: processedData.length,
        metric: selectedMetric,
        timeframe,
        viewMode,
      },
      { userId: user?.userId }
    );
  }, [triggerHooks, processedData.length, selectedMetric, timeframe, viewMode, user?.userId]);

  useEffect(() => {
    void handleChartReady();
  }, [handleChartReady]);

  /* ------------------------------- Refreshing ------------------------------ */

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    setIsLoading(true);
    try {
      await onRefresh();
      toast({
        title: "Analytics Refreshed",
        description: "Analytics data has been updated successfully.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Refresh Failed",
        description: "Failed to refresh analytics data. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, toast]);

  /* ------------------------------ Trend Badges ----------------------------- */

  const trendData = useMemo(() => {
    if (processedData.length < 2) return null;
    const latest = processedData[processedData.length - 1];
    const prev = processedData[processedData.length - 2];
    const pct = (cur: number, p: number) => (p ? ((cur - p) / p) * 100 : 0);
    return {
      messageChange: pct(latest.messageCount, prev.messageCount),
      responseTimeChange: pct(latest.responseTime, prev.responseTime),
      satisfactionChange: pct(latest.userSatisfaction, prev.userSatisfaction),
      insightsChange: pct(latest.aiInsights, prev.aiInsights),
    };
  }, [processedData]);

  const StatCard = ({
    icon: Icon,
    title,
    value,
    change,
    suffix = "",
  }: {
    icon: any;
    title: string;
    value: number | string;
    change?: number;
    suffix?: string;
  }) => {
    const isUp = (change ?? 0) >= 0;
    return (
      <div className="flex items-center space-x-3 p-4 bg-muted/50 rounded-lg border">
        <div className="p-3 bg-primary/10 rounded-lg">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="flex items-center space-x-2">
            <span className="text-xl font-bold">
              {value}
              {suffix}
            </span>
            {typeof change === "number" && !Number.isNaN(change) && (
              <Badge variant={isUp ? "default" : "destructive"} className="text-xs">
                {isUp ? (
                  <TrendingUp className="h-3 w-3 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1" />
                )}
                {Math.abs(change).toFixed(1)}%
              </Badge>
            )}
          </div>
        </div>
      </div>
    );
  };

  /* --------------------------------- Render -------------------------------- */

  return (
    <Card className={`w-full ${className}`}>
      {/* SR status region */}
      <div id={statusRegionId} role="status" aria-live="polite" className="sr-only">
        {`Loaded ${processedData.length} points for ${selectedMetric} in ${timeframe}`}
      </div>

      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Analytics
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats */}
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
            <StatCard icon={Users} title="Active Users" value={stats.activeUsers} />
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between mt-6 flex-wrap gap-3">
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="detailed">Detailed</TabsTrigger>
              <TabsTrigger value="comparison">Comparison</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-2">
            <Select value={selectedMetric} onValueChange={(v) => setSelectedMetric(v as MetricType)}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Metric" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="messages">Messages</SelectItem>
                <SelectItem value="responseTime">Response Time</SelectItem>
                <SelectItem value="satisfaction">Satisfaction</SelectItem>
                <SelectItem value="insights">AI Insights</SelectItem>
                <SelectItem value="tokens">Token Usage</SelectItem>
                <SelectItem value="providers">LLM Providers</SelectItem>
              </SelectContent>
            </Select>

            <Select value={chartType} onValueChange={(v) => setChartType(v as ChartType)}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Chart Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="line">
                  <div className="flex items-center gap-2">
                    <LineChart className="h-4 w-4" />
                    Line
                  </div>
                </SelectItem>
                <SelectItem value="bar">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Bar
                  </div>
                </SelectItem>
                <SelectItem value="area">Area</SelectItem>
                <SelectItem value="scatter">Scatter</SelectItem>
                <SelectItem value="pie">
                  <div className="flex items-center gap-2">
                    <PieChart className="h-4 w-4" />
                    Pie
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={timeframe}
              onValueChange={(v) => onTimeframeChange?.(v as "1h" | "24h" | "7d" | "30d")}
            >
              <SelectTrigger className="w-28">
                <SelectValue placeholder="Timeframe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">1H</SelectItem>
                <SelectItem value="24h">24H</SelectItem>
                <SelectItem value="7d">7D</SelectItem>
                <SelectItem value="30d">30D</SelectItem>
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
                      title: { text: "Primary Metric" },
                    }}
                  />
                </div>
                <div className="h-[400px]">
                  <AgCharts
                    options={
                      {
                        data: processedData as any,
                        theme: "ag-default",
                        background: { fill: "transparent" },
                        title: { text: "Secondary Analysis" },
                        series: [
                          {
                            type: "line",
                            xKey: "formattedTime",
                            yKey: "userSatisfaction",
                            yName: "Satisfaction",
                            stroke: "#10b981",
                          } as any,
                        ],
                        axes: [
                          { type: "category", position: "bottom", title: { text: "Time" } },
                          { type: "number", position: "left", title: { text: "Satisfaction" } },
                        ],
                      } as AgChartOptions
                    }
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="comparison" className="mt-0">
            <div className="h-[500px] w-full p-6 sm:p-4 md:p-6">
              <AgCharts
                options={
                  {
                    data: processedData as any,
                    theme: "ag-default",
                    background: { fill: "transparent" },
                    title: { text: "Multi-Metric Comparison" },
                    series: [
                      {
                        type: "line",
                        xKey: "formattedTime",
                        yKey: "messageCount",
                        yName: "Messages",
                        stroke: "#3b82f6",
                      } as any,
                      {
                        type: "line",
                        xKey: "formattedTime",
                        yKey: "aiInsights",
                        yName: "AI Insights",
                        stroke: "#8b5cf6",
                      } as any,
                    ],
                    axes: [
                      { type: "category", position: "bottom", title: { text: "Time" } },
                      { type: "number", position: "left", title: { text: "Value" } },
                    ],
                  } as AgChartOptions
                }
              />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
