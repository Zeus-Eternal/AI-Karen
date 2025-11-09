'use client';

import type { ReactNode } from 'react';

/**
 * Enhanced Authentication Types and Interfaces (barrel + config)
 *
 * ✅ Production-grade, tree-shakeable, type-safe re-exports
 * ✅ Centralizes constants, interfaces, and shared config
 * ✅ Avoids circular imports — only re-exports from leaf modules
 * ✅ Safe for Next.js “use client” contexts
 */

// ---------------------------------------------------------------------------
// Base Authentication Domain
// ---------------------------------------------------------------------------
export type {
  User,
  AuthenticationState,
  LoginCredentials,
  LoginResponse,
  AuthenticationError,
  ErrorClassification,
  SecurityFlags,
  AuthServiceResponse,
} from './auth';
export * from './auth-utils'; // runtime helpers

// ---------------------------------------------------------------------------
// Feedback System (UI feedback + reducer + props)
// ---------------------------------------------------------------------------
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
  FeedbackAction,
  FeedbackMessage,
} from './auth-feedback';
export { feedbackReducer, initialFeedbackState } from './auth-feedback';

// ---------------------------------------------------------------------------
// Form Types and Helpers
// ---------------------------------------------------------------------------
export type { AuthFormState, FormFieldType, ValidationErrors } from './auth-form';
export * from './auth-form';

// ---------------------------------------------------------------------------
// System Configuration
// ---------------------------------------------------------------------------
export interface AuthSystemConfig {
  enableRealTimeValidation: boolean;
  enableRetryLogic: boolean;
  enableFeedbackMessages: boolean;
  enableSecurityFeatures: boolean;
  enableAccessibility: boolean;
  enableLogging: boolean;
  maxRetryAttempts: number;
  retryBaseDelay: number; // ms
  feedbackAutoHideDuration: number; // ms
  validationDebounceDelay: number; // ms
}

export const DEFAULT_AUTH_SYSTEM_CONFIG: AuthSystemConfig = {
  enableRealTimeValidation: true,
  enableRetryLogic: true,
  enableFeedbackMessages: true,
  enableSecurityFeatures: true,
  enableAccessibility: true,
  enableLogging: true,
  maxRetryAttempts: 3,
  retryBaseDelay: 1_000,
  feedbackAutoHideDuration: 5_000,
  validationDebounceDelay: 300,
};

// ---------------------------------------------------------------------------
// Eventing + Telemetry Interfaces
// ---------------------------------------------------------------------------
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

import type {
  AuthenticationError,
  AuthenticationState,
  LoginCredentials,
  LoginResponse,
  AuthServiceResponse,
  SecurityFlags,
  ErrorClassification,
  User,
} from './auth';
import type { AuthFormState, ValidationErrors, FormFieldType } from './auth-form';
import type { FeedbackMessage } from './auth-feedback';

export interface AuthEvent {
  type: AuthEventType;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
  error?: AuthenticationError;
}

export interface AuthMetrics {
  totalAttempts: number;
  successfulAttempts: number;
  failedAttempts: number;
  validationErrors: number;
  networkErrors: number;
  securityBlocks: number;
  rateLimitHits: number;
  twoFactorRequests: number;
  averageResponseTime: number; // ms
  errorRate: number; // 0..1
}

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

// ---------------------------------------------------------------------------
// Enhanced Auth Service Contract (adapter interface)
// ---------------------------------------------------------------------------
export interface EnhancedAuthService {
  // Core authentication
  login(credentials: LoginCredentials): Promise<AuthServiceResponse<LoginResponse>>;
  logout(): Promise<void>;
  refreshToken(): Promise<AuthServiceResponse<LoginResponse>>;

  // Validation
  validateCredentials(credentials: LoginCredentials): Promise<ValidationErrors>;
  validateEmail(email: string): Promise<string | null>;
  validatePassword(password: string): Promise<string | null>;

  // Errors
  parseError(error: unknown): AuthenticationError;
  classifyError(error: AuthenticationError): ErrorClassification;
  shouldRetry(error: AuthenticationError, attemptCount: number): boolean;

  // Security
  checkSecurityFlags(credentials: LoginCredentials): Promise<SecurityFlags>;
  handleRateLimit(error: AuthenticationError): Promise<number>; // returns backoff ms

  // Telemetry
  logEvent(event: AuthEvent): void;
  getMetrics(): AuthMetrics;
  getSession(): AuthSession;
}

// ---------------------------------------------------------------------------
// React Hook Interface
// ---------------------------------------------------------------------------
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

  // Derivations
  canSubmit: boolean;
  hasErrors: boolean;
  isValid: boolean;
}

// ---------------------------------------------------------------------------
// Component Prop Types
// ---------------------------------------------------------------------------
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

export interface EnhancedAuthProviderProps {
  children: ReactNode;
  config?: Partial<AuthSystemConfig>;
  onAuthEvent?: (event: AuthEvent) => void;
  enableDevMode?: boolean;
}

// ---------------------------------------------------------------------------
// Type Guards
// ---------------------------------------------------------------------------
export const AuthTypeGuards = {
  isUser(value: unknown): value is User {
    return !!value && typeof value === 'object' && 'user_id' in (value as any) && 'email' in (value as any);
  },
  isAuthenticationError(value: unknown): value is AuthenticationError {
    return !!value && typeof value === 'object' && 'type' in (value as any) && 'message' in (value as any);
  },
  isFeedbackMessage(value: unknown): value is FeedbackMessage {
    return !!value && typeof value === 'object' && 'type' in (value as any) && 'title' in (value as any) && 'message' in (value as any);
  },
  isValidationErrors(value: unknown): value is ValidationErrors {
    return !!value && typeof value === 'object';
  },
};

// ---------------------------------------------------------------------------
// Constants (timeouts, limits, tunables, storage keys)
// ---------------------------------------------------------------------------
export const AUTH_CONSTANTS = {
  // Timeouts (ms)
  DEFAULT_REQUEST_TIMEOUT: 30_000,
  DEFAULT_RETRY_DELAY: 1_000,
  DEFAULT_FEEDBACK_DURATION: 5_000,

  // Limits
  MAX_RETRY_ATTEMPTS: 3,
  MAX_VALIDATION_ERRORS: 10,
  MAX_SESSION_DURATION: 24 * 60 * 60 * 1_000,

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
    LAST_LOGIN: 'auth_last_login',
  },
} as const;

// ---------------------------------------------------------------------------
// Error and Success Codes (normalized)
// ---------------------------------------------------------------------------
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
  UNKNOWN_ERROR: 'AUTH_999',
} as const;

export const AUTH_SUCCESS_CODES = {
  LOGIN_SUCCESS: 'AUTH_SUCCESS_001',
  LOGOUT_SUCCESS: 'AUTH_SUCCESS_002',
  TOKEN_REFRESH: 'AUTH_SUCCESS_003',
  VALIDATION_PASSED: 'AUTH_SUCCESS_004',
  TWO_FACTOR_SUCCESS: 'AUTH_SUCCESS_005',
} as const;
