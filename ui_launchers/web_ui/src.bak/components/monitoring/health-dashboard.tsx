/**
 * Health Dashboard Component
 * Displays API integration health metrics and alerts
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Server, 
  TrendingUp,
  XCircle,
  Bell,
  BellOff,
  RefreshCw,
  Zap
} from 'lucide-react';
import { getHealthMonitor, type HealthMetrics, type Alert as HealthAlert } from '@/lib/health-monitor';

interface HealthDashboardProps {
  className?: string;
}

export function HealthDashboard({ className }: HealthDashboardProps) {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    const healthMonitor = getHealthMonitor();

    // Get initial state
    setMetrics(healthMonitor.getMetrics());
    setAlerts(healthMonitor.getAlerts(20));
    setIsMonitoring(healthMonitor.getStatus().isMonitoring);

    // Set up listeners
    const unsubscribeMetrics = healthMonitor.onMetricsUpdate((newMetrics) => {
      setMetrics(newMetrics);
      setLastUpdate(new Date().toLocaleTimeString());
    });

    const unsubscribeAlerts = healthMonitor.onAlert((newAlert) => {
      setAlerts(prev => [newAlert, ...prev.slice(0, 19)]);
    });

    // Start monitoring if not already started
    if (!healthMonitor.getStatus().isMonitoring) {
      healthMonitor.start();
      setIsMonitoring(true);
    }

    return () => {
      unsubscribeMetrics();
      unsubscribeAlerts();
    };
  }, []);

  const handleToggleMonitoring = () => {
    const healthMonitor = getHealthMonitor();
    
    if (isMonitoring) {
      healthMonitor.stop();
      setIsMonitoring(false);
    } else {
      healthMonitor.start();
      setIsMonitoring(true);
    }
  };

  const handleAcknowledgeAlert = (alertId: string) => {
    const healthMonitor = getHealthMonitor();
    if (healthMonitor.acknowledgeAlert(alertId)) {
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    }
  };

  const handleClearAlerts = () => {
    const healthMonitor = getHealthMonitor();
    healthMonitor.clearAlerts();
    setAlerts([]);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'degraded': return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const formatUptime = (uptime: number) => {
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged);

  if (!metrics) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p>Loading health metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">API Health Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor backend API integration status and performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isMonitoring ? 'default' : 'secondary'}>
            {isMonitoring ? 'Monitoring Active' : 'Monitoring Stopped'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleMonitoring}
          >
            {isMonitoring ? <BellOff className="h-4 w-4" /> : <Bell className="h-4 w-4" />}
            {isMonitoring ? 'Stop' : 'Start'}
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getStatusIcon(metrics.errorRate > 0.1 ? 'error' : metrics.errorRate > 0.05 ? 'degraded' : 'healthy')}
              <span className="text-2xl font-bold">
                {metrics.errorRate > 0.1 ? 'Error' : metrics.errorRate > 0.05 ? 'Degraded' : 'Healthy'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Last check: {lastUpdate || 'Never'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(metrics.errorRate * 100).toFixed(1)}%
            </div>
            <Progress 
              value={metrics.errorRate * 100} 
              className="mt-2"
              max={100}
            />
            <p className="text-xs text-muted-foreground">
              {metrics.failedRequests} of {metrics.totalRequests} requests failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.averageResponseTime.toFixed(0)}ms
            </div>
            <Progress 
              value={Math.min((metrics.averageResponseTime / 5000) * 100, 100)} 
              className="mt-2"
              max={100}
            />
            <p className="text-xs text-muted-foreground">
              Average response time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatUptime(metrics.uptime)}
            </div>
            <p className="text-xs text-muted-foreground">
              Since monitoring started
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts Section */}
      {unacknowledgedAlerts.length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            You have {unacknowledgedAlerts.length} unacknowledged alert{unacknowledgedAlerts.length !== 1 ? 's' : ''}
          </AlertDescription>
        </Alert>
      )}

      {/* Detailed Tabs */}
      <Tabs defaultValue="endpoints" className="w-full">
        <TabsList>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts {unacknowledgedAlerts.length > 0 && (
              <Badge variant="destructive" className="ml-1 text-xs">
                {unacknowledgedAlerts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="endpoints" className="space-y-4">
          <div className="grid gap-4">
            {Object.entries(metrics.endpoints).map(([endpoint, result]) => (
              <Card key={endpoint}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">{endpoint}</CardTitle>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(result.status)}
                      <Badge variant={result.status === 'healthy' ? 'default' : 'destructive'}>
                        {result.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Response Time:</span>
                      <span className="ml-2 font-mono">{result.responseTime}ms</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Last Check:</span>
                      <span className="ml-2">{new Date(result.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                  {result.error && (
                    <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
                      <strong>Error:</strong> {result.error}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Recent Alerts</h3>
            {alerts.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleClearAlerts}>
                Clear All
              </Button>
            )}
          </div>
          
          {alerts.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                  <p className="text-muted-foreground">No alerts</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <Card key={alert.id} className={alert.acknowledged ? 'opacity-60' : ''}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm">{alert.message}</p>
                        {alert.acknowledged && (
                          <Badge variant="outline" className="mt-1">
                            Acknowledged
                          </Badge>
                        )}
                      </div>
                      {!alert.acknowledged && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAcknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Request Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span>Total Requests:</span>
                  <span className="font-mono">{metrics.totalRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span>Successful:</span>
                  <span className="font-mono text-green-600">{metrics.successfulRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span>Failed:</span>
                  <span className="font-mono text-red-600">{metrics.failedRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span>Success Rate:</span>
                  <span className="font-mono">
                    {metrics.totalRequests > 0 
                      ? ((metrics.successfulRequests / metrics.totalRequests) * 100).toFixed(1)
                      : 0}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span>Average Response Time:</span>
                  <span className="font-mono">{metrics.averageResponseTime.toFixed(0)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Error Rate:</span>
                  <span className="font-mono">{(metrics.errorRate * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Uptime:</span>
                  <span className="font-mono">{formatUptime(metrics.uptime)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Health Check:</span>
                  <span className="font-mono text-sm">
                    {new Date(metrics.lastHealthCheck).toLocaleTimeString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}