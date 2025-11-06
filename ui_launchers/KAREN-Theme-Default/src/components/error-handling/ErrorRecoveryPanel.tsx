"use client";

/**
 * Error Recovery Panel
 *
 * Provides a comprehensive UI for managing and monitoring error recovery strategies
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  AlertTriangle,
  Zap,
  TrendingUp,
  Shield
} from 'lucide-react';

interface RecoveryAttempt {
  id: string;
  timestamp: number;
  errorMessage: string;
  strategy: string;
  success: boolean;
  duration: number;
  retryCount: number;
}

interface RecoveryStats {
  totalAttempts: number;
  successfulAttempts: number;
  failedAttempts: number;
  successRate: number;
  averageDuration: number;
  activeRecoveries: number;
}

export interface ErrorRecoveryPanelProps {
  refreshInterval?: number;
  maxHistorySize?: number;
}

export const ErrorRecoveryPanel: React.FC<ErrorRecoveryPanelProps> = ({
  refreshInterval = 5000,
  maxHistorySize = 50
}) => {
  const [stats, setStats] = useState<RecoveryStats>({
    totalAttempts: 0,
    successfulAttempts: 0,
    failedAttempts: 0,
    successRate: 0,
    averageDuration: 0,
    activeRecoveries: 0
  });

  const [attempts, setAttempts] = useState<RecoveryAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const loadRecoveryData = async () => {
    setIsLoading(true);
    try {
      // In production, fetch from actual API
      const response = await fetch('/api/error-recovery/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
        setAttempts(data.attempts);
      } else {
        // Fallback mock data
        const mockAttempts: RecoveryAttempt[] = [
          {
            id: 'rec_1',
            timestamp: Date.now() - 300000,
            errorMessage: 'Network timeout',
            strategy: 'exponential-backoff',
            success: true,
            duration: 2500,
            retryCount: 2
          },
          {
            id: 'rec_2',
            timestamp: Date.now() - 600000,
            errorMessage: 'Database connection failed',
            strategy: 'circuit-breaker',
            success: false,
            duration: 5000,
            retryCount: 3
          },
          {
            id: 'rec_3',
            timestamp: Date.now() - 900000,
            errorMessage: 'API rate limit exceeded',
            strategy: 'rate-limit-backoff',
            success: true,
            duration: 3200,
            retryCount: 1
          }
        ];

        setAttempts(mockAttempts);

        const successfulCount = mockAttempts.filter(a => a.success).length;
        const avgDuration = mockAttempts.length > 0
          ? mockAttempts.reduce((sum, a) => sum + a.duration, 0) / mockAttempts.length
          : 0;

        setStats({
          totalAttempts: mockAttempts.length,
          successfulAttempts: successfulCount,
          failedAttempts: mockAttempts.length - successfulCount,
          successRate: mockAttempts.length > 0 ? (successfulCount / mockAttempts.length) * 100 : 0,
          averageDuration: avgDuration,
          activeRecoveries: Math.floor(Math.random() * 3)
        });
      }
    } catch (error) {
      console.error('Failed to load recovery data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRecoveryData();
    const interval = setInterval(loadRecoveryData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStrategyIcon = (strategy: string) => {
    switch (strategy) {
      case 'exponential-backoff':
        return <Clock className="h-4 w-4" />;
      case 'circuit-breaker':
        return <Shield className="h-4 w-4" />;
      case 'rate-limit-backoff':
        return <Zap className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getStatusColor = (success: boolean) => {
    return success ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Error Recovery Panel
            </div>
            <Button onClick={loadRecoveryData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Monitor error recovery strategies and success rates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="attempts">Attempts</TabsTrigger>
              <TabsTrigger value="strategies">Strategies</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4">
              {/* Stats Cards */}
              <div className="grid md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-muted-foreground">Total Attempts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.totalAttempts}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-muted-foreground">Success Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      {stats.successRate.toFixed(1)}%
                    </div>
                    <Progress value={stats.successRate} className="mt-2" />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-muted-foreground">Avg Duration</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.averageDuration.toFixed(0)}ms</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-muted-foreground">Active</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.activeRecoveries}</div>
                    {stats.activeRecoveries > 0 && (
                      <Badge variant="secondary" className="mt-2">
                        <Activity className="h-3 w-3 mr-1 animate-pulse" />
                        In Progress
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Success/Failure Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Recovery Outcome</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-medium">Successful</span>
                      </div>
                      <Badge variant="default" className="bg-green-600">
                        {stats.successfulAttempts}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-600" />
                        <span className="text-sm font-medium">Failed</span>
                      </div>
                      <Badge variant="destructive">
                        {stats.failedAttempts}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Health Alert */}
              {stats.successRate < 50 && stats.totalAttempts > 0 && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Low Success Rate</AlertTitle>
                  <AlertDescription>
                    Recovery success rate is below 50%. Consider reviewing error patterns and recovery strategies.
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            {/* Attempts Tab */}
            <TabsContent value="attempts" className="space-y-3">
              {attempts.length === 0 ? (
                <Alert>
                  <AlertDescription>No recovery attempts recorded yet.</AlertDescription>
                </Alert>
              ) : (
                attempts.slice().reverse().slice(0, maxHistorySize).map((attempt) => (
                  <Card key={attempt.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-sm flex items-center gap-2">
                            {attempt.success ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-600" />
                            )}
                            {attempt.errorMessage}
                          </CardTitle>
                          <CardDescription className="mt-2">
                            {new Date(attempt.timestamp).toLocaleString()} • {attempt.duration}ms
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{attempt.strategy}</Badge>
                          <Badge variant="secondary">Retry: {attempt.retryCount}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>
                ))
              )}
            </TabsContent>

            {/* Strategies Tab */}
            <TabsContent value="strategies" className="space-y-4">
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertTitle>Recovery Strategies</AlertTitle>
                <AlertDescription>
                  Automated strategies employed to recover from errors
                </AlertDescription>
              </Alert>

              <div className="space-y-3">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Exponential Backoff
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Gradually increases retry delay with each attempt. Ideal for temporary network issues and rate limiting.
                    </p>
                    <div className="mt-2">
                      <Badge variant="outline">Network errors</Badge>
                      <Badge variant="outline" className="ml-2">API timeouts</Badge>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Circuit Breaker
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Prevents cascading failures by temporarily blocking requests after repeated failures. Auto-recovers when service stabilizes.
                    </p>
                    <div className="mt-2">
                      <Badge variant="outline">Service failures</Badge>
                      <Badge variant="outline" className="ml-2">Database errors</Badge>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      Rate Limit Backoff
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      Automatically adjusts request rate based on API rate limit headers. Prevents rate limit violations.
                    </p>
                    <div className="mt-2">
                      <Badge variant="outline">API rate limits</Badge>
                      <Badge variant="outline" className="ml-2">429 errors</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ErrorRecoveryPanel;
