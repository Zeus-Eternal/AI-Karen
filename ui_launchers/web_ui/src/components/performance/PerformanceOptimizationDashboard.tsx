/**
 * Performance Optimization Dashboard
 * Interface for managing automatic performance optimizations
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { 
  Zap, 
  Image, 
  Package, 
  Database, 
  MemoryStick, 
  TrendingUp, 
  Settings, 
  Play, 
  CheckCircle, 
  AlertTriangle,
  Info,
  Lightbulb
} from 'lucide-react';
import { 
  performanceOptimizer, 
  OptimizationConfig, 
  OptimizationMetrics, 
  OptimizationRecommendation 
} from '@/services/performance-optimizer';

interface PerformanceOptimizationDashboardProps {
  autoApply?: boolean;
  showAdvancedSettings?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

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
    };

    loadData();
    const interval = setInterval(loadData, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Auto-apply optimizations if enabled
  useEffect(() => {
    if (autoApply && recommendations.length > 0) {
      const criticalRecommendations = recommendations.filter(
        r => r.priority === 'critical' || r.priority === 'high'
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
      console.error('Failed to apply optimizations:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleConfigUpdate = (newConfig: Partial<OptimizationConfig>) => {
    performanceOptimizer.updateConfig(newConfig);
    setConfig(performanceOptimizer['config']); // Access private config for display
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <AlertTriangle className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      case 'medium': return <Info className="h-4 w-4" />;
      case 'low': return <Lightbulb className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'bundle': return <Package className="h-4 w-4" />;
      case 'image': return <Image className="h-4 w-4" />;
      case 'cache': return <Database className="h-4 w-4" />;
      case 'memory': return <MemoryStick className="h-4 w-4" />;
      default: return <Zap className="h-4 w-4" />;
    }
  };

  // Prepare chart data
  const optimizationImpactData = recommendations.map(rec => ({
    name: rec.title.substring(0, 20) + '...',
    impact: rec.estimatedGain,
    priority: rec.priority,
  }));

  const metricsOverviewData = metrics ? [
    { name: 'Bundle Size', value: metrics.bundleSize.reduction, color: COLORS[0] },
    { name: 'Images', value: metrics.imageOptimization.sizeReduction, color: COLORS[1] },
    { name: 'Cache Hit Rate', value: metrics.cachePerformance.hitRate, color: COLORS[2] },
    { name: 'Memory Usage', value: 100 - (metrics.memoryUsage.heapUsed / metrics.memoryUsage.heapTotal * 100), color: COLORS[3] },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Performance Optimization</h2>
          <p className="text-muted-foreground">
            Automatic performance optimizations and recommendations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={handleApplyOptimizations}
            disabled={isOptimizing || recommendations.length === 0}
            className="flex items-center space-x-2"
          >
            <Play className="h-4 w-4" />
            <span>{isOptimizing ? 'Optimizing...' : 'Apply Optimizations'}</span>
          </Button>
          {showAdvancedSettings && (
            <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Optimization Settings</DialogTitle>
                  <DialogDescription>
                    Configure automatic performance optimization settings
                  </DialogDescription>
                </DialogHeader>
                <OptimizationSettings onConfigUpdate={handleConfigUpdate} />
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
          <AlertDescription>
            Applying performance optimizations. This may take a few moments.
          </AlertDescription>
        </Alert>
      )}

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bundle Size</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.bundleSize.reduction > 0 
                  ? `-${metrics.bundleSize.reduction}%` 
                  : `${(metrics.bundleSize.after / 1024).toFixed(0)}KB`
                }
              </div>
              <p className="text-xs text-muted-foreground">
                {metrics.bundleSize.reduction > 0 ? 'Size reduction' : 'Current size'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Images Optimized</CardTitle>
              <Image className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.imageOptimization.imagesOptimized}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.imageOptimization.webpConversions} WebP conversions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.cachePerformance.hitRate > 0 
                  ? `${((metrics.cachePerformance.hitRate / (metrics.cachePerformance.hitRate + metrics.cachePerformance.missRate)) * 100).toFixed(1)}%`
                  : '0%'
                }
              </div>
              <p className="text-xs text-muted-foreground">
                {metrics.cachePerformance.hitRate + metrics.cachePerformance.missRate} total requests
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              <MemoryStick className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.memoryUsage.heapTotal > 0 
                  ? `${((metrics.memoryUsage.heapUsed / metrics.memoryUsage.heapTotal) * 100).toFixed(1)}%`
                  : '0%'
                }
              </div>
              <p className="text-xs text-muted-foreground">
                {metrics.memoryUsage.leaksDetected} leaks detected
              </p>
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
              <CardDescription>
                Automated suggestions to improve performance
              </CardDescription>
            </div>
            <Badge variant="secondary">
              {recommendations.length} recommendations
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {recommendations.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium">All Optimized!</h3>
              <p className="text-muted-foreground">
                No performance optimizations needed at this time.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.slice(0, 5).map((recommendation) => (
                <div key={recommendation.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="flex items-center space-x-2">
                        {getTypeIcon(recommendation.type)}
                        {getPriorityIcon(recommendation.priority)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="font-medium">{recommendation.title}</h4>
                          <Badge variant={getPriorityColor(recommendation.priority) as any}>
                            {recommendation.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {recommendation.description}
                        </p>
                        <div className="text-xs text-muted-foreground">
                          <p><strong>Impact:</strong> {recommendation.impact}</p>
                          <p><strong>Implementation:</strong> {recommendation.implementation}</p>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-600">
                        +{recommendation.estimatedGain}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Est. improvement
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {recommendations.length > 5 && (
                <div className="text-center">
                  <Button variant="outline">
                    View {recommendations.length - 5} more recommendations
                  </Button>
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
              <CardDescription>
                Estimated performance improvements from recommendations
              </CardDescription>
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
              <CardDescription>
                Performance improvements over time
              </CardDescription>
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
  );
};

/**
 * Optimization Settings Component
 */
