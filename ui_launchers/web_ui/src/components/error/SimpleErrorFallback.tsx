/**
 * Simple Error Fallback Component
 * 
 * A lightweight error boundary fallback that doesn't trigger additional API calls
 */

'use client';

import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface SimpleErrorFallbackProps {
  error: Error;
  resetError: () => void;
  className?: string;
}

export const SimpleErrorFallback: React.FC<SimpleErrorFallbackProps> = ({
  error,
  resetError,
  className = '',
}) => {
  const handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  const handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  return (
    <div className={`min-h-screen bg-background flex items-center justify-center p-4 ${className}`}>
      <Card className="w-full max-w-md border-destructive/50">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <div>
              <CardTitle className="text-xl">Something went wrong</CardTitle>
              <CardDescription className="mt-1">
                An unexpected error occurred
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm font-medium text-destructive">
              {error.message || 'Unknown error'}
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={resetError} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            
            <Button variant="outline" onClick={handleReload} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Page
            </Button>
            
            <Button variant="outline" onClick={handleGoHome} className="w-full">
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            <p>If this error persists, please contact support.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SimpleErrorFallback;