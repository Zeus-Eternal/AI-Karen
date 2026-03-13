import { Task, TaskStatus, TaskPriority, TaskFilter, TaskStats, TaskFormData } from '../components/task/types';

// Storage key for localStorage
const TASKS_STORAGE_KEY = 'copilot-tasks';

type StoredTask = Omit<Task, 'createdAt' | 'updatedAt' | 'dueDate' | 'subtasks'> & {
  createdAt: string | Date;
  updatedAt: string | Date;
  dueDate?: string | Date;
  subtasks?: StoredTask[];
};

/**
 * Service for managing tasks with persistence and API communication
 */
export class TaskService {
  private static toTask(task: StoredTask): Task {
    return {
      ...task,
      createdAt: new Date(task.createdAt),
      updatedAt: new Date(task.updatedAt),
      dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
      subtasks: task.subtasks?.map(subtask => this.toTask(subtask))
    };
  }

  /**
   * Get all tasks from storage
   */
  static getTasks(): Task[] {
    if (typeof window === 'undefined') {
      return [];
    }
    
    try {
      const stored = localStorage.getItem(TASKS_STORAGE_KEY);
      if (!stored) {
        return [];
      }
      
      const parsedTasks = JSON.parse(stored) as unknown;

      if (!Array.isArray(parsedTasks)) {
        return [];
      }

      // Convert date strings back to Date objects
      return parsedTasks.map(task => this.toTask(task as StoredTask));
    } catch (error) {
      console.error('Failed to parse tasks from storage:', error);
      return [];
    }
  }
  
