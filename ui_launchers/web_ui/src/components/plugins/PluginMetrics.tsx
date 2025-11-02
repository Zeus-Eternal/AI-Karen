import React, { useState, useEffect } from 'react';
import { 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { PluginInfo, PluginMetrics as PluginMetricsType } from '@/types/plugins';
/**
 * Plugin Metrics Component
 * 
 * Displays performance statistics and resource usage for plugins.
 * Based on requirements: 5.4, 10.3
 */

"use client";



  Activity, 
  Clock, 
  Cpu, 
  HardDrive, 
  Network, 
  MemoryStick,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Timer,
  BarChart3,
  LineChart,
  PieChart,
  Settings,
  RefreshCw,
  Download,
  Upload,
  Database,
  Gauge,
  Target,
  AlertCircle,
  Info,
  Filter,
  Calendar,
  Eye,
  EyeOff,
} from 'lucide-react';








  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';



  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';



// Chart component placeholder (would use AG-Charts in real implementation)
const MetricChart: React.FC<{
  data: Array<{ timestamp: Date; value: number }>;
  type: 'line' | 'bar' | 'area';
  color: string;
  height?: number;
}> = ({ data, type, color, height = 200 }) => (
  <div 
    className="flex items-center justify-center border rounded-lg bg-muted/20"
    style={{ height }}
  >
    <div className="text-center text-muted-foreground">
      <BarChart3 className="w-8 h-8 mx-auto mb-2 sm:w-auto md:w-full" />
      <p className="text-sm md:text-base lg:text-lg">Chart: {data.length} data points</p>
      <p className="text-xs sm:text-sm md:text-base">Type: {type}</p>
    </div>
  </div>
);

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'good' | 'warning' | 'critical';
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon: Icon,
  trend,
  trendValue,
  status = 'good',
  description,
}) => {
  const statusColors = {
    good: 'text-green-600',
    warning: 'text-yellow-600',
    critical: 'text-red-600',
  };

  const trendIcons = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Activity,
  };

  const TrendIcon = trend ? trendIcons[trend] : null;

  return (
    <Card>
      <CardContent className="p-4 sm:p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`w-4 h-4 ${statusColors[status]}`} />
            <span className="text-sm font-medium md:text-base lg:text-lg">{title}</span>
          </div>
          {trend && TrendIcon && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
              <TrendIcon className="w-3 h-3 sm:w-auto md:w-full" />
              {trendValue && `${trendValue > 0 ? '+' : ''}${trendValue}%`}
            </div>
          )}
        </div>
        <div className="mt-2">
          <div className="text-2xl font-bold">
            {typeof value === 'number' ? value.toLocaleString() : value}
            {unit && <span className="text-sm font-normal text-muted-foreground ml-1 md:text-base lg:text-lg">{unit}</span>}
          </div>
          {description && (
            <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface PerformanceAlertsProps {
  plugin: PluginInfo;
  alerts: Array<{
    id: string;
    type: 'performance' | 'resource' | 'error' | 'health';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    timestamp: Date;
    threshold?: number;
    currentValue?: number;
  }>;
  onDismiss: (alertId: string) => void;
}

const PerformanceAlerts: React.FC<PerformanceAlertsProps> = ({
  plugin,
  alerts,
  onDismiss,
}) => {
  const severityConfig = {
    low: { variant: 'default' as const, icon: Info, color: 'text-blue-600' },
    medium: { variant: 'default' as const, icon: AlertCircle, color: 'text-yellow-600' },
    high: { variant: 'destructive' as const, icon: AlertTriangle, color: 'text-orange-600' },
    critical: { variant: 'destructive' as const, icon: XCircle, color: 'text-red-600' },
  };

  if (alerts.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center sm:p-4 md:p-6">
          <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600 sm:w-auto md:w-full" />
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No active alerts</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 sm:w-auto md:w-full" />
          Performance Alerts
          <Badge variant="outline">{alerts.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.map((alert) => {
            const config = severityConfig[alert.severity];
            const AlertIcon = config.icon;
            
            return (
              <Alert key={alert.id} variant={config.variant}>
                <AlertIcon className="w-4 h-4 sm:w-auto md:w-full" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <AlertDescription className="font-medium">
                      {alert.message}
                    </AlertDescription>
                    <button
                      variant="ghost"
                      size="sm"
                      onClick={() = aria-label="Button"> onDismiss(alert.id)}
                    >
                      <XCircle className="w-3 h-3 sm:w-auto md:w-full" />
                    </Button>
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground sm:text-sm md:text-base">
                    <span className="capitalize">{alert.type}</span>
                    <span className="capitalize">{alert.severity}</span>
                    <span>{alert.timestamp.toLocaleString()}</span>
                    {alert.threshold && alert.currentValue && (
                      <span>
                        {alert.currentValue} / {alert.threshold}
                      </span>
                    )}
                  </div>
                </div>
              </Alert>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

interface PluginMetricsProps {
  plugin: PluginInfo;
  onRefresh?: () => void;
  onConfigureAlerts?: () => void;
}

export const PluginMetrics: React.FC<PluginMetricsProps> = ({
  plugin,
  onRefresh,
  onConfigureAlerts,
}) => {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [refreshing, setRefreshing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Mock historical data (would come from API in real implementation)
  const [historicalData] = useState({
    performance: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000),
      executionTime: Math.random() * 1000 + 200,
      executions: Math.floor(Math.random() * 50) + 10,
      errorRate: Math.random() * 0.1,
    })),
    resources: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000),
      cpu: Math.random() * 10 + 5,
      memory: Math.random() * 50 + 20,
      network: Math.random() * 5 + 1,
      disk: Math.random() * 10 + 2,
    })),
  });

  // Mock alerts
  const [alerts, setAlerts] = useState([
    {
      id: 'alert-1',
      type: 'performance' as const,
      severity: 'medium' as const,
      message: 'Average execution time increased by 25% in the last hour',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      threshold: 500,
      currentValue: 625,
    },
    {
      id: 'alert-2',
      type: 'resource' as const,
      severity: 'low' as const,
      message: 'Memory usage is approaching 80% of allocated limit',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      threshold: 100,
      currentValue: 78,
    },
  ]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock API call
      onRefresh?.();
    } finally {
      setRefreshing(false);
    }
  };

  const handleDismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const metrics = plugin.metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Plugin Metrics</h2>
          <p className="text-muted-foreground">
            Performance and resource usage for {plugin.name}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <select value={timeRange} onValueChange={(value: any) = aria-label="Select option"> setTimeRange(value)}>
            <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="1h" aria-label="Select option">Last Hour</SelectItem>
              <selectItem value="24h" aria-label="Select option">Last 24h</SelectItem>
              <selectItem value="7d" aria-label="Select option">Last 7 days</SelectItem>
              <selectItem value="30d" aria-label="Select option">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <EyeOff className="w-4 h-4 sm:w-auto md:w-full" /> : <Eye className="w-4 h-4 sm:w-auto md:w-full" />}
            {showAdvanced ? 'Simple' : 'Advanced'}
          </Button>
          
          <button
            variant="outline"
            size="sm"
            onClick={onConfigureAlerts}
           aria-label="Button">
            <Settings className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Alerts
          </Button>
          
          <button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
           aria-label="Button">
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alerts */}
      <PerformanceAlerts
        plugin={plugin}
        alerts={alerts}
        onDismiss={handleDismissAlert}
      />

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="health">Health</TabsTrigger>
          {showAdvanced && <TabsTrigger value="advanced">Advanced</TabsTrigger>}
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Executions"
              value={metrics.performance.totalExecutions}
              icon={Zap}
              trend="up"
              trendValue={12}
              description="Total executions"
            />
            <MetricCard
              title="Avg Time"
              value={metrics.performance.averageExecutionTime}
              unit="ms"
              icon={Timer}
              trend="up"
              trendValue={5}
              status={metrics.performance.averageExecutionTime > 1000 ? 'warning' : 'good'}
              description="Average execution time"
            />
            <MetricCard
              title="Error Rate"
              value={(metrics.performance.errorRate * 100).toFixed(2)}
              unit="%"
              icon={AlertTriangle}
              trend="down"
              trendValue={-2}
              status={metrics.performance.errorRate > 0.1 ? 'critical' : 
                     metrics.performance.errorRate > 0.05 ? 'warning' : 'good'}
              description="Error rate"
            />
            <MetricCard
              title="Health Score"
              value={metrics.health.uptime.toFixed(1)}
              unit="%"
              icon={Activity}
              trend="stable"
              status={metrics.health.uptime > 95 ? 'good' : 
                     metrics.health.uptime > 90 ? 'warning' : 'critical'}
              description="Uptime percentage"
            />
          </div>

          {/* Resource Usage */}
          <Card>
            <CardHeader>
              <CardTitle>Resource Usage</CardTitle>
              <CardDescription>Current resource consumption</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 sm:w-auto md:w-full" />
                      <span>CPU Usage</span>
                    </div>
                    <span>{metrics.resources.cpuUsage.toFixed(1)}%</span>
                  </div>
                  <Progress value={metrics.resources.cpuUsage} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <div className="flex items-center gap-2">
                      <MemoryStick className="w-4 h-4 sm:w-auto md:w-full" />
                      <span>Memory Usage</span>
                    </div>
                    <span>{metrics.resources.memoryUsage.toFixed(1)} MB</span>
                  </div>
                  <Progress value={(metrics.resources.memoryUsage / 100) * 100} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 sm:w-auto md:w-full" />
                      <span>Network Usage</span>
                    </div>
                    <span>{metrics.resources.networkUsage.toFixed(1)} MB/s</span>
                  </div>
                  <Progress value={(metrics.resources.networkUsage / 10) * 100} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <div className="flex items-center gap-2">
                      <HardDrive className="w-4 h-4 sm:w-auto md:w-full" />
                      <span>Disk Usage</span>
                    </div>
                    <span>{metrics.resources.diskUsage.toFixed(1)} MB</span>
                  </div>
                  <Progress value={(metrics.resources.diskUsage / 50) * 100} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span>Last Execution</span>
                    <span className="text-muted-foreground">
                      {metrics.performance.lastExecution?.toLocaleString() || 'Never'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span>Last Health Check</span>
                    <span className="text-muted-foreground">
                      {metrics.health.lastHealthCheck.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span>Plugin Status</span>
                    <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
                      {plugin.status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Health Issues</CardTitle>
              </CardHeader>
              <CardContent>
                {metrics.health.issues.length === 0 ? (
                  <div className="text-center py-4">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600 sm:w-auto md:w-full" />
                    <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No health issues</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {metrics.health.issues.slice(0, 3).map((issue, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm md:text-base lg:text-lg">
                        <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0 sm:w-auto md:w-full" />
                        <span>{issue}</span>
                      </div>
                    ))}
                    {metrics.health.issues.length > 3 && (
                      <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        +{metrics.health.issues.length - 3} more issues
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Execution Time Trend</CardTitle>
                <CardDescription>Average execution time over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.performance.map(d => ({
                    timestamp: d.timestamp,
                    value: d.executionTime,
                  }))}
                  type="line"
                  color="#3b82f6"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution Count</CardTitle>
                <CardDescription>Number of executions over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.performance.map(d => ({
                    timestamp: d.timestamp,
                    value: d.executions,
                  }))}
                  type="bar"
                  color="#10b981"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Rate Trend</CardTitle>
                <CardDescription>Error rate percentage over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.performance.map(d => ({
                    timestamp: d.timestamp,
                    value: d.errorRate * 100,
                  }))}
                  type="area"
                  color="#ef4444"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Summary</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">P50 Execution Time</span>
                    <span className="font-medium">245ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">P95 Execution Time</span>
                    <span className="font-medium">890ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">P99 Execution Time</span>
                    <span className="font-medium">1.2s</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Success Rate</span>
                    <span className="font-medium text-green-600">
                      {((1 - metrics.performance.errorRate) * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Throughput</span>
                    <span className="font-medium">
                      {(metrics.performance.totalExecutions / 24).toFixed(1)} exec/hour
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>CPU Usage</CardTitle>
                <CardDescription>CPU utilization over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.resources.map(d => ({
                    timestamp: d.timestamp,
                    value: d.cpu,
                  }))}
                  type="line"
                  color="#f59e0b"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Memory Usage</CardTitle>
                <CardDescription>Memory consumption over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.resources.map(d => ({
                    timestamp: d.timestamp,
                    value: d.memory,
                  }))}
                  type="area"
                  color="#8b5cf6"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Network I/O</CardTitle>
                <CardDescription>Network usage over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.resources.map(d => ({
                    timestamp: d.timestamp,
                    value: d.network,
                  }))}
                  type="line"
                  color="#06b6d4"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Disk I/O</CardTitle>
                <CardDescription>Disk usage over {timeRange}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart
                  data={historicalData.resources.map(d => ({
                    timestamp: d.timestamp,
                    value: d.disk,
                  }))}
                  type="bar"
                  color="#84cc16"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Health Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center ${
                    metrics.health.status === 'healthy' ? 'bg-green-100 text-green-600' :
                    metrics.health.status === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-red-100 text-red-600'
                  }`}>
                    {metrics.health.status === 'healthy' ? (
                      <CheckCircle className="w-8 h-8 sm:w-auto md:w-full" />
                    ) : metrics.health.status === 'warning' ? (
                      <AlertTriangle className="w-8 h-8 sm:w-auto md:w-full" />
                    ) : (
                      <XCircle className="w-8 h-8 sm:w-auto md:w-full" />
                    )}
                  </div>
                  <h3 className="font-medium capitalize">{metrics.health.status}</h3>
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    {metrics.health.uptime.toFixed(1)}% uptime
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Health Checks</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">API Connectivity</span>
                    <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Dependencies</span>
                    <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Configuration</span>
                    <AlertTriangle className="w-4 h-4 text-yellow-600 sm:w-auto md:w-full" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Permissions</span>
                    <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-32">
                  <div className="space-y-2">
                    {metrics.health.issues.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4 md:text-base lg:text-lg">
                        No recent issues
                      </p>
                    ) : (
                      metrics.health.issues.map((issue, index) => (
                        <div key={index} className="text-sm p-2 bg-muted/50 rounded md:text-base lg:text-lg">
                          {issue}
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {showAdvanced && (
          <TabsContent value="advanced" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Metrics</CardTitle>
                  <CardDescription>Advanced performance metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm md:text-base lg:text-lg">
                    <div className="flex justify-between">
                      <span>Memory Heap Size</span>
                      <span>24.5 MB</span>
                    </div>
                    <div className="flex justify-between">
                      <span>GC Collections</span>
                      <span>142</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Event Loop Lag</span>
                      <span>2.3ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Handles</span>
                      <span>8</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Requests</span>
                      <span>3</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>System Integration</CardTitle>
                  <CardDescription>Plugin system integration status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm md:text-base lg:text-lg">
                    <div className="flex justify-between items-center">
                      <span>Hook Registrations</span>
                      <Badge variant="outline">5 active</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>API Endpoints</span>
                      <Badge variant="outline">3 exposed</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Event Listeners</span>
                      <Badge variant="outline">7 registered</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Scheduled Tasks</span>
                      <Badge variant="outline">2 active</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};