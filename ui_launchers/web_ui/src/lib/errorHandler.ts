/**
 * Unified Error Handler - Provides consistent error handling across the web UI
 * Integrates with Python backend error response format
 */

import { safeError, safeWarn, safeInfo } from './safe-console';

export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  PLUGIN_EXECUTION_ERROR = 'PLUGIN_EXECUTION_ERROR',
  MEMORY_ERROR = 'MEMORY_ERROR',
  AI_PROCESSING_ERROR = 'AI_PROCESSING_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
}

export interface ErrorResponse {
  errorCode: ErrorCode;
  message: string;
  details?: Record<string, any>;
  requestId?: string;
  timestamp: string;
  userFriendlyMessage?: string;
}

export interface ErrorContext {
  operation?: string;
  userId?: string;
  sessionId?: string;
  component?: string;
  additionalData?: Record<string, any>;
}

export class UnifiedErrorHandler {
  private static instance: UnifiedErrorHandler | null = null;
  private errorLog: ErrorResponse[] = [];
  private maxLogSize = 100;

  static getInstance(): UnifiedErrorHandler {
    if (!UnifiedErrorHandler.instance) {
      UnifiedErrorHandler.instance = new UnifiedErrorHandler();
    }
    return UnifiedErrorHandler.instance;
  }

  /**
   * Handle and format errors consistently
   */
  handleError(
    error: Error | any,
    context: ErrorContext = {}
  ): ErrorResponse {
    const timestamp = new Date().toISOString();
    const requestId = this.generateRequestId();

    let errorResponse: ErrorResponse;

    // Check if it's already a formatted error response
    if (this.isErrorResponse(error)) {
      return error;
    }

    // Handle different error types
    if (error instanceof Error) {
      errorResponse = this.handleJavaScriptError(error, context, timestamp, requestId);
    } else if (typeof error === 'object' && error.response) {
      // Handle HTTP response errors
      errorResponse = this.handleHttpError(error, context, timestamp, requestId);
    } else if (typeof error === 'string') {
      errorResponse = this.handleStringError(error, context, timestamp, requestId);
    } else {
      errorResponse = this.handleUnknownError(error, context, timestamp, requestId);
    }

    // Log the error
    this.logError(errorResponse, context);

    return errorResponse;
  }

