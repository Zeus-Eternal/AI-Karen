"use client";

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SimpleErrorFallbackProps {
  error?: Error;
  reset?: () => void;
  message?: string;
}

export function SimpleErrorFallback({ error, reset, message }: SimpleErrorFallbackProps) {
  return (
    <div className="flex items-center justify-center p-8 bg-muted/50 rounded-lg border border-destructive/20">
      <div className="text-center space-y-4 max-w-md">
        <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
        <div>
          <h3 className="text-lg font-semibold mb-2">Something went wrong</h3>
          <p className="text-sm text-muted-foreground">
            {message || error?.message || 'An unexpected error occurred. Please try again.'}
          </p>
        </div>
        {reset && (
          <Button onClick={reset} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}

export default SimpleErrorFallback;