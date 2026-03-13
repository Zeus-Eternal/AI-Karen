/**
 * Task Management API Service
 * Handles all API communications for the task management system
 */

import { BaseApiClient } from '@/lib/base-api-client';
import {
  Task,
  TaskFilters,
  TaskSortOptions,
  TaskListResponse,
  TaskStatistics,
  TaskActionPayload,
  TaskUpdateEvent
} from '../types';

// Define ApiResponse interface locally since it's not exported from base-api-client
interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  headers: Headers;
  ok: boolean;
}

// Create a dedicated API client for task management
const taskApiClient = new BaseApiClient({
  baseUrl: process.env.NEXT_PUBLIC_TASK_API_BASE_URL || '/api/tasks',
  timeout: 30000, // 30 seconds timeout for task operations
  defaultHeaders: {
    'X-Task-Client': 'karen-theme-default',
  },
});

/**
 * Task Management API Service
 */
export class TaskApiService {
  /**
   * Fetch tasks with optional filters and sorting
   */
  static async fetchTasks(
    filters?: TaskFilters,
    sort?: TaskSortOptions,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<TaskListResponse>> {
    const params: Record<string, string | number> = {
      page,
      pageSize,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
      if (filters.executionMode && filters.executionMode.length > 0) {
        params.executionMode = filters.executionMode.join(',');
      }
      if (filters.agent && filters.agent.length > 0) {
        params.agent = filters.agent.join(',');
      }
      if (filters.category && filters.category.length > 0) {
        params.category = filters.category.join(',');
      }
      if (filters.dateRange) {
        params.dateFrom = filters.dateRange.start.toISOString();
        params.dateTo = filters.dateRange.end.toISOString();
      }
      if (filters.search) {
        params.search = filters.search;
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return taskApiClient.get<TaskListResponse>('/', { params });
  }

  /**
   * Fetch a single task by ID
   */
  static async fetchTask(taskId: string): Promise<ApiResponse<Task>> {
    return taskApiClient.get<Task>(`/${taskId}`);
  }

  /**
   * Create a new task
   */
  static async createTask(task: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>('/', task);
  }

  /**
   * Update an existing task
   */
  static async updateTask(taskId: string, updates: Partial<Task>): Promise<ApiResponse<Task>> {
    return taskApiClient.patch<Task>(`/${taskId}`, updates);
  }

  /**
   * Delete a task
   */
  static async deleteTask(taskId: string): Promise<ApiResponse<void>> {
    return taskApiClient.delete<void>(`/${taskId}`);
  }

  /**
   * Execute an action on a task
   */
  static async executeTaskAction(payload: TaskActionPayload): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>(`/${payload.taskId}/actions`, {
      action: payload.action,
      data: payload.data,
    });
  }

  /**
   * Fetch task statistics
   */
  static async fetchStatistics(): Promise<ApiResponse<TaskStatistics>> {
    return taskApiClient.get<TaskStatistics>('/statistics');
  }

  /**
   * Cancel a running task
   */
  static async cancelTask(taskId: string): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>(`/${taskId}/cancel`);
  }

  /**
   * Retry a failed task
   */
  static async retryTask(taskId: string): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>(`/${taskId}/retry`);
  }

