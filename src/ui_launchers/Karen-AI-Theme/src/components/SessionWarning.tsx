"use client";

import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Clock, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';

interface SessionWarningProps {
  onExtendSession?: () => void;
}

export default function SessionWarning({ onExtendSession }: SessionWarningProps) {
  const [showWarning, setShowWarning] = useState(false);
  const [timeUntilExpiry, setTimeUntilExpiry] = useState<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  useEffect(() => {
    const handleSessionWarning = (event: CustomEvent) => {
      setShowWarning(true);
      setTimeUntilExpiry(event.detail.timeUntilExpiry);
    };

    const checkSessionStatus = async () => {
      try {
        const status = await apiClient.checkSessionStatus();
        if (status.shouldShowWarning && status.timeUntilExpiry) {
          setShowWarning(true);
          setTimeUntilExpiry(status.timeUntilExpiry);
        } else if (!status.isValid) {
          // Session is invalid, redirect will be handled by API client
          setShowWarning(false);
        }
      } catch (error) {
        console.error('Failed to check session status:', error);
      }
    };

    // Listen for session warning events
    window.addEventListener('sessionWarning', handleSessionWarning as EventListener);

    // Check session status on mount
    checkSessionStatus();

    // Check session status every 5 minutes
    const interval = setInterval(checkSessionStatus, 5 * 60 * 1000);

    return () => {
      window.removeEventListener('sessionWarning', handleSessionWarning as EventListener);
      clearInterval(interval);
    };
  }, []);

  const formatTimeRemaining = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const handleExtendSession = async () => {
    setIsRefreshing(true);
    setRefreshError(null);
    try {
      // This will trigger a proactive refresh
      await apiClient.get('/api/auth/me');
      setShowWarning(false);
      setTimeUntilExpiry(null);
      onExtendSession?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to extend session right now.';
      setRefreshError(message);
    } finally {
      setIsRefreshing(false);
    }
  };


  const refreshErrorHint = useMemo(() => {
    if (!refreshError) return null;
    if (refreshError.includes('503') || refreshError.toLowerCase().includes('database unavailable')) {
      return 'Session service is temporarily unavailable. Your current session remains active until expiry.';
    }
    return refreshError;
  }, [refreshError]);

  if (!showWarning || timeUntilExpiry === null) {
    return null;
  }

  return (
    <Alert className="border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/50">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertDescription className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-amber-600" />
          <span className="text-amber-800 dark:text-amber-200">
            Your session will expire in {formatTimeRemaining(timeUntilExpiry)}
          </span>
        </div>
        <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleExtendSession}
          disabled={isRefreshing}
          className="border-amber-300 text-amber-700 hover:bg-amber-100 dark:border-amber-700 dark:text-amber-300 dark:hover:bg-amber-900"
        >
          {isRefreshing ? (
            <RefreshCw className="mr-2 h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-3 w-3" />
          )}
          Extend Session
        </Button>
        </div>
      </AlertDescription>
      {refreshErrorHint ? <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{refreshErrorHint}</p> : null}
    </Alert>
  );
}