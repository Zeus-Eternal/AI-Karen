import React, { useState, useEffect } from 'react';
import { Task, TaskStatus } from '../../types/task';

/**
 * TaskProgress Component
 * 
 * Displays the progress of a running task with visual indicators,
 * step information, and estimated time remaining.
 * 
 * @component
 * @example
 * ```tsx
 * <TaskProgress 
 *   task={activeTask}
 *   onTaskCancelled={(taskId) => console.log('Task cancelled:', taskId)}
 *   onTaskCompleted={(taskId, result) => console.log('Task completed:', taskId, result)}
 * />
 * ```
 */
export const TaskProgress: React.FC<TaskProgressProps> = ({ 
  task,
  onTaskCancelled,
  onTaskCompleted,
  className = ''
}) => {
  const [progress, setProgress] = useState(task.progress || {
    percentage: 0,
    currentStep: 'Initializing...',
    totalSteps: 1,
    currentStepNumber: 0
  });
  const [isCancelling, setIsCancelling] = useState(false);

  // Simulate progress updates
  useEffect(() => {
    if (task.status === 'running') {
      const interval = setInterval(() => {
        setProgress(prev => {
          // Simulate progress updates
          const newPercentage = Math.min(prev.percentage + Math.random() * 10, 95);
          const newStepNumber = Math.min(
            prev.currentStepNumber + (Math.random() > 0.7 ? 1 : 0),
            prev.totalSteps
          );
          
          return {
            ...prev,
            percentage: newPercentage,
            currentStepNumber: newStepNumber,
            currentStep: newStepNumber > prev.currentStepNumber 
              ? `Step ${newStepNumber} of ${prev.totalSteps}` 
              : prev.currentStep
          };
        });
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [task.status]);

  // Check for task completion
  useEffect(() => {
    if (progress.percentage >= 100 && task.status === 'running') {
      // Simulate task completion
      const timeout = setTimeout(() => {
        const result = {
          summary: 'Task completed successfully',
          output: 'Sample output data',
          timestamp: new Date().toISOString()
        };
        onTaskCompleted(task.id, result);
      }, 1000);

      return () => clearTimeout(timeout);
    }
  }, [progress.percentage, task.status, task.id, onTaskCompleted]);

  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      // In a real implementation, this would call an API to cancel the task
      await new Promise(resolve => setTimeout(resolve, 500));
      onTaskCancelled(task.id);
    } catch (error) {
      console.error('Error cancelling task:', error);
    } finally {
      setIsCancelling(false);
    }
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

  const getStatusText = (status: TaskStatus) => {
    switch (status) {
      case 'pending': return 'Pending';
      case 'running': return 'Running';
      case 'completed': return 'Completed';
      case 'cancelled': return 'Cancelled';
      case 'failed': return 'Failed';
      default: return status;
    }
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'Unknown';
    
    if (seconds < 60) {
      return `${Math.round(seconds)} seconds`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)} minutes`;
    } else {
      return `${Math.round(seconds / 3600)} hours`;
    }
  };

  return (
    <div className={`task-progress ${className}`}>
      <div className="task-progress-header">
        <h3>Task Progress</h3>
        <div className={`task-status ${getStatusColor(task.status)}`}>
          {getStatusText(task.status)}
        </div>
      </div>

      <div className="task-info">
        <h4>{task.title}</h4>
        <p>{task.description}</p>
        <div className="task-meta">
          <span>Type: {task.type}</span>
          <span>Priority: {task.priority}</span>
          <span>Execution Mode: {task.executionMode}</span>
        </div>
      </div>

      {task.status === 'running' && (
        <div className="progress-section">
          <div className="progress-bar-container">
            <div 
              className="progress-bar"
              style={{ width: `${progress.percentage}%` }}
              role="progressbar"
              aria-valuenow={progress.percentage}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Task progress"
            >
              <span className="progress-percentage">{Math.round(progress.percentage)}%</span>
            </div>
          </div>

          <div className="progress-details">
            <div className="progress-step">
              <span className="step-label">Current Step:</span>
              <span className="step-value">{progress.currentStep}</span>
            </div>
            
            <div className="progress-steps">
              <span className="steps-label">Progress:</span>
              <span className="steps-value">
                {progress.currentStepNumber} of {progress.totalSteps} steps
              </span>
            </div>

            {progress.estimatedTimeRemaining && (
              <div className="progress-time">
                <span className="time-label">Estimated Time Remaining:</span>
                <span className="time-value">
                  {formatTime(progress.estimatedTimeRemaining)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {task.status === 'completed' && task.result && (
        <div className="task-result">
          <h4>Task Result</h4>
          <div className="result-content">
            <p>{task.result.summary}</p>
            <pre className="result-output">{JSON.stringify(task.result.output, null, 2)}</pre>
            <div className="result-timestamp">
              Completed at: {new Date(task.result.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {task.status === 'failed' && task.error && (
        <div className="task-error">
          <h4>Task Failed</h4>
          <div className="error-message">{task.error}</div>
        </div>
      )}

      <div className="task-actions">
        {(task.status === 'running' || task.status === 'pending') && (
          <button
            onClick={handleCancel}
            disabled={isCancelling}
            className="cancel-button"
            aria-busy={isCancelling}
          >
            {isCancelling ? 'Cancelling...' : 'Cancel Task'}
          </button>
        )}
      </div>
    </div>
  );
};

interface TaskProgressProps {
  /** The task to display progress for */
  task: Task;
  /** Callback when the task is cancelled */
  onTaskCancelled: (taskId: string) => void;
  /** Callback when the task is completed */
  onTaskCompleted: (taskId: string, result: any) => void;
  /** Additional CSS classes for styling */
  className?: string;
}