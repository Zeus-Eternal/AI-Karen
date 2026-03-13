import { useState, useEffect, useCallback, useRef } from 'react';
import { Task, TaskStatus, TaskPriority, TaskFilter, TaskStats, TaskFormData } from '../components/task/types';
import { TaskService } from '../services/TaskService';

interface UseTaskManagementOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  persistTasks?: boolean;
}

interface UseTaskManagementResult {
  // Task state
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
  
  // Filter state
  activeFilter: TaskFilter;
  filteredTasks: Task[];
  
  // Stats
  stats: TaskStats;
  
  // Actions
  createTask: (taskData: TaskFormData, createdBy?: string) => Task;
  updateTask: (taskId: string, updates: Partial<Task>) => Task | null;
  deleteTask: (taskId: string) => boolean;
  updateTaskStatus: (taskId: string, status: TaskStatus) => Task | null;
  updateTaskProgress: (taskId: string, progress: number) => Task | null;
  cancelTask: (taskId: string) => Task | null;
  
  // Filter actions
  setFilter: (filter: TaskFilter) => void;
  resetFilter: () => void;
  
  // Utility actions
  refreshTasks: () => void;
  exportTasks: () => string | null;
  importTasks: (jsonData: string) => Task[] | null;
  clearAllTasks: () => void;
  
  // Getters
  getTaskById: (taskId: string) => Task | null;
  getTasksByStatus: (status: TaskStatus) => Task[];
  getTasksByPriority: (priority: TaskPriority) => Task[];
  getOverdueTasks: () => Task[];
  getTasksDueWithinDays: (days: number) => Task[];
}

/**
 * React hook for managing task state and operations
 */
