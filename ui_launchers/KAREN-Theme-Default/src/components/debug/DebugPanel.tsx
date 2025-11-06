"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Bug,
  Activity,
  Database,
  Network,
  Cpu,
  HardDrive,
  Download,
  RefreshCw,
  Terminal,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info
} from 'lucide-react';

interface SystemInfo {
  runtime: string;
  version: string;
  platform: string;
  nodeVersion: string;
  memoryUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  cpuUsage: number;
  uptime: number;
}

interface ApiEndpointStatus {
  endpoint: string;
  status: 'healthy' | 'degraded' | 'error';
  latency: number;
  lastChecked: string;
}

interface DebugLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source?: string;
}

const DebugPanel: React.FC = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [apiEndpoints, setApiEndpoints] = useState<ApiEndpointStatus[]>([]);
  const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('system');

  const fetchSystemInfo = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/debug/system-info');
      if (response.ok) {
        const data = await response.json();
        setSystemInfo(data);
      } else {
        // Fallback mock data
        setSystemInfo({
          runtime: 'Node.js',
          version: '20.11.0',
          platform: 'linux',
          nodeVersion: 'v20.11.0',
          memoryUsage: {
            used: 512,
            total: 2048,
            percentage: 25
          },
          cpuUsage: 35,
          uptime: 86400
        });
      }
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkApiEndpoints = async () => {
    const endpoints = [
      '/api/auth/session',
      '/api/dashboard/stats',
      '/api/analytics/summary',
      '/api/chat/sessions',
      '/api/admin/users'
    ];

    const results: ApiEndpointStatus[] = [];

    for (const endpoint of endpoints) {
      const startTime = Date.now();
      try {
        const response = await fetch(endpoint, { method: 'HEAD' });
        const latency = Date.now() - startTime;

        results.push({
          endpoint,
          status: response.ok ? 'healthy' : response.status < 500 ? 'degraded' : 'error',
          latency,
          lastChecked: new Date().toISOString()
        });
      } catch (error) {
        results.push({
          endpoint,
          status: 'error',
          latency: Date.now() - startTime,
          lastChecked: new Date().toISOString()
        });
      }
    }

    setApiEndpoints(results);
  };

  const fetchDebugLogs = () => {
    // In production, fetch from actual logging service
    const mockLogs: DebugLog[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'info',
        message: 'Application initialized successfully',
        source: 'system'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: 'warning',
        message: 'High memory usage detected: 85%',
        source: 'monitoring'
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'error',
        message: 'Failed to connect to external service',
        source: 'api'
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 180000).toISOString(),
        level: 'debug',
        message: 'Cache invalidated: user-sessions',
        source: 'cache'
      }
    ];

    setDebugLogs(mockLogs);
  };

  const refreshAll = () => {
    fetchSystemInfo();
    checkApiEndpoints();
    fetchDebugLogs();
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'debug':
        return <Terminal className="h-4 w-4 text-gray-600" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const exportDebugData = () => {
    const data = {
      systemInfo,
      apiEndpoints,
      debugLogs,
      timestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bug className="h-5 w-5" />
              Debug Panel
            </div>
            <div className="flex gap-2">
              <Button onClick={exportDebugData} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button onClick={refreshAll} disabled={isLoading} size="sm">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            System diagnostics and debugging tools
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="system">System</TabsTrigger>
              <TabsTrigger value="api">API Status</TabsTrigger>
              <TabsTrigger value="logs">Logs</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
            </TabsList>

            {/* System Info Tab */}
            <TabsContent value="system" className="space-y-4">
              {systemInfo ? (
                <>
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Cpu className="h-4 w-4" />
                          Runtime
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Runtime:</span>
                            <span className="font-medium">{systemInfo.runtime}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Version:</span>
                            <span className="font-medium">{systemInfo.version}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Platform:</span>
                            <span className="font-medium">{systemInfo.platform}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Uptime:</span>
                            <span className="font-medium">{formatUptime(systemInfo.uptime)}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <HardDrive className="h-4 w-4" />
                          Resources
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-muted-foreground">Memory</span>
                              <span className="font-medium">{systemInfo.memoryUsage.percentage}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                              <div
                                className="bg-primary rounded-full h-2"
                                style={{ width: `${systemInfo.memoryUsage.percentage}%` }}
                              />
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {systemInfo.memoryUsage.used}MB / {systemInfo.memoryUsage.total}MB
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-muted-foreground">CPU</span>
                              <span className="font-medium">{systemInfo.cpuUsage}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                              <div
                                className="bg-primary rounded-full h-2"
                                style={{ width: `${systemInfo.cpuUsage}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <div className="animate-pulse space-y-3">
                  <div className="h-32 bg-muted rounded" />
                </div>
              )}
            </TabsContent>

            {/* API Status Tab */}
            <TabsContent value="api" className="space-y-3">
              {apiEndpoints.length > 0 ? (
                apiEndpoints.map((endpoint) => (
                  <div key={endpoint.endpoint} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(endpoint.status)}
                      <div>
                        <div className="font-medium text-sm">{endpoint.endpoint}</div>
                        <div className="text-xs text-muted-foreground">
                          Last checked: {new Date(endpoint.lastChecked).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={endpoint.status === 'healthy' ? 'default' : 'destructive'}>
                        {endpoint.latency}ms
                      </Badge>
                    </div>
                  </div>
                ))
              ) : (
                <Alert>
                  <AlertDescription>Click Refresh to check API endpoint status</AlertDescription>
                </Alert>
              )}
            </TabsContent>

            {/* Logs Tab */}
            <TabsContent value="logs" className="space-y-3">
              <div className="max-h-96 overflow-y-auto space-y-2">
                {debugLogs.map((log) => (
                  <div key={log.id} className="flex items-start gap-3 p-3 border rounded text-sm">
                    {getLogIcon(log.level)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {log.level.toUpperCase()}
                        </Badge>
                        {log.source && (
                          <Badge variant="secondary" className="text-xs">
                            {log.source}
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-sm">{log.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* Performance Tab */}
            <TabsContent value="performance" className="space-y-4">
              <Alert>
                <Activity className="h-4 w-4" />
                <AlertDescription>
                  Performance monitoring dashboard - Track response times, throughput, and resource usage
                </AlertDescription>
              </Alert>

              <div className="grid md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Avg Response Time</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {apiEndpoints.length > 0
                        ? Math.round(apiEndpoints.reduce((acc, e) => acc + e.latency, 0) / apiEndpoints.length)
                        : 0}ms
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Healthy Endpoints</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {apiEndpoints.filter(e => e.status === 'healthy').length}/{apiEndpoints.length}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">System Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Badge variant="default" className="text-lg">
                      {systemInfo && systemInfo.memoryUsage.percentage < 80 ? 'Healthy' : 'Warning'}
                    </Badge>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default DebugPanel;
