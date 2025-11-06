"use client";

/**
 * Automation Scheduler
 *
 * Schedule and manage automated tasks, workflows, and recurring jobs
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Calendar,
  Clock,
  PlayCircle,
  PauseCircle,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
  Timer
} from 'lucide-react';

export interface ScheduledTask {
  id: string;
  name: string;
  type: 'agent' | 'workflow' | 'task';
  schedule: string;
  nextRun: string;
  lastRun?: string;
  status: 'active' | 'paused' | 'error';
  enabled: boolean;
  executionCount: number;
  successRate: number;
}

export interface ExecutionHistory {
  id: string;
  taskId: string;
  taskName: string;
  startTime: string;
  endTime: string;
  status: 'success' | 'failed' | 'running';
  duration: number;
  error?: string;
}

export interface AutomationSchedulerProps {
  refreshInterval?: number;
}

export default function AutomationScheduler({
  refreshInterval = 10000
}: AutomationSchedulerProps) {
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('scheduled');

  const loadSchedulerData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/automation/scheduler');
      if (response.ok) {
        const data = await response.json();
        setScheduledTasks(data.tasks);
        setExecutionHistory(data.history);
      } else {
        // Fallback mock data
        const mockTasks: ScheduledTask[] = [
          {
            id: 'task-1',
            name: 'Daily Build Agent',
            type: 'agent',
            schedule: '0 0 * * *',
            nextRun: new Date(Date.now() + 3600000).toISOString(),
            lastRun: new Date(Date.now() - 86400000).toISOString(),
            status: 'active',
            enabled: true,
            executionCount: 127,
            successRate: 98.4
          },
          {
            id: 'task-2',
            name: 'Hourly Health Check',
            type: 'task',
            schedule: '0 * * * *',
            nextRun: new Date(Date.now() + 600000).toISOString(),
            lastRun: new Date(Date.now() - 3000000).toISOString(),
            status: 'active',
            enabled: true,
            executionCount: 1543,
            successRate: 99.9
          },
          {
            id: 'task-3',
            name: 'Weekly Report Workflow',
            type: 'workflow',
            schedule: '0 9 * * 1',
            nextRun: new Date(Date.now() + 259200000).toISOString(),
            lastRun: new Date(Date.now() - 345600000).toISOString(),
            status: 'active',
            enabled: true,
            executionCount: 52,
            successRate: 96.2
          },
          {
            id: 'task-4',
            name: 'Code Review Agent',
            type: 'agent',
            schedule: '0 */4 * * *',
            nextRun: new Date(Date.now() + 7200000).toISOString(),
            status: 'paused',
            enabled: false,
            executionCount: 234,
            successRate: 94.4
          },
          {
            id: 'task-5',
            name: 'Backup Workflow',
            type: 'workflow',
            schedule: '0 2 * * *',
            nextRun: new Date(Date.now() + 21600000).toISOString(),
            lastRun: new Date(Date.now() - 64800000).toISOString(),
            status: 'error',
            enabled: true,
            executionCount: 89,
            successRate: 87.6
          }
        ];

        const mockHistory: ExecutionHistory[] = [
          {
            id: 'exec-1',
            taskId: 'task-2',
            taskName: 'Hourly Health Check',
            startTime: new Date(Date.now() - 3000000).toISOString(),
            endTime: new Date(Date.now() - 2995000).toISOString(),
            status: 'success',
            duration: 5000
          },
          {
            id: 'exec-2',
            taskId: 'task-1',
            taskName: 'Daily Build Agent',
            startTime: new Date(Date.now() - 86400000).toISOString(),
            endTime: new Date(Date.now() - 86100000).toISOString(),
            status: 'success',
            duration: 300000
          },
          {
            id: 'exec-3',
            taskId: 'task-5',
            taskName: 'Backup Workflow',
            startTime: new Date(Date.now() - 64800000).toISOString(),
            endTime: new Date(Date.now() - 64500000).toISOString(),
            status: 'failed',
            duration: 300000,
            error: 'Network timeout during backup operation'
          },
          {
            id: 'exec-4',
            taskId: 'task-3',
            taskName: 'Weekly Report Workflow',
            startTime: new Date(Date.now() - 345600000).toISOString(),
            endTime: new Date(Date.now() - 345000000).toISOString(),
            status: 'success',
            duration: 600000
          }
        ];

        setScheduledTasks(mockTasks);
        setExecutionHistory(mockHistory);
      }
    } catch (error) {
      console.error('Failed to load scheduler data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSchedulerData();
    const interval = setInterval(loadSchedulerData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const toggleTask = (taskId: string, enabled: boolean) => {
    setScheduledTasks(prev =>
      prev.map(task =>
        task.id === taskId
          ? { ...task, enabled, status: enabled ? 'active' : 'paused' }
          : task
      )
    );
  };

  const runTaskNow = (taskId: string) => {
    const task = scheduledTasks.find(t => t.id === taskId);
    if (task) {
      const newExecution: ExecutionHistory = {
        id: `exec-${Date.now()}`,
        taskId: task.id,
        taskName: task.name,
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + 5000).toISOString(),
        status: 'running',
        duration: 0
      };
      setExecutionHistory(prev => [newExecution, ...prev]);
    }
  };

  const formatSchedule = (cron: string): string => {
    // Simple cron to human-readable conversion
    const patterns: Record<string, string> = {
      '0 0 * * *': 'Daily at midnight',
      '0 * * * *': 'Every hour',
      '0 9 * * 1': 'Weekly on Monday at 9 AM',
      '0 */4 * * *': 'Every 4 hours',
      '0 2 * * *': 'Daily at 2 AM'
    };
    return patterns[cron] || cron;
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  };

  const getTimeUntilNext = (nextRun: string): string => {
    const diff = new Date(nextRun).getTime() - Date.now();
    if (diff < 0) return 'Overdue';
    if (diff < 60000) return 'Less than 1 minute';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours`;
    return `${Math.floor(diff / 86400000)} days`;
  };

  const activeTasks = scheduledTasks.filter(t => t.enabled);
  const pausedTasks = scheduledTasks.filter(t => !t.enabled);
  const recentExecutions = executionHistory.slice(0, 10);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Automation Scheduler
            </div>
            <Button onClick={loadSchedulerData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage scheduled tasks and workflows (Updates every {refreshInterval / 1000}s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Total Tasks</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{scheduledTasks.length}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Active</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{activeTasks.length}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Paused</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-600">{pausedTasks.length}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Avg Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {(scheduledTasks.reduce((acc, t) => acc + t.successRate, 0) / scheduledTasks.length || 0).toFixed(1)}%
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="scheduled">
                <Clock className="h-4 w-4 mr-2" />
                Scheduled Tasks
              </TabsTrigger>
              <TabsTrigger value="history">
                <Activity className="h-4 w-4 mr-2" />
                Execution History
              </TabsTrigger>
            </TabsList>

            {/* Scheduled Tasks Tab */}
            <TabsContent value="scheduled" className="space-y-4">
              <ScrollArea className="h-[600px]">
                <div className="space-y-3 pr-4">
                  {scheduledTasks.map((task) => (
                    <Card key={task.id}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-base">{task.name}</CardTitle>
                              <Badge variant="outline" className="capitalize">
                                {task.type}
                              </Badge>
                              {task.status === 'active' && (
                                <Badge variant="default" className="bg-green-600">Active</Badge>
                              )}
                              {task.status === 'paused' && (
                                <Badge variant="secondary">Paused</Badge>
                              )}
                              {task.status === 'error' && (
                                <Badge variant="destructive">Error</Badge>
                              )}
                            </div>
                            <CardDescription>{formatSchedule(task.schedule)}</CardDescription>
                          </div>
                          <Switch
                            checked={task.enabled}
                            onCheckedChange={(enabled) => toggleTask(task.id, enabled)}
                          />
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Next Run:</span>
                              <div className="flex items-center gap-1">
                                <Timer className="h-3 w-3" />
                                <span className="font-medium">{getTimeUntilNext(task.nextRun)}</span>
                              </div>
                            </div>
                            {task.lastRun && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Last Run:</span>
                                <span>{new Date(task.lastRun).toLocaleString()}</span>
                              </div>
                            )}
                          </div>

                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Executions:</span>
                              <span className="font-medium">{task.executionCount}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Success Rate:</span>
                              <span className="font-medium text-green-600">{task.successRate}%</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => runTaskNow(task.id)}
                            disabled={!task.enabled}
                          >
                            <PlayCircle className="h-4 w-4 mr-2" />
                            Run Now
                          </Button>
                          <Button size="sm" variant="outline">
                            Edit Schedule
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Execution History Tab */}
            <TabsContent value="history" className="space-y-4">
              <ScrollArea className="h-[600px]">
                <div className="space-y-3 pr-4">
                  {recentExecutions.map((execution) => (
                    <Card key={execution.id}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">{execution.taskName}</CardTitle>
                            <CardDescription>
                              {new Date(execution.startTime).toLocaleString()}
                            </CardDescription>
                          </div>
                          {execution.status === 'success' && (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                          {execution.status === 'failed' && (
                            <XCircle className="h-5 w-5 text-red-600" />
                          )}
                          {execution.status === 'running' && (
                            <Activity className="h-5 w-5 text-blue-600 animate-pulse" />
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid md:grid-cols-3 gap-4">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Status:</span>
                            <Badge
                              variant={
                                execution.status === 'success'
                                  ? 'default'
                                  : execution.status === 'failed'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                              className={execution.status === 'success' ? 'bg-green-600' : ''}
                            >
                              {execution.status}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Duration:</span>
                            <span className="font-medium">{formatDuration(execution.duration)}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Task ID:</span>
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {execution.taskId}
                            </code>
                          </div>
                        </div>
                        {execution.error && (
                          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
                              <div className="flex-1">
                                <p className="text-sm font-medium text-destructive">Error</p>
                                <p className="text-sm text-muted-foreground mt-1">{execution.error}</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { AutomationScheduler };
export type { AutomationSchedulerProps, ScheduledTask, ExecutionHistory };
