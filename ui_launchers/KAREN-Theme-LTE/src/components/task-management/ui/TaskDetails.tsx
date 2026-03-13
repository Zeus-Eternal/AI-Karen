"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  TaskActionPayload,
  TaskDetailsProps,
} from '../types';
import { TaskStatusBadge } from './TaskStatusBadge';
import { TaskPriorityBadge } from './TaskStatusBadge';
import { TaskExecutionModeBadge } from './TaskStatusBadge';
import { TaskProgressBar } from './TaskProgressBar';
import { TaskActions } from './TaskActions';
import { cn } from '@/lib/utils';
import { formatRelativeTime, formatDate } from '@/lib/utils';

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
const ArrowLeft = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
  </svg>
);

const Copy = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2zm-2-4h.01M16 12h.01" />
  </svg>
);

const Clock = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Cpu = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H9a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const Memory = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
  </svg>
);

const MessageSquare = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.003 9.003 0 00-8.354-5.834L3.416 18.166A9.003 9.003 0 003 21c4.418 0 8-3.582 8-9z" />
  </svg>
);

type TaskDetailsTab = 'overview' | 'steps' | 'logs' | 'metadata';

const taskDetailsTabs: Array<{ id: TaskDetailsTab; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'steps', label: 'Steps' },
  { id: 'logs', label: 'Logs' },
  { id: 'metadata', label: 'Metadata' },
];

