"use client";

import React, { useCallback, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  Activity,
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  Database,
  Download,
  Edit3,
  FileText,
  Globe,
  Network,
  Pause,
  Play,
  Plus,
  Rocket,
  RotateCcw,
  Settings,
  Timer,
  Trash2,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { WorkflowAutomationAnalytics, WorkflowQueue, WorkflowTrigger } from '@/types/workflows';

const triggerTypeIcons: Record<string, LucideIcon> = {
  schedule: Calendar,
  event: Zap,
  webhook: Globe,
  file: FileText,
  condition: Settings,
  api: Network,
  database: Database,
  message: Users,
};

const priorityColors: Record<'low' | 'medium' | 'high' | 'critical', string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const priorityOrder: Record<'low' | 'medium' | 'high' | 'critical', number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

const queueStatusColors: Record<'active' | 'paused' | 'draining', string> = {
  active: 'bg-green-100 text-green-700 border-green-200',
  paused: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  draining: 'bg-orange-100 text-orange-700 border-orange-200',
};

type BulkAction = 'enable' | 'disable' | 'run' | 'delete';

export interface WorkflowSchedulerProps {
  triggers: WorkflowTrigger[];
  queues: WorkflowQueue[];
  analytics: WorkflowAutomationAnalytics;
  onCreateTrigger?: (trigger: Omit<WorkflowTrigger, 'id'>) => Promise<void>;
  onUpdateTrigger?: (triggerId: string, updates: Partial<WorkflowTrigger>) => Promise<void>;
  onDeleteTrigger?: (triggerId: string) => Promise<void>;
  onToggleTrigger?: (triggerId: string, enabled: boolean) => Promise<void>;
  onRunTrigger?: (triggerId: string) => Promise<void>;
  onPauseQueue?: (queueId: string) => Promise<void>;
  onResumeQueue?: (queueId: string) => Promise<void>;
  onExportData?: (type: 'triggers' | 'queues' | 'analytics') => Promise<void>;
  className?: string;
}

function getPriorityRank(priority?: WorkflowTrigger['priority']) {
  return priorityOrder[priority ?? 'medium'];
}

function formatPercent(value: number) {
  if (!Number.isFinite(value)) {
    return '0.0%';
  }
  const normalized = value > 1 ? value : value * 100;
  return `${normalized.toFixed(1)}%`;
}

export function WorkflowScheduler({
  triggers,
  queues,
  analytics,
  onCreateTrigger,
  onUpdateTrigger,
  onDeleteTrigger,
  onToggleTrigger,
  onRunTrigger,
  onPauseQueue,
  onResumeQueue,
  onExportData,
  className = '',
}: WorkflowSchedulerProps) {
  const [selectedTab, setSelectedTab] = useState('triggers');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'type' | 'priority' | 'lastTriggered'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedTriggers, setSelectedTriggers] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const schedulerStats = useMemo(() => {
    const activeTriggers = triggers.filter((trigger) => trigger.enabled).length;
    const totalQueued = queues.reduce((sum, queue) => sum + queue.tasks.length, 0);
    const totalProcessing = queues.reduce((sum, queue) => sum + queue.currentLoad, 0);
    const totalExecutions = triggers.reduce((sum, trigger) => sum + (trigger.executionCount ?? 0), 0);
    const successRate = totalExecutions > 0
      ? triggers.reduce((sum, trigger) => sum + (trigger.successCount ?? 0), 0) / totalExecutions
      : 0;

    return {
      totalTriggers: triggers.length,
      activeTriggers,
      inactiveTriggers: triggers.length - activeTriggers,
      totalQueues: queues.length,
      totalQueued,
      totalProcessing,
      totalExecutions,
      successRate,
      avgExecutionTime: analytics.averageExecutionTime,
      resourceUtilization: analytics.resourceUtilization,
      costPerExecution: analytics.costAnalysis.costPerExecution,
    };
  }, [analytics, queues, triggers]);

  const availableTriggerTypes = useMemo(
    () => Array.from(new Set(triggers.map((trigger) => trigger.type))).sort(),
    [triggers],
  );

  const filteredTriggers = useMemo(() => {
    return triggers
      .filter((trigger) => {
        const matchesSearch = trigger.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus =
          filterStatus === 'all' || (filterStatus === 'active' ? trigger.enabled : !trigger.enabled);
        const matchesType = filterType === 'all' || trigger.type === filterType;
        return matchesSearch && matchesStatus && matchesType;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'name':
            return sortOrder === 'asc'
              ? a.name.localeCompare(b.name)
              : b.name.localeCompare(a.name);
          case 'type':
            return sortOrder === 'asc'
              ? a.type.localeCompare(b.type)
              : b.type.localeCompare(a.type);
          case 'priority': {
            const aRank = getPriorityRank(a.priority);
            const bRank = getPriorityRank(b.priority);
            return sortOrder === 'asc' ? aRank - bRank : bRank - aRank;
          }
          case 'lastTriggered': {
            const aTime = a.lastTriggered?.getTime() ?? 0;
            const bTime = b.lastTriggered?.getTime() ?? 0;
            return sortOrder === 'asc' ? aTime - bTime : bTime - aTime;
          }
          default:
            return 0;
        }
      });
  }, [filterStatus, filterType, searchTerm, sortBy, sortOrder, triggers]);

  const toggleTriggerSelection = useCallback((triggerId: string) => {
    setSelectedTriggers((current) => {
      const next = new Set(current);
      if (next.has(triggerId)) {
        next.delete(triggerId);
      } else {
        next.add(triggerId);
      }
      return next;
    });
  }, []);

  const selectAllTriggers = useCallback(() => {
    setSelectedTriggers((current) => {
      if (current.size === filteredTriggers.length) {
        return new Set();
      }
      return new Set(filteredTriggers.map((trigger) => trigger.id));
    });
  }, [filteredTriggers]);

  const clearSelection = useCallback(() => setSelectedTriggers(new Set()), []);

  const handleBulkAction = useCallback(async (action: BulkAction) => {
    if (selectedTriggers.size === 0) {
      toast({
        variant: 'destructive',
        title: 'No triggers selected',
        description: 'Select at least one trigger to perform bulk actions.',
      });
      return;
    }

    const ids = Array.from(selectedTriggers);

    try {
      switch (action) {
        case 'enable':
          await Promise.all(ids.map((id) => onToggleTrigger?.(id, true)));
          toast({ title: 'Triggers enabled', description: `${ids.length} trigger(s) are now active.` });
          break;
        case 'disable':
          await Promise.all(ids.map((id) => onToggleTrigger?.(id, false)));
          toast({ title: 'Triggers disabled', description: `${ids.length} trigger(s) are now inactive.` });
          break;
        case 'run':
          await Promise.all(ids.map((id) => onRunTrigger?.(id)));
          toast({ title: 'Triggers executed', description: `${ids.length} trigger(s) executed.` });
          break;
        case 'delete':
          if (confirm(`Delete ${ids.length} trigger(s)? This action cannot be undone.`)) {
            await Promise.all(ids.map((id) => onDeleteTrigger?.(id)));
            toast({ title: 'Triggers deleted', description: `${ids.length} trigger(s) removed.` });
          } else {
            return;
          }
          break;
      }
    } catch (error) {
      console.error('Bulk trigger action failed', error);
      toast({
        variant: 'destructive',
        title: 'Bulk action failed',
        description: 'An error occurred while executing the selected action.',
      });
    } finally {
      clearSelection();
    }
  }, [clearSelection, onDeleteTrigger, onRunTrigger, onToggleTrigger, selectedTriggers, toast]);

  const handleCreateTrigger = useCallback(async () => {
    if (!onCreateTrigger) {
      toast({
        title: 'Creation unavailable',
        description: 'Provide an onCreateTrigger handler to enable trigger creation.',
        variant: 'destructive',
      });
      return;
    }

    const workflowId = triggers[0]?.workflowId;
    if (!workflowId) {
      toast({
        title: 'Workflow required',
        description: 'At least one existing trigger must define a workflowId to clone defaults from.',
        variant: 'destructive',
      });
      return;
    }

    const now = new Date();
    const defaultTrigger: Omit<WorkflowTrigger, 'id'> = {
      name: `New Trigger ${now.toLocaleTimeString()}`,
      type: 'schedule',
      config: {
        schedule: {
          expression: '0 * * * *',
          timezone: 'UTC',
          enabled: true,
          nextRun: undefined,
          lastRun: undefined,
        },
      },
      enabled: true,
      workflowId,
      lastTriggered: undefined,
      nextTrigger: undefined,
      priority: 'medium',
      executionCount: 0,
      successCount: 0,
      failureCount: 0,
    };

    try {
      await onCreateTrigger(defaultTrigger);
      toast({ title: 'Trigger created', description: `${defaultTrigger.name} has been created.` });
    } catch (error) {
      console.error('Failed to create trigger', error);
      toast({
        variant: 'destructive',
        title: 'Create trigger failed',
        description: 'Verify backend connectivity and try again.',
      });
    }
  }, [onCreateTrigger, toast, triggers]);

  const handleNewQueueClick = useCallback(() => {
    toast({
      title: 'Queue creation managed externally',
      description: 'Use backend tooling to provision queues, then refresh this view.',
    });
  }, [toast]);

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Rocket className="h-6 w-6" />
            Workflow Scheduler
          </h2>
          <p className="text-muted-foreground">
            Coordinate triggers, queues, and optimization insights for production workflows.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex gap-2">
            <Button
              onClick={() => onExportData?.('analytics')}
              variant="outline"
              size="sm"
              disabled={!onExportData}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
            <Button onClick={clearSelection} variant="outline" size="sm">
              <RotateCcw className="h-4 w-4 mr-2" />
              Deselect All
            </Button>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreateTrigger} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              New Trigger
            </Button>
            <Button onClick={handleNewQueueClick}>
              <Plus className="h-4 w-4 mr-2" />
              New Queue
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Active Triggers"
          value={schedulerStats.activeTriggers}
          total={schedulerStats.totalTriggers}
          trend="up"
          icon={<Timer className="h-8 w-8 text-blue-600" />}
        />
        <StatsCard
          title="Queued Tasks"
          value={schedulerStats.totalQueued}
          total={schedulerStats.totalProcessing}
          trend="stable"
          icon={<Activity className="h-8 w-8 text-orange-600" />}
        />
        <StatsCard
          title="Success Rate"
          value={formatPercent(schedulerStats.successRate)}
          trend="up"
          icon={<TrendingUp className="h-8 w-8 text-green-600" />}
        />
        <StatsCard
          title="Avg Duration"
          value={
            schedulerStats.avgExecutionTime < 1000
              ? `${schedulerStats.avgExecutionTime}ms`
              : `${(schedulerStats.avgExecutionTime / 1000).toFixed(1)}s`
          }
          trend="down"
          icon={<Clock className="h-8 w-8 text-purple-600" />}
        />
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full lg:w-auto grid-cols-4">
          <TabsTrigger value="triggers">Triggers</TabsTrigger>
          <TabsTrigger value="queues">Queues</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="triggers" className="space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4">
            <Input
              placeholder="Search triggers"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              className="lg:w-1/2"
            />
            <Select value={filterStatus} onValueChange={(value) => setFilterStatus(value as 'all' | 'active' | 'inactive')}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {availableTriggerTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={(value) => setSortBy(value as typeof sortBy)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="type">Type</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
                <SelectItem value="lastTriggered">Last Triggered</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={selectAllTriggers}>
              Toggle Selection
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleBulkAction('enable')} disabled={!onToggleTrigger}>
              Enable
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleBulkAction('disable')} disabled={!onToggleTrigger}>
              Disable
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleBulkAction('run')} disabled={!onRunTrigger}>
              Run
            </Button>
            <Button variant="destructive" size="sm" onClick={() => handleBulkAction('delete')} disabled={!onDeleteTrigger}>
              Delete
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredTriggers.map((trigger) => (
              <EnhancedTriggerCard
                key={trigger.id}
                trigger={trigger}
                selected={selectedTriggers.has(trigger.id)}
                onSelect={() => toggleTriggerSelection(trigger.id)}
                onEdit={onUpdateTrigger}
                onDelete={onDeleteTrigger}
                onToggle={onToggleTrigger}
                onRun={onRunTrigger}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="queues" className="space-y-4">
          {queues.length > 0 ? (
            queues.map((queue) => (
              <QueueCard
                key={queue.id}
                queue={queue}
                onPauseQueue={onPauseQueue}
                onResumeQueue={onResumeQueue}
              />
            ))
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No queues available. Create one from your backend configuration.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="analytics">
          <AnalyticsOverview analytics={analytics} />
        </TabsContent>

        <TabsContent value="optimization">
          <OptimizationPanel analytics={analytics} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string | number;
  total?: number;
  trend?: 'up' | 'down' | 'stable';
  icon: React.ReactNode;
}

function StatsCard({ title, value, total, trend, icon }: StatsCardProps) {
  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {typeof total === 'number' && (
              <p className="text-xs text-muted-foreground">Total: {total}</p>
            )}
            {trend && (
              <p className="text-xs text-muted-foreground">Trend: {trend}</p>
            )}
          </div>
          {icon}
        </div>
      </CardContent>
    </Card>
  );
}

interface EnhancedTriggerCardProps {
  trigger: WorkflowTrigger;
  selected: boolean;
  onSelect: () => void;
  onEdit?: (triggerId: string, updates: Partial<WorkflowTrigger>) => Promise<void> | void;
  onDelete?: (triggerId: string) => Promise<void> | void;
  onToggle?: (triggerId: string, enabled: boolean) => Promise<void> | void;
  onRun?: (triggerId: string) => Promise<void> | void;
}

function EnhancedTriggerCard({ trigger, selected, onSelect, onEdit, onDelete, onToggle, onRun }: EnhancedTriggerCardProps) {
  const [isBusy, setIsBusy] = React.useState(false);
  const Icon = triggerTypeIcons[trigger.type] ?? Settings;
  const priority = trigger.priority ?? 'medium';
  const lastTriggered = trigger.lastTriggered?.toLocaleString() ?? 'Never';
  const nextTrigger = trigger.nextTrigger?.toLocaleString() ?? 'Pending';

  const handleToggle = async () => {
    if (!onToggle) return;
    setIsBusy(true);
    try {
      await onToggle(trigger.id, !trigger.enabled);
    } finally {
      setIsBusy(false);
    }
  };

  const handleRun = async () => {
    if (!onRun) return;
    setIsBusy(true);
    try {
      await onRun(trigger.id);
    } finally {
      setIsBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete) return;
    setIsBusy(true);
    try {
      await onDelete(trigger.id);
    } finally {
      setIsBusy(false);
    }
  };

  const handleEdit = async () => {
    if (!onEdit) return;
    setIsBusy(true);
    try {
      await onEdit(trigger.id, {});
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <Card
      className={`transition-all ${selected ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
      onClick={onSelect}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <div>
            <CardTitle className="text-base sm:text-lg">{trigger.name}</CardTitle>
            <div className="flex gap-2 mt-1">
              <Badge className={trigger.enabled ? 'bg-green-100 text-green-700 border-green-200' : 'bg-gray-100 text-gray-700 border-gray-200'}>
                {trigger.enabled ? 'Active' : 'Inactive'}
              </Badge>
              <Badge className={priorityColors[priority]}>Priority: {priority}</Badge>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); handleToggle(); }} disabled={isBusy || !onToggle}>
            {trigger.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); handleRun(); }} disabled={isBusy || !onRun}>
            <Play className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); handleEdit(); }} disabled={isBusy || !onEdit}>
            <Edit3 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); handleDelete(); }} disabled={isBusy || !onDelete}>
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="font-medium text-foreground">Last Triggered</p>
            <p>{lastTriggered}</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Next Trigger</p>
            <p>{nextTrigger}</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Executions</p>
            <p>{trigger.executionCount ?? 0}</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Success Rate</p>
            <p>{formatPercent(trigger.successCount && trigger.executionCount ? trigger.successCount / trigger.executionCount : 0)}</p>
          </div>
        </div>
        {trigger.config.schedule && (
          <div>
            <p className="font-medium text-foreground">Cron Expression</p>
            <p>{trigger.config.schedule.expression}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface QueueCardProps {
  queue: WorkflowQueue;
  onPauseQueue?: (queueId: string) => Promise<void> | void;
  onResumeQueue?: (queueId: string) => Promise<void> | void;
}

function QueueCard({ queue, onPauseQueue, onResumeQueue }: QueueCardProps) {
  const [isBusy, setIsBusy] = React.useState(false);
  const status = queue.status ?? 'active';
  const queuePriority = queue.queuePriority ?? 'medium';

  const handlePause = async () => {
    if (!onPauseQueue) return;
    setIsBusy(true);
    try {
      await onPauseQueue(queue.id);
    } finally {
      setIsBusy(false);
    }
  };

  const handleResume = async () => {
    if (!onResumeQueue) return;
    setIsBusy(true);
    try {
      await onResumeQueue(queue.id);
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <Card className="border">
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="text-lg">{queue.name}</CardTitle>
          <div className="flex gap-2 mt-2">
            <Badge className={queueStatusColors[status]}>Status: {status}</Badge>
            <Badge className={priorityColors[queuePriority]}>Priority: {queuePriority}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handlePause} disabled={isBusy || !onPauseQueue}>
            Pause
          </Button>
          <Button variant="outline" size="sm" onClick={handleResume} disabled={isBusy || !onResumeQueue}>
            Resume
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="font-medium text-foreground">Queued</p>
            <p>{queue.tasks.length}</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Current Load</p>
            <p>{queue.currentLoad} / {queue.maxConcurrency}</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Throughput</p>
            <p>{queue.metrics.throughput.toFixed(2)} ops/min</p>
          </div>
          <div>
            <p className="font-medium text-foreground">Error Rate</p>
            <p>{formatPercent(queue.metrics.errorRate)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AnalyticsOverview({ analytics }: { analytics: WorkflowAutomationAnalytics }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Execution Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div className="flex justify-between">
            <span>Success Rate</span>
            <span className="font-medium text-foreground">{formatPercent(analytics.successRate)}</span>
          </div>
          <div className="flex justify-between">
            <span>Failure Rate</span>
            <span className="font-medium text-foreground">{formatPercent(analytics.failureRate)}</span>
          </div>
          <div className="flex justify-between">
            <span>Average Execution Time</span>
            <span className="font-medium text-foreground">{analytics.averageExecutionTime}ms</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resource Utilization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div className="flex justify-between">
            <span>CPU</span>
            <span className="font-medium text-foreground">{formatPercent(analytics.resourceUtilization.cpu)}</span>
          </div>
          <div className="flex justify-between">
            <span>Memory</span>
            <span className="font-medium text-foreground">{formatPercent(analytics.resourceUtilization.memory)}</span>
          </div>
          {typeof analytics.resourceUtilization.gpu === 'number' && (
            <div className="flex justify-between">
              <span>GPU</span>
              <span className="font-medium text-foreground">{formatPercent(analytics.resourceUtilization.gpu)}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Cost per Execution</span>
            <span className="font-medium text-foreground">${analytics.costAnalysis.costPerExecution.toFixed(2)}</span>
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Cost Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {Object.entries(analytics.costAnalysis.costBreakdown).map(([label, value]) => (
            <div key={label} className="flex justify-between">
              <span className="capitalize">{label}</span>
              <span className="font-medium text-foreground">${value.toFixed(2)}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function OptimizationPanel({ analytics }: { analytics: WorkflowAutomationAnalytics }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Bottlenecks</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          {analytics.bottlenecks.map((bottleneck) => (
            <div key={bottleneck.nodeId} className="border rounded p-3">
              <p className="font-medium text-foreground">{bottleneck.nodeName}</p>
              <p>Average Time: {bottleneck.averageExecutionTime}ms</p>
              <p>Impact: {bottleneck.impact}</p>
              <p>Suggestions: {bottleneck.suggestions.join(', ')}</p>
            </div>
          ))}
          {analytics.bottlenecks.length === 0 && <p>No bottlenecks detected.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Optimization Suggestions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          {analytics.optimizationSuggestions.map((suggestion) => (
            <div key={suggestion.id} className="border rounded p-3">
              <p className="font-medium text-foreground">{suggestion.title}</p>
              <p>Type: {suggestion.type} • Priority: {suggestion.priority}</p>
              <p className="mt-1">{suggestion.description}</p>
              <p className="mt-1 text-foreground">Impact: {suggestion.estimatedImpact}</p>
            </div>
          ))}
          {analytics.optimizationSuggestions.length === 0 && <p>No optimization suggestions available.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
