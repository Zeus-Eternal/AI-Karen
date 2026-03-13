import React from 'react';
import { Task, TaskStatus, Theme } from './types';

interface TaskProgressComponentProps {
  task: Task;
  theme: Theme;
  showDetails?: boolean;
  className?: string;
  onUpdateProgress?: (taskId: string, progress: number) => void;
  onUpdateStatus?: (taskId: string, status: TaskStatus) => void;
}

export const TaskProgressComponent: React.FC<TaskProgressComponentProps> = ({
  task,
  theme,
  showDetails = true,
  className = '',
  onUpdateProgress,
  onUpdateStatus
}) => {
  // Get status color
  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return theme.colors.success;
      case TaskStatus.IN_PROGRESS:
        return theme.colors.info;
      case TaskStatus.PENDING:
        return theme.colors.warning;
      case TaskStatus.FAILED:
        return theme.colors.error;
      case TaskStatus.CANCELLED:
        return theme.colors.textSecondary;
      default:
        return theme.colors.textSecondary;
    }
  };

  // Get status text
  const getStatusText = (status: TaskStatus): string => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return 'Completed';
      case TaskStatus.IN_PROGRESS:
        return 'In Progress';
      case TaskStatus.PENDING:
        return 'Pending';
      case TaskStatus.FAILED:
        return 'Failed';
      case TaskStatus.CANCELLED:
        return 'Cancelled';
      default:
        return 'Unknown';
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'urgent':
        return theme.colors.error;
      case 'high':
        return theme.colors.warning;
      case 'medium':
        return theme.colors.info;
      case 'low':
        return theme.colors.success;
      default:
        return theme.colors.textSecondary;
    }
  };

  // Format duration
  const formatDuration = (minutes?: number): string => {
    if (!minutes) return 'N/A';
    
    if (minutes < 60) {
      return `${minutes} min`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
  };

  // Format date
  const formatDate = (date?: Date): string => {
    if (!date) return 'N/A';
    
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  // Handle progress change
  const handleProgressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const progress = parseInt(e.target.value, 10);
    if (onUpdateProgress) {
      onUpdateProgress(task.id, progress);
    }
  };

  // Handle status change
  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const status = e.target.value as TaskStatus;
    if (onUpdateStatus) {
      onUpdateStatus(task.id, status);
    }
  };

  const containerStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    marginBottom: theme.spacing.sm
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm
  };

  const titleStyle: React.CSSProperties = {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: theme.typography.fontSize.lg,
    color: theme.colors.text,
    margin: 0
  };

  const statusBadgeStyle: React.CSSProperties = {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: '12px',
    fontSize: theme.typography.fontSize.xs,
    fontWeight: theme.typography.fontWeight.medium,
    color: 'white',
    backgroundColor: getStatusColor(task.status)
  };

  const priorityBadgeStyle: React.CSSProperties = {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: '12px',
    fontSize: theme.typography.fontSize.xs,
    fontWeight: theme.typography.fontWeight.medium,
    color: 'white',
    backgroundColor: getPriorityColor(task.priority),
    marginLeft: theme.spacing.xs
  };

  const progressContainerStyle: React.CSSProperties = {
    marginBottom: theme.spacing.sm
  };

  const progressBarContainerStyle: React.CSSProperties = {
    height: '8px',
    backgroundColor: theme.colors.border,
    borderRadius: '4px',
    overflow: 'hidden',
    marginBottom: theme.spacing.xs
  };

  const progressBarStyle: React.CSSProperties = {
    height: '100%',
    backgroundColor: getStatusColor(task.status),
    borderRadius: '4px',
    transition: 'width 0.3s ease',
    width: `${task.progress}%`
  };

  const progressLabelStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.textSecondary
  };

  const detailsContainerStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm
  };

  const detailItemStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column'
  };

  const detailLabelStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs
  };

  const detailValueStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text,
    fontWeight: theme.typography.fontWeight.medium
  };

  const controlsContainerStyle: React.CSSProperties = {
    display: 'flex',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.md
  };

  const inputStyle: React.CSSProperties = {
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm
  };

  const selectStyle: React.CSSProperties = {
    ...inputStyle,
    flex: 1
  };

  const buttonStyle: React.CSSProperties = {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: theme.borderRadius,
    border: 'none',
    cursor: 'pointer',
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.medium,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  return (
    <div className={`copilot-task-progress ${className}`} style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <h3 style={titleStyle}>{task.title}</h3>
        <div>
          <span style={statusBadgeStyle} aria-label={`Status: ${getStatusText(task.status)}`}>
            {getStatusText(task.status)}
          </span>
          <span style={priorityBadgeStyle} aria-label={`Priority: ${task.priority}`}>
            {task.priority}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={progressContainerStyle}>
        <div style={progressBarContainerStyle} role="progressbar" aria-valuenow={task.progress} aria-valuemin={0} aria-valuemax={100}>
          <div style={progressBarStyle} />
        </div>
        <div style={progressLabelStyle}>
          <span>Progress</span>
          <span>{task.progress}%</span>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div style={detailsContainerStyle}>
          <div style={detailItemStyle}>
            <span style={detailLabelStyle}>Created</span>
            <span style={detailValueStyle}>{formatDate(task.createdAt)}</span>
          </div>
          <div style={detailItemStyle}>
            <span style={detailLabelStyle}>Updated</span>
            <span style={detailValueStyle}>{formatDate(task.updatedAt)}</span>
          </div>
          {task.dueDate && (
            <div style={detailItemStyle}>
              <span style={detailLabelStyle}>Due Date</span>
              <span style={detailValueStyle}>{formatDate(task.dueDate)}</span>
            </div>
          )}
          {task.assignedTo && (
            <div style={detailItemStyle}>
              <span style={detailLabelStyle}>Assigned To</span>
              <span style={detailValueStyle}>{task.assignedTo}</span>
            </div>
          )}
          <div style={detailItemStyle}>
            <span style={detailLabelStyle}>Estimated</span>
            <span style={detailValueStyle}>{formatDuration(task.estimatedDuration)}</span>
          </div>
          {task.actualDuration && (
            <div style={detailItemStyle}>
              <span style={detailLabelStyle}>Actual</span>
              <span style={detailValueStyle}>{formatDuration(task.actualDuration)}</span>
            </div>
          )}
        </div>
      )}

      {/* Controls */}
      {(onUpdateProgress || onUpdateStatus) && (
        <div style={controlsContainerStyle}>
          {onUpdateProgress && (
            <div style={{ flex: 1 }}>
              <label htmlFor={`progress-${task.id}`} style={detailLabelStyle}>
                Update Progress
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
                <input
                  id={`progress-${task.id}`}
                  type="range"
                  min="0"
                  max="100"
                  value={task.progress}
                  onChange={handleProgressChange}
                  style={{ flex: 1 }}
                  aria-label="Task progress"
                />
                <span style={{ fontSize: theme.typography.fontSize.sm, minWidth: '40px' }}>
                  {task.progress}%
                </span>
              </div>
            </div>
          )}
          
          {onUpdateStatus && (
            <div style={{ flex: 1 }}>
              <label htmlFor={`status-${task.id}`} style={detailLabelStyle}>
                Update Status
              </label>
              <select
                id={`status-${task.id}`}
                value={task.status}
                onChange={handleStatusChange}
                style={selectStyle}
                aria-label="Task status"
              >
                {Object.values(TaskStatus).map(status => (
                  <option key={status} value={status}>
                    {getStatusText(status)}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}
    </div>
  );
};