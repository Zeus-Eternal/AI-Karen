/**
 * Background Task Monitor Component
 * 
 * Real-time monitoring of extension background tasks
 */

"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { useExtensionTaskMonitoring, useExtensionTasks } from '@/lib/extensions/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

import { 
  RefreshCw, 
  Activity, 
  CheckCircle, 
  Timer, 
  Calendar, 
  Clock, 
  XCircle, 
  AlertCircle 
} from 'lucide-react';

interface BackgroundTaskMonitorProps {
  extensionId?: string;
  className?: string;
}

export function BackgroundTaskMonitor({ extensionId, className }: BackgroundTaskMonitorProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedExtension, setSelectedExtension] = useState<string | null>(extensionId || null);
  
  const taskData = useExtensionTaskMonitoring(extensionId);
  const { executeTask, history, loading } = useExtensionTasks(selectedExtension || '');

  const taskStats = useMemo(() => {
    const recentExecutions = history.slice(0, 10);
    const completedTasks = recentExecutions.filter(h => h.status === 'completed').length;
    const failedTasks = recentExecutions.filter(h => h.status === 'failed').length;
    const runningTasks = recentExecutions.filter(h => h.status === 'running').length;
    
    const avgDuration = recentExecutions
      .filter(h => h.duration_seconds)
      .reduce((sum, h) => sum + (h.duration_seconds || 0), 0) / 
      (recentExecutions.filter(h => h.duration_seconds).length || 1);

    return {
      total: recentExecutions.length,
      completed: completedTasks,
      failed: failedTasks,
      running: runningTasks,
      avgDuration: avgDuration.toFixed(2)
    };
  }, [history]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Background Task Monitor</h2>
          <p className="text-gray-600 mt-1">
            {extensionId 
              ? `Monitoring tasks for ${extensionId}`
              : 'Monitor background tasks across all extensions'
            }
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => window.location.reload()}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4 " />
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Active Tasks</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskData.totalActiveTasks}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {taskData.totalTasks} total tasks
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {taskStats.total > 0 
                ? Math.round((taskStats.completed / taskStats.total) * 100)
                : 0
              }%
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {taskStats.completed}/{taskStats.total} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Avg Duration</CardTitle>
            <Timer className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskStats.avgDuration}s</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Average execution time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Extensions</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{taskData.extensionsWithTasks}</div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              With active tasks
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="extensions">By Extension</TabsTrigger>
          <TabsTrigger value="history">Execution History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <TaskOverview taskData={taskData} />
        </TabsContent>

        <TabsContent value="extensions" className="space-y-4">
          <ExtensionTaskList 
            extensions={taskData.statuses}
            selectedExtension={selectedExtension}
            onSelectExtension={setSelectedExtension}
          />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <TaskExecutionHistory 
            history={history}
            loading={loading}
            extensionId={selectedExtension}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function TaskOverview({ taskData }: { taskData: any }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Task Distribution</CardTitle>
          <CardDescription>Tasks across all extensions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {taskData.statuses.map((status: any) => (
              <div key={status.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    status.status === 'active' ? 'bg-green-400' :
                    status.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                  }`} />
                  <span className="font-medium">{status.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {status.backgroundTasks?.active || 0} active
                  </Badge>
                  <Badge variant="secondary">
                    {status.backgroundTasks?.total || 0} total
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Task Utilization</CardTitle>
          <CardDescription>Overall system task usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2 md:text-base lg:text-lg">
                <span>Active Tasks</span>
                <span>{taskData.taskUtilization}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${taskData.taskUtilization}%` }}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{taskData.totalActiveTasks}</div>
                <div className="text-sm text-gray-500 md:text-base lg:text-lg">Active</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">{taskData.totalTasks}</div>
                <div className="text-sm text-gray-500 md:text-base lg:text-lg">Total</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ExtensionTaskList({ 
  extensions, 
  selectedExtension, 
  onSelectExtension 
}: { 
  extensions: any[];
  selectedExtension: string | null;
  onSelectExtension: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {extensions.map((extension) => (
        <Card 
          key={extension.id}
          className={`cursor-pointer transition-colors ${
            selectedExtension === extension.id 
              ? 'ring-2 ring-blue-500 bg-blue-50' 
              : 'hover:bg-gray-50'
          }`}
          onClick={() => onSelectExtension(extension.id)}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{extension.name}</CardTitle>
              <div className={`w-3 h-3 rounded-full ${
                extension.status === 'active' ? 'bg-green-400' :
                extension.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
              }`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 md:text-base lg:text-lg">Active Tasks</span>
                <Badge variant="default">
                  {extension.backgroundTasks?.active || 0}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 md:text-base lg:text-lg">Total Tasks</span>
                <Badge variant="secondary">
                  {extension.backgroundTasks?.total || 0}
                </Badge>
              </div>
              
              {extension.backgroundTasks?.lastExecution && (
                <div className="text-xs text-gray-500 sm:text-sm md:text-base">
                  Last run: {new Date(extension.backgroundTasks.lastExecution).toLocaleString()}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TaskExecutionHistory({ 
  history, 
  loading, 
  extensionId 
}: { 
  history: any[];
  loading: boolean;
  extensionId: string | null;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-600 mr-2 " />
        <span>Loading task history...</span>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Clock className="h-12 w-12 text-gray-300 mx-auto mb-4 " />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Task History</h3>
          <p className="text-gray-600">
            {extensionId 
              ? `No background tasks have been executed for ${extensionId} yet.`
              : 'No background tasks have been executed yet.'
            }
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {history.map((execution, index) => (
        <Card key={execution.execution_id || index}>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">{execution.task_name}</h3>
                <p className="text-sm text-gray-500 md:text-base lg:text-lg">ID: {execution.execution_id}</p>
              </div>
              
              <Badge 
                variant={
                  execution.status === 'completed' ? 'default' :
                  execution.status === 'failed' ? 'destructive' :
                  execution.status === 'running' ? 'secondary' : 'outline'
                }
                className="flex items-center gap-1"
              >
                {execution.status === 'completed' && <CheckCircle className="h-3 w-3 " />}
                {execution.status === 'failed' && <XCircle className="h-3 w-3 " />}
                {execution.status === 'running' && <RefreshCw className="h-3 w-3 animate-spin " />}
                {execution.status}
              </Badge>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {execution.started_at && (
                <div>
                  <span className="text-gray-500">Started:</span>
                  <div className="font-medium">
                    {new Date(execution.started_at).toLocaleString()}
                  </div>
                </div>
              )}
              
              {execution.completed_at && (
                <div>
                  <span className="text-gray-500">Completed:</span>
                  <div className="font-medium">
                    {new Date(execution.completed_at).toLocaleString()}
                  </div>
                </div>
              )}
              
              {execution.duration_seconds && (
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <div className="font-medium">{execution.duration_seconds.toFixed(2)}s</div>
                </div>
              )}
              
              <div>
                <span className="text-gray-500">Status:</span>
                <div className="font-medium capitalize">{execution.status}</div>
              </div>
            </div>
            
            {execution.error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
                <div className="flex items-center gap-2 text-red-800 font-medium mb-1">
                  <AlertCircle className="h-4 w-4 " />
                </div>
                <p className="text-red-700 text-sm md:text-base lg:text-lg">{execution.error}</p>
              </div>
            )}
            
            {execution.result && (
              <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md sm:p-4 md:p-6">
                <div className="text-gray-700 font-medium mb-2">Result:</div>
                <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto sm:text-sm md:text-base">
                  {JSON.stringify(execution.result, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default BackgroundTaskMonitor;