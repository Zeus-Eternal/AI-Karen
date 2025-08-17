import type { AuthenticationError, FeedbackMessage, FeedbackMessageType } from './auth';

/**
 * Types and interfaces for authentication feedback components
 */

/**
 * Success message component props
 */
export interface SuccessMessageProps {
  message: string;
  onComplete?: () => void;
  autoRedirectDelay?: number;
  showProgress?: boolean;
}

/**
 * Error message component props
 */
export interface ErrorMessageProps {
  error: AuthenticationError;
  onRetry?: () => void;
  onDismiss?: () => void;
  showRetryButton?: boolean;
  showSupportLink?: boolean;
}

/**
 * Loading indicator component props
 */
export interface LoadingIndicatorProps {
  message: string;
  showProgress?: boolean;
  timeout?: number;
  onTimeout?: () => void;
  size?: 'small' | 'medium' | 'large';
}

/**
 * Feedback container component props
 */
export interface FeedbackContainerProps {
  message: FeedbackMessage | null;
  onDismiss?: () => void;
  className?: string;
}

/**
 * Toast notification props for feedback messages
 */
export interface ToastNotificationProps {
  type: FeedbackMessageType;
  title: string;
  message: string;
  duration?: number;
  onClose?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Progress indicator props for loading states
 */
export interface ProgressIndicatorProps {
  progress: number;
  message?: string;
  showPercentage?: boolean;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

/**
 * Countdown timer props for rate limiting
 */
export interface CountdownTimerProps {
  endTime: Date;
  onComplete?: () => void;
  format?: 'mm:ss' | 'seconds' | 'minutes';
  showIcon?: boolean;
}

/**
 * Alert banner props for important messages
 */
export interface AlertBannerProps {
  type: 'info' | 'warning' | 'error' | 'success';
  title?: string;
  message: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'outline';
  }>;
}

/**
 * Status indicator props for authentication states
 */
export interface StatusIndicatorProps {
  status: 'idle' | 'loading' | 'success' | 'error' | 'warning';
  message?: string;
  size?: 'small' | 'medium' | 'large';
  showIcon?: boolean;
}

/**
 * Feedback animation configuration
 */
export interface FeedbackAnimationConfig {
  enter: {
    duration: number;
    easing: string;
  };
  exit: {
    duration: number;
    easing: string;
  };
  bounce?: boolean;
  fade?: boolean;
}

/**
 * Default animation configurations
 */
export const DEFAULT_FEEDBACK_ANIMATIONS: Record<FeedbackMessageType, FeedbackAnimationConfig> = {
  success: {
    enter: { duration: 300, easing: 'ease-out' },
    exit: { duration: 200, easing: 'ease-in' },
    bounce: true,
    fade: true
  },
  error: {
    enter: { duration: 400, easing: 'ease-out' },
    exit: { duration: 300, easing: 'ease-in' },
    bounce: false,
    fade: true
  },
  warning: {
    enter: { duration: 300, easing: 'ease-out' },
    exit: { duration: 200, easing: 'ease-in' },
    bounce: false,
    fade: true
  },
  info: {
    enter: { duration: 250, easing: 'ease-out' },
    exit: { duration: 200, easing: 'ease-in' },
    bounce: false,
    fade: true
  }
};

/**
 * Feedback message factory functions
 */
export class FeedbackMessageFactory {
  static createSuccessMessage(
    title: string,
    message: string,
    autoHide: boolean = true,
    duration: number = 3000
  ): FeedbackMessage {
    return {
      type: 'success',
      title,
      message,
      autoHide,
      duration
    };
  }

  static createErrorMessage(
    title: string,
    message: string,
    onRetry?: () => void,
    autoHide: boolean = false
  ): FeedbackMessage {
    return {
      type: 'error',
      title,
      message,
      action: onRetry ? {
        label: 'Try Again',
        onClick: onRetry
      } : undefined,
      autoHide
    };
  }

  static createWarningMessage(
    title: string,
    message: string,
    autoHide: boolean = true,
    duration: number = 5000
  ): FeedbackMessage {
    return {
      type: 'warning',
      title,
      message,
      autoHide,
      duration
    };
  }

  static createInfoMessage(
    title: string,
    message: string,
    autoHide: boolean = true,
    duration: number = 4000
  ): FeedbackMessage {
    return {
      type: 'info',
      title,
      message,
      autoHide,
      duration
    };
  }

  static fromAuthError(
    error: AuthenticationError,
    onRetry?: () => void
  ): FeedbackMessage {
    const errorConfig = ERROR_MESSAGES[error.type];
    
    return {
      type: 'error',
      title: errorConfig.title,
      message: error.retryAfter 
        ? errorConfig.message.replace('{retryAfter}', formatRetryTime(error.retryAfter))
        : errorConfig.message,
      action: onRetry && errorConfig.action ? {
        label: errorConfig.action.label,
        onClick: onRetry
      } : undefined,
      autoHide: false
    };
  }
}

/**
 * Feedback state management types
 */
export interface FeedbackState {
  message: FeedbackMessage | null;
  isVisible: boolean;
  queue: FeedbackMessage[];
}

/**
 * Feedback actions for state management
 */
export type FeedbackAction = 
  | { type: 'SHOW_MESSAGE'; payload: FeedbackMessage }
  | { type: 'HIDE_MESSAGE' }
  | { type: 'CLEAR_MESSAGE' }
  | { type: 'QUEUE_MESSAGE'; payload: FeedbackMessage }
  | { type: 'PROCESS_QUEUE' };

/**
 * Feedback reducer for state management
 */
export function feedbackReducer(state: FeedbackState, action: FeedbackAction): FeedbackState {
  switch (action.type) {
    case 'SHOW_MESSAGE':
      return {
        ...state,
        message: action.payload,
        isVisible: true
      };
    
    case 'HIDE_MESSAGE':
      return {
        ...state,
        isVisible: false
      };
    
    case 'CLEAR_MESSAGE':
      return {
        ...state,
        message: null,
        isVisible: false
      };
    
    case 'QUEUE_MESSAGE':
      return {
        ...state,
        queue: [...state.queue, action.payload]
      };
    
    case 'PROCESS_QUEUE':
      if (state.queue.length > 0 && !state.isVisible) {
        const [nextMessage, ...remainingQueue] = state.queue;
        return {
          ...state,
          message: nextMessage,
          isVisible: true,
          queue: remainingQueue
        };
      }
      return state;
    
    default:
      return state;
  }
}

/**
 * Initial feedback state
 */
export const initialFeedbackState: FeedbackState = {
  message: null,
  isVisible: false,
  queue: []
};

// Import helper functions from auth-utils
import { ERROR_MESSAGES, formatRetryTime } from './auth-utils';