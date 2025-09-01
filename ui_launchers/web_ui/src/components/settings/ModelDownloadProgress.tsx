"use client";

import React, { useState, useEffect } from 'react';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from "@/hooks/use-toast";
import { 
  handleApiError, 
  handleDownloadError,
  formatFileSize,
  formatSpeed,
  formatDuration
} from '@/lib/error-handler';
import {
  Loader2,
  X,
  Pause,
  Play,
  AlertCircle,
  Download,
  CheckCircle,
  Clock,
  HardDrive
} from 'lucide-react';

interface DownloadTask {
  id: string;
  modelId: string;
  modelName: string;
  status: 'pending' | 'downloading' | 'paused' | 'completed' | 'error' | 'cancelled';
  progress: number;
  downloadedBytes: number;
  totalBytes: number;
  speed: number; // bytes per second
  estimatedTimeRemaining: number; // seconds
  error?: string;
  startTime: number;
  lastUpdateTime: number;
}

interface ModelDownloadProgressProps {
  task: DownloadTask;
  onCancel: (taskId: string) => Promise<void>;
  onPause?: (taskId: string) => Promise<void>;
  onResume?: (taskId: string) => Promise<void>;
  onRetry?: (taskId: string) => Promise<void>;
  compact?: boolean;
}

/**
 * @file ModelDownloadProgress.tsx
 * @description Component for displaying download progress with cancellation support and error states.
 * Uses existing Progress component for visualization and follows established UI patterns.
 */
export default function ModelDownloadProgress({
  task,
  onCancel,
  onPause,
  onResume,
  onRetry,
  compact = false
}: ModelDownloadProgressProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();

  // Use centralized formatting functions
  const formatBytes = formatFileSize;
  const formatTime = formatDuration;

  const handleAction = async (action: string, actionFn?: (taskId: string) => Promise<void>) => {
    if (!actionFn) return;
    
    setActionLoading(action);
    try {
      await actionFn(task.id);
    } catch (error) {
      console.error(`Failed to ${action} download:`, error);
      handleDownloadError(error, task.modelName);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = () => {
    switch (task.status) {
      case 'downloading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-500" />;
      default:
        return <Download className="h-4 w-4" />;
    }
  };

  const getStatusBadge = () => {
    switch (task.status) {
      case 'downloading':
        return <Badge variant="default" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Downloading
        </Badge>;
      case 'paused':
        return <Badge variant="secondary" className="gap-1">
          <Pause className="h-3 w-3" />
          Paused
        </Badge>;
      case 'completed':
        return <Badge variant="default" className="gap-1 bg-green-500 hover:bg-green-600">
          <CheckCircle className="h-3 w-3" />
          Completed
        </Badge>;
      case 'error':
        return <Badge variant="destructive" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Error
        </Badge>;
      case 'cancelled':
        return <Badge variant="outline" className="gap-1">
          <X className="h-3 w-3" />
          Cancelled
        </Badge>;
      case 'pending':
        return <Badge variant="outline" className="gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const renderActions = () => {
    switch (task.status) {
      case 'downloading':
        return (
          <div className="flex gap-2">
            {onPause && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('pause', onPause)}
                disabled={actionLoading === 'pause'}
                className="gap-1"
              >
                {actionLoading === 'pause' ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Pause className="h-3 w-3" />
                )}
                Pause
              </Button>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleAction('cancel', onCancel)}
              disabled={actionLoading === 'cancel'}
              className="gap-1"
            >
              {actionLoading === 'cancel' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Cancel
            </Button>
          </div>
        );
      
      case 'paused':
        return (
          <div className="flex gap-2">
            {onResume && (
              <Button
                variant="default"
                size="sm"
                onClick={() => handleAction('resume', onResume)}
                disabled={actionLoading === 'resume'}
                className="gap-1"
              >
                {actionLoading === 'resume' ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                Resume
              </Button>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleAction('cancel', onCancel)}
              disabled={actionLoading === 'cancel'}
              className="gap-1"
            >
              {actionLoading === 'cancel' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Cancel
            </Button>
          </div>
        );
      
      case 'error':
        return (
          <div className="flex gap-2">
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('retry', onRetry)}
                disabled={actionLoading === 'retry'}
                className="gap-1"
              >
                {actionLoading === 'retry' ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Download className="h-3 w-3" />
                )}
                Retry
              </Button>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleAction('cancel', onCancel)}
              disabled={actionLoading === 'cancel'}
              className="gap-1"
            >
              {actionLoading === 'cancel' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <X className="h-3 w-3" />
              )}
              Remove
            </Button>
          </div>
        );
      
      case 'completed':
        return (
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction('remove', onCancel)}
            disabled={actionLoading === 'remove'}
            className="gap-1"
          >
            {actionLoading === 'remove' ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <X className="h-3 w-3" />
            )}
            Remove
          </Button>
        );
      
      default:
        return null;
    }
  };

  // Compact view for embedding in other components
  if (compact) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium">{task.modelName}</span>
            {getStatusBadge()}
          </div>
          <div className="flex items-center gap-2">
            {task.status === 'downloading' && (
              <span className="text-muted-foreground">
                {Math.round(task.progress)}%
              </span>
            )}
            {renderActions()}
          </div>
        </div>
        
        {(task.status === 'downloading' || task.status === 'paused') && (
          <div className="space-y-1">
            <Progress value={task.progress} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                {formatBytes(task.downloadedBytes)} / {formatBytes(task.totalBytes)}
              </span>
              {task.status === 'downloading' && task.speed > 0 && (
                <span>
                  {formatSpeed(task.speed)} • {formatTime(task.estimatedTimeRemaining)} remaining
                </span>
              )}
            </div>
          </div>
        )}

        {task.status === 'error' && task.error && (
          <Alert variant="destructive" className="mt-2">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {task.error}
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  // Full card view
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base leading-tight truncate flex items-center gap-2">
              {getStatusIcon()}
              {task.modelName}
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              Model download task
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {getStatusBadge()}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress Section */}
        {(task.status === 'downloading' || task.status === 'paused') && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Progress</span>
              <span className="text-muted-foreground">
                {Math.round(task.progress)}%
              </span>
            </div>
            <Progress value={task.progress} className="h-3" />
            
            {/* Download Stats */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Downloaded:</span>
                <div className="font-medium">
                  {formatBytes(task.downloadedBytes)} / {formatBytes(task.totalBytes)}
                </div>
              </div>
              {task.status === 'downloading' && task.speed > 0 && (
                <div>
                  <span className="text-muted-foreground">Speed:</span>
                  <div className="font-medium">{formatSpeed(task.speed)}</div>
                </div>
              )}
            </div>

            {task.status === 'downloading' && task.estimatedTimeRemaining > 0 && (
              <div className="text-sm">
                <span className="text-muted-foreground">Time remaining:</span>
                <span className="ml-2 font-medium">
                  {formatTime(task.estimatedTimeRemaining)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Completed Status */}
        {task.status === 'completed' && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span>Download completed successfully</span>
          </div>
        )}

        {/* Error Alert */}
        {task.status === 'error' && task.error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {task.error}
            </AlertDescription>
          </Alert>
        )}

        {/* Cancelled Status */}
        {task.status === 'cancelled' && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <X className="h-4 w-4" />
            <span>Download was cancelled</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end pt-2">
          {renderActions()}
        </div>
      </CardContent>
    </Card>
  );
}