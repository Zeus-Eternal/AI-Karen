// ui_launchers/KAREN-Theme-Default/src/components/performance/ResourceMonitoringDashboard.tsx
"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ErrorBoundary,
  type ErrorFallbackProps,
} from "@/components/error-handling/ErrorBoundary";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// Resource monitoring services
import {
  resourceMonitor,
  type ResourceMetrics,
  type ResourceAlert,
  type ScalingRecommendation,
  type CapacityPlan,
} from "@/services/resource-monitor";
import {
  Cpu,
  MemoryStick,
  Network,
  HardDrive,
  AlertTriangle,
  Activity,
  CheckCircle,
  Zap,
  TrendingUp,
  TrendingDown,
  X,
} from "lucide-react";

export interface ResourceMonitoringDashboardProps {
  refreshInterval?: number;
  showCapacityPlanning?: boolean;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];
type BadgeVariant = NonNullable<BadgeProps["variant"]>;
type Timeframe = "1h" | "6h" | "24h" | "7d";
const TIMEFRAME_OPTIONS: readonly Timeframe[] = ["1h", "6h", "24h", "7d"];
type AlertBoxProps = React.ComponentPropsWithoutRef<"div"> & {
  variant?: "default" | "destructive";
};
const AlertBox = Alert as React.ComponentType<AlertBoxProps>;

const ResourceMonitoringFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
}) => (
  <div className="space-y-2 p-4">
    <p className="font-medium">Something went wrong in ResourceMonitoringDashboard.</p>
    <Button variant="outline" size="sm" onClick={resetError}>
      Try again
    </Button>
  </div>
);

const isTimeframe = (value: string): value is Timeframe =>
  (TIMEFRAME_OPTIONS as readonly string[]).includes(value);