export const useTaskManagement = (options: UseTaskManagementOptions = {}): UseTaskManagementResult => {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    persistTasks = true
  } = options;
  
  // State
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<TaskFilter>({});
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats>({
    totalTasks: 0,
    completedTasks: 0,
    inProgressTasks: 0,
    pendingTasks: 0,
    failedTasks: 0,
    cancelledTasks: 0,
    averageCompletionTime: 0,
    overdueTasks: 0,
    highPriorityTasks: 0
  });
  
  // Refs
  const isMountedRef = useRef(true);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Load tasks from storage
  const loadTasks = useCallback(() => {
    if (!persistTasks) {
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const loadedTasks = TaskService.getTasks();
      setTasks(loadedTasks);
      
      // Update stats
      const taskStats = TaskService.getTaskStats();
      setStats(taskStats);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      setError('Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  }, [persistTasks]);
  
  // Apply filter to tasks
  const applyFilter = useCallback((filter: TaskFilter) => {
    try {
      const filtered = TaskService.filterTasks(filter);
      setFilteredTasks(filtered);
    } catch (err) {
      console.error('Failed to filter tasks:', err);
      setError('Failed to filter tasks');
      setFilteredTasks(tasks);
    }
  }, [tasks]);
  
  // Initialize
  useEffect(() => {
    loadTasks();
    
    return () => {
      isMountedRef.current = false;
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [loadTasks]);
  
  // Set up auto refresh
  useEffect(() => {
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        loadTasks();
      }, refreshInterval);
    }
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, loadTasks]);
  
  // Apply filter when tasks or filter changes
  useEffect(() => {
    applyFilter(activeFilter);
  }, [tasks, activeFilter, applyFilter]);
  
  // Create a new task
  const createTask = useCallback((taskData: TaskFormData, createdBy = 'user'): Task => {
    try {
      const newTask = TaskService.createTask(taskData, createdBy);
      
      if (isMountedRef.current) {
        setTasks(prev => [newTask, ...prev]);
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return newTask;
    } catch (err) {
      console.error('Failed to create task:', err);
      setError('Failed to create task');
      throw err;
    }
  }, []);
  
  // Update a task
  const updateTask = useCallback((taskId: string, updates: Partial<Task>): Task | null => {
    try {
      const updatedTask = TaskService.updateTask(taskId, updates);
      
      if (updatedTask && isMountedRef.current) {
        setTasks(prev => 
          prev.map(task => task.id === taskId ? updatedTask : task)
        );
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return updatedTask;
    } catch (err) {
      console.error('Failed to update task:', err);
      setError('Failed to update task');
      return null;
    }
  }, []);
  
  // Delete a task
  const deleteTask = useCallback((taskId: string): boolean => {
    try {
      const success = TaskService.deleteTask(taskId);
      
      if (success && isMountedRef.current) {
        setTasks(prev => prev.filter(task => task.id !== taskId));
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return success;
    } catch (err) {
      console.error('Failed to delete task:', err);
      setError('Failed to delete task');
      return false;
    }
  }, []);
  
  // Update task status
  const updateTaskStatus = useCallback((taskId: string, status: TaskStatus): Task | null => {
    try {
      const updatedTask = TaskService.updateTaskStatus(taskId, status);
      
      if (updatedTask && isMountedRef.current) {
        setTasks(prev => 
          prev.map(task => task.id === taskId ? updatedTask : task)
        );
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return updatedTask;
    } catch (err) {
      console.error('Failed to update task status:', err);
      setError('Failed to update task status');
      return null;
    }
  }, []);
  
  // Update task progress
  const updateTaskProgress = useCallback((taskId: string, progress: number): Task | null => {
    try {
      const updatedTask = TaskService.updateTaskProgress(taskId, progress);
      
      if (updatedTask && isMountedRef.current) {
        setTasks(prev => 
          prev.map(task => task.id === taskId ? updatedTask : task)
        );
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return updatedTask;
    } catch (err) {
      console.error('Failed to update task progress:', err);
      setError('Failed to update task progress');
      return null;
    }
  }, []);
  
  // Cancel a task
  const cancelTask = useCallback((taskId: string): Task | null => {
    return updateTaskStatus(taskId, TaskStatus.CANCELLED);
  }, [updateTaskStatus]);
  
  // Set filter
  const setFilter = useCallback((filter: TaskFilter) => {
    setActiveFilter(filter);
  }, []);
  
  // Reset filter
  const resetFilter = useCallback(() => {
    setActiveFilter({});
  }, []);
  
  // Refresh tasks
  const refreshTasks = useCallback(() => {
    loadTasks();
  }, [loadTasks]);
  
  // Export tasks
  const exportTasks = useCallback((): string | null => {
    try {
      return TaskService.exportTasks();
    } catch (err) {
      console.error('Failed to export tasks:', err);
      setError('Failed to export tasks');
      return null;
    }
  }, []);
  
  // Import tasks
  const importTasks = useCallback((jsonData: string): Task[] | null => {
    try {
      const importedTasks = TaskService.importTasks(jsonData);
      
      if (importedTasks && isMountedRef.current) {
        setTasks(importedTasks);
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
      
      return importedTasks;
    } catch (err) {
      console.error('Failed to import tasks:', err);
      setError('Failed to import tasks');
      return null;
    }
  }, []);
  
  // Clear all tasks
  const clearAllTasks = useCallback(() => {
    try {
      TaskService.clearAllTasks();
      
      if (isMountedRef.current) {
        setTasks([]);
        
        // Update stats
        const taskStats = TaskService.getTaskStats();
        setStats(taskStats);
      }
    } catch (err) {
      console.error('Failed to clear tasks:', err);
      setError('Failed to clear tasks');
    }
  }, []);
  
  // Get task by ID
  const getTaskById = useCallback((taskId: string): Task | null => {
    return tasks.find(task => task.id === taskId) || null;
  }, [tasks]);
  
  // Get tasks by status
  const getTasksByStatus = useCallback((status: TaskStatus): Task[] => {
    return tasks.filter(task => task.status === status);
  }, [tasks]);
  
  // Get tasks by priority
  const getTasksByPriority = useCallback((priority: TaskPriority): Task[] => {
    return tasks.filter(task => task.priority === priority);
  }, [tasks]);
  
  // Get overdue tasks
  const getOverdueTasks = useCallback((): Task[] => {
    return TaskService.getOverdueTasks();
  }, [tasks]);
  
  // Get tasks due within days
  const getTasksDueWithinDays = useCallback((days: number): Task[] => {
    return TaskService.getTasksDueWithinDays(days);
  }, [tasks]);
  
  return {
    // Task state
    tasks,
    isLoading,
    error,
    
    // Filter state
    activeFilter,
    filteredTasks,
    
    // Stats
    stats,
    
    // Actions
    createTask,
    updateTask,
    deleteTask,
    updateTaskStatus,
    updateTaskProgress,
    cancelTask,
    
    // Filter actions
    setFilter,
    resetFilter,
    
    // Utility actions
    refreshTasks,
    exportTasks,
    importTasks,
    clearAllTasks,
    
    // Getters
    getTaskById,
    getTasksByStatus,
    getTasksByPriority,
    getOverdueTasks,
    getTasksDueWithinDays
  };
};

export default useTaskManagement;