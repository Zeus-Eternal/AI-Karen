import React, { useState, useEffect } from 'react';
import { TaskCreation } from './TaskCreation';
import { TaskProgress } from './TaskProgress';
import { TaskList } from './TaskList';
import { TaskCancellation } from './TaskCancellation';
import { Task } from '../../types/task';

/**
 * TaskManagement Component
 * 
 * Main container for all task-related functionality including:
 * - Task creation interface
 * - Task progress display
 * - Task cancellation features
 * - Task list view
 * 
 * @component
 * @example
 * ```tsx
 * <TaskManagement sessionId="user-session-123" />
 * ```
 */
export const TaskManagement: React.FC<TaskManagementProps> = ({ 
  sessionId,
  className = '',
  onTaskCreated,
  onTaskCancelled,
  onTaskCompleted
}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [view, setView] = useState<'creation' | 'progress' | 'list'>('creation');

  // Load tasks from session storage or API
  useEffect(() => {
    const loadTasks = async () => {
      try {
        // In a real implementation, this would fetch from an API
        // For now, we'll use mock data
        const mockTasks: Task[] = [];
        setTasks(mockTasks);
      } catch (error) {
        console.error('Error loading tasks:', error);
      }
    };

    loadTasks();
  }, [sessionId]);

  const handleTaskCreated = (task: Task) => {
    setTasks(prev => [...prev, task]);
    setActiveTaskId(task.id);
    setView('progress');
    onTaskCreated?.(task);
  };

  const handleTaskCancelled = (taskId: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: 'cancelled' as const } : task
    ));
    if (activeTaskId === taskId) {
      setActiveTaskId(null);
    }
    onTaskCancelled?.(taskId);
  };

  const handleTaskCompleted = (taskId: string, result: any) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: 'completed' as const, result } : task
    ));
    if (activeTaskId === taskId) {
      setActiveTaskId(null);
    }
    onTaskCompleted?.(taskId, result);
  };

  const activeTask = tasks.find(task => task.id === activeTaskId);

  return (
    <div className={`task-management ${className}`} role="region" aria-label="Task Management">
      <div className="task-management-header">
        <h2>Task Management</h2>
        <div className="task-management-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={view === 'creation'}
            aria-controls="creation-panel"
            onClick={() => setView('creation')}
            className={view === 'creation' ? 'active' : ''}
          >
            Create Task
          </button>
          <button
            role="tab"
            aria-selected={view === 'progress'}
            aria-controls="progress-panel"
            onClick={() => setView('progress')}
            className={view === 'progress' ? 'active' : ''}
            disabled={!activeTask}
          >
            Progress
          </button>
          <button
            role="tab"
            aria-selected={view === 'list'}
            aria-controls="list-panel"
            onClick={() => setView('list')}
            className={view === 'list' ? 'active' : ''}
          >
            Task List
          </button>
        </div>
      </div>

      <div className="task-management-content">
        {view === 'creation' && (
          <div id="creation-panel" role="tabpanel">
            <TaskCreation 
              sessionId={sessionId}
              onTaskCreated={handleTaskCreated}
            />
          </div>
        )}

        {view === 'progress' && activeTask && (
          <div id="progress-panel" role="tabpanel">
            <TaskProgress 
              task={activeTask}
              onTaskCancelled={handleTaskCancelled}
              onTaskCompleted={handleTaskCompleted}
            />
          </div>
        )}

        {view === 'list' && (
          <div id="list-panel" role="tabpanel">
            <TaskList 
              tasks={tasks}
              onTaskSelect={setActiveTaskId}
              onTaskCancelled={handleTaskCancelled}
              onViewTask={() => setView('progress')}
            />
          </div>
        )}
      </div>
    </div>
  );
};

interface TaskManagementProps {
  /** Unique identifier for the user session */
  sessionId: string;
  /** Additional CSS classes for styling */
  className?: string;
  /** Callback when a task is created */
  onTaskCreated?: (task: Task) => void;
  /** Callback when a task is cancelled */
  onTaskCancelled?: (taskId: string) => void;
  /** Callback when a task is completed */
  onTaskCompleted?: (taskId: string, result: any) => void;
}