import React, { useState } from 'react';
import { telemetryService } from '../../lib/telemetry';

export interface RecoveryAction {
  id: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  action: () => void | Promise<void>;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  loading?: boolean;
}

export interface ErrorRecoveryProps {
  title?: string;
  message?: string;
  actions: RecoveryAction[];
  className?: string;
  correlationId?: string;
  errorId?: string;
  compact?: boolean;
}

export const ErrorRecovery: React.FC<ErrorRecoveryProps> = ({
  title = 'Something went wrong',
  message = 'An error occurred. Please try one of the following actions:',
  actions,
  className = '',
  correlationId,
  errorId,
  compact = false,
}) => {
  const [actionStates, setActionStates] = useState<Record<string, boolean>>({});

  const handleActionClick = async (action: RecoveryAction) => {
    if (action.disabled || actionStates[action.id]) {
      return;
    }

    setActionStates(prev => ({ ...prev, [action.id]: true }));

    telemetryService.track('error_recovery.action_clicked', {
      actionId: action.id,
      actionLabel: action.label,
      errorId,
      correlationId,
    }, correlationId);

    try {
      await action.action();
      
      telemetryService.track('error_recovery.action_completed', {
        actionId: action.id,
        actionLabel: action.label,
        errorId,
        correlationId,
      }, correlationId);
    } catch (error) {
      telemetryService.track('error_recovery.action_failed', {
        actionId: action.id,
        actionLabel: action.label,
        error: error instanceof Error ? error.message : 'Unknown error',
        errorId,
        correlationId,
      }, correlationId);
    } finally {
      setActionStates(prev => ({ ...prev, [action.id]: false }));
    }
  };

  const containerClasses = [
    'error-recovery',
    compact && 'error-recovery--compact',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses} role="region" aria-labelledby="error-recovery-title">
      {!compact && (
        <div className="error-recovery__header">
          <div className="error-recovery__icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12l2 2 4-4"/>
              <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"/>
              <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"/>
              <path d="M12 3c0 1-1 3-3 3s-3-2-3-3 1-3 3-3 3 2 3 3"/>
              <path d="M12 21c0-1-1-3-3-3s-3 2-3 3 1 3 3 3 3-2 3-3"/>
            </svg>
          </div>
          <div className="error-recovery__text">
            <h3 id="error-recovery-title" className="error-recovery__title">
              {title}
            </h3>
            <p className="error-recovery__message">
              {message}
            </p>
          </div>
        </div>
      )}

      <div className="error-recovery__actions">
        {actions.map((action) => {
          const isLoading = actionStates[action.id] || action.loading;
          const isDisabled = action.disabled || isLoading;

          return (
            <button
              key={action.id}
              className={`error-recovery__action error-recovery__action--${action.variant || 'secondary'}`}
              onClick={() => handleActionClick(action)}
              disabled={isDisabled}
              type="button"
              aria-describedby={action.description ? `${action.id}-description` : undefined}
            >
              <div className="error-recovery__action-content">
                {action.icon && !isLoading && (
                  <div className="error-recovery__action-icon">
                    {action.icon}
                  </div>
                )}
                
                {isLoading && (
                  <div className="error-recovery__action-spinner">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12a9 9 0 11-6.219-8.56"/>
                    </svg>
                  </div>
                )}
                
                <div className="error-recovery__action-text">
                  <span className="error-recovery__action-label">
                    {action.label}
                  </span>
                  {action.description && !compact && (
                    <span
                      id={`${action.id}-description`}
                      className="error-recovery__action-description"
                    >
                      {action.description}
                    </span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// Predefined common recovery actions
export const createRetryAction = (
  onRetry: () => void | Promise<void>,
  options: Partial<RecoveryAction> = {}
): RecoveryAction => ({
  id: 'retry',
  label: 'Try Again',
  description: 'Retry the failed operation',
  icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 4 23 10 17 10"/>
      <polyline points="1 20 1 14 7 14"/>
      <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    </svg>
  ),
  action: onRetry,
  variant: 'primary',
  ...options,
});

export const createReloadAction = (
  options: Partial<RecoveryAction> = {}
): RecoveryAction => ({
  id: 'reload',
  label: 'Reload Page',
  description: 'Refresh the page to start over',
  icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 4 23 10 17 10"/>
      <polyline points="1 20 1 14 7 14"/>
      <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    </svg>
  ),
  action: () => window.location.reload(),
  variant: 'secondary',
  ...options,
});

export const createGoBackAction = (
  options: Partial<RecoveryAction> = {}
): RecoveryAction => ({
  id: 'go-back',
  label: 'Go Back',
  description: 'Return to the previous page',
  icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="15 18 9 12 15 6"/>
    </svg>
  ),
  action: () => window.history.back(),
  variant: 'secondary',
  ...options,
});

export const createContactSupportAction = (
  supportUrl: string,
  options: Partial<RecoveryAction> = {}
): RecoveryAction => ({
  id: 'contact-support',
  label: 'Contact Support',
  description: 'Get help from our support team',
  icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/>
      <path d="M17.657 16.657l-4.243 4.243a2 2 0 0 1 -2.827 0l-4.244 -4.243a8 8 0 1 1 11.314 0z"/>
    </svg>
  ),
  action: () => window.open(supportUrl, '_blank', 'noopener,noreferrer'),
  variant: 'secondary',
  ...options,
});

export const createReportIssueAction = (
  reportUrl: string,
  errorDetails?: any,
  options: Partial<RecoveryAction> = {}
): RecoveryAction => ({
  id: 'report-issue',
  label: 'Report Issue',
  description: 'Help us improve by reporting this problem',
  icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 9V5a3 3 0 0 0-6 0v4"/>
      <rect x="2" y="9" width="20" height="11" rx="2" ry="2"/>
      <circle cx="12" cy="15" r="1"/>
    </svg>
  ),
  action: () => {
    const params = new URLSearchParams();
    if (errorDetails) {
      params.set('error', JSON.stringify(errorDetails));
    }
    const url = `${reportUrl}?${params.toString()}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  },
  variant: 'secondary',
  ...options,
});

export default ErrorRecovery;