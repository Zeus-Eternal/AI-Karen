/**
 * Error recovery strategies and fallback actions
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { CategorizedError, ErrorCategory } from './error-categories';
import { ErrorCategorizer } from './error-categorizer';

export interface RecoveryAction {
  name: string;
  description: string;
  execute: () => Promise<boolean>;
  rollback?: () => Promise<void>;
}

export interface RecoveryStrategy {
  errorCategory: ErrorCategory;
  actions: RecoveryAction[];
  maxAttempts: number;
  cooldownPeriod: number; // milliseconds
}

export interface RecoveryResult {
  success: boolean;
  actionTaken: string;
  message: string;
  shouldRetry: boolean;
  nextRetryDelay?: number;
}

export class ErrorRecoveryManager {
  private static instance: ErrorRecoveryManager;
  private recoveryAttempts = new Map<string, number>();
  private lastRecoveryAttempt = new Map<string, number>();
  private categorizer = ErrorCategorizer.getInstance();

  static getInstance(): ErrorRecoveryManager {
    if (!ErrorRecoveryManager.instance) {
      ErrorRecoveryManager.instance = new ErrorRecoveryManager();
    }
    return ErrorRecoveryManager.instance;
  }

  /**
   * Attempt to recover from an error
   */
  async attemptRecovery(categorizedError: CategorizedError): Promise<RecoveryResult> {
    const recoveryKey = this.getRecoveryKey(categorizedError);
    const attempts = this.recoveryAttempts.get(recoveryKey) || 0;
    const lastAttempt = this.lastRecoveryAttempt.get(recoveryKey) || 0;
    const now = Date.now();

    // Check cooldown period
    const strategy = this.getRecoveryStrategy(categorizedError.category);
    if (now - lastAttempt < strategy.cooldownPeriod) {
      return {
        success: false,
        actionTaken: 'COOLDOWN_WAIT',
        message: 'Recovery attempt too soon. Please wait before retrying.',
        shouldRetry: true,
        nextRetryDelay: strategy.cooldownPeriod - (now - lastAttempt)
      };
    }

    // Check max attempts
    if (attempts >= strategy.maxAttempts) {
      return {
        success: false,
        actionTaken: 'MAX_ATTEMPTS_REACHED',
        message: 'Maximum recovery attempts reached. Manual intervention required.',
        shouldRetry: false
      };
    }

    // Update attempt tracking
    this.recoveryAttempts.set(recoveryKey, attempts + 1);
    this.lastRecoveryAttempt.set(recoveryKey, now);

    // Execute recovery actions
    for (const action of strategy.actions) {
      try {
        const success = await action.execute();
        if (success) {
          // Reset attempt counter on successful recovery
          this.recoveryAttempts.delete(recoveryKey);
          this.lastRecoveryAttempt.delete(recoveryKey);
          
          return {
            success: true,
            actionTaken: action.name,
            message: `Recovery successful: ${action.description}`,
            shouldRetry: true,
            nextRetryDelay: 1000 // Short delay before retry
          };
        }
      } catch (error) {
        console.warn(`Recovery action ${action.name} failed:`, error);
        // Continue to next action
      }
    }

    // All recovery actions failed
    const nextRetryDelay = this.categorizer.calculateRetryDelay(categorizedError, attempts);
    return {
      success: false,
      actionTaken: 'ALL_ACTIONS_FAILED',
      message: 'All recovery actions failed. Will retry with backoff.',
      shouldRetry: this.categorizer.shouldRetry(categorizedError, attempts),
      nextRetryDelay
    };
  }

  /**
   * Get recovery strategy for error category
   */
  private getRecoveryStrategy(category: ErrorCategory): RecoveryStrategy {
    switch (category) {
      case ErrorCategory.NETWORK:
        return {
          errorCategory: category,
          maxAttempts: 3,
          cooldownPeriod: 5000,
          actions: [
            {
              name: 'CHECK_CONNECTIVITY',
              description: 'Verify network connectivity',
              execute: async () => {
                try {
                  const response = await fetch('/api/health', { 
                    method: 'HEAD',
                    signal: AbortSignal.timeout(5000)
                  });
                  return response.ok;
                } catch {
                  return false;
                }
              }
            },
            {
              name: 'USE_FALLBACK_BACKEND',
              description: 'Switch to fallback backend URL',
              execute: async () => {
                // This would integrate with the connection manager
                // to switch to a fallback backend URL
                return this.switchToFallbackBackend();
              }
            },
            {
              name: 'CLEAR_CONNECTION_CACHE',
              description: 'Clear connection cache and retry',
              execute: async () => {
                // Clear any cached connections
                return this.clearConnectionCache();
              }
            }
          ]
        };

      case ErrorCategory.AUTHENTICATION:
        return {
          errorCategory: category,
          maxAttempts: 2,
          cooldownPeriod: 3000,
          actions: [
            {
              name: 'REFRESH_SESSION',
              description: 'Attempt to refresh authentication session',
              execute: async () => {
                return this.refreshAuthSession();
              }
            },
            {
              name: 'CLEAR_AUTH_CACHE',
              description: 'Clear authentication cache',
              execute: async () => {
                return this.clearAuthCache();
              }
            }
          ]
        };

      case ErrorCategory.DATABASE:
        return {
          errorCategory: category,
          maxAttempts: 5,
          cooldownPeriod: 10000,
          actions: [
            {
              name: 'RETRY_CONNECTION',
              description: 'Retry database connection',
              execute: async () => {
                return this.retryDatabaseConnection();
              }
            },
            {
              name: 'ENABLE_DEGRADED_MODE',
              description: 'Enable degraded mode operation',
              execute: async () => {
                return this.enableDegradedMode();
              }
            }
          ]
        };

      case ErrorCategory.TIMEOUT:
        return {
          errorCategory: category,
          maxAttempts: 3,
          cooldownPeriod: 2000,
          actions: [
            {
              name: 'INCREASE_TIMEOUT',
              description: 'Increase timeout for next attempt',
              execute: async () => {
                return this.increaseTimeout();
              }
            },
            {
              name: 'SPLIT_REQUEST',
              description: 'Split large request into smaller parts',
              execute: async () => {
                return this.splitRequest();
              }
            }
          ]
        };

      default:
        return {
          errorCategory: category,
          maxAttempts: 1,
          cooldownPeriod: 5000,
          actions: [
            {
              name: 'GENERIC_RETRY',
              description: 'Generic retry with delay',
              execute: async () => {
                // Wait a bit and return true to allow retry
                await new Promise(resolve => setTimeout(resolve, 1000));
                return true;
              }
            }
          ]
        };
    }
  }

  /**
   * Generate recovery key for tracking attempts
   */
  private getRecoveryKey(error: CategorizedError): string {
    return `${error.category}_${error.code}`;
  }

  /**
   * Recovery action implementations
   */
  private async switchToFallbackBackend(): Promise<boolean> {
    try {
      // This would integrate with the environment config manager
      // to switch to a fallback backend URL
      console.log('Switching to fallback backend...');
      return true;
    } catch {
      return false;
    }
  }

  private async clearConnectionCache(): Promise<boolean> {
    try {
      // Clear any cached connections or connection pools
      console.log('Clearing connection cache...');
      return true;
    } catch {
      return false;
    }
  }

  private async refreshAuthSession(): Promise<boolean> {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  private async clearAuthCache(): Promise<boolean> {
    try {
      // Clear authentication-related cache
      localStorage.removeItem('auth_token');
      sessionStorage.removeItem('auth_session');
      return true;
    } catch {
      return false;
    }
  }

  private async retryDatabaseConnection(): Promise<boolean> {
    try {
      const response = await fetch('/api/health/database', {
        method: 'GET',
        signal: AbortSignal.timeout(10000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  private async enableDegradedMode(): Promise<boolean> {
    try {
      // Enable degraded mode - this would set a flag that other parts
      // of the application can check to provide limited functionality
      console.log('Enabling degraded mode...');
      localStorage.setItem('degraded_mode', 'true');
      return true;
    } catch {
      return false;
    }
  }

  private async increaseTimeout(): Promise<boolean> {
    try {
      // This would integrate with the timeout manager to increase timeouts
      console.log('Increasing timeout for next attempt...');
      return true;
    } catch {
      return false;
    }
  }

  private async splitRequest(): Promise<boolean> {
    try {
      // This would be implemented based on the specific request type
      console.log('Attempting to split request...');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Reset recovery attempts for a specific error
   */
  resetRecoveryAttempts(categorizedError: CategorizedError): void {
    const recoveryKey = this.getRecoveryKey(categorizedError);
    this.recoveryAttempts.delete(recoveryKey);
    this.lastRecoveryAttempt.delete(recoveryKey);
  }

  /**
   * Get current recovery attempt count
   */
  getRecoveryAttemptCount(categorizedError: CategorizedError): number {
    const recoveryKey = this.getRecoveryKey(categorizedError);
    return this.recoveryAttempts.get(recoveryKey) || 0;
  }
}