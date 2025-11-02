"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { safeError } from '@/lib/safe-console';
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from '@/lib/karen-backend';
import {
  handleDownloadError,
  showSuccess,
  showInfo
} from '@/lib/error-handler';

type ApiDownloadStatus = Record<string, any>;

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

type DownloadTaskStatus = DownloadTask["status"];

const STATUS_MAP: Record<string, DownloadTaskStatus> = {
  pending: "pending",
  queued: "pending",
  running: "downloading",
  downloading: "downloading",
  in_progress: "downloading",
  paused: "paused",
  completed: "completed",
  success: "completed",
  done: "completed",
  error: "error",
  failed: "error",
  failure: "error",
  cancelled: "cancelled",
  canceled: "cancelled"
};

const generateTaskId = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  return `download-${Math.random().toString(36).slice(2, 10)}`;
};

const toUnixSeconds = (value?: number | string | Date | null): number => {
  if (value == null) {
    return Date.now() / 1000;
  }

  if (typeof value === 'number') {
    // Detect if already in seconds (10 digits) or milliseconds (13 digits)
    if (value > 1e12) {
      return value / 1000;
    }
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return parsed / 1000;
    }
    const numeric = Number(value);
    if (!Number.isNaN(numeric)) {
      return toUnixSeconds(numeric);
    }
  }

  if (value instanceof Date) {
    return value.getTime() / 1000;
  }

  return Date.now() / 1000;
};

const calculateSpeed = (apiResponse: ApiDownloadStatus): number => {
  const downloaded = apiResponse.downloaded_size ?? apiResponse.bytes_downloaded ?? apiResponse.current_size;
  if (!downloaded) {
    return 0;
  }

  const start = toUnixSeconds(apiResponse.start_time ?? apiResponse.started_at);
  const elapsed = Math.max(0, (Date.now() / 1000) - start);
  if (elapsed <= 0) {
    return 0;
  }

  return downloaded / elapsed;
};

const normaliseProgress = (rawProgress?: number | null): number => {
  if (rawProgress == null || Number.isNaN(rawProgress)) {
    return 0;
  }

  if (rawProgress > 1) {
    return Math.min(100, rawProgress);
  }

  return Math.max(0, rawProgress * 100);
};

const resolveStatus = (status?: string | null): DownloadTaskStatus => {
  if (!status) {
    return "pending";
  }

  const key = status.toLowerCase();
  return STATUS_MAP[key] ?? "pending";
};

export const createDownloadTaskFromApiResponse = (apiResponse: ApiDownloadStatus): DownloadTask => {
  const status = resolveStatus(apiResponse.status ?? apiResponse.state);
  const totalBytes = apiResponse.total_size ?? apiResponse.size ?? apiResponse.estimated_size ?? 0;
  const downloadedBytes = apiResponse.downloaded_size ?? apiResponse.bytes_downloaded ?? apiResponse.current_size ?? 0;

  return {
    id: apiResponse.task_id ?? apiResponse.job_id ?? apiResponse.id ?? generateTaskId(),
    modelId: apiResponse.model_id ?? apiResponse.model ?? apiResponse.modelId ?? "unknown-model",
    modelName: apiResponse.filename
      ?? apiResponse.model_name
      ?? apiResponse.artifact
      ?? apiResponse.display_name
      ?? apiResponse.model_id
      ?? apiResponse.model
      ?? "Unknown Model",
    status,
    progress: normaliseProgress(apiResponse.progress),
    downloadedBytes,
    totalBytes,
    speed: apiResponse.speed ?? apiResponse.download_speed ?? calculateSpeed(apiResponse),
    estimatedTimeRemaining: apiResponse.estimated_time_remaining ?? apiResponse.eta ?? 0,
    error: apiResponse.error ?? apiResponse.error_message,
    startTime: toUnixSeconds(apiResponse.start_time ?? apiResponse.started_at ?? apiResponse.created_at),
    lastUpdateTime: Date.now() / 1000,
  };
};

interface DownloadStatusHookReturn {
  downloadTasks: DownloadTask[];
  activeDownloads: DownloadTask[];
  completedDownloads: DownloadTask[];
  erroredDownloads: DownloadTask[];
  isPolling: boolean;
  startPolling: () => void;
  stopPolling: () => void;
  refreshDownloads: () => Promise<void>;
  getDownloadStatus: (taskId: string) => Promise<DownloadTask | null>;
  cancelDownload: (taskId: string) => Promise<void>;
  pauseDownload: (taskId: string) => Promise<void>;
  resumeDownload: (taskId: string) => Promise<void>;
  retryDownload: (taskId: string) => Promise<void>;
  clearCompletedDownloads: () => void;
  addDownloadTask: (task: DownloadTask) => void;
}

/**
 * @file use-download-status.ts
 * @description Hook for managing download status integration with real-time progress updates.
 * Connects frontend to download progress API endpoints and implements polling for updates.
 */
