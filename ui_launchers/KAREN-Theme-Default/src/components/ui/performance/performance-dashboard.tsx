
"use client";
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { usePerformanceMonitor, checkPerformanceBudget } from '@/utils/performance-monitor';

export interface PerformanceDashboardProps {
  className?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  className = '',
  showDetails = true,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const { isMonitoring, metrics, getPerformanceSummary } = usePerformanceMonitor();
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);
  const [recentMetrics, setRecentMetrics] = useState<(WebVitalsMetric | CustomMetric)[]>([]);

  useEffect(() => {
    const updateSummary = () => {
      setSummary(getPerformanceSummary());
    };

    updateSummary();

    if (autoRefresh) {
      const interval = setInterval(updateSummary, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [getPerformanceSummary, autoRefresh, refreshInterval]);

  if (!isMonitoring || !summary) {
    return (
      <div className={`p-4 bg-muted rounded-lg ${className}`}>
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Activity className="h-4 w-4 " />
          <span>Performance monitoring not available</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-primary " />
          <h2 className="text-lg font-semibold">Performance Dashboard</h2>
        </div>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground md:text-base lg:text-lg">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse " />
            <span>Monitoring Active</span>
          </div>
        </div>
      </div>

      {/* Web Vitals Overview */}
      <WebVitalsOverview summary={summary} />

      {/* Custom Metrics */}
      {showDetails && (
        <>
          <CustomMetricsSection metrics={summary.customMetrics} />
          <ResourceTimingSection resourceTiming={summary.resourceTiming} />
          <NavigationTimingSection navigationTiming={summary.navigationTiming} />
        </>
      )}

      {/* Recent Alerts */}
      <PerformanceAlerts metrics={recentMetrics} />
    </div>
  );
};

const WebVitalsOverview: React.FC<{ summary: PerformanceSummary }> = ({ summary }) => {
  const webVitalsMetrics = [
    { name: 'LCP', label: 'Largest Contentful Paint', unit: 'ms', icon: Zap },
    { name: 'FID', label: 'First Input Delay', unit: 'ms', icon: Clock },
    { name: 'CLS', label: 'Cumulative Layout Shift', unit: '', icon: TrendingUp },
    { name: 'FCP', label: 'First Contentful Paint', unit: 'ms', icon: Activity },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {webVitalsMetrics.map((metric) => {
        const value = summary.webVitals[metric.name];
        const threshold = PERFORMANCE_THRESHOLDS[metric.name as keyof typeof PERFORMANCE_THRESHOLDS];
        
        let rating: 'good' | 'needs-improvement' | 'poor' = 'good';
        if (value && threshold) {
          if (value > threshold.poor) rating = 'poor';
          else if (value > threshold.good) rating = 'needs-improvement';
        }

        const ratingColors = {
          good: 'text-green-600 bg-green-50 border-green-200',
          'needs-improvement': 'text-yellow-600 bg-yellow-50 border-yellow-200',
          poor: 'text-red-600 bg-red-50 border-red-200',
        };

        const Icon = metric.icon;

        return (
          <motion.div
            key={metric.name}
            className={`p-4 rounded-lg border ${ratingColors[rating]}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center justify-between mb-2">
              <Icon className="h-4 w-4 " />
              <span className="text-xs font-medium uppercase tracking-wide sm:text-sm md:text-base">
                {metric.name}
              </span>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {value ? `${Math.round(value)}${metric.unit}` : 'N/A'}
              </div>
              <div className="text-xs opacity-75 sm:text-sm md:text-base">
                {metric.label}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};

const CustomMetricsSection: React.FC<{ 
  metrics: Record<string, any> 
}> = ({ metrics }) => {
  const metricEntries = Object.entries(metrics).slice(0, 6); // Show top 6 metrics

  if (metricEntries.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-md font-semibold flex items-center space-x-2">
        <TrendingUp className="h-4 w-4 " />
        <span>Custom Metrics</span>
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metricEntries.map(([name, data]) => (
          <motion.div
            key={name}
            className="p-4 bg-card rounded-lg border sm:p-4 md:p-6"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
                {name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              <div className="text-xl font-bold">
                {Math.round(data.avg)}ms
              </div>
              <div className="flex justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
                <span>Min: {Math.round(data.min)}ms</span>
                <span>Max: {Math.round(data.max)}ms</span>
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                P95: {Math.round(data.p95)}ms ({data.count} samples)
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

const ResourceTimingSection: React.FC<{ 
  resourceTiming: PerformanceSummary['resourceTiming'] 
}> = ({ resourceTiming }) => {
  const resourceTypes = Object.entries(resourceTiming.byType)
    .sort(([,a], [,b]) => b.totalSize - a.totalSize)
    .slice(0, 5);

  return (
    <div className="space-y-4">
      <h3 className="text-md font-semibold flex items-center space-x-2">
        <Activity className="h-4 w-4 " />
        <span>Resource Loading</span>
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-card rounded-lg border sm:p-4 md:p-6">
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Overview</div>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-sm md:text-base lg:text-lg">Total Resources:</span>
                <span className="font-medium">{resourceTiming.totalResources}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm md:text-base lg:text-lg">Total Size:</span>
                <span className="font-medium">{formatBytes(resourceTiming.totalSize)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm md:text-base lg:text-lg">Total Load Time:</span>
                <span className="font-medium">{Math.round(resourceTiming.totalLoadTime)}ms</span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-card rounded-lg border sm:p-4 md:p-6">
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">By Resource Type</div>
            <div className="space-y-1">
              {resourceTypes.map(([type, data]) => (
                <div key={type} className="flex justify-between text-sm md:text-base lg:text-lg">
                  <span className="capitalize">{type}:</span>
                  <span>{data.count} ({formatBytes(data.totalSize)})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const NavigationTimingSection: React.FC<{ 
  navigationTiming: PerformanceSummary['navigationTiming'] 
}> = ({ navigationTiming }) => {
  const timingMetrics = [
    { label: 'DNS Lookup', value: navigationTiming.dnsTime },
    { label: 'Connection', value: navigationTiming.connectTime },
    { label: 'TTFB', value: navigationTiming.ttfb },
    { label: 'DOM Content Loaded', value: navigationTiming.domContentLoaded },
    { label: 'Load Complete', value: navigationTiming.loadComplete },
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-md font-semibold flex items-center space-x-2">
        <Clock className="h-4 w-4 " />
        <span>Navigation Timing</span>
      </h3>
      
      <div className="p-4 bg-card rounded-lg border sm:p-4 md:p-6">
        <div className="space-y-2">
          {timingMetrics.map((metric) => (
            <div key={metric.label} className="flex justify-between">
              <span className="text-sm text-muted-foreground md:text-base lg:text-lg">{metric.label}:</span>
              <span className="font-medium">{Math.round(metric.value)}ms</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const PerformanceAlerts: React.FC<{ 
  metrics: (WebVitalsMetric | CustomMetric)[] 
}> = ({ metrics }) => {
  const alerts = metrics
    .map(metric => {
      const budget = checkPerformanceBudget(metric);
      return { metric, budget };
    })
    .filter(({ budget }) => budget.rating !== 'good')
    .slice(0, 5);

  if (alerts.length === 0) {
    return (
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg sm:p-4 md:p-6">
        <div className="flex items-center space-x-2 text-green-700">
          <CheckCircle className="h-4 w-4 " />
          <span className="text-sm font-medium md:text-base lg:text-lg">All performance metrics are within budget</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-md font-semibold flex items-center space-x-2">
        <AlertTriangle className="h-4 w-4 " />
        <span>Performance Alerts</span>
      </h3>
      
      <div className="space-y-2">
        {alerts.map(({ metric, budget }, index) => {
          const isError = budget.rating === 'poor';
          const alertColor = isError ? 'red' : 'yellow';
          
          return (
            <motion.div
              key={`${metric.name}-${index}`}
              className={`p-3 bg-${alertColor}-50 border border-${alertColor}-200 rounded-lg`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <div className="flex items-start space-x-2">
                {isError ? (
                  <AlertTriangle className={`h-4 w-4 text-${alertColor}-600 mt-0.5`} />
                ) : (
                  <Info className={`h-4 w-4 text-${alertColor}-600 mt-0.5`} />
                )}
                <div className="flex-1">
                  <div className={`text-sm font-medium text-${alertColor}-800`} role="alert">
                    {metric.name}: {Math.round(metric.value)}ms
                  </div>
                  <div className={`text-xs text-${alertColor}-700`} role="alert">
                    {isError ? 'Exceeds' : 'Approaching'} performance budget
                    {budget.threshold && (
                      <span> (target: {budget.threshold.good}ms)</span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

// Utility function
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default PerformanceDashboard;