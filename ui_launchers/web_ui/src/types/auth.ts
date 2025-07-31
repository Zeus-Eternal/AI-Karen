export interface User {
  user_id: string;
  email: string;
  roles: string[];
  tenant_id: string;
  two_factor_enabled: boolean;
  preferences: {
    personalityTone: string;
    personalityVerbosity: string;
    memoryDepth: string;
    customPersonaInstructions: string;
    preferredLLMProvider: string;
    preferredModel: string;
    temperature: number;
    maxTokens: number;
    notifications: {
      email: boolean;
      push: boolean;
    };
    ui: {
      theme: string;
      language: string;
      avatarUrl?: string;
    };
  };
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  token: string;
  user_id: string;
  email: string;
  roles: string[];
  tenant_id: string;
  preferences: any;
  two_factor_enabled: boolean;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: LoginCredentials) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateUserPreferences: (preferences: Partial<User['preferences']>) => Promise<void>;
}

// Enhanced Authentication Types and Interfaces

/**
 * Authentication step types for the authentication flow
 */
export type AuthenticationStep = 
  | 'initial'
  | 'validating'
  | 'authenticating'
  | 'two_factor'
  | 'success'
  | 'error';

/**
 * Authentication error types for comprehensive error classification
 */
export type AuthenticationErrorType = 
  | 'invalid_credentials'
  | 'network_error'
  | 'security_block'
  | 'rate_limit'
  | 'server_error'
  | 'verification_required'
  | 'account_locked'
  | 'account_suspended'
  | 'two_factor_required'
  | 'two_factor_invalid'
  | 'validation_error'
  | 'timeout_error'
  | 'unknown_error';

/**
 * Feedback message types for user interface feedback
 */
export type FeedbackMessageType = 'success' | 'error' | 'warning' | 'info';

/**
 * Error categories for classification system
 */
export type ErrorCategory = 
  | 'authentication'
  | 'validation'
  | 'network'
  | 'security'
  | 'server'
  | 'rate_limit';

/**
 * Error severity levels
 */
export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

/**
 * User action types for error handling guidance
 */
export type UserAction = 
  | 'retry'
  | 'correct_input'
  | 'wait'
  | 'contact_support'
  | 'verify_email'
  | 'enable_2fa'
  | 'reset_password'
  | 'check_connection';

/**
 * Authentication error interface with detailed information
 */
export interface AuthenticationError {
  type: AuthenticationErrorType;
  message: string;
  details?: any;
  retryAfter?: number;
  timestamp?: Date;
  requestId?: string;
}

/**
 * Validation errors for form fields
 */
export interface ValidationErrors {
  email?: string;
  password?: string;
  totp_code?: string;
  general?: string;
}

/**
 * Authentication state with comprehensive status tracking
 */
export interface AuthenticationState {
  status: AuthenticationStep;
  error?: AuthenticationError;
  requiresTwoFactor?: boolean;
  isSubmitting?: boolean;
  lastAttemptTime?: Date;
  attemptCount?: number;
}

/**
 * Feedback message interface for user notifications
 */
export interface FeedbackMessage {
  type: FeedbackMessageType;
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  autoHide?: boolean;
  duration?: number;
}

/**
 * Login form state interface
 */
export interface LoginFormState {
  credentials: LoginCredentials;
  validationErrors: ValidationErrors;
  authenticationState: AuthenticationState;
  feedbackMessage: FeedbackMessage | null;
  showTwoFactor: boolean;
  isSubmitting: boolean;
}

/**
 * Authentication flow context interface
 */
export interface AuthenticationFlow {
  currentStep: AuthenticationStep;
  previousStep?: AuthenticationStep;
  context: AuthenticationContext;
  feedback: FeedbackState;
}

/**
 * Authentication context for flow management
 */
export interface AuthenticationContext {
  credentials: LoginCredentials;
  attemptCount: number;
  lastAttemptTime?: Date;
  requiresTwoFactor: boolean;
  securityFlags: SecurityFlags;
}

/**
 * Security flags for authentication decisions
 */
export interface SecurityFlags {
  isHighRisk: boolean;
  requiresAdditionalVerification: boolean;
  rateLimited: boolean;
  rateLimitResetTime?: Date;
}

/**
 * Feedback state for UI management
 */
export interface FeedbackState {
  message?: FeedbackMessage;
  isVisible: boolean;
  autoHide: boolean;
  duration?: number;
}

/**
 * Error classification interface
 */
export interface ErrorClassification {
  category: ErrorCategory;
  severity: ErrorSeverity;
  userAction: UserAction;
  retryable: boolean;
  supportContact: boolean;
}

/**
 * Error message configuration for user-friendly messages
 */
export interface ErrorMessageConfig {
  title: string;
  message: string;
  action?: {
    label: string;
    type: 'retry' | 'dismiss' | 'support' | 'resend_verification' | 'reset_password';
  };
}

/**
 * Validation rule interface for form validation
 */
export interface ValidationRule {
  validate: (value: string) => boolean;
  message: string;
}

/**
 * Validation configuration for form fields
 */
export interface ValidationConfig {
  email: ValidationRule[];
  password: ValidationRule[];
  totp_code?: ValidationRule[];
}

/**
 * Retry configuration for authentication attempts
 */
export interface RetryConfig {
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential';
  baseDelay: number;
  maxDelay: number;
}

/**
 * Authentication service response interface
 */
export interface AuthServiceResponse<T> {
  success: boolean;
  data?: T;
  error?: AuthenticationError;
}

/**
 * Enhanced authentication context type with feedback support
 */
export interface EnhancedAuthContextType extends AuthContextType {
  authenticationState: AuthenticationState;
  feedbackMessage: FeedbackMessage | null;
  validationErrors: ValidationErrors;
  clearError: () => void;
  clearFeedback: () => void;
  setFeedback: (message: FeedbackMessage) => void;
  validateCredentials: (credentials: LoginCredentials) => ValidationErrors;
}

