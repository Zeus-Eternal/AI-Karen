/**
 * Error handling system exports
 * Centralized exports to avoid circular dependencies
 */

export {
  ErrorCategory,
  ErrorSeverity,
  ERROR_PATTERNS,
  USER_ERROR_MESSAGES
} from './error-categories';

export type { CategorizedError } from './error-categories';
export { ErrorCategorizer } from './error-categorizer';
export type { RecoveryAction, RecoveryStrategy, RecoveryResult } from './error-recovery';
export { ErrorRecoveryManager } from './error-recovery';
export type { ErrorHandlingOptions, ErrorHandlingResult } from './comprehensive-error-handler';
export { ComprehensiveErrorHandler } from './comprehensive-error-handler';
export { handleError, withErrorHandling, withRetry } from './error-utils';
