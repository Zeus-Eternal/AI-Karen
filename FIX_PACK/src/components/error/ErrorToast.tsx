import React, { useEffect, useState } from 'react';
import { telemetryService } from '../../lib/telemetry';

export interface ErrorToastProps {
  id: string;
  title: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  duration?: number;
  persistent?: boolean;
  actions?: ErrorToastAction[];
  onDismiss?: (id: string) => void;
  correlationId?: string;
}

export interface ErrorToastAction {
  label: string;
  action: () => void | Promise<void>;
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  id,
  title,
  message,
  type = 'error',
  duration = 5000,
  persistent = false,
  actions = [],
  onDismiss,
  correlationId,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);
  const [actionStates, setActionStates] = useState<Record<string, boolean>>({});

  useEffect(() => {
    telemetryService.track('error_toast.displayed', {
      id,
      type,
      title,
      persistent,
      correlationId,
    }, correlationId);

    if (!persistent && duration > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, type, title, persistent, duration, correlationId]);

  const handleDismiss = () => {
    setIsExiting(true);
    
    telemetryService.track('error_toast.dismissed', {
      id,
      type,
      correlationId,
    }, correlationId);

    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.(id);
    }, 300); // Match CSS animation duration
  };

  const handleActionClick = async (actionIndex: number, action: ErrorToastAction) => {
    const actionKey = `action_${actionIndex}`;
    
    setActionStates(prev => ({ ...prev, [actionKey]: true }));
    
    telemetryService.track('error_toast.action_clicked', {
      id,
      actionIndex,
      actionLabel: action.label,
      correlationId,
    }, correlationId);

    try {
      await action.action();
      
      telemetryService.track('error_toast.action_completed', {
        id,
        actionIndex,
        actionLabel: action.label,
        correlationId,
      }, correlationId);
    } catch (error) {
      telemetryService.track('error_toast.action_failed', {
        id,
        actionIndex,
        actionLabel: action.label,
        error: error instanceof Error ? error.message : 'Unknown error',
        correlationId,
      }, correlationId);
    } finally {
      setActionStates(prev => ({ ...prev, [actionKey]: false }));
    }
  };

  if (!isVisible) {
    return null;
  }

  const getIcon = () => {
    switch (type) {
      case 'error':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        );
      case 'warning':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        );
      case 'info':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className={`error-toast error-toast--${type} ${isExiting ? 'error-toast--exiting' : ''}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="error-toast__content">
        <div className="error-toast__icon">
          {getIcon()}
        </div>
        
        <div className="error-toast__text">
          <div className="error-toast__title">{title}</div>
          <div className="error-toast__message">{message}</div>
        </div>

        {!persistent && (
          <button
            className="error-toast__dismiss"
            onClick={handleDismiss}
            aria-label="Dismiss notification"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        )}
      </div>

      {actions.length > 0 && (
        <div className="error-toast__actions">
          {actions.map((action, index) => {
            const actionKey = `action_${index}`;
            const isLoading = actionStates[actionKey] || action.loading;
            
            return (
              <button
                key={index}
                className={`error-toast__action error-toast__action--${action.variant || 'secondary'}`}
                onClick={() => handleActionClick(index, action)}
                disabled={isLoading}
                type="button"
              >
                {isLoading && (
                  <svg
                    className="error-toast__action-spinner"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                  </svg>
                )}
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ErrorToast;