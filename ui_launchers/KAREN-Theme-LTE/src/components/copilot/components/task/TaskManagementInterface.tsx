import React, { useState, useEffect } from 'react';
import { Task, TaskStatus, TaskPriority, TaskFilter, Theme } from './types';
import { TaskCreationComponent } from './TaskCreationComponent';
import { TaskProgressComponent } from './TaskProgressComponent';
import { TaskCancellationComponent } from './TaskCancellationComponent';
import { CompletedTasksComponent } from './CompletedTasksComponent';
import { useTheme } from '../chat/ThemeProvider';

interface TaskManagementInterfaceProps {
  className?: string;
  theme?: Partial<Theme>;
  autoRefresh?: boolean;
  refreshInterval?: number;
  persistTasks?: boolean;
  assignedToOptions?: string[];
  tagOptions?: string[];
}

export const TaskManagementInterface: React.FC<TaskManagementInterfaceProps> = ({
  className = '',
  theme: customTheme,
  autoRefresh = true,
  refreshInterval = 30000,
  persistTasks = true,
  assignedToOptions = ['User', 'Agent', 'System'],
  tagOptions = ['Development', 'Research', 'Testing', 'Documentation', 'Review']
}) => {
  const { theme } = useTheme();
  
  // State
  const [activeView, setActiveView] = useState<'all' | 'active' | 'completed'>('active');
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [taskToCancel, setTaskToCancel] = useState<Task | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [activeFilter, setActiveFilter] = useState<TaskFilter>({});
  const [showCompletedView, setShowCompletedView] = useState(false);

  // Mock hook for task management (in a real implementation, this would use the useTaskManagement hook)
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load tasks (mock implementation)
  useEffect(() => {
    // In a real implementation, this would use the useTaskManagement hook
    const loadTasks = () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Mock tasks for demonstration
        const mockTasks: Task[] = [
          {
            id: 'task-1',
            title: 'Research AI integration options',
            description: 'Research and evaluate different AI integration options for the CoPilot system',
            status: TaskStatus.IN_PROGRESS,
            priority: TaskPriority.HIGH,
            createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
            updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
            progress: 65,
            estimatedDuration: 240, // 4 hours
            createdBy: 'user',
            tags: ['Research', 'AI']
          },
          {
            id: 'task-2',
            title: 'Implement task management UI',
            description: 'Create the task management interface for the CoPilot system',
            status: TaskStatus.IN_PROGRESS,
            priority: TaskPriority.MEDIUM,
            createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
            updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
            progress: 30,
            estimatedDuration: 480, // 8 hours
            createdBy: 'user',
            tags: ['Development', 'UI']
          },
          {
            id: 'task-3',
            title: 'Write documentation',
            description: 'Write comprehensive documentation for the CoPilot system',
            status: TaskStatus.PENDING,
            priority: TaskPriority.MEDIUM,
            createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
            updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
            progress: 0,
            estimatedDuration: 360, // 6 hours
            createdBy: 'user',
            tags: ['Documentation']
          },
          {
            id: 'task-4',
            title: 'Test system performance',
            description: 'Conduct performance testing on the CoPilot system',
            status: TaskStatus.COMPLETED,
            priority: TaskPriority.HIGH,
            createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
            updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
            progress: 100,
            estimatedDuration: 180, // 3 hours
            actualDuration: 165, // 2 hours 45 minutes
            createdBy: 'user',
            tags: ['Testing']
          }
        ];
        
        setTasks(mockTasks);
      } catch (err) {
        console.error('Failed to load tasks:', err);
        setError('Failed to load tasks');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadTasks();
  }, []);

  // Filter tasks based on active view
  const filteredTasks = tasks.filter(task => {
    if (activeView === 'active') {
      return task.status !== TaskStatus.COMPLETED;
    } else if (activeView === 'completed') {
      return task.status === TaskStatus.COMPLETED;
    }
    return true; // 'all' view
  });

  // Task actions
  const handleCreateTask = (taskData: any) => {
    // In a real implementation, this would use the useTaskManagement hook
    const newTask: Task = {
      id: `task-${Date.now()}`,
      title: taskData.title,
      description: taskData.description,
      status: TaskStatus.PENDING,
      priority: taskData.priority,
      createdAt: new Date(),
      updatedAt: new Date(),
      progress: 0,
      estimatedDuration: taskData.estimatedDuration,
      createdBy: 'user',
      tags: taskData.tags || []
    };
    
    setTasks(prev => [newTask, ...prev]);
    setShowCreateTask(false);
  };

  const handleUpdateProgress = (taskId: string, progress: number) => {
    // In a real implementation, this would use the useTaskManagement hook
    setTasks(prev => 
      prev.map(task => 
        task.id === taskId 
          ? { 
              ...task, 
              progress, 
              updatedAt: new Date(),
              status: progress === 100 ? TaskStatus.COMPLETED : 
                        progress > 0 ? TaskStatus.IN_PROGRESS : TaskStatus.PENDING
            } 
          : task
      )
    );
  };

  const handleUpdateStatus = (taskId: string, status: TaskStatus) => {
    // In a real implementation, this would use the useTaskManagement hook
    setTasks(prev => 
      prev.map(task => 
        task.id === taskId 
          ? { 
              ...task, 
              status, 
              updatedAt: new Date(),
              progress: status === TaskStatus.COMPLETED ? 100 : task.progress
            } 
          : task
      )
    );
  };

  const handleCancelTask = (taskId: string, reason?: string) => {
    // In a real implementation, this would use the useTaskManagement hook
    setTasks(prev => 
      prev.map(task => 
        task.id === taskId 
          ? { 
              ...task, 
              status: TaskStatus.CANCELLED, 
              updatedAt: new Date(),
              metadata: { 
                ...task.metadata, 
                cancellationReason: reason 
              }
            } 
          : task
      )
    );
    
    setShowCancelDialog(false);
    setTaskToCancel(null);
  };

  const handleViewTask = (task: Task) => {
    setSelectedTask(task);
  };

  const handleCloseTaskDetails = () => {
    setSelectedTask(null);
  };

  const handleExportTasks = (tasksToExport: Task[]) => {
    // In a real implementation, this would use the useTaskManagement hook
    const dataStr = JSON.stringify(tasksToExport, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `tasks-${new Date().toISOString().slice(0,10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleClearCompletedTasks = () => {
    // In a real implementation, this would use the useTaskManagement hook
    setTasks(prev => prev.filter(task => task.status !== TaskStatus.COMPLETED));
    setShowCompletedView(false);
  };

  // Get tasks by status
  const pendingTasks = tasks.filter(task => task.status === TaskStatus.PENDING);
  const inProgressTasks = tasks.filter(task => task.status === TaskStatus.IN_PROGRESS);
  const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED);
  const cancelledTasks = tasks.filter(task => task.status === TaskStatus.CANCELLED);

  // Container style
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    width: '100%',
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    borderRadius: theme.borderRadius,
    overflow: 'hidden'
  };

  // Header style
  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.surface
  };

  // Title style
  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: theme.typography.fontSize.xl,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  // Tabs style
  const tabsStyle: React.CSSProperties = {
    display: 'flex',
    borderBottom: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.surface
  };

  // Tab style
  const tabStyle = (isActive: boolean): React.CSSProperties => ({
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    cursor: 'pointer',
    borderBottom: isActive ? `2px solid ${theme.colors.primary}` : 'none',
    color: isActive ? theme.colors.primary : theme.colors.textSecondary,
    fontWeight: isActive ? theme.typography.fontWeight.semibold : theme.typography.fontWeight.normal,
    transition: 'all 0.2s ease'
  });

  // Content style
  const contentStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: theme.spacing.lg
  };

  // Empty state style
  const emptyStateStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: theme.colors.textSecondary,
    textAlign: 'center',
    padding: theme.spacing.xl
  };

  // Empty icon style
  const emptyIconStyle: React.CSSProperties = {
    fontSize: '4rem',
    marginBottom: theme.spacing.lg
  };

  // Button style
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

  // Primary button style
  const primaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  // Floating button style
  const floatingButtonStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: theme.spacing.xl,
    right: theme.spacing.xl,
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: theme.colors.primary,
    color: 'white',
    border: 'none',
    boxShadow: theme.shadows.lg,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.5rem',
    zIndex: 10
  };

  // Modal overlay style
  const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20
  };

  // Modal content style
  const modalContentStyle: React.CSSProperties = {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    maxWidth: '90vw',
    maxHeight: '90vh',
    overflow: 'auto',
    position: 'relative'
  };

  // Close button style
  const closeButtonStyle: React.CSSProperties = {
    position: 'absolute',
    top: theme.spacing.md,
    right: theme.spacing.md,
    background: 'none',
    border: 'none',
    fontSize: theme.typography.fontSize.lg,
    cursor: 'pointer',
    color: theme.colors.textSecondary,
    padding: 0,
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  return (
    <div className={`copilot-task-management ${className}`} style={containerStyle}>
      {/* Header */}
      <header className="copilot-header" style={headerStyle}>
        <h1 style={titleStyle}>Task Management</h1>
        <div style={{ display: 'flex', gap: theme.spacing.sm }}>
          <button
            onClick={() => setShowCompletedView(true)}
            style={primaryButtonStyle}
          >
            View Completed
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="copilot-tabs" style={tabsStyle}>
        <div 
          style={tabStyle(activeView === 'all')}
          onClick={() => setActiveView('all')}
          role="tab"
          aria-selected={activeView === 'all'}
          tabIndex={0}
        >
          All Tasks
        </div>
        <div 
          style={tabStyle(activeView === 'active')}
          onClick={() => setActiveView('active')}
          role="tab"
          aria-selected={activeView === 'active'}
          tabIndex={0}
        >
          Active
        </div>
        <div 
          style={tabStyle(activeView === 'completed')}
          onClick={() => setActiveView('completed')}
          role="tab"
          aria-selected={activeView === 'completed'}
          tabIndex={0}
        >
          Completed
        </div>
      </div>

      {/* Content */}
      <main className="copilot-content" style={contentStyle}>
        {isLoading ? (
          <div style={emptyStateStyle}>
            <div className="copilot-loading-spinner" style={{ 
              width: '40px', 
              height: '40px', 
              border: `3px solid ${theme.colors.border}`,
              borderTop: `3px solid ${theme.colors.primary}`,
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginBottom: theme.spacing.md
            }} />
            <p>Loading tasks...</p>
          </div>
        ) : error ? (
          <div style={emptyStateStyle}>
            <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }} aria-hidden="true">⚠️</div>
            <h2 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>Error</h2>
            <p>{error}</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div style={emptyStateStyle}>
            <div style={emptyIconStyle} aria-hidden="true">📋</div>
            <h2 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>No tasks found</h2>
            <p>Create a new task to get started</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.md }}>
            {filteredTasks.map(task => (
              <TaskProgressComponent
                key={task.id}
                task={task}
                theme={theme}
                onUpdateProgress={handleUpdateProgress}
                onUpdateStatus={handleUpdateStatus}
              />
            ))}
          </div>
        )}
      </main>

      {/* Floating Action Button */}
      <button
        onClick={() => setShowCreateTask(true)}
        style={floatingButtonStyle}
        aria-label="Create new task"
      >
        +
      </button>

      {/* Create Task Modal */}
      {showCreateTask && (
        <div style={modalOverlayStyle} onClick={() => setShowCreateTask(false)}>
          <div 
            style={modalContentStyle} 
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-task-title"
          >
            <button
              onClick={() => setShowCreateTask(false)}
              style={closeButtonStyle}
              aria-label="Close dialog"
            >
              ×
            </button>
            <TaskCreationComponent
              theme={theme}
              onCreateTask={handleCreateTask}
              onCancel={() => setShowCreateTask(false)}
              assignedToOptions={assignedToOptions}
              tagOptions={tagOptions}
            />
          </div>
        </div>
      )}

      {/* Cancel Task Modal */}
      {showCancelDialog && taskToCancel && (
        <div style={modalOverlayStyle} onClick={() => setShowCancelDialog(false)}>
          <div 
            style={modalContentStyle} 
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-task-title"
          >
            <TaskCancellationComponent
              task={taskToCancel}
              theme={theme}
              onCancelTask={handleCancelTask}
              onClose={() => {
                setShowCancelDialog(false);
                setTaskToCancel(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Completed Tasks Modal */}
      {showCompletedView && (
        <div style={modalOverlayStyle} onClick={() => setShowCompletedView(false)}>
          <div 
            style={{ ...modalContentStyle, width: '90vw', maxWidth: '1200px' }} 
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="completed-tasks-title"
          >
            <button
              onClick={() => setShowCompletedView(false)}
              style={closeButtonStyle}
              aria-label="Close dialog"
            >
              ×
            </button>
            <CompletedTasksComponent
              tasks={completedTasks}
              theme={theme}
              onViewTask={handleViewTask}
              onExportTasks={handleExportTasks}
              onClearCompletedTasks={handleClearCompletedTasks}
            />
          </div>
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <div style={modalOverlayStyle} onClick={handleCloseTaskDetails}>
          <div 
            style={{ ...modalContentStyle, width: '90vw', maxWidth: '800px' }} 
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="task-details-title"
          >
            <button
              onClick={handleCloseTaskDetails}
              style={closeButtonStyle}
              aria-label="Close dialog"
            >
              ×
            </button>
            <div style={{ padding: theme.spacing.lg }}>
              <h2 id="task-details-title" style={{ margin: `0 0 ${theme.spacing.lg} 0` }}>
                {selectedTask.title}
              </h2>
              <TaskProgressComponent
                task={selectedTask}
                theme={theme}
                showDetails={true}
              />
              <div style={{ marginTop: theme.spacing.lg, display: 'flex', justifyContent: 'flex-end', gap: theme.spacing.sm }}>
                {selectedTask.status !== TaskStatus.COMPLETED && selectedTask.status !== TaskStatus.CANCELLED && (
                  <button
                    onClick={() => {
                      setTaskToCancel(selectedTask);
                      setShowCancelDialog(true);
                      setSelectedTask(null);
                    }}
                    style={{
                      ...buttonStyle,
                      backgroundColor: theme.colors.error,
                      color: 'white'
                    }}
                  >
                    Cancel Task
                  </button>
                )}
                <button
                  onClick={handleCloseTaskDetails}
                  style={buttonStyle}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
          .copilot-task-management {
            height: 100vh;
            width: 100vw;
            border-radius: 0;
          }
          
          .copilot-header {
            padding: 12px 16px;
          }
          
          .copilot-content {
            padding: 16px;
          }
        }
        
        @media (max-width: 480px) {
          .copilot-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
          }
          
          .copilot-tabs {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
          }
        }
      `}</style>
    </div>
  );
};

export default TaskManagementInterface;