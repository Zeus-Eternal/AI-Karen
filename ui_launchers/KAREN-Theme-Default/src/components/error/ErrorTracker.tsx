"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, XCircle, AlertTriangle, Info, Trash2, Eye, EyeOff } from 'lucide-react';

interface TrackedError {
  id: string;
  timestamp: number;
  message: string;
  stack?: string;
  boundary: string;
  level: 'info' | 'warning' | 'error' | 'critical';
}

interface ErrorTrackerProps {
  maxErrors?: number;
  autoCollapse?: boolean;
  persistErrors?: boolean;
  onErrorTracked?: (error: TrackedError) => void;
}

const ErrorTracker: React.FC<ErrorTrackerProps> = ({
  maxErrors = 50,
  autoCollapse = false,
  persistErrors = true,
  onErrorTracked
}) => {
  const [errors, setErrors] = useState<TrackedError[]>([]);
  const [isVisible, setIsVisible] = useState(!autoCollapse);
  const [filter, setFilter] = useState<string>('all');

  // Load persisted errors on mount
  useEffect(() => {
    if (persistErrors && typeof window !== 'undefined') {
      const stored = localStorage.getItem('kari:tracked-errors');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setErrors(parsed);
        } catch (e) {
          console.error('Failed to parse stored errors:', e);
        }
      }
    }
  }, [persistErrors]);

  // Persist errors to localStorage
  useEffect(() => {
    if (persistErrors && typeof window !== 'undefined' && errors.length > 0) {
      localStorage.setItem('kari:tracked-errors', JSON.stringify(errors.slice(-maxErrors)));
    }
  }, [errors, maxErrors, persistErrors]);

  // Listen for error events
  const handleError = useCallback((event: CustomEvent) => {
    const { boundary, message, stack } = event.detail;

    const newError: TrackedError = {
      id: `error_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      timestamp: Date.now(),
      message: message || 'Unknown error',
      stack: stack || undefined,
      boundary: boundary || 'Unknown',
      level: determineErrorLevel(message, boundary)
    };

    setErrors(prev => {
      const updated = [...prev, newError].slice(-maxErrors);
      return updated;
    });

    onErrorTracked?.(newError);
  }, [maxErrors, onErrorTracked]);

  // Determine error level based on message and boundary
  const determineErrorLevel = (message: string, boundary: string): TrackedError['level'] => {
    const lowerMessage = message?.toLowerCase() || '';

    if (lowerMessage.includes('critical') || lowerMessage.includes('fatal')) {
      return 'critical';
    }
    if (lowerMessage.includes('network') || lowerMessage.includes('timeout') || boundary.includes('Api')) {
      return 'error';
    }
    if (lowerMessage.includes('warning') || lowerMessage.includes('deprecated')) {
      return 'warning';
    }
    return 'info';
  };

  // Set up event listener
  useEffect(() => {
    const listener = (e: Event) => handleError(e as CustomEvent);
    window.addEventListener('kari:error', listener);

    return () => {
      window.removeEventListener('kari:error', listener);
    };
  }, [handleError]);

  const clearErrors = () => {
    setErrors([]);
    if (persistErrors && typeof window !== 'undefined') {
      localStorage.removeItem('kari:tracked-errors');
    }
  };

  const getErrorIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-orange-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-600" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case 'critical':
        return 'destructive';
      case 'error':
        return 'destructive';
      case 'warning':
        return 'secondary';
      case 'info':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const filteredErrors = filter === 'all'
    ? errors
    : errors.filter(e => e.level === filter);

  const errorCounts = {
    all: errors.length,
    critical: errors.filter(e => e.level === 'critical').length,
    error: errors.filter(e => e.level === 'error').length,
    warning: errors.filter(e => e.level === 'warning').length,
    info: errors.filter(e => e.level === 'info').length
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Error Tracker
            {errors.length > 0 && (
              <Badge variant="secondary">{errors.length}</Badge>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsVisible(!isVisible)}
            >
              {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearErrors}
              disabled={errors.length === 0}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          Real-time error tracking across all error boundaries
        </CardDescription>
      </CardHeader>

      {isVisible && (
        <CardContent>
          {/* Filter Tabs */}
          <div className="flex gap-2 mb-4 flex-wrap">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              All ({errorCounts.all})
            </Button>
            <Button
              variant={filter === 'critical' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('critical')}
              className={filter === 'critical' ? 'bg-red-600' : ''}
            >
              Critical ({errorCounts.critical})
            </Button>
            <Button
              variant={filter === 'error' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('error')}
            >
              Error ({errorCounts.error})
            </Button>
            <Button
              variant={filter === 'warning' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('warning')}
            >
              Warning ({errorCounts.warning})
            </Button>
            <Button
              variant={filter === 'info' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('info')}
            >
              Info ({errorCounts.info})
            </Button>
          </div>

          {/* Error List */}
          <ScrollArea className="h-[400px] pr-4">
            {filteredErrors.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-muted-foreground">
                <p>No errors tracked yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredErrors.slice().reverse().map((error) => (
                  <div
                    key={error.id}
                    className="flex items-start gap-3 p-3 border rounded-lg hover:bg-muted/50"
                  >
                    <div className="mt-0.5">{getErrorIcon(error.level)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="flex-1">
                          <div className="font-medium text-sm break-words">
                            {error.message}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {error.boundary} • {new Date(error.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Badge variant={getLevelBadgeVariant(error.level)} className="shrink-0">
                          {error.level.toUpperCase()}
                        </Badge>
                      </div>
                      {error.stack && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                            Stack trace
                          </summary>
                          <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                            {error.stack}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  );
};

export default ErrorTracker;
export { ErrorTracker };
export type { ErrorTrackerProps, TrackedError };
