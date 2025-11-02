import type {
  AuthenticationError,
  AuthenticationErrorType,
  ValidationErrors,
  ValidationRule,
  ValidationConfig,
  LoginCredentials,
  ErrorClassification,
  ErrorMessageConfig,
  RetryConfig
} from './auth';

/**
 * Utility functions for authentication error handling and validation
 */

/**
 * Error message mapping for different error types
 */
export const ERROR_MESSAGES: Record<AuthenticationErrorType, ErrorMessageConfig> = {
  'invalid_credentials': {
    title: 'Login Failed',
    message: 'Invalid email or password. Please check your credentials and try again.',
    action: { label: 'Try Again', type: 'retry' }
  },
  'network_error': {
    title: 'Connection Problem',
    message: 'Unable to connect to the server. Please check your internet connection and try again.',
    action: { label: 'Retry', type: 'retry' }
  },
  'rate_limit': {
    title: 'Too Many Attempts',
    message: 'Too many login attempts. Please wait before trying again.',
    action: { label: 'OK', type: 'dismiss' }
  },
  'security_block': {
    title: 'Security Verification Required',
    message: 'Your login attempt has been blocked for security reasons. Please verify your identity through alternative means.',
    action: { label: 'Contact Support', type: 'support' }
  },
  'verification_required': {
    title: 'Email Verification Required',
    message: 'Please verify your email address before logging in. Check your inbox for a verification link.',
    action: { label: 'Resend Email', type: 'resend_verification' }
  },
  'account_locked': {
    title: 'Account Locked',
    message: 'Your account has been temporarily locked due to multiple failed login attempts.',
    action: { label: 'Reset Password', type: 'reset_password' }
  },
  'account_suspended': {
    title: 'Account Suspended',
    message: 'Your account has been suspended. Please contact support for assistance.',
    action: { label: 'Contact Support', type: 'support' }
  },
  'two_factor_required': {
    title: 'Two-Factor Authentication Required',
    message: 'Please enter your two-factor authentication code to continue.',
    action: { label: 'OK', type: 'dismiss' }
  },
  'two_factor_invalid': {
    title: 'Invalid 2FA Code',
    message: 'The two-factor authentication code you entered is invalid. Please try again.',
    action: { label: 'Try Again', type: 'retry' }
  },
  'server_error': {
    title: 'Server Error',
    message: 'An unexpected server error occurred. Please try again later or contact support if the problem persists.',
    action: { label: 'Contact Support', type: 'support' }
  },
  'validation_error': {
    title: 'Validation Error',
    message: 'Please correct the errors in the form and try again.',
    action: { label: 'OK', type: 'dismiss' }
  },
  'timeout_error': {
    title: 'Request Timeout',
    message: 'The request timed out. Please check your connection and try again.',
    action: { label: 'Retry', type: 'retry' }
  },
  'unknown_error': {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred. Please try again or contact support if the problem persists.',
    action: { label: 'Contact Support', type: 'support' }
  }
};

/**
 * Error classification mapping for different error types
 */
export const ERROR_CLASSIFICATIONS: Record<AuthenticationErrorType, ErrorClassification> = {
  'invalid_credentials': {
    category: 'authentication',
    severity: 'medium',
    userAction: 'correct_input',
    retryable: true,
    supportContact: false
  },
  'network_error': {
    category: 'network',
    severity: 'medium',
    userAction: 'check_connection',
    retryable: true,
    supportContact: false
  },
  'rate_limit': {
    category: 'rate_limit',
    severity: 'medium',
    userAction: 'wait',
    retryable: true,
    supportContact: false
  },
  'security_block': {
    category: 'security',
    severity: 'high',
    userAction: 'contact_support',
    retryable: false,
    supportContact: true
  },
  'verification_required': {
    category: 'authentication',
    severity: 'medium',
    userAction: 'verify_email',
    retryable: false,
    supportContact: false
  },
  'account_locked': {
    category: 'security',
    severity: 'high',
    userAction: 'reset_password',
    retryable: false,
    supportContact: true
  },
  'account_suspended': {
    category: 'security',
    severity: 'critical',
    userAction: 'contact_support',
    retryable: false,
    supportContact: true
  },
  'two_factor_required': {
    category: 'authentication',
    severity: 'low',
    userAction: 'correct_input',
    retryable: true,
    supportContact: false
  },
  'two_factor_invalid': {
    category: 'authentication',
    severity: 'low',
    userAction: 'correct_input',
    retryable: true,
    supportContact: false
  },
  'server_error': {
    category: 'server',
    severity: 'high',
    userAction: 'contact_support',
    retryable: true,
    supportContact: true
  },
  'validation_error': {
    category: 'validation',
    severity: 'low',
    userAction: 'correct_input',
    retryable: true,
    supportContact: false
  },
  'timeout_error': {
    category: 'network',
    severity: 'medium',
    userAction: 'retry',
    retryable: true,
    supportContact: false
  },
  'unknown_error': {
    category: 'server',
    severity: 'high',
    userAction: 'contact_support',
    retryable: true,
    supportContact: true
  }
};

