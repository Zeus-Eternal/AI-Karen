"use client";

/**
 * System Information
 *
 * Display comprehensive system information including platform details,
 * resource usage, and system health metrics
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Server,
  Cpu,
  HardDrive,
  Activity,
  Info,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  MemoryStick,
  Network
} from 'lucide-react';

export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    model: string;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    usagePercent: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    usagePercent: number;
  };
  network: {
    sent: number;
    received: number;
    connections: number;
  };
}

export interface SystemDetails {
  platform: string;
  architecture: string;
  version: string;
  hostname: string;
  uptime: number;
  nodeVersion: string;
  processId: number;
}

export interface SystemInfoProps {
  refreshInterval?: number;
}

export default function SystemInfo({
  refreshInterval = 5000
}: SystemInfoProps) {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [details, setDetails] = useState<SystemDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadSystemInfo = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/system/info');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics);
        setDetails(data.details);
      } else {
        // Mock data
        const mockMetrics: SystemMetrics = {
          cpu: {
            usage: 45.2,
            cores: 8,
            model: 'Intel Core i7-9700K'
          },
          memory: {
            total: 16384,
            used: 8192,
            free: 8192,
            usagePercent: 50
          },
          disk: {
            total: 512000,
            used: 256000,
            free: 256000,
            usagePercent: 50
          },
          network: {
            sent: 1024000,
            received: 2048000,
            connections: 42
          }
        };

        const mockDetails: SystemDetails = {
          platform: 'Linux',
          architecture: 'x64',
          version: '5.15.0-generic',
          hostname: 'kari-server-01',
          uptime: 345600,
          nodeVersion: 'v20.10.0',
          processId: 12345
        };

        setMetrics(mockMetrics);
        setDetails(mockDetails);
      }
    } catch (error) {
      console.error('Failed to load system info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSystemInfo();
    const interval = setInterval(loadSystemInfo, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getHealthStatus = (percent: number): { color: string; status: string; icon: React.ReactNode } => {
    if (percent < 60) return {
      color: 'text-green-600',
      status: 'Healthy',
      icon: <CheckCircle className="h-4 w-4 text-green-600" />
    };
    if (percent < 80) return {
      color: 'text-yellow-600',
      status: 'Warning',
      icon: <AlertTriangle className="h-4 w-4 text-yellow-600" />
    };
    return {
      color: 'text-red-600',
      status: 'Critical',
      icon: <AlertTriangle className="h-4 w-4 text-red-600" />
    };
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              System Information
            </div>
            <Button onClick={loadSystemInfo} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            System metrics and resource utilization (Updates every {refreshInterval / 1000}s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="metrics">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="metrics">
                <Activity className="h-4 w-4 mr-2" />
                Metrics
              </TabsTrigger>
              <TabsTrigger value="details">
                <Info className="h-4 w-4 mr-2" />
                Details
              </TabsTrigger>
            </TabsList>

            {/* Metrics Tab */}
            <TabsContent value="metrics" className="space-y-6">
              {metrics && (
                <>
                  {/* CPU */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Cpu className="h-4 w-4" />
                          CPU Usage
                        </div>
                        <div className="flex items-center gap-2">
                          {getHealthStatus(metrics.cpu.usage).icon}
                          <span className={`text-sm ${getHealthStatus(metrics.cpu.usage).color}`}>
                            {getHealthStatus(metrics.cpu.usage).status}
                          </span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Usage</span>
                          <span className="text-2xl font-bold">{metrics.cpu.usage.toFixed(1)}%</span>
                        </div>
                        <Progress value={metrics.cpu.usage} />
                      </div>
                      <div className="grid md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Cores:</span>
                          <span className="ml-2 font-medium">{metrics.cpu.cores}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Model:</span>
                          <span className="ml-2 font-medium">{metrics.cpu.model}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Memory */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MemoryStick className="h-4 w-4" />
                          Memory Usage
                        </div>
                        <div className="flex items-center gap-2">
                          {getHealthStatus(metrics.memory.usagePercent).icon}
                          <span className={`text-sm ${getHealthStatus(metrics.memory.usagePercent).color}`}>
                            {getHealthStatus(metrics.memory.usagePercent).status}
                          </span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Usage</span>
                          <span className="text-2xl font-bold">{metrics.memory.usagePercent.toFixed(1)}%</span>
                        </div>
                        <Progress value={metrics.memory.usagePercent} />
                      </div>
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Total:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.memory.total * 1024 * 1024)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Used:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.memory.used * 1024 * 1024)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Free:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.memory.free * 1024 * 1024)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Disk */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <HardDrive className="h-4 w-4" />
                          Disk Usage
                        </div>
                        <div className="flex items-center gap-2">
                          {getHealthStatus(metrics.disk.usagePercent).icon}
                          <span className={`text-sm ${getHealthStatus(metrics.disk.usagePercent).color}`}>
                            {getHealthStatus(metrics.disk.usagePercent).status}
                          </span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Usage</span>
                          <span className="text-2xl font-bold">{metrics.disk.usagePercent.toFixed(1)}%</span>
                        </div>
                        <Progress value={metrics.disk.usagePercent} />
                      </div>
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Total:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.disk.total * 1024 * 1024)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Used:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.disk.used * 1024 * 1024)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Free:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.disk.free * 1024 * 1024)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Network */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Network className="h-4 w-4" />
                        Network Activity
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Sent:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.network.sent)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Received:</span>
                          <span className="ml-2 font-medium">{formatBytes(metrics.network.received)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Connections:</span>
                          <span className="ml-2 font-medium">{metrics.network.connections}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Details Tab */}
            <TabsContent value="details" className="space-y-4">
              {details && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Platform</h4>
                          <p className="text-lg font-semibold">{details.platform}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Architecture</h4>
                          <p className="text-lg font-semibold">{details.architecture}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">OS Version</h4>
                          <p className="text-lg font-semibold">{details.version}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Hostname</h4>
                          <p className="text-lg font-semibold">{details.hostname}</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Uptime</h4>
                          <p className="text-lg font-semibold">{formatUptime(details.uptime)}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Node.js Version</h4>
                          <p className="text-lg font-semibold">{details.nodeVersion}</p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Process ID</h4>
                          <p className="text-lg font-semibold">{details.processId}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { SystemInfo };
export type { SystemInfoProps, SystemMetrics, SystemDetails };
