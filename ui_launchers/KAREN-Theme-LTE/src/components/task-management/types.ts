/**
 * Task Management Types
 * TypeScript interfaces for the CoPilot Task Management System
 */

// Task status enumeration
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';

// Task priority enumeration
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

// Execution mode enumeration
export type ExecutionMode = 'native' | 'langgraph' | 'deepagents';

// Task step interface for multi-step tasks
export interface TaskStep {
  id: string;
  name: string;
  description?: string;
  status: TaskStatus;
  progress: number; // 0-100
  startTime?: Date;
  endTime?: Date;
  duration?: number; // in milliseconds
  error?: string;
  metadata?: Record<string, unknown>;
}

// Resource usage metrics
export interface ResourceUsage {
  cpu: number; // percentage
  memory: number; // in MB
  tokens?: number; // for AI tasks
  apiCalls?: number;
  networkRequests?: number;
}

// Task metadata
export interface TaskMetadata {
  agentUsed?: string;
  agentVersion?: string;
  modelUsed?: string;
  temperature?: number;
  maxTokens?: number;
  plugins?: string[];
  tags?: string[];
  category?: string;
  estimatedDuration?: number; // in milliseconds
  actualDuration?: number; // in milliseconds
  retryCount?: number;
  parentTaskId?: string;
  childTaskIds?: string[];
  correlationId?: string;
}

// Main task interface
export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  executionMode: ExecutionMode;
  createdAt: Date;
  updatedAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  progress: number; // 0-100
  steps?: TaskStep[];
  metadata?: TaskMetadata;
  resourceUsage?: ResourceUsage;
  error?: string;
  result?: unknown;
  userId?: string;
  sessionId?: string;
  tenantId?: string;
}

// Task filter options
export interface TaskFilters {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  executionMode?: ExecutionMode[];
  agent?: string[];
  category?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  search?: string;
}

// Task sort options
export interface TaskSortOptions {
  field: 'createdAt' | 'updatedAt' | 'priority' | 'progress' | 'title';
  direction: 'asc' | 'desc';
}

// Task list response
export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Task statistics
export interface TaskStatistics {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  paused: number;
  averageExecutionTime: number;
  successRate: number;
  tasksByPriority: Record<TaskPriority, number>;
  tasksByExecutionMode: Record<ExecutionMode, number>;
  tasksByAgent: Record<string, number>;
}

// Real-time task update event
export interface TaskUpdateEvent {
  type: 'task_created' | 'task_updated' | 'task_deleted' | 'step_updated';
  taskId: string;
  task?: Task;
  stepId?: string;
  step?: TaskStep;
  timestamp: Date;
}

// Task action types
export type TaskAction = 'view' | 'cancel' | 'retry' | 'delete' | 'pause' | 'resume';

// Task action payload
export interface TaskActionPayload {
  taskId: string;
  action: TaskAction;
  data?: Record<string, unknown>;
}

// Task management store state
export interface TaskManagementState {
  // Tasks
  tasks: Task[];
  selectedTask: Task | null;
  isLoading: boolean;
  error: string | null;
  
  // Filters and sorting
  filters: TaskFilters;
  sortOptions: TaskSortOptions;
  
  // Real-time updates
  isRealTimeEnabled: boolean;
  lastUpdate: Date | null;
  
  // Statistics
  statistics: TaskStatistics | null;
  
  // UI state
  showDetails: boolean;
  showFilters: boolean;
  viewMode: 'list' | 'grid' | 'kanban';
}

// Task management store actions
export interface TaskManagementActions {
  // Task operations
  fetchTasks: (filters?: TaskFilters, sort?: TaskSortOptions) => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  createTask: (task: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  executeTaskAction: (payload: TaskActionPayload) => Promise<void>;
  
  // Filters and sorting
  setFilters: (filters: TaskFilters) => void;
  setSortOptions: (sortOptions: TaskSortOptions) => void;
  clearFilters: () => void;
  
  // Real-time updates
  enableRealTimeUpdates: () => void;
  disableRealTimeUpdates: () => void;
  handleRealTimeUpdate: (event: TaskUpdateEvent) => void;
  
  // Statistics
  fetchStatistics: () => Promise<void>;
  
  // UI state
  setSelectedTask: (task: Task | null) => void;
  setShowDetails: (show: boolean) => void;
  setShowFilters: (show: boolean) => void;
  setViewMode: (mode: 'list' | 'grid' | 'kanban') => void;
  
  // Utility
  clearError: () => void;
  reset: () => void;
}

// Task management store (combined state and actions)
export type TaskManagementStore = TaskManagementState & TaskManagementActions;

// Props for TaskManagement component
export interface TaskManagementProps {
  className?: string;
  onTaskSelect?: (task: Task) => void;
  onTaskAction?: (payload: TaskActionPayload) => void;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

// Props for TaskCard component
export interface TaskCardProps {
  task: Task;
  onSelect?: (task: Task) => void;
  onAction?: (payload: TaskActionPayload) => void;
  showSteps?: boolean;
  compact?: boolean;
  className?: string;
}

// Props for TaskDetails component
export interface TaskDetailsProps {
  task: Task;
  onClose?: () => void;
  onAction?: (payload: TaskActionPayload) => void;
  showActions?: boolean;
  className?: string;
}

// Props for TaskFilters component
export interface TaskFiltersComponentProps {
  filters: TaskFilters;
  onFiltersChange: (filters: TaskFilters) => void;
  onClear: () => void;
  className?: string;
}

// Props for TaskProgressBar component
export interface TaskProgressBarProps {
  task: Task;
  showSteps?: boolean;
  compact?: boolean;
  className?: string;
}

// Props for TaskActions component
export interface TaskActionsProps {
  task: Task;
  onAction: (payload: TaskActionPayload) => void;
  compact?: boolean;
  className?: string;
}

// Props for TaskStatusBadge component
export interface TaskStatusBadgeProps {
  status: TaskStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}
