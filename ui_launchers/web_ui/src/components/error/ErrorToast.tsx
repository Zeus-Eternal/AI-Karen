'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useTelemetry } from '@/hooks/use-telemetry';

export interface ErrorToastProps {
  id?: string;
  message: string;
  title?: string;
  type?: 'error' | 'warning' | 'info' | 'success';
  duration?: number;
  persistent?: boolean;
  onClose?: () => void;
  actionLabel?: string;
  onAction?: () => void;
  correlationId?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  dismissible?: boolean;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  showProgress?: boolean;
  maxWidth?: string;
  className?: string;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  message,
  title,
  type = 'error',
  duration = 5000,
  persistent = false,
  onClose,
  actionLabel,
  onAction,
  correlationId,
  priority = 'medium',
  dismissible = true,
  position = 'top-right',
  showProgress = true,
  maxWidth = 'max-w-sm',
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(100);
  const [isPaused, setIsPaused] = useState(false);
  const { track } = useTelemetry();
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  const clearTimers = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    if (persistent || duration <= 0) return;

    clearTimers();
    
    const remainingTime = duration - (Date.now() - startTimeRef.current);
    if (remainingTime <= 0) {
      handleAutoClose();
      return;
    }

    // Main timer for auto-close
    timerRef.current = setTimeout(() => {
      handleAutoClose();
    }, remainingTime);

