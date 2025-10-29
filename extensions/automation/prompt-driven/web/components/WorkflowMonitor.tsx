/**
 * Workflow Monitor - Real-time monitoring dashboard for automation workflows
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  RefreshCw,
  BarChart3
} from 'lucide-react';

interface ExecutionMetrics {
  total_workflows: number;
  active_workflows: number;
  total_executions: number;
  successful_executions: number;
  success_rate: number;
  avg_workflow_success_rate: number;
}

interface ExecutionHistory {
  execution_id: string;
  workflow_id: string;
  success: boolean;
  duration: number;
  steps_executed: number;
  start_time: string;
  end_time: string;
  error?: string;
  failed_step?: string;
}

interface WorkflowStatus {
  id: string;
  name: string;
  status: string;
  execution_count: number;
  success_rate: number;
  last_execution?: string;
  avg_duration?: number;
}

const WorkflowMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [executions, setExecutions] = useState<ExecutionHistory[]>([]);
  const [workflowStatuses, setWorkflowStatuses] = useState<WorkflowStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const API_BASE = '/api/extensions/prompt-driven-automation';

  useEffect(() => {
    loadMonitoringData();
    
    if (autoRefresh) {
      const interval = setInterval(loadMonitoringData, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    }
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [autoRefresh]);

  const loadMonitoringData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadMetrics(),
        loadExecutionHistory(),
        loadWorkflowStatuses()
      ]);
    } catch (error) {
      console.error('Error loading monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    const response = await fetch(`${API_BASE}/metrics`);
    if (response.ok) {
      const data = await response.json();
      setMetrics(data);
    }
  };

  const loadExecutionHistory = async () => {
    const response = await fetch(`${API_BASE}/execution-history?limit=50`);
    if (response.ok) {
      const data = await response.json();
      setExecutions(data.executions || []);
    }
  };

  const loadWorkflowStatuses = async () => {
    const response = await fetch(`${API_BASE}/workflows`);
    if (response.ok) {
      const data = await response.json();
      const workflows = data.workflows || [];
      
      // Calculate additional metrics for each workflow
      const statusData = workflows.map((workflow: any) => {
        const workflowExecutions = executions.filter(e => e.workflow_id === workflow.id);
        const avgDuration = workflowExecutions.length > 0 
          ? workflowExecutions.reduce((sum, e) => sum + e.duration, 0) / workflowExecutions.length
          : 0;
        
        const lastExecution = workflowExecutions.length > 0 
          ? workflowExecutions.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())[0]
          : null;

        return {
          id: workflow.id,
          name: workflow.name,
          status: workflow.status,
          execution_count: workflow.execution_count,
          success_rate: workflow.success_rate,
          last_execution: lastExecution?.start_time,
          avg_duration: avgDuration
        };
      });
      
      setWorkflowStatuses(statusData);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    );
  };

  const getWorkflowStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const recentFailures = executions.filter(e => !e.success).slice(0, 5);
  const recentSuccesses = executions.filter(e => e.success).slice(0, 10);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold">Workflow Monitor</h1>
          <Badge variant={autoRefresh ? "default" : "secondary"}>
            {autoRefresh ? "Live" : "Paused"}
          </Badge>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? "Pause" : "Resume"} Auto-refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadMonitoringData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Workflows</p>
                  <p className="text-2xl font-bold">{metrics.total_workflows}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Workflows</p>
                  <p className="text-2xl font-bold">{metrics.active_workflows}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-purple-500" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Executions</p>
                  <p className="text-2xl font-bold">{metrics.total_executions}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold">{(metrics.success_rate * 100).toFixed(1)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="executions">Recent Executions</TabsTrigger>
          <TabsTrigger value="workflows">Workflow Status</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Recent Successful Executions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Recent Successful Executions</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentSuccesses.slice(0, 5).map((execution) => (
                    <div key={execution.execution_id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{execution.workflow_id}</p>
                        <p className="text-xs text-gray-600">{formatTimestamp(execution.start_time)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{formatDuration(execution.duration)}</p>
                        <p className="text-xs text-gray-600">{execution.steps_executed} steps</p>
                      </div>
                    </div>
                  ))}
                  {recentSuccesses.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No recent successful executions</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recent Failures */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span>Recent Failures</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentFailures.map((execution) => (
                    <div key={execution.execution_id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{execution.workflow_id}</p>
                        <p className="text-xs text-gray-600">{formatTimestamp(execution.start_time)}</p>
                        {execution.error && (
                          <p className="text-xs text-red-600 mt-1">{execution.error}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{formatDuration(execution.duration)}</p>
                        {execution.failed_step && (
                          <p className="text-xs text-red-600">Failed: {execution.failed_step}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {recentFailures.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No recent failures</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execution History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {executions.map((execution) => (
                  <div key={execution.execution_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(execution.success)}
                      <div>
                        <p className="font-medium">{execution.workflow_id}</p>
                        <p className="text-sm text-gray-600">ID: {execution.execution_id}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-6 text-sm">
                      <div className="text-center">
                        <p className="font-medium">{formatDuration(execution.duration)}</p>
                        <p className="text-gray-600">Duration</p>
                      </div>
                      
                      <div className="text-center">
                        <p className="font-medium">{execution.steps_executed}</p>
                        <p className="text-gray-600">Steps</p>
                      </div>
                      
                      <div className="text-center">
                        <p className="font-medium">{formatTimestamp(execution.start_time)}</p>
                        <p className="text-gray-600">Started</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <div className="grid gap-4">
            {workflowStatuses.map((workflow) => (
              <Card key={workflow.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-semibold">{workflow.name}</h3>
                        <Badge className={getWorkflowStatusColor(workflow.status)}>
                          {workflow.status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-600">Executions</p>
                          <p className="font-medium">{workflow.execution_count}</p>
                        </div>
                        
                        <div>
                          <p className="text-gray-600">Success Rate</p>
                          <div className="flex items-center space-x-2">
                            <Progress value={workflow.success_rate * 100} className="w-16 h-2" />
                            <span className="font-medium">{(workflow.success_rate * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                        
                        <div>
                          <p className="text-gray-600">Avg Duration</p>
                          <p className="font-medium">{formatDuration(workflow.avg_duration || 0)}</p>
                        </div>
                        
                        <div>
                          <p className="text-gray-600">Last Execution</p>
                          <p className="font-medium">
                            {workflow.last_execution 
                              ? formatTimestamp(workflow.last_execution)
                              : 'Never'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <span>System Alerts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Generate alerts based on metrics */}
                {metrics && metrics.success_rate < 0.8 && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="font-medium text-yellow-800">Low Success Rate</p>
                        <p className="text-sm text-yellow-700">
                          Overall success rate is {(metrics.success_rate * 100).toFixed(1)}%. Consider reviewing failed workflows.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {workflowStatuses.filter(w => w.success_rate < 0.7).map((workflow) => (
                  <div key={workflow.id} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <XCircle className="h-5 w-5 text-red-600" />
                      <div>
                        <p className="font-medium text-red-800">Workflow Issues: {workflow.name}</p>
                        <p className="text-sm text-red-700">
                          Success rate is {(workflow.success_rate * 100).toFixed(1)}%. This workflow may need attention.
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                
                {metrics && metrics.active_workflows === 0 && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-blue-800">No Active Workflows</p>
                        <p className="text-sm text-blue-700">
                          You have no active workflows. Consider activating some workflows to start automation.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Show success message if everything is good */}
                {metrics && 
                 metrics.success_rate >= 0.9 && 
                 metrics.active_workflows > 0 && 
                 workflowStatuses.every(w => w.success_rate >= 0.8) && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium text-green-800">All Systems Operational</p>
                        <p className="text-sm text-green-700">
                          All workflows are performing well with high success rates.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WorkflowMonitor;