/**
 * Creates a standardized authentication error
 */
export function createAuthError(
  type: AuthenticationErrorType,
  message?: string,
  details?: any,
  retryAfter?: number
): AuthenticationError {
  return {
    type,
    message: message || ERROR_MESSAGES[type].message,
    details,
    retryAfter,
    timestamp: new Date(),
    requestId: generateRequestId()
  };
}

/**
 * Generates a unique request ID for error tracking
 */
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Classifies an authentication error
 */
export function classifyError(errorType: AuthenticationErrorType): ErrorClassification {
  return ERROR_CLASSIFICATIONS[errorType];
}

/**
 * Gets user-friendly error message configuration
 */
export function getErrorMessage(errorType: AuthenticationErrorType): ErrorMessageConfig {
  return ERROR_MESSAGES[errorType];
}

/**
 * Determines if an error is retryable
 */
export function isRetryableError(error: AuthenticationError): boolean {
  const classification = classifyError(error.type);
  return classification.retryable;
}

/**
 * Determines if an error requires support contact
 */
export function requiresSupportContact(error: AuthenticationError): boolean {
  const classification = classifyError(error.type);
  return classification.supportContact;
}

/**
 * Email validation rules
 */
export const EMAIL_VALIDATION_RULES: ValidationRule[] = [
  {
    validate: (value: string) => value.trim().length > 0,
    message: 'Email is required'
  },
  {
    validate: (value: string) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value.trim());
    },
    message: 'Please enter a valid email address'
  },
  {
    validate: (value: string) => value.trim().length <= 254,
    message: 'Email address is too long'
  }
];

/**
 * Password validation rules
 */
export const PASSWORD_VALIDATION_RULES: ValidationRule[] = [
  {
    validate: (value: string) => value.length > 0,
    message: 'Password is required'
  },
  {
    validate: (value: string) => value.length >= 8,
    message: 'Password must be at least 8 characters long'
  },
  {
    validate: (value: string) => value.length <= 128,
    message: 'Password is too long'
  }
];

/**
 * TOTP code validation rules
 */
export const TOTP_VALIDATION_RULES: ValidationRule[] = [
  {
    validate: (value: string) => value.trim().length > 0,
    message: '2FA code is required'
  },
  {
    validate: (value: string) => {
      const totpRegex = /^\d{6}$/;
      return totpRegex.test(value.trim());
    },
    message: '2FA code must be 6 digits'
  }
];

/**
 * Default validation configuration
 */
export const DEFAULT_VALIDATION_CONFIG: ValidationConfig = {
  email: EMAIL_VALIDATION_RULES,
  password: PASSWORD_VALIDATION_RULES,
  totp_code: TOTP_VALIDATION_RULES
};

/**
 * Validates a single field against its rules
 */
export function validateField(
  field: keyof LoginCredentials,
  value: string,
  rules: ValidationRule[]
): string | null {
  for (const rule of rules) {
    if (!rule.validate(value)) {
      return rule.message;
    }
  }
  return null;
}

/**
 * Validates login credentials and returns validation errors
 */
export function validateCredentials(
  credentials: LoginCredentials,
  config: ValidationConfig = DEFAULT_VALIDATION_CONFIG
): ValidationErrors {
  const errors: ValidationErrors = {};

  // Validate email
  const emailError = validateField('email', credentials.email, config.email);
  if (emailError) {
    errors.email = emailError;
  }

  // Validate password
  const passwordError = validateField('password', credentials.password, config.password);
  if (passwordError) {
    errors.password = passwordError;
  }

  // Validate TOTP code if provided
  if (credentials.totp_code && config.totp_code) {
    const totpError = validateField('totp_code', credentials.totp_code, config.totp_code);
    if (totpError) {
      errors.totp_code = totpError;
    }
  }

  return errors;
}

/**
 * Checks if validation errors exist
 */
