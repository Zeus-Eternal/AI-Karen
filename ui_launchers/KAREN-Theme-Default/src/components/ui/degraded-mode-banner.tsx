"use client";

import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface DegradedModeBannerProps {
  /** Whether the banner is visible */
  show?: boolean;
  /** Custom message to display */
  message?: string;
  /** Custom title for the banner */
  title?: string;
  /** Whether the banner can be dismissed */
  dismissible?: boolean;
  /** Callback when banner is dismissed */
  onDismiss?: () => void;
  /** Additional CSS classes */
  className?: string;
  /** Severity level */
  severity?: 'warning' | 'error' | 'info';
}

export default function DegradedModeBanner({
  show = false,
  message = 'Some features may be unavailable or slower than usual. We are working to restore full functionality.',
  title = 'System in Degraded Mode',
  dismissible = true,
  onDismiss,
  className,
  severity = 'warning',
}: DegradedModeBannerProps) {
  if (!show) return null;

  return (
    <Alert
      className={cn(
        'relative',
        severity === 'warning' && 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-600',
        severity === 'error' && 'border-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-600',
        severity === 'info' && 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-600',
        className
      )}
    >
      <AlertTriangle className={cn(
        'h-4 w-4',
        severity === 'warning' && 'text-yellow-600 dark:text-yellow-400',
        severity === 'error' && 'text-red-600 dark:text-red-400',
        severity === 'info' && 'text-blue-600 dark:text-blue-400'
      )} />
      <AlertTitle className="font-semibold">{title}</AlertTitle>
      <AlertDescription>{message}</AlertDescription>

      {dismissible && onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-6 w-6 p-0"
          onClick={onDismiss}
          aria-label="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </Alert>
  );
}

export { DegradedModeBanner };