export function TaskDetails({
  task,
  onClose,
  onAction,
  showActions = true,
  className,
}: TaskDetailsProps) {
  const [activeTab, setActiveTab] = useState<TaskDetailsTab>('overview');

  const {
    id,
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
    error,
    result,
  } = task;

  const handleAction = (payload: TaskActionPayload) => {
    onAction?.(payload);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatDuration = (start: Date, end: Date) => {
    const duration = end.getTime() - start.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CardTitle className="text-xl">{title}</CardTitle>
              <TaskStatusBadge status={status} />
              <TaskPriorityBadge priority={priority} />
              <TaskExecutionModeBadge executionMode={executionMode} />
            </div>
            
            <div className="flex items-center gap-2">
              {onClose && (
                <button
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                    getButtonVariant("outline")
                  )}
                  onClick={onClose}
                >
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  Back
                </button>
              )}
              
              {showActions && (
                <TaskActions task={task} onAction={handleAction} />
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Card>
        <CardContent className="p-0">
          <div className="border-b">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                ...taskDetailsTabs,
              ].map((tab) => (
                <button
                  key={tab.id}
                  className={cn(
                    "py-4 px-1 border-b-2 text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  )}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Description */}
                {description && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">Description</h3>
                    <p className="text-muted-foreground">{description}</p>
                  </div>
                )}
                
                {/* Progress */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Progress</h3>
                  <TaskProgressBar task={task} showSteps />
                </div>
                
                {/* Timing Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Timing</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">Created:</span>
                      </div>
                      <p className="text-sm text-muted-foreground ml-6">
                        {formatDate(createdAt)} ({formatRelativeTime(createdAt)})
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">Updated:</span>
                      </div>
                      <p className="text-sm text-muted-foreground ml-6">
                        {formatDate(updatedAt)} ({formatRelativeTime(updatedAt)})
                      </p>
                    </div>
                    
                    {startedAt && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">Started:</span>
                        </div>
                        <p className="text-sm text-muted-foreground ml-6">
                          {formatDate(startedAt)} ({formatRelativeTime(startedAt)})
                        </p>
                      </div>
                    )}
                    
                    {completedAt && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">Completed:</span>
                        </div>
                        <p className="text-sm text-muted-foreground ml-6">
                          {formatDate(completedAt)} ({formatRelativeTime(completedAt)})
                        </p>
                      </div>
                    )}
                    
                    {startedAt && completedAt && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">Duration:</span>
                        </div>
                        <p className="text-sm text-muted-foreground ml-6">
                          {formatDuration(startedAt, completedAt)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Resource Usage */}
                {resourceUsage && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Resource Usage</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {resourceUsage.cpu !== undefined && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <Cpu className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">CPU:</span>
                          </div>
                          <p className="text-sm text-muted-foreground ml-6">
                            {resourceUsage.cpu}%
                          </p>
                        </div>
                      )}
                      
                      {resourceUsage.memory !== undefined && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <Memory className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">Memory:</span>
                          </div>
                          <p className="text-sm text-muted-foreground ml-6">
                            {(resourceUsage.memory / 1024).toFixed(1)} GB
                          </p>
                        </div>
                      )}
                      
                      {resourceUsage.tokens !== undefined && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <MessageSquare className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">Tokens:</span>
                          </div>
                          <p className="text-sm text-muted-foreground ml-6">
                            {resourceUsage.tokens.toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Error */}
                {error && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Error</h3>
                    <div className="p-4 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
                      <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Steps Tab */}
            {activeTab === 'steps' && steps && steps.length > 0 && (
              <div className="space-y-4">
                {steps.map((step, index) => (
                  <Card key={step.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">Step {index + 1}: {step.name}</h4>
                          <TaskStatusBadge status={step.status} size="sm" />
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {step.progress}%
                        </span>
                      </div>
                      
                      {step.description && (
                        <p className="text-sm text-muted-foreground mb-2">{step.description}</p>
                      )}
                      
                      <div className="w-full">
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                      </div>
                      
                      {step.error && (
                        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
                          <p className="text-sm text-red-800 dark:text-red-200">{step.error}</p>
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-4">
                          {step.startTime && (
                            <span>Started: {new Date(step.startTime).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: true,
                              timeZone: 'UTC'
                            })}</span>
                          )}
                          {step.endTime && (
                            <span>Ended: {new Date(step.endTime).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: true,
                              timeZone: 'UTC'
                            })}</span>
                          )}
                        </div>
                        {step.duration && (
                          <span>Duration: {(step.duration / 1000).toFixed(2)}s</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
            
            {/* Logs Tab */}
            {activeTab === 'logs' && (
              <div className="space-y-4">
                <div className="text-center text-muted-foreground py-8">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p>Task logs will be displayed here</p>
                  <p className="text-sm">This feature is coming soon</p>
                </div>
              </div>
            )}
            
            {/* Metadata Tab */}
            {activeTab === 'metadata' && (
              <div className="space-y-6">
                {/* Task ID */}
                <div>
                  <h3 className="text-lg font-semibold mb-2">Task ID</h3>
                  <div className="flex items-center gap-2">
                    <code className="px-2 py-1 bg-muted rounded text-sm">{id}</code>
                    <button
                      className={cn(
                        "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                        getButtonVariant("outline")
                      )}
                      onClick={() => copyToClipboard(id)}
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                {/* Metadata */}
                {metadata && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Metadata</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {metadata.agentUsed && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Agent:</span>
                          <p className="text-sm text-muted-foreground">{metadata.agentUsed}</p>
                        </div>
                      )}
                      
                      {metadata.agentVersion && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Agent Version:</span>
                          <p className="text-sm text-muted-foreground">{metadata.agentVersion}</p>
                        </div>
                      )}
                      
                      {metadata.modelUsed && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Model:</span>
                          <p className="text-sm text-muted-foreground">{metadata.modelUsed}</p>
                        </div>
                      )}
                      
                      {metadata.temperature !== undefined && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Temperature:</span>
                          <p className="text-sm text-muted-foreground">{metadata.temperature}</p>
                        </div>
                      )}
                      
                      {metadata.maxTokens && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Max Tokens:</span>
                          <p className="text-sm text-muted-foreground">{metadata.maxTokens}</p>
                        </div>
                      )}
                      
                      {metadata.category && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Category:</span>
                          <p className="text-sm text-muted-foreground">{metadata.category}</p>
                        </div>
                      )}
                      
                      {metadata.estimatedDuration && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Estimated Duration:</span>
                          <p className="text-sm text-muted-foreground">
                            {(metadata.estimatedDuration / 1000).toFixed(2)}s
                          </p>
                        </div>
                      )}
                      
                      {metadata.actualDuration && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Actual Duration:</span>
                          <p className="text-sm text-muted-foreground">
                            {(metadata.actualDuration / 1000).toFixed(2)}s
                          </p>
                        </div>
                      )}
                      
                      {metadata.retryCount !== undefined && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Retry Count:</span>
                          <p className="text-sm text-muted-foreground">{metadata.retryCount}</p>
                        </div>
                      )}
                      
                      {metadata.tags && metadata.tags.length > 0 && (
                        <div className="space-y-2">
                          <span className="text-sm font-medium">Tags:</span>
                          <div className="flex flex-wrap gap-2">
                            {metadata.tags.map((tag) => (
                              <span key={tag} className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold border-gray-200 bg-gray-50 text-gray-800 dark:border-gray-800 dark:bg-gray-900/20 dark:text-gray-300">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Result */}
                {result && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Result</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Output:</span>
                        <button
                          className={cn(
                            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                            getButtonVariant("outline")
                          )}
                          onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                      </div>
                      <pre className="p-4 bg-muted rounded text-sm overflow-auto max-h-60">
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
