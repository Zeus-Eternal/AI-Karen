import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ErrorToast, ErrorToastProps } from './ErrorToast';
import { telemetryService } from '../../lib/telemetry';

export interface ToastOptions {
  title: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  duration?: number;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    action: () => void | Promise<void>;
    variant?: 'primary' | 'secondary' | 'danger';
  }>;
  correlationId?: string;
}

export interface ToastContextValue {
  showToast: (options: ToastOptions) => string;
  dismissToast: (id: string) => void;
  dismissAll: () => void;
  toasts: ErrorToastProps[];
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export interface ToastProviderProps {
  children: ReactNode;
  maxToasts?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

export const ToastProvider: React.FC<ToastProviderProps> = ({
  children,
  maxToasts = 5,
  position = 'top-right',
}) => {
  const [toasts, setToasts] = useState<ErrorToastProps[]>([]);

  const generateId = useCallback(() => {
    return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const showToast = useCallback((options: ToastOptions): string => {
    const id = generateId();
    
    const newToast: ErrorToastProps = {
      id,
      ...options,
      onDismiss: (toastId) => dismissToast(toastId),
    };

    setToasts(prev => {
      const updated = [newToast, ...prev];
      
      // Limit number of toasts
      if (updated.length > maxToasts) {
        const removed = updated.slice(maxToasts);
        removed.forEach(toast => {
          telemetryService.track('error_toast.auto_dismissed', {
            id: toast.id,
            reason: 'max_toasts_exceeded',
            correlationId: toast.correlationId,
          }, toast.correlationId);
        });
        return updated.slice(0, maxToasts);
      }
      
      return updated;
    });

    telemetryService.track('error_toast.created', {
      id,
      type: options.type || 'error',
      title: options.title,
      persistent: options.persistent || false,
      correlationId: options.correlationId,
    }, options.correlationId);

    return id;
  }, [generateId, maxToasts]);

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    const currentToasts = toasts;
    setToasts([]);
    
    currentToasts.forEach(toast => {
      telemetryService.track('error_toast.dismissed_all', {
        id: toast.id,
        correlationId: toast.correlationId,
      }, toast.correlationId);
    });
  }, [toasts]);

  const contextValue: ToastContextValue = {
    showToast,
    dismissToast,
    dismissAll,
    toasts,
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ErrorToastContainer toasts={toasts} position={position} />
    </ToastContext.Provider>
  );
};

interface ErrorToastContainerProps {
  toasts: ErrorToastProps[];
  position: string;
}

const ErrorToastContainer: React.FC<ErrorToastContainerProps> = ({ toasts, position }) => {
  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      className={`error-toast-container error-toast-container--${position}`}
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map(toast => (
        <ErrorToast key={toast.id} {...toast} />
      ))}
    </div>
  );
};

// Utility functions for common toast types
export const useErrorToast = () => {
  const { showToast } = useToast();
  
  return {
    showError: (title: string, message: string, options?: Partial<ToastOptions>) =>
      showToast({ ...options, title, message, type: 'error' }),
    
    showWarning: (title: string, message: string, options?: Partial<ToastOptions>) =>
      showToast({ ...options, title, message, type: 'warning' }),
    
    showInfo: (title: string, message: string, options?: Partial<ToastOptions>) =>
      showToast({ ...options, title, message, type: 'info' }),
    
    showNetworkError: (error: Error, options?: Partial<ToastOptions>) =>
      showToast({
        ...options,
        title: 'Network Error',
        message: error.message || 'A network error occurred. Please check your connection and try again.',
        type: 'error',
        actions: [
          {
            label: 'Retry',
            action: () => window.location.reload(),
            variant: 'primary',
          },
        ],
      }),
    
    showValidationError: (field: string, message: string, options?: Partial<ToastOptions>) =>
      showToast({
        ...options,
        title: `${field} Error`,
        message,
        type: 'error',
        duration: 3000,
      }),
  };
};

export default ToastProvider;