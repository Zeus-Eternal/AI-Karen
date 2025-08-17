/**
 * Monitoring Status Component
 * Shows a compact status indicator for API health and performance
 */

'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '@/components/ui/popover';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Zap,
  TrendingUp
} from 'lucide-react';
import { useMonitoring } from '@/hooks/use-monitoring';

interface MonitoringStatusProps {
  className?: string;
  showDetails?: boolean;
}

export function MonitoringStatus({ className, showDetails = true }: MonitoringStatusProps) {
  const { health, performance, utils } = useMonitoring();

  const overallStatus = utils.getOverallStatus();
  const unacknowledgedAlerts = utils.getUnacknowledgedHealthAlerts();
  const criticalAlerts = utils.getCriticalHealthAlerts();

  const getStatusIcon = () => {
    switch (overallStatus) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (overallStatus) {
      case 'healthy':
        return 'default';
      case 'degraded':
        return 'secondary';
      case 'error':
      case 'critical':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusText = () => {
    switch (overallStatus) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'error':
        return 'Error';
      case 'critical':
        return 'Critical';
      default:
        return 'Unknown';
    }
  };

  if (!showDetails) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {getStatusIcon()}
        <Badge variant={getStatusColor()}>
          {getStatusText()}
        </Badge>
        {unacknowledgedAlerts.length > 0 && (
          <Badge variant="destructive" className="text-xs">
            {unacknowledgedAlerts.length}
          </Badge>
        )}
      </div>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className={`gap-2 ${className}`}>
          {getStatusIcon()}
          <Badge variant={getStatusColor()}>
            {getStatusText()}
          </Badge>
          {unacknowledgedAlerts.length > 0 && (
            <Badge variant="destructive" className="text-xs">
              {unacknowledgedAlerts.length}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">API Status</h4>
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <Badge variant={getStatusColor()}>
                {getStatusText()}
              </Badge>
            </div>
          </div>

          {health.metrics && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Error Rate</div>
                    <div className="text-muted-foreground">
                      {(health.metrics.errorRate * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">Response Time</div>
                    <div className="text-muted-foreground">
                      {health.metrics.averageResponseTime.toFixed(0)}ms
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-sm">
                <div className="font-medium mb-1">Requests</div>
                <div className="text-muted-foreground">
                  {health.metrics.totalRequests} total, {health.metrics.failedRequests} failed
                </div>
              </div>

              {performance.stats && (
                <div className="text-sm">
                  <div className="font-medium mb-1">Performance</div>
                  <div className="text-muted-foreground">
                    P95: {performance.stats.p95ResponseTime.toFixed(0)}ms, 
                    P99: {performance.stats.p99ResponseTime.toFixed(0)}ms
                  </div>
                </div>
              )}
            </div>
          )}

          {criticalAlerts.length > 0 && (
            <div className="space-y-2">
              <div className="font-medium text-red-600 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Critical Alerts
              </div>
              {criticalAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="text-sm p-2 bg-red-50 rounded border-l-2 border-red-500">
                  <div className="font-medium">{alert.message}</div>
                  <div className="text-muted-foreground text-xs">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
              {criticalAlerts.length > 3 && (
                <div className="text-xs text-muted-foreground">
                  +{criticalAlerts.length - 3} more critical alerts
                </div>
              )}
            </div>
          )}

          {unacknowledgedAlerts.length > 0 && criticalAlerts.length === 0 && (
            <div className="space-y-2">
              <div className="font-medium text-yellow-600 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {unacknowledgedAlerts.length} Unacknowledged Alert{unacknowledgedAlerts.length !== 1 ? 's' : ''}
              </div>
              {unacknowledgedAlerts.slice(0, 2).map((alert) => (
                <div key={alert.id} className="text-sm p-2 bg-yellow-50 rounded border-l-2 border-yellow-500">
                  <div className="font-medium">{alert.message}</div>
                  <div className="text-muted-foreground text-xs">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}

          {health.metrics && (
            <div className="text-xs text-muted-foreground border-t pt-2">
              Last updated: {new Date(health.metrics.lastHealthCheck).toLocaleTimeString()}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}