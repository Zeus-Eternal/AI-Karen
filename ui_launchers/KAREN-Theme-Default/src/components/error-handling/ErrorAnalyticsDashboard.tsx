// ui_launchers/KAREN-Theme-Default/src/components/error-handling/ErrorAnalyticsDashboard.tsx
/**
 * Error Analytics Dashboard
 *
 * Provides comprehensive error trend analysis, resolution tracking,
 * and performance impact visualization for production monitoring.
 */
"use client";

import React, { useState, useEffect, useMemo } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

import {
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  TrendingUp,
  BarChart3,
  PieChart,
  Activity,
  Download,
  Filter,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";

import type {
  ErrorAnalytics,
  ErrorAnalyticsReport,
} from "@/lib/error-handling/error-analytics";

export interface ErrorAnalyticsDashboardProps {
  analytics: ErrorAnalytics;
  refreshInterval?: number;
  enableRealTimeUpdates?: boolean;
}

export const ErrorAnalyticsDashboard: React.FC<ErrorAnalyticsDashboardProps> = ({
  analytics,
  refreshInterval = 30_000,
  enableRealTimeUpdates = true,
}) => {
  const [report, setReport] = useState<ErrorAnalyticsReport | null>(null);
  const [loading, setLoading] = useState(true);

  const [timeRange, setTimeRange] = useState<"1h" | "24h" | "7d" | "30d">(
    "24h"
  );
  const [selectedSeverity, setSelectedSeverity] = useState<
    "all" | "critical" | "high" | "medium" | "low"
  >("all");

  // Optional future use
  const [selectedSection, setSelectedSection] = useState<string>("all");

  // Fetch analytics report
  const fetchReport = async () => {
    try {
      setLoading(true);
      const analyticsReport = analytics.getAnalyticsReport({ timeRange });
      setReport(analyticsReport);
    } catch (error) {
      // Silently handled — ErrorBoundary above will catch render issues
      // eslint-disable-next-line no-console
      console.error("Error fetching analytics report:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
    if (enableRealTimeUpdates) {
      const interval = setInterval(fetchReport, refreshInterval);
      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshInterval, enableRealTimeUpdates, timeRange]);

  // Filtered aggregates
  const filteredData = useMemo(() => {
    if (!report) return null;

    let topErrors = report.topErrors;

    if (selectedSeverity !== "all") {
      topErrors = topErrors.filter((e) => e.severity === selectedSeverity);
    }

    if (selectedSection !== "all") {
      topErrors = topErrors.filter((e) => e.section === selectedSection);
    }

    return { ...report, topErrors };
  }, [report, selectedSeverity, selectedSection]);

  const handleExportReport = () => {
    if (!report) return;
    const exportData = analytics.exportAnalytics({ timeRange });
    const blob = new Blob([exportData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `error-analytics-${new Date()
      .toISOString()
      .split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <ErrorBoundary fallback={<div>Something went wrong in ErrorAnalyticsDashboard</div>}>
      {loading && !report ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Loading analytics...</span>
          </div>
        </div>
      ) : !report ? (
        <Card>
          <CardContent className="flex items-center justify-center h-64">
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">No analytics data available</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Error Analytics Dashboard</h2>
              <p className="text-muted-foreground">
                Trends, severity, sections, and performance impact — at a glance.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchReport}
                disabled={loading}
                aria-label="Refresh analytics"
              >
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportReport}
                aria-label="Export analytics JSON"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <span className="text-sm font-medium md:text-base lg:text-lg">
                Filters:
              </span>
            </div>

            {/* Time Range */}
            <Select
              value={timeRange}
              onValueChange={(v: "1h" | "24h" | "7d" | "30d") => setTimeRange(v)}
            >
              <SelectTrigger className="w-40" aria-label="Select time range">
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
              </SelectContent>
            </Select>

            {/* Severity */}
            <Select
              value={selectedSeverity}
              onValueChange={(v: "all" | "critical" | "high" | "medium" | "low") =>
                setSelectedSeverity(v)
              }
            >
              <SelectTrigger className="w-40" aria-label="Select severity">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            {/* Section (optional) */}
            <Select
              value={selectedSection}
              onValueChange={(v: string) => setSelectedSection(v)}
            >
              <SelectTrigger className="w-48" aria-label="Select section">
                <SelectValue placeholder="Section" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sections</SelectItem>
                {Object.keys(report.sectionBreakdown).map((k) => (
                  <SelectItem key={k} value={k}>
                    {k}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Total Errors
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {report.summary.totalErrors.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {report.summary.uniqueErrors} unique errors
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Resolution Rate
                </CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(report.summary.resolutionRate * 100).toFixed(1)}%
                </div>
                <Progress value={report.summary.resolutionRate * 100} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Avg Resolution Time
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(report.summary.averageResolutionTime / 1000)}s
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Average time to close across all severities
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Critical Errors
                </CardTitle>
                <XCircle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-destructive">
                  {report.summary.criticalErrors}
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Incidents tagged as critical
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <Tabs defaultValue="trends" className="space-y-4">
            <TabsList>
              <TabsTrigger value="trends">
                <TrendingUp className="w-4 h-4 mr-2" />
                Trends
              </TabsTrigger>
              <TabsTrigger value="errors">
                <BarChart3 className="w-4 h-4 mr-2" />
                Errors
              </TabsTrigger>
              <TabsTrigger value="sections">
                <PieChart className="w-4 h-4 mr-2" />
                Sections
              </TabsTrigger>
              <TabsTrigger value="performance">
                <Activity className="w-4 h-4 mr-2" />
                Performance
              </TabsTrigger>
            </TabsList>

            {/* Trends */}
            <TabsContent value="trends" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Error Trends</CardTitle>
                  <CardDescription>
                    Rolling windows for counts, uniqueness, and resolutions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {report.trends.length > 0 ? (
                    <div className="space-y-4">
                      {report.trends.slice(-12).map((trend) => (
                        <div
                          key={trend.period}
                          className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                        >
                          <div className="flex items-center gap-3">
                            <div className="text-sm font-medium md:text-base lg:text-lg">
                              {new Date(trend.period).toLocaleString()}
                            </div>
                            <Badge variant="outline">{trend.errorCount} errors</Badge>
                            <Badge variant="secondary">
                              {trend.uniqueErrors} unique
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {(trend.resolutionRate * 100).toFixed(1)}% resolved
                            </div>
                            <Progress value={trend.resolutionRate * 100} className="w-20" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No trend data available for this range.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Errors */}
            <TabsContent value="errors" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Top Errors</CardTitle>
                  <CardDescription>
                    Most frequent error signatures in the selected window
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {filteredData?.topErrors?.length ? (
                    <div className="space-y-3">
                      {filteredData.topErrors.map((err, index) => (
                        <div
                          key={`${err.message}-${index}`}
                          className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge
                                variant={
                                  err.severity === "critical"
                                    ? "destructive"
                                    : err.severity === "high"
                                    ? "destructive"
                                    : err.severity === "medium"
                                    ? "secondary"
                                    : "outline"
                                }
                              >
                                {err.severity}
                              </Badge>
                              {err.category && (
                                <Badge variant="outline">{err.category}</Badge>
                              )}
                              {err.section && (
                                <Badge variant="outline">{err.section}</Badge>
                              )}
                            </div>
                            <div className="text-sm font-medium truncate md:text-base lg:text-lg">
                              {err.message}
                            </div>
                            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              Last seen:{" "}
                              {new Date(err.lastOccurrence).toLocaleString()}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold">{err.count}</div>
                            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              occurrences
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No errors match current filters.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Sections */}
            <TabsContent value="sections" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Errors by Section</CardTitle>
                  <CardDescription>
                    Volume and resolution by UI surface / module
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(report.sectionBreakdown).map(([section, data]) => (
                      <div
                        key={section}
                        className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                      >
                        <div>
                          <div className="font-medium">{section}</div>
                          <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            {data.count} errors
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium md:text-base lg:text-lg">
                            {(data.resolutionRate * 100).toFixed(1)}% resolved
                          </div>
                          <Progress value={data.resolutionRate * 100} className="w-24 mt-1" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Performance */}
            <TabsContent value="performance" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Memory Impact</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {(
                        report.performanceImpact.averageMemoryIncrease /
                        1024 /
                        1024
                      ).toFixed(1)}
                      MB
                    </div>
                    <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                      Avg working set increase during error windows
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Render Delay</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {report.performanceImpact.averageRenderDelay.toFixed(0)}ms
                    </div>
                    <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                      Additional TTI/paint delay correlated with errors
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Network Error Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {(report.performanceImpact.networkErrorRate * 100).toFixed(1)}%
                    </div>
                    <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                      Of all errors are network-related
                    </p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </ErrorBoundary>
  );
};

export default ErrorAnalyticsDashboard;
