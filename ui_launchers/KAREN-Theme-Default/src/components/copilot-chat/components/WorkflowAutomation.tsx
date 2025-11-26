import React, { useState } from 'react';
import { useWorkflowEngine } from '../core/workflow-engine-hooks';
import { useWorkflowTemplates } from '../core/workflow-engine-hooks';
import { CopilotWorkflow } from '../types/copilot';
import { Button } from '../../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';
import { Clock, CheckCircle, XCircle, Pause, Play, RotateCcw, Trash2, Plus, FileText } from 'lucide-react';

/**
 * WorkflowAutomation - Provides Copilot-powered workflow automation features
 * Implements Phase 4 of the INNOVATIVE_COPILOT_PLAN.md
 */

interface WorkflowAutomationProps {
  className?: string;
}

interface WorkflowCardProps {
  workflow: CopilotWorkflow;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  result?: unknown;
  onStart: () => void;
  onCancel: () => void;
  onPause: () => void;
  onResume: () => void;
  onRetry: () => void;
}

/**
 * WorkflowCard component for displaying a single workflow
 */
const WorkflowCard: React.FC<WorkflowCardProps> = ({
  workflow,
  status,
  progress,
  result,
  onStart,
  onCancel,
  onPause,
  onResume,
  onRetry,
}) => {
  const [expanded, setExpanded] = useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Clock className="h-4 w-4 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      default:
        return <Play className="h-4 w-4" />;
    }
  };

  const getStatusBadgeVariant = () => {
    switch (status) {
      case 'running':
        return 'default';
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'cancelled':
        return 'secondary';
      case 'paused':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Running';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      case 'paused':
        return 'Paused';
      default:
        return 'Idle';
    }
  };

  const getComplexityBadgeVariant = () => {
    switch (workflow.complexity) {
      case 'basic':
        return 'secondary';
      case 'intermediate':
        return 'default';
      case 'advanced':
        return 'default';
      case 'expert':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="flex items-center gap-2">
              {workflow.title}
              <Badge variant={getComplexityBadgeVariant()}>
                {workflow.complexity}
              </Badge>
            </CardTitle>
            <CardDescription>{workflow.description}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusBadgeVariant()} className="flex items-center gap-1">
              {getStatusIcon()}
              {getStatusText()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Estimated time: {workflow.estimatedTime}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Show Less' : 'Show Steps'}
            </Button>
          </div>

          {status !== 'idle' && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {expanded && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Steps:</h4>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                {workflow.steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {status === 'failed' && result && typeof result === 'object' && result !== null && 'error' in result ? (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Workflow Failed</AlertTitle>
              <AlertDescription>{String((result as Record<string, unknown>).error)}</AlertDescription>
            </Alert>
          ) : null}

          {status === 'completed' && result ? (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Workflow Completed</AlertTitle>
              <AlertDescription>
                {typeof result === 'object' && result !== null && 'success' in result && (result as Record<string, unknown>).success ? 'Workflow completed successfully.' : 'Workflow completed with warnings.'}
              </AlertDescription>
            </Alert>
          ) : null}

          <div className="flex justify-end gap-2">
            {status === 'idle' && (
              <Button onClick={onStart} size="sm">
                <Play className="h-4 w-4 mr-1" />
                Start
              </Button>
            )}
            {status === 'running' && (
              <>
                <Button onClick={onPause} variant="outline" size="sm">
                  <Pause className="h-4 w-4 mr-1" />
                  Pause
                </Button>
                <Button onClick={onCancel} variant="outline" size="sm">
                  <XCircle className="h-4 w-4 mr-1" />
                  Cancel
                </Button>
              </>
            )}
            {status === 'paused' && (
              <>
                <Button onClick={onResume} size="sm">
                  <Play className="h-4 w-4 mr-1" />
                  Resume
                </Button>
                <Button onClick={onCancel} variant="outline" size="sm">
                  <XCircle className="h-4 w-4 mr-1" />
                  Cancel
                </Button>
              </>
            )}
            {status === 'failed' && (
              <Button onClick={onRetry} variant="outline" size="sm">
                <RotateCcw className="h-4 w-4 mr-1" />
                Retry
              </Button>
            )}
            {(status === 'completed' || status === 'cancelled') && (
              <Button onClick={onStart} variant="outline" size="sm">
                <Play className="h-4 w-4 mr-1" />
                Run Again
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * WorkflowAutomation component
 */
export const WorkflowAutomation: React.FC<WorkflowAutomationProps> = ({ className }) => {
  const {
    startWorkflow,
    cancelWorkflow,
    pauseWorkflow,
    resumeWorkflow,
    retryWorkflow,
    getWorkflowHistory,
    clearWorkflowHistory,
    error,
    clearError,
  } = useWorkflowEngine();

  const workflowTemplates = useWorkflowTemplates();
  const workflowHistory = getWorkflowHistory();
  const { getWorkflowStatus, getWorkflowProgress, getWorkflowResult } = useWorkflowEngine();
  

  // Get all unique workflow IDs from templates and history
  const allWorkflowIds = Array.from(new Set([
    ...workflowTemplates.map(t => t.id),
    ...workflowHistory.map(h => h.workflowId),
  ]));

  // Get workflow details for all workflow IDs
  const allWorkflows = allWorkflowIds.map(id => {
    const template = workflowTemplates.find(t => t.id === id);
    const status = getWorkflowStatus(id);
    const progress = getWorkflowProgress(id);
    const result = getWorkflowResult(id);
    
    return {
      id,
      workflow: template || {
        id,
        title: `Unknown Workflow (${id})`,
        description: 'Workflow details not available',
        steps: [],
        estimatedTime: 'Unknown',
        complexity: 'basic' as const,
        metadata: {},
      },
      status,
      progress,
      result,
    };
  });

  // Group workflows by status
  const runningWorkflows = allWorkflows.filter(w => w.status === 'running');
  const completedWorkflows = allWorkflows.filter(w => w.status === 'completed');
  const failedWorkflows = allWorkflows.filter(w => w.status === 'failed');
  const idleWorkflows = allWorkflows.filter(w => w.status === 'idle');

  return (
    <div className={className}>
      {error && (
        <Alert variant="destructive" className="mb-4">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
          <Button variant="outline" size="sm" onClick={clearError} className="mt-2">
            Dismiss
          </Button>
        </Alert>
      )}

      <Tabs defaultValue="templates" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="running">Running</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="failed">Failed</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Workflow Templates</h2>
            <Button>
              <Plus className="h-4 w-4 mr-1" />
              New Template
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {idleWorkflows.map(({ id, workflow, status, progress, result }) => (
              <WorkflowCard
                key={id}
                workflow={workflow}
                status={status}
                progress={progress}
                result={result}
                onStart={() => startWorkflow(id)}
                onCancel={() => cancelWorkflow(id)}
                onPause={() => pauseWorkflow(id)}
                onResume={() => resumeWorkflow(id)}
                onRetry={() => retryWorkflow(id)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="running" className="space-y-4">
          <h2 className="text-xl font-semibold">Running Workflows</h2>
          
          {runningWorkflows.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-2" />
              <p>No workflows are currently running</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {runningWorkflows.map(({ id, workflow, status, progress, result }) => (
                <WorkflowCard
                  key={id}
                  workflow={workflow}
                  status={status}
                  progress={progress}
                  result={result}
                  onStart={() => startWorkflow(id)}
                  onCancel={() => cancelWorkflow(id)}
                  onPause={() => pauseWorkflow(id)}
                  onResume={() => resumeWorkflow(id)}
                  onRetry={() => retryWorkflow(id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Completed Workflows</h2>
            {completedWorkflows.length > 0 && (
              <Button variant="outline" onClick={clearWorkflowHistory}>
                <Trash2 className="h-4 w-4 mr-1" />
                Clear History
              </Button>
            )}
          </div>
          
          {completedWorkflows.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-2" />
              <p>No workflows have been completed yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {completedWorkflows.map(({ id, workflow, status, progress, result }) => (
                <WorkflowCard
                  key={id}
                  workflow={workflow}
                  status={status}
                  progress={progress}
                  result={result}
                  onStart={() => startWorkflow(id)}
                  onCancel={() => cancelWorkflow(id)}
                  onPause={() => pauseWorkflow(id)}
                  onResume={() => resumeWorkflow(id)}
                  onRetry={() => retryWorkflow(id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="failed" className="space-y-4">
          <h2 className="text-xl font-semibold">Failed Workflows</h2>
          
          {failedWorkflows.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <XCircle className="h-12 w-12 mx-auto mb-2" />
              <p>No workflows have failed</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {failedWorkflows.map(({ id, workflow, status, progress, result }) => (
                <WorkflowCard
                  key={id}
                  workflow={workflow}
                  status={status}
                  progress={progress}
                  result={result}
                  onStart={() => startWorkflow(id)}
                  onCancel={() => cancelWorkflow(id)}
                  onPause={() => pauseWorkflow(id)}
                  onResume={() => resumeWorkflow(id)}
                  onRetry={() => retryWorkflow(id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Workflow History</h2>
            {workflowHistory.length > 0 && (
              <Button variant="outline" onClick={clearWorkflowHistory}>
                <Trash2 className="h-4 w-4 mr-1" />
                Clear History
              </Button>
            )}
          </div>
          
          {workflowHistory.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-2" />
              <p>No workflow history available</p>
            </div>
          ) : (
            <div className="space-y-4">
              {workflowHistory.map((history, index) => {
                const workflow = workflowTemplates.find(t => t.id === history.workflowId);
                if (!workflow) return null;
                
                return (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            {workflow.title}
                            <Badge variant={
                              history.status === 'completed' ? 'default' :
                              history.status === 'failed' ? 'destructive' :
                              history.status === 'cancelled' ? 'secondary' :
                              'outline'
                            }>
                              {history.status}
                            </Badge>
                          </CardTitle>
                          <CardDescription>
                            Started: {history.startTime.toLocaleString()}
                            {history.endTime && ` • Ended: ${history.endTime.toLocaleString()}`}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {history.error && (
                        <Alert variant="destructive" className="mb-2">
                          <XCircle className="h-4 w-4" />
                          <AlertTitle>Error</AlertTitle>
                          <AlertDescription>{history.error}</AlertDescription>
                        </Alert>
                      )}
                      {history.result ? (
                        <Alert className="mb-2">
                          <CheckCircle className="h-4 w-4" />
                          <AlertTitle>Result</AlertTitle>
                          <AlertDescription>
                            {typeof history.result === 'object' && history.result !== null
                              ? JSON.stringify(history.result as Record<string, unknown>, null, 2)
                              : String(history.result)}
                          </AlertDescription>
                        </Alert>
                      ) : null}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WorkflowAutomation;