export function hasValidationErrors(errors: ValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

/**
 * Clears specific validation errors
 */
export function clearValidationError(
  errors: ValidationErrors,
  field: keyof ValidationErrors
): ValidationErrors {
  const newErrors = { ...errors };
  delete newErrors[field];
  return newErrors;
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  backoffStrategy: 'exponential',
  baseDelay: 1000, // 1 second
  maxDelay: 30000  // 30 seconds
};

/**
 * Calculates retry delay based on attempt count and configuration
 */
export function calculateRetryDelay(
  attemptCount: number,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): number {
  if (config.backoffStrategy === 'linear') {
    return Math.min(config.baseDelay * attemptCount, config.maxDelay);
  } else {
    // Exponential backoff
    return Math.min(config.baseDelay * Math.pow(2, attemptCount - 1), config.maxDelay);
  }
}

/**
 * Determines if a retry should be attempted
 */
export function shouldRetry(
  error: AuthenticationError,
  attemptCount: number,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): boolean {
  if (attemptCount >= config.maxAttempts) {
    return false;
  }

  return isRetryableError(error);
}

/**
 * Checks if enough time has passed since last attempt for retry
 */
export function canRetryAfter(
  lastAttemptTime: Date,
  retryDelay: number
): boolean {
  const now = new Date();
  const timeSinceLastAttempt = now.getTime() - lastAttemptTime.getTime();
  return timeSinceLastAttempt >= retryDelay;
}

/**
 * Parses backend error response into AuthenticationError
 */
export function parseBackendError(error: any): AuthenticationError {
  // Handle network errors
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return createAuthError('network_error', 'Network connection failed');
  }

  // Handle timeout errors
  if (error.name === 'AbortError' || error.message?.includes('timeout')) {
    return createAuthError('timeout_error', 'Request timed out');
  }

  // Handle HTTP errors with response
  if (error.message) {
    const message = error.message.toLowerCase();
    
    if (message.includes('invalid') && (message.includes('credential') || message.includes('password'))) {
      return createAuthError('invalid_credentials');
    }
    
    if (message.includes('rate limit') || message.includes('too many')) {
      // Try to extract retry time from message
      const retryMatch = message.match(/(\d+)\s*(minute|second)/);
      const retryAfter = retryMatch ? parseInt(retryMatch[1]) * (retryMatch[2] === 'minute' ? 60000 : 1000) : undefined;
      return createAuthError('rate_limit', error.message, null, retryAfter);
    }
    
    if (message.includes('2fa') || message.includes('two.factor')) {
      if (message.includes('required')) {
        return createAuthError('two_factor_required');
      } else if (message.includes('invalid')) {
        return createAuthError('two_factor_invalid');
      }
    }
    
    if (message.includes('verify') && message.includes('email')) {
      return createAuthError('verification_required');
    }
    
    if (message.includes('locked')) {
      return createAuthError('account_locked');
    }
    
    if (message.includes('suspended')) {
      return createAuthError('account_suspended');
    }
    
    if (message.includes('security') || message.includes('blocked')) {
      return createAuthError('security_block');
    }
    
    if (message.includes('server') || message.includes('internal')) {
      return createAuthError('server_error');
    }
  }

  // Default to unknown error
  return createAuthError('unknown_error', error.message || 'An unexpected error occurred');
}

/**
 * Formats retry time for user display
 */
export function formatRetryTime(retryAfter: number): string {
  const seconds = Math.ceil(retryAfter / 1000);
  
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''}`;
  }
  
  const minutes = Math.ceil(seconds / 60);
  return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
}

/**
 * Checks if credentials are empty
 */
export function areCredentialsEmpty(credentials: LoginCredentials): boolean {
  return !credentials.email.trim() || !credentials.password.trim();
}

/**
 * Sanitizes credentials for logging (removes sensitive data)
 */
export function sanitizeCredentialsForLogging(credentials: LoginCredentials): Partial<LoginCredentials> {
  return {
    email: credentials.email,
    // Never log passwords or TOTP codes
    password: '[REDACTED]',
    totp_code: credentials.totp_code ? '[REDACTED]' : undefined
  };
}

/**
 * Creates a debounced validation function
 */
export function createDebouncedValidator(
  validationFn: (value: string) => string | null,
  delay: number = 300
): (value: string, callback: (error: string | null) => void) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (value: string, callback: (error: string | null) => void) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      const error = validationFn(value);
      callback(error);
    }, delay);
  };
}

/**
 * Type guard to check if an error is an AuthenticationError
 */
export function isAuthenticationError(error: any): error is AuthenticationError {
  return error && typeof error === 'object' && 'type' in error && 'message' in error;
}