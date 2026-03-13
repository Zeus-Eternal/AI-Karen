import React, { useState, useMemo } from 'react';
import { Task, TaskStatus, TaskType, ExecutionMode, TaskPriority, TaskFilterOptions, TaskSortOptions } from '../../types/task';

/**
 * TaskList Component
 * 
 * Displays a list of tasks with filtering, sorting, and pagination capabilities.
 * Allows users to view, select, and manage tasks.
 * 
 * @component
 * @example
 * ```tsx
 * <TaskList 
 *   tasks={allTasks}
 *   onTaskSelect={(taskId) => console.log('Selected task:', taskId)}
 *   onTaskCancelled={(taskId) => console.log('Cancelled task:', taskId)}
 *   onViewTask={() => console.log('View task details')}
 * />
 * ```
 */
export const TaskList: React.FC<TaskListProps> = ({ 
  tasks,
  onTaskSelect,
  onTaskCancelled,
  onViewTask,
  className = ''
}) => {
  const [filters, setFilters] = useState<TaskFilterOptions>({});
  const [sort, setSort] = useState<TaskSortOptions>({ field: 'createdAt', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [showCancellationDialog, setShowCancellationDialog] = useState<string | null>(null);

  // Filter tasks based on filter options
  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      // Status filter
      if (filters.status && filters.status.length > 0 && !filters.status.includes(task.status)) {
        return false;
      }
      
      // Type filter
      if (filters.type && filters.type.length > 0 && !filters.type.includes(task.type)) {
        return false;
      }
      
      // Execution mode filter
      if (filters.executionMode && filters.executionMode.length > 0 && !filters.executionMode.includes(task.executionMode)) {
        return false;
      }
      
      // Priority filter
      if (filters.priority && filters.priority.length > 0 && !filters.priority.includes(task.priority)) {
        return false;
      }
      
      // Tag filter
      if (filters.tags && filters.tags.length > 0) {
        const hasMatchingTag = filters.tags.some(tag => 
          task.tags?.includes(tag)
        );
        if (!hasMatchingTag) {
          return false;
        }
      }
      
      // Date range filter
      if (filters.dateRange) {
        const taskDate = new Date(task.createdAt);
        if (filters.dateRange.start && taskDate < filters.dateRange.start) {
          return false;
        }
        if (filters.dateRange.end && taskDate > filters.dateRange.end) {
          return false;
        }
      }
      
      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const titleMatch = task.title.toLowerCase().includes(query);
        const descriptionMatch = task.description?.toLowerCase().includes(query);
        const tagMatch = task.tags?.some(tag => tag.toLowerCase().includes(query));
        
        if (!titleMatch && !descriptionMatch && !tagMatch) {
          return false;
        }
      }
      
      return true;
    });
  }, [tasks, filters]);

  // Sort tasks based on sort options
  const sortedTasks = useMemo(() => {
    return [...filteredTasks].sort((a, b) => {
      const aValue = a[sort.field];
      const bValue = b[sort.field];
      
      // Handle different value types
      if (aValue instanceof Date && bValue instanceof Date) {
        return sort.direction === 'asc' 
          ? aValue.getTime() - bValue.getTime()
          : bValue.getTime() - aValue.getTime();
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sort.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      // Default comparison for numbers or other types
      return sort.direction === 'asc'
        ? (aValue as any) - (bValue as any)
        : (bValue as any) - (aValue as any);
    });
  }, [filteredTasks, sort]);

  // Paginate tasks
  const paginatedTasks = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedTasks.slice(startIndex, startIndex + pageSize);
  }, [sortedTasks, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedTasks.length / pageSize);

  const handleSort = (field: keyof Task) => {
    setSort(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleCancelTask = (taskId: string) => {
    setShowCancellationDialog(taskId);
  };

  const handleConfirmCancellation = (taskId: string) => {
    onTaskCancelled(taskId);
    setShowCancellationDialog(null);
  };

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'running': return 'status-running';
      case 'completed': return 'status-completed';
      case 'cancelled': return 'status-cancelled';
      case 'failed': return 'status-failed';
      default: return '';
    }
  };

  const getPriorityColor = (priority: TaskPriority) => {
    switch (priority) {
      case 'low': return 'priority-low';
      case 'medium': return 'priority-medium';
      case 'high': return 'priority-high';
      case 'critical': return 'priority-critical';
      default: return '';
    }
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString();
  };

  return (
    <div className={`task-list ${className}`}>
      <div className="task-list-header">
        <h3>Tasks</h3>
        <div className="task-count">
          Showing {paginatedTasks.length} of {sortedTasks.length} tasks
        </div>
      </div>

      {/* Filters */}
      <div className="task-filters">
        <div className="filter-group">
          <label htmlFor="search-query">Search</label>
          <input
            id="search-query"
            type="text"
            placeholder="Search tasks..."
            value={filters.searchQuery || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="status-filter">Status</label>
          <select
            id="status-filter"
            value={filters.status?.[0] || ''}
            onChange={(e) => setFilters(prev => ({ 
              ...prev, 
              status: e.target.value ? [e.target.value as TaskStatus] : undefined 
            }))}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="type-filter">Type</label>
          <select
            id="type-filter"
            value={filters.type?.[0] || ''}
            onChange={(e) => setFilters(prev => ({ 
              ...prev, 
              type: e.target.value ? [e.target.value as TaskType] : undefined 
            }))}
          >
            <option value="">All Types</option>
            <option value="text_transform">Text Transform</option>
            <option value="code_analysis">Code Analysis</option>
            <option value="file_operation">File Operation</option>
            <option value="data_processing">Data Processing</option>
            <option value="research">Research</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sort-field">Sort By</label>
          <select
            id="sort-field"
            value={sort.field}
            onChange={(e) => handleSort(e.target.value as keyof Task)}
          >
            <option value="createdAt">Created Date</option>
            <option value="title">Title</option>
            <option value="status">Status</option>
            <option value="priority">Priority</option>
            <option value="type">Type</option>
          </select>
          <button
            className="sort-direction"
            onClick={() => setSort(prev => ({ 
              ...prev, 
              direction: prev.direction === 'asc' ? 'desc' : 'asc' 
            }))}
            aria-label={`Sort ${sort.direction === 'asc' ? 'descending' : 'ascending'}`}
          >
            {sort.direction === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Task Table */}
      <div className="task-table-container">
        <table className="task-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Type</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedTasks.map(task => (
              <tr 
                key={task.id} 
                className={task.id === showCancellationDialog ? 'selected' : ''}
                onClick={() => onTaskSelect(task.id)}
              >
                <td className="task-title">
                  <div className="title-text">{task.title}</div>
                  {task.description && (
                    <div className="task-description">{task.description}</div>
                  )}
                </td>
                <td className="task-type">{task.type}</td>
                <td className={`task-status ${getStatusColor(task.status)}`}>
                  {task.status}
                </td>
                <td className={`task-priority ${getPriorityColor(task.priority)}`}>
                  {task.priority}
                </td>
                <td className="task-date">{formatDate(task.createdAt)}</td>
                <td className="task-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onTaskSelect(task.id);
                      onViewTask();
                    }}
                    aria-label={`View details for ${task.title}`}
                  >
                    View
                  </button>
                  {(task.status === 'pending' || task.status === 'running') && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelTask(task.id);
                      }}
                      className="cancel-button"
                      aria-label={`Cancel ${task.title}`}
                    >
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {paginatedTasks.length === 0 && (
          <div className="no-tasks">
            No tasks found matching the current filters.
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="task-pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            aria-label="Previous page"
          >
            Previous
          </button>
          
          <div className="page-info">
            Page {currentPage} of {totalPages}
          </div>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      )}

      {/* Task Cancellation Dialog */}
      {showCancellationDialog && (
        <TaskCancellation
          task={tasks.find(t => t.id === showCancellationDialog) || null}
          onConfirm={handleConfirmCancellation}
          onCancel={() => setShowCancellationDialog(null)}
          isOpen={!!showCancellationDialog}
        />
      )}
    </div>
  );
};

// Import TaskCancellation component
import { TaskCancellation } from './TaskCancellation';

interface TaskListProps {
  /** Array of tasks to display */
  tasks: Task[];
  /** Callback when a task is selected */
  onTaskSelect: (taskId: string) => void;
  /** Callback when a task is cancelled */
  onTaskCancelled: (taskId: string) => void;
  /** Callback when viewing task details */
  onViewTask: () => void;
  /** Additional CSS classes for styling */
  className?: string;
}