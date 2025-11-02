'use client';

/**
 * Loading Components with Next.js Consistency
 * 
 * Features:
 * - Consistent with Next.js loading patterns
 * - React Suspense integration
 * - Server-side rendering compatibility
 * - Accessible loading states
 * - Customizable loading indicators
 */

import React, { Suspense } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Bot, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  message?: string;
  className?: string;
  fullScreen?: boolean;
}

/**
 * Primary loading component
 */
const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  variant = 'spinner',
  message,
  className,
  fullScreen = false
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  const containerClasses = cn(
    'flex items-center justify-center',
    fullScreen && 'min-h-screen',
    className
  );

  const renderLoadingIndicator = () => {
    switch (variant) {
      case 'dots':
        return (
          <div className="flex items-center gap-1">
            {[0, 0.2, 0.4].map((delay, index) => (
              <motion.div
                key={index}
                animate={{ scale: [1, 1.5, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ 
                  repeat: Infinity, 
                  duration: 1.5, 
                  delay,
                  ease: "easeInOut"
                }}
                className={cn(
                  "rounded-full bg-blue-500",
                  size === 'sm' && 'w-2 h-2',
                  size === 'md' && 'w-3 h-3',
                  size === 'lg' && 'w-4 h-4'
                )}
              />
            ))}
          </div>
        );

      case 'pulse':
        return (
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className={cn(
              "rounded-full bg-blue-500/20 flex items-center justify-center",
              size === 'sm' && 'w-8 h-8',
              size === 'md' && 'w-12 h-12',
              size === 'lg' && 'w-16 h-16'
            )}
          >
            <Bot className={cn("text-blue-500", sizeClasses[size])} />
          </motion.div>
        );

      case 'skeleton':
        return (
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
            <Skeleton className="h-4 w-[150px]" />
          </div>
        );

      case 'spinner':
      default:
        return (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className={cn("text-blue-500", sizeClasses[size])} />
          </motion.div>
        );
    }
  };

  return (
    <div className={containerClasses}>
      <div className="flex flex-col items-center gap-3">
        {renderLoadingIndicator()}
        {message && (
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

/**
 * Page-level loading component for Next.js pages
 */
const PageLoading: React.FC<{ message?: string }> = ({ 
  message = "Loading..." 
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <Card className="w-full max-w-md">
      <CardContent className="p-8">
        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-full"
          >
            <Sparkles className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </motion.div>
          
          <div className="text-center">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {message}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Please wait while we prepare your experience
            </p>
          </div>
          
          <div className="flex items-center gap-1">
            {[0, 0.3, 0.6].map((delay, index) => (
              <motion.div
                key={index}
                animate={{ 
                  y: [-4, 4, -4],
                  opacity: [0.5, 1, 0.5]
                }}
                transition={{ 
                  repeat: Infinity, 
                  duration: 1.5, 
                  delay,
                  ease: "easeInOut"
                }}
                className="w-2 h-2 rounded-full bg-blue-500"
              />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);

/**
 * Component loading wrapper for Suspense boundaries
 */
const ComponentLoading: React.FC<{ 
  message?: string;
  variant?: 'card' | 'inline' | 'overlay';
}> = ({ 
  message = "Loading component...", 
  variant = 'card' 
}) => {
  if (variant === 'inline') {
    return (
      <div className="flex items-center gap-2 p-2">
        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {message}
        </span>
      </div>
    );
  }

  if (variant === 'overlay') {
    return (
      <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-10">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {message}
          </span>
        </div>
      </div>
    );
  }

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div className="flex items-center justify-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          <span className="text-gray-600 dark:text-gray-400">
            {message}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Chat-specific loading component
 */
const ChatLoading: React.FC = () => (
  <div className="flex gap-3 mb-6">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 text-white flex items-center justify-center shadow-sm">
      <Bot className="h-4 w-4" />
    </div>
    <div className="flex-1">
      <div className="inline-block p-4 rounded-2xl bg-white border border-gray-200 shadow-sm dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {[0, 0.2, 0.4].map((delay, index) => (
            <motion.div
              key={index}
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 1.5, delay }}
              className="w-2 h-2 bg-emerald-500 rounded-full"
            />
          ))}
          <span className="text-sm text-gray-500 ml-2">AI is thinking...</span>
        </div>
      </div>
    </div>
  </div>
);

/**
 * Higher-order component for adding loading states
 */
function withLoading<P extends object>(
  Component: React.ComponentType<P>,
  LoadingComponent: React.ComponentType = Loading
) {
  return function WithLoadingComponent(props: P & { isLoading?: boolean }) {
    const { isLoading, ...componentProps } = props;
    
    if (isLoading) {
      return <LoadingComponent />;
    }
    
    return <Component {...(componentProps as P)} />;
  };
}

/**
 * Suspense wrapper with consistent loading UI
 */
const SuspenseWrapper: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
  message?: string;
}> = ({ 
  children, 
  fallback, 
  message = "Loading..." 
}) => (
  <Suspense 
    fallback={fallback || <ComponentLoading message={message} />}
  >
    {children}
  </Suspense>
);

/**
 * Loading state hook for consistent loading management
 */
function useLoadingState(initialState = false) {
  const [isLoading, setIsLoading] = React.useState(initialState);
  const [error, setError] = React.useState<Error | null>(null);

  const startLoading = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const stopLoading = React.useCallback(() => {
    setIsLoading(false);
  }, []);

  const setLoadingError = React.useCallback((error: Error) => {
    setError(error);
    setIsLoading(false);
  }, []);

  const withLoading = React.useCallback(
    async <T,>(asyncFn: () => Promise<T>): Promise<T | null> => {
      try {
        startLoading();
        const result = await asyncFn();
        stopLoading();
        return result;
      } catch (err) {
        setLoadingError(err instanceof Error ? err : new Error('Unknown error'));
        return null;
      }
    },
    [startLoading, stopLoading, setLoadingError]
  );

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setLoadingError,
    withLoading
  };
}

// Export all components
export {
  Loading as default,
  PageLoading,
  ComponentLoading,
  ChatLoading,
  withLoading,
  SuspenseWrapper,
  useLoadingState
};