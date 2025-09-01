"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from '@/lib/karen-backend';
import { 
  handleApiError, 
  handleDownloadError,
  showSuccess,
  showInfo,
  showWarning
} from '@/lib/error-handler';

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

  // Convert API response to DownloadTask
  const convertApiResponseToTask = (apiResponse: any): DownloadTask => {
    return {
      id: apiResponse.task_id,
      modelId: apiResponse.model_id,
      modelName: apiResponse.filename || apiResponse.model_id, // Use filename or fallback to model_id
      status: apiResponse.status,
      progress: apiResponse.progress || 0,
      downloadedBytes: apiResponse.downloaded_size || 0,
      totalBytes: apiResponse.total_size || 0,
      speed: calculateSpeed(apiResponse),
      estimatedTimeRemaining: apiResponse.estimated_time_remaining || 0,
      error: apiResponse.error_message,
      startTime: apiResponse.start_time || Date.now() / 1000,
      lastUpdateTime: Date.now() / 1000
    };
  };

  // Calculate download speed from API response
  const calculateSpeed = (apiResponse: any): number => {
    if (!apiResponse.start_time || !apiResponse.downloaded_size) return 0;
    
    const elapsedTime = (Date.now() / 1000) - apiResponse.start_time;
    if (elapsedTime <= 0) return 0;
    
    return apiResponse.downloaded_size / elapsedTime;
  };

  // Get download status for a specific task
  const getDownloadStatus = useCallback(async (taskId: string): Promise<DownloadTask | null> => {
    try {
      const response = await backend.makeRequestPublic(`/api/models/download/${taskId}`);
      if (response) {
        return convertApiResponseToTask(response);
      }
      return null;
    } catch (error) {
      console.error(`Failed to get download status for task ${taskId}:`, error);
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
      console.error('Failed to refresh downloads:', error);
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
      await backend.makeRequestPublic(`/api/models/download/${taskId}`, {
        method: 'DELETE'
      });

      // Update local state
      setDownloadTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: 'cancelled' as const }
          : task
      ));

      showInfo("Download Cancelled", "The download has been cancelled successfully.");
    } catch (error) {
      console.error(`Failed to cancel download ${taskId}:`, error);
      handleDownloadError(error, "download");
      throw error;
    }
  }, [backend, toast]);

  // Pause download (placeholder - not implemented in backend yet)
  const pauseDownload = useCallback(async (taskId: string) => {
    // TODO: Implement when backend supports pause functionality
    showWarning("Pause Not Available", "Download pause functionality is not yet implemented.");
    throw new Error("Pause functionality not implemented");
  }, [toast]);

  // Resume download (placeholder - not implemented in backend yet)
  const resumeDownload = useCallback(async (taskId: string) => {
    // TODO: Implement when backend supports resume functionality
    showWarning("Resume Not Available", "Download resume functionality is not yet implemented.");
    throw new Error("Resume functionality not implemented");
  }, [toast]);

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
        body: JSON.stringify({ model_id: task.modelId })
      });

      if (response) {
        const newTask = convertApiResponseToTask(response);
        
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
      console.error(`Failed to retry download ${taskId}:`, error);
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