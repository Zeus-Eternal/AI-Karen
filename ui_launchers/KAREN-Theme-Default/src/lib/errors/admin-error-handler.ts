/**
 * Admin Error Handler
 * 
 * Centralized error handling system for admin operations with user-friendly
 * error messages and suggested remediation steps.
 * 
 * Requirements: 7.2, 7.4
 */
export interface AdminError {
  code: string;
  message: string;
  details?: string;
  remediation?: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  retryable: boolean;
}
export interface ErrorContext {
  operation: string;
  resource?: string;
  userId?: string;
  timestamp: Date;
}
export class AdminErrorHandler {
  private static errorMap: Record<string, Omit<AdminError, 'details'>> = {
    // Authentication Errors
    'AUTH_INSUFFICIENT_PERMISSIONS': {
      code: 'AUTH_INSUFFICIENT_PERMISSIONS',
      message: 'You do not have sufficient permissions to perform this action.',
      remediation: [
        'Contact your system administrator to request the necessary permissions',
        'Verify you are logged in with the correct account',
        'Check if your session has expired and try logging in again'
      ],
      severity: 'medium',
      retryable: false
    },
    'AUTH_SESSION_EXPIRED': {
      code: 'AUTH_SESSION_EXPIRED',
      message: 'Your session has expired. Please log in again.',
      remediation: [
        'Click the login button to authenticate again',
        'Ensure cookies are enabled in your browser',
        'Clear your browser cache if the problem persists'
      ],
      severity: 'medium',
      retryable: true
    },
    'AUTH_INVALID_CREDENTIALS': {
      code: 'AUTH_INVALID_CREDENTIALS',
      message: 'Invalid email or password.',
      remediation: [
        'Double-check your email address and password',
        'Use the "Forgot Password" link if you cannot remember your password',
        'Contact support if you continue to have login issues'
      ],
      severity: 'low',
      retryable: true
    },
    // User Management Errors
    'USER_NOT_FOUND': {
      code: 'USER_NOT_FOUND',
      message: 'The requested user could not be found.',
      remediation: [
        'Verify the user ID or email address is correct',
        'Check if the user has been deleted recently',
        'Refresh the page to ensure you have the latest data'
      ],
      severity: 'medium',
      retryable: true
    },
    'USER_EMAIL_EXISTS': {
      code: 'USER_EMAIL_EXISTS',
      message: 'A user with this email address already exists.',
      remediation: [
        'Use a different email address',
        'Check if the user already exists in the system',
        'Consider updating the existing user instead of creating a new one'
      ],
      severity: 'low',
      retryable: false
    },
    'USER_CANNOT_DELETE_SELF': {
      code: 'USER_CANNOT_DELETE_SELF',
      message: 'You cannot delete your own account.',
      remediation: [
        'Ask another administrator to delete your account',
        'Transfer your responsibilities to another admin first',
        'Consider deactivating the account instead of deleting it'
      ],
      severity: 'low',
      retryable: false
    },
    'USER_CANNOT_DEMOTE_LAST_ADMIN': {
      code: 'USER_CANNOT_DEMOTE_LAST_ADMIN',
      message: 'Cannot demote the last administrator in the system.',
      remediation: [
        'Promote another user to admin first',
        'Ensure there is always at least one active administrator',
        'Contact system support if you need to change the admin structure'
      ],
      severity: 'high',
      retryable: false
    },
    // Validation Errors
    'VALIDATION_WEAK_PASSWORD': {
      code: 'VALIDATION_WEAK_PASSWORD',
      message: 'Password does not meet security requirements.',
      remediation: [
        'Use at least 12 characters',
        'Include uppercase and lowercase letters',
        'Add numbers and special characters',
        'Avoid common words or personal information'
      ],
      severity: 'medium',
      retryable: true
    },
    'VALIDATION_INVALID_EMAIL': {
      code: 'VALIDATION_INVALID_EMAIL',
      message: 'Please enter a valid email address.',
      remediation: [
        'Check for typos in the email address',
        'Ensure the email follows the format: user@domain.com',
        'Verify the domain name is spelled correctly'
      ],
      severity: 'low',
      retryable: true
    },
    'VALIDATION_REQUIRED_FIELD': {
      code: 'VALIDATION_REQUIRED_FIELD',
      message: 'This field is required.',
      remediation: [
        'Fill in all required fields marked with an asterisk (*)',
        'Check that no required information is missing',
        'Ensure all mandatory data is provided'
      ],
      severity: 'low',
      retryable: true
    },
    // System Errors
    'SYSTEM_DATABASE_ERROR': {
      code: 'SYSTEM_DATABASE_ERROR',
      message: 'A database error occurred. Please try again.',
      remediation: [
        'Wait a moment and try the operation again',
        'Check your internet connection',
        'Contact support if the error persists',
        'Try refreshing the page'
      ],
      severity: 'high',
      retryable: true
    },
    'SYSTEM_NETWORK_ERROR': {
      code: 'SYSTEM_NETWORK_ERROR',
      message: 'Network connection error. Please check your connection.',
      remediation: [
        'Check your internet connection',
        'Try refreshing the page',
        'Wait a moment and try again',
        'Contact your network administrator if the problem persists'
      ],
      severity: 'medium',
      retryable: true
    },
    'SYSTEM_SERVER_ERROR': {
      code: 'SYSTEM_SERVER_ERROR',
      message: 'An internal server error occurred.',
      remediation: [
        'Try the operation again in a few minutes',
        'Check the system status page',
        'Contact technical support if the error continues',
        'Save your work and try again later'
      ],
      severity: 'high',
      retryable: true
    },
    // Bulk Operation Errors
    'BULK_OPERATION_PARTIAL_FAILURE': {
      code: 'BULK_OPERATION_PARTIAL_FAILURE',
      message: 'Some items in the bulk operation failed to process.',
      remediation: [
        'Review the detailed error report',
        'Retry the operation for failed items only',
        'Check individual item permissions and validity',
        'Consider processing items in smaller batches'
      ],
      severity: 'medium',
      retryable: true
    },
    'BULK_OPERATION_TOO_LARGE': {
      code: 'BULK_OPERATION_TOO_LARGE',
      message: 'The bulk operation is too large to process.',
      remediation: [
        'Reduce the number of items in the operation',
        'Process items in smaller batches',
        'Consider using the import/export functionality',
        'Contact support for assistance with large operations'
      ],
      severity: 'medium',
      retryable: true
    },
    // Email Errors
    'EMAIL_SEND_FAILED': {
      code: 'EMAIL_SEND_FAILED',
      message: 'Failed to send email notification.',
      remediation: [
        'Check the recipient email address is valid',
        'Verify email service configuration',
        'Try sending the email again',
        'Contact the user through alternative means'
      ],
      severity: 'medium',
      retryable: true
    },
    'EMAIL_TEMPLATE_ERROR': {
      code: 'EMAIL_TEMPLATE_ERROR',
      message: 'Email template processing failed.',
      remediation: [
        'Check the email template configuration',
        'Verify all required template variables are provided',
        'Contact support to review the email template',
        'Try using a different email template'
      ],
      severity: 'medium',
      retryable: true
    }
  };
  static createError(
    code: string, 
    details?: string, 
    _context?: ErrorContext
  ): AdminError {
    const baseError = this.errorMap[code];
    if (!baseError) {
      return {
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred.',
        details: details || `Unknown error code: ${code}`,
        remediation: [
          'Try refreshing the page',
          'Contact support with the error details',
          'Check the browser console for more information'
        ],
        severity: 'medium',
        retryable: true
      };
    }
    return {
      ...baseError,
      details: details || baseError.message
    };
  }
  static fromHttpError(
    status: number, 
    response?: unknown, 
    _context?: ErrorContext
  ): AdminError {
    switch (status) {
      case 400:
        return this.createError('VALIDATION_ERROR', response?.message);
      case 401:
        return this.createError('AUTH_SESSION_EXPIRED');
      case 403:
        return this.createError('AUTH_INSUFFICIENT_PERMISSIONS');
      case 404:
        return this.createError('USER_NOT_FOUND');
      case 409:
        return this.createError('USER_EMAIL_EXISTS', response?.message);
      case 422:
        return this.createError('VALIDATION_REQUIRED_FIELD', response?.message);
      case 429:
        return {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests. Please wait before trying again.',
          details: response?.message,
          remediation: [
            'Wait a few minutes before trying again',
            'Reduce the frequency of your requests',
            'Contact support if you need higher rate limits'
          ],
          severity: 'medium',
          retryable: true
        };
      case 500:
        return this.createError('SYSTEM_SERVER_ERROR');
      case 502:
      case 503:
      case 504:
        return this.createError('SYSTEM_NETWORK_ERROR');
      default:
        return this.createError('UNKNOWN_ERROR', `HTTP ${status}: ${response?.message || 'Unknown error'}`);
    }
  }
  static fromNetworkError(error: Error, _context?: ErrorContext): AdminError {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return this.createError('SYSTEM_NETWORK_ERROR', error.message);
    }
    if (error.name === 'AbortError') {
      return {
        code: 'OPERATION_CANCELLED',
        message: 'Operation was cancelled.',
        details: error.message,
        remediation: [
          'Try the operation again if needed',
          'Ensure you have a stable internet connection',
          'Contact support if cancellations happen frequently'
        ],
        severity: 'low',
        retryable: true
      };
    }
    return this.createError('UNKNOWN_ERROR', error.message);
  }
  static getRetryDelay(error: AdminError, attemptNumber: number): number {
    if (!error.retryable) return 0;
    // Exponential backoff with jitter
    const baseDelay = Math.min(1000 * Math.pow(2, attemptNumber - 1), 30000);
    const jitter = Math.random() * 1000;
    return baseDelay + jitter;
  }
  static shouldRetry(error: AdminError, attemptNumber: number): boolean {
    if (!error.retryable) return false;
    if (attemptNumber >= 3) return false;
    // Don't retry validation errors or permission errors
    if (error.severity === 'low' && error.code.startsWith('VALIDATION_')) return false;
    if (error.code.startsWith('AUTH_')) return false;
    return true;
  }
  static logError(error: AdminError, context?: ErrorContext): void {
    const logData = {
      error: error.code,
      message: error.message,
      details: error.details,
      severity: error.severity,
      context,
      timestamp: new Date().toISOString()
    };
    switch (error.severity) {
      case 'critical':
      case 'high':
        console.error('[AdminError]', error.message, logData);
        break;
      case 'medium':
        console.warn('[AdminError]', error.message, logData);
        break;
      case 'low':
        console.info('[AdminError]', error.message, logData);
        break;
    }
    // In production, send to error tracking service
    if (typeof window !== 'undefined' && (window as unknown).errorTracker) {
      (window as unknown).errorTracker.captureException(error, { extra: logData });
    }
  }
}
export default AdminErrorHandler;
