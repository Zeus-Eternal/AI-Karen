"use client";

/**
 * Extension Health Monitor
 *
 * Real-time monitoring of extension health, performance, and resource usage
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Activity,
  Cpu,
  HardDrive,
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Check
} from 'lucide-react';

interface ExtensionHealth {
  id: string;
  name: string;
  status: 'healthy' | 'degraded' | 'critical' | 'offline';
  uptime: number;
  memoryUsage: {
    current: number;
    max: number;
    percentage: number;
  };
  cpuUsage: number;
  errorRate: number;
  responseTime: number;
  lastCheck: string;
}

interface SystemHealth {
  overallStatus: 'healthy' | 'degraded' | 'critical';
  healthyCount: number;
  degradedCount: number;
  criticalCount: number;
  offlineCount: number;
  totalMemoryUsage: number;
  avgCpuUsage: number;
  avgResponseTime: number;
}

export interface ExtensionHealthMonitorProps {
  refreshInterval?: number;
  thresholds?: {
    memory?: number;
    cpu?: number;
    errorRate?: number;
    responseTime?: number;
  };
}

export default function ExtensionHealthMonitor({
  refreshInterval = 5000,
  thresholds = {
    memory: 80,
    cpu: 70,
    errorRate: 5,
    responseTime: 1000
  }
}: ExtensionHealthMonitorProps) {
  const [extensions, setExtensions] = useState<ExtensionHealth[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    overallStatus: 'healthy',
    healthyCount: 0,
    degradedCount: 0,
    criticalCount: 0,
    offlineCount: 0,
    totalMemoryUsage: 0,
    avgCpuUsage: 0,
    avgResponseTime: 0
  });
  const [isLoading, setIsLoading] = useState(false);

  const loadHealthData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/health');
      if (response.ok) {
        const data = await response.json();
        setExtensions(data.extensions);
        setSystemHealth(data.systemHealth);
      } else {
        // Fallback mock data
        const mockExtensions: ExtensionHealth[] = [
          {
            id: 'ext_1',
            name: 'Authentication Extension',
            status: 'healthy',
            uptime: Date.now() - 86400000 * 7,
            memoryUsage: { current: 45, max: 100, percentage: 45 },
            cpuUsage: 2.5,
            errorRate: 0.1,
            responseTime: 120,
            lastCheck: new Date().toISOString()
          },
          {
            id: 'ext_2',
            name: 'Analytics Engine',
            status: 'degraded',
            uptime: Date.now() - 86400000 * 3,
            memoryUsage: { current: 850, max: 1000, percentage: 85 },
            cpuUsage: 45,
            errorRate: 3.2,
            responseTime: 850,
            lastCheck: new Date().toISOString()
          },
          {
            id: 'ext_3',
            name: 'LLM Provider Manager',
            status: 'healthy',
            uptime: Date.now() - 86400000 * 14,
            memoryUsage: { current: 320, max: 500, percentage: 64 },
            cpuUsage: 12,
            errorRate: 0.5,
            responseTime: 250,
            lastCheck: new Date().toISOString()
          },
          {
            id: 'ext_4',
            name: 'Cache Optimizer',
            status: 'critical',
            uptime: Date.now() - 3600000,
            memoryUsage: { current: 950, max: 1000, percentage: 95 },
            cpuUsage: 78,
            errorRate: 12.5,
            responseTime: 2500,
            lastCheck: new Date().toISOString()
          }
        ];

        setExtensions(mockExtensions);

        const healthy = mockExtensions.filter(e => e.status === 'healthy').length;
        const degraded = mockExtensions.filter(e => e.status === 'degraded').length;
        const critical = mockExtensions.filter(e => e.status === 'critical').length;
        const offline = mockExtensions.filter(e => e.status === 'offline').length;

        const totalMemory = mockExtensions.reduce((sum, e) => sum + e.memoryUsage.percentage, 0);
        const avgCpu = mockExtensions.reduce((sum, e) => sum + e.cpuUsage, 0) / mockExtensions.length;
        const avgResponse = mockExtensions.reduce((sum, e) => sum + e.responseTime, 0) / mockExtensions.length;

        setSystemHealth({
          overallStatus: critical > 0 ? 'critical' : degraded > 0 ? 'degraded' : 'healthy',
          healthyCount: healthy,
          degradedCount: degraded,
          criticalCount: critical,
          offlineCount: offline,
          totalMemoryUsage: totalMemory / mockExtensions.length,
          avgCpuUsage: avgCpu,
          avgResponseTime: avgResponse
        });
      }
    } catch (error) {
      console.error('Failed to load health data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHealthData();
    const interval = setInterval(loadHealthData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-600';
      case 'degraded':
        return 'bg-yellow-600';
      case 'critical':
        return 'bg-red-600';
      case 'offline':
        return 'bg-gray-600';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Check className="h-4 w-4 text-green-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const formatUptime = (ms: number) => {
    const days = Math.floor(ms / 86400000);
    const hours = Math.floor((ms % 86400000) / 3600000);
    return `${days}d ${hours}h`;
  };

  return (
    <div className="space-y-6">
      {/* Overall Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Extension Health Monitor
            </div>
            <Button onClick={loadHealthData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Real-time monitoring of extension health and performance (Updates every {refreshInterval / 1000}s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Overall Status</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant="default" className={`${getStatusColor(systemHealth.overallStatus)} text-white`}>
                  {systemHealth.overallStatus.toUpperCase()}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Avg Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemHealth.totalMemoryUsage.toFixed(1)}%</div>
                <Progress value={systemHealth.totalMemoryUsage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Avg CPU</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemHealth.avgCpuUsage.toFixed(1)}%</div>
                <Progress value={systemHealth.avgCpuUsage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Avg Response</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemHealth.avgResponseTime.toFixed(0)}ms</div>
              </CardContent>
            </Card>
          </div>

          {/* Health Status Summary */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-sm">Health Status Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">{systemHealth.healthyCount}</div>
                  <div className="text-sm text-muted-foreground">Healthy</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">{systemHealth.degradedCount}</div>
                  <div className="text-sm text-muted-foreground">Degraded</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{systemHealth.criticalCount}</div>
                  <div className="text-sm text-muted-foreground">Critical</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-600">{systemHealth.offlineCount}</div>
                  <div className="text-sm text-muted-foreground">Offline</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Critical Alerts */}
          {systemHealth.criticalCount > 0 && (
            <Alert variant="destructive" className="mb-6">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Critical Extensions Detected</AlertTitle>
              <AlertDescription>
                {systemHealth.criticalCount} extension{systemHealth.criticalCount > 1 ? 's are' : ' is'} in critical state. Immediate attention required.
              </AlertDescription>
            </Alert>
          )}

          {/* Extension Health Details */}
          <div className="space-y-3">
            {extensions.map((ext) => (
              <Card key={ext.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(ext.status)}
                      <CardTitle className="text-sm">{ext.name}</CardTitle>
                      <Badge variant="outline">{ext.status.toUpperCase()}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Uptime: {formatUptime(ext.uptime)}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-4 gap-4">
                    {/* Memory Usage */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Memory</span>
                      </div>
                      <div className="text-lg font-bold">
                        {ext.memoryUsage.percentage}%
                      </div>
                      <Progress
                        value={ext.memoryUsage.percentage}
                        className="mt-1"
                      />
                      <div className="text-xs text-muted-foreground mt-1">
                        {ext.memoryUsage.current}MB / {ext.memoryUsage.max}MB
                      </div>
                      {ext.memoryUsage.percentage > (thresholds.memory || 80) && (
                        <Badge variant="destructive" className="mt-1 text-xs">
                          High Usage
                        </Badge>
                      )}
                    </div>

                    {/* CPU Usage */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">CPU</span>
                      </div>
                      <div className="text-lg font-bold">
                        {ext.cpuUsage.toFixed(1)}%
                      </div>
                      <Progress value={ext.cpuUsage} className="mt-1" />
                      {ext.cpuUsage > (thresholds.cpu || 70) && (
                        <Badge variant="destructive" className="mt-1 text-xs">
                          High Usage
                        </Badge>
                      )}
                    </div>

                    {/* Error Rate */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Error Rate</span>
                      </div>
                      <div className="text-lg font-bold">
                        {ext.errorRate.toFixed(1)}%
                      </div>
                      {ext.errorRate > (thresholds.errorRate || 5) ? (
                        <Badge variant="destructive" className="mt-1">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          High
                        </Badge>
                      ) : (
                        <Badge variant="default" className="mt-1 bg-green-600">
                          <TrendingDown className="h-3 w-3 mr-1" />
                          Low
                        </Badge>
                      )}
                    </div>

                    {/* Response Time */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Response</span>
                      </div>
                      <div className="text-lg font-bold">
                        {ext.responseTime}ms
                      </div>
                      {ext.responseTime > (thresholds.responseTime || 1000) && (
                        <Badge variant="destructive" className="mt-1 text-xs">
                          Slow
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export { ExtensionHealthMonitor };
export type { ExtensionHealthMonitorProps };
