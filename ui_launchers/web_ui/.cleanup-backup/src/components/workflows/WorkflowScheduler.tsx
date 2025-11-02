'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Calendar, 
  Clock, 
  Play, 
  Pause, 
  Trash2, 
  Plus, 
  Settings, 
  Zap, 
  FileText, 
  Globe, 
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Activity,
  Timer,
  BarChart3
} from 'lucide-react';

import { 
  WorkflowTrigger, 
  CronSchedule, 
  WorkflowQueue, 
  QueuedWorkflow,
  WorkflowAutomationAnalytics,
  TimeSeriesData,
  OptimizationSuggestion
} from '@/types/workflows';

interface WorkflowSchedulerProps {
  triggers: WorkflowTrigger[];
  queues: WorkflowQueue[];
  analytics: WorkflowAutomationAnalytics;
  onCreateTrigger?: (trigger: Omit<WorkflowTrigger, 'id'>) => Promise<void>;
  onUpdateTrigger?: (triggerId: string, updates: Partial<WorkflowTrigger>) => Promise<void>;
  onDeleteTrigger?: (triggerId: string) => Promise<void>;
  onToggleTrigger?: (triggerId: string, enabled: boolean) => Promise<void>;
  onCreateQueue?: (queue: Omit<WorkflowQueue, 'id' | 'currentLoad' | 'tasks' | 'metrics'>) => Promise<void>;
  onUpdateQueue?: (queueId: string, updates: Partial<WorkflowQueue>) => Promise<void>;
  onDeleteQueue?: (queueId: string) => Promise<void>;
  className?: string;
}

const triggerTypeIcons = {
  schedule: Calendar,
  event: Zap,
  webhook: Globe,
  file: FileText,
  condition: Settings,
};

const triggerTypeColors = {
  schedule: 'bg-blue-100 text-blue-700 border-blue-200',
  event: 'bg-purple-100 text-purple-700 border-purple-200',
  webhook: 'bg-green-100 text-green-700 border-green-200',
  file: 'bg-orange-100 text-orange-700 border-orange-200',
  condition: 'bg-gray-100 text-gray-700 border-gray-200',
};

