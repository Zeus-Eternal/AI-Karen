'use client';

import React, { ReactNode } from 'react';
import { RefreshCw, AlertCircle, Clock, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { useRetry, RetryConfig } from '@/utils/retry-mechanisms';

interface RetryButtonProps {
  onRetry: () => void;
  isRetrying?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'icon';
  variant?: 'default' | 'outline' | 'ghost';
  className?: string;
  children?: ReactNode;
}

/**
 * Simple retry button component
 */
function RetryButton({
  onRetry,
  isRetrying = false,
  disabled = false,
  size = 'md',
  variant = 'default',
  className = '',
  children = 'Retry',
}: RetryButtonProps) {
  return (
    <Button
      onClick={onRetry}
      disabled={disabled || isRetrying}
      size={size}
      variant={variant}
      className={className}
    >
      <RefreshCw className={`h-4 w-4 mr-2 ${isRetrying ? 'animate-spin' : ''}`} />
      {isRetrying ? 'Retrying...' : children}
    </Button>
  );
}

interface RetryCardProps {
  title?: string;
  description?: string;
  error?: Error | null;
  onRetry: () => void;
  isRetrying?: boolean;
  attempt?: number;
  maxAttempts?: number;
  nextRetryIn?: number;
  canRetry?: boolean;
  className?: string;
}

/**
 * Comprehensive retry card with error details and progress
 */
function RetryCard({
  title = 'Operation Failed',
  description = 'An error occurred while processing your request.',
  error,
  onRetry,
  isRetrying = false,
  attempt = 0,
  maxAttempts = 3,
  nextRetryIn = 0,
  canRetry = true,
  className = '',
}: RetryCardProps) {
  const [countdown, setCountdown] = React.useState(nextRetryIn);

  React.useEffect(() => {
    if (nextRetryIn > 0 && isRetrying) {
      setCountdown(nextRetryIn);
      const interval = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 100) {
            clearInterval(interval);
            return 0;
          }
          return prev - 100;
        });
      }, 100);

      return () => clearInterval(interval);
    }
  }, [nextRetryIn, isRetrying]);

  const getErrorType = (error: Error | null) => {
    if (!error) return 'unknown';
    
    const message = error.message.toLowerCase();
    if (message.includes('network') || message.includes('fetch')) return 'network';
    if (message.includes('timeout')) return 'timeout';
    if (message.includes('server') || message.includes('5')) return 'server';
    return 'unknown';
  };

  const getErrorIcon = (errorType: string) => {
    switch (errorType) {
      case 'network':
        return <WifiOff className="h-5 w-5 text-orange-500" />;
      case 'timeout':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'server':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-destructive" />;
    }
  };

  const errorType = getErrorType(error || null);
  const progressValue = nextRetryIn > 0 ? ((nextRetryIn - countdown) / nextRetryIn) * 100 : 0;

  return (
    <Card className={`border-destructive/50 ${className}`}>
      <CardHeader>
        <div className="flex items-center space-x-3">
          {getErrorIcon(errorType)}
          <div className="flex-1">
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription className="flex items-center space-x-2 mt-1">
              <span>{description}</span>
              {attempt > 0 && (
                <Badge variant="outline" className="text-xs">
                  Attempt {attempt}/{maxAttempts}
                </Badge>
              )}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error Details</AlertTitle>
            <AlertDescription className="text-sm">
              {error.message}
            </AlertDescription>
          </Alert>
        )}

        {isRetrying && nextRetryIn > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Retrying automatically...</span>
              <span>{Math.ceil(countdown / 1000)}s</span>
            </div>
            <Progress value={progressValue} className="h-2" />
          </div>
        )}

        <div className="flex gap-2">
          <RetryButton
            onRetry={onRetry}
            isRetrying={isRetrying}
            disabled={!canRetry}
            className="flex-1"
          />
          
          {!canRetry && (
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
              className="flex-1"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Page
            </Button>
          )}
        </div>

        {errorType === 'network' && (
          <div className="text-xs text-muted-foreground text-center">
            Check your internet connection and try again
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface RetryWrapperProps<T> {
  operation: () => Promise<T>;
  config?: Partial<RetryConfig>;
  children: (state: {
    data: T | null;
    error: Error | null;
    isLoading: boolean;
    isRetrying: boolean;
    attempt: number;
    canRetry: boolean;
    retry: () => void;
    reset: () => void;
  }) => ReactNode;
  fallback?: ReactNode;
  errorFallback?: (error: Error, retry: () => void) => ReactNode;
}

/**
 * Wrapper component that handles retry logic and provides render props
 */
function RetryWrapper<T>({
  operation,
  config = {},
  children,
  fallback,
  errorFallback,
}: RetryWrapperProps<T>) {
  const retryState = useRetry(operation, config);

  React.useEffect(() => {
    // Auto-execute on mount
    retryState.execute();
  }, []);

  if (retryState.isLoading && !retryState.isRetrying && fallback) {
    return <>{fallback}</>;
  }

  if (retryState.error && !retryState.isRetrying && errorFallback) {
    return <>{errorFallback(retryState.error, retryState.retry)}</>;
  }

  return <>{children(retryState)}</>;
}

interface InlineRetryProps {
  onRetry: () => void;
  error?: Error | null;
  isRetrying?: boolean;
  canRetry?: boolean;
  className?: string;
}

/**
 * Inline retry component for smaller UI elements
 */
function InlineRetry({
  onRetry,
  error,
  isRetrying = false,
  canRetry = true,
  className = '',
}: InlineRetryProps) {
  return (
    <div className={`flex items-center space-x-2 text-sm ${className}`}>
      <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
      <span className="text-destructive flex-1">
        {error?.message || 'Failed to load'}
      </span>
      {canRetry && (
        <button
          onClick={onRetry}
          disabled={isRetrying}
          className="text-primary hover:text-primary/80 underline disabled:opacity-50"
        >
          {isRetrying ? 'Retrying...' : 'Retry'}
        </button>
      )}
    </div>
  );
}

interface RetryBannerProps {
  message?: string;
  onRetry: () => void;
  onDismiss?: () => void;
  isRetrying?: boolean;
  canRetry?: boolean;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
}

/**
 * Banner component for retry notifications
 */
function RetryBanner({
  message = 'Something went wrong. Please try again.',
  onRetry,
  onDismiss,
  isRetrying = false,
  canRetry = true,
  variant = 'error',
  className = '',
}: RetryBannerProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-red-50 border-red-200 text-red-800';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getVariantStyles()} ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm font-medium">{message}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          {canRetry && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              disabled={isRetrying}
              className="h-8"
            >
              <RefreshCw className={`h-3 w-3 mr-1 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? 'Retrying' : 'Retry'}
            </Button>
          )}
          
          {onDismiss && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onDismiss}
              className="h-8 w-8 p-0"
            >
              ×
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

interface LoadingRetryProps {
  isLoading: boolean;
  isRetrying: boolean;
  error?: Error | null;
  onRetry: () => void;
  loadingText?: string;
  retryingText?: string;
  children: ReactNode;
  className?: string;
}

/**
 * Component that shows loading states and retry options
 */
function LoadingRetry({
  isLoading,
  isRetrying,
  error,
  onRetry,
  loadingText = 'Loading...',
  retryingText = 'Retrying...',
  children,
  className = '',
}: LoadingRetryProps) {
  if (isLoading && !isRetrying) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center space-y-3">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{loadingText}</p>
        </div>
      </div>
    );
  }

  if (isRetrying) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center space-y-3">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-sm text-muted-foreground">{retryingText}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <RetryCard
          error={error}
          onRetry={onRetry}
          canRetry={true}
          className="max-w-md"
        />
      </div>
    );
  }

  return <div className={className}>{children}</div>;
}

export {
  RetryButton,
  RetryCard,
  RetryWrapper,
  InlineRetry,
  RetryBanner,
  LoadingRetry,
};