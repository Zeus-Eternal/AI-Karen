/**
 * Performance Dashboard Component
 * 
 * Displays real-time performance metrics and Core Web Vitals
 * for production monitoring and optimization.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Clock, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  Download,
  RefreshCw
} from 'lucide-react';
import { 
  getPerformanceMonitor, 
  trackCustomEvent, 
  PerformanceMetric, 
  CustomMetric 
} from '@/lib/performance/monitoring';

interface PerformanceDashboardProps {
  className?: string;
}

export function PerformanceDashboard({ className }: PerformanceDashboardProps) {
  const [metrics, setMetrics] = useState<{
    coreWebVitals: PerformanceMetric[];
    customMetrics: CustomMetric[];
  }>({ coreWebVitals: [], customMetrics: [] });
  
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const monitor = getPerformanceMonitor();
    if (monitor) {
      const updateMetrics = () => {
        const currentMetrics = monitor.getMetrics();
        setMetrics(currentMetrics);
        setLastUpdate(new Date());
      };

      // Initial load
      updateMetrics();

      // Update every 5 seconds
      const interval = setInterval(updateMetrics, 5000);

      return () => clearInterval(interval);
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    trackCustomEvent('dashboard-refresh', 1, 'count');
    
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const monitor = getPerformanceMonitor();
    if (monitor) {
      const currentMetrics = monitor.getMetrics();
      setMetrics(currentMetrics);
      setLastUpdate(new Date());
    }
    
    setIsRefreshing(false);
  };

  const handleExportReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      metrics: metrics,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    trackCustomEvent('report-export', 1, 'count');
  };

  const getMetricIcon = (name: string) => {
    switch (name) {
      case 'CLS': return <Activity className="h-4 w-4" />;
      case 'INP': return <Zap className="h-4 w-4" />;
      case 'FCP': return <Clock className="h-4 w-4" />;
      case 'LCP': return <Clock className="h-4 w-4" />;
      case 'TTFB': return <TrendingUp className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getMetricColor = (rating: string) => {
    switch (rating) {
      case 'good': return 'text-green-600';
      case 'needs-improvement': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getMetricBadgeVariant = (rating: string) => {
    switch (rating) {
      case 'good': return 'default';
      case 'needs-improvement': return 'secondary';
      case 'poor': return 'destructive';
      default: return 'outline';
    }
  };

  const formatMetricValue = (name: string, value: number) => {
    switch (name) {
      case 'CLS': return value.toFixed(3);
      case 'INP':
      case 'FID':
      case 'FCP':
      case 'LCP':
      case 'TTFB': return `${Math.round(value)}ms`;
      default: return value.toString();
    }
  };

  const getProgressValue = (name: string, value: number) => {
    // Convert metric to 0-100 scale for progress bar
    switch (name) {
      case 'CLS': return Math.max(0, 100 - (value * 400)); // 0.25 = 0%, 0 = 100%
      case 'INP':
      case 'FID': return Math.max(0, 100 - (value / 3)); // 300ms = 0%, 0ms = 100%
      case 'FCP': return Math.max(0, 100 - (value / 30)); // 3000ms = 0%, 0ms = 100%
      case 'LCP': return Math.max(0, 100 - (value / 40)); // 4000ms = 0%, 0ms = 100%
      case 'TTFB': return Math.max(0, 100 - (value / 18)); // 1800ms = 0%, 0ms = 100%
      default: return 50;
    }
  };

  const coreWebVitals = metrics.coreWebVitals.filter(metric => 
    ['CLS', 'INP', 'FCP', 'LCP', 'TTFB'].includes(metric.name)
  );

  const customPerformanceMetrics = metrics.customMetrics.filter(metric => 
    ['memory-used', 'long-task', 'time-on-page'].includes(metric.name)
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Performance Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time performance metrics and Core Web Vitals
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-sm text-muted-foreground">
        Last updated: {lastUpdate.toLocaleTimeString()}
      </div>

      {/* Core Web Vitals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            Core Web Vitals
          </CardTitle>
          <CardDescription>
            Essential user experience metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {coreWebVitals.map((metric) => (
              <div key={metric.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getMetricIcon(metric.name)}
                    <span className="font-medium">{metric.name}</span>
                  </div>
                  <Badge variant={getMetricBadgeVariant(metric.rating)}>
                    {metric.rating}
                  </Badge>
                </div>
                
                <div className={`text-2xl font-bold ${getMetricColor(metric.rating)}`}>
                  {formatMetricValue(metric.name, metric.value)}
                </div>
                
                <Progress 
                  value={getProgressValue(metric.name, metric.value)} 
                  className="h-2"
                />
                
                {metric.delta && (
                  <div className="text-xs text-muted-foreground">
                    Delta: {formatMetricValue(metric.name, metric.delta)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Custom Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            Custom Metrics
          </CardTitle>
          <CardDescription>
            Application-specific performance indicators
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {customPerformanceMetrics.map((metric) => (
              <div key={metric.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium capitalize">
                    {metric.name.replace('-', ' ')}
                  </span>
                  <Badge variant="outline">
                    {metric.unit}
                  </Badge>
                </div>
                
                <div className="text-xl font-bold">
                  {metric.name === 'memory-used' 
                    ? `${(metric.value / 1024 / 1024).toFixed(1)}MB`
                    : metric.name === 'time-on-page'
                    ? `${Math.round(metric.value / 1000)}s`
                    : `${Math.round(metric.value)}ms`
                  }
                </div>
                
                {metric.metadata && (
                  <div className="text-xs text-muted-foreground">
                    {Object.entries(metric.metadata).map(([key, value]) => (
                      <div key={key}>
                        {key}: {String(value)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckCircle className="h-5 w-5 mr-2" />
            Performance Summary
          </CardTitle>
          <CardDescription>
            Overall performance assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Overall Performance Score</span>
              <div className="flex items-center space-x-2">
                <div className="text-2xl font-bold">
                  {Math.round(
                    coreWebVitals.reduce((acc, metric) => {
                      const score = metric.rating === 'good' ? 100 : 
                                   metric.rating === 'needs-improvement' ? 50 : 0;
                      return acc + score;
                    }, 0) / Math.max(coreWebVitals.length, 1)
                  )}
                </div>
                <span className="text-muted-foreground">/100</span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>Good: {coreWebVitals.filter(m => m.rating === 'good').length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span>Needs Improvement: {coreWebVitals.filter(m => m.rating === 'needs-improvement').length}</span>
              </div>
              <div className="flex items-center space-x-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span>Poor: {coreWebVitals.filter(m => m.rating === 'poor').length}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default PerformanceDashboard;
