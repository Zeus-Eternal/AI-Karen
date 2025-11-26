import React from 'react';
import { Button } from './button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

/**
 * Component for handling errors in functional components
 */
export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          <div className="p-6 text-center">
            <div className="flex justify-center mb-4">
              <div className="rounded-full bg-red-100 dark:bg-red-900/20 p-3">
                <AlertTriangle className="h-12 w-12 text-red-600 dark:text-red-400" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
              An error occurred while rendering this component.
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md text-xs font-mono overflow-auto max-h-40">
                <div className="font-bold text-gray-900 dark:text-white">{error.name}:</div>
                <div className="text-gray-700 dark:text-gray-300">{error.message}</div>
                {error.stack && (
                  <div className="mt-2">
                    <div className="font-bold text-gray-900 dark:text-white">Stack:</div>
                    <pre className="whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300">
                      {error.stack}
                    </pre>
                  </div>
                )}
              </div>
            </div>
            
            <Button onClick={resetErrorBoundary} className="w-full gap-2">
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}