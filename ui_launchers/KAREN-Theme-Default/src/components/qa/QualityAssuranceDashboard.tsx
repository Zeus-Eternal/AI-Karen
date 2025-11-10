"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { enhancedApiClient } from '@/lib/enhanced-api-client';

import {
  AlertTriangle,
  Bug,
  CheckCircle,
  Download,
  Eye,
  RefreshCw,
  Shield,
  Target,
  TrendingDown,
  TrendingUp,
  XCircle,
} from 'lucide-react';
export interface QualityMetrics {
  testCoverage: {
    unit: number;
    integration: number;
    e2e: number;
    visual: number;
    overall: number;
  };
  testResults: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    flaky: number;
  };
  performance: {
    loadTime: number;
    interactionTime: number;
    memoryUsage: number;
    errorRate: number;
  };
  accessibility: {
    score: number;
    violations: number;
    warnings: number;
    passes: number;
  };
  security: {
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    score: number;
  };
  codeQuality: {
    maintainabilityIndex: number;
    technicalDebt: number;
    duplicateCode: number;
    complexity: number;
  };
}
export interface QualityTrend {
  date: string;
  coverage: number;
  passRate: number;
  performance: number;
  accessibility: number;
  security: number;
}
export interface QualityGate {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'warning';
  threshold: number;
  actual: number;
  description: string;
}

interface QualityGateSummary {
  overallScore: number;
  coverage?: number;
  passRate?: number;
  accessibility?: number;
  security?: number;
  maintainability?: number;
}