    // Progress timer
    if (showProgress) {
      const progressInterval = 50; // Update every 50ms
      progressTimerRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        const newProgress = Math.max(0, ((duration - elapsed) / duration) * 100);
        setProgress(newProgress);
        
        if (newProgress <= 0) {
          clearInterval(progressTimerRef.current!);
        }
      }, progressInterval);
    }
  }, [duration, persistent, showProgress]);

  const pauseTimer = useCallback(() => {
    if (isPaused) return;
    setIsPaused(true);
    clearTimers();
  }, [isPaused, clearTimers]);

  const resumeTimer = useCallback(() => {
    if (!isPaused) return;
    setIsPaused(false);
    startTimeRef.current = Date.now() - (duration * (1 - progress / 100));
    startTimer();
  }, [isPaused, progress, duration, startTimer]);

  const handleAutoClose = useCallback(() => {
    track('error_toast_auto_closed', {
      id,
      message,
      type,
      duration,
      correlationId,
      priority
    });
    handleClose();
  }, [id, message, type, duration, correlationId, priority, track]);

  const handleClose = useCallback(() => {
    if (isExiting) return;
    
    track('error_toast_dismissed', {
      id,
      message,
      type,
      correlationId,
      priority,
      timeVisible: Date.now() - startTimeRef.current
    });
    
    setIsExiting(true);
    clearTimers();
    
    setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, 300); // Animation duration
  }, [isExiting, id, message, type, correlationId, priority, track, clearTimers, onClose]);

  const handleAction = useCallback(() => {
    track('error_toast_action_clicked', {
      id,
      message,
      type,
      actionLabel,
      correlationId,
      priority
    });
    onAction?.();
  }, [id, message, type, actionLabel, correlationId, priority, track, onAction]);

  useEffect(() => {
    track('error_toast_shown', {
      id,
      message,
      title,
      type,
      duration,
      persistent,
      correlationId,
      priority,
      position
    });

    startTimer();

    return () => {
      clearTimers();
    };
  }, []);

  // Keyboard accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dismissible) {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [dismissible, handleClose]);

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2';
      case 'top-right':
        return 'top-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2';
      case 'bottom-right':
        return 'bottom-4 right-4';
      default:
        return 'top-4 right-4';
    }
  };

  const getTypeStyles = () => {
    const baseStyles = 'border shadow-lg backdrop-blur-sm';
    
    switch (type) {
      case 'error':
        return `${baseStyles} bg-red-50/95 border-red-200 text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200`;
      case 'warning':
        return `${baseStyles} bg-yellow-50/95 border-yellow-200 text-yellow-800 dark:bg-yellow-900/30 dark:border-yellow-800 dark:text-yellow-200`;
      case 'info':
        return `${baseStyles} bg-blue-50/95 border-blue-200 text-blue-800 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-200`;
      case 'success':
        return `${baseStyles} bg-green-50/95 border-green-200 text-green-800 dark:bg-green-900/30 dark:border-green-800 dark:text-green-200`;
      default:
        return `${baseStyles} bg-red-50/95 border-red-200 text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200`;
    }
  };

  const getPriorityStyles = () => {
    switch (priority) {
      case 'critical':
        return 'ring-2 ring-red-500 ring-opacity-50 animate-pulse';
      case 'high':
        return 'ring-1 ring-current ring-opacity-30';
      default:
        return '';
    }
  };

  const getIcon = () => {
    const iconClass = "w-5 h-5 flex-shrink-0";
    
    switch (type) {
      case 'error':
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case 'success':
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  if (!isVisible) return null;

  return (
    <div 
      className={`
        fixed z-50 ${maxWidth} w-full
        transform transition-all duration-300 ease-in-out
        ${getPositionClasses()}
        ${isExiting ? 'translate-x-full opacity-0 scale-95' : 'translate-x-0 opacity-100 scale-100'}
        ${className}
      `}
      role="alert"
      aria-live={priority === 'critical' ? 'assertive' : 'polite'}
      aria-atomic="true"
      onMouseEnter={pauseTimer}
      onMouseLeave={resumeTimer}
      onFocus={pauseTimer}
      onBlur={resumeTimer}
    >
      <div className={`
        relative flex items-start p-4 rounded-lg
        ${getTypeStyles()}
        ${getPriorityStyles()}
      `}>
        {/* Progress bar */}
        {showProgress && !persistent && duration > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/10 dark:bg-white/10 rounded-b-lg overflow-hidden">
            <div 
              className="h-full bg-current opacity-30 transition-all duration-75 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <div className="flex items-start space-x-3 w-full">
          {getIcon()}
          
          <div className="flex-1 min-w-0">
            {title && (
              <h4 className="text-sm font-semibold mb-1">
                {title}
              </h4>
            )}
            <p className="text-sm leading-5">
              {message}
            </p>
            
            {actionLabel && onAction && (
              <div className="mt-3">
                <button
                  onClick={handleAction}
                  className="text-sm font-medium underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current rounded transition-colors"
                >
                  {actionLabel}
                </button>
              </div>
            )}
          </div>
          
          {dismissible && (
            <div className="flex-shrink-0">
              <button
                onClick={handleClose}
                className="inline-flex rounded-md p-1.5 hover:bg-black/5 dark:hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current transition-colors"
                aria-label="Close notification"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Toast Container for managing multiple toasts
export interface ToastContainerProps {
  toasts: ErrorToastProps[];
  onRemove: (id: string) => void;
  maxToasts?: number;
  position?: ErrorToastProps['position'];
  className?: string;
}

export const ErrorToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onRemove,
  maxToasts = 5,
  position = 'top-right',
  className = ''
}) => {
  const { track } = useTelemetry();

  // Limit number of toasts and prioritize by priority
  const visibleToasts = toasts
    .sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return (priorityOrder[b.priority || 'medium'] || 2) - (priorityOrder[a.priority || 'medium'] || 2);
    })
    .slice(0, maxToasts);

  useEffect(() => {
    if (toasts.length > maxToasts) {
      track('toast_container_overflow', {
        totalToasts: toasts.length,
        maxToasts,
        position
      });
    }
  }, [toasts.length, maxToasts, position, track]);

  const getContainerPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4 items-start';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2 items-center';
      case 'top-right':
        return 'top-4 right-4 items-end';
      case 'bottom-left':
        return 'bottom-4 left-4 items-start';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2 items-center';
      case 'bottom-right':
        return 'bottom-4 right-4 items-end';
      default:
        return 'top-4 right-4 items-end';
    }
  };

  if (visibleToasts.length === 0) return null;

  return (
    <div 
      className={`fixed z-50 flex flex-col space-y-2 pointer-events-none ${getContainerPositionClasses()} ${className}`}
      aria-live="polite"
      aria-label="Notifications"
    >
      {visibleToasts.map((toast, index) => (
        <div key={toast.id} className="pointer-events-auto" style={{ zIndex: 1000 - index }}>
          <ErrorToast
            {...toast}
            position={position}
            onClose={() => onRemove(toast.id!)}
          />
        </div>
      ))}
    </div>
  );
};

export default ErrorToast;