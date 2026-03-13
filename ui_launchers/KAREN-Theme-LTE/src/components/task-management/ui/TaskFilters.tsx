"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  type TaskFilters,
  type TaskSortOptions,
  TaskStatus,
  TaskPriority,
  ExecutionMode,
} from '../types';
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
const Filter = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
  </svg>
);

const SortAsc = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
  </svg>
);

const SortDesc = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l3-3m-3 3l-3-3" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const Calendar = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

interface TaskFiltersComponentProps {
  filters: TaskFilters;
  onFiltersChange: (filters: TaskFilters) => void;
  onClear: () => void;
  className?: string;
}

export function TaskFilters({
  filters,
  onFiltersChange,
  onClear,
  className,
}: TaskFiltersComponentProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: filters.dateRange?.start ? new Date(filters.dateRange.start).toISOString().split('T')[0] : '',
    end: filters.dateRange?.end ? new Date(filters.dateRange.end).toISOString().split('T')[0] : '',
  });

  // Status options
  const statusOptions: { value: TaskStatus; label: string }[] = [
    { value: 'pending', label: 'Pending' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' },
    { value: 'paused', label: 'Paused' },
  ];

  // Priority options
  const priorityOptions: { value: TaskPriority; label: string }[] = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'critical', label: 'Critical' },
  ];

  // Execution mode options
  const executionModeOptions: { value: ExecutionMode; label: string }[] = [
    { value: 'native', label: 'Native' },
    { value: 'langgraph', label: 'LangGraph' },
    { value: 'deepagents', label: 'DeepAgents' },
  ];

  const handleStatusChange = (status: TaskStatus) => {
    const currentStatuses = filters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status];
    
    onFiltersChange({ ...filters, status: newStatuses });
  };

  const handlePriorityChange = (priority: TaskPriority) => {
    const currentPriorities = filters.priority || [];
    const newPriorities = currentPriorities.includes(priority)
      ? currentPriorities.filter(p => p !== priority)
      : [...currentPriorities, priority];
    
    onFiltersChange({ ...filters, priority: newPriorities });
  };

  const handleExecutionModeChange = (executionMode: ExecutionMode) => {
    const currentModes = filters.executionMode || [];
    const newModes = currentModes.includes(executionMode)
      ? currentModes.filter(m => m !== executionMode)
      : [...currentModes, executionMode];
    
    onFiltersChange({ ...filters, executionMode: newModes });
  };

  const handleDateRangeChange = (nextDateRange: typeof dateRange) => {
    if (nextDateRange.start && nextDateRange.end) {
      onFiltersChange({
        ...filters,
        dateRange: {
          start: new Date(nextDateRange.start),
          end: new Date(nextDateRange.end),
        },
      });
    }
  };

  const clearDateRange = () => {
    setDateRange({ start: '', end: '' });
    onFiltersChange({ ...filters, dateRange: undefined });
  };

  const hasActiveFilters = () => {
    return (
      (filters.status && filters.status.length > 0) ||
      (filters.priority && filters.priority.length > 0) ||
      (filters.executionMode && filters.executionMode.length > 0) ||
      (filters.agent && filters.agent.length > 0) ||
      (filters.category && filters.category.length > 0) ||
      filters.dateRange ||
      filters.search
    );
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
            {hasActiveFilters() && (
              <span className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
                Active
              </span>
            )}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                getButtonVariant("outline")
              )}
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
            
            {hasActiveFilters() && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                  getButtonVariant("outline")
                )}
                onClick={onClear}
              >
                <X className="h-4 w-4 mr-1" />
                Clear All
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <Input
              placeholder="Search tasks..."
              value={filters.search || ''}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              className="max-w-md"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Status</label>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.status?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handleStatusChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Priority Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Priority</label>
            <div className="flex flex-wrap gap-2">
              {priorityOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.priority?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handlePriorityChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Execution Mode Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Execution Mode</label>
            <div className="flex flex-wrap gap-2">
              {executionModeOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.executionMode?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handleExecutionModeChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date Range Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Date Range</label>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  placeholder="Start date"
                  value={dateRange.start}
                  onChange={(e) => {
                    const nextDateRange = { ...dateRange, start: e.target.value };
                    setDateRange(nextDateRange);
                    handleDateRangeChange(nextDateRange);
                  }}
                  className="w-40"
                />
                <span className="text-muted-foreground">to</span>
                <Input
                  type="date"
                  placeholder="End date"
                  value={dateRange.end}
                  onChange={(e) => {
                    const nextDateRange = { ...dateRange, end: e.target.value };
                    setDateRange(nextDateRange);
                    handleDateRangeChange(nextDateRange);
                  }}
                  className="w-40"
                />
              </div>
              
              {(dateRange.start || dateRange.end) && (
                <button
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                    getButtonVariant("outline")
                  )}
                  onClick={clearDateRange}
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Sort options component
interface TaskSortOptionsProps {
  sortOptions: TaskSortOptions;
  onSortChange: (sort: TaskSortOptions) => void;
  className?: string;
}

export function TaskSortOptions({
  sortOptions,
  onSortChange,
  className,
}: TaskSortOptionsProps) {
  const sortFieldOptions: { value: TaskSortOptions['field']; label: string }[] = [
    { value: 'createdAt', label: 'Created Date' },
    { value: 'updatedAt', label: 'Updated Date' },
    { value: 'priority', label: 'Priority' },
    { value: 'progress', label: 'Progress' },
    { value: 'title', label: 'Title' },
  ];

  const handleFieldChange = (field: TaskSortOptions['field']) => {
    onSortChange({ ...sortOptions, field });
  };

  const handleDirectionToggle = () => {
    onSortChange({
      ...sortOptions,
      direction: sortOptions.direction === 'asc' ? 'desc' : 'asc',
    });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
            getButtonVariant("outline")
          )}>
            Sort by: {sortFieldOptions.find(o => o.value === sortOptions.field)?.label}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          {sortFieldOptions.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onClick={() => handleFieldChange(option.value)}
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-1",
          getButtonVariant("outline")
        )}
        onClick={handleDirectionToggle}
      >
        {sortOptions.direction === 'asc' ? (
          <SortAsc className="h-4 w-4" />
        ) : (
          <SortDesc className="h-4 w-4" />
        )}
        {sortOptions.direction === 'asc' ? 'Ascending' : 'Descending'}
      </button>
    </div>
  );
}

// Quick filter buttons
interface QuickFiltersProps {
  onFiltersChange: (filters: TaskFilters) => void;
  className?: string;
}

export function QuickFilters({ onFiltersChange, className }: QuickFiltersProps) {
  const quickFilters = [
    {
      name: 'Running Tasks',
      filters: { status: ['running'] },
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      name: 'Failed Tasks',
      filters: { status: ['failed'] },
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      name: 'High Priority',
      filters: { priority: ['high', 'critical'] },
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      ),
    },
    {
      name: 'Recent Tasks',
      filters: {
        dateRange: {
          start: new Date(Date.now() - 24 * 60 * 60 * 1000), // Last 24 hours
          end: new Date(),
        }
      },
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {quickFilters.map((filter) => (
        <button
          key={filter.name}
          className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
            getButtonVariant("outline")
          )}
          onClick={() => onFiltersChange(filter.filters as TaskFilters)}
        >
          {filter.icon}
          {filter.name}
        </button>
      ))}
    </div>
  );
}
