/**
 * Task Management Module
 * Comprehensive task management system for CoPilot interface
 */

// Main component
export { TaskManagement } from './TaskManagement';

// UI Components
export { TaskCard, TaskGridCard, TaskKanbanCard } from './ui/TaskCard';
export { TaskDetails } from './ui/TaskDetails';
export { TaskFilters as TaskFiltersComponent, TaskSortOptions as TaskSortOptionsComponent, QuickFilters } from './ui/TaskFilters';
export { TaskProgressBar, StepProgressIndicator, ResourceUsageIndicator } from './ui/TaskProgressBar';
export { TaskActions, QuickTaskActions } from './ui/TaskActions';
export {
  TaskStatusBadge,
  TaskPriorityBadge,
  TaskExecutionModeBadge
} from './ui/TaskStatusBadge';

// Store
export {
  useTaskStore,
  useTasks,
  useSelectedTask,
  useTaskLoading,
  useTaskError,
  useTaskFilters,
  useTaskSortOptions,
  useTaskStatistics,
  useTaskViewMode,
  useTaskActions,
  useRealTimeEnabled,
  getTaskById,
  getTasksByStatus,
  getTasksByPriority,
  getTasksByExecutionMode,
  getRunningTasks,
  getFailedTasks,
  getCompletedTasks,
  getTaskStatistics,
} from './store/taskStore';

// Services
export { TaskApiService, taskApi } from './services/taskApi';

// Types
export type {
  Task,
  TaskStatus,
  TaskPriority,
  ExecutionMode,
  TaskStep,
  ResourceUsage,
  TaskMetadata,
  TaskFilters,
  TaskSortOptions,
  TaskListResponse,
  TaskStatistics,
  TaskUpdateEvent,
  TaskAction,
  TaskActionPayload,
  TaskManagementState,
  TaskManagementActions,
  TaskManagementStore,
  TaskManagementProps,
  TaskCardProps,
  TaskDetailsProps,
  TaskFiltersComponentProps,
  TaskProgressBarProps,
  TaskActionsProps,
  TaskStatusBadgeProps,
  TaskActionsProps as QuickTaskActionsProps,
} from './types';
