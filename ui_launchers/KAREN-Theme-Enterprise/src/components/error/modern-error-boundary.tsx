// ui_launchers/KAREN-Theme-Default/src/components/error/modern-error-boundary.tsx
"use client";

import React, { Component, ReactNode, ErrorInfo } from "react";
import {
  AlertTriangle,
  RefreshCw,
  Home,
  Bug,
  ExternalLink,
  Clock,
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

  interface WindowWithGtag extends Window {
    gtag?: (...args: unknown[]) => void;
  }

  interface ModernErrorBoundaryProps {
  children: ReactNode;
  /** Custom fallback renderer; if provided, this takes precedence. */
  fallback?: (error: Error, errorInfo: ErrorInfo, retry: () => void) => ReactNode;
  /** Called synchronously in componentDidCatch. */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Maximum auto/manual retry attempts before disabling Retry. */
  maxRetries?: number;
  /** Delay (ms) before auto-retry fires. */
  retryDelay?: number;
  /** Logical section id (e.g., "chat-right-panel") for telemetry. */
  section?: string;
  /** Enables auto-retry countdown/progress after a crash. */
  enableAutoRetry?: boolean;
  /** Shows the “Show Technical Details” toggle by default (also always on in dev). */
  showTechnicalDetails?: boolean;
  /** Enables client-side reporting hook (e.g., GA/Sentry bridge). */
  enableErrorReporting?: boolean;
  /** Optional classes on the outer wrapper. */
  className?: string;
}

interface ModernErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  showDetails: boolean;
  retryProgress: number; // 0..100
}

export class ModernErrorBoundary extends Component<
  ModernErrorBoundaryProps,
  ModernErrorBoundaryState
