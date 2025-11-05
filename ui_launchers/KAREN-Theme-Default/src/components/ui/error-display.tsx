/**
 * Error Display Components
 * 
 * Reusable components for displaying errors with user-friendly messages
 * and suggested remediation steps.
 * 
 * Requirements: 7.2, 7.4
 */
"use client";

import React from 'react';
import { AlertTriangle, RefreshCw, X, Info, AlertCircle, XCircle } from 'lucide-react';
import type { AdminError } from '@/lib/errors/admin-error-handler';
interface ErrorDisplayProps {
  error: AdminError;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  showRemediation?: boolean;
  compact?: boolean;
}
export function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  className = '',
  showRemediation = true,
  compact = false
}: ErrorDisplayProps) {
  const getSeverityIcon = () => {
    switch (error.severity) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500 " />;
      case 'high':
        return <AlertCircle className="h-5 w-5 text-red-500 " />;
      case 'medium':
        return <AlertTriangle className="h-5 w-5 text-yellow-500 " />;
      case 'low':
        return <Info className="h-5 w-5 text-blue-500 " />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500 " />;
    }
  };
  const getSeverityColors = () => {
    switch (error.severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'high':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    }
  };
  if (compact) {
    return (
      <div className={`flex items-center p-3 border rounded-md ${getSeverityColors()} ${className}`}>
        {getSeverityIcon()}
        <span className="ml-2 text-sm font-medium md:text-base lg:text-lg">{error.message}</span>
        <div className="ml-auto flex items-center space-x-2">
          {error.retryable && onRetry && (
            <Button
              onClick={onRetry}
              className="text-sm underline hover:no-underline focus:outline-none md:text-base lg:text-lg"
              aria-label="Retry operation"
            >
            </Button>
          )}
          {onDismiss && (
            <Button
              onClick={onDismiss}
              className="text-sm hover:opacity-70 focus:outline-none md:text-base lg:text-lg"
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4 " />
            </Button>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className={`border rounded-lg p-4 ${getSeverityColors()} ${className}`} role="alert">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getSeverityIcon()}
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium md:text-base lg:text-lg">
            {error.message}
          </h3>
          {error.details && error.details !== error.message && (
            <div className="mt-2 text-sm opacity-90 md:text-base lg:text-lg">
              {error.details}
            </div>
          )}
          {showRemediation && error.remediation && error.remediation.length > 0 && (
            <div className="mt-3">
              <h4 className="text-sm font-medium mb-2 md:text-base lg:text-lg">What you can do:</h4>
              <ul className="text-sm space-y-1 list-disc list-inside opacity-90 md:text-base lg:text-lg">
                {error.remediation.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="mt-4 flex items-center space-x-3">
            {error.retryable && onRetry && (
              <Button
                onClick={onRetry}
                className="inline-flex items-center text-sm font-medium underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 md:text-base lg:text-lg"
                aria-label="Retry the failed operation"
              >
                <RefreshCw className="h-4 w-4 mr-1 " />
              </Button>
            )}
            <span className="text-xs opacity-75 sm:text-sm md:text-base">
              Error Code: {error.code}
            </span>
          </div>
        </div>
        {onDismiss && (
          <div className="ml-4 flex-shrink-0">
            <Button
              onClick={onDismiss}
              className="inline-flex text-sm hover:opacity-70 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 md:text-base lg:text-lg"
              aria-label="Dismiss this error"
            >
              <X className="h-5 w-5 " />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
interface ErrorBoundaryState {
  hasError: boolean;
  error?: AdminError;
}
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: AdminError; retry: () => void }>;
  onError?: (error: AdminError) => void;
}
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error: {
        code: 'COMPONENT_ERROR',
        message: 'A component error occurred.',
        details: error.message,
        remediation: [
          'Try refreshing the page',
          'Clear your browser cache',
          'Contact support if the problem persists'
        ],
        severity: 'high',
        retryable: true
      }
    };
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (this.props.onError && this.state.error) {
      this.props.onError(this.state.error);
    }
  }
  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };
  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error} retry={this.handleRetry} />;
      }
      return (
        <div className="p-4 sm:p-4 md:p-6">
          <ErrorDisplay
            error={this.state.error}
            onRetry={this.handleRetry}
            showRemediation={true}
          />
        </div>
      );
    }
    return this.props.children;
  }
}
interface ErrorToastProps {
  error: AdminError;
  onDismiss: () => void;
  autoHide?: boolean;
  hideDelay?: number;
}
export function ErrorToast({ 
  error, 
  onDismiss, 
  autoHide = true, 
  hideDelay = 5000 
}: ErrorToastProps) {
  React.useEffect(() => {
    if (autoHide && error.severity !== 'critical' && error.severity !== 'high') {
      const timer = setTimeout(onDismiss, hideDelay);
      return () => clearTimeout(timer);
    }
  }, [autoHide, hideDelay, onDismiss, error.severity]);
  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      <ErrorDisplay
        error={error}
        onDismiss={onDismiss}
        compact={true}
        showRemediation={false}
        className="shadow-lg"
      />
    </div>
  );
}
export default ErrorDisplay;
