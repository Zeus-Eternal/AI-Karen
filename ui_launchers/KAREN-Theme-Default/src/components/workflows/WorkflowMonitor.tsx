"use client";
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { } from 'lucide-react';

import { } from '@/types/workflows';

export interface WorkflowMonitorProps {
  executions: WorkflowExecution[];
  workflows: WorkflowDefinition[];
  onPauseExecution?: (executionId: string) => Promise<void>;
  onResumeExecution?: (executionId: string) => Promise<void>;
  onCancelExecution?: (executionId: string) => Promise<void>;
  onRetryExecution?: (executionId: string) => Promise<void>;
  onExportLogs?: (executionId: string) => void;
  className?: string;
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-700 border-gray-200',
  running: 'bg-blue-100 text-blue-700 border-blue-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  failed: 'bg-red-100 text-red-700 border-red-200',
  cancelled: 'bg-orange-100 text-orange-700 border-orange-200',
};

const logLevelColors = {
  debug: 'text-gray-600 bg-gray-50 border-gray-200',
  info: 'text-blue-600 bg-blue-50 border-blue-200',
  warn: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  error: 'text-red-600 bg-red-50 border-red-200',
};

export function WorkflowMonitor({
  executions,
  workflows,
  onPauseExecution,
  onResumeExecution,
  onCancelExecution,
  onRetryExecution,
  onExportLogs,
  className = '',
}: WorkflowMonitorProps) {
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [logLevelFilter, setLogLevelFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});

  const filteredExecutions = useMemo(() => {
    return executions.filter(execution => {
      const workflow = workflows.find(w => w.id === execution.workflowId);
      const workflowName = workflow?.name || 'Unknown';
      const matchesSearch = workflowName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           execution.id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || execution.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [executions, workflows, searchTerm, statusFilter]);

  const executionStats = useMemo(() => {
    const stats = {
      total: executions.length,
      running: 0,
      completed: 0,
      failed: 0,
      pending: 0,
      cancelled: 0,
      averageDuration: 0,
      successRate: 0,
    };
    let totalDuration = 0;
    let completedCount = 0;
    executions.forEach(execution => {
      stats[execution.status]++;
      if (execution.duration) {
        totalDuration += execution.duration;
        completedCount++;
      }
    });
    stats.averageDuration = completedCount > 0 ? totalDuration / completedCount : 0;
    stats.successRate = stats.total > 0 ? (stats.completed / stats.total) * 100 : 0;
    return stats;
  }, [executions]);

  const handleExecutionAction = useCallback(async (
    action: 'pause' | 'resume' | 'cancel' | 'retry',
    executionId: string
  ) => {
    setIsLoading(prev => ({ ...prev, [executionId]: true }));
    try {
      switch (action) {
        case 'pause':
          await onPauseExecution?.(executionId);
          break;
        case 'resume':
          await onResumeExecution?.(executionId);
          break;
        case 'cancel':
          await onCancelExecution?.(executionId);
          break;
        case 'retry':
          await onRetryExecution?.(executionId);
          break;
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(prev => ({ ...prev, [executionId]: false }));
    }
  }, [onPauseExecution, onResumeExecution, onCancelExecution, onRetryExecution]);

  const formatDuration = (duration: number) => {
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}m`;
  };

  const getExecutionIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="h-4 w-4 animate-pulse " />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 " />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 " />;
      case 'pending':
        return <Clock className="h-4 w-4 " />;
      case 'cancelled':
        return <Square className="h-4 w-4 " />;
      default:
        return <Clock className="h-4 w-4 " />;
    }
  };

  const filteredLogs = useMemo(() => {
    if (!selectedExecution) return [];
    return selectedExecution.logs.filter(log => 
      logLevelFilter === 'all' || log.level === logLevelFilter
    );
  }, [selectedExecution, logLevelFilter]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Monitor Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Workflow Monitor</h2>
          <p className="text-muted-foreground">Track workflow executions and performance</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground " />
            <input
              type="text"
              placeholder="Search executions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border border-input rounded-md text-sm w-64 "
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-input rounded-md text-sm md:text-base lg:text-lg"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Total Executions</p>
                <p className="text-2xl font-bold">{executionStats.total}</p>
              </div>
              <Activity className="h-8 w-8 text-muted-foreground " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {executionStats.successRate.toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600 " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Running</p>
                <p className="text-2xl font-bold text-blue-600">{executionStats.running}</p>
              </div>
              <Play className="h-8 w-8 text-blue-600 " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {formatDuration(executionStats.averageDuration)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground " />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Execution List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Executions ({filteredExecutions.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {filteredExecutions.map((execution) => {
                    const workflow = workflows.find(w => w.id === execution.workflowId);
                    return (
                      <Card
                        key={execution.id}
                        className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                          selectedExecution?.id === execution.id ? 'ring-2 ring-blue-500' : ''
                        }`}
                        onClick={() => setSelectedExecution(execution)}
                      >
                        <CardContent className="p-4 sm:p-4 md:p-6">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                {getExecutionIcon(execution.status)}
                                <h3 className="font-semibold">
                                  {workflow?.name || 'Unknown Workflow'}
                                </h3>
                                <Badge className={statusColors[execution.status]}>
                                  {execution.status}
                                </Badge>
                              </div>
                              <div className="grid grid-cols-2 gap-4 text-sm mb-3 md:text-base lg:text-lg">
                                <div>
                                  <span className="text-muted-foreground">Started:</span>
                                  <span className="ml-2 font-medium">
                                    {execution.startTime.toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Duration:</span>
                                  <span className="ml-2 font-medium">
                                    {execution.duration ? formatDuration(execution.duration) : 'Running...'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Progress:</span>
                                  <span className="ml-2 font-medium">{execution.progress}%</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Triggered by:</span>
                                  <span className="ml-2 font-medium">{execution.metadata.triggeredBy}</span>
                                </div>
                              </div>
                              {/* Progress Bar */}
                              <Progress value={execution.progress} className="mb-3" />
                              {/* Current Node */}
                              {execution.currentNode && (
                                <div className="text-sm md:text-base lg:text-lg">
                                  <span className="text-muted-foreground">Current step:</span>
                                  <span className="ml-2 font-medium">{execution.currentNode}</span>
                                </div>
                              )}
                              {/* Error Message */}
                              {execution.error && (
                                <Alert variant="destructive" className="mt-2">
                                  <AlertCircle className="h-4 w-4 " />
                                  <AlertDescription className="text-sm md:text-base lg:text-lg">
                                    {execution.error}
                                  </AlertDescription>
                                </Alert>
                              )}
                            </div>
                            {/* Action Buttons */}
                            <div className="flex flex-col gap-2 ml-4">
                              {execution.status === 'running' && (
                                <>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleExecutionAction('pause', execution.id);
                                    }}
                                    disabled={isLoading[execution.id]}
                                  >
                                    <Pause className="h-4 w-4 mr-1 " />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleExecutionAction('cancel', execution.id);
                                    }}
                                    disabled={isLoading[execution.id]}
                                  >
                                    <Square className="h-4 w-4 mr-1 " />
                                  </Button>
                                </>
                              )}
                              {execution.status === 'failed' && (
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    e.stopPropagation();
                                    handleExecutionAction('retry', execution.id);
                                  }}
                                  disabled={isLoading[execution.id]}
                                >
                                  <RotateCcw className="h-4 w-4 mr-1 " />
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onExportLogs?.(execution.id);
                                }}
                              >
                                <Download className="h-4 w-4 mr-1 " />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                  {filteredExecutions.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Activity className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                      <p>No executions found matching your criteria.</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
        {/* Execution Details Panel */}
        <div>
          {selectedExecution ? (
            <ExecutionDetailsPanel 
              execution={selectedExecution}
              workflow={workflows.find(w => w.id === selectedExecution.workflowId)}
              logLevelFilter={logLevelFilter}
              onLogLevelFilterChange={setLogLevelFilter}
              onClose={() => setSelectedExecution(null)}
            />
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-[600px] text-muted-foreground">
                <div className="text-center">
                  <Eye className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                  <p>Select an execution to view details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export interface ExecutionDetailsPanelProps {
  execution: WorkflowExecution;
  workflow?: WorkflowDefinition;
  logLevelFilter: string;
  onLogLevelFilterChange: (level: string) => void;
  onClose: () => void;
}

function ExecutionDetailsPanel({ 
  execution, 
  workflow, 
  logLevelFilter, 
  onLogLevelFilterChange, 
  onClose 
}: ExecutionDetailsPanelProps) {
  const filteredLogs = useMemo(() => {
    return execution.logs.filter(log => 
      logLevelFilter === 'all' || log.level === logLevelFilter
    );
  }, [execution.logs, logLevelFilter]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {workflow?.name || 'Unknown Workflow'}
            <Badge className={statusColors[execution.status]}>
              {execution.status}
            </Badge>
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} >
            ×
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="logs" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>
          <TabsContent value="logs" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground " />
                <select
                  value={logLevelFilter}
                  onChange={(e) => onLogLevelFilterChange(e.target.value)}
                  className="px-2 py-1 border border-input rounded text-sm md:text-base lg:text-lg"
                >
                  <option value="all">All Levels</option>
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warn">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>
              <Badge variant="outline">
                {filteredLogs.length} entries
              </Badge>
            </div>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {filteredLogs.map((log, index) => (
                  <div
                    key={log.id || index}
                    className={`p-3 rounded border text-sm ${logLevelColors[log.level]}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                        {log.level.toUpperCase()}
                      </Badge>
                      <span className="text-xs opacity-75 sm:text-sm md:text-base">
                        {log.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="font-medium">{log.message}</p>
                    {log.nodeId && (
                      <p className="text-xs opacity-75 mt-1 sm:text-sm md:text-base">
                        Node: {log.nodeId}
                      </p>
                    )}
                    {log.data && (
                      <details className="mt-2">
                        <summary className="text-xs cursor-pointer opacity-75 sm:text-sm md:text-base">
                        </summary>
                        <pre className="text-xs mt-1 p-2 bg-black/5 rounded overflow-auto sm:text-sm md:text-base">
                          {JSON.stringify(log.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
                {filteredLogs.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Bug className="h-6 w-6 mx-auto mb-2 opacity-50 " />
                    <p className="text-sm md:text-base lg:text-lg">No logs found for selected level</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="results" className="space-y-4">
            <ScrollArea className="h-[400px]">
              <div className="space-y-4">
                {Object.entries(execution.results).map(([nodeId, result]) => {
                  const node = workflow?.nodes.find(n => n.id === nodeId);
                  return (
                    <Card key={nodeId} className="p-3 sm:p-4 md:p-6">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-sm md:text-base lg:text-lg">
                          {node?.data.label || nodeId}
                        </h4>
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {typeof result}
                        </Badge>
                      </div>
                      <div className="bg-muted rounded p-2 sm:p-4 md:p-6">
                        <pre className="text-xs overflow-auto sm:text-sm md:text-base">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    </Card>
                  );
                })}
                {Object.keys(execution.results).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="h-6 w-6 mx-auto mb-2 opacity-50 " />
                    <p className="text-sm md:text-base lg:text-lg">No results available</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="performance" className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
              <div>
                <span className="text-muted-foreground">Execution ID:</span>
                <p className="font-mono text-xs mt-1 sm:text-sm md:text-base">{execution.id}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Workflow ID:</span>
                <p className="font-mono text-xs mt-1 sm:text-sm md:text-base">{execution.workflowId}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Start Time:</span>
                <p className="font-medium mt-1">{execution.startTime.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-muted-foreground">End Time:</span>
                <p className="font-medium mt-1">
                  {execution.endTime ? execution.endTime.toLocaleString() : 'Running...'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Duration:</span>
                <p className="font-medium mt-1">
                  {execution.duration ? `${execution.duration}ms` : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Progress:</span>
                <p className="font-medium mt-1">{execution.progress}%</p>
              </div>
            </div>
            {execution.currentNode && (
              <div>
                <span className="text-muted-foreground text-sm md:text-base lg:text-lg">Current Node:</span>
                <p className="font-medium mt-1">{execution.currentNode}</p>
              </div>
            )}
            <div>
              <span className="text-muted-foreground text-sm md:text-base lg:text-lg">Triggered By:</span>
              <p className="font-medium mt-1">{execution.metadata.triggeredBy}</p>
              {execution.metadata.trigger && (
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  Trigger: {execution.metadata.trigger}
                </p>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
