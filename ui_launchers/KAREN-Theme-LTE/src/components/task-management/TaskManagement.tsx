"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Task,
  TaskFilters,
  TaskSortOptions,
  TaskActionPayload,
  TaskManagementProps,
} from './types';
import { useTaskStore, useTaskActions, useTaskLoading, useTaskError, useTaskFilters, useTaskSortOptions, useTaskViewMode } from './store/taskStore';
import { TaskCard, TaskGridCard, TaskKanbanCard } from './ui/TaskCard';
import { TaskFilters as TaskFiltersComponent, TaskSortOptions as TaskSortOptionsComponent, QuickFilters } from './ui/TaskFilters';
import { cn } from '@/lib/utils';

// Button variant helper function
const getButtonVariant = (variant: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link") => {
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    link: "text-primary underline-offset-4 hover:underline",
  };
  return variants[variant];
};

// Icon components
const Grid = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 00-2 2h2a2 2 0 002 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 00-2 2h2a2 2 0 002 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
  </svg>
);

const List = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const Columns = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2M9 7a2 2 0 00-2 2H5a2 2 0 00-2 2m0 10a2 2 0 002 2h2a2 2 0 002-2m0-10a2 2 0 002 2h2a2 2 0 002-2" />
  </svg>
);

const RefreshCw = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const Settings = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c-.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 00-1.066-2.573c.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