  /**
   * Pause a running task
   */
  static async pauseTask(taskId: string): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>(`/${taskId}/pause`);
  }

  /**
   * Resume a paused task
   */
  static async resumeTask(taskId: string): Promise<ApiResponse<Task>> {
    return taskApiClient.post<Task>(`/${taskId}/resume`);
  }

  /**
   * Fetch task logs
   */
  static async fetchTaskLogs(taskId: string): Promise<ApiResponse<string[]>> {
    return taskApiClient.get<string[]>(`/${taskId}/logs`);
  }

  /**
   * Fetch task execution details
   */
  static async fetchTaskExecutionDetails(taskId: string): Promise<ApiResponse<Record<string, unknown>>> {
    return taskApiClient.get<Record<string, unknown>>(`/${taskId}/execution`);
  }

  /**
   * Export tasks to various formats
   */
  static async exportTasks(
    filters?: TaskFilters,
    format: 'json' | 'csv' | 'xlsx' = 'json'
  ): Promise<ApiResponse<Blob>> {
    const params: Record<string, string | number> = {
      format,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
      if (filters.executionMode && filters.executionMode.length > 0) {
        params.executionMode = filters.executionMode.join(',');
      }
      if (filters.dateRange) {
        params.dateFrom = filters.dateRange.start.toISOString();
        params.dateTo = filters.dateRange.end.toISOString();
      }
    }

    return taskApiClient.get<Blob>('/export', { params });
  }

  /**
   * Create a WebSocket connection for real-time updates
   */
  static createWebSocketConnection(): WebSocket {
    const wsUrl = process.env.NEXT_PUBLIC_TASK_WS_URL || 
                  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/tasks/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    return ws;
  }

  /**
   * Subscribe to real-time task updates
   */
  static subscribeToTaskUpdates(
    callback: (event: TaskUpdateEvent) => void
  ): () => void {
    const ws = this.createWebSocketConnection();
    
    ws.onopen = () => {
      console.log('Task updates WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const taskEvent: TaskUpdateEvent = JSON.parse(event.data);
        callback(taskEvent);
      } catch (error) {
        console.error('Error parsing task update event:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('Task updates WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Task updates WebSocket disconnected');
    };
    
    // Return unsubscribe function
    return () => {
      ws.close();
    };
  }

  /**
   * Fetch tasks by agent
   */
  static async fetchTasksByAgent(
    agentId: string,
    filters?: TaskFilters,
    sort?: TaskSortOptions
  ): Promise<ApiResponse<TaskListResponse>> {
    const params: Record<string, string | number> = {
      agent: agentId,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return taskApiClient.get<TaskListResponse>('/by-agent', { params });
  }

  /**
   * Fetch tasks by execution mode
   */
  static async fetchTasksByExecutionMode(
    executionMode: string,
    filters?: TaskFilters,
    sort?: TaskSortOptions
  ): Promise<ApiResponse<TaskListResponse>> {
    const params: Record<string, string | number> = {
      executionMode,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return taskApiClient.get<TaskListResponse>('/by-execution-mode', { params });
  }

  /**
   * Bulk operations on tasks
   */
  static async bulkUpdateTasks(
    taskIds: string[],
    updates: Partial<Task>
  ): Promise<ApiResponse<Task[]>> {
    return taskApiClient.patch<Task[]>('/bulk', {
      taskIds,
      updates,
    });
  }

  /**
   * Bulk delete tasks
   */
  static async bulkDeleteTasks(taskIds: string[]): Promise<ApiResponse<void>> {
    return taskApiClient.delete<void>('/bulk', {
      params: { taskIds: taskIds.join(',') },
    });
  }

  /**
   * Bulk execute actions on tasks
   */
  static async bulkExecuteActions(
    taskIds: string[],
    action: TaskActionPayload['action'],
    data?: unknown
  ): Promise<ApiResponse<Task[]>> {
    return taskApiClient.post<Task[]>('/bulk-actions', {
      taskIds,
      action,
      data,
    });
  }
}

// Export the default API client for advanced usage
export { taskApiClient };

// Export convenience functions for common operations
export const taskApi = {
  fetchTasks: TaskApiService.fetchTasks,
  fetchTask: TaskApiService.fetchTask,
  createTask: TaskApiService.createTask,
  updateTask: TaskApiService.updateTask,
  deleteTask: TaskApiService.deleteTask,
  executeTaskAction: TaskApiService.executeTaskAction,
  fetchStatistics: TaskApiService.fetchStatistics,
  cancelTask: TaskApiService.cancelTask,
  retryTask: TaskApiService.retryTask,
  pauseTask: TaskApiService.pauseTask,
  resumeTask: TaskApiService.resumeTask,
  fetchTaskLogs: TaskApiService.fetchTaskLogs,
  fetchTaskExecutionDetails: TaskApiService.fetchTaskExecutionDetails,
  exportTasks: TaskApiService.exportTasks,
  subscribeToTaskUpdates: TaskApiService.subscribeToTaskUpdates,
  fetchTasksByAgent: TaskApiService.fetchTasksByAgent,
  fetchTasksByExecutionMode: TaskApiService.fetchTasksByExecutionMode,
  bulkUpdateTasks: TaskApiService.bulkUpdateTasks,
  bulkDeleteTasks: TaskApiService.bulkDeleteTasks,
  bulkExecuteActions: TaskApiService.bulkExecuteActions,
};
