/**
 * Error categorization system for backend connectivity and authentication
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

export enum ErrorCategory {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION', 
  DATABASE = 'DATABASE',
  CONFIGURATION = 'CONFIGURATION',
  TIMEOUT = 'TIMEOUT',
  VALIDATION = 'VALIDATION',
  UNKNOWN = 'UNKNOWN'
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export interface CategorizedError {
  category: ErrorCategory;
  severity: ErrorSeverity;
  code: string;
  message: string;
  userMessage: string;
  retryable: boolean;
  maxRetries: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
  fallbackAction?: string;
  timestamp: Date;
  correlationId?: string;
  context?: Record<string, any>;
}

export interface ErrorPattern {
  pattern: RegExp | string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  retryable: boolean;
  maxRetries: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
  fallbackAction?: string;
}

/**
 * Error patterns for categorizing different types of failures
 */
export const ERROR_PATTERNS: ErrorPattern[] = [
  // Network Errors
  {
    pattern: /ECONNREFUSED|ENOTFOUND|ECONNRESET|ETIMEDOUT/i,
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    maxRetries: 3,
    backoffStrategy: 'exponential',
    fallbackAction: 'USE_FALLBACK_BACKEND'
  },
  {
    pattern: /fetch.*failed|NetworkError|ERR_NETWORK/i,
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    maxRetries: 3,
    backoffStrategy: 'exponential'
  },
  
  // Authentication Errors (put specific patterns first)
  {
    pattern: /authentication.*timeout|auth.*timeout/i,
    category: ErrorCategory.TIMEOUT,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    maxRetries: 2,
    backoffStrategy: 'fixed'
  },
  {
    pattern: /unauthorized|401|invalid.*credentials|authentication.*failed/i,
    category: ErrorCategory.AUTHENTICATION,
    severity: ErrorSeverity.MEDIUM,
    retryable: false,
    maxRetries: 0,
    backoffStrategy: 'fixed'
  },
  {
    pattern: /session.*expired|token.*expired|403/i,
    category: ErrorCategory.AUTHENTICATION,
    severity: ErrorSeverity.MEDIUM,
    retryable: true,
    maxRetries: 1,
    backoffStrategy: 'fixed',
    fallbackAction: 'REFRESH_SESSION'
  },
  
  // Database Errors
  {
    pattern: /database.*connection|connection.*pool|db.*timeout/i,
    category: ErrorCategory.DATABASE,
    severity: ErrorSeverity.CRITICAL,
    retryable: true,
    maxRetries: 5,
    backoffStrategy: 'linear',
    fallbackAction: 'ENABLE_DEGRADED_MODE'
  },
  {
    pattern: /constraint.*violation|duplicate.*key|foreign.*key/i,
    category: ErrorCategory.DATABASE,
    severity: ErrorSeverity.MEDIUM,
    retryable: false,
    maxRetries: 0,
    backoffStrategy: 'fixed'
  },
  
  // Configuration Errors
  {
    pattern: /invalid.*url|missing.*environment|config.*error/i,
    category: ErrorCategory.CONFIGURATION,
    severity: ErrorSeverity.CRITICAL,
    retryable: false,
    maxRetries: 0,
    backoffStrategy: 'fixed'
  },
  
  // Timeout Errors
  {
    pattern: /timeout|timed.*out|request.*timeout/i,
    category: ErrorCategory.TIMEOUT,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    maxRetries: 3,
    backoffStrategy: 'exponential'
  },
  
  // Validation Errors
  {
    pattern: /validation.*error|invalid.*input|bad.*request|400/i,
    category: ErrorCategory.VALIDATION,
    severity: ErrorSeverity.LOW,
    retryable: false,
    maxRetries: 0,
    backoffStrategy: 'fixed'
  }
];

/**
 * User-friendly error messages for each error category
 */
export const USER_ERROR_MESSAGES: Record<ErrorCategory, Record<string, string>> = {
  [ErrorCategory.NETWORK]: {
    default: 'Unable to connect to server. Please check your internet connection and try again.',
    retry: 'Connection failed. Retrying...',
    fallback: 'Primary server unavailable. Switching to backup server...'
  },
  [ErrorCategory.AUTHENTICATION]: {
    default: 'Authentication failed. Please check your credentials and try again.',
    expired: 'Your session has expired. Please log in again.',
    timeout: 'Login is taking longer than expected. Please wait...',
    invalid: 'Invalid username or password. Please try again.'
  },
  [ErrorCategory.DATABASE]: {
    default: 'Database service temporarily unavailable. Please try again in a moment.',
    connection: 'Unable to connect to database. Please try again later.',
    timeout: 'Database operation timed out. Please try again.',
    degraded: 'Running in limited mode due to database issues.'
  },
  [ErrorCategory.CONFIGURATION]: {
    default: 'System configuration error. Please contact support.',
    missing: 'Required configuration is missing. Please contact your administrator.',
    invalid: 'Invalid system configuration detected.'
  },
  [ErrorCategory.TIMEOUT]: {
    default: 'Request timed out. Please try again.',
    retry: 'Operation is taking longer than expected. Retrying...',
    extended: 'This operation may take a few moments. Please be patient.'
  },
  [ErrorCategory.VALIDATION]: {
    default: 'Invalid input provided. Please check your data and try again.',
    required: 'Required fields are missing. Please complete all required information.',
    format: 'Invalid format detected. Please check your input.'
  },
  [ErrorCategory.UNKNOWN]: {
    default: 'An unexpected error occurred. Please try again or contact support.',
    retry: 'Something went wrong. Retrying...',
    support: 'Persistent error detected. Please contact support with error code.'
  }
};