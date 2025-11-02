/**
 * Error Analytics Dashboard
 * 
 * Provides comprehensive error trend analysis, resolution tracking,
 * and performance impact visualization for production monitoring.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  CheckCircle, 
  XCircle,
  BarChart3,
  PieChart,
  Activity,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Progress } from '../ui/progress';
import { ErrorAnalytics, ErrorAnalyticsReport } from '../../lib/error-handling/error-analytics';
interface ErrorAnalyticsDashboardProps {
  analytics: ErrorAnalytics;
  refreshInterval?: number;
  enableRealTimeUpdates?: boolean;
}
export const ErrorAnalyticsDashboard: React.FC<ErrorAnalyticsDashboardProps> = ({
  analytics,
  refreshInterval = 30000,
  enableRealTimeUpdates = true
}) => {
  const [report, setReport] = useState<ErrorAnalyticsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedSection, setSelectedSection] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  // Fetch analytics report
  const fetchReport = async () => {
    try {
      setLoading(true);
      const analyticsReport = analytics.getAnalyticsReport();
      setReport(analyticsReport);
    } catch (error) {
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
  }, [refreshInterval, enableRealTimeUpdates]);
  // Filter data based on selected filters
  const filteredData = useMemo(() => {
    if (!report) return null;
    let filteredErrors = report.topErrors;
    if (selectedSeverity !== 'all') {
      filteredErrors = filteredErrors.filter(error => error.severity === selectedSeverity);
    }
    return {
      ...report,
      topErrors: filteredErrors
    };
  }, [report, selectedSeverity]);
  const handleExportReport = () => {
    if (!report) return;
    const exportData = analytics.exportAnalytics();
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error-analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  if (loading && !report) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in ErrorAnalyticsDashboard</div>}>
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin sm:w-auto md:w-full" />
          <span>Loading analytics...</span>
        </div>
      </div>
    );
  }
  if (!report) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="w-8 h-8 text-muted-foreground mx-auto mb-2 sm:w-auto md:w-full" />
            <p className="text-muted-foreground">No analytics data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Error Analytics Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor error trends, resolution rates, and performance impact
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button variant="outline" size="sm" onClick={fetchReport} disabled={loading} aria-label="Button">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <button variant="outline" size="sm" onClick={handleExportReport} aria-label="Button">
            <Download className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Export
          </Button>
        </div>
      </div>
      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 sm:w-auto md:w-full" />
          <span className="text-sm font-medium md:text-base lg:text-lg">Filters:</span>
        </div>
        <select value={timeRange} onValueChange={(value: any) = aria-label="Select option"> setTimeRange(value)}>
          <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
            <selectValue />
          </SelectTrigger>
          <selectContent aria-label="Select option">
            <selectItem value="1h" aria-label="Select option">Last Hour</SelectItem>
            <selectItem value="24h" aria-label="Select option">Last 24h</SelectItem>
            <selectItem value="7d" aria-label="Select option">Last 7 days</SelectItem>
            <selectItem value="30d" aria-label="Select option">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
        <select value={selectedSeverity} onValueChange={setSelectedSeverity} aria-label="Select option">
          <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
            <selectValue />
          </SelectTrigger>
          <selectContent aria-label="Select option">
            <selectItem value="all" aria-label="Select option">All Severity</SelectItem>
            <selectItem value="critical" aria-label="Select option">Critical</SelectItem>
            <selectItem value="high" aria-label="Select option">High</SelectItem>
            <selectItem value="medium" aria-label="Select option">Medium</SelectItem>
            <selectItem value="low" aria-label="Select option">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Total Errors</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{report.summary.totalErrors.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {report.summary.uniqueErrors} unique errors
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Resolution Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(report.summary.resolutionRate * 100).toFixed(1)}%
            </div>
            <Progress 
              value={report.summary.resolutionRate * 100} 
              className="mt-2"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Avg Resolution Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(report.summary.averageResolutionTime / 1000)}s
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Average time to resolve
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Critical Errors</CardTitle>
            <XCircle className="h-4 w-4 text-destructive sm:w-auto md:w-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {report.summary.criticalErrors}
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Require immediate attention
            </p>
          </CardContent>
        </Card>
      </div>
      {/* Main Content */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">
            <TrendingUp className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Trends
          </TabsTrigger>
          <TabsTrigger value="errors">
            <BarChart3 className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Top Errors
          </TabsTrigger>
          <TabsTrigger value="sections">
            <PieChart className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            By Section
          </TabsTrigger>
          <TabsTrigger value="performance">
            <Activity className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Performance Impact
          </TabsTrigger>
        </TabsList>
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Error Trends</CardTitle>
              <CardDescription>
                Error frequency and resolution patterns over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report.trends.length > 0 ? (
                <div className="space-y-4">
                  {report.trends.slice(-12).map((trend, index) => (
                    <div key={trend.period} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
                      <div className="flex items-center gap-3">
                        <div className="text-sm font-medium md:text-base lg:text-lg">
                          {new Date(trend.period).toLocaleString()}
                        </div>
                        <Badge variant="outline">
                          {trend.errorCount} errors
                        </Badge>
                        <Badge variant="secondary">
                          {trend.uniqueErrors} unique
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {(trend.resolutionRate * 100).toFixed(1)}% resolved
                        </div>
                        <Progress 
                          value={trend.resolutionRate * 100} 
                          className="w-20 sm:w-auto md:w-full"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No trend data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Errors</CardTitle>
              <CardDescription>
                Most frequent errors and their resolution status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredData?.topErrors.map((error, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
                    <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={
                          error.severity === 'critical' ? 'destructive' :
                          error.severity === 'high' ? 'destructive' :
                          error.severity === 'medium' ? 'secondary' : 'outline'
                        }>
                          {error.severity}
                        </Badge>
                        <Badge variant="outline">
                          {error.category}
                        </Badge>
                      </div>
                      <div className="text-sm font-medium truncate md:text-base lg:text-lg">
                        {error.message}
                      </div>
                      <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        Last seen: {new Date(error.lastOccurrence).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">
                        {error.count}
                      </div>
                      <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        occurrences
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="sections" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Errors by Section</CardTitle>
              <CardDescription>
                Error distribution and resolution rates across application sections
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(report.sectionBreakdown).map(([section, data]) => (
                  <div key={section} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
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
                      <Progress 
                        value={data.resolutionRate * 100} 
                        className="w-24 mt-1 sm:w-auto md:w-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Memory Impact</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(report.performanceImpact.averageMemoryIncrease / 1024 / 1024).toFixed(1)}MB
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Average memory increase per error
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
                  Average render delay
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
    </ErrorBoundary>
  );
};
export default ErrorAnalyticsDashboard;
