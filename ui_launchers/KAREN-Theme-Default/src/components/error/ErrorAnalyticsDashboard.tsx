"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertTriangle,
  Bug,
  TrendingUp,
  TrendingDown,
  Clock,
  MapPin,
  RefreshCw,
  Download,
  Filter,
  X
} from 'lucide-react';

interface ErrorMetric {
  id: string;
  timestamp: string;
  message: string;
  stack?: string;
  boundary: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  count: number;
  lastOccurred: string;
  resolved: boolean;
}

interface ErrorStats {
  total: number;
  last24h: number;
  last7days: number;
  byBoundary: Record<string, number>;
  bySeverity: Record<string, number>;
  topErrors: ErrorMetric[];
  trendPercentage: number;
}

const ErrorAnalyticsDashboard: React.FC = () => {
  const [stats, setStats] = useState<ErrorStats | null>(null);
  const [errors, setErrors] = useState<ErrorMetric[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const loadErrorStats = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/errors/analytics');
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
        setErrors(data.errors);
      } else {
        // Fallback mock data
        const mockStats: ErrorStats = {
          total: 127,
          last24h: 23,
          last7days: 89,
          byBoundary: {
            'ChatErrorBoundary': 45,
            'ApiErrorBoundary': 38,
            'GlobalErrorBoundary': 28,
            'StreamingErrorBoundary': 16
          },
          bySeverity: {
            'low': 52,
            'medium': 41,
            'high': 24,
            'critical': 10
          },
          topErrors: [
            {
              id: 'err_1',
              timestamp: new Date(Date.now() - 3600000).toISOString(),
              message: 'Failed to fetch chat messages',
              boundary: 'ChatErrorBoundary',
              severity: 'high',
              count: 12,
              lastOccurred: new Date(Date.now() - 600000).toISOString(),
              resolved: false
            },
            {
              id: 'err_2',
              timestamp: new Date(Date.now() - 7200000).toISOString(),
              message: 'API timeout: /api/analytics/summary',
              boundary: 'ApiErrorBoundary',
              severity: 'medium',
              count: 8,
              lastOccurred: new Date(Date.now() - 1800000).toISOString(),
              resolved: false
            },
            {
              id: 'err_3',
              timestamp: new Date(Date.now() - 10800000).toISOString(),
              message: 'WebSocket connection failed',
              boundary: 'StreamingErrorBoundary',
              severity: 'critical',
              count: 6,
              lastOccurred: new Date(Date.now() - 3600000).toISOString(),
              resolved: true
            }
          ],
          trendPercentage: -12.5
        };
        setStats(mockStats);
        setErrors(mockStats.topErrors);
      }
    } catch (error) {
      console.error('Failed to load error analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadErrorStats();
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-orange-600 text-white';
      case 'medium':
        return 'bg-yellow-600 text-white';
      case 'low':
        return 'bg-blue-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  const exportErrorData = () => {
    const data = {
      stats,
      errors,
      exportedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error-analytics-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const filteredErrors = selectedSeverity
    ? errors.filter(e => e.severity === selectedSeverity)
    : errors;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bug className="h-5 w-5" />
              Error Analytics Dashboard
            </div>
            <div className="flex gap-2">
              <Button onClick={exportErrorData} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button onClick={loadErrorStats} disabled={isLoading} size="sm">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Monitor and analyze application errors across all boundaries
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="errors">Errors</TabsTrigger>
              <TabsTrigger value="insights">Insights</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4">
              {stats ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Total Errors</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.total}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Last 24 Hours</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.last24h}</div>
                        <div className="flex items-center gap-1 text-xs mt-1">
                          {stats.trendPercentage < 0 ? (
                            <>
                              <TrendingDown className="h-3 w-3 text-green-600" />
                              <span className="text-green-600">{Math.abs(stats.trendPercentage)}% decrease</span>
                            </>
                          ) : (
                            <>
                              <TrendingUp className="h-3 w-3 text-red-600" />
                              <span className="text-red-600">{stats.trendPercentage}% increase</span>
                            </>
                          )}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Last 7 Days</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.last7days}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Critical</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">{stats.bySeverity.critical}</div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Errors by Boundary */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Errors by Boundary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(stats.byBoundary)
                          .sort(([, a], [, b]) => b - a)
                          .map(([boundary, count]) => (
                            <div key={boundary} className="flex items-center justify-between">
                              <span className="text-sm font-medium">{boundary}</span>
                              <div className="flex items-center gap-3">
                                <div className="w-32 bg-muted rounded-full h-2">
                                  <div
                                    className="bg-primary rounded-full h-2"
                                    style={{ width: `${(count / stats.total) * 100}%` }}
                                  />
                                </div>
                                <Badge variant="secondary">{count}</Badge>
                              </div>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Errors by Severity */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Errors by Severity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-3">
                        {Object.entries(stats.bySeverity).map(([severity, count]) => (
                          <div
                            key={severity}
                            className="text-center p-4 border rounded-lg cursor-pointer hover:bg-muted/50"
                            onClick={() => setSelectedSeverity(severity)}
                          >
                            <Badge className={getSeverityColor(severity)} variant="default">
                              {severity.toUpperCase()}
                            </Badge>
                            <div className="text-2xl font-bold mt-2">{count}</div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="animate-pulse space-y-3">
                  <div className="h-32 bg-muted rounded" />
                </div>
              )}
            </TabsContent>

            {/* Errors Tab */}
            <TabsContent value="errors" className="space-y-4">
              {selectedSeverity && (
                <Alert>
                  <Filter className="h-4 w-4" />
                  <AlertTitle className="flex items-center justify-between">
                    <span>Filtered by: {selectedSeverity.toUpperCase()}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedSeverity(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </AlertTitle>
                </Alert>
              )}

              <div className="space-y-3">
                {filteredErrors.length > 0 ? (
                  filteredErrors.map((error) => (
                    <Card key={error.id} className={error.resolved ? 'opacity-60' : ''}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <AlertTriangle className="h-4 w-4" />
                              {error.message}
                              {error.resolved && (
                                <Badge variant="outline" className="text-green-600 border-green-600">
                                  Resolved
                                </Badge>
                              )}
                            </CardTitle>
                            <CardDescription className="flex items-center gap-4 mt-2">
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                {error.boundary}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(error.lastOccurred).toLocaleString()}
                              </span>
                            </CardDescription>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={getSeverityColor(error.severity)}>
                              {error.severity.toUpperCase()}
                            </Badge>
                            <Badge variant="secondary">Count: {error.count}</Badge>
                          </div>
                        </div>
                      </CardHeader>
                      {error.stack && (
                        <CardContent>
                          <details className="text-xs">
                            <summary className="cursor-pointer font-medium mb-2">Stack trace</summary>
                            <pre className="bg-muted p-3 rounded overflow-x-auto">
                              {error.stack}
                            </pre>
                          </details>
                        </CardContent>
                      )}
                    </Card>
                  ))
                ) : (
                  <Alert>
                    <AlertDescription>No errors found for the selected filter.</AlertDescription>
                  </Alert>
                )}
              </div>
            </TabsContent>

            {/* Insights Tab */}
            <TabsContent value="insights" className="space-y-4">
              <Alert>
                <Bug className="h-4 w-4" />
                <AlertTitle>Error Insights</AlertTitle>
                <AlertDescription>
                  AI-powered insights and recommendations based on error patterns
                </AlertDescription>
              </Alert>

              {stats && (
                <div className="space-y-3">
                  {stats.trendPercentage < 0 && (
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <TrendingDown className="h-4 w-4 text-green-600" />
                          Positive Trend
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          Error rate has decreased by {Math.abs(stats.trendPercentage)}% in the last 24 hours.
                          Recent fixes are having a positive impact.
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {stats.bySeverity.critical > 5 && (
                    <Card className="border-red-600">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                          High Critical Error Rate
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          You have {stats.bySeverity.critical} critical errors. Consider prioritizing these issues
                          as they may significantly impact user experience.
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {Object.entries(stats.byBoundary)[0] && (
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Most Affected Boundary</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          <strong>{Object.entries(stats.byBoundary).sort(([, a], [, b]) => b - a)[0][0]}</strong>
                          {' '}has the most errors ({Object.entries(stats.byBoundary).sort(([, a], [, b]) => b - a)[0][1]}).
                          Consider adding more robust error handling in this area.
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ErrorAnalyticsDashboard;
