import { ErrorCategory, ErrorSeverity } from './ErrorHandlingService';

/**
 * User-friendly error message configuration
 */
export interface ErrorMessageConfig {
  /** Technical error code or pattern */
  code: string;
  
  /** User-friendly error message */
  message: string;
  
  /** Suggested actions for the user */
  suggestedActions?: string[];
  
  /** Whether to show technical details to user */
  showTechnicalDetails?: boolean;
  
  /** Error category override */
  category?: ErrorCategory;
  
  /** Error severity override */
  severity?: ErrorSeverity;
}

/**
 * Service for managing user-friendly error messages
 */
class UserErrorMessageService {
  private static instance: UserErrorMessageService;
  private errorMessages: Map<string, ErrorMessageConfig> = new Map();
  private errorPatterns: Array<{ pattern: RegExp; config: ErrorMessageConfig }> = [];

  private constructor() {
    this.initializeDefaultMessages();
  }

  public static getInstance(): UserErrorMessageService {
    if (!UserErrorMessageService.instance) {
      UserErrorMessageService.instance = new UserErrorMessageService();
    }
    return UserErrorMessageService.instance;
  }

  /**
   * Initialize default error messages
   */
  private initializeDefaultMessages(): void {
    // Network errors
    this.addErrorMessage({
      code: 'network_error',
      message: 'Network connection error. Please check your internet connection and try again.',
      suggestedActions: [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact your network administrator if the problem persists'
      ],
      category: ErrorCategory.NETWORK,
      severity: ErrorSeverity.MEDIUM
    });

    this.addErrorMessage({
      code: 'timeout_error',
      message: 'Request timed out. The server took too long to respond.',
      suggestedActions: [
        'Try again later',
        'Check your internet connection',
        'Contact support if the problem persists'
      ],
      category: ErrorCategory.TIMEOUT,
      severity: ErrorSeverity.MEDIUM
    });

    // API errors
    this.addErrorMessage({
      code: 'api_error',
      message: 'An error occurred while communicating with the server.',
      suggestedActions: [
        'Try again later',
        'Refresh the page',
        'Contact support if the problem persists'
      ],
      category: ErrorCategory.API,
      severity: ErrorSeverity.MEDIUM
    });

    this.addErrorMessage({
      code: 'api_rate_limit',
      message: 'Too many requests. Please wait before trying again.',
      suggestedActions: [
        'Wait a few minutes before trying again',
        'Reduce the frequency of your requests',
        'Contact support if you need higher limits'
      ],
      category: ErrorCategory.API,
      severity: ErrorSeverity.LOW
    });

    // Authentication errors
    this.addErrorMessage({
      code: 'auth_error',
      message: 'Authentication error. Please log in again.',
      suggestedActions: [
        'Log out and log back in',
        'Check your credentials',
        'Contact support if the problem persists'
      ],
      category: ErrorCategory.AUTH,
      severity: ErrorSeverity.HIGH
    });

    this.addErrorMessage({
      code: 'permission_denied',
      message: 'You do not have permission to perform this action.',
      suggestedActions: [
        'Contact your administrator for access',
        'Make sure you are logged in with the correct account',
        'Request the necessary permissions'
      ],
      category: ErrorCategory.AUTH,
      severity: ErrorSeverity.HIGH
    });

    // Validation errors
    this.addErrorMessage({
      code: 'validation_error',
      message: 'Invalid input. Please check your data and try again.',
      suggestedActions: [
        'Check the form for errors',
        'Make sure all required fields are filled',
        'Ensure your data is in the correct format'
      ],
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.LOW
    });

    this.addErrorMessage({
      code: 'required_field_missing',
      message: 'Required information is missing. Please fill in all required fields.',
      suggestedActions: [
        'Look for fields marked as required',
        'Make sure no required fields are left empty',
        'Check for validation messages below the fields'
      ],
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.LOW
    });

    // Execution errors
    this.addErrorMessage({
      code: 'execution_error',
      message: 'An error occurred while processing your request.',
      suggestedActions: [
        'Try again',
        'Refresh the page',
        'Contact support if the problem persists'
      ],
      category: ErrorCategory.EXECUTION,
      severity: ErrorSeverity.HIGH
    });

    // Configuration errors
    this.addErrorMessage({
      code: 'configuration_error',
      message: 'System configuration error. Please contact support.',
      suggestedActions: [
        'Contact support with details about what you were trying to do',
        'Try again later',
        'Check system status page for known issues'
      ],
      category: ErrorCategory.CONFIGURATION,
      severity: ErrorSeverity.HIGH
    });

    // Extension errors
    this.addErrorMessage({
      code: 'extension_error',
      message: 'An error occurred in an extension.',
      suggestedActions: [
        'Try disabling extensions one by one to identify the problematic one',
        'Update your extensions',
        'Contact extension developer for support'
      ],
      category: ErrorCategory.EXTENSION,
      severity: ErrorSeverity.MEDIUM
    });

    this.addErrorMessage({
      code: 'extension_not_found',
      message: 'The requested extension could not be found.',
      suggestedActions: [
        'Check if the extension is installed',
        'Try installing the extension',
        'Contact support for assistance'
      ],
      category: ErrorCategory.EXTENSION,
      severity: ErrorSeverity.LOW
    });

    // UI errors
    this.addErrorMessage({
      code: 'ui_error',
      message: 'An error occurred in the user interface.',
      suggestedActions: [
        'Refresh the page',
        'Clear your browser cache',
        'Try a different browser'
      ],
      category: ErrorCategory.UI,
      severity: ErrorSeverity.MEDIUM
    });

    // Generic errors
    this.addErrorMessage({
      code: 'unknown_error',
      message: 'An unexpected error occurred.',
      suggestedActions: [
        'Try again',
        'Refresh the page',
        'Contact support if the problem persists'
      ],
      category: ErrorCategory.UNKNOWN,
      severity: ErrorSeverity.HIGH
    });

    // Add error patterns
    this.addErrorPattern({
      pattern: /network.*error/i,
      config: {
        code: 'network_error',
        message: 'Network connection error. Please check your internet connection and try again.',
        suggestedActions: [
          'Check your internet connection',
          'Try refreshing the page',
          'Contact your network administrator if the problem persists'
        ],
        category: ErrorCategory.NETWORK,
        severity: ErrorSeverity.MEDIUM
      }
    });

    this.addErrorPattern({
      pattern: /timeout/i,
      config: {
        code: 'timeout_error',
        message: 'Request timed out. The server took too long to respond.',
        suggestedActions: [
          'Try again later',
          'Check your internet connection',
          'Contact support if the problem persists'
        ],
        category: ErrorCategory.TIMEOUT,
        severity: ErrorSeverity.MEDIUM
      }
    });

    this.addErrorPattern({
      pattern: /permission.*denied/i,
      config: {
        code: 'permission_denied',
        message: 'You do not have permission to perform this action.',
        suggestedActions: [
          'Contact your administrator for access',
          'Make sure you are logged in with the correct account',
          'Request the necessary permissions'
        ],
        category: ErrorCategory.AUTH,
        severity: ErrorSeverity.HIGH
      }
    });

    this.addErrorPattern({
      pattern: /not.*found/i,
      config: {
        code: 'not_found',
        message: 'The requested resource could not be found.',
        suggestedActions: [
          'Check the URL or resource identifier',
          'Make sure you have access to this resource',
          'Contact support for assistance'
        ],
        category: ErrorCategory.UNKNOWN,
        severity: ErrorSeverity.MEDIUM
      }
    });
  }

