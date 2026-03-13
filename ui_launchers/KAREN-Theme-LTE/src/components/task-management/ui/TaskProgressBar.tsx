"use client";

import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Task, TaskStep } from '../types';
import { TaskStatusBadge } from './TaskStatusBadge';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils';

interface TaskProgressBarProps {
  task: Task;
  showSteps?: boolean;
  compact?: boolean;
  className?: string;
}

export function TaskProgressBar({
  task,
  showSteps = true,
  compact = false,
  className,
}: TaskProgressBarProps) {
  const { progress, steps, status } = task;
  
  // Determine progress variant based on status
  const getProgressVariant = () => {
    switch (status) {
      case 'completed':
        return 'success' as const;
      case 'failed':
        return 'destructive' as const;
      case 'running':
        return 'default' as const;
      default:
        return 'default' as const;
    }
  };

  // Calculate step progress
  const getStepProgress = (step: TaskStep) => {
    if (step.status === 'completed') return 100;
    if (step.status === 'running') return step.progress || 50;
    if (step.status === 'failed') return 100;
    return 0;
  };

  // Get step status color
  const getStepColor = (step: TaskStep) => {
    switch (step.status) {
      case 'completed':
        return 'bg-green-500';
      case 'running':
        return 'bg-blue-500';
      case 'failed':
        return 'bg-red-500';
      case 'paused':
        return 'bg-orange-500';
      default:
        return 'bg-gray-300';
    }
  };

  if (compact) {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Progress</span>
          <span className="text-sm text-muted-foreground">{progress}%</span>
        </div>
        <Progress 
          value={progress} 
          variant={getProgressVariant()}
          className="h-2"
        />
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Overall Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Overall Progress</span>
          <div className="flex items-center gap-2">
            <TaskStatusBadge status={status} size="sm" />
            <span className="text-sm text-muted-foreground">{progress}%</span>
          </div>
        </div>
        <Progress 
          value={progress} 
          variant={getProgressVariant()}
          className="h-3"
        />
      </div>

      {/* Steps Progress */}
      {showSteps && steps && steps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Steps ({steps.filter(s => s.status === 'completed').length}/{steps.length})</span>
            {task.startedAt && (
              <span className="text-xs text-muted-foreground">
                Started {formatRelativeTime(task.startedAt)}
              </span>
            )}
          </div>
          
          <div className="space-y-2">
            {steps.map((step, index) => (
              <div key={step.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {/* Step number */}
                      <div 
                        className={cn(
                          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                          getStepColor(step),
                          step.status === 'completed' ? 'text-white' : 'text-white'
                        )}
                      >
                        {index + 1}
                      </div>
                      
                      {/* Step name */}
                      <span className="text-sm font-medium">{step.name}</span>
                    </div>
                    
                    {/* Step status and progress */}
                    <div className="flex items-center gap-2">
                      <TaskStatusBadge status={step.status} size="sm" showLabel={false} />
                      <span className="text-xs text-muted-foreground">
                        {getStepProgress(step)}%
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Step progress bar */}
                <div className="ml-8">
                  <Progress 
                    value={getStepProgress(step)} 
                    variant={step.status === 'failed' ? 'destructive' : 'default'}
                    className="h-1"
                  />
                </div>
                
                {/* Step details */}
                {(step.description || step.error || step.duration) && (
                  <div className="ml-8 space-y-1">
                    {step.description && (
                      <p className="text-xs text-muted-foreground">{step.description}</p>
                    )}
                    
                    {step.error && (
                      <p className="text-xs text-destructive">{step.error}</p>
                    )}
                    
                    {step.duration && (
                      <p className="text-xs text-muted-foreground">
                        Duration: {(step.duration / 1000).toFixed(2)}s
                      </p>
                    )}
                    
                    {step.startTime && step.endTime && (
                      <p className="text-xs text-muted-foreground">
                        {new Date(step.startTime).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: true,
                          timeZone: 'UTC'
                        })} - {new Date(step.endTime).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: true,
                          timeZone: 'UTC'
                        })}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Task timing information */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          {task.createdAt && (
            <span>Created {formatRelativeTime(task.createdAt)}</span>
          )}
          
          {task.startedAt && (
            <span>Started {formatRelativeTime(task.startedAt)}</span>
          )}
          
          {task.completedAt && (
            <span>Completed {formatRelativeTime(task.completedAt)}</span>
          )}
        </div>
        
        {task.startedAt && task.completedAt && (
          <span>
            Duration: {((task.completedAt.getTime() - task.startedAt.getTime()) / 1000).toFixed(2)}s
          </span>
        )}
      </div>
    </div>
  );
}

// Compact step progress indicator
interface StepProgressIndicatorProps {
  steps: TaskStep[];
  className?: string;
}

export function StepProgressIndicator({ steps, className }: StepProgressIndicatorProps) {
  const completedSteps = steps.filter(step => step.status === 'completed').length;
  const totalSteps = steps.length;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1">
        <div className="flex items-center gap-1">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  step.status === 'completed' ? 'bg-green-500' :
                  step.status === 'running' ? 'bg-blue-500 animate-pulse' :
                  step.status === 'failed' ? 'bg-red-500' :
                  'bg-gray-300'
                )}
                title={`${step.name}: ${step.status}`}
              />
              {index < steps.length - 1 && (
                <div 
                  className={cn(
                    "flex-1 h-0.5",
                    step.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
      
      <span className="text-xs text-muted-foreground">
        {completedSteps}/{totalSteps}
      </span>
    </div>
  );
}

// Resource usage indicator
interface ResourceUsageIndicatorProps {
  resourceUsage?: {
    cpu: number;
    memory: number;
    tokens?: number;
  };
  className?: string;
}

export function ResourceUsageIndicator({ resourceUsage, className }: ResourceUsageIndicatorProps) {
  if (!resourceUsage) return null;

  const { cpu, memory, tokens } = resourceUsage;

  return (
    <div className={cn("flex items-center gap-4 text-xs", className)}>
      {cpu !== undefined && (
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>{cpu}%</span>
        </div>
      )}
      
      {memory !== undefined && (
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span>{(memory / 1024).toFixed(1)}GB</span>
        </div>
      )}
      
      {tokens !== undefined && (
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <span>{tokens.toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
