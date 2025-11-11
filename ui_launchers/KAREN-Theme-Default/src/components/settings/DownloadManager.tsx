"use client";

import React, { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { HelpTooltip } from "@/components/ui/help-tooltip";

import {
  Download,
  Loader2,
  RefreshCw,
  Trash2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

import { useDownloadStatus } from "@/hooks/use-download-status";
import ModelDownloadProgress from "./ModelDownloadProgress";

export interface DownloadManagerProps {
  onDownloadComplete?: (modelId: string) => void;
  compact?: boolean;
}

/**
 * @file DownloadManager.tsx
 * @description Manage active model downloads with real-time progress.
 * Uses the download status hook for polling + control actions.
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
    clearCompletedDownloads,
  } = useDownloadStatus();

  // ---- Side-effect safety: notify completion OUTSIDE render ----
  // Track which completed task IDs we've already notified for, to avoid duplicate callbacks.
  const notifiedCompletedIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!onDownloadComplete) return;
    for (const t of completedDownloads) {
      if (!notifiedCompletedIds.current.has(t.id)) {
        notifiedCompletedIds.current.add(t.id);
        // Fire and forget — caller decides what to do on completion.
        try {
          onDownloadComplete(t.modelId);
        } catch {
          // Swallow — UI must stay resilient
        }
      }
    }
  }, [completedDownloads, onDownloadComplete]);

  const handleDownloadAction = async (
    taskId: string,
    action: "cancel" | "pause" | "resume" | "retry"
  ) => {
    try {
      if (action === "cancel") await cancelDownload(taskId);
      else if (action === "pause") await pauseDownload(taskId);
      else if (action === "resume") await resumeDownload(taskId);
      else if (action === "retry") await retryDownload(taskId);
    } catch {
      // Hook handles error reporting; keep UI calm.
    }
  };

  // Compact embed view
  if (compact) {
    if (activeDownloads.length === 0 && erroredDownloads.length === 0) return null;

    return (
      <div className="space-y-3">
        {activeDownloads.map((task) => (
          <ModelDownloadProgress
            key={task.id}
            task={task}
            onCancel={(taskId) => handleDownloadAction(taskId, "cancel")}
            onPause={(taskId) => handleDownloadAction(taskId, "pause")}
            onResume={(taskId) => handleDownloadAction(taskId, "resume")}
            compact
          />
        ))}
        {erroredDownloads.map((task) => (
          <ModelDownloadProgress
            key={task.id}
            task={task}
            onCancel={(taskId) => handleDownloadAction(taskId, "cancel")}
            onRetry={(taskId) => handleDownloadAction(taskId, "retry")}
            compact
          />
        ))}
      </div>
    );
  }

  // Derived counts with memo for tiny perf win in large lists
  const counts = {
    active: activeDownloads.length,
    completed: completedDownloads.length,
    errored: erroredDownloads.length,
    total: downloadTasks.length,
  };

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
                {isPolling && <Loader2 className="h-4 w-4 animate-spin text-blue-500" aria-label="Polling downloads" />}
              </CardTitle>
              <CardDescription>Monitor and manage model downloads in real time.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refreshDownloads}
                disabled={isPolling}
                aria-label="Refresh downloads"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isPolling ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              {counts.completed > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearCompletedDownloads}
                  aria-label="Clear completed"
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
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-blue-500" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium">Active</p>
                <p className="text-2xl font-bold">{counts.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-2xl font-bold">{counts.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium">Errors</p>
                <p className="text-2xl font-bold">{counts.errored}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium">Total</p>
                <p className="text-2xl font-bold">{counts.total}</p>
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
              <Badge variant="default" className="gap-1">
                {activeDownloads.length} active
              </Badge>
            </CardTitle>
            <CardDescription>Pause or cancel any active download.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeDownloads.map((task) => (
              <ModelDownloadProgress
                key={task.id}
                task={task}
                onCancel={(taskId) => handleDownloadAction(taskId, "cancel")}
                onPause={(taskId) => handleDownloadAction(taskId, "pause")}
                onResume={(taskId) => handleDownloadAction(taskId, "resume")}
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
              <Badge variant="destructive" className="gap-1">
                {erroredDownloads.length} failed
              </Badge>
            </CardTitle>
            <CardDescription>Retry failed downloads or remove them.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {erroredDownloads.map((task) => (
              <ModelDownloadProgress
                key={task.id}
                task={task}
                onCancel={(taskId) => handleDownloadAction(taskId, "cancel")}
                onRetry={(taskId) => handleDownloadAction(taskId, "retry")}
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
                  <Badge variant="default" className="gap-1 bg-green-500 hover:bg-green-600">
                    {completedDownloads.length} completed
                  </Badge>
                </CardTitle>
                <CardDescription>These models are now available in your local library.</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCompleted((v) => !v)}
                aria-expanded={showCompleted}
                aria-controls="completed-list"
              >
                {showCompleted ? "Hide" : "Show"} Completed
              </Button>
            </div>
          </CardHeader>
          {showCompleted && (
            <CardContent id="completed-list" className="space-y-4">
              {completedDownloads.map((task) => (
                <ModelDownloadProgress
                  key={task.id}
                  task={task}
                  onCancel={(taskId) => handleDownloadAction(taskId, "cancel")}
                />
              ))}
            </CardContent>
          )}
        </Card>
      )}

      {/* Empty State */}
      {downloadTasks.length === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <Download className="h-8 w-8 mx-auto text-muted-foreground" aria-hidden="true" />
              <div className="space-y-2">
                <p className="text-lg font-medium">No Downloads</p>
                <p className="text-sm text-muted-foreground">
                  Start downloads from the Model Library to see them here.
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
            Monitoring {activeDownloads.length} active download{activeDownloads.length !== 1 ? "s" : ""}…
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
