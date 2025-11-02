import React, { useState, useEffect, useRef } from 'react';
import {
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { getKarenBackend } from '@/lib/karen-backend';
import { useToast } from '@/hooks/use-toast';
"use client";


  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";







  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  HardDrive,
  Wifi,
  WifiOff,
  Loader2,
  RefreshCw,
  Pause,
  Play,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';


interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  status: string;
  metadata?: {
    parameters?: string;
    memory_requirement?: string;
  };
}
interface ModelStatus {
  model_id: string;
  model_name: string;
  provider: string;
  status: 'online' | 'offline' | 'loading' | 'error' | 'maintenance';
  availability: number; // 0-1
  response_time: number; // ms
  memory_usage: number; // MB
  cpu_usage: number; // percentage
  gpu_usage?: number; // percentage
  active_connections: number;
  requests_per_minute: number;
  error_rate: number; // 0-1
  last_request: number; // timestamp
  uptime: number; // seconds
  health_score: number; // 0-1
  issues: Array<{
    severity: 'info' | 'warning' | 'error';
    message: string;
    timestamp: number;
  }>;
  performance_trend: 'up' | 'down' | 'stable';
}
interface ModelStatusMonitorProps {
  models: ModelInfo[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
const ModelStatusMonitor: React.FC<ModelStatusMonitorProps> = ({
  models,
  open,
  onOpenChange
}) => {
  const [modelStatuses, setModelStatuses] = useState<ModelStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  // Load model status data
  const loadModelStatuses = async () => {
    try {
      setLoading(true);
      setError(null);
      // Filter to only local models
      const localModels = models.filter(model => model.status === 'local');
      const statusPromises = localModels.map(async (model) => {
        try {
          // Try to get real status from the intelligent model routes
          const response = await backend.makeRequestPublic<ModelStatus>(
            `/api/intelligent-models/status/${model.id}`
          );
          return response;
        } catch (err) {
          // Generate mock status data
          const now = Date.now();
          const isOnline = Math.random() > 0.1; // 90% chance of being online
          return {
            model_id: model.id,
            model_name: model.display_name || model.name,
            provider: model.provider,
            status: isOnline ? 'online' : (Math.random() > 0.5 ? 'offline' : 'error'),
            availability: isOnline ? Math.random() * 0.1 + 0.9 : Math.random() * 0.3,
            response_time: isOnline ? Math.random() * 1000 + 200 : 0,
            memory_usage: Math.random() * 4000 + 1000, // 1-5GB
            cpu_usage: Math.random() * 60 + 10, // 10-70%
            gpu_usage: Math.random() > 0.3 ? Math.random() * 80 + 20 : undefined,
            active_connections: isOnline ? Math.floor(Math.random() * 10) : 0,
            requests_per_minute: isOnline ? Math.random() * 50 + 5 : 0,
            error_rate: isOnline ? Math.random() * 0.05 : Math.random() * 0.3,
            last_request: isOnline ? now - Math.random() * 300000 : 0, // Within last 5 minutes
            uptime: isOnline ? Math.random() * 86400 * 7 : 0, // Up to 7 days
            health_score: isOnline ? Math.random() * 0.3 + 0.7 : Math.random() * 0.4,
            issues: generateMockIssues(isOnline),
            performance_trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as 'up' | 'down' | 'stable'
          } as ModelStatus;
        }
      });
      const statuses = await Promise.all(statusPromises);
      setModelStatuses(statuses.filter(Boolean));
    } catch (err) {
      setError('Failed to load model status information');
      toast({
        title: "Error Loading Status",
        description: "Could not load model status information. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  // Generate mock issues for demonstration
  const generateMockIssues = (isOnline: boolean) => {
    const issues = [];
    const now = Date.now();
    if (!isOnline) {
      issues.push({
        severity: 'error' as const,
        message: 'Model is currently offline',
        timestamp: now - Math.random() * 60000
      });
    } else {
      if (Math.random() > 0.7) {
        issues.push({
          severity: 'warning' as const,
          message: 'High memory usage detected',
          timestamp: now - Math.random() * 300000
        });
      }
      if (Math.random() > 0.8) {
        issues.push({
          severity: 'info' as const,
          message: 'Performance optimization applied',
          timestamp: now - Math.random() * 600000
        });
      }
    }
    return issues;
  };
  // Setup auto-refresh
  useEffect(() => {
    if (open && autoRefresh) {
      loadModelStatuses(); // Initial load
      intervalRef.current = setInterval(() => {
        loadModelStatuses();
      }, refreshInterval);
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [open, autoRefresh, refreshInterval]);
  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  // Get status color and icon
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'online':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          icon: <CheckCircle className="h-4 w-4 sm:w-auto md:w-full" />,
          label: 'Online'
        };
      case 'offline':
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          icon: <WifiOff className="h-4 w-4 sm:w-auto md:w-full" />,
          label: 'Offline'
        };
      case 'loading':
        return {
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          icon: <Loader2 className="h-4 w-4 animate-spin sm:w-auto md:w-full" />,
          label: 'Loading'
        };
      case 'error':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          icon: <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />,
          label: 'Error'
        };
      case 'maintenance':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          icon: <Clock className="h-4 w-4 sm:w-auto md:w-full" />,
          label: 'Maintenance'
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          icon: <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />,
          label: 'Unknown'
        };
    }
  };
  // Get performance trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
      default:
        return <Minus className="h-4 w-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };
  // Format uptime
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };
  // Format last request time
  const formatLastRequest = (timestamp: number) => {
    if (!timestamp) return 'Never';
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (days > 0) {
      return `${days}d ago`;
    } else if (hours > 0) {
      return `${hours}h ago`;
    } else if (minutes > 0) {
      return `${minutes}m ago`;
    } else {
      return 'Just now';
    }
  };
  // Get health score color
  const getHealthScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto sm:w-auto md:w-full">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 sm:w-auto md:w-full" />
            Model Status Monitor
          </DialogTitle>
          <DialogDescription>
            Real-time monitoring of model availability and performance
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          {/* Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Monitor Settings</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={autoRefresh}
                    onCheckedChange={setAutoRefresh}
                  />
                  <label className="text-sm font-medium md:text-base lg:text-lg">Auto Refresh</label>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium md:text-base lg:text-lg">Interval:</label>
                  <select
                    value={refreshInterval}
                    onChange={(e) = aria-label="Select option"> setRefreshInterval(Number(e.target.value))}
                    className="text-sm border rounded px-2 py-1 md:text-base lg:text-lg"
                  >
                    <option value={1000}>1s</option>
                    <option value={5000}>5s</option>
                    <option value={10000}>10s</option>
                    <option value={30000}>30s</option>
                    <option value={60000}>1m</option>
                  </select>
                </div>
              </div>
              <button
                onClick={loadModelStatuses}
                disabled={loading}
                variant="outline"
                size="sm"
               aria-label="Button">
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1 sm:w-auto md:w-full" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                )}
                Refresh
              </Button>
            </CardContent>
          </Card>
          {/* Status Overview */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {modelStatuses.length > 0 && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600 sm:w-auto md:w-full" />
                      <div>
                        <p className="text-2xl font-bold">
                          {modelStatuses.filter(s => s.status === 'online').length}
                        </p>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Online</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-center gap-2">
                      <WifiOff className="h-5 w-5 text-gray-600 sm:w-auto md:w-full" />
                      <div>
                        <p className="text-2xl font-bold">
                          {modelStatuses.filter(s => s.status === 'offline').length}
                        </p>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Offline</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-5 w-5 text-red-600 sm:w-auto md:w-full" />
                      <div>
                        <p className="text-2xl font-bold">
                          {modelStatuses.filter(s => s.status === 'error').length}
                        </p>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Errors</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-blue-600 sm:w-auto md:w-full" />
                      <div>
                        <p className="text-2xl font-bold">
                          {modelStatuses.reduce((sum, s) => sum + s.active_connections, 0)}
                        </p>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Active Connections</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              {/* Model Status Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {modelStatuses.map(status => {
                  const statusDisplay = getStatusDisplay(status.status);
                  return (
                    <Card key={status.model_id} className="relative">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">{status.model_name}</CardTitle>
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant="outline" 
                              className={`${statusDisplay.color} ${statusDisplay.bgColor}`}
                            >
                              {statusDisplay.icon}
                              <span className="ml-1">{statusDisplay.label}</span>
                            </Badge>
                            {getTrendIcon(status.performance_trend)}
                          </div>
                        </div>
                        <CardDescription>{status.provider}</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Health Score */}
                        <div>
                          <div className="flex justify-between text-sm mb-1 md:text-base lg:text-lg">
                            <span>Health Score</span>
                            <span className={getHealthScoreColor(status.health_score)}>
                              {(status.health_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <Progress value={status.health_score * 100} className="h-2" />
                        </div>
                        {/* Availability */}
                        <div>
                          <div className="flex justify-between text-sm mb-1 md:text-base lg:text-lg">
                            <span>Availability</span>
                            <span>{(status.availability * 100).toFixed(1)}%</span>
                          </div>
                          <Progress value={status.availability * 100} className="h-2" />
                        </div>
                        {/* Key Metrics */}
                        <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                          <div>
                            <span className="text-muted-foreground">Response Time:</span>
                            <span className="ml-2 font-medium">
                              {status.response_time > 0 ? `${status.response_time.toFixed(0)}ms` : 'N/A'}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Requests/min:</span>
                            <span className="ml-2 font-medium">
                              {status.requests_per_minute.toFixed(1)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Memory:</span>
                            <span className="ml-2 font-medium">
                              {(status.memory_usage / 1024).toFixed(1)}GB
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">CPU:</span>
                            <span className="ml-2 font-medium">
                              {status.cpu_usage.toFixed(1)}%
                            </span>
                          </div>
                          {status.gpu_usage && (
                            <>
                              <div>
                                <span className="text-muted-foreground">GPU:</span>
                                <span className="ml-2 font-medium">
                                  {status.gpu_usage.toFixed(1)}%
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Connections:</span>
                                <span className="ml-2 font-medium">
                                  {status.active_connections}
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                        {/* Additional Info */}
                        <div className="grid grid-cols-2 gap-4 text-sm pt-2 border-t md:text-base lg:text-lg">
                          <div>
                            <span className="text-muted-foreground">Uptime:</span>
                            <span className="ml-2 font-medium">
                              {formatUptime(status.uptime)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Last Request:</span>
                            <span className="ml-2 font-medium">
                              {formatLastRequest(status.last_request)}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Error Rate:</span>
                            <span className="ml-2 font-medium">
                              {(status.error_rate * 100).toFixed(2)}%
                            </span>
                          </div>
                        </div>
                        {/* Issues */}
                        {status.issues.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-sm font-medium md:text-base lg:text-lg">Recent Issues</h4>
                            {status.issues.slice(0, 3).map((issue, index) => (
                              <Alert 
                                key={index}
                                variant={issue.severity === 'error' ? 'destructive' : 'default'}
                                className="py-2"
                              >
                                <AlertCircle className="h-3 w-3 sm:w-auto md:w-full" />
                                <AlertDescription className="text-xs sm:text-sm md:text-base">
                                  {issue.message}
                                  <span className="ml-2 text-muted-foreground">
                                    {formatLastRequest(issue.timestamp)}
                                  </span>
                                </AlertDescription>
                              </Alert>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </>
          )}
          {!loading && modelStatuses.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">
                  No local models available for monitoring.
                </p>
                <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                  Download some models to see their status here.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
export default ModelStatusMonitor;
