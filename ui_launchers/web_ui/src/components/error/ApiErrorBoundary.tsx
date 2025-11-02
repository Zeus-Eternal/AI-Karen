/**
 * API Error Boundary - Specialized error boundary for API-related errors
 * Provides intelligent retry logic and graceful degradation for API failures
 */
'use client';
import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Wifi, WifiOff, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
interface ApiErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: ApiError, retry: () => void, isRetrying: boolean) => ReactNode;
  onError?: (error: ApiError, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number;
  retryDelay?: number;
  enableOfflineMode?: boolean;
  showNetworkStatus?: boolean;
  autoRetry?: boolean;
  criticalEndpoints?: string[];
}
interface ApiErrorBoundaryState {
  hasError: boolean;
  error: ApiError | null;
  errorInfo: React.ErrorInfo | null;
  retryCount: number;
  isRetrying: boolean;
  isOnline: boolean;
  lastRetryTime: number;
  nextRetryTime: number;
  autoRetryEnabled: boolean;
}
interface ApiError extends Error {
  status?: number;
  statusText?: string;
  endpoint?: string;
  responseTime?: number;
  isNetworkError?: boolean;
  isCorsError?: boolean;
  isTimeoutError?: boolean;
  originalError?: Error;
}
export class ApiErrorBoundary extends Component<ApiErrorBoundaryProps, ApiErrorBoundaryState> {
  private retryTimeouts: NodeJS.Timeout[] = [];
  private networkStatusInterval: NodeJS.Timeout | null = null;
  private enhancedApiClient = enhancedApiClient;
  constructor(props: ApiErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      isRetrying: false,
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      lastRetryTime: 0,
      nextRetryTime: 0,
      autoRetryEnabled: props.autoRetry ?? false,
    };
  }
  static getDerivedStateFromError(error: Error): Partial<ApiErrorBoundaryState> {
    // Only handle API-related errors
    if (ApiErrorBoundary.isApiError(error)) {
      return {
        hasError: true,
        error: error as ApiError,
      };
    }
    // Let other error boundaries handle non-API errors
    throw error;
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (!ApiErrorBoundary.isApiError(error)) {
      // Re-throw non-API errors
      throw error;
    }
    this.setState({ errorInfo });
    // Call the onError callback if provided
    this.props.onError?.(error as ApiError, errorInfo);
    // Start auto-retry if enabled and appropriate
    if (this.state.autoRetryEnabled && this.shouldAutoRetry(error as ApiError)) {
      this.scheduleAutoRetry();
    }
  }
  componentDidMount() {
    // Set up network status monitoring
    if (this.props.showNetworkStatus && typeof window !== 'undefined') {
      this.setupNetworkMonitoring();
    }
  }
  componentWillUnmount() {
    // Clear all timeouts and intervals
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
    if (this.networkStatusInterval) {
      clearInterval(this.networkStatusInterval);
    }
    // Remove network event listeners
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }
  }
  private static isApiError(error: Error): boolean {
    return (
      error.name === 'ApiError' ||
      error.name === 'EnhancedApiError' ||
      error.message.includes('fetch') ||
      error.message.includes('Network') ||
      error.message.includes('CORS') ||
      error.message.includes('timeout') ||
      (error as any).status !== undefined ||
      (error as any).endpoint !== undefined
    );
  }
  private setupNetworkMonitoring(): void {
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
    // Periodic network check
    this.networkStatusInterval = setInterval(() => {
      const isOnline = navigator.onLine;
      if (isOnline !== this.state.isOnline) {
        this.setState({ isOnline });
      }
    }, 5000);
  }
  private handleOnline = (): void => {
    this.setState({ isOnline: true });
    // Auto-retry if we have an error and auto-retry is enabled
    if (this.state.hasError && this.state.autoRetryEnabled && !this.state.isRetrying) {
      this.handleRetry();
    }
  };
  private handleOffline = (): void => {
    this.setState({ isOnline: false });
  };
  private shouldAutoRetry(error: ApiError): boolean {
    const maxRetries = this.props.maxRetries ?? 3;
    // Don't auto-retry if we've exceeded max retries
    if (this.state.retryCount >= maxRetries) {
      return false;
    }
    // Auto-retry for network errors
    if (error.isNetworkError || error.isTimeoutError) {
      return true;
    }
    // Auto-retry for specific status codes
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    if (error.status && retryableStatuses.includes(error.status)) {
      return true;
    }
    return false;
  }
  private scheduleAutoRetry(): void {
    const delay = this.calculateRetryDelay();
    const nextRetryTime = Date.now() + delay;
    this.setState({ 
      nextRetryTime,
      isRetrying: true,
    });
    const timeout = setTimeout(() => {
      this.handleRetry();
    }, delay);
    this.retryTimeouts.push(timeout);
  }
  private calculateRetryDelay(): number {
    const baseDelay = this.props.retryDelay ?? 2000;
    const retryCount = this.state.retryCount;
    // Exponential backoff with jitter
    const exponentialDelay = baseDelay * Math.pow(2, retryCount);
    const jitter = Math.random() * 1000; // 0-1s jitter
    const maxDelay = 30000; // 30 seconds max
    return Math.min(exponentialDelay + jitter, maxDelay);
  }
  private handleRetry = (): void => {
    const maxRetries = this.props.maxRetries ?? 3;
    if (this.state.retryCount >= maxRetries) {
      this.setState({ isRetrying: false });
      return;
    }
    console.log(`ApiErrorBoundary: Retrying... (attempt ${this.state.retryCount + 1}/${maxRetries})`);
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1,
      isRetrying: false,
      lastRetryTime: Date.now(),
      nextRetryTime: 0,
    }));
  };
  private handleManualRetry = (): void => {
    // Clear any pending auto-retries
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
    this.retryTimeouts = [];
    this.handleRetry();
  };
  private handleToggleAutoRetry = (): void => {
    this.setState(prevState => ({
      autoRetryEnabled: !prevState.autoRetryEnabled,
    }));
  };
  private getErrorSeverity(error: ApiError): 'low' | 'medium' | 'high' | 'critical' {
    // Critical endpoints
    const criticalEndpoints = this.props.criticalEndpoints ?? ['/api/auth', '/api/health'];
    if (error.endpoint && criticalEndpoints.some(ep => error.endpoint!.includes(ep))) {
      return 'critical';
    }
    // High severity for auth and server errors
    if (error.status && (error.status >= 500 || error.status === 401 || error.status === 403)) {
      return 'high';
    }
    // Medium severity for client errors
    if (error.status && error.status >= 400) {
      return 'medium';
    }
    // Low severity for network issues (usually temporary)
    if (error.isNetworkError || error.isTimeoutError) {
      return 'low';
    }
    return 'medium';
  }
  private getSeverityColor(severity: 'low' | 'medium' | 'high' | 'critical'): string {
    switch (severity) {
      case 'low': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'medium': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'critical': return 'bg-red-200 text-red-900 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  }
  private getRetryProgress(): number {
    if (!this.state.isRetrying || this.state.nextRetryTime === 0) {
      return 0;
    }
    const now = Date.now();
    const totalTime = this.state.nextRetryTime - this.state.lastRetryTime;
    const elapsed = now - this.state.lastRetryTime;
    return Math.min((elapsed / totalTime) * 100, 100);
  }
  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }
    const { error, retryCount, isRetrying, isOnline, autoRetryEnabled } = this.state;
    const { fallback, maxRetries = 3 } = this.props;
    if (!error) {
      return this.props.children;
    }
    // Use custom fallback if provided
    if (fallback) {
      return fallback(error, this.handleManualRetry, isRetrying);
    }
    const severity = this.getErrorSeverity(error);
    const canRetry = retryCount < maxRetries;
    const retryProgress = this.getRetryProgress();
    return (
      <div className="min-h-[400px] flex items-center justify-center p-4 sm:p-4 md:p-6">
        <Card className={`w-full max-w-2xl border-2 ${this.getSeverityColor(severity)}`}>
          <CardHeader>
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-8 w-8 text-destructive sm:w-auto md:w-full" />
              <div className="flex-1">
                <CardTitle className="text-xl">API Connection Error</CardTitle>
                <CardDescription className="flex items-center space-x-2 mt-1">
                  <span>Unable to communicate with the server</span>
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {severity.toUpperCase()}
                  </Badge>
                  {this.props.showNetworkStatus && (
                    <div className="flex items-center space-x-1">
                      {isOnline ? (
                        <Wifi className="h-3 w-3 text-green-500 sm:w-auto md:w-full" />
                      ) : (
                        <WifiOff className="h-3 w-3 text-red-500 sm:w-auto md:w-full" />
                      )}
                      <span className="text-xs sm:text-sm md:text-base">
                        {isOnline ? 'Online' : 'Offline'}
                      </span>
                    </div>
                  )}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Error Details */}
            <Alert>
              <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
              <AlertTitle>Error Details</AlertTitle>
              <AlertDescription className="mt-2 space-y-1">
                <p className="font-medium">{error.message}</p>
                {error.endpoint && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Endpoint: <code className="bg-muted px-1 rounded">{error.endpoint}</code>
                  </p>
                )}
                {error.status && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Status: {error.status} {error.statusText && `(${error.statusText})`}
                  </p>
                )}
                {retryCount > 0 && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Retry attempts: {retryCount} of {maxRetries}
                  </p>
                )}
              </AlertDescription>
            </Alert>
            {/* Auto-retry Progress */}
            {isRetrying && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                  <span className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 sm:w-auto md:w-full" />
                    <span>Auto-retrying...</span>
                  </span>
                  <span>{Math.round(retryProgress)}%</span>
                </div>
                <Progress value={retryProgress} className="h-2" />
              </div>
            )}
            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              {canRetry && !isRetrying && (
                <button 
                  onClick={this.handleManualRetry} 
                  className="flex items-center gap-2"
                 aria-label="Button">
                  <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                  Retry Now
                </Button>
              )}
              {canRetry && (
                <button
                  variant="outline"
                  onClick={this.handleToggleAutoRetry}
                  className="flex items-center gap-2"
                 aria-label="Button">
                  {autoRetryEnabled ? 'Disable' : 'Enable'} Auto-retry
                </Button>
              )}
              <button
                variant="outline"
                onClick={() = aria-label="Button"> window.location.reload()}
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                Reload Page
              </Button>
            </div>
            {/* Offline Mode Notice */}
            {!isOnline && this.props.enableOfflineMode && (
              <Alert className="bg-yellow-50 border-yellow-200">
                <WifiOff className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertTitle>Offline Mode</AlertTitle>
                <AlertDescription>
                  You're currently offline. Some features may be limited. 
                  The app will automatically retry when your connection is restored.
                </AlertDescription>
              </Alert>
            )}
            {/* Max Retries Reached */}
            {retryCount >= maxRetries && (
              <Alert className="bg-red-50 border-red-200">
                <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertTitle>Maximum Retries Reached</AlertTitle>
                <AlertDescription>
                  Unable to establish connection after {maxRetries} attempts. 
                  Please check your network connection or try reloading the page.
                </AlertDescription>
              </Alert>
            )}
            {/* Help Text */}
            <div className="text-center text-sm text-muted-foreground pt-2 border-t md:text-base lg:text-lg">
              <p>
                If this problem persists, please check your network connection 
                or contact support with error code: <code className="bg-muted px-1 rounded">{error.name}</code>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
}
/**
 * Higher-order component to wrap components with API error boundary
 */
export function withApiErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ApiErrorBoundaryProps, 'children'>
) {
  return function WrappedComponent(props: P) {
    return (
      <ApiErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </ApiErrorBoundary>
    );
  };
}
export default ApiErrorBoundary;
