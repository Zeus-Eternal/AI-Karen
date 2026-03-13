/**
 * RBAC Custom Error Classes
 * 
 * This file defines custom error classes for the Role-Based Access Control (RBAC) system.
 * These errors provide more specific information about RBAC-related issues and help with debugging.
 */

import { RBACErrorType } from '../types';

/**
 * Base RBAC error class that all RBAC errors extend from
 */
export class RBACError extends Error {
  public readonly type: RBACErrorType;
  public readonly timestamp: Date;
  public readonly details?: Record<string, unknown>;

  constructor(
    type: RBACErrorType,
    message: string,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = this.constructor.name;
    this.type = type;
    this.timestamp = new Date();
    this.details = details;

    // Maintain proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, new.target.prototype);
    
    // Capture stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert the error to a JSON-serializable object
   */
  toJSON() {
    return {
      name: this.name,
      type: this.type,
      message: this.message,
      timestamp: this.timestamp.toISOString(),
      stack: this.stack,
      details: this.details
    };
  }

  /**
   * Create a user-friendly error message
   */
  toUserMessage(): string {
    switch (this.type) {
      case RBACErrorType.ROLE_NOT_FOUND:
        return `The specified role was not found.`;
      case RBACErrorType.PERMISSION_NOT_FOUND:
        return `The specified permission was not found.`;
      case RBACErrorType.CIRCULAR_INHERITANCE:
        return `A circular inheritance was detected in the role hierarchy.`;
      case RBACErrorType.INVALID_ROLE_DEFINITION:
        return `The role definition is invalid.`;
      case RBACErrorType.INVALID_PERMISSION:
        return `The specified permission is invalid.`;
      case RBACErrorType.USER_NOT_FOUND:
        return `The specified user was not found.`;
      case RBACErrorType.CACHE_ERROR:
        return `An error occurred with the permission cache.`;
      case RBACErrorType.INITIALIZATION_ERROR:
        return `The RBAC system failed to initialize.`;
      case RBACErrorType.VALIDATION_ERROR:
        return `A validation error occurred.`;
      default:
        return `An unknown RBAC error occurred.`;
    }
  }
}

/**
 * Error thrown when a role is not found in the system
 */
export class RoleNotFoundError extends RBACError {
  constructor(roleName: string, details?: Record<string, unknown>) {
    super(
      RBACErrorType.ROLE_NOT_FOUND,
      `Role '${roleName}' not found`,
      { ...details, roleName }
    );
  }
}

/**
 * Error thrown when a permission is not found in the system
 */
export class PermissionNotFoundError extends RBACError {
  constructor(permissionName: string, details?: Record<string, unknown>) {
    super(
      RBACErrorType.PERMISSION_NOT_FOUND,
      `Permission '${permissionName}' not found`,
      { ...details, permissionName }
    );
  }
}

/**
 * Error thrown when a circular inheritance is detected in the role hierarchy
 */
export class CircularInheritanceError extends RBACError {
  constructor(
    roleName: string,
    inheritanceChain: string[],
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.CIRCULAR_INHERITANCE,
      `Circular inheritance detected for role '${roleName}': ${inheritanceChain.join(' -> ')} -> ${roleName}`,
      { ...details, roleName, inheritanceChain }
    );
  }
}

/**
 * Error thrown when a role definition is invalid
 */
export class InvalidRoleDefinitionError extends RBACError {
  constructor(
    roleName: string,
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.INVALID_ROLE_DEFINITION,
      `Invalid role definition for '${roleName}': ${reason}`,
      { ...details, roleName, reason }
    );
  }
}

/**
 * Error thrown when a permission is invalid
 */
export class InvalidPermissionError extends RBACError {
  constructor(
    permissionName: string,
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.INVALID_PERMISSION,
      `Invalid permission '${permissionName}': ${reason}`,
      { ...details, permissionName, reason }
    );
  }
}

/**
 * Error thrown when a user is not found in the system
 */
export class UserNotFoundError extends RBACError {
  constructor(userId: string, details?: Record<string, unknown>) {
    super(
      RBACErrorType.USER_NOT_FOUND,
      `User with ID '${userId}' not found`,
      { ...details, userId }
    );
  }
}

/**
 * Error thrown when a cache operation fails
 */
export class CacheError extends RBACError {
  constructor(
    operation: string,
    originalError?: Error,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.CACHE_ERROR,
      `Cache error during ${operation}: ${originalError?.message || 'Unknown error'}`,
      { ...details, operation, originalError: originalError?.message }
    );
  }
}

/**
 * Error thrown when the RBAC system fails to initialize
 */
export class InitializationError extends RBACError {
  constructor(
    reason: string,
    originalError?: Error,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.INITIALIZATION_ERROR,
      `RBAC initialization error: ${reason}`,
      { ...details, reason, originalError: originalError?.message }
    );
  }
}

/**
 * Error thrown when a validation fails
 */
export class ValidationError extends RBACError {
  constructor(
    field: string,
    value: unknown,
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.VALIDATION_ERROR,
      `Validation error for field '${field}' with value '${value}': ${reason}`,
      { ...details, field, value, reason }
    );
  }
}

/**
 * Error thrown when a dynamic permission operation fails
 */
export class DynamicPermissionError extends RBACError {
  constructor(
    operation: 'add' | 'remove',
    permissionName: string,
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.VALIDATION_ERROR,
      `Failed to ${operation} dynamic permission '${permissionName}': ${reason}`,
      { ...details, operation, permissionName, reason }
    );
  }
}

/**
 * Error thrown when a dynamic role operation fails
 */
export class DynamicRoleError extends RBACError {
  constructor(
    operation: 'add' | 'remove',
    roleName: string,
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.VALIDATION_ERROR,
      `Failed to ${operation} dynamic role '${roleName}': ${reason}`,
      { ...details, operation, roleName, reason }
    );
  }
}

/**
 * Error thrown when a role assignment operation fails
 */
export class RoleAssignmentError extends RBACError {
  constructor(
    userId: string,
    roleName: string,
    operation: 'assign' | 'remove',
    reason: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.VALIDATION_ERROR,
      `Failed to ${operation} role '${roleName}' to user '${userId}': ${reason}`,
      { ...details, userId, roleName, operation, reason }
    );
  }
}

/**
 * Error thrown when an API call to the backend fails
 */
export class RBACApiError extends RBACError {
  constructor(
    endpoint: string,
    statusCode: number,
    message: string,
    details?: Record<string, unknown>
  ) {
    super(
      RBACErrorType.VALIDATION_ERROR,
      `RBAC API error for endpoint '${endpoint}' (${statusCode}): ${message}`,
      { ...details, endpoint, statusCode }
    );
  }
}

/**
 * Helper function to check if an error is an RBAC error
 */
export function isRBACError(error: unknown): error is RBACError {
  return error instanceof RBACError;
}

/**
 * Helper function to check if an error is a specific type of RBAC error
 */
export function isRBACErrorOfType<T extends RBACError>(
  error: unknown,
  errorType: RBACErrorType
): error is T {
  return isRBACError(error) && error.type === errorType;
}

/**
 * Helper function to create an error handler for RBAC errors
 */
export function createRBACErrorHandler<T>(
  fallbackValue: T,
  logger?: (error: RBACError) => void
) {
  return (error: unknown): T => {
    if (isRBACError(error)) {
      logger?.(error);
      return fallbackValue;
    }
    throw error; // Re-throw non-RBAC errors
  };
}