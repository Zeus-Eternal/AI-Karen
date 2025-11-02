
"use client";
import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';


import { } from 'lucide-react';

import { } from '@/types/workflows';
interface AgentDashboardProps {
  agents: Agent[];
  onStartAgent?: (agentId: string) => Promise<void>;
  onStopAgent?: (agentId: string) => Promise<void>;
  onRestartAgent?: (agentId: string) => Promise<void>;
  onConfigureAgent?: (agentId: string) => void;
  className?: string;
}
const statusColors = {
  idle: 'bg-gray-100 text-gray-700 border-gray-200',
  running: 'bg-green-100 text-green-700 border-green-200',
  paused: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  stopped: 'bg-gray-100 text-gray-600 border-gray-200',
};
const healthColors = {
  healthy: 'text-green-600',
  warning: 'text-yellow-600',
  critical: 'text-red-600',
  unknown: 'text-gray-600',
};
const taskPriorityColors = {
  low: 'bg-blue-100 text-blue-700',
  normal: 'bg-gray-100 text-gray-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};
const getHealthIcon = (health: AgentHealth) => {
  switch (health.status) {
    case 'healthy':
      return <CheckCircle className="h-4 w-4 text-green-600 " />;
    case 'warning':
      return <AlertCircle className="h-4 w-4 text-yellow-600 " />;
    case 'critical':
      return <AlertCircle className="h-4 w-4 text-red-600 " />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-600 " />;
  }
};
export function AgentDashboard({
  agents,
  onStartAgent,
  onStopAgent,
  onRestartAgent,
  onConfigureAgent,
  className = '',
}: AgentDashboardProps) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});
  const filteredAgents = useMemo(() => {
    return agents.filter(agent => {
      const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           agent.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
      return matchesSearch && matchesStatus;

  }, [agents, searchTerm, statusFilter]);
  const agentStats = useMemo(() => {
    const stats = {
      total: agents.length,
      running: 0,
      idle: 0,
      error: 0,
      paused: 0,
      stopped: 0,
      totalTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
    };
    agents.forEach(agent => {
      stats[agent.status]++;
      stats.totalTasks += agent.metrics.tasksCompleted + agent.metrics.tasksInProgress + agent.metrics.tasksFailed;
      stats.completedTasks += agent.metrics.tasksCompleted;
      stats.failedTasks += agent.metrics.tasksFailed;

    return stats;
  }, [agents]);
  const handleAgentAction = useCallback(async (
    action: 'start' | 'stop' | 'restart',
    agentId: string
  ) => {
    setIsLoading(prev => ({ ...prev, [agentId]: true }));
    try {
      switch (action) {
        case 'start':
          await onStartAgent?.(agentId);
          break;
        case 'stop':
          await onStopAgent?.(agentId);
          break;
        case 'restart':
          await onRestartAgent?.(agentId);
          break;
      }
    } catch (error) {
    } finally {
      setIsLoading(prev => ({ ...prev, [agentId]: false }));
    }
  }, [onStartAgent, onStopAgent, onRestartAgent]);
  const formatUptime = (uptime: number) => {
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };
  const formatResourceUsage = (usage: number) => {
    return `${(usage * 100).toFixed(1)}%`;
  };
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Agent Management</h2>
          <p className="text-muted-foreground">Monitor and control your AI agents</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground " />
            <input
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64 "
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-input rounded-md text-sm md:text-base lg:text-lg"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="idle">Idle</option>
            <option value="paused">Paused</option>
            <option value="error">Error</option>
            <option value="stopped">Stopped</option>
          </select>
        </div>
      </div>
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Total Agents</p>
                <p className="text-2xl font-bold">{agentStats.total}</p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Running</p>
                <p className="text-2xl font-bold text-green-600">{agentStats.running}</p>
              </div>
              <Activity className="h-8 w-8 text-green-600 " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Tasks Completed</p>
                <p className="text-2xl font-bold">{agentStats.completedTasks}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-blue-600 " />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">Success Rate</p>
                <p className="text-2xl font-bold">
                  {agentStats.totalTasks > 0 
                    ? `${((agentStats.completedTasks / agentStats.totalTasks) * 100).toFixed(1)}%`
                    : '0%'
                  }
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600 " />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Agents ({filteredAgents.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {filteredAgents.map((agent) => (
                    <Card
                      key={agent.id}
                      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                        selectedAgent?.id === agent.id ? 'ring-2 ring-blue-500' : ''
                      }`}
                      onClick={() => setSelectedAgent(agent)}
                    >
                      <CardContent className="p-4 sm:p-4 md:p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-semibold">{agent.name}</h3>
                              <Badge className={statusColors[agent.status]}>
                                {agent.status}
                              </Badge>
                              {getHealthIcon(agent.health)}
                            </div>
                            <p className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">
                              {agent.description}
                            </p>
                            <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                              <div>
                                <span className="text-muted-foreground">Type:</span>
                                <span className="ml-2 font-medium">{agent.type}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Uptime:</span>
                                <span className="ml-2 font-medium">{formatUptime(agent.metrics.uptime)}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Tasks:</span>
                                <span className="ml-2 font-medium">
                                  {agent.metrics.tasksInProgress} running, {agent.taskQueue.length} queued
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Success Rate:</span>
                                <span className="ml-2 font-medium">
                                  {(agent.metrics.successRate * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                            {/* Resource Usage */}
                            <div className="mt-3 space-y-2">
                              <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                                <span className="flex items-center gap-1">
                                  <Cpu className="h-3 w-3 " />
                                </span>
                                <span>{formatResourceUsage(agent.metrics.resourceUsage.cpu)}</span>
                              </div>
                              <Progress 
                                value={agent.metrics.resourceUsage.cpu * 100} 
                                className="h-1"
                              />
                              <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                                <span className="flex items-center gap-1">
                                  <MemoryStick className="h-3 w-3 " />
                                </span>
                                <span>{formatResourceUsage(agent.metrics.resourceUsage.memory)}</span>
                              </div>
                              <Progress 
                                value={agent.metrics.resourceUsage.memory * 100} 
                                className="h-1"
                              />
                            </div>
                          </div>
                          {/* Action Buttons */}
                          <div className="flex flex-col gap-2 ml-4">
                            {agent.status === 'stopped' || agent.status === 'idle' ? (
                              <button
                                size="sm"
                                onClick={() => {
                                  e.stopPropagation();
                                  handleAgentAction('start', agent.id);
                                }}
                                disabled={isLoading[agent.id]}
                              >
                                <Play className="h-4 w-4 mr-1 " />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={(e) = > {
                                  e.stopPropagation();
                                  handleAgentAction('stop', agent.id);
                                }}
                                disabled={isLoading[agent.id]}
                              >
                                <Square className="h-4 w-4 mr-1 " />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) = > {
                                e.stopPropagation();
                                handleAgentAction('restart', agent.id);
                              }}
                              disabled={isLoading[agent.id]}
                            >
                              <RotateCcw className="h-4 w-4 mr-1 " />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) = > {
                                e.stopPropagation();
                                onConfigureAgent?.(agent.id);
                              }}
                            >
                              <Settings className="h-4 w-4 mr-1 " />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {filteredAgents.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Users className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                      <p>No agents found matching your criteria.</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
        {/* Agent Details Panel */}
        <div>
          {selectedAgent ? (
            <AgentDetailsPanel 
              agent={selectedAgent} 
              onClose={() => setSelectedAgent(null)}
            />
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-[600px] text-muted-foreground">
                <div className="text-center">
                  <Activity className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                  <p>Select an agent to view details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
interface AgentDetailsPanelProps {
  agent: Agent;
  onClose: () => void;
}
function AgentDetailsPanel({ agent, onClose }: AgentDetailsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {agent.name}
            <Badge className={statusColors[agent.status]}>
              {agent.status}
            </Badge>
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} >
            ×
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div>
              <Label className="text-sm font-medium md:text-base lg:text-lg">Description</Label>
              <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">{agent.description}</p>
            </div>
            <div>
              <Label className="text-sm font-medium md:text-base lg:text-lg">Configuration</Label>
              <div className="mt-2 space-y-2 text-sm md:text-base lg:text-lg">
                <div className="flex justify-between">
                  <span>Max Concurrent Tasks:</span>
                  <span>{agent.config.maxConcurrentTasks}</span>
                </div>
                <div className="flex justify-between">
                  <span>Timeout:</span>
                  <span>{agent.config.timeout}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Retry Attempts:</span>
                  <span>{agent.config.retryAttempts}</span>
                </div>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium md:text-base lg:text-lg">Performance Metrics</Label>
              <div className="mt-2 space-y-2 text-sm md:text-base lg:text-lg">
                <div className="flex justify-between">
                  <span>Tasks Completed:</span>
                  <span>{agent.metrics.tasksCompleted}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tasks In Progress:</span>
                  <span>{agent.metrics.tasksInProgress}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tasks Failed:</span>
                  <span>{agent.metrics.tasksFailed}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Execution Time:</span>
                  <span>{agent.metrics.averageExecutionTime}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Success Rate:</span>
                  <span>{(agent.metrics.successRate * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="tasks" className="space-y-4">
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {agent.taskQueue.map((task) => (
                  <Card key={task.id} className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm md:text-base lg:text-lg">{task.type}</span>
                      <div className="flex items-center gap-2">
                        <Badge className={taskPriorityColors[task.priority]}>
                          {task.priority}
                        </Badge>
                        <Badge variant="outline">
                          {task.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                      <div>Created: {task.createdAt.toLocaleString()}</div>
                      {task.startedAt && (
                        <div>Started: {task.startedAt.toLocaleString()}</div>
                      )}
                      {task.completedAt && (
                        <div>Completed: {task.completedAt.toLocaleString()}</div>
                      )}
                      {task.error && (
                        <div className="text-red-600 mt-1">Error: {task.error}</div>
                      )}
                    </div>
                  </Card>
                ))}
                {agent.taskQueue.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Clock className="h-6 w-6 mx-auto mb-2 opacity-50 " />
                    <p className="text-sm md:text-base lg:text-lg">No tasks in queue</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="health" className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              {getHealthIcon(agent.health)}
              <span className={`font-medium ${healthColors[agent.health.status]}`}>
                {agent.health.status.toUpperCase()}
              </span>
              <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Last check: {agent.health.lastCheck.toLocaleString()}
              </span>
            </div>
            {agent.health.issues.length > 0 && (
              <div>
                <Label className="text-sm font-medium md:text-base lg:text-lg">Issues</Label>
                <div className="mt-2 space-y-2">
                  {agent.health.issues.map((issue) => (
                    <Alert key={issue.id} variant={issue.severity === 'critical' ? 'destructive' : 'default'}>
                      <AlertCircle className="h-4 w-4 " />
                      <AlertDescription>
                        <div className="font-medium">{issue.type}</div>
                        <div className="text-sm md:text-base lg:text-lg">{issue.message}</div>
                        <div className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                          {issue.timestamp.toLocaleString()}
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </div>
            )}
            <div>
              <Label className="text-sm font-medium md:text-base lg:text-lg">Health Checks</Label>
              <div className="mt-2 space-y-2">
                {agent.health.checks.map((check, index) => (
                  <div key={index} className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span>{check.name}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant={check.status === 'pass' ? 'default' : 'destructive'}>
                        {check.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        {check.duration}ms
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
