import type {
/**
 * Enhanced Authentication Types and Interfaces
 *
 * This module exports all enhanced authentication types, interfaces, and utilities
 * for the comprehensive login feedback system.
 */

// Re-export all base authentication types
export * from './auth';

// Re-export authentication utilities
export * from './auth-utils';

// Re-export feedback types (excluding conflicting FeedbackState)
export type {
  SuccessMessageProps,
  ErrorMessageProps,
  LoadingIndicatorProps,
  FeedbackContainerProps,
  ToastNotificationProps,
  ProgressIndicatorProps,
  CountdownTimerProps,
  AlertBannerProps,
  StatusIndicatorProps,
  FeedbackAnimationConfig,
  FeedbackAction
} from './auth-feedback';

export {
  DEFAULT_FEEDBACK_ANIMATIONS,
  FeedbackMessageFactory,
  feedbackReducer,
  initialFeedbackState
} from './auth-feedback';

// Re-export form management types
export * from './auth-form';

// Import types for use in this file

  AuthenticationError,
  AuthenticationState,
  LoginCredentials,
  AuthServiceResponse,
  LoginResponse,
  ValidationErrors,
  ErrorClassification,
  SecurityFlags,
  FeedbackMessage,
  User
} from './auth';


  FormFieldType,
  AuthFormState
} from './auth-form';

// Additional type definitions for enhanced authentication system

/**
 * Authentication system configuration
 */
export interface AuthSystemConfig {
  enableRealTimeValidation: boolean;
  enableRetryLogic: boolean;
  enableFeedbackMessages: boolean;
  enableSecurityFeatures: boolean;
  enableAccessibility: boolean;
  enableLogging: boolean;
  maxRetryAttempts: number;
  retryBaseDelay: number;
  feedbackAutoHideDuration: number;
  validationDebounceDelay: number;
}

/**
 * Default authentication system configuration
 */
export const DEFAULT_AUTH_SYSTEM_CONFIG: AuthSystemConfig = {
  enableRealTimeValidation: true,
  enableRetryLogic: true,
  enableFeedbackMessages: true,
  enableSecurityFeatures: true,
  enableAccessibility: true,
  enableLogging: true,
  maxRetryAttempts: 3,
  retryBaseDelay: 1000,
  feedbackAutoHideDuration: 5000,
  validationDebounceDelay: 300
};

/**
 * Authentication event types for logging and analytics
 */
export type AuthEventType =
  | 'login_attempt'
  | 'login_success'
  | 'login_failed'
  | 'validation_error'
  | 'network_error'
  | 'security_block'
  | 'rate_limit_hit'
  | 'two_factor_required'
  | 'two_factor_success'
  | 'two_factor_failure'
  | 'form_submitted'
  | 'form_reset'
  | 'feedback_shown'
  | 'feedback_dismissed'
  | 'retry_attempted';

/**
 * Authentication event data for logging
 */
export interface AuthEvent {
  type: AuthEventType;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
  error?: AuthenticationError;
}

/**
 * Authentication metrics for monitoring
 */
export interface AuthMetrics {
  totalAttempts: number;
  successfulAttempts: number;
  failedAttempts: number;
  validationErrors: number;
  networkErrors: number;
  securityBlocks: number;
  rateLimitHits: number;
  twoFactorRequests: number;
  averageResponseTime: number;
  errorRate: number;
}

/**
 * Authentication session data
 */
export interface AuthSession {
  sessionId: string;
  startTime: Date;
  lastActivity: Date;
  attemptCount: number;
  events: AuthEvent[];
  currentState: AuthenticationState;
  userAgent?: string;
  ipAddress?: string;
}

/**
 * Enhanced authentication service interface
 */
export interface EnhancedAuthService {
  // Core authentication methods
  login(credentials: LoginCredentials): Promise<AuthServiceResponse<LoginResponse>>;
  logout(): Promise<void>;
  refreshToken(): Promise<AuthServiceResponse<LoginResponse>>;

  // Validation methods
  validateCredentials(credentials: LoginCredentials): Promise<ValidationErrors>;
  validateEmail(email: string): Promise<string | null>;
  validatePassword(password: string): Promise<string | null>;

  // Error handling methods
  parseError(error: any): AuthenticationError;
  classifyError(error: AuthenticationError): ErrorClassification;
  shouldRetry(error: AuthenticationError, attemptCount: number): boolean;

  // Security methods
  checkSecurityFlags(credentials: LoginCredentials): Promise<SecurityFlags>;
  handleRateLimit(error: AuthenticationError): Promise<number>;

