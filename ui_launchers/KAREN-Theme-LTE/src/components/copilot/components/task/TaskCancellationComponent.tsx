import React, { useState } from 'react';
import { Task, TaskStatus, Theme } from './types';

interface TaskCancellationComponentProps {
  task: Task;
  theme: Theme;
  className?: string;
  onCancelTask: (taskId: string, reason?: string) => void;
  onClose: () => void;
}

export const TaskCancellationComponent: React.FC<TaskCancellationComponentProps> = ({
  task,
  theme,
  className = '',
  onCancelTask,
  onClose
}) => {
  const [reason, setReason] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle cancellation
  const handleCancel = async () => {
    if (isSubmitting) return;
    
    // Verify confirmation text matches task title
    if (confirmText !== task.title) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await onCancelTask(task.id, reason || undefined);
      onClose();
    } catch (error) {
      console.error('Failed to cancel task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const containerStyle: React.CSSProperties = {
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    maxWidth: '500px',
    width: '100%'
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

  const closeButtonStyle: React.CSSProperties = {
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

  const contentStyle: React.CSSProperties = {
    marginBottom: theme.spacing.lg
  };

  const warningStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing.md,
    backgroundColor: `${theme.colors.warning}20`,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md,
    color: theme.colors.warning
  };

  const warningIconStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.lg,
    marginRight: theme.spacing.sm
  };

  const taskInfoStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    backgroundColor: theme.colors.background,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.md
  };

  const taskTitleStyle: React.CSSProperties = {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: theme.typography.fontSize.lg,
    margin: `0 0 ${theme.spacing.xs} 0`,
    color: theme.colors.text
  };

  const taskMetaStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.textSecondary
  };

  const metaItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center'
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontWeight: theme.typography.fontWeight.medium,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text
  };

  const textareaStyle: React.CSSProperties = {
    width: '100%',
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base,
    minHeight: '100px',
    resize: 'vertical',
    marginBottom: theme.spacing.md
  };

  const confirmationStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    backgroundColor: `${theme.colors.error}10`,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.lg
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base,
    marginTop: theme.spacing.sm
  };

  const buttonContainerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: theme.spacing.sm
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

  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: 'transparent',
    color: theme.colors.text,
    border: `1px solid ${theme.colors.border}`
  };

  const dangerButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.error,
    color: 'white'
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

  return (
    <div className={`copilot-task-cancellation ${className}`} style={containerStyle} role="dialog" aria-modal="true" aria-labelledby="cancellation-title">
      {/* Header */}
      <div style={headerStyle}>
        <h2 id="cancellation-title" style={titleStyle}>Cancel Task</h2>
        <button 
          onClick={onClose}
          style={closeButtonStyle}
          aria-label="Close dialog"
        >
          ×
        </button>
      </div>

      {/* Warning */}
      <div style={warningStyle} role="alert">
        <span style={warningIconStyle} aria-hidden="true">⚠️</span>
        <span>You are about to cancel this task. This action cannot be undone.</span>
      </div>

      {/* Task Info */}
      <div style={taskInfoStyle}>
        <h3 style={taskTitleStyle}>{task.title}</h3>
        <div style={taskMetaStyle}>
          <div style={metaItemStyle}>
            <span>Status: </span>
            <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
              {task.status.charAt(0).toUpperCase() + task.status.slice(1).replace('_', ' ')}
            </span>
          </div>
          <div style={metaItemStyle}>
            <span>Priority: </span>
            <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
            </span>
          </div>
          <div style={metaItemStyle}>
            <span>Created: </span>
            <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
              {formatDate(task.createdAt)}
            </span>
          </div>
          {task.dueDate && (
            <div style={metaItemStyle}>
              <span>Due: </span>
              <span style={{ fontWeight: theme.typography.fontWeight.medium }}>
                {formatDate(task.dueDate)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div style={contentStyle}>
        {/* Reason (Optional) */}
        <div style={{ marginBottom: theme.spacing.lg }}>
          <label htmlFor="cancellation-reason" style={labelStyle}>
            Reason for Cancellation (Optional)
          </label>
          <textarea
            id="cancellation-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={textareaStyle}
            placeholder="Provide a reason for cancelling this task..."
            aria-describedby="reason-description"
          />
          <div id="reason-description" style={{ fontSize: theme.typography.fontSize.sm, color: theme.colors.textSecondary }}>
            This information will be saved with the task for future reference.
          </div>
        </div>

        {/* Confirmation */}
        <div style={confirmationStyle}>
          <label htmlFor="confirm-text" style={labelStyle}>
            Confirm Cancellation
          </label>
          <p style={{ margin: `${theme.spacing.xs} 0`, color: theme.colors.textSecondary }}>
            To confirm cancellation, please type the task title below:
          </p>
          <div style={{ fontWeight: theme.typography.fontWeight.semibold, marginBottom: theme.spacing.sm, color: theme.colors.text }}>
            {task.title}
          </div>
          <input
            id="confirm-text"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            style={inputStyle}
            placeholder="Type the task title to confirm"
            aria-required="true"
            aria-invalid={confirmText !== task.title}
            aria-describedby="confirm-help"
          />
          <div id="confirm-help" style={{ fontSize: theme.typography.fontSize.sm, color: theme.colors.textSecondary, marginTop: theme.spacing.xs }}>
            This is required to prevent accidental cancellations.
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={buttonContainerStyle}>
        <button
          onClick={onClose}
          style={secondaryButtonStyle}
          disabled={isSubmitting}
        >
          Keep Task
        </button>
        <button
          onClick={handleCancel}
          style={dangerButtonStyle}
          disabled={confirmText !== task.title || isSubmitting}
          aria-live="polite"
        >
          {isSubmitting ? 'Cancelling...' : 'Cancel Task'}
        </button>
      </div>
    </div>
  );
};