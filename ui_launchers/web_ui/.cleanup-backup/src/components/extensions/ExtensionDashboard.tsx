/**
 * Extension Dashboard Component
 * 
 * Real-time dashboard showing extension status, health, and background tasks
 */

'use client';

import React, { useState, useMemo } from 'react';
import { 
  ExtensionStatusDashboard, 
  ExtensionWidgetsDashboard,
  ExtensionTaskHistory 
} from '../../lib/extensions/components';
import { 
  useExtensionStatuses, 
  useExtensionHealth, 
  useExtensionPerformance,
  useExtensionTaskMonitoring 
} from '../../lib/extensions/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { RefreshCw, Activity, Zap, AlertTriangle, CheckCircle } from 'lucide-react';

interface ExtensionDashboardProps {
  className?: string;
}

export default function ExtensionDashboard({ className }: ExtensionDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedExtension, setSelectedExtension] = useState<string | null>(null);
  
  const { statuses, loading, error } = useExtensionStatuses();
  const healthData = useExtensionHealth();
  const performanceData = useExtensionPerformance();
  const taskData = useExtensionTaskMonitoring();

  const dashboardStats = useMemo(() => {
    const activeExtensions = statuses.filter(s => s.status === 'active').length;
    const errorExtensions = statuses.filter(s => s.status === 'error').length;
    const totalMemoryUsage = statuses.reduce((sum, s) => sum + s.resources.memory, 0);
    const avgCpuUsage = statuses.length > 0 
      ? statuses.reduce((sum, s) => sum + s.resources.cpu, 0) / statuses.length 
      : 0;

    return {
      total: statuses.length,
      active: activeExtensions,
      errors: errorExtensions,
      totalMemory: totalMemoryUsage,
      avgCpu: avgCpuUsage,
      healthScore: healthData.healthPercentage
    };
  }, [statuses, healthData]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading extension dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
          <div>
            <h3 className="text-lg font-semibold text-red-800">Dashboard Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Extension Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and manage your extensions in real-time</p>
        </div>
        <Button
          variant="outline"
          onClick={() => window.location.reload()}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Extensions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.total}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardStats.active} active, {dashboardStats.errors} errors
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Health Score</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.healthScore}%</div>
            <div className="flex items-center mt-1">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    dashboardStats.healthScore >= 80 ? 'bg-green-500' :
                    dashboardStats.healthScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${dashboardStats.healthScore}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.avgCpu.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Average across all extensions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskData.totalActiveTasks}</div>
            <p className="text-xs text-muted-foreground">
              {taskData.totalTasks} total background tasks
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="extensions">Extensions</TabsTrigger>
          <TabsTrigger value="tasks">Background Tasks</TabsTrigger>
          <TabsTrigger value="widgets">Widgets</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <ExtensionStatusDashboard />
        </TabsContent>

        <TabsContent value="extensions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Extension Status</CardTitle>
              <CardDescription>
                Detailed view of all extensions and their current status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ExtensionStatusDashboard />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Extensions with Tasks</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {taskData.statuses.map((status) => (
                    <div
                      key={status.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedExtension === status.id 
                          ? 'bg-blue-50 border-blue-200' 
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedExtension(status.id)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{status.name}</span>
                        <Badge variant={status.status === 'active' ? 'default' : 'secondary'}>
                          {status.backgroundTasks?.active || 0}/{status.backgroundTasks?.total || 0}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Task Execution History</CardTitle>
                <CardDescription>
                  {selectedExtension 
                    ? `History for ${statuses.find(s => s.id === selectedExtension)?.name || selectedExtension}`
                    : 'Select an extension to view task history'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedExtension ? (
                  <ExtensionTaskHistory extensionId={selectedExtension} />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Select an extension from the list to view its task execution history
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="widgets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Extension Widgets</CardTitle>
              <CardDescription>
                Dashboard widgets provided by extensions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ExtensionWidgetsDashboard />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Compact extension dashboard for embedding in other pages
 */
export function CompactExtensionDashboard({ className }: { className?: string }) {
  const healthData = useExtensionHealth();
  const taskData = useExtensionTaskMonitoring();

  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${className}`}>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Extensions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{healthData.total}</div>
          <p className="text-xs text-muted-foreground">
            {healthData.healthy} healthy
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{healthData.healthPercentage}%</div>
          <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
            <div 
              className={`h-1 rounded-full ${
                healthData.healthPercentage >= 80 ? 'bg-green-500' :
                healthData.healthPercentage >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${healthData.healthPercentage}%` }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Active Tasks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{taskData.totalActiveTasks}</div>
          <p className="text-xs text-muted-foreground">
            {taskData.totalTasks} total
          </p>
        </CardContent>
      </Card>
    </div>
  );
}