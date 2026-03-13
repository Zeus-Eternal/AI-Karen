"use client";

import React, { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Task, TaskAction, TaskActionPayload } from '../types';
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
const MoreVertical = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
  </svg>
);

const Eye = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const RotateCcw = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const Pause = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Play = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Trash = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

interface TaskActionsProps {
  task: Task;
  onAction: (payload: TaskActionPayload) => void;
  compact?: boolean;
  className?: string;
}

export function TaskActions({
  task,
  onAction,
  compact = false,
  className,
}: TaskActionsProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<TaskAction | null>(null);

  // Get available actions based on task status
  const getAvailableActions = (): TaskAction[] => {
    const actions: TaskAction[] = ['view'];
    
    switch (task.status) {
      case 'pending':
        actions.push('delete');
        break;
      case 'running':
        actions.push('cancel', 'pause');
        break;
      case 'paused':
        actions.push('resume', 'cancel', 'delete');
        break;
      case 'completed':
        actions.push('delete');
        break;
      case 'failed':
        actions.push('retry', 'delete');
        break;
      case 'cancelled':
        actions.push('retry', 'delete');
        break;
    }
    
    return actions;
  };

  const handleAction = (action: TaskAction) => {
    if (action === 'delete') {
      setDeleteDialogOpen(true);
    } else if (action === 'cancel' || action === 'retry') {
      setPendingAction(action);
      setActionDialogOpen(true);
    } else {
      onAction({ taskId: task.id, action });
    }
  };

  const confirmDelete = () => {
    onAction({ taskId: task.id, action: 'delete' });
    setDeleteDialogOpen(false);
  };

  const confirmAction = () => {
    if (pendingAction) {
      onAction({ taskId: task.id, action: pendingAction });
      setActionDialogOpen(false);
      setPendingAction(null);
    }
  };

  const getActionIcon = (action: TaskAction) => {
    switch (action) {
      case 'view':
        return <Eye className="h-4 w-4" />;
      case 'cancel':
        return <X className="h-4 w-4" />;
      case 'retry':
        return <RotateCcw className="h-4 w-4" />;
      case 'pause':
        return <Pause className="h-4 w-4" />;
      case 'resume':
        return <Play className="h-4 w-4" />;
      case 'delete':
        return <Trash className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getActionLabel = (action: TaskAction) => {
    switch (action) {
      case 'view':
        return 'View Details';
      case 'cancel':
        return 'Cancel Task';
      case 'retry':
        return 'Retry Task';
      case 'pause':
        return 'Pause Task';
      case 'resume':
        return 'Resume Task';
      case 'delete':
        return 'Delete Task';
      default:
        return action;
    }
  };

  const getActionVariant = (action: TaskAction): "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" => {
    switch (action) {
      case 'delete':
        return 'destructive';
      case 'view':
        return 'outline';
      default:
        return 'default';
    }
  };

  const availableActions = getAvailableActions();

  if (compact) {
    return (
      <>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 w-8 p-0",
                "aria-label:Task actions"
              )}
              aria-label="Task actions"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {availableActions.map((action) => (
              <DropdownMenuItem
                key={action}
                onClick={() => handleAction(action)}
                className="flex items-center gap-2"
              >
                {getActionIcon(action)}
                {getActionLabel(action)}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Delete confirmation dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Task</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this task? This action cannot be undone.
                <br />
                <strong>Task:</strong> {task.title}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Action confirmation dialog */}
        <AlertDialog open={actionDialogOpen} onOpenChange={setActionDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {pendingAction && getActionLabel(pendingAction)}
              </AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to {pendingAction?.toLowerCase()} this task?
                <br />
                <strong>Task:</strong> {task.title}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmAction}>
                {pendingAction && getActionLabel(pendingAction)}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </>
    );
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {availableActions.map((action) => (
        <button
          key={action}
          className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
            getButtonVariant(getActionVariant(action))
          )}
          onClick={() => handleAction(action)}
        >
          {getActionIcon(action)}
          {getActionLabel(action)}
        </button>
      ))}

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this task? This action cannot be undone.
              <br />
              <strong>Task:</strong> {task.title}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Action confirmation dialog */}
      <AlertDialog open={actionDialogOpen} onOpenChange={setActionDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction && getActionLabel(pendingAction)}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to {pendingAction?.toLowerCase()} this task?
              <br />
              <strong>Task:</strong> {task.title}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmAction}>
              {pendingAction && getActionLabel(pendingAction)}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// Quick action buttons for common operations
interface QuickTaskActionsProps {
  task: Task;
  onAction: (payload: TaskActionPayload) => void;
  className?: string;
}

export function QuickTaskActions({
  task,
  onAction,
  className,
}: QuickTaskActionsProps) {
  const getQuickActions = () => {
    const actions: TaskAction[] = [];
    
    switch (task.status) {
      case 'running':
        actions.push('pause');
        break;
      case 'paused':
        actions.push('resume');
        break;
      case 'failed':
      case 'cancelled':
        actions.push('retry');
        break;
    }
    
    return actions;
  };

  const quickActions = getQuickActions();

  if (quickActions.length === 0) {
    return null;
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {quickActions.map((action) => (
        <button
          key={action}
          className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-6 w-6 p-0",
            getButtonVariant("ghost")
          )}
          onClick={() => onAction({ taskId: task.id, action })}
          title={action.charAt(0).toUpperCase() + action.slice(1)}
        >
          {action === 'pause' && <Pause className="h-3 w-3" />}
          {action === 'resume' && <Play className="h-3 w-3" />}
          {action === 'retry' && <RotateCcw className="h-3 w-3" />}
        </button>
      ))}
    </div>
  );
}
