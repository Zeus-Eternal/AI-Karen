/**
 * Performance Optimization Component
 * Main component that integrates all performance optimization features
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  PerformanceOptimizationState, 
  PerformanceReport,
} from './types';
import { usePerformanceOptimizationStore } from './store/performanceOptimizationStore';

interface PerformanceOptimizationProps {
  children?: React.ReactNode;
  config?: Partial<PerformanceOptimizationState['settings']>;
  showDashboard?: boolean;
  autoOptimize?: boolean;
}

export const PerformanceOptimization: React.FC<PerformanceOptimizationProps> = ({
  children,
  config,
  showDashboard = false,
  autoOptimize = true,
}) => {
  const {
    settings,
    metrics,
    alerts,
    deviceProfile,
    updateSettings,
    startMonitoring,
    generateReport,
  } = usePerformanceOptimizationStore();

  const [isInitialized, setIsInitialized] = useState(false);
  const [latestReport, setLatestReport] = useState<PerformanceReport | null>(null);
  void autoOptimize;

  // Initialize performance optimization
  useEffect(() => {
    const initializePerformanceOptimization = async () => {
      try {
        // Apply custom configuration
        if (config) {
          updateSettings(config);
        }

        // Start monitoring if enabled
        if (settings.enableMonitoring) {
          startMonitoring();
        }

        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize performance optimization:', error);
      }
    };

    initializePerformanceOptimization();
  }, [config, settings, updateSettings, startMonitoring]);

  // Generate performance report
  const generatePerformanceReport = useCallback(() => {
    const report = generateReport();
    setLatestReport(report);
    return report;
  }, [generateReport]);

  // Calculate overall performance score
  const performanceScore = useMemo(() => {
    if (!latestReport) return 0;
    return latestReport.score;
  }, [latestReport]);

  // Get performance status
  const performanceStatus = useMemo(() => {
    if (performanceScore >= 90) return { status: 'excellent', color: 'bg-green-500' };
    if (performanceScore >= 75) return { status: 'good', color: 'bg-blue-500' };
    if (performanceScore >= 60) return { status: 'fair', color: 'bg-yellow-500' };
    return { status: 'poor', color: 'bg-red-500' };
  }, [performanceScore]);

  // Render dashboard
  if (showDashboard) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Performance Optimization Dashboard</CardTitle>
            <CardDescription>
              Monitor and optimize application performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Performance Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{performanceScore}</div>
                    <Badge className={`${performanceStatus.color} text-white`}>
                      {performanceStatus.status}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Monitoring Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={settings.enableMonitoring ? 'default' : 'secondary'}>
                      {settings.enableMonitoring ? 'Active' : 'Inactive'}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Device Optimization</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={settings.enableDeviceOptimization ? 'default' : 'secondary'}>
                      {settings.enableDeviceOptimization ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{alerts.length}</div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Performance Score Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Progress value={performanceScore} className="w-full" />
                    <div className="flex justify-between text-sm text-muted-foreground mt-2">
                      <span>0</span>
                      <span>{performanceScore}</span>
                      <span>100</span>
                    </div>
                  </CardContent>
                </Card>

                {deviceProfile && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Device Profile</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Type:</span> {deviceProfile.type}
                        </div>
                        <div>
                          <span className="font-medium">OS:</span> {deviceProfile.os}
                        </div>
                        <div>
                          <span className="font-medium">Browser:</span> {deviceProfile.browser}
                        </div>
                        <div>
                          <span className="font-medium">Connection:</span> {deviceProfile.connectionType}
                        </div>
                        <div>
                          <span className="font-medium">Memory:</span> {deviceProfile.memory}GB
                        </div>
                        <div>
                          <span className="font-medium">CPU Cores:</span> {deviceProfile.cpuCores}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle>Performance Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {metrics.slice(0, 5).map((metric, index) => (
                        <div key={index} className="flex justify-between items-center">
                          <div>
                            <div className="font-medium">{metric.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {metric.value} {metric.unit}
                            </div>
                          </div>
                          <Badge variant={
                            metric.rating === 'good' ? 'default' :
                            metric.rating === 'needs-improvement' ? 'secondary' : 'destructive'
                          }>
                            {metric.rating}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Performance Alerts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {alerts.length === 0 ? (
                        <div className="text-center text-muted-foreground py-4">
                          No performance alerts at this time.
                        </div>
                      ) : (
                        alerts.slice(0, 3).map((alert, index) => (
                          <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                            <div>
                              <div className="font-medium">{alert.message}</div>
                              <div className="text-sm text-muted-foreground">
                                {alert.timestamp.toLocaleString()}
                              </div>
                            </div>
                            <Badge variant={
                              alert.severity === 'critical' ? 'destructive' :
                              alert.severity === 'high' ? 'destructive' :
                              alert.severity === 'medium' ? 'secondary' : 'default'
                            }>
                              {alert.severity}
                            </Badge>
                          </div>
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Performance Settings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableLazyLoading}
                              onChange={(e) => updateSettings({ enableLazyLoading: e.target.checked })}
                            />
                            <span>Enable Lazy Loading</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableMonitoring}
                              onChange={(e) => updateSettings({ enableMonitoring: e.target.checked })}
                            />
                            <span>Enable Monitoring</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableCaching}
                              onChange={(e) => updateSettings({ enableCaching: e.target.checked })}
                            />
                            <span>Enable Caching</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableDeviceOptimization}
                              onChange={(e) => updateSettings({ enableDeviceOptimization: e.target.checked })}
                            />
                            <span>Enable Device Optimization</span>
                          </label>
                        </div>

                        <div className="space-y-2">
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enablePreloading}
                              onChange={(e) => updateSettings({ enablePreloading: e.target.checked })}
                            />
                            <span>Enable Preloading</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enablePrefetching}
                              onChange={(e) => updateSettings({ enablePrefetching: e.target.checked })}
                            />
                            <span>Enable Prefetching</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableProfiling}
                              onChange={(e) => updateSettings({ enableProfiling: e.target.checked })}
                            />
                            <span>Enable Profiling</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={settings.enableBudgetAlerts}
                              onChange={(e) => updateSettings({ enableBudgetAlerts: e.target.checked })}
                            />
                            <span>Enable Budget Alerts</span>
                          </label>
                        </div>
                      </div>

                      <div className="flex justify-end">
                        <Button onClick={generatePerformanceReport}>
                          Generate Performance Report
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render children with performance optimization
  return (
    <div className="performance-optimization">
      {isInitialized ? children : (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <div className="text-muted-foreground">Initializing Performance Optimization...</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceOptimization;
