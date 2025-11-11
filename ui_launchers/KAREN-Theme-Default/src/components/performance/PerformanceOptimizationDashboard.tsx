// ui_launchers/KAREN-Theme-Default/src/components/performance/PerformanceOptimizationDashboard.tsx
"use client";

import React, { useState, useEffect } from "react";
import {
  ErrorBoundary,
  type ErrorFallbackProps,
} from "@/components/error-handling/ErrorBoundary";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

import {
  performanceOptimizer,
  type OptimizationConfig,
  type OptimizationMetrics,
  type OptimizationRecommendation,
} from "@/services/performance-optimizer"; // Ensure this service exists
import {
  AlertTriangle,
  CheckCircle,
  Info,
  Lightbulb,
  Play,
  Package,
  Image,
  Database,
  MemoryStick,
  Zap,
  Settings,
} from "lucide-react";

export interface PerformanceOptimizationDashboardProps {
  autoApply?: boolean;
  showAdvancedSettings?: boolean;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

const PerformanceOptimizationFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
}) => (
  <div className="space-y-2 p-4">
    <p className="font-medium">Something went wrong in PerformanceOptimizationDashboard.</p>
    <Button variant="outline" size="sm" onClick={resetError}>
      Try again
    </Button>
  </div>
);

type BadgeVariant = NonNullable<BadgeProps["variant"]>;

interface OptimizationSettingsProps {
  config: OptimizationConfig;
  onConfigUpdate: (config: Partial<OptimizationConfig>) => void;
}

const SettingToggle: React.FC<{
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}> = ({ label, description, checked, onCheckedChange }) => (
  <div className="flex items-start justify-between rounded-lg border p-4">
    <div className="pr-4">
      <p className="font-medium">{label}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
    <Switch checked={checked} onCheckedChange={onCheckedChange} aria-label={label} />
  </div>
);

const OptimizationSettings: React.FC<OptimizationSettingsProps> = ({
  config,
  onConfigUpdate,
}) => {
  const handleSectionToggle = <K extends keyof OptimizationConfig>(
    section: K,
    key: keyof OptimizationConfig[K],
    value: boolean
  ) => {
    const sectionConfig = config[section];
    onConfigUpdate({
      [section]: { ...sectionConfig, [key]: value },
    } as Partial<OptimizationConfig>);
  };

  return (
    <div className="space-y-4">
      <SettingToggle
        label="Bundle Splitting"
        description="Enable runtime bundle analysis and dynamic code splitting hints."
        checked={config.bundleSplitting.enabled}
        onCheckedChange={(checked) =>
          handleSectionToggle("bundleSplitting", "enabled", checked)
        }
      />
      <SettingToggle
        label="Route-based Splitting"
        description="Prefetch and split bundles on likely navigation paths."
        checked={config.bundleSplitting.routeBasedSplitting}
        onCheckedChange={(checked) =>
          handleSectionToggle("bundleSplitting", "routeBasedSplitting", checked)
        }
      />
      <SettingToggle
        label="Image Optimization"
        description="Monitor image payloads and recommend lazy loading / WebP swaps."
        checked={config.imageOptimization.enabled}
        onCheckedChange={(checked) =>
          handleSectionToggle("imageOptimization", "enabled", checked)
        }
      />
      <SettingToggle
        label="Runtime Caching"
        description="Apply intelligent caching strategies and preload hints."
        checked={config.caching.enabled}
        onCheckedChange={(checked) =>
          handleSectionToggle("caching", "enabled", checked)
        }
      />
      <SettingToggle
        label="Memory Management"
        description="Enable leak detection and component cleanup heuristics."
        checked={config.memoryManagement.enabled}
        onCheckedChange={(checked) =>
          handleSectionToggle("memoryManagement", "enabled", checked)
        }
      />
    </div>
  );
};