  /**
   * Save tasks to storage
   */
  static saveTasks(tasks: Task[]): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.setItem(TASKS_STORAGE_KEY, JSON.stringify(tasks));
    } catch (error) {
      console.error('Failed to save tasks to storage:', error);
    }
  }
  
  /**
   * Get a task by ID
   */
  static getTaskById(id: string): Task | null {
    const tasks = this.getTasks();
    return tasks.find(task => task.id === id) || null;
  }
  
  /**
   * Create a new task
   */
  static createTask(taskData: TaskFormData, createdBy: string): Task {
    const newTask: Task = {
      id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title: taskData.title,
      description: taskData.description,
      status: TaskStatus.PENDING,
      priority: taskData.priority,
      createdAt: new Date(),
      updatedAt: new Date(),
      dueDate: taskData.dueDate,
      assignedTo: taskData.assignedTo,
      createdBy,
      progress: 0,
      estimatedDuration: taskData.estimatedDuration,
      tags: taskData.tags,
      dependencies: taskData.dependencies
    };
    
    const tasks = this.getTasks();
    tasks.unshift(newTask); // Add to beginning
    this.saveTasks(tasks);
    
    return newTask;
  }
  
  /**
   * Update a task
   */
  static updateTask(id: string, updates: Partial<Task>): Task | null {
    const tasks = this.getTasks();
    const index = tasks.findIndex(task => task.id === id);
    
    if (index === -1) {
      return null;
    }
    
    const existingTask = tasks[index];
    if (!existingTask) {
      return null;
    }

    const updatedTask = {
      ...existingTask,
      ...updates,
      updatedAt: new Date()
    };
    
    tasks[index] = updatedTask;
    this.saveTasks(tasks);
    
    return updatedTask;
  }
  
  /**
   * Delete a task
   */
  static deleteTask(id: string): boolean {
    const tasks = this.getTasks();
    const filteredTasks = tasks.filter(task => task.id !== id);
    
    if (filteredTasks.length === tasks.length) {
      return false; // Task not found
    }
    
    this.saveTasks(filteredTasks);
    return true;
  }
  
  /**
   * Update task status
   */
  static updateTaskStatus(id: string, status: TaskStatus): Task | null {
    const task = this.getTaskById(id);
    if (!task) {
      return null;
    }
    
    // Calculate actual duration when completing a task
    let actualDuration = task.actualDuration;
    if (status === TaskStatus.COMPLETED && task.status !== TaskStatus.COMPLETED) {
      const now = new Date();
      actualDuration = Math.round((now.getTime() - task.createdAt.getTime()) / 60000); // minutes
    }
    
    return this.updateTask(id, {
      status,
      actualDuration,
      progress: status === TaskStatus.COMPLETED ? 100 : task.progress
    });
  }
  
  /**
   * Update task progress
   */
  static updateTaskProgress(id: string, progress: number): Task | null {
    if (progress < 0 || progress > 100) {
      throw new Error('Progress must be between 0 and 100');
    }
    
    const task = this.getTaskById(id);
    if (!task) {
      return null;
    }
    
    // Auto-update status based on progress
    let status = task.status;
    if (progress === 0 && status !== TaskStatus.PENDING) {
      status = TaskStatus.PENDING;
    } else if (progress > 0 && progress < 100 && status !== TaskStatus.IN_PROGRESS) {
      status = TaskStatus.IN_PROGRESS;
    } else if (progress === 100 && status !== TaskStatus.COMPLETED) {
      status = TaskStatus.COMPLETED;
    }
    
    return this.updateTask(id, {
      progress,
      status
    });
  }
  
  /**
   * Cancel a task
   */
  static cancelTask(id: string): Task | null {
    return this.updateTaskStatus(id, TaskStatus.CANCELLED);
  }
  
  /**
   * Filter tasks based on filter criteria
   */
  static filterTasks(filter: TaskFilter): Task[] {
    let tasks = this.getTasks();
    
    if (filter.status && filter.status.length > 0) {
      tasks = tasks.filter(task => filter.status!.includes(task.status));
    }
    
    if (filter.priority && filter.priority.length > 0) {
      tasks = tasks.filter(task => filter.priority!.includes(task.priority));
    }
    
    if (filter.assignedTo && filter.assignedTo.length > 0) {
      tasks = tasks.filter(task => 
        task.assignedTo && filter.assignedTo!.includes(task.assignedTo)
      );
    }
    
    if (filter.tags && filter.tags.length > 0) {
      tasks = tasks.filter(task => 
        task.tags && task.tags.some(tag => filter.tags!.includes(tag))
      );
    }
    
    if (filter.dateRange) {
      const { start, end } = filter.dateRange;
      tasks = tasks.filter(task => {
        const taskDate = new Date(task.createdAt);
        return taskDate >= start && taskDate <= end;
      });
    }
    
    if (filter.searchQuery) {
      const query = filter.searchQuery.toLowerCase();
      tasks = tasks.filter(task => 
        task.title.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query) ||
        (task.tags && task.tags.some(tag => tag.toLowerCase().includes(query)))
      );
    }
    
    return tasks;
  }
  
  /**
   * Get task statistics
   */
  static getTaskStats(): TaskStats {
    const tasks = this.getTasks();
    
    const stats: TaskStats = {
      totalTasks: tasks.length,
      completedTasks: 0,
      inProgressTasks: 0,
      pendingTasks: 0,
      failedTasks: 0,
      cancelledTasks: 0,
      averageCompletionTime: 0,
      overdueTasks: 0,
      highPriorityTasks: 0
    };
    
    const completedTasks: Task[] = [];
    
    tasks.forEach(task => {
      switch (task.status) {
        case TaskStatus.COMPLETED:
          stats.completedTasks++;
          completedTasks.push(task);
          break;
        case TaskStatus.IN_PROGRESS:
          stats.inProgressTasks++;
          break;
        case TaskStatus.PENDING:
          stats.pendingTasks++;
          break;
        case TaskStatus.FAILED:
          stats.failedTasks++;
          break;
        case TaskStatus.CANCELLED:
          stats.cancelledTasks++;
          break;
      }
      
      if (task.priority === TaskPriority.HIGH || task.priority === TaskPriority.URGENT) {
        stats.highPriorityTasks++;
      }
      
      // Check if task is overdue
      if (task.dueDate && task.status !== TaskStatus.COMPLETED && task.status !== TaskStatus.CANCELLED) {
        const now = new Date();
        if (now > task.dueDate) {
          stats.overdueTasks++;
        }
      }
    });
    
    // Calculate average completion time
    if (completedTasks.length > 0) {
      const totalTime = completedTasks.reduce((sum, task) => {
        return sum + (task.actualDuration || 0);
      }, 0);
      stats.averageCompletionTime = Math.round(totalTime / completedTasks.length);
    }
    
    return stats;
  }
  
  /**
   * Get tasks by status
   */
  static getTasksByStatus(status: TaskStatus): Task[] {
    const tasks = this.getTasks();
    return tasks.filter(task => task.status === status);
  }
  
  /**
   * Get tasks by priority
   */
  static getTasksByPriority(priority: TaskPriority): Task[] {
    const tasks = this.getTasks();
    return tasks.filter(task => task.priority === priority);
  }
  
  /**
   * Get tasks assigned to a user
   */
  static getTasksByAssignedTo(assignedTo: string): Task[] {
    const tasks = this.getTasks();
    return tasks.filter(task => task.assignedTo === assignedTo);
  }
  
  /**
   * Get overdue tasks
   */
  static getOverdueTasks(): Task[] {
    const tasks = this.getTasks();
    const now = new Date();
    
    return tasks.filter(task => 
      task.dueDate && 
      task.status !== TaskStatus.COMPLETED && 
      task.status !== TaskStatus.CANCELLED &&
      now > task.dueDate
    );
  }
  
  /**
   * Get tasks due within a certain number of days
   */
  static getTasksDueWithinDays(days: number): Task[] {
    const tasks = this.getTasks();
    const now = new Date();
    const futureDate = new Date();
    futureDate.setDate(now.getDate() + days);
    
    return tasks.filter(task => 
      task.dueDate && 
      task.status !== TaskStatus.COMPLETED && 
      task.status !== TaskStatus.CANCELLED &&
      task.dueDate >= now && 
      task.dueDate <= futureDate
    );
  }
  
  /**
   * Export tasks to JSON
   */
  static exportTasks(): string | null {
    const tasks = this.getTasks();
    
    try {
      return JSON.stringify(tasks, null, 2);
    } catch (error) {
      console.error('Failed to export tasks:', error);
      return null;
    }
  }
  
  /**
   * Import tasks from JSON
   */
  static importTasks(jsonData: string): Task[] | null {
    try {
      const importedTasks = JSON.parse(jsonData) as unknown;
      
      // Validate required fields
      if (!Array.isArray(importedTasks)) {
        throw new Error('Invalid tasks format');
      }
      
      // Convert date strings back to Date objects
      const tasks = importedTasks.map(task => this.toTask(task as StoredTask));
      
      // Save the imported tasks
      this.saveTasks(tasks);
      
      return tasks;
    } catch (error) {
      console.error('Failed to import tasks:', error);
      return null;
    }
  }
  
  /**
   * Clear all tasks
   */
  static clearAllTasks(): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.removeItem(TASKS_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear tasks from storage:', error);
    }
  }
}