  /**
   * Handle JavaScript Error objects
   */
  private handleJavaScriptError(
    error: Error,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorResponse {
    let errorCode = ErrorCode.INTERNAL_ERROR;
    let userFriendlyMessage = "I encountered an unexpected issue. Please try again.";

    // Categorize based on error message patterns
    if (error.message.includes("API key not valid") || error.message.includes("API_KEY_INVALID")) {
      errorCode = ErrorCode.AUTHENTICATION_ERROR;
      userFriendlyMessage = "There seems to be an issue with the API key configuration. Please check the settings.";
    } else if (error.message.includes("INVALID_ARGUMENT") && error.message.includes("Schema validation failed")) {
      errorCode = ErrorCode.VALIDATION_ERROR;
      userFriendlyMessage = "I'm having trouble processing that request. Could you try rephrasing it?";
    } else if (error.message.includes("fetch") || error.message.includes("network")) {
      errorCode = ErrorCode.NETWORK_ERROR;
      userFriendlyMessage = "I'm having trouble connecting to my services. Please check your connection and try again.";
    } else if (error.message.includes("timeout")) {
      errorCode = ErrorCode.TIMEOUT_ERROR;
      userFriendlyMessage = "The request took too long to process. Please try again.";
    } else if (error.message.includes("plugin")) {
      errorCode = ErrorCode.PLUGIN_EXECUTION_ERROR;
      userFriendlyMessage = "I encountered an issue while executing a plugin. Please try again.";
    } else if (error.message.includes("memory")) {
      errorCode = ErrorCode.MEMORY_ERROR;
      userFriendlyMessage = "I had trouble accessing my memory. Please try again.";
    } else if (error.message.includes("AI") || error.message.includes("processing")) {
      errorCode = ErrorCode.AI_PROCESSING_ERROR;
      userFriendlyMessage = "I'm having trouble processing your request right now. Please try again.";
    }

    return {
      errorCode,
      message: error.message,
      details: {
        stack: error.stack,
        name: error.name,
        context,
      },
      requestId,
      timestamp,
      userFriendlyMessage,
    };
  }

  /**
   * Handle HTTP response errors
   */
  private handleHttpError(
    error: any,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorResponse {
    const status = error.response?.status || 0;
    const statusText = error.response?.statusText || 'Unknown';
    const responseData = error.response?.data;

    let errorCode = ErrorCode.INTERNAL_ERROR;
    let userFriendlyMessage = "I encountered a service error. Please try again.";

    // Map HTTP status codes to error codes
    switch (status) {
      case 400:
        errorCode = ErrorCode.VALIDATION_ERROR;
        userFriendlyMessage = "There was an issue with the request format. Please try again.";
        break;
      case 401:
        errorCode = ErrorCode.AUTHENTICATION_ERROR;
        userFriendlyMessage = "Authentication failed. Please check your credentials.";
        break;
      case 403:
        errorCode = ErrorCode.AUTHORIZATION_ERROR;
        userFriendlyMessage = "You don't have permission to perform this action.";
        break;
      case 404:
        errorCode = ErrorCode.NOT_FOUND;
        userFriendlyMessage = "The requested resource was not found.";
        break;
      case 429:
        errorCode = ErrorCode.RATE_LIMIT_EXCEEDED;
        userFriendlyMessage = "Too many requests. Please wait a moment and try again.";
        break;
      case 500:
      case 502:
      case 503:
        errorCode = ErrorCode.SERVICE_UNAVAILABLE;
        userFriendlyMessage = "The service is temporarily unavailable. Please try again later.";
        break;
      case 504:
        errorCode = ErrorCode.TIMEOUT_ERROR;
        userFriendlyMessage = "The request timed out. Please try again.";
        break;
    }

    return {
      errorCode,
      message: `HTTP ${status}: ${statusText}`,
      details: {
        status,
        statusText,
        responseData,
        context,
      },
      requestId,
      timestamp,
      userFriendlyMessage,
    };
  }

  /**
   * Handle string errors
   */
  private handleStringError(
    error: string,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorResponse {
    return {
      errorCode: ErrorCode.INTERNAL_ERROR,
      message: error,
      details: { context },
      requestId,
      timestamp,
      userFriendlyMessage: error.startsWith("Karen:") ? error : "I encountered an issue. Please try again.",
    };
  }

  /**
   * Handle unknown error types
   */
  private handleUnknownError(
    error: any,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorResponse {
    return {
      errorCode: ErrorCode.INTERNAL_ERROR,
      message: "An unknown error occurred",
      details: {
        error: JSON.stringify(error),
        context,
      },
      requestId,
      timestamp,
      userFriendlyMessage: "I encountered an unexpected issue. Please try again.",
    };
  }

  /**
   * Check if an object is already an ErrorResponse
   */
  private isErrorResponse(obj: any): obj is ErrorResponse {
    return obj && typeof obj === 'object' && 'errorCode' in obj && 'message' in obj && 'timestamp' in obj;
  }

  /**
   * Generate a unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Log error for debugging and monitoring
   */
  private logError(errorResponse: ErrorResponse, context: ErrorContext): void {
    // Add to internal log
    this.errorLog.push(errorResponse);
    
    // Keep log size manageable
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.splice(0, this.errorLog.length - this.maxLogSize);
    }

    // Console logging based on error severity
    const logLevel = this.getLogLevel(errorResponse.errorCode);
    const logMessage = `[${errorResponse.errorCode}] ${errorResponse.message}`;
    const logDetails = {
      requestId: errorResponse.requestId,
      timestamp: errorResponse.timestamp,
      context,
      details: errorResponse.details,
    };

    switch (logLevel) {
      case 'error':
        safeError(logMessage, logDetails);
        break;
      case 'warn':
        safeWarn(logMessage, logDetails);
        break;
      case 'info':
        safeInfo(logMessage, logDetails);
        break;
      default:
        console.log(logMessage, logDetails);
    }
  }

  /**
   * Get appropriate log level for error code
   */
  private getLogLevel(errorCode: ErrorCode): 'error' | 'warn' | 'info' | 'log' {
    switch (errorCode) {
      case ErrorCode.INTERNAL_ERROR:
      case ErrorCode.SERVICE_UNAVAILABLE:
      case ErrorCode.AI_PROCESSING_ERROR:
        return 'error';
      case ErrorCode.AUTHENTICATION_ERROR:
      case ErrorCode.AUTHORIZATION_ERROR:
      case ErrorCode.PLUGIN_EXECUTION_ERROR:
      case ErrorCode.MEMORY_ERROR:
        return 'warn';
      case ErrorCode.VALIDATION_ERROR:
      case ErrorCode.NOT_FOUND:
      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return 'info';
      default:
        return 'log';
    }
  }

  /**
   * Get recent error log
   */
  getErrorLog(limit: number = 10): ErrorResponse[] {
    return this.errorLog.slice(-limit);
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Get error statistics
   */
  getErrorStats(): {
    total: number;
    byCode: Record<string, number>;
    recent: ErrorResponse[];
  } {
    const byCode: Record<string, number> = {};
    
    this.errorLog.forEach(error => {
      byCode[error.errorCode] = (byCode[error.errorCode] || 0) + 1;
    });

    return {
      total: this.errorLog.length,
      byCode,
      recent: this.errorLog.slice(-5),
    };
  }
}

// Convenience functions
export function handleError(error: any, context: ErrorContext = {}): ErrorResponse {
  return UnifiedErrorHandler.getInstance().handleError(error, context);
}

export function getUserFriendlyMessage(error: any, context: ErrorContext = {}): string {
  const errorResponse = handleError(error, context);
  return errorResponse.userFriendlyMessage || errorResponse.message;
}

export function getErrorLog(limit?: number): ErrorResponse[] {
  return UnifiedErrorHandler.getInstance().getErrorLog(limit);
}

export function clearErrorLog(): void {
  UnifiedErrorHandler.getInstance().clearErrorLog();
}

export function getErrorStats() {
  return UnifiedErrorHandler.getInstance().getErrorStats();
}