export const ResourceMonitoringDashboard: React.FC<ResourceMonitoringDashboardProps> = ({
  refreshInterval = 5000,
  showCapacityPlanning = true,
}) => {
  const [currentMetrics, setCurrentMetrics] = useState<ResourceMetrics | null>(null);
  const [historicalMetrics, setHistoricalMetrics] = useState<ResourceMetrics[]>([]);
  const [alerts, setAlerts] = useState<ResourceAlert[]>([]);
  const [recommendations, setRecommendations] = useState<ScalingRecommendation[]>([]);
  const [capacityPlans, setCapacityPlans] = useState<CapacityPlan[]>([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>("1h");
  const timeWindowAnchorRef = useRef<number>(Date.now());

  useEffect(() => {
    const updateData = () => {
      setCurrentMetrics(resourceMonitor.getCurrentMetrics());
      setHistoricalMetrics(resourceMonitor.getHistoricalMetrics(100));
      setAlerts(resourceMonitor.getAlerts());
      setRecommendations(resourceMonitor.getScalingRecommendations());

      if (showCapacityPlanning) {
        setCapacityPlans(resourceMonitor.generateCapacityPlan("3months"));
      }
      timeWindowAnchorRef.current = Date.now();
    };

    updateData();
    const interval = setInterval(updateData, refreshInterval);

    const unsubscribe = resourceMonitor.onAlert((alert) => {
      setAlerts((prev) => [alert, ...prev.slice(0, 19)]);
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [refreshInterval, showCapacityPlanning]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNow(Date.now());
    }, 60_000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  const filteredHistoricalData = useMemo(() => {
    const timeRanges = {
      "1h": 60 * 60 * 1000,
      "6h": 6 * 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
    };

    const cutoff = timeWindowAnchorRef.current - timeRanges[selectedTimeframe];
    return historicalMetrics
      .filter((m) => m.timestamp > cutoff)
      .map((m) => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        timestamp: m.timestamp,
        cpu: m.cpu.usage,
        memory: m.memory.percentage,
        network: m.network.latency,
        storage: m.storage.percentage,
      }));
  }, [currentMetrics, historicalMetrics, selectedTimeframe]);

  const handleResolveAlert = (alertId: string) => {
    resourceMonitor.resolveAlert(alertId);
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );
  };

  const getSeverityColor = (
    severity: ResourceAlert["severity"] | ScalingRecommendation["priority"]
  ): BadgeVariant => {
    switch (severity) {
      case "critical":
        return "destructive";
      case "high":
        return "secondary";
      case "medium":
        return "secondary";
      case "low":
        return "outline";
      default:
        return "outline";
    }
  };

  const getSeverityIcon = (severity: ResourceAlert["severity"]) => {
    switch (severity) {
      case "critical":
        return <AlertTriangle className="h-4 w-4 text-red-500 " />;
      case "high":
        return <AlertTriangle className="h-4 w-4 text-orange-500 " />;
      case "medium":
        return <Activity className="h-4 w-4 text-yellow-500 " />;
      case "low":
        return <Activity className="h-4 w-4 text-blue-500 " />;
      default:
        return <Activity className="h-4 w-4 " />;
    }
  };

  const getResourceIcon = (
    resource: ResourceAlert["type"] | ScalingRecommendation["resource"]
  ) => {
    switch (resource) {
      case "cpu":
        return <Cpu className="h-4 w-4 " />;
      case "memory":
        return <MemoryStick className="h-4 w-4 " />;
      case "network":
        return <Network className="h-4 w-4 " />;
      case "storage":
        return <HardDrive className="h-4 w-4 " />;
      default:
        return <Activity className="h-4 w-4 " />;
    }
  };

  const getRecommendationIcon = (type: ScalingRecommendation["type"]) => {
    switch (type) {
      case "scale-up":
        return <TrendingUp className="h-4 w-4 text-green-500 " />;
      case "scale-down":
        return <TrendingDown className="h-4 w-4 text-blue-500 " />;
      case "optimize":
        return <Zap className="h-4 w-4 text-yellow-500 " />;
      default:
        return <Activity className="h-4 w-4 " />;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  return (
    <ErrorBoundary fallback={ResourceMonitoringFallback}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Resource Monitoring</h2>
            <p className="text-muted-foreground"></p>
          </div>
          <div className="flex items-center space-x-2">
            <Tabs
              value={selectedTimeframe}
              onValueChange={(value) => {
                if (isTimeframe(value)) {
                  timeWindowAnchorRef.current = Date.now();
                  setSelectedTimeframe(value);
                }
              }}
            >
              <TabsList>
                <TabsTrigger value="1h">1H</TabsTrigger>
                <TabsTrigger value="6h">6H</TabsTrigger>
                <TabsTrigger value="24h">24H</TabsTrigger>
                <TabsTrigger value="7d">7D</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {/* Current Resource Status */}
        {currentMetrics && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* CPU Usage Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  CPU Usage
                </CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground " />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentMetrics.cpu.usage.toFixed(1)}%</div>
                <Progress value={currentMetrics.cpu.usage} className="mt-2" />
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {currentMetrics.cpu.cores} cores available
                </p>
              </CardContent>
            </Card>

            {/* Memory Usage Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Memory Usage
                </CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground " />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentMetrics.memory.percentage.toFixed(1)}%</div>
                <Progress value={currentMetrics.memory.percentage} className="mt-2" />
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {formatBytes(currentMetrics.memory.used)} / {formatBytes(currentMetrics.memory.total)}
                </p>
              </CardContent>
            </Card>

            {/* Network Latency Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Network Latency
                </CardTitle>
                <Network className="h-4 w-4 text-muted-foreground " />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentMetrics.network.latency.toFixed(0)}ms</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {currentMetrics.network.bandwidth}Mbps • {currentMetrics.network.connectionType}
                </p>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {formatBytes(currentMetrics.network.bytesReceived)} received
                </p>
              </CardContent>
            </Card>

            {/* Storage Usage Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
                  Storage Usage
                </CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground " />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentMetrics.storage.percentage.toFixed(1)}%</div>
                <Progress value={currentMetrics.storage.percentage} className="mt-2" />
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {formatBytes(currentMetrics.storage.used)} / {formatBytes(currentMetrics.storage.total)}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Active Alerts */}
        {alerts.filter((a) => !a.resolved).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-500 " />
                <span>Active Alerts</span>
                <Badge variant="destructive">
                  {alerts.filter((a) => !a.resolved).length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="space-y-2">
                  {alerts
                    .filter((a) => !a.resolved)
                    .slice(0, 10)
                    .map((alert) => (
                      <AlertBox
                        key={alert.id}
                        variant={alert.severity === "critical" ? "destructive" : "default"}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2">
                            {getSeverityIcon(alert.severity)}
                            <div>
                              <AlertTitle className="flex items-center space-x-2">
                                {getResourceIcon(alert.type)}
                                <span>{alert.type.toUpperCase()} Alert</span>
                                <Badge variant={getSeverityColor(alert.severity)}>
                                  {alert.severity}
                                </Badge>
                              </AlertTitle>
                              <AlertDescription>
                                {alert.message}
                                <br />
                                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                  {new Date(alert.timestamp).toLocaleString()}
                                </span>
                              </AlertDescription>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleResolveAlert(alert.id)}
                          >
                            <X className="h-4 w-4 " />
                          </Button>
                        </div>
                      </AlertBox>
                    ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Resource Charts */}
        <Tabs defaultValue="trends" className="space-y-4">
          <TabsList>
            <TabsTrigger value="trends">Resource Trends</TabsTrigger>
            <TabsTrigger value="distribution">Resource Distribution</TabsTrigger>
            <TabsTrigger value="recommendations">Scaling Recommendations</TabsTrigger>
            {showCapacityPlanning && <TabsTrigger value="capacity">Capacity Planning</TabsTrigger>}
          </TabsList>

          {/* Trends Tab Content */}
          <TabsContent value="trends" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* CPU & Memory Usage Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>CPU & Memory Usage</CardTitle>
                  <CardDescription>Resource utilization over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={filteredHistoricalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                      <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Network & Storage Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Network & Storage</CardTitle>
                  <CardDescription>Network latency and storage usage</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={filteredHistoricalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="network" stroke="#ffc658" name="Latency (ms)" />
                      <Line type="monotone" dataKey="storage" stroke="#ff7300" name="Storage %" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Distribution Tab Content */}
          <TabsContent value="distribution" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Current Resource Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={currentMetrics
                        ? [
                            { name: "CPU", value: currentMetrics.cpu.usage, fill: COLORS[0] },
                            { name: "Memory", value: currentMetrics.memory.percentage, fill: COLORS[1] },
                            { name: "Storage", value: currentMetrics.storage.percentage, fill: COLORS[2] },
                            { name: "Available", value: 100 - Math.max(currentMetrics.cpu.usage, currentMetrics.memory.percentage, currentMetrics.storage.percentage), fill: COLORS[3] },
                          ]
                        : []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {currentMetrics &&
                        [0, 1, 2, 3].map((index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recommendations Tab Content */}
          <TabsContent value="recommendations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Scaling Recommendations</CardTitle>
                <CardDescription></CardDescription>
              </CardHeader>
              <CardContent>
                {recommendations.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4 " />
                    <h3 className="text-lg font-medium">Resources Optimized</h3>
                    <p className="text-muted-foreground">No scaling recommendations at this time.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {recommendations.map((rec) => (
                      <div key={rec.id} className="border rounded-lg p-4 sm:p-4 md:p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="flex items-center space-x-2">
                              {getResourceIcon(rec.resource)}
                              {getRecommendationIcon(rec.type)}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <h4 className="font-medium">{rec.title}</h4>
                                <Badge variant={getSeverityColor(rec.priority)}>
                                  {rec.priority}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                                {rec.description}
                              </p>
                              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                <p><strong>Impact:</strong> {rec.impact}</p>
                                <p><strong>Implementation:</strong> {rec.implementation}</p>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium md:text-base lg:text-lg">
                              {rec.estimatedCost > 0 && (
                                <div className="text-red-600">
                                  Cost: {formatCurrency(rec.estimatedCost)}
                                </div>
                              )}
                              {rec.estimatedSavings > 0 && (
                                <div className="text-green-600">
                                  Savings: {formatCurrency(rec.estimatedSavings)}
                                </div>
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              {rec.confidence}% confidence
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Capacity Planning Tab Content */}
          {showCapacityPlanning && (
            <TabsContent value="capacity" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Capacity Planning</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {capacityPlans.map((plan) => (
                      <div key={plan.resource} className="border rounded-lg p-4 sm:p-4 md:p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center space-x-2">
                            {getResourceIcon(plan.resource)}
                            <h4 className="font-medium capitalize">{plan.resource} Capacity</h4>
                          </div>
                          <Badge variant="outline">{plan.timeframe}</Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Current Usage</p>
                            <p className="text-lg font-medium">{plan.currentUsage.toFixed(1)}%</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Projected Usage</p>
                            <p className="text-lg font-medium">{plan.projectedUsage.toFixed(1)}%</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Growth Rate</p>
                            <p className="text-lg font-medium">{plan.growthRate.toFixed(1)}%/month</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Cost Impact</p>
                            <p className="text-lg font-medium">
                              {plan.costImpact > 0 ? formatCurrency(plan.costImpact) : 'No change'}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between text-sm md:text-base lg:text-lg">
                            <span>Current</span>
                            <span>Projected</span>
                          </div>
                          <Progress value={plan.currentUsage} className="h-2" />
                          <Progress value={plan.projectedUsage} className="h-2" />
                        </div>

                        {plan.projectedUsage > 80 && (
                          <AlertBox className="mt-4">
                            <AlertTriangle className="h-4 w-4 " />
                            <AlertTitle>Capacity Warning</AlertTitle>
                            <AlertDescription>
                              Projected {plan.resource} usage will exceed 80% in {plan.timeframe}.
                              Consider scaling up resources.
                            </AlertDescription>
                          </AlertBox>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </div>
    </ErrorBoundary>
  );
};
