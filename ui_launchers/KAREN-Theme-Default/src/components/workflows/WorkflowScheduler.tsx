"use client";

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from '@/lib/karen-backend';
import { handleApiError } from '@/lib/error-handler';
import { Calendar, Zap, Globe, FileText, Settings, Play, Pause, RotateCcw, Trash2, Edit3 } from 'lucide-react';

interface WorkflowSchedulerProps {
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

const triggerTypeIcons = {
  schedule: Calendar,
  event: Zap,
  webhook: Globe,
  file: FileText,
  condition: Settings,
  api: Network,
  database: Database,
  message: Users,
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

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
  const backend = getKarenBackend();

  // Stats Computation for triggers and queues
  const schedulerStats = useMemo(() => {
    const activeTriggers = triggers.filter(t => t.enabled).length;
    const totalQueued = queues.reduce((sum, queue) => sum + queue.tasks.length, 0);
    const totalProcessing = queues.reduce((sum, queue) => sum + queue.currentLoad, 0);
    const totalExecutions = triggers.reduce((sum, trigger) => sum + trigger.executionCount, 0);
    const successRate = totalExecutions > 0 
      ? triggers.reduce((sum, trigger) => sum + trigger.successCount, 0) / totalExecutions 
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
  }, [triggers, queues, analytics]);

  // Filtering and sorting the triggers
  const filteredTriggers = useMemo(() => {
    return triggers
      .filter(trigger => {
        const matchesSearch = trigger.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || 
                            (filterStatus === 'active' && trigger.enabled) ||
                            (filterStatus === 'inactive' && !trigger.enabled);
        const matchesType = filterType === 'all' || trigger.type === filterType;
        return matchesSearch && matchesStatus && matchesType;
      })
      .sort((a, b) => {
        let aValue: any, bValue: any;
        
        switch (sortBy) {
          case 'name':
            aValue = a.name;
            bValue = b.name;
            break;
          case 'type':
            aValue = a.type;
            bValue = b.type;
            break;
          case 'priority':
            const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
            aValue = priorityOrder[a.priority];
            bValue = priorityOrder[b.priority];
            break;
          case 'lastTriggered':
            aValue = a.lastTriggered?.getTime() || 0;
            bValue = b.lastTriggered?.getTime() || 0;
            break;
          default:
            return 0;
        }

        if (sortOrder === 'asc') {
          return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
          return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
      });
  }, [triggers, searchTerm, filterStatus, filterType, sortBy, sortOrder]);

  // Handling bulk actions
  const handleBulkAction = async (action: string) => {
    if (selectedTriggers.size === 0) {
      toast({
        variant: 'destructive',
        title: 'No triggers selected',
        description: 'Please select triggers to perform bulk actions.',
      });
      return;
    }

    try {
      switch (action) {
        case 'enable':
          await Promise.all(
            Array.from(selectedTriggers).map(triggerId => onToggleTrigger?.(triggerId, true))
          );
          toast({
            title: 'Triggers Enabled',
            description: `${selectedTriggers.size} triggers have been enabled.`,
          });
          break;
        case 'disable':
          await Promise.all(
            Array.from(selectedTriggers).map(triggerId => onToggleTrigger?.(triggerId, false))
          );
          toast({
            title: 'Triggers Disabled',
            description: `${selectedTriggers.size} triggers have been disabled.`,
          });
          break;
        case 'run':
          await Promise.all(
            Array.from(selectedTriggers).map(triggerId => onRunTrigger?.(triggerId))
          );
          toast({
            title: 'Triggers Executed',
            description: `${selectedTriggers.size} triggers have been executed.`,
          });
          break;
        case 'delete':
          if (confirm(`Are you sure you want to delete ${selectedTriggers.size} triggers?`)) {
            await Promise.all(
              Array.from(selectedTriggers).map(triggerId => onDeleteTrigger?.(triggerId))
            );
            toast({
              title: 'Triggers Deleted',
              description: `${selectedTriggers.size} triggers have been deleted.`,
            });
          }
          break;
        default:
          toast({
            variant: 'destructive',
            title: 'Unknown Action',
            description: 'The selected action is unknown.',
          });
      }
      
      setSelectedTriggers(new Set());
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'An error occurred while performing the bulk action.',
      });
    }
  };

  const toggleTriggerSelection = (triggerId: string) => {
    const newSelection = new Set(selectedTriggers);
    if (newSelection.has(triggerId)) {
      newSelection.delete(triggerId);
    } else {
      newSelection.add(triggerId);
    }
    setSelectedTriggers(newSelection);
  };

  const selectAllTriggers = () => {
    if (selectedTriggers.size === filteredTriggers.length) {
      setSelectedTriggers(new Set());
    } else {
      setSelectedTriggers(new Set(filteredTriggers.map(t => t.id)));
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Rocket className="h-6 w-6" />
            Workflow Scheduler
          </h2>
          <p className="text-muted-foreground">
            Advanced workflow automation with real-time monitoring and optimization
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex gap-2">
            <Button
              onClick={() => onExportData?.('analytics')}
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
            <Button
              onClick={() => setSelectedTriggers(new Set())}
              variant="outline"
              size="sm"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Deselect All
            </Button>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowCreateTrigger(true)}
              variant="outline"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Trigger
            </Button>
            <Button
              onClick={() => setShowCreateQueue(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              New Queue
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
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
          value={(schedulerStats.successRate * 100).toFixed(1) + '%'}
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

      {/* Trigger Management */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full lg:w-auto grid-cols-4">
          <TabsTrigger value="triggers">Triggers</TabsTrigger>
          <TabsTrigger value="queues">Queues</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="triggers" className="space-y-4">
          {/* Filter/Search Bar */}
          <div className="flex items-center gap-4">
            <Input
              placeholder="Search triggers"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-1/2"
            />
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {Object.keys(triggerTypeIcons).map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Sort by Name</SelectItem>
                <SelectItem value="type">Sort by Type</SelectItem>
                <SelectItem value="priority">Sort by Priority</SelectItem>
                <SelectItem value="lastTriggered">Sort by Last Run</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>

          {/* Trigger Grid */}
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

        {/* Queues Tab */}
        <TabsContent value="queues" className="space-y-4">
          {/* Queue Cards */}
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          {/* Analytics Display */}
        </TabsContent>

        {/* Optimization Tab */}
        <TabsContent value="optimization" className="space-y-4">
          {/* Optimization Suggestions */}
        </TabsContent>
      </Tabs>
    </div>
  );
}
