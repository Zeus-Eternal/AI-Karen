"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Download,
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { useDownloadStatus, DownloadTask } from '@/hooks/use-download-status';
import ModelDownloadProgress from './ModelDownloadProgress';
import { HelpTooltip } from '@/components/ui/help-tooltip';

interface DownloadManagerProps {
  onDownloadComplete?: (modelId: string) => void;
  compact?: boolean;
}

/**
 * @file DownloadManager.tsx
 * @description Component for managing active downloads with real-time progress updates.
 * Integrates with the download status hook to provide a centralized download management interface.
 */
export default function DownloadManager({ onDownloadComplete, compact = false }: DownloadManagerProps) {
  const [showCompleted, setShowCompleted] = useState(false);
  
  const {
    downloadTasks,
    activeDownloads,
    completedDownloads,
    erroredDownloads,
    isPolling,
    refreshDownloads,
    cancelDownload,
    pauseDownload,
    resumeDownload,
    retryDownload,
    clearCompletedDownloads
  } = useDownloadStatus();

  const handleDownloadAction = async (taskId: string, action: 'cancel' | 'pause' | 'resume' | 'retry') => {
    try {
      switch (action) {
        case 'cancel':
          await cancelDownload(taskId);
          break;
        case 'pause':
          await pauseDownload(taskId);
          break;
        case 'resume':
          await resumeDownload(taskId);
          break;
        case 'retry':
          await retryDownload(taskId);
          break;
      }
    } catch (error) {
      // Error handling is done in the hook
      console.error(`Download action ${action} failed:`, error);
    }
  };

  const handleDownloadComplete = (task: DownloadTask) => {
    if (task.status === 'completed' && onDownloadComplete) {
      onDownloadComplete(task.modelId);
    }
  };

  // Compact view for embedding in other components
  if (compact) {
    if (activeDownloads.length === 0 && erroredDownloads.length === 0) {
      return null;
    }

    return (
      <div className="space-y-3">
        {/* Active Downloads */}
        {activeDownloads.map(task => (
          <ModelDownloadProgress
            key={task.id}
            task={task}
            onCancel={(taskId) => handleDownloadAction(taskId, 'cancel')}
            onPause={(taskId) => handleDownloadAction(taskId, 'pause')}
            onResume={(taskId) => handleDownloadAction(taskId, 'resume')}
            compact={true}
          />
        ))}

        {/* Error Downloads */}
        {erroredDownloads.map(task => (
          <ModelDownloadProgress
            key={task.id}
            task={task}
            onCancel={(taskId) => handleDownloadAction(taskId, 'cancel')}
            onRetry={(taskId) => handleDownloadAction(taskId, 'retry')}
            compact={true}
          />
        ))}
      </div>
    );
  }

  // Full view
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Download Manager
                <HelpTooltip helpKey="downloadManager" variant="inline" size="sm" />
                {isPolling && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
              </CardTitle>
              <CardDescription>
                Monitor and manage model downloads in real-time.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refreshDownloads}
                disabled={isPolling}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isPolling ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              {completedDownloads.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearCompletedDownloads}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear Completed
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Download Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Active</p>
                <p className="text-2xl font-bold">{activeDownloads.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-2xl font-bold">{completedDownloads.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-sm font-medium">Errors</p>
                <p className="text-2xl font-bold">{erroredDownloads.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total</p>
                <p className="text-2xl font-bold">{downloadTasks.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Downloads */}
      {activeDownloads.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
              Active Downloads
              <Badge variant="default" className="gap-1">
                {activeDownloads.length} active
              </Badge>
            </CardTitle>
            <CardDescription>
              Downloads currently in progress. You can pause or cancel them at any time.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeDownloads.map(task => (
              <ModelDownloadProgress
                key={task.id}
                task={task}
                onCancel={(taskId) => handleDownloadAction(taskId, 'cancel')}
                onPause={(taskId) => handleDownloadAction(taskId, 'pause')}
                onResume={(taskId) => handleDownloadAction(taskId, 'resume')}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Error Downloads */}
      {erroredDownloads.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              Failed Downloads
              <Badge variant="destructive" className="gap-1">
                {erroredDownloads.length} failed
              </Badge>
            </CardTitle>
            <CardDescription>
              Downloads that encountered errors. You can retry or remove them.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {erroredDownloads.map(task => (
              <ModelDownloadProgress
                key={task.id}
                task={task}
                onCancel={(taskId) => handleDownloadAction(taskId, 'cancel')}
                onRetry={(taskId) => handleDownloadAction(taskId, 'retry')}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Completed Downloads */}
      {completedDownloads.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  Completed Downloads
                  <Badge variant="default" className="gap-1 bg-green-500 hover:bg-green-600">
                    {completedDownloads.length} completed
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Successfully downloaded models. These are now available in your local library.
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCompleted(!showCompleted)}
              >
                {showCompleted ? 'Hide' : 'Show'} Completed
              </Button>
            </div>
          </CardHeader>
          {showCompleted && (
            <CardContent className="space-y-4">
              {completedDownloads.map(task => {
                // Trigger completion callback
                handleDownloadComplete(task);
                
                return (
                  <ModelDownloadProgress
                    key={task.id}
                    task={task}
                    onCancel={(taskId) => handleDownloadAction(taskId, 'cancel')}
                  />
                );
              })}
            </CardContent>
          )}
        </Card>
      )}

      {/* No Downloads */}
      {downloadTasks.length === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <Download className="h-8 w-8 mx-auto text-muted-foreground" />
              <div className="space-y-2">
                <p className="text-lg font-medium">No Downloads</p>
                <p className="text-sm text-muted-foreground">
                  Start downloading models from the Model Library to see them here.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Polling Status */}
      {isPolling && activeDownloads.length > 0 && (
        <Alert>
          <Loader2 className="h-4 w-4 animate-spin" />
          <AlertDescription>
            Monitoring {activeDownloads.length} active download{activeDownloads.length !== 1 ? 's' : ''}...
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}