export function WorkflowScheduler({
  triggers,
  queues,
  analytics,
  onCreateTrigger,
  onUpdateTrigger,
  onDeleteTrigger,
  onToggleTrigger,
  onCreateQueue,
  onUpdateQueue,
  onDeleteQueue,
  className = '',
}: WorkflowSchedulerProps) {
  const [selectedTab, setSelectedTab] = useState('triggers');
  const [showCreateTrigger, setShowCreateTrigger] = useState(false);
  const [showCreateQueue, setShowCreateQueue] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState<WorkflowTrigger | null>(null);

  const schedulerStats = useMemo(() => {
    const activeTriggers = triggers.filter(t => t.enabled).length;
    const totalQueued = queues.reduce((sum, queue) => sum + queue.tasks.length, 0);
    const totalProcessing = queues.reduce((sum, queue) => sum + queue.currentLoad, 0);
    
    return {
      totalTriggers: triggers.length,
      activeTriggers,
      totalQueues: queues.length,
      totalQueued,
      totalProcessing,
      successRate: analytics.successRate,
      avgExecutionTime: analytics.averageExecutionTime,
    };
  }, [triggers, queues, analytics]);

  const formatNextRun = (date?: Date) => {
    if (!date) return 'Not scheduled';
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    
    if (diff < 0) return 'Overdue';
    if (diff < 60000) return 'In < 1 minute';
    if (diff < 3600000) return `In ${Math.floor(diff / 60000)} minutes`;
    if (diff < 86400000) return `In ${Math.floor(diff / 3600000)} hours`;
    return `In ${Math.floor(diff / 86400000)} days`;
  };

  const validateCronExpression = (expression: string): boolean => {
    // Basic cron validation - in a real app, use a proper cron parser
    const parts = expression.split(' ');
    return parts.length === 5 || parts.length === 6;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Scheduler Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Workflow Scheduler</h2>
          <p className="text-muted-foreground">Automate workflow execution with triggers and queues</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowCreateQueue(true)}
            variant="outline"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Queue
          </Button>
          <Button
            onClick={() => setShowCreateTrigger(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Trigger
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Triggers</p>
                <p className="text-2xl font-bold">{schedulerStats.activeTriggers}</p>
                <p className="text-xs text-muted-foreground">
                  of {schedulerStats.totalTriggers} total
                </p>
              </div>
              <Timer className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Queued Tasks</p>
                <p className="text-2xl font-bold">{schedulerStats.totalQueued}</p>
                <p className="text-xs text-muted-foreground">
                  {schedulerStats.totalProcessing} processing
                </p>
              </div>
              <Activity className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {(schedulerStats.successRate * 100).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {schedulerStats.avgExecutionTime < 1000 
                    ? `${schedulerStats.avgExecutionTime}ms`
                    : `${(schedulerStats.avgExecutionTime / 1000).toFixed(1)}s`
                  }
                </p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="triggers">Triggers</TabsTrigger>
          <TabsTrigger value="queues">Queues</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="triggers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Triggers ({triggers.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-4">
                  {triggers.map((trigger) => {
                    const IconComponent = triggerTypeIcons[trigger.type];
                    
                    return (
                      <Card key={trigger.id} className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <IconComponent className="h-5 w-5" />
                              <h3 className="font-semibold">{trigger.name}</h3>
                              <Badge className={triggerTypeColors[trigger.type]}>
                                {trigger.type}
                              </Badge>
                              {trigger.enabled ? (
                                <Badge className="bg-green-100 text-green-700">
                                  Active
                                </Badge>
                              ) : (
                                <Badge variant="secondary">
                                  Inactive
                                </Badge>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                              <div>
                                <span className="text-muted-foreground">Workflow:</span>
                                <span className="ml-2 font-medium">{trigger.workflowId}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Last Triggered:</span>
                                <span className="ml-2 font-medium">
                                  {trigger.lastTriggered 
                                    ? trigger.lastTriggered.toLocaleString()
                                    : 'Never'
                                  }
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Next Run:</span>
                                <span className="ml-2 font-medium">
                                  {formatNextRun(trigger.nextTrigger)}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Type:</span>
                                <span className="ml-2 font-medium">{trigger.type}</span>
                              </div>
                            </div>
                            
                            {/* Trigger-specific details */}
                            {trigger.type === 'schedule' && trigger.config.schedule && (
                              <div className="text-sm">
                                <span className="text-muted-foreground">Schedule:</span>
                                <code className="ml-2 px-2 py-1 bg-muted rounded text-xs">
                                  {trigger.config.schedule.expression}
                                </code>
                                <span className="ml-2 text-muted-foreground">
                                  ({trigger.config.schedule.timezone})
                                </span>
                              </div>
                            )}
                            
                            {trigger.type === 'webhook' && trigger.config.webhook && (
                              <div className="text-sm">
                                <span className="text-muted-foreground">URL:</span>
                                <code className="ml-2 px-2 py-1 bg-muted rounded text-xs">
                                  {trigger.config.webhook.method} {trigger.config.webhook.url}
                                </code>
                              </div>
                            )}
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="flex items-center gap-2 ml-4">
                            <Switch
                              checked={trigger.enabled}
                              onCheckedChange={(enabled) => 
                                onToggleTrigger?.(trigger.id, enabled)
                              }
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingTrigger(trigger)}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onDeleteTrigger?.(trigger.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                  
                  {triggers.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Timer className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No triggers configured.</p>
                      <Button 
                        className="mt-2" 
                        onClick={() => setShowCreateTrigger(true)}
                      >
                        Create your first trigger
                      </Button>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="queues" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {queues.map((queue) => (
              <Card key={queue.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      {queue.name}
                    </CardTitle>
                    <Badge variant="outline">
                      Priority {queue.priority}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Max Concurrency:</span>
                        <span className="ml-2 font-medium">{queue.maxConcurrency}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Current Load:</span>
                        <span className="ml-2 font-medium">
                          {queue.currentLoad}/{queue.maxConcurrency}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Queued Tasks:</span>
                        <span className="ml-2 font-medium">{queue.tasks.length}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Throughput:</span>
                        <span className="ml-2 font-medium">
                          {queue.metrics.throughput.toFixed(1)}/min
                        </span>
                      </div>
                    </div>
                    
                    {/* Queue Progress */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Capacity Usage</span>
                        <span>{Math.round((queue.currentLoad / queue.maxConcurrency) * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(queue.currentLoad / queue.maxConcurrency) * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    {/* Queue Metrics */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Avg Wait Time:</span>
                        <span className="ml-2 font-medium">
                          {queue.metrics.averageWaitTime < 1000 
                            ? `${queue.metrics.averageWaitTime}ms`
                            : `${(queue.metrics.averageWaitTime / 1000).toFixed(1)}s`
                          }
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Error Rate:</span>
                        <span className="ml-2 font-medium">
                          {(queue.metrics.errorRate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    {/* Recent Tasks */}
                    {queue.tasks.length > 0 && (
                      <div>
                        <Label className="text-sm font-medium">Recent Tasks</Label>
                        <div className="mt-2 space-y-1">
                          {queue.tasks.slice(0, 3).map((task) => (
                            <div key={task.id} className="flex items-center justify-between text-xs p-2 bg-muted rounded">
                              <span>{task.workflowId}</span>
                              <Badge variant="outline" className="text-xs">
                                Priority {task.priority}
                              </Badge>
                            </div>
                          ))}
                          {queue.tasks.length > 3 && (
                            <div className="text-xs text-muted-foreground text-center">
                              +{queue.tasks.length - 3} more tasks
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {queues.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center">
                    <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No queues configured.</p>
                    <Button 
                      className="mt-2" 
                      onClick={() => setShowCreateQueue(true)}
                    >
                      Create your first queue
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Execution Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-600">
                        {(analytics.successRate * 100).toFixed(1)}%
                      </p>
                      <p className="text-sm text-muted-foreground">Success Rate</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">
                        {(analytics.failureRate * 100).toFixed(1)}%
                      </p>
                      <p className="text-sm text-muted-foreground">Failure Rate</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {analytics.averageExecutionTime < 1000 
                          ? `${analytics.averageExecutionTime}ms`
                          : `${(analytics.averageExecutionTime / 1000).toFixed(1)}s`
                        }
                      </p>
                      <p className="text-sm text-muted-foreground">Avg Duration</p>
                    </div>
                  </div>
                  
                  {/* Placeholder for chart */}
                  <div className="h-[200px] bg-muted rounded flex items-center justify-center">
                    <BarChart3 className="h-8 w-8 text-muted-foreground" />
                    <span className="ml-2 text-muted-foreground">Execution Trends Chart</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Resource Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>CPU Usage</span>
                      <span>{(analytics.resourceUtilization.cpu * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${analytics.resourceUtilization.cpu * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Memory Usage</span>
                      <span>{(analytics.resourceUtilization.memory * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${analytics.resourceUtilization.memory * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  {analytics.resourceUtilization.gpu && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>GPU Usage</span>
                        <span>{(analytics.resourceUtilization.gpu * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${analytics.resourceUtilization.gpu * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="pt-4">
                    <h4 className="font-medium mb-2">Cost Analysis</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Total Cost:</span>
                        <span className="ml-2 font-medium">
                          ${analytics.costAnalysis.totalCost.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Cost per Execution:</span>
                        <span className="ml-2 font-medium">
                          ${analytics.costAnalysis.costPerExecution.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="optimization" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Bottlenecks</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {analytics.bottlenecks.map((bottleneck, index) => (
                      <Alert key={index} className={
                        bottleneck.impact === 'high' ? 'border-red-200 bg-red-50' :
                        bottleneck.impact === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                        'border-blue-200 bg-blue-50'
                      }>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <div className="font-medium">{bottleneck.nodeName}</div>
                          <div className="text-sm text-muted-foreground">
                            Avg execution: {bottleneck.averageExecutionTime}ms
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Impact: {bottleneck.impact} • Frequency: {bottleneck.frequency}
                          </div>
                          {bottleneck.suggestions.length > 0 && (
                            <ul className="text-sm mt-2 list-disc list-inside">
                              {bottleneck.suggestions.map((suggestion, i) => (
                                <li key={i}>{suggestion}</li>
                              ))}
                            </ul>
                          )}
                        </AlertDescription>
                      </Alert>
                    ))}
                    
                    {analytics.bottlenecks.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground">
                        <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No performance bottlenecks detected.</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Optimization Suggestions</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {analytics.optimizationSuggestions.map((suggestion) => (
                      <Alert key={suggestion.id} className={
                        suggestion.priority === 'high' ? 'border-red-200 bg-red-50' :
                        suggestion.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                        'border-green-200 bg-green-50'
                      }>
                        <TrendingUp className="h-4 w-4" />
                        <AlertDescription>
                          <div className="font-medium">{suggestion.title}</div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {suggestion.description}
                          </div>
                          <div className="text-sm mt-2">
                            <strong>Impact:</strong> {suggestion.estimatedImpact}
                          </div>
                          <div className="text-sm">
                            <strong>Implementation:</strong> {suggestion.implementation}
                          </div>
                          <Badge 
                            variant="outline" 
                            className={`mt-2 ${
                              suggestion.priority === 'high' ? 'border-red-300 text-red-700' :
                              suggestion.priority === 'medium' ? 'border-yellow-300 text-yellow-700' :
                              'border-green-300 text-green-700'
                            }`}
                          >
                            {suggestion.priority} priority
                          </Badge>
                        </AlertDescription>
                      </Alert>
                    ))}
                    
                    {analytics.optimizationSuggestions.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground">
                        <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No optimization suggestions available.</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Trigger Modal */}
      {showCreateTrigger && (
        <TriggerCreationModal
          onClose={() => setShowCreateTrigger(false)}
          onSave={onCreateTrigger}
        />
      )}

      {/* Edit Trigger Modal */}
      {editingTrigger && (
        <TriggerEditModal
          trigger={editingTrigger}
          onClose={() => setEditingTrigger(null)}
          onSave={onUpdateTrigger}
        />
      )}

      {/* Create Queue Modal */}
      {showCreateQueue && (
        <QueueCreationModal
          onClose={() => setShowCreateQueue(false)}
          onSave={onCreateQueue}
        />
      )}
    </div>
  );
}

// Modal components would be implemented here
function TriggerCreationModal({ onClose, onSave }: any) {
  return <div>Trigger Creation Modal</div>;
}

function TriggerEditModal({ trigger, onClose, onSave }: any) {
  return <div>Trigger Edit Modal</div>;
}

function QueueCreationModal({ onClose, onSave }: any) {
  return <div>Queue Creation Modal</div>;
}