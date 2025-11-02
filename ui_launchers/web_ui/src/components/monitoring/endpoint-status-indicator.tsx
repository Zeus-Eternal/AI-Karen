import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
import { Progress } from '@/components/ui/progress';
/**
 * Endpoint Status Indicator Component
 * Compact status indicator for endpoint connectivity with real-time updates
 */

'use client';





  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '@/components/ui/popover';


  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Zap,
  TrendingUp,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

  getHealthMonitor, 
  type HealthMetrics 
} from '@/lib/health-monitor';

  getDiagnosticLogger 
} from '@/lib/diagnostics';

interface EndpointStatusIndicatorProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function EndpointStatusIndicator({ 
  className, 
  showDetails = true, 
  compact = false 
}: EndpointStatusIndicatorProps) {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [recentErrors, setRecentErrors] = useState<number>(0);

  useEffect(() => {
    const healthMonitor = getHealthMonitor();
    const diagnosticLogger = getDiagnosticLogger();

    // Get initial state
    setMetrics(healthMonitor.getMetrics());
    setIsMonitoring(healthMonitor.getStatus().isMonitoring);

    // Count recent errors (last 5 minutes)
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    const errorLogs = diagnosticLogger.getLogs(100, 'network')
      .filter(log => log.level === 'error' && new Date(log.timestamp).getTime() > fiveMinutesAgo);
    setRecentErrors(errorLogs.length);

    // Set up listeners
    const unsubscribeMetrics = healthMonitor.onMetricsUpdate((newMetrics) => {
      setMetrics(newMetrics);
      setLastUpdate(new Date().toLocaleTimeString());
    });

    const unsubscribeLogs = diagnosticLogger.onLog((newLog) => {
      if (newLog.level === 'error' && newLog.category === 'network') {
        setRecentErrors(prev => prev + 1);
        // Reset counter after 5 minutes
        setTimeout(() => {
          setRecentErrors(prev => Math.max(0, prev - 1));
        }, 5 * 60 * 1000);
      }
    });

    return () => {
      unsubscribeMetrics();
      unsubscribeLogs();
    };
  }, []);

  const getOverallStatus = () => {
    if (!metrics) return 'unknown';
    
    // Check if any endpoints are in error state
    const hasErrors = Object.values(metrics.endpoints).some(endpoint => endpoint.status === 'error');
    if (hasErrors) return 'error';
    
    // Check error rate
    if (metrics.errorRate > 0.1) return 'error';
    if (metrics.errorRate > 0.05) return 'degraded';
    
    // Check response time
    if (metrics.averageResponseTime > 10000) return 'error';
    if (metrics.averageResponseTime > 5000) return 'degraded';
    
    return 'healthy';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600 sm:w-auto md:w-full" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'default';
      case 'degraded':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const formatUptime = (uptime: number) => {
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m`;
    return `${seconds}s`;
  };

  const overallStatus = getOverallStatus();
  const healthyEndpoints = metrics ? Object.values(metrics.endpoints).filter(e => e.status === 'healthy').length : 0;
  const totalEndpoints = metrics ? Object.keys(metrics.endpoints).length : 0;

  if (compact) {
    return (
      <div className={`flex items-center gap-1 ${className}`}>
        {getStatusIcon(overallStatus)}
        {recentErrors > 0 && (
          <Badge variant="destructive" className="text-xs px-1 py-0 h-4 min-w-4 sm:w-auto md:w-full">
            {recentErrors}
          </Badge>
        )}
      </div>
    );
  }

  if (!showDetails) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {getStatusIcon(overallStatus)}
        <Badge variant={getStatusColor(overallStatus)}>
          {getStatusText(overallStatus)}
        </Badge>
        {recentErrors > 0 && (
          <Badge variant="destructive" className="text-xs sm:text-sm md:text-base">
            {recentErrors}
          </Badge>
        )}
      </div>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button variant="ghost" size="sm" className={`gap-2 ${className}`} aria-label="Button">
          {getStatusIcon(overallStatus)}
          <Badge variant={getStatusColor(overallStatus)}>
            {getStatusText(overallStatus)}
          </Badge>
          {recentErrors > 0 && (
            <Badge variant="destructive" className="text-xs sm:text-sm md:text-base">
              {recentErrors}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 sm:w-auto md:w-full" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Endpoint Status</h4>
            <div className="flex items-center gap-2">
              {getStatusIcon(overallStatus)}
              <Badge variant={getStatusColor(overallStatus)}>
                {getStatusText(overallStatus)}
              </Badge>
            </div>
          </div>

          {metrics && (
            <div className="space-y-3">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                  <div>
                    <div className="font-medium">Error Rate</div>
                    <div className="text-muted-foreground">
                      {(metrics.errorRate * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                  <div>
                    <div className="font-medium">Response Time</div>
                    <div className="text-muted-foreground">
                      {metrics.averageResponseTime.toFixed(0)}ms
                    </div>
                  </div>
                </div>
              </div>

              {/* Endpoint Summary */}
              <div className="text-sm md:text-base lg:text-lg">
                <div className="font-medium mb-2">Endpoints ({healthyEndpoints}/{totalEndpoints} healthy)</div>
                <Progress 
                  value={totalEndpoints > 0 ? (healthyEndpoints / totalEndpoints) * 100 : 0} 
                  className="h-2"
                />
              </div>

              {/* Individual Endpoints */}
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {Object.entries(metrics.endpoints).map(([endpoint, result]) => (
                  <div key={endpoint} className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                    <div className="flex items-center gap-2 flex-1 min-w-0 sm:w-auto md:w-full">
                      {getStatusIcon(result.status)}
                      <span className="truncate" title={endpoint}>
                        {endpoint.split('/').pop() || endpoint}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <span>{result.responseTime}ms</span>
                      <button
                        variant="ghost"
                        size="sm"
                        className="h-4 w-4 p-0 sm:w-auto md:w-full"
                        onClick={() = aria-label="Button"> window.open(endpoint, '_blank')}
                      >
                        <ExternalLink className="h-3 w-3 sm:w-auto md:w-full" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Recent Activity */}
              <div className="text-sm md:text-base lg:text-lg">
                <div className="font-medium mb-1">Activity</div>
                <div className="text-muted-foreground space-y-1">
                  <div className="flex justify-between">
                    <span>Total Requests:</span>
                    <span>{metrics.totalRequests}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Errors:</span>
                    <span className={recentErrors > 0 ? 'text-red-600' : ''}>
                      {recentErrors}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uptime:</span>
                    <span>{formatUptime(metrics.uptime)}</span>
                  </div>
                </div>
              </div>

              {/* Monitoring Status */}
              <div className="flex items-center justify-between text-sm pt-2 border-t md:text-base lg:text-lg">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${isMonitoring ? 'bg-green-500' : 'bg-gray-400'}`} />
                  <span className="text-muted-foreground">
                    {isMonitoring ? 'Monitoring Active' : 'Monitoring Stopped'}
                  </span>
                </div>
                {lastUpdate && (
                  <span className="text-muted-foreground text-xs sm:text-sm md:text-base">
                    {lastUpdate}
                  </span>
                )}
              </div>
            </div>
          )}

          {!metrics && (
            <div className="flex items-center justify-center py-4">
              <div className="text-center">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-muted-foreground sm:w-auto md:w-full" />
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Loading status...</p>
              </div>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}