interface QualityGatesApiResponse {
  success?: boolean;
  generated_at?: string;
  gates?: QualityGate[];
  metrics_summary?: QualityGateSummary;
  overrides?: Record<string, unknown>;
}
export function QualityAssuranceDashboard() {
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
  const [trends, setTrends] = useState<QualityTrend[]>([]);
  const [qualityGates, setQualityGates] = useState<QualityGate[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [qualityGateSummary, setQualityGateSummary] = useState<QualityGateSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadQualityMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [metricsResult, trendsResult, gatesResult] = await Promise.allSettled([
        enhancedApiClient.get<QualityMetrics>('/api/qa/metrics', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
        enhancedApiClient.get<QualityTrend[]>('/api/qa/trends', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
        enhancedApiClient.get<QualityGatesApiResponse>('/api/qa/quality-gates', {
          headers: { 'Cache-Control': 'no-cache' },
        }),
      ]);

      let errorMessage: string | null = null;
      let updatedAt: Date | null = null;

      if (metricsResult.status === 'fulfilled') {
        setMetrics(metricsResult.value.data);
        updatedAt = new Date();
      } else {
        console.error('Failed to load quality metrics:', metricsResult.reason);
        setMetrics(null);
        errorMessage = 'Failed to load quality metrics.';
      }

      if (trendsResult.status === 'fulfilled') {
        const trendPayload = trendsResult.value.data;
        setTrends(Array.isArray(trendPayload) ? trendPayload : []);
      } else {
        console.error('Failed to load quality trends:', trendsResult.reason);
        setTrends([]);
      }

      if (gatesResult.status === 'fulfilled') {
        const gatesPayload = gatesResult.value.data;
        const gates = Array.isArray(gatesPayload)
          ? gatesPayload
          : gatesPayload?.gates ?? [];
        setQualityGates(gates);
        if (!Array.isArray(gatesPayload) && gatesPayload && typeof gatesPayload === 'object') {
          setQualityGateSummary(gatesPayload.metrics_summary ?? null);
        } else {
          setQualityGateSummary(null);
        }
      } else {
        console.error('Failed to load quality gates:', gatesResult.reason);
        setQualityGates([]);
        setQualityGateSummary(null);
        if (!errorMessage) {
          errorMessage = 'Failed to load quality gate information.';
        }
      }

      if (updatedAt) {
        setLastUpdated(updatedAt);
      }

      if (errorMessage) {
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Unexpected quality metrics error:', err);
      setMetrics(null);
      setTrends([]);
      setQualityGates([]);
      setQualityGateSummary(null);
      setError('Unable to refresh quality assurance data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQualityMetrics();
    const interval = setInterval(loadQualityMetrics, 300000); // Update every 5 minutes
    return () => clearInterval(interval);
  }, [loadQualityMetrics]);
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 " />;
      case 'failed': return <XCircle className="h-4 w-4 " />;
      case 'warning': return <AlertTriangle className="h-4 w-4 " />;
      default: return null;
    }
  };
  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) {
      return <TrendingUp className="h-4 w-4 text-green-600 " />;
    } else if (current < previous) {
      return <TrendingDown className="h-4 w-4 text-red-600 " />;
    }
    return null;
  };
  const exportReport = async () => {
    try {
      const response = await fetch('/api/qa/export-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format: 'pdf', includeCharts: true })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qa-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to export report:', error);
    }
  };
  if (loading) {
    return (
      <ErrorBoundary fallback={({ error }) => <div>Something went wrong in QualityAssuranceDashboard: {error?.message}</div>}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin " />
          <span className="ml-2">Loading quality metrics...</span>
        </div>
      </ErrorBoundary>
    );
  }
  if (!metrics) {
    return (
      <ErrorBoundary fallback={({ error }) => <div>Something went wrong in QualityAssuranceDashboard: {error?.message}</div>}>
        <Alert variant="destructive" className="mx-auto w-full max-w-2xl">
          <AlertTitle>Quality Metrics Unavailable</AlertTitle>
          <AlertDescription>
            {error ?? 'Quality assurance metrics could not be retrieved. Please try refreshing the page.'}
          </AlertDescription>
        </Alert>
      </ErrorBoundary>
    );
  }
  const overallQualityScore = qualityGateSummary?.overallScore ?? Math.round(
    (metrics.testCoverage.overall +
     (metrics.testResults.passed / Math.max(metrics.testResults.total, 1) * 100) +
     metrics.accessibility.score +
     metrics.security.score +
     metrics.codeQuality.maintainabilityIndex) / 5
  );
  return (
    <div className="space-y-6" data-testid="qa-dashboard">
      {error && (
        <Alert variant="destructive" data-testid="qa-error">
          <AlertTitle>Data refresh issue</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Quality Assurance Dashboard</h1>
          <p className="text-muted-foreground">
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={loadQualityMetrics} disabled={loading} >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" onClick={exportReport} >
            <Download className="h-4 w-4 mr-2 " />
          </Button>
        </div>
      </div>
      {/* Overall Quality Score */}
      <Card data-testid="overall-quality-score">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2 " />
          </CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="text-4xl font-bold">
              {overallQualityScore}%
            </div>
            <div className="flex-1">
              <Progress value={overallQualityScore} className="h-3" />
            </div>
            <Badge variant={overallQualityScore >= 80 ? 'default' : overallQualityScore >= 60 ? 'secondary' : 'destructive'}>
              {overallQualityScore >= 80 ? 'Excellent' : overallQualityScore >= 60 ? 'Good' : 'Needs Improvement'}
            </Badge>
          </div>
          {lastUpdated && (
            <p className="text-sm text-muted-foreground mt-2 md:text-base lg:text-lg">
              Last updated: {lastUpdated.toLocaleString()}
            </p>
          )}
        </CardContent>
      </Card>
      {/* Quality Gates */}
      <Card data-testid="quality-gates">
        <CardHeader>
          <CardTitle>Quality Gates</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {qualityGates.map((gate) => (
              <div
                key={gate.id}
                className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                data-testid={`quality-gate-${gate.id}`}
              >
                <div className="flex items-center space-x-2">
                  <span className={getStatusColor(gate.status)}>
                    {getStatusIcon(gate.status)}
                  </span>
                  <div>
                    <p className="font-medium">{gate.name}</p>
                    <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                      {gate.actual}% (min: {gate.threshold}%)
                    </p>
                  </div>
                </div>
                <Badge variant={gate.status === 'passed' ? 'default' : gate.status === 'warning' ? 'secondary' : 'destructive'}>
                  {gate.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      {/* Detailed Metrics Tabs */}
      <Tabs defaultValue="testing" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="testing">Testing</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="accessibility">Accessibility</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="code-quality">Code Quality</TabsTrigger>
        </TabsList>
        {/* Testing Tab */}
        <TabsContent value="testing" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Test Coverage */}
            <Card data-testid="test-coverage-card">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Eye className="h-4 w-4 mr-2 " />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Unit Tests</span>
                    <span>{metrics.testCoverage.unit}%</span>
                  </div>
                  <Progress value={metrics.testCoverage.unit} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Integration Tests</span>
                    <span>{metrics.testCoverage.integration}%</span>
                  </div>
                  <Progress value={metrics.testCoverage.integration} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>E2E Tests</span>
                    <span>{metrics.testCoverage.e2e}%</span>
                  </div>
                  <Progress value={metrics.testCoverage.e2e} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Visual Tests</span>
                    <span>{metrics.testCoverage.visual}%</span>
                  </div>
                  <Progress value={metrics.testCoverage.visual} />
                </div>
                <div className="pt-2 border-t">
                  <div className="flex justify-between font-semibold">
                    <span>Overall Coverage</span>
                    <span>{metrics.testCoverage.overall}%</span>
                  </div>
                  <Progress value={metrics.testCoverage.overall} className="mt-2" />
                </div>
              </CardContent>
            </Card>
            {/* Test Results */}
            <Card data-testid="test-results-card">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="h-4 w-4 mr-2 " />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {metrics.testResults.passed}
                    </div>
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Passed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {metrics.testResults.failed}
                    </div>
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {metrics.testResults.skipped}
                    </div>
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Skipped</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {metrics.testResults.flaky}
                    </div>
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Flaky</div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t">
                  <div className="flex justify-between items-center">
                    <span>Pass Rate</span>
                    <span className="font-semibold">
                      {Math.round((metrics.testResults.passed / metrics.testResults.total) * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={(metrics.testResults.passed / metrics.testResults.total) * 100} 
                    className="mt-2"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card data-testid="load-time-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Load Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.performance.loadTime}ms</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Average page load</p>
              </CardContent>
            </Card>
            <Card data-testid="interaction-time-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Interaction Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.performance.interactionTime}ms</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Average response time</p>
              </CardContent>
            </Card>
            <Card data-testid="memory-usage-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Memory Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.performance.memoryUsage}MB</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Peak memory usage</p>
              </CardContent>
            </Card>
            <Card data-testid="error-rate-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Error Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.performance.errorRate}%</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Request error rate</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        {/* Accessibility Tab */}
        <TabsContent value="accessibility" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card data-testid="accessibility-score-card">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="h-4 w-4 mr-2 " />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold mb-2">{metrics.accessibility.score}%</div>
                  <Progress value={metrics.accessibility.score} className="mb-4" />
                  <Badge variant={metrics.accessibility.score >= 90 ? 'default' : 'secondary'}>
                    WCAG 2.1 {metrics.accessibility.score >= 90 ? 'AA' : 'Partial'} Compliance
                  </Badge>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="accessibility-issues-card">
              <CardHeader>
                <CardTitle>Accessibility Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="flex items-center">
                      <XCircle className="h-4 w-4 mr-2 text-red-600 " />
                    </span>
                    <Badge variant="destructive">{metrics.accessibility.violations}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center">
                      <AlertTriangle className="h-4 w-4 mr-2 text-yellow-600 " />
                    </span>
                    <Badge variant="secondary">{metrics.accessibility.warnings}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="flex items-center">
                      <CheckCircle className="h-4 w-4 mr-2 text-green-600 " />
                    </span>
                    <Badge variant="default">{metrics.accessibility.passes}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card data-testid="security-score-card">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="h-4 w-4 mr-2 " />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold mb-2">{metrics.security.score}%</div>
                  <Progress value={metrics.security.score} className="mb-4" />
                  <Badge variant={metrics.security.score >= 80 ? 'default' : 'destructive'}>
                    {metrics.security.score >= 80 ? 'Secure' : 'Needs Attention'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="vulnerabilities-card">
              <CardHeader>
                <CardTitle>Vulnerabilities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Critical</span>
                    <Badge variant="destructive">{metrics.security.vulnerabilities.critical}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>High</span>
                    <Badge variant="destructive">{metrics.security.vulnerabilities.high}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Medium</span>
                    <Badge variant="secondary">{metrics.security.vulnerabilities.medium}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Low</span>
                    <Badge variant="outline">{metrics.security.vulnerabilities.low}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        {/* Code Quality Tab */}
        <TabsContent value="code-quality" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card data-testid="maintainability-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Maintainability</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.codeQuality.maintainabilityIndex}%</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Maintainability index</p>
              </CardContent>
            </Card>
            <Card data-testid="technical-debt-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Technical Debt</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.codeQuality.technicalDebt}h</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Estimated debt</p>
              </CardContent>
            </Card>
            <Card data-testid="duplicate-code-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Duplicate Code</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.codeQuality.duplicateCode}%</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Code duplication</p>
              </CardContent>
            </Card>
            <Card data-testid="complexity-metric">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Complexity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.codeQuality.complexity}</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Cyclomatic complexity</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      {/* Alerts */}
      {qualityGates.some(gate => gate.status === 'failed') && (
        <Alert variant="destructive" data-testid="quality-gate-failures">
          <Bug className="h-4 w-4 " />
          <AlertTitle>Quality Gate Failures</AlertTitle>
          <AlertDescription>
            Some quality gates are failing. Review the issues above and address them before deployment.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
