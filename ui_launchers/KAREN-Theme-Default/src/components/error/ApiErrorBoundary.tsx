// ui_launchers/KAREN-Theme-Default/src/components/error/ApiErrorBoundary.tsx
/**
 * API Error Boundary - Specialized error boundary for API-related errors
 * Provides intelligent retry logic and graceful degradation for API failures
 */
"use client";

import React, { Component, ReactNode } from "react";
import {
  AlertTriangle,
  RefreshCw,
  Wifi,
  WifiOff,
  Clock,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface ApiErrorBoundaryProps {
  children: ReactNode;
  fallback?: (
    error: ApiError,
    retry: () => void,
    isRetrying: boolean
  ) => ReactNode;
  onError?: (error: ApiError, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number; // default 3
  retryDelay?: number; // base delay ms, default 2000
  enableOfflineMode?: boolean; // show offline hint, default false
  showNetworkStatus?: boolean; // show online/offline chip, default false
  autoRetry?: boolean; // default false
  criticalEndpoints?: string[]; // severity boost
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
  name: string; // keep explicit for error code display
}

export class ApiErrorBoundary extends Component<
  ApiErrorBoundaryProps,
  ApiErrorBoundaryState
> {
  private retryTimeouts: Array<ReturnType<typeof setTimeout>> = [];
  private networkStatusInterval: ReturnType<typeof setInterval> | null = null;

  constructor(props: ApiErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      isRetrying: false,
      isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
      lastRetryTime: 0,
      nextRetryTime: 0,
      autoRetryEnabled: props.autoRetry ?? false,
    };
  }

  // Only transition to error UI for API-related failures
  static getDerivedStateFromError(error: Error): Partial<ApiErrorBoundaryState> {
    if (ApiErrorBoundary.isApiError(error)) {
      return { hasError: true, error: error as ApiError };
    }
    // Non-API errors should bubble to a higher boundary
    // Return empty state here; rethrow happens in componentDidCatch
    return {};
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (!ApiErrorBoundary.isApiError(error)) {
      // Re-throw to be handled by the nearest non-API boundary
      throw error;
    }
    this.setState({ errorInfo });
    this.props.onError?.(error as ApiError, errorInfo);

    // Begin auto-retry if allowed and advisable
    if (this.state.autoRetryEnabled && this.shouldAutoRetry(error as ApiError)) {
      this.scheduleAutoRetry();
    }
  }

  componentDidMount() {
    if (this.props.showNetworkStatus && typeof window !== "undefined") {
      this.setupNetworkMonitoring();
    }
  }

  componentWillUnmount() {
    this.retryTimeouts.forEach(clearTimeout);
    this.retryTimeouts = [];
    if (this.networkStatusInterval) {
      clearInterval(this.networkStatusInterval);
    }
    if (typeof window !== "undefined") {
      window.removeEventListener("online", this.handleOnline);
      window.removeEventListener("offline", this.handleOffline);
    }
  }

  /* ------------------------- Classification helpers ------------------------ */

  private static isApiError(error: Error): boolean {
    const e = error as Partial<ApiError> & { message?: string; name?: string };
    const msg = (e.message ?? "").toLowerCase();
    return (
      e.name === "ApiError" ||
      e.name === "EnhancedApiError" ||
      msg.includes("fetch") ||
      msg.includes("network") ||
      msg.includes("cors") ||
      msg.includes("timeout") ||
      (e as unknown).status !== undefined ||
      (e as unknown).endpoint !== undefined
    );
  }

  private getErrorSeverity(
    error: ApiError
  ): "low" | "medium" | "high" | "critical" {
    const criticalEndpoints =
      this.props.criticalEndpoints ?? ["/api/auth", "/api/health"];
    if (
      error.endpoint &&
      criticalEndpoints.some((ep) => error.endpoint!.includes(ep))
    ) {
      return "critical";
    }
    if (error.status && (error.status >= 500 || error.status === 401 || error.status === 403)) {
      return "high";
    }
    if (error.status && error.status >= 400) {
      return "medium";
    }
    if (error.isNetworkError || error.isTimeoutError) {
      return "low";
    }
    return "medium";
  }

  private getSeverityColor(severity: "low" | "medium" | "high" | "critical") {
    switch (severity) {
      case "low":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "medium":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      case "critical":
        return "bg-red-200 text-red-900 border-red-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  }

  /* ----------------------------- Network status ---------------------------- */

  private setupNetworkMonitoring(): void {
    window.addEventListener("online", this.handleOnline);
    window.addEventListener("offline", this.handleOffline);
    this.networkStatusInterval = setInterval(() => {
      const isOnline = navigator.onLine;
      if (isOnline !== this.state.isOnline) {
        this.setState({ isOnline });
      }
    }, 5000);
  }

  private handleOnline = (): void => {
    this.setState({ isOnline: true });
    if (
      this.state.hasError &&
      this.state.autoRetryEnabled &&
      !this.state.isRetrying
    ) {
      this.handleRetry();
    }
  };

  private handleOffline = (): void => {
    this.setState({ isOnline: false });
  };

  /* ------------------------------ Retry logic ------------------------------ */

  private shouldAutoRetry(error: ApiError): boolean {
    const maxRetries = this.props.maxRetries ?? 3;
    if (this.state.retryCount >= maxRetries) return false;

    if (error.isNetworkError || error.isTimeoutError) return true;

    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    if (error.status && retryableStatuses.includes(error.status)) return true;

    return false;
  }

  private calculateRetryDelay(): number {
    const baseDelay = this.props.retryDelay ?? 2000;
    const retryCount = this.state.retryCount;
    const exponentialDelay = baseDelay * Math.pow(2, retryCount); // 2s, 4s, 8s...
    const jitter = Math.random() * 1000; // 0–1s jitter
    const maxDelay = 30_000;
    return Math.min(exponentialDelay + jitter, maxDelay);
  }

  private scheduleAutoRetry(): void {
    const delay = this.calculateRetryDelay();
    const now = Date.now();
    const nextRetryTime = now + delay;

    this.setState({
      nextRetryTime,
      lastRetryTime: now,
      isRetrying: true,
    });

    const timeout = setTimeout(() => {
      this.handleRetry();
    }, delay);

    this.retryTimeouts.push(timeout);
  }

  private handleRetry = (): void => {
    const maxRetries = this.props.maxRetries ?? 3;
    if (this.state.retryCount >= maxRetries) {
      this.setState({ isRetrying: false });
      return;
    }

    // Reset visual error UI and increment attempt counter
    this.setState((prev) => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prev.retryCount + 1,
      isRetrying: false,
      lastRetryTime: Date.now(),
      nextRetryTime: 0,
    }));
  };

  private handleManualRetry = (): void => {
    this.retryTimeouts.forEach(clearTimeout);
    this.retryTimeouts = [];
    this.handleRetry();
  };

  private handleToggleAutoRetry = (): void => {
    this.setState((prev) => ({
      autoRetryEnabled: !prev.autoRetryEnabled,
    }));
  };

  private getRetryProgress(): number {
    if (!this.state.isRetrying || this.state.nextRetryTime === 0) return 0;
    const now = Date.now();
    const totalTime = this.state.nextRetryTime - this.state.lastRetryTime;
    if (totalTime <= 0) return 0;
    const elapsed = now - this.state.lastRetryTime;
    return Math.min((elapsed / totalTime) * 100, 100);
    }

  /* --------------------------------- Render -------------------------------- */

  render() {
    const { children, fallback, maxRetries = 3 } = this.props;
    const { hasError, error, retryCount, isRetrying, isOnline, autoRetryEnabled } =
      this.state;

    if (!hasError) return children;
    if (!error) return children;

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
              <AlertTriangle className="h-8 w-8 text-destructive" aria-hidden />
              <div className="flex-1">
                <CardTitle className="text-xl">API Connection Error</CardTitle>
                <CardDescription className="mt-1 flex items-center space-x-2">
                  <span>Unable to communicate with the server</span>
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {severity.toUpperCase()}
                  </Badge>
                  {this.props.showNetworkStatus && (
                    <div className="flex items-center space-x-1">
                      {isOnline ? (
                        <Wifi className="h-3 w-3 text-green-500" aria-hidden />
                      ) : (
                        <WifiOff className="h-3 w-3 text-red-500" aria-hidden />
                      )}
                      <span className="text-xs sm:text-sm md:text-base">
                        {isOnline ? "Online" : "Offline"}
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
              <AlertCircle className="h-4 w-4" aria-hidden />
              <AlertTitle>Error Details</AlertTitle>
              <AlertDescription className="mt-2 space-y-1">
                <p className="font-medium">{error.message}</p>
                {error.endpoint && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Endpoint:{" "}
                    <code className="rounded bg-muted px-1">{error.endpoint}</code>
                  </p>
                )}
                {error.status !== undefined && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Status: {error.status}{" "}
                    {error.statusText ? `(${error.statusText})` : ""}
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
                    <Clock className="h-4 w-4" aria-hidden />
                    <span>Auto-retrying…</span>
                  </span>
                  <span>{Math.round(retryProgress)}%</span>
                </div>
                <Progress value={retryProgress} className="h-2" />
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              {canRetry && !isRetrying && (
                <Button
                  onClick={this.handleManualRetry}
                  className="flex items-center gap-2"
                  aria-label="Retry request"
                >
                  <RefreshCw className="h-4 w-4" aria-hidden />
                  Retry
                </Button>
              )}
              {canRetry && (
                <Button
                  variant="outline"
                  onClick={this.handleToggleAutoRetry}
                  className="flex items-center gap-2"
                  aria-pressed={autoRetryEnabled}
                  aria-label={autoRetryEnabled ? "Disable auto-retry" : "Enable auto-retry"}
                >
                  {autoRetryEnabled ? "Disable" : "Enable"} Auto-retry
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                className="flex items-center gap-2"
                aria-label="Reload page"
              >
                <RefreshCw className="h-4 w-4" aria-hidden />
                Reload Page
              </Button>
            </div>

            {/* Offline Mode Notice */}
            {!isOnline && this.props.enableOfflineMode && (
              <Alert className="border-yellow-200 bg-yellow-50">
                <WifiOff className="h-4 w-4" aria-hidden />
                <AlertTitle>Offline Mode</AlertTitle>
                <AlertDescription>
                  You’re currently offline. Some features may be limited. The app
                  will automatically retry when your connection is restored.
                </AlertDescription>
              </Alert>
            )}

            {/* Max Retries Reached */}
            {retryCount >= maxRetries && (
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4" aria-hidden />
                <AlertTitle>Maximum Retries Reached</AlertTitle>
                <AlertDescription>
                  Unable to establish connection after {maxRetries} attempts. Please
                  check your network connection or try reloading the page.
                </AlertDescription>
              </Alert>
            )}

            {/* Help Text */}
            <div className="border-t pt-2 text-center text-sm text-muted-foreground md:text-base lg:text-lg">
              <p>
                Contact support with error code:{" "}
                <code className="rounded bg-muted px-1">{error.name}</code>
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
  Wrapped: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ApiErrorBoundaryProps, "children">
) {
  return function WrappedComponent(props: P) {
    return (
      <ApiErrorBoundary {...errorBoundaryProps}>
        <Wrapped {...props} />
      </ApiErrorBoundary>
    );
  };
}

export default ApiErrorBoundary;
