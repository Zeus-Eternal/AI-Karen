import React, { useState, useMemo } from 'react';
import { Task, TaskStatus, TaskPriority, Theme } from './types';

interface CompletedTasksComponentProps {
  tasks: Task[];
  theme: Theme;
  className?: string;
  onViewTask?: (task: Task) => void;
  onExportTasks?: (tasks: Task[]) => void;
  onClearCompletedTasks?: () => void;
}

export const CompletedTasksComponent: React.FC<CompletedTasksComponentProps> = ({
  tasks,
  theme,
  className = '',
  onViewTask,
  onExportTasks,
  onClearCompletedTasks
}) => {
  const [sortBy, setSortBy] = useState<'completionDate' | 'title' | 'duration'>('completionDate');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | 'all'>('all');

  // Filter and sort tasks
  const filteredAndSortedTasks = useMemo(() => {
    // Filter tasks
    let result = tasks.filter(task => task.status === TaskStatus.COMPLETED);
    
    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(task => 
        task.title.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query) ||
        (task.tags && task.tags.some(tag => tag.toLowerCase().includes(query)))
      );
    }
    
    // Apply priority filter
    if (priorityFilter !== 'all') {
      result = result.filter(task => task.priority === priorityFilter);
    }
    
    // Sort tasks
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'completionDate':
          comparison = a.updatedAt.getTime() - b.updatedAt.getTime();
          break;
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'duration':
          const durationA = a.actualDuration || 0;
          const durationB = b.actualDuration || 0;
          comparison = durationA - durationB;
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
    
    return result;
  }, [tasks, sortBy, sortOrder, searchQuery, priorityFilter]);

  // Task statistics
  const stats = useMemo(() => {
    const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED);
    
    const totalTasks = completedTasks.length;
    const totalEstimatedDuration = completedTasks.reduce((sum, task) => sum + (task.estimatedDuration || 0), 0);
    const totalActualDuration = completedTasks.reduce((sum, task) => sum + (task.actualDuration || 0), 0);
    
    // Calculate efficiency (how close actual duration was to estimated)
    let efficiency = 0;
    if (totalEstimatedDuration > 0) {
      efficiency = Math.min(100, Math.round((totalEstimatedDuration / totalActualDuration) * 100));
    }
    
    // Count by priority
    const priorityCounts = {
      urgent: completedTasks.filter(task => task.priority === TaskPriority.URGENT).length,
      high: completedTasks.filter(task => task.priority === TaskPriority.HIGH).length,
      medium: completedTasks.filter(task => task.priority === TaskPriority.MEDIUM).length,
      low: completedTasks.filter(task => task.priority === TaskPriority.LOW).length
    };
    
    return {
      totalTasks,
      totalEstimatedDuration,
      totalActualDuration,
      efficiency,
      priorityCounts
    };
  }, [tasks]);

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

  // Format relative date
  const formatRelativeDate = (date?: Date): string => {
    if (!date) return 'N/A';
    
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  // Handle sort change
  const handleSortChange = (newSortBy: 'completionDate' | 'title' | 'duration') => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  // Handle export
  const handleExport = () => {
    if (onExportTasks) {
      onExportTasks(filteredAndSortedTasks);
    }
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.lg,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.background,
    borderRadius: theme.borderRadius
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md
  };

  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: theme.typography.fontSize.xl,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  const statsContainerStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg
  };

  const statCardStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    boxShadow: theme.shadows.sm
  };

  const statLabelStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs
  };

  const statValueStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.lg,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  const controlsContainerStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
    padding: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`
  };

  const searchContainerStyle: React.CSSProperties = {
    flex: 1,
    minWidth: '200px'
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base
  };

  const selectStyle: React.CSSProperties = {
    ...inputStyle,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    cursor: 'pointer'
  };

  const buttonStyle: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.borderRadius,
    border: 'none',
    cursor: 'pointer',
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base,
    fontWeight: theme.typography.fontWeight.medium,
    transition: 'all 0.2s ease'
  };

  const primaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: 'transparent',
    color: theme.colors.text,
    border: `1px solid ${theme.colors.border}`
  };

  const taskListStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.sm
  };

  const taskItemStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    boxShadow: theme.shadows.sm,
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  };

  const taskItemHoverStyle: React.CSSProperties = {
    ...taskItemStyle,
    boxShadow: theme.shadows.md,
    transform: 'translateY(-2px)'
  };

  const taskHeaderStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: theme.spacing.sm
  };

  const taskTitleStyle: React.CSSProperties = {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: theme.typography.fontSize.lg,
    color: theme.colors.text,
    margin: 0,
    flex: 1
  };

  const taskMetaStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm
  };

  const metaItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center'
  };

  const priorityBadgeStyle = (priority: TaskPriority): React.CSSProperties => ({
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: '12px',
    fontSize: theme.typography.fontSize.xs,
    fontWeight: theme.typography.fontWeight.medium,
    color: 'white',
    backgroundColor: 
      priority === TaskPriority.URGENT ? theme.colors.error :
      priority === TaskPriority.HIGH ? theme.colors.warning :
      priority === TaskPriority.MEDIUM ? theme.colors.info :
      theme.colors.success
  });

  const durationStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.sm
  };

  const emptyStateStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
    color: theme.colors.textSecondary,
    textAlign: 'center'
  };

  const emptyIconStyle: React.CSSProperties = {
    fontSize: '3rem',
    marginBottom: theme.spacing.md
  };

  return (
    <div className={`copilot-completed-tasks ${className}`} style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <h2 style={titleStyle}>Completed Tasks</h2>
        <div style={{ display: 'flex', gap: theme.spacing.sm }}>
          {onExportTasks && (
            <button
              onClick={handleExport}
              style={secondaryButtonStyle}
              disabled={filteredAndSortedTasks.length === 0}
            >
              Export
            </button>
          )}
          {onClearCompletedTasks && (
            <button
              onClick={onClearCompletedTasks}
              style={secondaryButtonStyle}
              disabled={filteredAndSortedTasks.length === 0}
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Statistics */}
      <div style={statsContainerStyle}>
        <div style={statCardStyle}>
          <div style={statLabelStyle}>Total Completed</div>
          <div style={statValueStyle}>{stats.totalTasks}</div>
        </div>
        
        <div style={statCardStyle}>
          <div style={statLabelStyle}>Efficiency</div>
          <div style={statValueStyle}>{stats.efficiency}%</div>
        </div>
        
        <div style={statCardStyle}>
          <div style={statLabelStyle}>Total Time</div>
          <div style={statValueStyle}>{formatDuration(stats.totalActualDuration)}</div>
        </div>
        
        <div style={statCardStyle}>
          <div style={statLabelStyle}>Time Saved</div>
          <div style={statValueStyle}>
            {stats.totalEstimatedDuration > stats.totalActualDuration 
              ? formatDuration(stats.totalEstimatedDuration - stats.totalActualDuration)
              : '0 min'
            }
          </div>
        </div>
      </div>

      {/* Controls */}
      <div style={controlsContainerStyle}>
        <div style={searchContainerStyle}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={inputStyle}
            placeholder="Search completed tasks..."
            aria-label="Search completed tasks"
          />
        </div>
        
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as TaskPriority | 'all')}
          style={selectStyle}
          aria-label="Filter by priority"
        >
          <option value="all">All Priorities</option>
          <option value={TaskPriority.URGENT}>Urgent</option>
          <option value={TaskPriority.HIGH}>High</option>
          <option value={TaskPriority.MEDIUM}>Medium</option>
          <option value={TaskPriority.LOW}>Low</option>
        </select>
        
        <select
          value={`${sortBy}-${sortOrder}`}
          onChange={(e) => {
            const [newSortBy] = e.target.value.split('-') as ['completionDate' | 'title' | 'duration'];
            handleSortChange(newSortBy);
          }}
          style={selectStyle}
          aria-label="Sort tasks"
        >
          <option value="completionDate-desc">Newest First</option>
          <option value="completionDate-asc">Oldest First</option>
          <option value="title-asc">Title (A-Z)</option>
          <option value="title-desc">Title (Z-A)</option>
          <option value="duration-asc">Duration (Shortest)</option>
          <option value="duration-desc">Duration (Longest)</option>
        </select>
      </div>

      {/* Task List */}
      {filteredAndSortedTasks.length === 0 ? (
        <div style={emptyStateStyle}>
          <div style={emptyIconStyle} aria-hidden="true">✅</div>
          <h3 style={{ margin: `0 0 ${theme.spacing.sm} 0` }}>No completed tasks found</h3>
          <p>Try adjusting your search or filter criteria</p>
        </div>
      ) : (
        <div style={taskListStyle}>
          {filteredAndSortedTasks.map(task => (
            <div 
              key={task.id}
              style={taskItemStyle}
              onClick={() => onViewTask && onViewTask(task)}
              onMouseEnter={(e) => {
                const element = e.currentTarget;
                Object.assign(element.style, taskItemHoverStyle);
              }}
              onMouseLeave={(e) => {
                const element = e.currentTarget;
                Object.assign(element.style, taskItemStyle);
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onViewTask && onViewTask(task)}
              aria-label={`View task: ${task.title}`}
            >
              {/* Task Header */}
              <div style={taskHeaderStyle}>
                <h3 style={taskTitleStyle}>{task.title}</h3>
                <span style={priorityBadgeStyle(task.priority)}>
                  {task.priority}
                </span>
              </div>
              
              {/* Task Meta */}
              <div style={taskMetaStyle}>
                <div style={metaItemStyle}>
                  <span>Completed: </span>
                  <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
                    {formatRelativeDate(task.updatedAt)}
                  </span>
                </div>
                {task.assignedTo && (
                  <div style={metaItemStyle}>
                    <span>Assigned to: </span>
                    <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
                      {task.assignedTo}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Duration Comparison */}
              <div style={durationStyle}>
                <span>Estimated: {formatDuration(task.estimatedDuration)}</span>
                <span>Actual: {formatDuration(task.actualDuration)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};