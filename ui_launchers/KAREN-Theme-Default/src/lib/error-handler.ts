/**
 * @file error-handler.ts
 * @description Comprehensive error handling utilities for the frontend
 * 
 * Provides:
 * - User-friendly error message formatting
 * - Error categorization and severity assessment
 * - Toast notification integration
 * - Loading state management
 * - Retry logic coordination
 */
import { toast } from "@/hooks/use-toast";
export interface ErrorInfo {
  category: string;
  severity: string;
  title: string;
  message: string;
  technical_details?: string;
  resolution_steps?: string[];
  retry_possible?: boolean;
  user_action_required?: boolean;
  error_code?: string;
  context?: Record<string, any>;
}
export interface ApiErrorResponse {
  error: boolean;
  error_code?: string;
  category?: string;
  severity?: string;
  title?: string;
  message?: string;
  technical_details?: string;
  resolution_steps?: string[];
  retry_possible?: boolean;
  user_action_required?: boolean;
  context?: Record<string, any>;
}

// Extended Error interface to handle API errors with additional properties
interface ExtendedError extends Error {
  detail?: ApiErrorResponse;
  response?: {
    status?: number;
    data?: ApiErrorResponse;
  };
  code?: string;
  status?: number;
}
export class ErrorHandler {
  private static instance: ErrorHandler;
  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }
  /**
   * Handle API errors and show appropriate user feedback
   */
  public handleApiError(error: ExtendedError, operation: string = 'operation'): ErrorInfo {
    let errorInfo: ErrorInfo;
    // Check if it's a structured API error response
    if (error?.detail && typeof error.detail === 'object' && error.detail.error) {
      errorInfo = this.parseApiErrorResponse(error.detail);
    } else if (error?.response?.data && typeof error.response.data === 'object' && error.response.data.error) {
      errorInfo = this.parseApiErrorResponse(error.response.data);
    } else {
      // Handle generic errors
      errorInfo = this.createGenericErrorInfo(error, operation);
    }
    // Show toast notification
    this.showErrorToast(errorInfo);
    return errorInfo;
  }
  /**
   * Parse structured API error response
   */
  private parseApiErrorResponse(apiError: ApiErrorResponse): ErrorInfo {
    return {
      category: apiError.category || 'system',
      severity: apiError.severity || 'medium',
      title: apiError.title || 'Error',
      message: apiError.message || 'An error occurred',
      technical_details: apiError.technical_details,
      resolution_steps: apiError.resolution_steps || [],
      retry_possible: apiError.retry_possible || false,
      user_action_required: apiError.user_action_required || false,
      error_code: apiError.error_code,
      context: apiError.context || {}
    };
  }
  /**
   * Create error info for generic errors
   */
  private createGenericErrorInfo(error: ExtendedError, operation: string): ErrorInfo {
    let title = 'Operation Failed';
    let message = `The ${operation} could not be completed.`;
    let category = 'system';
    let severity = 'medium';
    let retryPossible = true;
    // Handle specific error types
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('network')) {
      title = 'Network Error';
      message = 'Unable to connect to the server. Please check your internet connection.';
      category = 'network';
      severity = 'high';
    } else if (error?.code === 'TIMEOUT' || error?.message?.includes('timeout')) {
      title = 'Request Timeout';
      message = 'The request took too long to complete. Please try again.';
      category = 'network';
      severity = 'medium';
    } else if (error?.status === 404) {
      title = 'Not Found';
      message = 'The requested resource was not found.';
      category = 'validation';
      severity = 'medium';
      retryPossible = false;
    } else if (error?.status === 403) {
      title = 'Permission Denied';
      message = 'You do not have permission to perform this action.';
      category = 'permission';
      severity = 'high';
      retryPossible = false;
    } else if (error?.status === 507) {
      title = 'Insufficient Storage';
      message = 'Not enough disk space available to complete the operation.';
      category = 'disk_space';
      severity = 'high';
      retryPossible = false;
    } else if (error?.status && error.status >= 500) {
      title = 'Server Error';
      message = 'The server encountered an error. Please try again later.';
      category = 'system';
      severity = 'high';
    }
    return {
      category,
      severity,
      title,
      message,
      technical_details: error?.message || String(error),
      resolution_steps: this.getDefaultResolutionSteps(category),
      retry_possible: retryPossible,
      user_action_required: !retryPossible,
      error_code: error?.code || error?.status?.toString(),
      context: { operation, originalError: error }
    };
  }
  /**
   * Get default resolution steps for error categories
   */
  private getDefaultResolutionSteps(category: string): string[] {
    switch (category) {
      case 'network':
        return [
          'Check your internet connection',
          'Try again in a few moments',
          'Contact support if the problem persists'
        ];
      case 'disk_space':
        return [
          'Free up disk space by deleting unnecessary files',
          'Remove unused models from the Model Library',
          'Check available storage in system settings'
        ];
      case 'permission':
        return [
          'Check if you have the necessary permissions',
          'Try running as administrator if needed',
          'Contact your system administrator'
        ];
      case 'validation':
        return [
          'Check the input and try again',
          'Refresh the page and retry',
          'Contact support if the problem persists'
        ];
      default:
        return [
          'Try the operation again',
          'Refresh the page if the problem persists',
          'Contact support for assistance'
        ];
    }
  }
  /**
   * Show error toast notification (client-side only)
   */
  private showErrorToast(errorInfo: ErrorInfo) {
    // Only show toast on client side
    if (typeof window === 'undefined') {
      return;
    }
    const variant = this.getToastVariant(errorInfo.severity);
    toast({
      title: errorInfo.title,
      description: errorInfo.message,
      variant,
      duration: this.getToastDuration(errorInfo.severity),
    });
  }
  /**
   * Get toast variant based on severity
   */
  private getToastVariant(severity: string): "default" | "destructive" {
    return severity === 'high' || severity === 'critical' ? 'destructive' : 'default';
  }
  /**
   * Get toast duration based on severity
   */
  private getToastDuration(severity: string): number {
    switch (severity) {
      case 'critical':
        return 10000; // 10 seconds
      case 'high':
        return 7000;  // 7 seconds
      case 'medium':
        return 5000;  // 5 seconds
      case 'low':
        return 3000;  // 3 seconds
      default:
        return 5000;
    }
  }
  /**
   * Show success notification
   */
  public showSuccess(title: string, message: string, duration: number = 3000) {
    toast({
      title,
      description: message,
      variant: "default",
      duration,
    });
  }
  /**
   * Show info notification
   */
  public showInfo(title: string, message: string, duration: number = 4000) {
    toast({
      title,
      description: message,
      variant: "default",
      duration,
    });
  }
  /**
   * Show warning notification
   */
  public showWarning(title: string, message: string, duration: number = 5000) {
    toast({
      title,
      description: message,
      variant: "default",
      duration,
    });
  }
  /**
   * Handle download-specific errors
   */
  public handleDownloadError(error: ExtendedError, modelName: string): ErrorInfo {
    const errorInfo = this.handleApiError(error, `download of ${modelName}`);
    // Add download-specific context
    errorInfo.context = {
      ...errorInfo.context,
      modelName,
      operation: 'download'
    };
    return errorInfo;
  }
  /**
   * Handle model management errors
   */
  public handleModelManagementError(error: ExtendedError, operation: string, modelName: string): ErrorInfo {
    const errorInfo = this.handleApiError(error, `${operation} of ${modelName}`);
    // Add model management context
    errorInfo.context = {
      ...errorInfo.context,
      modelName,
      operation
    };
    return errorInfo;
  }
  /**
   * Create confirmation dialog data for destructive operations
   */
  public createConfirmationDialog(operation: string, modelName: string) {
    const confirmations = {
      delete: {
        title: 'Delete Model',
        message: `Are you sure you want to delete "${modelName}"? This action cannot be undone.`,
        confirmText: 'Delete',
        cancelText: 'Cancel',
        variant: 'destructive' as const
      },
      cancel: {
        title: 'Cancel Download',
        message: `Are you sure you want to cancel the download of "${modelName}"?`,
        confirmText: 'Cancel Download',
        cancelText: 'Keep Downloading',
        variant: 'destructive' as const
      }
    };
    return confirmations[operation as keyof typeof confirmations] || {
      title: 'Confirm Action',
      message: `Are you sure you want to ${operation} "${modelName}"?`,
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      variant: 'default' as const
    };
  }
  /**
   * Format file size for user display
   */
  public formatFileSize(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
  /**
   * Format download speed
   */
  public formatSpeed(bytesPerSecond: number): string {
    return `${this.formatFileSize(bytesPerSecond)}/s`;
  }
  /**
   * Format time duration
   */
  public formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  }
  /**
   * Check if error is retryable
   */
  public isRetryable(errorInfo: ErrorInfo): boolean {
    return errorInfo.retry_possible === true;
  }
  /**
   * Check if user action is required
   */
  public requiresUserAction(errorInfo: ErrorInfo): boolean {
    return errorInfo.user_action_required === true;
  }
  /**
   * Get resolution steps as formatted string
   */
  public getResolutionStepsText(errorInfo: ErrorInfo): string {
    if (!errorInfo.resolution_steps || errorInfo.resolution_steps.length === 0) {
      return '';
    }
    return errorInfo.resolution_steps
      .map((step, index) => `${index + 1}. ${step}`)
      .join('\n');
  }
}
// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();
// Export convenience functions
export const handleApiError = (error: ExtendedError, operation?: string) => 
  errorHandler.handleApiError(error, operation);
export const showSuccess = (title: string, message: string, duration?: number) => 
  errorHandler.showSuccess(title, message, duration);
export const showInfo = (title: string, message: string, duration?: number) => 
  errorHandler.showInfo(title, message, duration);
export const showWarning = (title: string, message: string, duration?: number) => 
  errorHandler.showWarning(title, message, duration);
export const handleDownloadError = (error: ExtendedError, modelName: string) => 
  errorHandler.handleDownloadError(error, modelName);
export const handleModelManagementError = (error: ExtendedError, operation: string, modelName: string) => 
  errorHandler.handleModelManagementError(error, operation, modelName);
export const createConfirmationDialog = (operation: string, modelName: string) => 
  errorHandler.createConfirmationDialog(operation, modelName);
export const formatFileSize = (bytes: number) => errorHandler.formatFileSize(bytes);
export const formatSpeed = (bytesPerSecond: number) => errorHandler.formatSpeed(bytesPerSecond);
export const formatDuration = (seconds: number) => errorHandler.formatDuration(seconds);
