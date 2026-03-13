"use client";

import React from 'react';
import { Loader2, RefreshCw, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import { Card, CardContent } from './card';

export interface EnhancedLoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'skeleton' | 'progress' | 'dots';
  message?: string;
  showProgress?: boolean;
  progress?: number;
  cancellable?: boolean;
  onCancel?: () => void;
  retryable?: boolean;
  onRetry?: () => void;
  error?: string;
  className?: string;
  fullScreen?: boolean;
  centered?: boolean;
}

const LoadingSpinner = ({ size = 'md', className }: { size?: 'sm' | 'md' | 'lg' | 'xl'; className?: string }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <Loader2 className={cn('animate-spin', sizeClasses[size], className)} />
  );
};

const LoadingSkeleton = ({ 
  lines = 3, 
  className 
}: { 
  lines?: number; 
  className?: string; 
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-muted rounded animate-pulse"
          style={{
            width: `${Math.random() * 40 + 60}%`, // Random width between 60-100%
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
};

const LoadingDots = ({ className }: { className?: string }) => {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  );
};

const ProgressBar = ({ 
  progress = 0, 
  showPercentage = true,
  className 
}: { 
  progress?: number; 
  showPercentage?: boolean;
  className?: string; 
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  
  return (
    <div className={cn('w-full', className)}>
      {showPercentage && (
        <div className="mb-2 text-sm text-muted-foreground text-center">
          {Math.round(clampedProgress)}%
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
};

export const EnhancedLoading: React.FC<EnhancedLoadingProps> = ({
  size = 'md',
  variant = 'spinner',
  message,
  showProgress = false,
  progress = 0,
  cancellable = false,
  onCancel,
  retryable = false,
  onRetry,
  error,
  className,
  fullScreen = false,
  centered = true,
}) => {
  const content = (
    <div className={cn(
      'flex flex-col items-center justify-center space-y-4',
      centered && 'min-h-[200px]',
      fullScreen && 'min-h-screen',
      className
    )}>
      {/* Loading Indicator */}
      <div className="flex items-center justify-center">
        {variant === 'spinner' && <LoadingSpinner size={size} />}
        {variant === 'skeleton' && <LoadingSkeleton />}
        {variant === 'dots' && <LoadingDots />}
        {variant === 'progress' && <ProgressBar progress={progress} />}
      </div>

      {/* Message */}
      {message && (
        <p className="text-sm text-muted-foreground text-center max-w-md">
          {message}
        </p>
      )}

      {/* Progress Bar (if separate from variant) */}
      {showProgress && variant !== 'progress' && (
        <div className="w-full max-w-sm">
          <ProgressBar progress={progress} showPercentage={false} />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex flex-col items-center space-y-3 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-destructive max-w-md">{error}</p>
          {retryable && onRetry && (
            <Button
              onClick={onRetry}
              variant="outline"
              size="sm"
              aria-label="Retry operation"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          )}
        </div>
      )}

      {/* Cancel Button */}
      {cancellable && onCancel && !error && (
        <Button
          onClick={onCancel}
          variant="outline"
          size="sm"
          aria-label="Cancel operation"
        >
          Cancel
        </Button>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
};

// Card wrapper for inline loading states
export const LoadingCard: React.FC<
  Omit<EnhancedLoadingProps, 'fullScreen' | 'centered'> & {
    title?: string;
  }
> = ({ title, ...props }) => {
  return (
    <Card className="w-full">
      {title && (
        <div className="p-4 border-b">
          <h3 className="font-medium">{title}</h3>
        </div>
      )}
      <CardContent className="p-6">
        <EnhancedLoading {...props} centered={false} />
      </CardContent>
    </Card>
  );
};

// Hook for managing loading states
export const useLoadingState = (
  initialState: boolean = false
) => {
  const [isLoading, setIsLoading] = React.useState(initialState);
  const [error, setError] = React.useState<string | null>(null);
  const [progress, setProgress] = React.useState<number>(0);

  const startLoading = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
  }, []);

  const stopLoading = React.useCallback(() => {
    setIsLoading(false);
  }, []);

  const setLoadingError = React.useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
  }, []);

  const updateProgress = React.useCallback((newProgress: number) => {
    setProgress(Math.min(100, Math.max(0, newProgress)));
  }, []);

  return {
    isLoading,
    error,
    progress,
    startLoading,
    stopLoading,
    setLoadingError,
    updateProgress,
  };
};

export default EnhancedLoading;