  /**
   * Add an error message configuration
   */
  public addErrorMessage(config: ErrorMessageConfig): void {
    this.errorMessages.set(config.code, config);
  }

  /**
   * Add an error pattern configuration
   */
  public addErrorPattern(patternConfig: { pattern: RegExp; config: ErrorMessageConfig }): void {
    this.errorPatterns.push(patternConfig);
  }

  /**
   * Get user-friendly error message
   */
  public getUserFriendlyError(
    error: Error | { code?: string; message?: string } | string,
    context?: {
      component?: string;
      action?: string;
      [key: string]: unknown;
    }
  ): {
    message: string;
    suggestedActions: string[];
    showTechnicalDetails: boolean;
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    technicalMessage?: string;
  } {
    // Extract error code and message
    let errorCode = 'unknown_error';
    let technicalMessage = '';

    if (typeof error === 'string') {
      technicalMessage = error;
    } else if (error instanceof Error) {
      const maybeCode = error as Error & { code?: string };
      errorCode = maybeCode.code || error.name || 'unknown_error';
      technicalMessage = error.message;
    } else if (error && typeof error === 'object') {
      errorCode = error.code || 'unknown_error';
      technicalMessage = error.message || '';
    }

    // Try to find a direct match for the error code
    let config = this.errorMessages.get(errorCode);

    // If no direct match, try to match with patterns
    if (!config) {
      for (const { pattern, config: patternConfig } of this.errorPatterns) {
        if (pattern.test(technicalMessage)) {
          config = patternConfig;
          break;
        }
      }
    }

    // If still no match, use the default unknown error
    if (!config) {
      config = this.errorMessages.get('unknown_error')!;
    }

    // Customize message based on context
    let message = config.message;
    if (context) {
      message = this.customizeMessage(message, context);
    }

    return {
      message,
      suggestedActions: config.suggestedActions || [],
      showTechnicalDetails: config.showTechnicalDetails || false,
      category: config.category,
      severity: config.severity,
      technicalMessage
    };
  }

  /**
   * Get error message by code
   */
  public getErrorMessageByCode(code: string): ErrorMessageConfig | undefined {
    return this.errorMessages.get(code);
  }

  /**
   * Get all error message configurations
   */
  public getAllErrorMessages(): ErrorMessageConfig[] {
    return Array.from(this.errorMessages.values());
  }

  /**
   * Update an error message configuration
   */
  public updateErrorMessage(code: string, updates: Partial<ErrorMessageConfig>): boolean {
    const config = this.errorMessages.get(code);
    if (!config) {
      return false;
    }

    const updatedConfig = { ...config, ...updates };
    this.errorMessages.set(code, updatedConfig);
    return true;
  }

  /**
   * Remove an error message configuration
   */
  public removeErrorMessage(code: string): boolean {
    return this.errorMessages.delete(code);
  }

  /**
   * Clear all error message configurations
   */
  public clearAllErrorMessages(): void {
    this.errorMessages.clear();
    this.errorPatterns = [];
  }

  /**
   * Customize error message based on context
   */
  private customizeMessage(message: string, context: { [key: string]: unknown }): string {
    let customizedMessage = message;

    // Replace component name if available
    if (context.component) {
      customizedMessage = customizedMessage.replace(
        'the user interface',
        `the ${context.component} component`
      );
    }

    // Replace action name if available
    if (context.action) {
      customizedMessage = customizedMessage.replace(
        'perform this action',
        `${context.action}`
      );
    }

    return customizedMessage;
  }
}

export default UserErrorMessageService;
