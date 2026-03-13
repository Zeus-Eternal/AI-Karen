// Type definitions for Task Management components

export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: Date;
  updatedAt: Date;
  dueDate?: Date;
  assignedTo?: string;
  createdBy: string;
  progress: number; // 0-100 percentage
  estimatedDuration?: number; // in minutes
  actualDuration?: number; // in minutes
  tags?: string[];
  dependencies?: string[]; // task IDs
  subtasks?: Task[];
  attachments?: Array<{
    id: string;
    name: string;
    size: string;
    type: string;
    url?: string;
  }>;
  metadata?: Record<string, any>;
}

export interface TaskFilter {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  assignedTo?: string[];
  tags?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  searchQuery?: string;
}

export interface TaskFormData {
  title: string;
  description: string;
  priority: TaskPriority;
  dueDate?: Date;
  assignedTo?: string;
  estimatedDuration?: number;
  tags?: string[];
  dependencies?: string[];
}

export interface TaskStats {
  totalTasks: number;
  completedTasks: number;
  inProgressTasks: number;
  pendingTasks: number;
  failedTasks: number;
  cancelledTasks: number;
  averageCompletionTime: number; // in minutes
  overdueTasks: number;
  highPriorityTasks: number;
}