export function useDownloadStatus(): DownloadStatusHookReturn {
  const [downloadTasks, setDownloadTasks] = useState<DownloadTask[]>([]);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();

  // Derived state
  const activeDownloads = downloadTasks.filter(task =>
    task.status === 'downloading' || task.status === 'pending' || task.status === 'paused'
  );
  const completedDownloads = downloadTasks.filter(task => task.status === 'completed');
  const erroredDownloads = downloadTasks.filter(task => task.status === 'error');

  // Get download status for a specific task
  const getDownloadStatus = useCallback(async (taskId: string): Promise<DownloadTask | null> => {
    try {
      const response = await backend.makeRequestPublic(`/api/models/download/jobs/${taskId}`);
      if (response) {
        return createDownloadTaskFromApiResponse(response);
      }
      return null;
    } catch (error) {
      safeError(`Failed to get download status for task ${taskId}:`, error);
      return null;
    }
  }, [backend]);

  // Refresh all download tasks
  const refreshDownloads = useCallback(async () => {
    try {
      // For now, we'll maintain the existing tasks and update their status
      const updatedTasks: DownloadTask[] = [];
      
      for (const task of downloadTasks) {
        const updatedTask = await getDownloadStatus(task.id);
        if (updatedTask) {
          updatedTasks.push(updatedTask);
        }
      }

      setDownloadTasks(updatedTasks);
    } catch (error) {
      safeError('Failed to refresh downloads:', error);
    }
  }, [downloadTasks, getDownloadStatus]);

  // Start polling for download updates
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return; // Already polling

    setIsPolling(true);
    pollingIntervalRef.current = setInterval(async () => {
      if (activeDownloads.length > 0) {
        await refreshDownloads();
      } else {
        // Stop polling if no active downloads
        stopPolling();
      }
    }, 2000); // Poll every 2 seconds
  }, [activeDownloads.length, refreshDownloads]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Cancel download
  const cancelDownload = useCallback(async (taskId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/download/jobs/${taskId}/cancel`, {
        method: 'POST'
      });

      // Update local state
      setDownloadTasks(prev => prev.map(task =>
        task.id === taskId
          ? { ...task, status: 'cancelled' as const }
          : task
      ));

      showInfo("Download Cancelled", "The download has been cancelled successfully.");
    } catch (error) {
      safeError(`Failed to cancel download ${taskId}:`, error);
      handleDownloadError(error, "download");
      throw error;
    }
  }, [backend, toast]);

  // Pause download
  const pauseDownload = useCallback(async (taskId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/download/jobs/${taskId}/pause`, {
        method: 'POST'
      });

      setDownloadTasks(prev => prev.map(task =>
        task.id === taskId
          ? { ...task, status: 'paused' as const }
          : task
      ));

      showInfo("Download Paused", "The download has been paused successfully.");
    } catch (error) {
      safeError(`Failed to pause download ${taskId}:`, error);
      handleDownloadError(error, "download");
      throw error;
    }
  }, [backend, toast]);

  // Resume download
  const resumeDownload = useCallback(async (taskId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/download/jobs/${taskId}/resume`, {
        method: 'POST'
      });

      setDownloadTasks(prev => prev.map(task =>
        task.id === taskId
          ? { ...task, status: 'downloading' as const }
          : task
      ));

      showInfo("Download Resumed", "The download has been resumed successfully.");
    } catch (error) {
      safeError(`Failed to resume download ${taskId}:`, error);
      handleDownloadError(error, "download");
      throw error;
    }
  }, [backend, toast]);

  // Retry download
  const retryDownload = useCallback(async (taskId: string) => {
    const task = downloadTasks.find(t => t.id === taskId);
    try {
      if (!task) {
        throw new Error("Task not found");
      }

      // Start a new download for the same model
      const response = await backend.makeRequestPublic('/api/models/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_id: task.modelId })
      });

      if (response) {
        const newTask = createDownloadTaskFromApiResponse({
          ...response,
          model_id: task.modelId
        });

        // Remove old task and add new one
        setDownloadTasks(prev => [
          ...prev.filter(t => t.id !== taskId),
          newTask
        ]);

        showSuccess("Download Restarted", "The download has been restarted successfully.");

        // Start polling if not already active
        if (!isPolling) {
          startPolling();
        }
      }
    } catch (error) {
      safeError(`Failed to retry download ${taskId}:`, error);
      handleDownloadError(error, task?.modelId || "unknown model");
      throw error;
    }
  }, [backend, downloadTasks, toast, isPolling, startPolling]);

  // Clear completed downloads from the list
  const clearCompletedDownloads = useCallback(() => {
    setDownloadTasks(prev => prev.filter(task => 
      task.status !== 'completed' && task.status !== 'cancelled'
    ));
  }, []);

  // Add a new download task (to be called when starting a download)
  const addDownloadTask = useCallback((task: DownloadTask) => {
    setDownloadTasks(prev => {
      // Remove any existing task with the same ID
      const filtered = prev.filter(t => t.id !== task.id);
      return [...filtered, task];
    });

    // Start polling if not already active
    if (!isPolling) {
      startPolling();
    }
  }, [isPolling, startPolling]);

  // Auto-start polling when there are active downloads
  useEffect(() => {
    if (activeDownloads.length > 0 && !isPolling) {
      startPolling();
    } else if (activeDownloads.length === 0 && isPolling) {
      stopPolling();
    }
  }, [activeDownloads.length, isPolling, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    downloadTasks,
    activeDownloads,
    completedDownloads,
    erroredDownloads,
    isPolling,
    startPolling,
    stopPolling,
    refreshDownloads,
    getDownloadStatus,
    cancelDownload,
    pauseDownload,
    resumeDownload,
    retryDownload,
    clearCompletedDownloads,
    addDownloadTask
  };
}

// Export the DownloadTask type for use in other components
export type { DownloadTask };