'use client';

import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  RefreshCw,
  Settings,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Cpu,
  HardDrive,
  Zap,
  Database,
  Brain,
  Gauge
} from 'lucide-react';

interface IntegrationStatus {
  initialized: boolean;
  initialization_error?: string;
  component_status: Record<string, {
    integrated: boolean;
    error_message?: string;
    integration_time?: string;
  }>;
  integrated_components: string[];
  configuration_summary: {
    optimization_enabled: boolean;
    optimization_level: string;
    config_version: string;
    last_updated: string;
    components: Record<string, boolean>;
    reasoning_preservation: Record<string, boolean>;
    validation_status: boolean;
  };
}

interface HealthStatus {
  overall_health: string;
  timestamp: string;
  components: Record<string, {
    status: string;
    error?: string;
    details?: Record<string, any>;
  }>;
}

interface PerformanceDashboard {
  timestamp: string;
  metrics_count: number;
  aggregated_stats: Record<string, Record<string, number>>;
  active_alerts: Array<{
    alert_id: string;
    metric_name: string;
    current_value: number;
    threshold_value: number;
    severity: string;
    message: string;
    timestamp: string;
  }>;
  component_health: Record<string, number>;
  trends: Record<string, string>;
}

const OptimizationDashboard: React.FC = () => {
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [performanceDashboard, setPerformanceDashboard] = useState<PerformanceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [statusRes, healthRes, perfRes] = await Promise.all([
        fetch('/api/optimization/status'),
        fetch('/api/optimization/health'),
        fetch('/api/optimization/performance/dashboard')
      ]);

      if (!statusRes.ok || !healthRes.ok || !perfRes.ok) {
        throw new Error('Failed to fetch optimization data');
      }

      const [status, health, perf] = await Promise.all([
        statusRes.json(),
        healthRes.json(),
        perfRes.json()
      ]);

      setIntegrationStatus(status);
      setHealthStatus(health);
      setPerformanceDashboard(perf);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      setRefreshing(true);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  };

  const initializeIntegration = async () => {
    try {
      const response = await fetch('/api/optimization/initialize', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to initialize integration');
      }
      
      // Refresh data after initialization
      setTimeout(() => fetchData(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Initialization failed');
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/optimization/performance/alerts/${alertId}/resolve`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to resolve alert');
      }
      
      await fetchData(); // Refresh to update alert status
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve alert');
    }
  };

  useEffect(() => {
    fetchData();
    
    // Set up periodic refresh
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'unhealthy': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return CheckCircle;
      case 'degraded': return AlertTriangle;
      case 'unhealthy': return XCircle;
      default: return Minus;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return TrendingUp;
      case 'decreasing': return TrendingDown;
      default: return Minus;
    }
  };

  const getTrendColor = (trend: string, isGoodWhenIncreasing: boolean = false) => {
    if (trend === 'stable') return 'text-gray-500';
    if (trend === 'increasing') return isGoodWhenIncreasing ? 'text-green-500' : 'text-red-500';
    if (trend === 'decreasing') return isGoodWhenIncreasing ? 'text-red-500' : 'text-green-500';
    return 'text-gray-500';
  };

  if (loading) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in OptimizationDashboard</div>}>
      <div className="flex items-center justify-center p-8 sm:p-4 md:p-6">
        <RefreshCw className="h-6 w-6 animate-spin mr-2 sm:w-auto md:w-full" />
        <span>Loading optimization dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <XCircle className="h-4 w-4 sm:w-auto md:w-full" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6 p-6 sm:p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Optimization Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and manage the intelligent response optimization system
          </p>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={refreshData} 
            disabled={refreshing}
            variant="outline"
           aria-label="Button">
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {!integrationStatus?.initialized && (
            <button onClick={initializeIntegration} aria-label="Button">
              Initialize Integration
            </Button>
          )}
        </div>
      </div>

      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Integration Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {integrationStatus?.initialized ? (
                <CheckCircle className="h-5 w-5 text-green-500 sm:w-auto md:w-full" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500 sm:w-auto md:w-full" />
              )}
              <span className="text-lg font-semibold">
                {integrationStatus?.initialized ? 'Initialized' : 'Not Initialized'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {(() => {
                const HealthIcon = getHealthIcon(healthStatus?.overall_health || 'unknown');
                return (
                  <HealthIcon className={`h-5 w-5 ${getHealthColor(healthStatus?.overall_health || 'unknown')}`} />
                );
              })()}
              <span className="text-lg font-semibold capitalize">
                {healthStatus?.overall_health || 'Unknown'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Active Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500 sm:w-auto md:w-full" />
              <span className="text-lg font-semibold">
                {performanceDashboard?.active_alerts?.length || 0}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Optimization Level</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Gauge className="h-5 w-5 text-blue-500 sm:w-auto md:w-full" />
              <span className="text-lg font-semibold capitalize">
                {integrationStatus?.configuration_summary?.optimization_level || 'Unknown'}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="components">Components</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Component Health */}
            <Card>
              <CardHeader>
                <CardTitle>Component Health</CardTitle>
                <CardDescription>Health status of optimization components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {performanceDashboard?.component_health && Object.entries(performanceDashboard.component_health).map(([component, health]) => (
                  <div key={component} className="space-y-2">
                    <div className="flex justify-between text-sm md:text-base lg:text-lg">
                      <span className="capitalize">{component.replace('_', ' ')}</span>
                      <span>{Math.round(health)}%</span>
                    </div>
                    <Progress value={health} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Performance Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
                <CardDescription>Recent performance trend indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {performanceDashboard?.trends && Object.entries(performanceDashboard.trends).map(([metric, trend]) => {
                  const TrendIcon = getTrendIcon(trend);
                  const isGoodWhenIncreasing = metric.includes('hit_rate') || metric.includes('success');
                  
                  return (
                    <div key={metric} className="flex items-center justify-between">
                      <span className="text-sm capitalize md:text-base lg:text-lg">{metric.replace('_', ' ')}</span>
                      <div className="flex items-center space-x-2">
                        <TrendIcon className={`h-4 w-4 ${getTrendColor(trend, isGoodWhenIncreasing)}`} />
                        <span className="text-sm capitalize md:text-base lg:text-lg">{trend}</span>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Aggregated Statistics */}
          {performanceDashboard?.aggregated_stats && (
            <Card>
              <CardHeader>
                <CardTitle>Performance Statistics</CardTitle>
                <CardDescription>Aggregated performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(performanceDashboard.aggregated_stats).map(([category, stats]) => (
                    <div key={category} className="space-y-2">
                      <h4 className="font-medium capitalize">{category.replace('_', ' ')}</h4>
                      <div className="space-y-1">
                        {Object.entries(stats).map(([metric, value]) => (
                          <div key={metric} className="flex justify-between text-sm md:text-base lg:text-lg">
                            <span className="text-muted-foreground">
                              {metric.replace('_', ' ').replace(/([A-Z])/g, ' $1').toLowerCase()}
                            </span>
                            <span>
                              {typeof value === 'number' ? 
                                (metric.includes('ms') ? `${Math.round(value)}ms` : 
                                 metric.includes('percent') ? `${Math.round(value)}%` :
                                 metric.includes('mb') ? `${Math.round(value)}MB` :
                                 Math.round(value * 100) / 100) : 
                                value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="components" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Integration Status */}
            <Card>
              <CardHeader>
                <CardTitle>Integration Status</CardTitle>
                <CardDescription>Status of integrated optimization components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {integrationStatus?.component_status && Object.entries(integrationStatus.component_status).map(([component, status]) => (
                  <div key={component} className="flex items-center justify-between p-3 border rounded sm:p-4 md:p-6">
                    <div className="flex items-center space-x-3">
                      {status.integrated ? (
                        <CheckCircle className="h-5 w-5 text-green-500 sm:w-auto md:w-full" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500 sm:w-auto md:w-full" />
                      )}
                      <div>
                        <p className="font-medium capitalize">{component.replace('_', ' ')}</p>
                        {status.error_message && (
                          <p className="text-sm text-red-500 md:text-base lg:text-lg">{status.error_message}</p>
                        )}
                        {status.integration_time && (
                          <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            Integrated: {new Date(status.integration_time).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge variant={status.integrated ? "default" : "destructive"}>
                      {status.integrated ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Component Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>Component Configuration</CardTitle>
                <CardDescription>Current configuration status of optimization components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {integrationStatus?.configuration_summary?.components && Object.entries(integrationStatus.configuration_summary.components).map(([component, enabled]) => (
                  <div key={component} className="flex items-center justify-between">
                    <span className="capitalize">{component.replace('_', ' ')}</span>
                    <Switch checked={enabled} disabled />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Reasoning Preservation */}
          <Card>
            <CardHeader>
              <CardTitle>Reasoning Preservation</CardTitle>
              <CardDescription>Status of reasoning logic preservation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {integrationStatus?.configuration_summary?.reasoning_preservation && Object.entries(integrationStatus.configuration_summary.reasoning_preservation).map(([component, preserved]) => (
                  <div key={component} className="flex items-center space-x-2">
                    {preserved ? (
                      <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />
                    )}
                    <span className="text-sm capitalize md:text-base lg:text-lg">{component.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          {/* Performance metrics content would go here */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>Detailed performance monitoring data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
                <p>Performance metrics visualization coming soon</p>
                <p className="text-sm md:text-base lg:text-lg">Metrics are being collected: {performanceDashboard?.metrics_count || 0} data points</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-4">
          {/* Configuration management content would go here */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration Management</CardTitle>
              <CardDescription>Manage optimization system configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Settings className="h-12 w-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
                <p>Configuration management interface coming soon</p>
                <p className="text-sm md:text-base lg:text-lg">Current config version: {integrationStatus?.configuration_summary?.config_version}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          {/* Active Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Active Alerts</CardTitle>
              <CardDescription>Current performance alerts requiring attention</CardDescription>
            </CardHeader>
            <CardContent>
              {performanceDashboard?.active_alerts && performanceDashboard.active_alerts.length > 0 ? (
                <div className="space-y-4">
                  {performanceDashboard.active_alerts.map((alert) => (
                    <div key={alert.alert_id} className="border rounded p-4 sm:p-4 md:p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <AlertTriangle className={`h-4 w-4 ${alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                            <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                              {alert.severity}
                            </Badge>
                            <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {new Date(alert.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="font-medium">{alert.message}</p>
                          <div className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                            Current: {alert.current_value} | Threshold: {alert.threshold_value}
                          </div>
                        </div>
                        <button
                          size="sm"
                          variant="outline"
                          onClick={() = aria-label="Button"> resolveAlert(alert.alert_id)}
                        >
                          Resolve
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50 text-green-500 sm:w-auto md:w-full" />
                  <p>No active alerts</p>
                  <p className="text-sm md:text-base lg:text-lg">All systems are operating within normal parameters</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
    </ErrorBoundary>
  );
};

export default OptimizationDashboard;