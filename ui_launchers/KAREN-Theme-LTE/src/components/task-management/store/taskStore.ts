/**
 * Task Management Store
 * Zustand store for managing task state and operations
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { 
  Task, 
  TaskFilters, 
  TaskSortOptions, 
  TaskActionPayload,
  TaskUpdateEvent,
  TaskManagementStore,
  TaskManagementState,
} from '../types';
import { taskApi } from '../services/taskApi';

type TaskStoreState = TaskManagementStore & {
  unsubscribeFromUpdates?: () => void;
};

// Default filters
const defaultFilters: TaskFilters = {
  status: [],
  priority: [],
  executionMode: [],
  agent: [],
  category: [],
};

// Default sort options
const defaultSortOptions: TaskSortOptions = {
  field: 'createdAt',
  direction: 'desc',
};

// Initial state
const initialState: TaskManagementState = {
  tasks: [],
  selectedTask: null,
  isLoading: false,
  error: null,
  filters: defaultFilters,
  sortOptions: defaultSortOptions,
  isRealTimeEnabled: false,
  lastUpdate: null,
  statistics: null,
  showDetails: false,
  showFilters: false,
  viewMode: 'list',
};

// Create the store
export const useTaskStore = create<TaskStoreState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Task operations
                fetchTasks: async (filters?: TaskFilters, sort?: TaskSortOptions) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    const currentFilters = filters || get().filters;
                    const currentSort = sort || get().sortOptions;
                    
                    const response = await taskApi.fetchTasks(currentFilters, currentSort);
                    
                    set({
                      tasks: response.data.tasks,
                      isLoading: false,
                      filters: currentFilters,
                      sortOptions: currentSort,
                    });
                  } catch (error) {
                    console.error('Failed to fetch tasks:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to fetch tasks',
                      isLoading: false,
                    });
                  }
                },
        
                fetchTask: async (taskId: string) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    const response = await taskApi.fetchTask(taskId);
                    const task = response.data;
                    
                    // Update task in the list if it exists
                    set((state) => ({
                      tasks: state.tasks.some(t => t.id === task.id)
                        ? state.tasks.map(t => t.id === task.id ? task : t)
                        : [...state.tasks, task],
                      selectedTask: task,
                      isLoading: false,
                    }));
                  } catch (error) {
                    console.error('Failed to fetch task:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to fetch task',
                      isLoading: false,
                    });
                  }
                },
        
                createTask: async (taskData: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    const response = await taskApi.createTask(taskData);
                    const newTask = response.data;
                    
                    set((state) => ({
                      tasks: [newTask, ...state.tasks],
                      isLoading: false,
                    }));
                  } catch (error) {
                    console.error('Failed to create task:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to create task',
                      isLoading: false,
                    });
                    throw error;
                  }
                },
        
                updateTask: async (taskId: string, updates: Partial<Task>) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    const response = await taskApi.updateTask(taskId, updates);
                    const updatedTask = response.data;
                    
                    set((state) => ({
                      tasks: state.tasks.map(task =>
                        task.id === taskId ? updatedTask : task
                      ),
                      selectedTask: state.selectedTask?.id === taskId ? updatedTask : state.selectedTask,
                      isLoading: false,
                    }));
                  } catch (error) {
                    console.error('Failed to update task:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to update task',
                      isLoading: false,
                    });
                    throw error;
                  }
                },
        
                deleteTask: async (taskId: string) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    await taskApi.deleteTask(taskId);
                    
                    set((state) => ({
                      tasks: state.tasks.filter(task => task.id !== taskId),
                      selectedTask: state.selectedTask?.id === taskId ? null : state.selectedTask,
                      isLoading: false,
                    }));
                  } catch (error) {
                    console.error('Failed to delete task:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to delete task',
                      isLoading: false,
                    });
                    throw error;
                  }
                },
        
                executeTaskAction: async (payload: TaskActionPayload) => {
                  set({ isLoading: true, error: null });
                  
                  try {
                    const response = await taskApi.executeTaskAction(payload);
                    const updatedTask = response.data;
                    
                    set((state) => ({
                      tasks: state.tasks.map(task =>
                        task.id === payload.taskId ? updatedTask : task
                      ),
                      selectedTask: state.selectedTask?.id === payload.taskId ? updatedTask : state.selectedTask,
                      isLoading: false,
                    }));
                  } catch (error) {
                    console.error('Failed to execute task action:', error);
                    set({
                      error: error instanceof Error ? error.message : 'Failed to execute task action',
                      isLoading: false,
                    });
                    throw error;
                  }
                },

        // Filters and sorting
        setFilters: (filters: TaskFilters) => {
          set({ filters });
          // Auto-refresh with new filters
          const { sortOptions } = get();
          get().fetchTasks(filters, sortOptions);
        },

        setSortOptions: (sortOptions: TaskSortOptions) => {
          set({ sortOptions });
          // Auto-refresh with new sort
          const { filters } = get();
          get().fetchTasks(filters, sortOptions);
        },

        clearFilters: () => {
          set({ filters: defaultFilters });
          const { sortOptions } = get();
          get().fetchTasks(defaultFilters, sortOptions);
        },

        // Real-time updates
        enableRealTimeUpdates: () => {
          const { isRealTimeEnabled } = get();
          if (isRealTimeEnabled) return;
          
          const unsubscribe = taskApi.subscribeToTaskUpdates((event: TaskUpdateEvent) => {
            get().handleRealTimeUpdate(event);
          });
          
          set({ 
            isRealTimeEnabled: true,
            lastUpdate: new Date(),
          });
          
          // Store unsubscribe function for cleanup
          set({ unsubscribeFromUpdates: unsubscribe });
        },

        disableRealTimeUpdates: () => {
          const { isRealTimeEnabled } = get();
          if (!isRealTimeEnabled) return;
          
          const { unsubscribeFromUpdates: unsubscribe } = get();
          if (unsubscribe) {
            unsubscribe();
          }
          
          set({ isRealTimeEnabled: false, unsubscribeFromUpdates: undefined });
        },

        handleRealTimeUpdate: (event: TaskUpdateEvent) => {
          const { type, taskId, task, stepId, step } = event;
          
          set((state) => {
            let updatedTasks = [...state.tasks];
            let updatedSelectedTask = state.selectedTask;
            
            switch (type) {
              case 'task_created':
                if (task) {
                  updatedTasks = [task, ...updatedTasks];
                }
                break;
                
              case 'task_updated':
                if (task) {
                  updatedTasks = updatedTasks.map(t => 
                    t.id === taskId ? task : t
                  );
                  if (updatedSelectedTask?.id === taskId) {
                    updatedSelectedTask = task;
                  }
                }
                break;
                
              case 'task_deleted':
                updatedTasks = updatedTasks.filter(t => t.id !== taskId);
                if (updatedSelectedTask?.id === taskId) {
                  updatedSelectedTask = null;
                }
                break;
                
              case 'step_updated':
                if (task && stepId && step) {
                  updatedTasks = updatedTasks.map(t => {
                    if (t.id === taskId && t.steps) {
                      return {
                        ...t,
                        steps: t.steps.map(s => 
                          s.id === stepId ? step : s
                        ),
                        // Update overall progress based on steps
                        progress: task.progress,
                      };
                    }
                    return t;
                  });
                  
                  if (updatedSelectedTask?.id === taskId && updatedSelectedTask.steps) {
                    updatedSelectedTask = {
                      ...updatedSelectedTask,
                      steps: updatedSelectedTask.steps.map(s => 
                        s.id === stepId ? step : s
                      ),
                      progress: task.progress,
                    };
                  }
                }
                break;
            }
            
            return {
              tasks: updatedTasks,
              selectedTask: updatedSelectedTask,
              lastUpdate: new Date(),
            };
          });
        },

        // Statistics
        fetchStatistics: async () => {
          try {
            const response = await taskApi.fetchStatistics();
            set({ statistics: response.data });
          } catch (error) {
            console.error('Failed to fetch statistics:', error);
          }
        },

        // UI state
        setSelectedTask: (task: Task | null) => {
          set({ selectedTask: task });
        },

        setShowDetails: (show: boolean) => {
          set({ showDetails: show });
        },

        setShowFilters: (show: boolean) => {
          set({ showFilters: show });
        },

        setViewMode: (mode: 'list' | 'grid' | 'kanban') => {
          set({ viewMode: mode });
        },

        // Utility
        clearError: () => {
          set({ error: null });
        },

        reset: () => {
          // Disable real-time updates before resetting
          const { isRealTimeEnabled } = get();
          if (isRealTimeEnabled) {
            get().disableRealTimeUpdates();
          }
          
          set(initialState);
        },
      }),
      {
        name: 'task-store',
        partialize: (state) => ({
          filters: state.filters,
          sortOptions: state.sortOptions,
          viewMode: state.viewMode,
          isRealTimeEnabled: state.isRealTimeEnabled,
        }),
      }
    ),
    {
      name: 'task-store',
    }
  )
);

// Selectors for common state combinations
export const useTasks = () => useTaskStore((state) => state.tasks);
export const useSelectedTask = () => useTaskStore((state) => state.selectedTask);
export const useTaskLoading = () => useTaskStore((state) => state.isLoading);
export const useTaskError = () => useTaskStore((state) => state.error);
export const useTaskFilters = () => useTaskStore((state) => state.filters);
export const useTaskSortOptions = () => useTaskStore((state) => state.sortOptions);
export const useTaskStatistics = () => useTaskStore((state) => state.statistics);
export const useTaskViewMode = () => useTaskStore((state) => state.viewMode);
export const useRealTimeEnabled = () => useTaskStore((state) => state.isRealTimeEnabled);

// Action hooks
export const useTaskActions = () => useTaskStore((state) => ({
  fetchTasks: state.fetchTasks,
  fetchTask: state.fetchTask,
  createTask: state.createTask,
  updateTask: state.updateTask,
  deleteTask: state.deleteTask,
  executeTaskAction: state.executeTaskAction,
  setFilters: state.setFilters,
  setSortOptions: state.setSortOptions,
  clearFilters: state.clearFilters,
  enableRealTimeUpdates: state.enableRealTimeUpdates,
  disableRealTimeUpdates: state.disableRealTimeUpdates,
  fetchStatistics: state.fetchStatistics,
  setSelectedTask: state.setSelectedTask,
  setShowDetails: state.setShowDetails,
  setShowFilters: state.setShowFilters,
  setViewMode: state.setViewMode,
  clearError: state.clearError,
  reset: state.reset,
}));

// Utility functions
export const getTaskById = (id: string, tasks: Task[]): Task | undefined => {
  return tasks.find((task) => task.id === id);
};

export const getTasksByStatus = (status: Task['status'], tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.status === status);
};

export const getTasksByPriority = (priority: Task['priority'], tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.priority === priority);
};

export const getTasksByExecutionMode = (executionMode: Task['executionMode'], tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.executionMode === executionMode);
};

export const getRunningTasks = (tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.status === 'running');
};

export const getFailedTasks = (tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.status === 'failed');
};

export const getCompletedTasks = (tasks: Task[]): Task[] => {
  return tasks.filter((task) => task.status === 'completed');
};

export const getTaskStatistics = (tasks: Task[]) => {
  const total = tasks.length;
  const pending = tasks.filter(t => t.status === 'pending').length;
  const running = tasks.filter(t => t.status === 'running').length;
  const completed = tasks.filter(t => t.status === 'completed').length;
  const failed = tasks.filter(t => t.status === 'failed').length;
  const cancelled = tasks.filter(t => t.status === 'cancelled').length;
  const paused = tasks.filter(t => t.status === 'paused').length;
  
  const successRate = total > 0 ? (completed / total) * 100 : 0;
  
  const tasksByPriority = {
    low: tasks.filter(t => t.priority === 'low').length,
    medium: tasks.filter(t => t.priority === 'medium').length,
    high: tasks.filter(t => t.priority === 'high').length,
    critical: tasks.filter(t => t.priority === 'critical').length,
  };
  
  const tasksByExecutionMode = {
    native: tasks.filter(t => t.executionMode === 'native').length,
    langgraph: tasks.filter(t => t.executionMode === 'langgraph').length,
    deepagents: tasks.filter(t => t.executionMode === 'deepagents').length,
  };
  
  const tasksByAgent: Record<string, number> = {};
  tasks.forEach(task => {
    if (task.metadata?.agentUsed) {
      tasksByAgent[task.metadata.agentUsed] = (tasksByAgent[task.metadata.agentUsed] || 0) + 1;
    }
  });
  
  // Calculate average execution time for completed tasks
  const completedTasksWithDuration = tasks.filter(t => 
    t.status === 'completed' && t.startedAt && t.completedAt
  );
  const averageExecutionTime = completedTasksWithDuration.length > 0
    ? completedTasksWithDuration.reduce((sum, task) => {
        const duration = task.completedAt!.getTime() - task.startedAt!.getTime();
        return sum + duration;
      }, 0) / completedTasksWithDuration.length
    : 0;
  
  return {
    total,
    pending,
    running,
    completed,
    failed,
    cancelled,
    paused,
    averageExecutionTime,
    successRate,
    tasksByPriority,
    tasksByExecutionMode,
    tasksByAgent,
  };
};
