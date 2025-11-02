'use client';

import React, { useState } from 'react';
import { ModernSidebar } from '@/components/layout/ModernSidebar';
import { ModernHeader } from '@/components/layout/ModernHeader';
import { MetricCard } from '@/components/ui/metric-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { StatusIndicator } from '@/components/ui/status-indicator';
import {
  Zap,
  Play,
  Pause,
  Square,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Workflow,
} from 'lucide-react';
import { AnimatedNumber } from '@/components/ui/animated-number';

interface Agent {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'error' | 'idle';
  progress: number;
  currentTask: string;
  tasksCompleted: number;
  tasksTotal: number;
  startTime: Date;
  elapsedTime: number; // seconds
}

export default function AgentForgePage() {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: '1',
      name: 'Data Analysis Pipeline',
      status: 'running',
      progress: 65,
      currentTask: 'Processing dataset chunk 3/5',
      tasksCompleted: 13,
      tasksTotal: 20,
      startTime: new Date(Date.now() - 3600000),
      elapsedTime: 3600,
    },
    {
      id: '2',
      name: 'Code Review Bot',
      status: 'running',
      progress: 40,
      currentTask: 'Analyzing security vulnerabilities',
      tasksCompleted: 8,
      tasksTotal: 20,
      startTime: new Date(Date.now() - 1800000),
      elapsedTime: 1800,
    },
    {
      id: '3',
      name: 'Content Generator',
      status: 'paused',
      progress: 80,
      currentTask: 'Waiting for user input',
      tasksCompleted: 16,
      tasksTotal: 20,
      startTime: new Date(Date.now() - 7200000),
      elapsedTime: 7200,
    },
    {
      id: '4',
      name: 'Report Builder',
      status: 'completed',
      progress: 100,
      currentTask: 'Completed successfully',
      tasksCompleted: 20,
      tasksTotal: 20,
      startTime: new Date(Date.now() - 10800000),
      elapsedTime: 10800,
    },
  ]);

  const agentStats = {
    activeAgents: agents.filter((a) => a.status === 'running').length,
    completedToday: 47,
    queuedTasks: 12,
    avgCompletionTime: 2.3, // hours
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const statusColors = {
    running: 'success',
    paused: 'warning',
    completed: 'success',
    error: 'error',
    idle: 'offline',
  } as const;

  return (
    <div className="min-h-screen bg-background">
      <ModernSidebar />
      <ModernHeader />

      <main className="ml-64 mt-16 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">Agent Forge</h1>
                  <p className="text-muted-foreground">
                    Create and manage autonomous AI agents and workflows
                  </p>
                </div>
              </div>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Create Agent
              </Button>
            </div>
          </div>

          {/* Agent Statistics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Active Agents"
              value={<AnimatedNumber value={agentStats.activeAgents} />}
              subtitle="Currently running"
              icon={Zap}
              variant="success"
            />
            <MetricCard
              title="Completed Today"
              value={<AnimatedNumber value={agentStats.completedToday} />}
              subtitle="Finished workflows"
              icon={CheckCircle2}
              variant="primary"
              trend={{
                value: 15.3,
                isPositive: true,
              }}
            />
            <MetricCard
              title="Queued Tasks"
              value={<AnimatedNumber value={agentStats.queuedTasks} />}
              subtitle="Awaiting execution"
              icon={Clock}
              variant="warning"
            />
            <MetricCard
              title="Avg Completion"
              value={`${agentStats.avgCompletionTime}h`}
              subtitle="Average runtime"
              icon={TrendingUp}
              variant="default"
            />
          </div>

          {/* Agent Management Interface */}
          <Card>
            <CardHeader>
              <CardTitle>Active Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="running" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="running">
                    Running ({agentStats.activeAgents})
                  </TabsTrigger>
                  <TabsTrigger value="all">All Agents</TabsTrigger>
                  <TabsTrigger value="templates">Templates</TabsTrigger>
                  <TabsTrigger value="workflows">Workflows</TabsTrigger>
                </TabsList>

                {/* Running Agents Tab */}
                <TabsContent value="running" className="space-y-4">
                  <ScrollArea className="h-[600px]">
                    <div className="space-y-4">
                      {agents
                        .filter((agent) => agent.status === 'running' || agent.status === 'paused')
                        .map((agent) => (
                          <Card
                            key={agent.id}
                            className="transition-all hover:shadow-md"
                          >
                            <CardContent className="p-6">
                              <div className="space-y-4">
                                {/* Agent Header */}
                                <div className="flex items-start justify-between">
                                  <div className="space-y-1">
                                    <h3 className="text-lg font-semibold">
                                      {agent.name}
                                    </h3>
                                    <p className="text-sm text-muted-foreground">
                                      {agent.currentTask}
                                    </p>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <StatusIndicator
                                      status={statusColors[agent.status]}
                                      size="sm"
                                      pulse={agent.status === 'running'}
                                    />
                                    <div className="flex gap-1">
                                      {agent.status === 'running' ? (
                                        <Button size="icon" variant="outline">
                                          <Pause className="h-4 w-4" />
                                        </Button>
                                      ) : (
                                        <Button size="icon" variant="outline">
                                          <Play className="h-4 w-4" />
                                        </Button>
                                      )}
                                      <Button
                                        size="icon"
                                        variant="outline"
                                        className="text-destructive"
                                      >
                                        <Square className="h-4 w-4" />
                                      </Button>
                                    </div>
                                  </div>
                                </div>

                                {/* Progress */}
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between text-sm">
                                    <span className="text-muted-foreground">
                                      Progress
                                    </span>
                                    <span className="font-semibold">
                                      {agent.progress}%
                                    </span>
                                  </div>
                                  <Progress value={agent.progress} className="h-2" />
                                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                                    <span>
                                      {agent.tasksCompleted} / {agent.tasksTotal} tasks
                                    </span>
                                    <span>Elapsed: {formatTime(agent.elapsedTime)}</span>
                                  </div>
                                </div>

                                {/* Metadata */}
                                <div className="flex flex-wrap gap-2">
                                  <Badge variant="outline">
                                    Started {agent.startTime.toLocaleTimeString()}
                                  </Badge>
                                  <Badge variant="outline">
                                    ID: {agent.id}
                                  </Badge>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                    </div>
                  </ScrollArea>
                </TabsContent>

                {/* All Agents Tab */}
                <TabsContent value="all" className="space-y-4">
                  <ScrollArea className="h-[600px]">
                    <div className="space-y-4">
                      {agents.map((agent) => (
                        <Card
                          key={agent.id}
                          className="transition-all hover:shadow-md"
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4">
                                <div
                                  className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                                    agent.status === 'completed'
                                      ? 'bg-green-500/10'
                                      : agent.status === 'running'
                                      ? 'bg-blue-500/10'
                                      : agent.status === 'error'
                                      ? 'bg-red-500/10'
                                      : 'bg-gray-500/10'
                                  }`}
                                >
                                  {agent.status === 'completed' ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                  ) : agent.status === 'error' ? (
                                    <AlertCircle className="h-5 w-5 text-red-600" />
                                  ) : (
                                    <Zap className="h-5 w-5 text-blue-600" />
                                  )}
                                </div>
                                <div>
                                  <h4 className="font-semibold">{agent.name}</h4>
                                  <p className="text-sm text-muted-foreground">
                                    {agent.currentTask}
                                  </p>
                                </div>
                              </div>
                              <StatusIndicator
                                status={statusColors[agent.status]}
                                size="sm"
                              />
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>

                {/* Templates Tab */}
                <TabsContent value="templates" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <Card className="cursor-pointer transition-all hover:shadow-md">
                      <CardContent className="p-6">
                        <div className="space-y-3">
                          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500/10">
                            <Workflow className="h-6 w-6 text-blue-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold">Data Processing</h4>
                            <p className="text-sm text-muted-foreground">
                              Automated data analysis and transformation pipeline
                            </p>
                          </div>
                          <Button variant="outline" className="w-full">
                            Use Template
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="cursor-pointer transition-all hover:shadow-md">
                      <CardContent className="p-6">
                        <div className="space-y-3">
                          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10">
                            <CheckCircle2 className="h-6 w-6 text-green-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold">Code Review</h4>
                            <p className="text-sm text-muted-foreground">
                              Automated code quality and security analysis
                            </p>
                          </div>
                          <Button variant="outline" className="w-full">
                            Use Template
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="cursor-pointer transition-all hover:shadow-md">
                      <CardContent className="p-6">
                        <div className="space-y-3">
                          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-500/10">
                            <Zap className="h-6 w-6 text-purple-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold">Content Generation</h4>
                            <p className="text-sm text-muted-foreground">
                              Automated content creation and optimization
                            </p>
                          </div>
                          <Button variant="outline" className="w-full">
                            Use Template
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Workflows Tab */}
                <TabsContent value="workflows" className="space-y-4">
                  <Card className="flex items-center justify-center h-[400px]">
                    <div className="text-center text-muted-foreground">
                      <Workflow className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium">Visual Workflow Builder</p>
                      <p className="text-sm mt-2">
                        Drag-and-drop workflow creation coming soon
                      </p>
                      <p className="text-xs mt-1">
                        Will use React Flow for node-based workflow design
                      </p>
                    </div>
                  </Card>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
