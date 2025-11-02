/**
 * Real-time monitoring dashboard component
 */

import React, { useState, useEffect, useCallback } from 'react';
import { SystemHealth, MonitoringConfig } from './types';
import { ConnectionStatusIndicator } from './ConnectionStatusIndicator';
import { PerformanceMetricsDisplay } from './PerformanceMetricsDisplay';
import { ErrorRateDisplay } from './ErrorRateDisplay';
import { AuthenticationMetricsDisplay } from './AuthenticationMetricsDisplay';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { connectivityLogger } from '../../lib/logging';
import { performanceTracker } from '../../lib/logging';

interface RealTimeMonitoringDashboardProps {
  config?: Partial<MonitoringConfig>;
  className?: string;
  onHealthChange?: (health: SystemHealth) => void;
}

export const RealTimeMonitoringDashboard: React.FC<RealTimeMonitoringDashboardProps> = ({
  config = {},
  className = '',
  onHealthChange
}) => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const defaultConfig: MonitoringConfig = {
    refreshInterval: 30000, // 30 seconds
    enableRealTimeUpdates: true,
    showDetailedMetrics: true,
    alertThresholds: {
      responseTime: 5000,
      errorRate: 5,
      authFailureRate: 15
    },
    ...config
  };

  // Mock data generator for demonstration
  const generateMockSystemHealth = useCallback((): SystemHealth => {
    const now = new Date();
    const performanceStats = performanceTracker.getPerformanceStats();
    
    // Generate realistic mock data
    const baseResponseTime = 800 + Math.random() * 400;
    const errorRate = Math.random() * 3;
    const authSuccessRate = 95 + Math.random() * 4;
    
    return {
      overall: errorRate < 1 && baseResponseTime < 2000 && authSuccessRate > 95 ? 'healthy' : 
               errorRate < 5 && baseResponseTime < 5000 && authSuccessRate > 85 ? 'degraded' : 'critical',
      components: {
        backend: {
          isConnected: Math.random() > 0.05,
          lastCheck: new Date(now.getTime() - Math.random() * 60000),
          responseTime: baseResponseTime,
          endpoint: 'http://localhost:8000',
          status: baseResponseTime < 2000 ? 'healthy' : baseResponseTime < 5000 ? 'degraded' : 'failed',
          errorCount: Math.floor(Math.random() * 10),
          successCount: Math.floor(Math.random() * 100) + 50
        },
        database: {
          isConnected: Math.random() > 0.02,
          lastCheck: new Date(now.getTime() - Math.random() * 30000),
          responseTime: baseResponseTime * 0.6,
          endpoint: 'postgresql://localhost:5432',
          status: baseResponseTime < 1500 ? 'healthy' : baseResponseTime < 3000 ? 'degraded' : 'failed',
          errorCount: Math.floor(Math.random() * 5),
          successCount: Math.floor(Math.random() * 200) + 100
        },
        authentication: {
          isConnected: Math.random() > 0.01,
          lastCheck: new Date(now.getTime() - Math.random() * 45000),
          responseTime: baseResponseTime * 1.2,
          endpoint: '/api/auth',
          status: authSuccessRate > 95 ? 'healthy' : authSuccessRate > 85 ? 'degraded' : 'failed',
          errorCount: Math.floor(Math.random() * 8),
          successCount: Math.floor(Math.random() * 80) + 40
        }
      },
      performance: {
        averageResponseTime: baseResponseTime,
        p95ResponseTime: baseResponseTime * 1.5,
        p99ResponseTime: baseResponseTime * 2.2,
        requestCount: performanceStats.count || Math.floor(Math.random() * 1000) + 500,
        errorRate: errorRate,
        throughput: 2.5 + Math.random() * 2,
        timeRange: 'Last 1 hour'
      },
      errors: {
        totalErrors: Math.floor(Math.random() * 50) + 10,
        errorRate: errorRate,
        errorsByType: {
          'Network Timeout': Math.floor(Math.random() * 15) + 5,
          'Authentication Failed': Math.floor(Math.random() * 10) + 2,
          'Database Connection': Math.floor(Math.random() * 8) + 1,
          'Validation Error': Math.floor(Math.random() * 12) + 3,
          'Server Error': Math.floor(Math.random() * 6) + 1
        },
        recentErrors: Array.from({ length: Math.floor(Math.random() * 10) + 5 }, (_, i) => ({
          timestamp: new Date(now.getTime() - Math.random() * 3600000),
          type: ['Network Timeout', 'Authentication Failed', 'Database Connection'][Math.floor(Math.random() * 3)],
          message: `Error message ${i + 1}`,
          correlationId: `corr_${Math.random().toString(36).substr(2, 9)}`
        }))
      },
      authentication: {
        totalAttempts: Math.floor(Math.random() * 200) + 100,
        successfulAttempts: Math.floor(authSuccessRate * 2),
        failedAttempts: Math.floor((100 - authSuccessRate) * 2),
        successRate: authSuccessRate,
        averageAuthTime: baseResponseTime * 0.8,
        recentFailures: Array.from({ length: Math.floor(Math.random() * 8) + 2 }, (_, i) => ({
          timestamp: new Date(now.getTime() - Math.random() * 7200000),
          reason: ['Invalid credentials', 'Account locked', 'Session expired', 'Network timeout'][Math.floor(Math.random() * 4)],
          email: Math.random() > 0.5 ? `user${i}@example.com` : undefined
        }))
      },
      lastUpdated: now
    };
  }, []);

  const fetchSystemHealth = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // In a real implementation, this would fetch from actual monitoring endpoints
      // For now, we'll generate mock data and integrate with the logging system
      const health = generateMockSystemHealth();
      
      setSystemHealth(health);
      setLastUpdate(new Date());
      
      if (onHealthChange) {
        onHealthChange(health);
      }
      
      // Log the health check
      connectivityLogger.logConnectivity(
        'debug',
        'System health check completed',
        {
          url: '/api/health',
          method: 'GET',
          statusCode: 200
        }
      );
      
    } catch (error) {
      console.error('Failed to fetch system health:', error);
      connectivityLogger.logError(
        'Failed to fetch system health',
        error as Error,
        'connectivity'
      );
    } finally {
      setIsLoading(false);
    }
  }, [generateMockSystemHealth, onHealthChange]);

  // Auto-refresh effect
  useEffect(() => {
    fetchSystemHealth();
    
    if (autoRefresh && defaultConfig.enableRealTimeUpdates) {
      const interval = setInterval(fetchSystemHealth, defaultConfig.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchSystemHealth, autoRefresh, defaultConfig.enableRealTimeUpdates, defaultConfig.refreshInterval]);

  const getOverallStatusColor = (status: SystemHealth['overall']) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'critical':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getOverallStatusBadge = (status: SystemHealth['overall']) => {
    switch (status) {
      case 'healthy':
        return 'default';
      case 'degraded':
        return 'secondary';
      case 'critical':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  if (isLoading && !systemHealth) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-muted-foreground">Loading system health...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!systemHealth) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">
              Failed to load system health data
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overall System Status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span className="text-xl font-bold">System Health Dashboard</span>
            <div className="flex items-center space-x-3">
              <Badge variant={getOverallStatusBadge(systemHealth.overall)} className="text-sm">
                {systemHealth.overall.toUpperCase()}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchSystemHealth}
                disabled={isLoading}
                className="text-xs"
              >
                {isLoading ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`text-xs ${autoRefresh ? 'text-blue-600' : 'text-muted-foreground'}`}
              >
                Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div 
                className={`w-4 h-4 rounded-full ${
                  systemHealth.overall === 'healthy' ? 'bg-green-500' :
                  systemHealth.overall === 'degraded' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
              />
              <span className={`text-lg font-semibold ${getOverallStatusColor(systemHealth.overall)}`}>
                System is {systemHealth.overall}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ConnectionStatusIndicator
          status={systemHealth.components.backend}
          title="Backend API"
          showDetails={defaultConfig.showDetailedMetrics}
        />
        <ConnectionStatusIndicator
          status={systemHealth.components.database}
          title="Database"
          showDetails={defaultConfig.showDetailedMetrics}
        />
        <ConnectionStatusIndicator
          status={systemHealth.components.authentication}
          title="Authentication"
          showDetails={defaultConfig.showDetailedMetrics}
        />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceMetricsDisplay
          metrics={systemHealth.performance}
          showTrends={defaultConfig.showDetailedMetrics}
        />
        <ErrorRateDisplay
          errorMetrics={systemHealth.errors}
          showRecentErrors={defaultConfig.showDetailedMetrics}
        />
      </div>

      {/* Authentication Metrics */}
      <AuthenticationMetricsDisplay
        metrics={systemHealth.authentication}
        showRecentFailures={defaultConfig.showDetailedMetrics}
      />
    </div>
  );
};