interface OptimizationSettingsProps {
  onConfigUpdate: (config: Partial<OptimizationConfig>) => void;
}

const OptimizationSettings: React.FC<OptimizationSettingsProps> = ({ onConfigUpdate }) => {
  const [config, setConfig] = useState<OptimizationConfig>({
    bundleSplitting: {
      enabled: true,
      chunkSizeLimit: 244 * 1024,
      routeBasedSplitting: true,
      componentBasedSplitting: true,
    },
    imageOptimization: {
      enabled: true,
      webpConversion: true,
      responsiveSizing: true,
      lazyLoading: true,
      qualityThreshold: 85,
    },
    caching: {
      enabled: true,
      serviceWorker: true,
      browserCache: true,
      preloadStrategies: ['critical-resources', 'next-page'],
      cacheInvalidation: 'smart',
    },
    memoryManagement: {
      enabled: true,
      gcMonitoring: true,
      leakDetection: true,
      componentCleanup: true,
      eventListenerCleanup: true,
    },
  });

  const handleConfigChange = (section: keyof OptimizationConfig, key: string, value: any) => {
    const newConfig = {
      ...config,
      [section]: {
        ...config[section],
        [key]: value,
      },
    };
    setConfig(newConfig);
    onConfigUpdate(newConfig);
  };

  return (
    <div className="space-y-6">
      {/* Bundle Splitting */}
      <div>
        <h3 className="text-lg font-medium mb-4">Bundle Splitting</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Bundle Splitting</label>
            <Switch
              checked={config.bundleSplitting.enabled}
              onCheckedChange={(checked) => handleConfigChange('bundleSplitting', 'enabled', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Route-based Splitting</label>
            <Switch
              checked={config.bundleSplitting.routeBasedSplitting}
              onCheckedChange={(checked) => handleConfigChange('bundleSplitting', 'routeBasedSplitting', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Component-based Splitting</label>
            <Switch
              checked={config.bundleSplitting.componentBasedSplitting}
              onCheckedChange={(checked) => handleConfigChange('bundleSplitting', 'componentBasedSplitting', checked)}
            />
          </div>
        </div>
      </div>

      {/* Image Optimization */}
      <div>
        <h3 className="text-lg font-medium mb-4">Image Optimization</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Image Optimization</label>
            <Switch
              checked={config.imageOptimization.enabled}
              onCheckedChange={(checked) => handleConfigChange('imageOptimization', 'enabled', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">WebP Conversion</label>
            <Switch
              checked={config.imageOptimization.webpConversion}
              onCheckedChange={(checked) => handleConfigChange('imageOptimization', 'webpConversion', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Lazy Loading</label>
            <Switch
              checked={config.imageOptimization.lazyLoading}
              onCheckedChange={(checked) => handleConfigChange('imageOptimization', 'lazyLoading', checked)}
            />
          </div>
        </div>
      </div>

      {/* Caching */}
      <div>
        <h3 className="text-lg font-medium mb-4">Caching</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Caching</label>
            <Switch
              checked={config.caching.enabled}
              onCheckedChange={(checked) => handleConfigChange('caching', 'enabled', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Service Worker</label>
            <Switch
              checked={config.caching.serviceWorker}
              onCheckedChange={(checked) => handleConfigChange('caching', 'serviceWorker', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Browser Cache</label>
            <Switch
              checked={config.caching.browserCache}
              onCheckedChange={(checked) => handleConfigChange('caching', 'browserCache', checked)}
            />
          </div>
        </div>
      </div>

      {/* Memory Management */}
      <div>
        <h3 className="text-lg font-medium mb-4">Memory Management</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Memory Management</label>
            <Switch
              checked={config.memoryManagement.enabled}
              onCheckedChange={(checked) => handleConfigChange('memoryManagement', 'enabled', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">GC Monitoring</label>
            <Switch
              checked={config.memoryManagement.gcMonitoring}
              onCheckedChange={(checked) => handleConfigChange('memoryManagement', 'gcMonitoring', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Leak Detection</label>
            <Switch
              checked={config.memoryManagement.leakDetection}
              onCheckedChange={(checked) => handleConfigChange('memoryManagement', 'leakDetection', checked)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};