export function TaskManagement({
  className,
  onTaskSelect,
  onTaskAction,
  autoRefresh = false,
  refreshInterval = 30000, // 30 seconds
}: TaskManagementProps) {
  // Store hooks
  const tasks = useTaskStore((state) => state.tasks);
  const isLoading = useTaskLoading();
  const error = useTaskError();
  const filters = useTaskFilters();
  const sortOptions = useTaskSortOptions();
  const viewMode = useTaskViewMode();
  
  const {
    fetchTasks,
    setFilters,
    setSortOptions,
    setViewMode,
    clearError,
    enableRealTimeUpdates,
    disableRealTimeUpdates,
  } = useTaskActions();

  // Local state
  const [showFilters, setShowFilters] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Initialize data
  useEffect(() => {
    fetchTasks();
    
    if (autoRefresh) {
      enableRealTimeUpdates();
    }
    
    return () => {
      if (autoRefresh) {
        disableRealTimeUpdates();
      }
    };
  }, [fetchTasks, autoRefresh, enableRealTimeUpdates, disableRealTimeUpdates]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchTasks();
      setLastRefresh(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchTasks]);

  // Handle task selection
  const handleTaskSelect = useCallback((task: Task) => {
    onTaskSelect?.(task);
  }, [onTaskSelect]);

  // Handle task action
  const handleTaskAction = useCallback((payload: TaskActionPayload) => {
    onTaskAction?.(payload);
  }, [onTaskAction]);

  // Handle filters change
  const handleFiltersChange = useCallback((newFilters: TaskFilters) => {
    setFilters(newFilters);
  }, [setFilters]);

  // Handle sort change
  const handleSortChange = useCallback((newSort: TaskSortOptions) => {
    setSortOptions(newSort);
  }, [setSortOptions]);

  // Handle view mode change
  const handleViewModeChange = (mode: 'list' | 'grid' | 'kanban') => {
    setViewMode(mode);
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchTasks();
    setLastRefresh(new Date());
  };

  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({
      status: [],
      priority: [],
      executionMode: [],
      agent: [],
      category: [],
    });
  };

  // Render task based on view mode
  const renderTask = (task: Task) => {
    switch (viewMode) {
      case 'grid':
        return (
          <TaskGridCard
            key={task.id}
            task={task}
            onSelect={handleTaskSelect}
            onAction={handleTaskAction}
          />
        );
      case 'kanban':
        return (
          <TaskKanbanCard
            key={task.id}
            task={task}
            onSelect={handleTaskSelect}
            onAction={handleTaskAction}
          />
        );
      default:
        return (
          <TaskCard
            key={task.id}
            task={task}
            onSelect={handleTaskSelect}
            onAction={handleTaskAction}
            showSteps={viewMode === 'list'}
          />
        );
    }
  };

  // Group tasks by status for kanban view
  const renderKanbanView = () => {
    const statusGroups = {
      pending: tasks.filter(t => t.status === 'pending'),
      running: tasks.filter(t => t.status === 'running'),
      completed: tasks.filter(t => t.status === 'completed'),
      failed: tasks.filter(t => t.status === 'failed'),
      cancelled: tasks.filter(t => t.status === 'cancelled'),
      paused: tasks.filter(t => t.status === 'paused'),
    };

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {Object.entries(statusGroups).map(([status, statusTasks]) => (
          <div key={status} className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold capitalize">{status}</h3>
              <span className="text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
                {statusTasks.length}
              </span>
            </div>
            <Separator className="my-3" />
            <div className="space-y-3 min-h-[200px]">
              {statusTasks.map(renderTask)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render loading skeleton
  const renderSkeleton = () => {
    const skeletonCount = viewMode === 'grid' ? 6 : viewMode === 'kanban' ? 6 : 3;
    
    return Array.from({ length: skeletonCount }).map((_, index) => (
      <Card key={index} className={viewMode === 'grid' ? 'h-full' : ''}>
        <CardContent className="p-4">
          <div className="space-y-3">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-2 w-full" />
            <div className="flex justify-between">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-6" />
            </div>
          </div>
        </CardContent>
      </Card>
    ));
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              Task Management
              {autoRefresh && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <RefreshCw className="h-3 w-3" />
                  Auto-refresh
                </div>
              )}
              {lastRefresh && (
                <span className="text-xs text-muted-foreground">
                  Last: {lastRefresh.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true,
                    timeZone: 'UTC'
                  })}
                </span>
              )}
            </CardTitle>
            
            <div className="flex items-center gap-2">
              {/* View Mode Toggle */}
              <div className="flex items-center border rounded-md">
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors",
                    viewMode === 'list' ? "bg-background text-foreground" : "text-muted-foreground hover:text-foreground"
                  )}
                  onClick={() => handleViewModeChange('list')}
                  title="List view"
                >
                  <List className="h-4 w-4" />
                </button>
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors",
                    viewMode === 'grid' ? "bg-background text-foreground" : "text-muted-foreground hover:text-foreground"
                  )}
                  onClick={() => handleViewModeChange('grid')}
                  title="Grid view"
                >
                  <Grid className="h-4 w-4" />
                </button>
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors",
                    viewMode === 'kanban' ? "bg-background text-foreground" : "text-muted-foreground hover:text-foreground"
                  )}
                  onClick={() => handleViewModeChange('kanban')}
                  title="Kanban view"
                >
                  <Columns className="h-4 w-4" />
                </button>
              </div>
              
              {/* Settings */}
              <button
                className={cn(
                  "p-2 text-sm font-medium transition-colors text-muted-foreground hover:text-foreground",
                  showFilters ? "bg-background text-foreground" : ""
                )}
                onClick={() => setShowFilters(!showFilters)}
                title="Toggle filters"
              >
                <Settings className="h-4 w-4" />
              </button>
              
              {/* Refresh */}
              <button
                className="p-2 text-sm font-medium transition-colors text-muted-foreground hover:text-foreground"
                onClick={handleRefresh}
                disabled={isLoading}
                title="Refresh tasks"
              >
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Quick Filters */}
      <div className="flex items-center justify-between">
        <QuickFilters onFiltersChange={handleFiltersChange} />
        <div className="text-sm text-muted-foreground">
          {tasks.length} tasks found
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <TaskFiltersComponent
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClear={handleClearFilters}
        />
      )}

      {/* Sort Options */}
      <div className="flex items-center justify-between">
        <TaskSortOptionsComponent
          sortOptions={sortOptions}
          onSortChange={handleSortChange}
        />
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-destructive">Error loading tasks</h3>
                <p className="text-sm text-destructive/80 mt-1">{error}</p>
              </div>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                  getButtonVariant("outline")
                )}
                onClick={clearError}
              >
                Dismiss
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tasks */}
      {isLoading ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : viewMode === 'kanban' ? '' : 'space-y-4'}>
          {renderSkeleton()}
        </div>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="space-y-3">
              <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
                <Settings className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium">No tasks found</h3>
              <p className="text-muted-foreground">
                {hasActiveFilters(filters) 
                  ? "Try adjusting your filters or search terms"
                  : "Tasks will appear here once they are created"
                }
              </p>
              {hasActiveFilters(filters) && (
                <button
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                    getButtonVariant("outline")
                  )}
                  onClick={handleClearFilters}
                >
                  Clear Filters
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'kanban' ? (
        renderKanbanView()
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {tasks.map(renderTask)}
        </div>
      )}
    </div>
  );
}

// Helper function to check if filters are active
function hasActiveFilters(filters: TaskFilters): boolean {
  return !!(
    (filters.status && filters.status.length > 0) ||
    (filters.priority && filters.priority.length > 0) ||
    (filters.executionMode && filters.executionMode.length > 0) ||
    (filters.agent && filters.agent.length > 0) ||
    (filters.category && filters.category.length > 0) ||
    filters.dateRange ||
    filters.search
  );
}