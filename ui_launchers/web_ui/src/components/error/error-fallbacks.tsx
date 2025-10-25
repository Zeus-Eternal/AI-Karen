'use client';

import React from 'react';
import { AlertTriangle, RefreshCw, Home, Wifi, WifiOff, Database, Server, Bug } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

interface ErrorFallbackProps {
  error?: Error;
  onRetry?: () => void;
  onReload?: () => void;
  onGoHome?: () => void;
  canRetry?: boolean;
  errorId?: string;
  className?: string;
}

/**
 * Generic error fallback component
 */
export function ErrorFallback({
  error,
  onRetry,
  onReload,
  onGoHome,
  canRetry = true,
  errorId,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={`flex items-center justify-center p-4 ${className || ''}`}>
      <Card className="w-full max-w-md border-destructive/50">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <AlertTriangle className="h-12 w-12 text-destructive" />
          </div>
          <CardTitle className="text-xl font-semibold">
            Something went wrong
          </CardTitle>
          <CardDescription>
            An unexpected error occurred. Please try again.
          </CardDescription>
          {errorId && (
            <Badge variant="outline" className="w-fit mx-auto mt-2">
              ID: {errorId.slice(-8)}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert>
              <Bug className="h-4 w-4" />
              <AlertTitle>Error Details</AlertTitle>
              <AlertDescription className="text-sm">
                {error.message}
              </AlertDescription>
            </Alert>
          )}
          
          <div className="flex gap-2">
            {canRetry && onRetry && (
              <Button onClick={onRetry} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}
            {onReload && (
              <Button variant="outline" onClick={onReload} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload
              </Button>
            )}
            {onGoHome && (
              <Button variant="outline" onClick={onGoHome} className="flex-1">
                <Home className="h-4 w-4 mr-2" />
                Home
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Network error fallback component
 */
export function NetworkErrorFallback({
  onRetry,
  onReload,
  canRetry = true,
  className,
}: Omit<ErrorFallbackProps, 'error'>) {
  return (
    <div className={`flex items-center justify-center p-4 ${className || ''}`}>
      <Card className="w-full max-w-md border-orange-500/50">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <WifiOff className="h-12 w-12 text-orange-500" />
          </div>
          <CardTitle className="text-xl font-semibold">
            Connection Error
          </CardTitle>
          <CardDescription>
            Unable to connect to the server. Please check your internet connection.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <Wifi className="h-4 w-4" />
            <AlertTitle>Network Issue</AlertTitle>
            <AlertDescription className="text-sm">
              This could be due to a temporary network issue or server maintenance.
            </AlertDescription>
          </Alert>
          
          <div className="flex gap-2">
            {canRetry && onRetry && (
              <Button onClick={onRetry} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}
            {onReload && (
              <Button variant="outline" onClick={onReload} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload Page
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Server error fallback component
 */
export function ServerErrorFallback({
  onRetry,
  onReload,
  canRetry = true,
  errorId,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={`flex items-center justify-center p-4 ${className || ''}`}>
      <Card className="w-full max-w-md border-red-500/50">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Server className="h-12 w-12 text-red-500" />
          </div>
          <CardTitle className="text-xl font-semibold">
            Server Error
          </CardTitle>
          <CardDescription>
            The server encountered an error. Our team has been notified.
          </CardDescription>
          {errorId && (
            <Badge variant="outline" className="w-fit mx-auto mt-2">
              ID: {errorId.slice(-8)}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <Server className="h-4 w-4" />
            <AlertTitle>Server Issue</AlertTitle>
            <AlertDescription className="text-sm">
              This is likely a temporary issue. Please try again in a few moments.
            </AlertDescription>
          </Alert>
          
          <div className="flex gap-2">
            {canRetry && onRetry && (
              <Button onClick={onRetry} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}
            {onReload && (
              <Button variant="outline" onClick={onReload} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload Page
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Database error fallback component
 */
export function DatabaseErrorFallback({
  onRetry,
  onReload,
  canRetry = true,
  errorId,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={`flex items-center justify-center p-4 ${className || ''}`}>
      <Card className="w-full max-w-md border-yellow-500/50">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Database className="h-12 w-12 text-yellow-500" />
          </div>
          <CardTitle className="text-xl font-semibold">
            Data Error
          </CardTitle>
          <CardDescription>
            Unable to load data. This may be a temporary issue.
          </CardDescription>
          {errorId && (
            <Badge variant="outline" className="w-fit mx-auto mt-2">
              ID: {errorId.slice(-8)}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <Database className="h-4 w-4" />
            <AlertTitle>Data Loading Issue</AlertTitle>
            <AlertDescription className="text-sm">
              We're having trouble accessing the data. Please try again.
            </AlertDescription>
          </Alert>
          
          <div className="flex gap-2">
            {canRetry && onRetry && (
              <Button onClick={onRetry} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            )}
            {onReload && (
              <Button variant="outline" onClick={onReload} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Compact error fallback for smaller UI sections
 */
export function CompactErrorFallback({
  error,
  onRetry,
  canRetry = true,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={`p-4 border border-destructive/50 rounded-lg bg-destructive/5 ${className || ''}`}>
      <div className="flex items-center space-x-3">
        <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-destructive">
            Error occurred
          </div>
          {error && (
            <div className="text-xs text-muted-foreground truncate">
              {error.message}
            </div>
          )}
        </div>
        {canRetry && onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RefreshCw className="h-3 w-3" />
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Inline error fallback for form fields and small components
 */
export function InlineErrorFallback({
  error,
  onRetry,
  canRetry = true,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={`flex items-center space-x-2 text-sm ${className || ''}`}>
      <AlertTriangle className="h-4 w-4 text-destructive flex-shrink-0" />
      <span className="text-destructive flex-1">
        {error?.message || 'An error occurred'}
      </span>
      {canRetry && onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-primary hover:text-primary/80 underline"
        >
          Retry
        </button>
      )}
    </div>
  );
}

/**
 * Loading error fallback with skeleton
 */
export function LoadingErrorFallback({
  onRetry,
  canRetry = true,
  className,
}: Omit<ErrorFallbackProps, 'error'>) {
  return (
    <div className={`space-y-3 ${className || ''}`}>
      <div className="animate-pulse">
        <div className="h-4 bg-muted rounded w-3/4"></div>
        <div className="h-4 bg-muted rounded w-1/2 mt-2"></div>
      </div>
      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
        <AlertTriangle className="h-4 w-4" />
        <span>Failed to load content</span>
        {canRetry && onRetry && (
          <button
            onClick={onRetry}
            className="text-primary hover:text-primary/80 underline ml-2"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

// Exports are already handled by individual export statements above