> {
  static defaultProps: Required<
    Pick<
      ModernErrorBoundaryProps,
      "maxRetries" | "retryDelay" | "enableAutoRetry" | "showTechnicalDetails" | "enableErrorReporting"
    >
  > = {
    maxRetries: 3,
    retryDelay: 2000,
    enableAutoRetry: false,
    showTechnicalDetails: false,
    enableErrorReporting: false,
  };

  private retryTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private progressIntervalId: ReturnType<typeof setInterval> | null = null;

  constructor(props: ModernErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRetrying: false,
      showDetails: false,
      retryProgress: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ModernErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `err-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Store component stack
    this.setState({ errorInfo });
    // Call consumer hook
    this.props.onError?.(error, errorInfo);
    // Fire-and-forget telemetry (safe; no await)
    this.reportError(error, errorInfo);
    // Schedule auto-retry if enabled
    if (
      this.props.enableAutoRetry &&
      this.state.retryCount < (this.props.maxRetries ?? 3)
    ) {
      this.scheduleRetry();
    }
  }

  componentWillUnmount() {
    this.clearRetryTimeout();
    this.clearProgressInterval();
  }

  /* ----------------------------- Timers ----------------------------- */

  private clearRetryTimeout = () => {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
      this.retryTimeoutId = null;
    }
  };

  private clearProgressInterval = () => {
    if (this.progressIntervalId) {
      clearInterval(this.progressIntervalId);
      this.progressIntervalId = null;
    }
  };

  private scheduleRetry = () => {
    const delay = this.props.retryDelay ?? 2000;
    this.setState({ isRetrying: true, retryProgress: 0 });

    // Progress bar updates every 100ms
    const tickMs = 100;
    const step = (100 * tickMs) / delay;

    this.progressIntervalId = setInterval(() => {
      this.setState((prev) => {
        const next = Math.min(prev.retryProgress + step, 100);
        return { retryProgress: next };
      });
    }, tickMs);

    this.retryTimeoutId = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };

  /* --------------------------- Telemetry ---------------------------- */

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    if (!this.props.enableErrorReporting) return;

    try {
      const payload = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        section: this.props.section ?? "any",
        timestamp: new Date().toISOString(),
        url: typeof window !== "undefined" ? window.location.href : undefined,
        userAgent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
        errorId: this.state.errorId,
        retryCount: this.state.retryCount,
      };

      // Example GA bridge (non-blocking, guarded)
      if (typeof window !== "undefined") {
        const win = window as WindowWithGtag;
        if (typeof win.gtag === "function") {
          win.gtag("event", "exception", {
            description: `${payload.section}: ${payload.message}`,
            fatal: false,
            error_id: payload.errorId,
            retry_count: payload.retryCount,
          });
        }
      }

      // Hook for Sentry or custom service
      // e.g., Sentry.captureException(error, { extra: payload });
      // or fetch('/api/telemetry/error', { method: 'POST', body: JSON.stringify(payload) })
      // For now, keep it quiet unless in dev:
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.debug("[ModernErrorBoundary] error payload", payload);
      }
    } catch {
      // Swallow telemetry errors (never throw from reporter)
    }
  };

  /* ----------------------------- Actions ---------------------------- */

  private handleRetry = () => {
    this.clearRetryTimeout();
    this.clearProgressInterval();
    const maxRetries = this.props.maxRetries ?? 3;

    if (this.state.retryCount < maxRetries) {
      // Reset error state and increment retry counter.
      this.setState((prev) => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prev.retryCount + 1,
        isRetrying: false,
        showDetails: false,
        retryProgress: 0,
      }));
    } else {
      // Exhausted; stop auto-retrying and keep error visible.
      this.setState({ isRetrying: false, retryProgress: 0 });
    }
  };

  private handleManualRetry = () => {
    this.clearRetryTimeout();
    this.clearProgressInterval();
    this.handleRetry();
  };

  private handleReload = () => {
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  private handleGoHome = () => {
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  private handleReportBug = () => {
    const { error, errorInfo, errorId, retryCount } = this.state;
    const section = this.props.section ?? "App";
    const subject = encodeURIComponent(`Bug Report: ${section} - ${error?.message ?? "any Error"}`);
    const body = encodeURIComponent(
      [
        "Error Details:",
        `- Section: ${section}`,
        `- Message: ${error?.message ?? "any"}`,
        `- Stack: ${error?.stack ?? "N/A"}`,
        `- Component Stack: ${errorInfo?.componentStack ?? "N/A"}`,
        `- Error ID: ${errorId ?? "N/A"}`,
        `- Retry Count: ${retryCount}`,
        `- URL: ${typeof window !== "undefined" ? window.location.href : "N/A"}`,
        `- Timestamp: ${new Date().toISOString()}`,
        `- User Agent: ${typeof navigator !== "undefined" ? navigator.userAgent : "N/A"}`,
        "",
        "Please describe what you were doing when this error occurred:",
        "[Your description here]",
      ].join("\n")
    );
    const mailtoUrl = `mailto:support@example.com?subject=${subject}&body=${body}`;
    if (typeof window !== "undefined") window.open(mailtoUrl, "_blank");
  };

  private toggleDetails = () => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  /* ------------------------------ View ------------------------------ */

  render() {
    const {
      fallback,
      maxRetries = 3,
      section,
      showTechnicalDetails = false,
      className,
    } = this.props;

    const {
      hasError,
      error,
      errorInfo,
      errorId,
      retryCount,
      isRetrying,
      showDetails,
      retryProgress,
    } = this.state;

    if (!hasError) return this.props.children;

    // Custom fallback wins
    if (fallback && error && errorInfo) {
      return fallback(error, errorInfo, this.handleManualRetry);
    }

    const sectionName =
      section ? section.charAt(0).toUpperCase() + section.slice(1) : "Application";
    const canRetry = retryCount < maxRetries;

    return (
      <div className={`flex items-center justify-center p-4 ${className ?? ""}`}>
        <Card className="w-full max-w-lg border-destructive/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-destructive flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <CardTitle className="text-lg">{sectionName} Error</CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1">
                  <span>Something went wrong in this section</span>
                  {errorId && (
                    <Badge variant="outline" className="text-xs">
                      {errorId.slice(-8)}
                    </Badge>
                  )}
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Error Summary */}
            <Alert>
              <Bug className="h-4 w-4" />
              <AlertTitle>Error Details</AlertTitle>
              <AlertDescription className="mt-2">
                <p className="font-medium text-sm md:text-base">
                  {error?.message || "any error occurred"}
                </p>
                {retryCount > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Retry attempt {retryCount} of {maxRetries}
                  </p>
                )}
              </AlertDescription>
            </Alert>

            {/* Auto-retry Progress */}
            {isRetrying && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>Retrying automatically…</span>
                </div>
                <Progress value={retryProgress} className="h-2" />
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              {canRetry && !isRetrying && (
                <Button
                  onClick={this.handleManualRetry}
                  size="sm"
                  className="flex items-center gap-2"
                  aria-label="Retry"
                >
                  <RefreshCw className="h-4 w-4" />
                  Retry
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={this.handleReload}
                className="flex items-center gap-2"
                aria-label="Reload page"
              >
                <RefreshCw className="h-4 w-4" />
                Reload Page
              </Button>

              {section !== "global" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={this.handleGoHome}
                  className="flex items-center gap-2"
                  aria-label="Go home"
                >
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={this.handleReportBug}
                className="flex items-center gap-2"
                aria-label="Report bug"
              >
                <ExternalLink className="h-4 w-4" />
                Report Bug
              </Button>
            </div>

            {/* Technical Details Toggle */}
            {(showTechnicalDetails || process.env.NODE_ENV === "development") && (
              <div className="pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={this.toggleDetails}
                  className="text-muted-foreground h-8"
                  aria-expanded={showDetails}
                >
                  {showDetails ? "Hide" : "Show"} Technical Details
                </Button>
              </div>
            )}

            {/* Technical Details */}
            {showDetails && (
              <div className="space-y-3 pt-2 border-t">
                {error?.stack && (
                  <div>
                    <h4 className="font-medium text-sm mb-2">Error Stack:</h4>
                    <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40 font-mono">
                      {error.stack}
                    </pre>
                  </div>
                )}

                {errorInfo?.componentStack && (
                  <div>
                    <h4 className="font-medium text-sm mb-2">Component Stack:</h4>
                    <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40 font-mono">
                      {errorInfo.componentStack}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
}

export default ModernErrorBoundary;
