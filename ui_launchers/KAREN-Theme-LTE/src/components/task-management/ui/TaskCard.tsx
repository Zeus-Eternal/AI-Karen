"use client";

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Task, TaskActionPayload } from '../types';
import { TaskStatusBadge } from './TaskStatusBadge';
import { TaskPriorityBadge } from './TaskStatusBadge';
import { TaskExecutionModeBadge } from './TaskStatusBadge';
import { TaskProgressBar, StepProgressIndicator, ResourceUsageIndicator } from './TaskProgressBar';
import { TaskActions } from './TaskActions';
import { QuickTaskActions } from './TaskActions';
import { cn } from '@/lib/utils';
import { formatRelativeTime, truncateText } from '@/lib/utils';

interface TaskCardProps {
  task: Task;
  onSelect?: (task: Task) => void;
  onAction?: (payload: TaskActionPayload) => void;
  showSteps?: boolean;
  compact?: boolean;
  className?: string;
}

export function TaskCard({
  task,
  onSelect,
  onAction,
  showSteps = false,
  compact = false,
  className,
}: TaskCardProps) {
  const {
    title,
    description,
    status,
    priority,
    executionMode,
    createdAt,
    updatedAt,
    startedAt,
    completedAt,
    steps,
    metadata,
    resourceUsage,
  } = task;

  const handleCardClick = () => {
    onSelect?.(task);
  };

  const handleAction = (payload: TaskActionPayload) => {
    onAction?.(payload);
  };

  if (compact) {
    return (
      <Card 
        className={cn(
          "cursor-pointer hover:shadow-md transition-shadow",
          className
        )}
        onClick={handleCardClick}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold truncate">{title}</h3>
                <TaskStatusBadge status={status} size="sm" />
              </div>
              
              {description && (
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {truncateText(description, 100)}
                </p>
              )}
              
              <div className="flex items-center gap-2 mb-2">
                <TaskPriorityBadge priority={priority} size="sm" />
                <TaskExecutionModeBadge executionMode={executionMode} size="sm" />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(updatedAt)}
                </span>
                <div className="flex items-center gap-2">
                  {steps && steps.length > 0 && (
                    <StepProgressIndicator steps={steps} />
                  )}
                  <QuickTaskActions task={task} onAction={handleAction} />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-md transition-shadow",
        className
      )}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold truncate">{title}</h3>
              <TaskStatusBadge status={status} size="sm" />
            </div>
            
            {description && (
              <p className="text-sm text-muted-foreground mb-2">
                {truncateText(description, 150)}
              </p>
            )}
            
            <div className="flex items-center gap-2 flex-wrap">
              <TaskPriorityBadge priority={priority} size="sm" />
              <TaskExecutionModeBadge executionMode={executionMode} size="sm" />
              
              {metadata?.agentUsed && (
                <div className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded-full dark:bg-gray-900/20 dark:text-gray-300">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {metadata.agentUsed}
                </div>
              )}
              
              {metadata?.category && (
                <div className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-purple-100 text-purple-800 rounded-full dark:bg-purple-900/20 dark:text-purple-300">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  {metadata.category}
                </div>
              )}
            </div>
          </div>
          
          <TaskActions task={task} onAction={handleAction} compact />
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Progress */}
        <div className="mb-4">
          <TaskProgressBar task={task} compact />
        </div>
        
        {/* Steps */}
        {showSteps && steps && steps.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Task Steps</span>
              <span className="text-xs text-muted-foreground">
                {steps.filter(s => s.status === 'completed').length}/{steps.length} completed
              </span>
            </div>
            <div className="space-y-2">
              {steps.slice(0, 3).map((step) => (
                <div key={step.id} className="flex items-center gap-2 text-sm">
                  <div 
                    className={cn(
                      "w-2 h-2 rounded-full flex-shrink-0",
                      step.status === 'completed' ? 'bg-green-500' :
                      step.status === 'running' ? 'bg-blue-500 animate-pulse' :
                      step.status === 'failed' ? 'bg-red-500' :
                      'bg-gray-300'
                    )}
                  />
                  <span className="truncate">{step.name}</span>
                  <TaskStatusBadge status={step.status} size="sm" showLabel={false} />
                </div>
              ))}
              {steps.length > 3 && (
                <div className="text-xs text-muted-foreground">
                  +{steps.length - 3} more steps...
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Resource Usage */}
        {resourceUsage && (
          <div className="mb-4">
            <ResourceUsageIndicator resourceUsage={resourceUsage} />
          </div>
        )}
        
        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span>Created {formatRelativeTime(createdAt)}</span>
            {startedAt && (
              <span>Started {formatRelativeTime(startedAt)}</span>
            )}
            {completedAt && (
              <span>Completed {formatRelativeTime(completedAt)}</span>
            )}
          </div>
          
          {startedAt && completedAt && (
            <span>
              Duration: {((completedAt.getTime() - startedAt.getTime()) / 1000).toFixed(1)}s
            </span>
          )}
        </div>
        
        {/* Error Message */}
        {task.error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
            <div className="flex items-start gap-2">
              <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{task.error}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Grid view task card
interface TaskGridCardProps {
  task: Task;
  onSelect?: (task: Task) => void;
  onAction?: (payload: TaskActionPayload) => void;
  className?: string;
}

export function TaskGridCard({
  task,
  onSelect,
  onAction,
  className,
}: TaskGridCardProps) {
  const handleCardClick = () => {
    onSelect?.(task);
  };

  const handleAction = (payload: TaskActionPayload) => {
    onAction?.(payload);
    // Prevent event bubbling to avoid triggering card click
    event?.stopPropagation();
  };

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-lg transition-all duration-200 h-full",
        className
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-4 flex flex-col h-full">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold truncate flex-1">{task.title}</h3>
          <TaskStatusBadge status={task.status} size="sm" />
        </div>
        
        {task.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-3 flex-1">
            {truncateText(task.description, 80)}
          </p>
        )}
        
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <TaskPriorityBadge priority={task.priority} size="sm" />
          <TaskExecutionModeBadge executionMode={task.executionMode} size="sm" />
        </div>
        
        <TaskProgressBar task={task} compact />
        
        <div className="mt-auto pt-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(task.updatedAt)}
            </span>
            <QuickTaskActions task={task} onAction={handleAction} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Kanban view task card
interface TaskKanbanCardProps {
  task: Task;
  onSelect?: (task: Task) => void;
  onAction?: (payload: TaskActionPayload) => void;
  className?: string;
}

export function TaskKanbanCard({
  task,
  onSelect,
  onAction,
  className,
}: TaskKanbanCardProps) {
  const handleCardClick = () => {
    onSelect?.(task);
  };

  const handleAction = (payload: TaskActionPayload) => {
    onAction?.(payload);
    // Prevent event bubbling to avoid triggering card click
    event?.stopPropagation();
  };

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-md transition-shadow mb-3",
        className
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-medium text-sm truncate flex-1">{task.title}</h3>
          <TaskStatusBadge status={task.status} size="sm" />
        </div>
        
        {task.description && (
          <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
            {truncateText(task.description, 60)}
          </p>
        )}
        
        <div className="flex items-center gap-2 mb-2">
          <TaskPriorityBadge priority={task.priority} size="sm" showLabel={false} />
          <TaskExecutionModeBadge executionMode={task.executionMode} size="sm" showLabel={false} />
        </div>
        
        <div className="flex items-center justify-between">
          <TaskProgressBar task={task} compact />
          <QuickTaskActions task={task} onAction={handleAction} />
        </div>
      </CardContent>
    </Card>
  );
}
