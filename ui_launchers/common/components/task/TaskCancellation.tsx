import React, { useState } from 'react';
import { Task } from '../../types/task';

/**
 * TaskCancellation Component
 * 
 * Provides a confirmation dialog and handles the cancellation of tasks
 * with proper error handling and user feedback.
 * 
 * @component
 * @example
 * ```tsx
 * <TaskCancellation 
 *   task={activeTask}
 *   onConfirm={(taskId) => console.log('Task cancelled:', taskId)}
 *   onCancel={() => console.log('Cancellation cancelled')}
 *   isOpen={showCancellationDialog}
 * />
 * ```
 */
export const TaskCancellation: React.FC<TaskCancellationProps> = ({ 
  task,
  onConfirm,
  onCancel,
  isOpen = false,
  className = ''
}) => {
  const [isCancelling, setIsCancelling] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (!task) return;
    
    setIsCancelling(true);
    setError(null);
    
    try {
      // In a real implementation, this would call an API to cancel the task
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onConfirm(task.id, reason || 'No reason provided');
    } catch (err) {
      console.error('Error cancelling task:', err);
      setError('Failed to cancel task. Please try again.');
    } finally {
      setIsCancelling(false);
    }
  };

  const handleCancel = () => {
    setReason('');
    setError(null);
    onCancel();
  };

  if (!isOpen || !task) {
    return null;
  }

  return (
    <div className={`task-cancellation-overlay ${className}`}>
      <div 
        className="task-cancellation-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cancellation-title"
        aria-describedby="cancellation-description"
      >
        <div className="modal-header">
          <h3 id="cancellation-title">Cancel Task</h3>
          <button 
            onClick={handleCancel}
            className="close-button"
            aria-label="Close dialog"
            disabled={isCancelling}
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          <p id="cancellation-description">
            Are you sure you want to cancel the task "{task.title}"? 
            This action cannot be undone.
          </p>

          <div className="task-details">
            <div className="detail-row">
              <span className="detail-label">Task Type:</span>
              <span className="detail-value">{task.type}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Status:</span>
              <span className={`detail-value status-${task.status}`}>
                {task.status}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Created:</span>
              <span className="detail-value">
                {new Date(task.createdAt).toLocaleString()}
              </span>
            </div>
          </div>

          <div className="reason-section">
            <label htmlFor="cancellation-reason">
              Reason for cancellation (optional):
            </label>
            <textarea
              id="cancellation-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Please provide a reason for cancelling this task..."
              rows={3}
              disabled={isCancelling}
            />
          </div>

          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            onClick={handleCancel}
            className="cancel-button"
            disabled={isCancelling}
          >
            Keep Task
          </button>
          <button
            onClick={handleConfirm}
            className="confirm-button"
            disabled={isCancelling}
            aria-busy={isCancelling}
          >
            {isCancelling ? 'Cancelling...' : 'Confirm Cancellation'}
          </button>
        </div>
      </div>
    </div>
  );
};

interface TaskCancellationProps {
  /** The task to be cancelled */
  task: Task | null;
  /** Callback when cancellation is confirmed */
  onConfirm: (taskId: string, reason?: string) => void;
  /** Callback when cancellation is cancelled */
  onCancel: () => void;
  /** Whether the cancellation dialog is open */
  isOpen?: boolean;
  /** Additional CSS classes for styling */
  className?: string;
}