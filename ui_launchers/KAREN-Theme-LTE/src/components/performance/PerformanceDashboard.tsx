"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Clock, 
  Zap, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Download,
  RefreshCw
} from 'lucide-react';
import { usePerformanceStore, usePerformanceActions, usePerformanceMetrics, useCoreWebVitals, usePerformanceScores, useResourceUsage } from '@/stores';
import { cn, formatDate } from '@/lib/utils';

export default function PerformanceDashboard() {
  const metrics = usePerformanceMetrics();
  const coreWebVitals = useCoreWebVitals();
  const scores = usePerformanceScores();
  const resourceUsage = useResourceUsage();
  const { 
    startMonitoring, 
    stopMonitoring, 
    toggleMonitoring, 
    generateReport, 
    optimizePerformance,
    clearMetrics 
  } = usePerformanceActions();
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // Auto-refresh metrics
  useEffect(() => {
    const interval = setInterval(() => {
      // Trigger performance measurement
      if (typeof window !== 'undefined' && 'performance' in window) {
        // This would trigger the store's measurePerformance action
        const event = new CustomEvent('measurePerformance');
        window.dispatchEvent(event);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

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

  const getProgressColor = (rating: string) => {
    switch (rating) {
      case 'good': return 'bg-green-600';
      case 'needs-improvement': return 'bg-yellow-600';
      case 'poor': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    try {
      const report = generateReport();
      
      // Download report as JSON
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `performance-report-${formatDate(new Date())}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const overallScore = Math.round(
    (scores.performance + scores.accessibility + scores.bestPractices + scores.seo) / 4
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Performance Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time performance metrics and Core Web Vitals
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleMonitoring}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Toggle Monitoring
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={optimizePerformance}
            className="gap-2"
          >
            <Zap className="h-4 w-4" />
            Optimize
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={clearMetrics}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Clear Metrics
          </Button>
          
          <Button
            variant="default"
            size="sm"
            onClick={handleGenerateReport}
            disabled={isGeneratingReport}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {isGeneratingReport ? 'Generating...' : 'Download Report'}
          </Button>
        </div>
      </div>

      {/* Overall Performance Score */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Performance Score</CardTitle>
          <CardDescription>
            Combined score based on all performance metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn(
                "text-3xl font-bold",
                overallScore >= 90 ? "text-green-600" :
                overallScore >= 70 ? "text-yellow-600" :
                "text-red-600"
              )}>
                {overallScore}
              </div>
              <span className="text-muted-foreground">/100</span>
            </div>
            
            <Badge
              variant={overallScore >= 90 ? "default" : overallScore >= 70 ? "secondary" : "destructive"}
            >
              {overallScore >= 90 ? "Excellent" : 
               overallScore >= 70 ? "Good" : "Needs Improvement"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Core Web Vitals */}
      <Card>
        <CardHeader>
          <CardTitle>Core Web Vitals</CardTitle>
          <CardDescription>
            Essential metrics for user experience
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(coreWebVitals).map(([name, value]) => (
              <div key={name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getMetricIcon(name)}
                    <span className="font-medium">{name}</span>
                  </div>
                  <span className={cn(
                    "text-sm font-mono",
                    name === 'CLS' ? getMetricColor(
                      value <= 0.1 ? 'good' : value <= 0.25 ? 'needs-improvement' : 'poor'
                    ) :
                    name === 'FID' || name === 'INP' ? getMetricColor(
                      value <= 100 ? 'good' : value <= 300 ? 'needs-improvement' : 'poor'
                    ) :
                    name === 'FCP' ? getMetricColor(
                      value <= 1800 ? 'good' : value <= 3000 ? 'needs-improvement' : 'poor'
                    ) :
                    getMetricColor(
                      value <= 2500 ? 'good' : value <= 4000 ? 'needs-improvement' : 'poor'
                    )
                  )}>
                    {name === 'CLS' ? value.toFixed(3) : `${Math.round(value)}ms`}
                  </span>
                </div>
                
                <Progress
                  value={name === 'CLS' ? 
                    Math.max(0, 100 - (value * 400)) : 
                    Math.max(0, 100 - (value / 3))
                  }
                  className="h-2"
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>
            Detailed performance measurements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {metrics.map((metric, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getMetricIcon(metric.name)}
                  <div>
                    <div className="font-medium">{metric.name}</div>
                    {metric.delta && (
                      <div className="text-sm text-muted-foreground">
                        Delta: {metric.name === 'CLS' ? metric.delta.toFixed(3) : `${Math.round(metric.delta)}ms`}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge
                    variant={metric.rating === 'good' ? 'default' : 
                             metric.rating === 'needs-improvement' ? 'secondary' : 'destructive'}
                  >
                    {metric.rating}
                  </Badge>
                  <div className={cn(
                    "text-2xl font-bold",
                    getMetricColor(metric.rating)
                  )}>
                    {metric.name === 'CLS' ? metric.value.toFixed(3) : `${Math.round(metric.value)}ms`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Resource Usage */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Usage</CardTitle>
          <CardDescription>
            Current system resource consumption
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Memory</span>
                <span className="text-sm font-mono">{resourceUsage.memory}MB</span>
              </div>
              <Progress
                value={Math.min(100, (resourceUsage.memory / 512) * 100)} // Assuming 512MB as max
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">CPU</span>
                <span className="text-sm font-mono">{resourceUsage.cpu}%</span>
              </div>
              <Progress
                value={resourceUsage.cpu}
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Network</span>
                <span className="text-sm font-mono">{resourceUsage.network}KB/s</span>
              </div>
              <Progress
                value={Math.min(100, (resourceUsage.network / 1024) * 100)} // Assuming 1MB/s as max
                className="h-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Performance Categories</CardTitle>
            <CardDescription>
              Scores by category
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(scores).map(([category, score]) => (
                <div key={category} className="flex items-center justify-between">
                  <span className="capitalize">{category.replace(/([A-Z])/g, ' $1').trim()}</span>
                  <div className="flex items-center gap-2">
                    <Progress value={score} className="h-2 w-20" />
                    <span className="text-sm font-mono">{score}/100</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status Indicators</CardTitle>
            <CardDescription>
              Current system status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>Service Worker Active</span>
              </div>
              
              <div className="flex items-center gap-2">
                {overallScore >= 70 ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                )}
                <span>Performance {overallScore >= 70 ? 'Good' : 'Needs Attention'}</span>
              </div>
              
              <div className="flex items-center gap-2">
                {resourceUsage.memory < 200 ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-600" />
                )}
                <span>Memory {resourceUsage.memory < 200 ? 'Optimal' : 'High'}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}