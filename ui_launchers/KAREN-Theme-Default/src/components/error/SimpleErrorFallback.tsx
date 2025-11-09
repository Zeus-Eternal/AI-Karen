"use client";

import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SimpleErrorFallbackProps {
  error?: Error | null;
  resetErrorBoundary?: () => void;
  onGoHome?: () => void;
  title?: string;
  message?: string;
  showDetails?: boolean;
  className?: string;
}

export default function SimpleErrorFallback({
  error,
  resetErrorBoundary,
  onGoHome,
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  showDetails = false,
  className,
}: SimpleErrorFallbackProps) {
  return (
    <div className={cn('flex items-center justify-center min-h-[400px] p-4', className)}>
      <Card className="max-w-lg w-full">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>{message}</CardDescription>
            </div>
          </div>
        </CardHeader>

        {showDetails && error && (
          <CardContent>
            <div className="rounded-md bg-gray-50 dark:bg-gray-900 p-4">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                Error Details:
              </p>
              <pre className="text-xs text-red-600 dark:text-red-400 overflow-auto max-h-32">
                {error.message}
              </pre>
              {error.stack && (
                <details className="mt-2">
                  <summary className="text-xs cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">
                    Stack Trace
                  </summary>
                  <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-48 mt-2">
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>
          </CardContent>
        )}

        <CardFooter className="gap-2">
          {resetErrorBoundary && (
            <Button onClick={resetErrorBoundary} variant="default" className="flex-1">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          )}
          {onGoHome && (
            <Button onClick={onGoHome} variant="outline" className="flex-1">
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}

export { SimpleErrorFallback };