export const PerformanceOptimizationDashboard: React.FC<PerformanceOptimizationDashboardProps> = ({
  autoApply = false,
  showAdvancedSettings = true,
}) => {
  const [config, setConfig] = useState<OptimizationConfig | null>(null);
  const [metrics, setMetrics] = useState<OptimizationMetrics | null>(null);
  const [recommendations, setRecommendations] = useState<OptimizationRecommendation[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  // Load data on mount
  useEffect(() => {
    const loadData = () => {
      setMetrics(performanceOptimizer.getMetrics());
      setRecommendations(performanceOptimizer.generateRecommendations());
      setConfig(performanceOptimizer.getConfig());
    };
    loadData();
    const interval = setInterval(loadData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Auto-apply optimizations if enabled
  useEffect(() => {
    if (autoApply && recommendations.length > 0) {
      const criticalRecommendations = recommendations.filter(
        (r) => r.priority === "critical" || r.priority === "high"
      );
      if (criticalRecommendations.length > 0) {
        handleApplyOptimizations();
      }
    }
  }, [recommendations, autoApply]);

  const handleApplyOptimizations = async () => {
    setIsOptimizing(true);
    try {
      await performanceOptimizer.applyOptimizations();
      // Refresh data after optimization
      setMetrics(performanceOptimizer.getMetrics());
      setRecommendations(performanceOptimizer.generateRecommendations());
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Failed to apply performance optimizations", error);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleConfigUpdate = (newConfig: Partial<OptimizationConfig>) => {
    performanceOptimizer.updateConfig(newConfig);
    setConfig(performanceOptimizer.getConfig());
  };

  const getPriorityColor = (
    priority: OptimizationRecommendation["priority"]
  ): BadgeVariant => {
    switch (priority) {
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

  const getPriorityIcon = (
    priority: OptimizationRecommendation["priority"]
  ) => {
    switch (priority) {
      case "critical":
        return <AlertTriangle className="h-4 w-4" />;
      case "high":
        return <AlertTriangle className="h-4 w-4" />;
      case "medium":
        return <Info className="h-4 w-4" />;
      case "low":
        return <Lightbulb className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getTypeIcon = (type: OptimizationRecommendation["type"]) => {
    switch (type) {
      case "bundle":
        return <Package className="h-4 w-4" />;
      case "image":
        return <Image className="h-4 w-4" />;
      case "cache":
        return <Database className="h-4 w-4" />;
      case "memory":
        return <MemoryStick className="h-4 w-4" />;
      default:
        return <Zap className="h-4 w-4" />;
    }
  };

  // Prepare chart data
  const optimizationImpactData = recommendations.map((rec) => ({
    name:
      rec.title.length > 20 ? `${rec.title.substring(0, 20)}…` : rec.title,
    impact: rec.estimatedGain,
    priority: rec.priority,
  }));

  const metricsOverviewData = metrics
    ? [
        { name: "Bundle Size", value: metrics.bundleSize.reduction, color: COLORS[0] },
        { name: "Images", value: metrics.imageOptimization.sizeReduction, color: COLORS[1] },
        { name: "Cache Hit Rate", value: metrics.cachePerformance.hitRate, color: COLORS[2] },
        {
          name: "Memory Availability",
          value:
            metrics.memoryUsage.heapTotal > 0
              ? Math.max(
                  0,
                  100 -
                    (metrics.memoryUsage.heapUsed / metrics.memoryUsage.heapTotal) * 100
                )
              : 0,
          color: COLORS[3],
        },
      ]
    : [];

  return (
    <ErrorBoundary fallback={PerformanceOptimizationFallback}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Performance Optimization</h2>
            <p className="text-muted-foreground"></p>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={handleApplyOptimizations}
              disabled={isOptimizing || recommendations.length === 0}
              className="flex items-center space-x-2"
              aria-label="Apply optimizations"
            >
              <Play className="h-4 w-4" />
              <span>{isOptimizing ? "Optimizing..." : "Apply Optimizations"}</span>
            </Button>
            {showAdvancedSettings && (
              <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline">
                    <Settings className="h-4 w-4 mr-2" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Optimization Settings</DialogTitle>
                    <DialogDescription>
                      Toggle runtime performance modules to match your production profile.
                    </DialogDescription>
                  </DialogHeader>
                  {config ? (
                    <OptimizationSettings
                      config={config}
                      onConfigUpdate={handleConfigUpdate}
                    />
                  ) : (
                    <div className="p-4 text-sm text-muted-foreground">
                      Loading configuration…
                    </div>
                  )}
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {/* Optimization Status */}
        {isOptimizing && (
          <Alert>
            <Zap className="h-4 w-4" />
            <AlertTitle>Optimization in Progress</AlertTitle>
            <AlertDescription>Applying performance optimizations. This may take a few moments.</AlertDescription>
          </Alert>
        )}

        {/* Metrics Overview */}
        {metrics && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Bundle Size</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics.bundleSize.reduction > 0 ? `-${metrics.bundleSize.reduction}%` : `${(metrics.bundleSize.after / 1024).toFixed(0)}KB`}
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{metrics.bundleSize.reduction > 0 ? "Size reduction" : "Current size"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Images Optimized</CardTitle>
                <Image className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.imageOptimization.imagesOptimized}</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{metrics.imageOptimization.webpConversions} WebP conversions</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Cache Hit Rate</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics.cachePerformance.hitRate > 0 ? `${((metrics.cachePerformance.hitRate / (metrics.cachePerformance.hitRate + metrics.cachePerformance.missRate)) * 100).toFixed(1)}%` : "0%"}
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{metrics.cachePerformance.hitRate + metrics.cachePerformance.missRate} total requests</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Memory Usage</CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics.memoryUsage.heapTotal > 0 ? `${((metrics.memoryUsage.heapUsed / metrics.memoryUsage.heapTotal) * 100).toFixed(1)}%` : "0%"}
                </div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{metrics.memoryUsage.leaksDetected} leaks detected</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Optimization Recommendations</CardTitle>
              </div>
              <Badge variant="secondary">{recommendations.length} recommendations</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium">All Optimized!</h3>
                <p className="text-muted-foreground">No performance optimizations needed at this time.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recommendations.slice(0, 5).map((recommendation) => (
                  <div key={recommendation.id} className="border rounded-lg p-4 sm:p-4 md:p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <div className="flex items-center space-x-2">
                          {getTypeIcon(recommendation.type)}
                          {getPriorityIcon(recommendation.priority)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-medium">{recommendation.title}</h4>
                            <Badge variant={getPriorityColor(recommendation.priority)}>
                              {recommendation.priority}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">{recommendation.description}</p>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            <p><strong>Impact:</strong> {recommendation.impact}</p>
                            <p><strong>Implementation:</strong> {recommendation.implementation}</p>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">+{recommendation.estimatedGain}%</div>
                        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Est. improvement</div>
                      </div>
                    </div>
                  </div>
                ))}
                {recommendations.length > 5 && (
                  <div className="text-center">
                    <Button variant="outline">View {recommendations.length - 5} more recommendations</Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Charts */}
        <Tabs defaultValue="impact" className="space-y-4">
          <TabsList>
            <TabsTrigger value="impact">Optimization Impact</TabsTrigger>
            <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
            <TabsTrigger value="trends">Optimization Trends</TabsTrigger>
          </TabsList>
          <TabsContent value="impact" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Potential Performance Gains</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={optimizationImpactData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="impact" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={metricsOverviewData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {metricsOverviewData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={[]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="performance" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ErrorBoundary>
  );
};

export default PerformanceOptimizationDashboard;