  // Logging and monitoring
  logEvent(event: AuthEvent): void;
  getMetrics(): AuthMetrics;
  getSession(): AuthSession;
}

/**
 * Authentication hook interface for React components
 */
export interface UseAuthenticationHook {
  // State
  authState: AuthenticationState;
  formState: AuthFormState;
  feedbackMessage: FeedbackMessage | null;
  validationErrors: ValidationErrors;
  isSubmitting: boolean;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  validateField: (field: FormFieldType, value: string) => Promise<string | null>;
  clearError: (field?: FormFieldType) => void;
  clearFeedback: () => void;
  setFeedback: (message: FeedbackMessage) => void;
  resetForm: () => void;

  // Utilities
  canSubmit: boolean;
  hasErrors: boolean;
  isValid: boolean;
}

/**
 * Component prop types for enhanced authentication components
 */
export interface EnhancedLoginFormProps {
  onSuccess?: (user: User) => void;
  onError?: (error: AuthenticationError) => void;
  onStateChange?: (state: AuthenticationState) => void;
  config?: Partial<AuthSystemConfig>;
  className?: string;
  autoFocus?: boolean;
  showRememberMe?: boolean;
  showForgotPassword?: boolean;
  showSignUpLink?: boolean;
}

/**
 * Authentication provider props
 */
export interface EnhancedAuthProviderProps {
  children: React.ReactNode;
  config?: Partial<AuthSystemConfig>;
  onAuthEvent?: (event: AuthEvent) => void;
  enableDevMode?: boolean;
}

/**
 * Type guards and utility functions
 */
export const AuthTypeGuards = {
  isUser: (value: any): value is User => {
    return value && typeof value === 'object' && 'user_id' in value && 'email' in value;
  },

  isAuthenticationError: (value: any): value is AuthenticationError => {
    return value && typeof value === 'object' && 'type' in value && 'message' in value;
  },

  isFeedbackMessage: (value: any): value is FeedbackMessage => {
    return value && typeof value === 'object' && 'type' in value && 'title' in value && 'message' in value;
  },

  isValidationErrors: (value: any): value is ValidationErrors => {
    return value && typeof value === 'object';
  }
};

/**
 * Constants for authentication system
 */
export const AUTH_CONSTANTS = {
  // Timeouts
  DEFAULT_REQUEST_TIMEOUT: 30000, // 30 seconds
  DEFAULT_RETRY_DELAY: 1000, // 1 second
  DEFAULT_FEEDBACK_DURATION: 5000, // 5 seconds

  // Limits
  MAX_RETRY_ATTEMPTS: 3,
  MAX_VALIDATION_ERRORS: 10,
  MAX_SESSION_DURATION: 24 * 60 * 60 * 1000, // 24 hours

  // Validation
  MIN_PASSWORD_LENGTH: 8,
  MAX_PASSWORD_LENGTH: 128,
  MAX_EMAIL_LENGTH: 254,
  TOTP_CODE_LENGTH: 6,

  // UI
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 300,
  LOADING_SPINNER_SIZE: 20,

  // Storage keys
  STORAGE_KEYS: {
    REMEMBER_EMAIL: 'auth_remember_email',
    SESSION_ID: 'auth_session_id',
    LAST_LOGIN: 'auth_last_login'
  }
} as const;

/**
 * Error codes for specific authentication scenarios
 */
export const AUTH_ERROR_CODES = {
  INVALID_CREDENTIALS: 'AUTH_001',
  NETWORK_ERROR: 'AUTH_002',
  RATE_LIMIT: 'AUTH_003',
  SECURITY_BLOCK: 'AUTH_004',
  VERIFICATION_REQUIRED: 'AUTH_005',
  ACCOUNT_LOCKED: 'AUTH_006',
  ACCOUNT_SUSPENDED: 'AUTH_007',
  TWO_FACTOR_REQUIRED: 'AUTH_008',
  TWO_FACTOR_INVALID: 'AUTH_009',
  SERVER_ERROR: 'AUTH_010',
  VALIDATION_ERROR: 'AUTH_011',
  TIMEOUT_ERROR: 'AUTH_012',
  UNKNOWN_ERROR: 'AUTH_999'
} as const;

/**
 * Success codes for authentication events
 */
export const AUTH_SUCCESS_CODES = {
  LOGIN_SUCCESS: 'AUTH_SUCCESS_001',
  LOGOUT_SUCCESS: 'AUTH_SUCCESS_002',
  TOKEN_REFRESH: 'AUTH_SUCCESS_003',
  VALIDATION_PASSED: 'AUTH_SUCCESS_004',
  TWO_FACTOR_SUCCESS: 'AUTH_SUCCESS_005'
} as const;
