/**
 * Task Types for CoPilot Architecture
 * 
 * This file defines the TypeScript interfaces and types used throughout
 * the Task Management UI components.
 */

/**
 * Task execution mode
 */
export type ExecutionMode = 'native' | 'deepagents' | 'langgraph';

/**
 * Task status
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'cancelled' | 'failed';

/**
 * Task type
 */
export type TaskType = 
  | 'text_transform'
  | 'code_analysis'
  | 'file_operation'
  | 'data_processing'
  | 'research'
  | 'custom';

/**
 * Task priority
 */
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Task progress information
 */
export interface TaskProgress {
  /** Current progress percentage (0-100) */
  percentage: number;
  /** Current step description */
  currentStep: string;
  /** Total number of steps */
  totalSteps: number;
  /** Current step number */
  currentStepNumber: number;
  /** Estimated time remaining in seconds */
  estimatedTimeRemaining?: number;
  /** Additional progress metadata */
  metadata?: Record<string, any>;
}

/**
 * Task interface
 */
export interface Task {
  /** Unique identifier for the task */
  id: string;
  /** Session identifier */
  sessionId: string;
  /** Thread identifier */
  threadId?: string;
  /** Task type */
  type: TaskType;
  /** Task title */
  title: string;
  /** Task description */
  description?: string;
  /** Task parameters */
  parameters: Record<string, any>;
  /** Execution mode */
  executionMode: ExecutionMode;
  /** Task status */
  status: TaskStatus;
  /** Task priority */
  priority: TaskPriority;
  /** Creation timestamp */
  createdAt: Date;
  /** Start timestamp */
  startedAt?: Date;
  /** Completion timestamp */
  completedAt?: Date;
  /** Progress information */
  progress?: TaskProgress;
  /** Task result */
  result?: any;
  /** Error message if failed */
  error?: string;
  /** Task tags */
  tags?: string[];
  /** Task dependencies */
  dependencies?: string[];
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Task creation parameters
 */
export interface TaskCreationParams {
  /** Task type */
  type: TaskType;
  /** Task title */
  title: string;
  /** Task description */
  description?: string;
  /** Task parameters */
  parameters: Record<string, any>;
  /** Execution mode */
  executionMode?: ExecutionMode;
  /** Task priority */
  priority?: TaskPriority;
  /** Task tags */
  tags?: string[];
  /** Task dependencies */
  dependencies?: string[];
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Task filter options
 */
export interface TaskFilterOptions {
  /** Task status filter */
  status?: TaskStatus[];
  /** Task type filter */
  type?: TaskType[];
  /** Execution mode filter */
  executionMode?: ExecutionMode[];
  /** Priority filter */
  priority?: TaskPriority[];
  /** Tag filter */
  tags?: string[];
  /** Date range filter */
  dateRange?: {
    start?: Date;
    end?: Date;
  };
  /** Search query */
  searchQuery?: string;
}

/**
 * Task sort options
 */
export interface TaskSortOptions {
  /** Sort field */
  field: keyof Task;
  /** Sort direction */
  direction: 'asc' | 'desc';
}

/**
 * Task list view options
 */
export interface TaskListViewOptions {
  /** Filter options */
  filters?: TaskFilterOptions;
  /** Sort options */
  sort?: TaskSortOptions;
  /** Pagination options */
  pagination?: {
    page: number;
    pageSize: number;
  };
}

/**
 * Task creation form state
 */
export interface TaskCreationFormState {
  /** Task type */
  type: TaskType;
  /** Task title */
  title: string;
  /** Task description */
  description: string;
  /** Task parameters */
  parameters: Record<string, any>;
  /** Execution mode */
  executionMode: ExecutionMode;
  /** Task priority */
  priority: TaskPriority;
  /** Task tags */
  tags: string[];
  /** Form validation errors */
  errors: Record<string, string>;
  /** Form submission state */
  isSubmitting: boolean;
}