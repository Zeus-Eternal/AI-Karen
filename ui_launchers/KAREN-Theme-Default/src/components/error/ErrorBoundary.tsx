// ui_launchers/KAREN-Theme-Default/src/components/error/ErrorBoundary.tsx
"use client";

import React, { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ErrorInfo = React.ErrorInfo;

interface Props {
  /** Children to render inside the boundary */
  children: ReactNode;
  /** Static fallback node (used if renderFallback not provided) */
  fallback?: ReactNode;
  /** Fallback renderer with access to error + reset */
  renderFallback?: (args: { error?: Error; reset: () => void }) => ReactNode;
  /** Callback when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Callback when the boundary is reset via Try Again */
  onReset?: () => void;
  /** Optional name for telemetry and UI title */
  boundaryName?: string;
  /** Keys that, when changed, auto-reset the boundary (like react-error-boundary) */
  resetKeys?: unknown[];
}

interface State {
  hasError: boolean;
  error?: Error;
}

type AnalyticsWindow = Window & {
  gtag?: (...args: unknown[]) => void;
  dataLayer?: unknown[];
};

function arraysAreEqual(a?: unknown[], b?: unknown[]) {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    // shallow equality is enough for reset semantics
    if (a[i] !== b[i]) return false;
  }
  return true;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: undefined };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // User callback
    this.props.onError?.(error, errorInfo);

    // Console (useful in dev and for dashboards piping console to logs)
    // eslint-disable-next-line no-console
    console.error(`[ErrorBoundary] ${this.props.boundaryName ?? "Boundary"} caught:`, error, errorInfo);

    // Lightweight browser telemetry (gtag or dataLayer if present)
    try {
      const analyticsWindow =
        typeof window !== "undefined" ? (window as AnalyticsWindow) : undefined;
      if (typeof analyticsWindow?.gtag === "function") {
        analyticsWindow.gtag("event", "exception", {
          description: error?.message ?? String(error),
          fatal: true,
          boundary: this.props.boundaryName ?? "UnnamedBoundary",
        });
      } else if (Array.isArray(analyticsWindow?.dataLayer)) {
        analyticsWindow.dataLayer.push({
          event: "exception",
          description: error?.message ?? String(error),
          fatal: true,
          boundary: this.props.boundaryName ?? "UnnamedBoundary",
        });
      }
      // Custom DOM event hook for your audit/Prometheus bridges
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("kari:error", {
            detail: {
              boundary: this.props.boundaryName ?? "UnnamedBoundary",
              message: error?.message ?? String(error),
              stack: error?.stack ?? "",
            },
          })
        );
      }
    } catch {
      // best-effort only
    }
  }

  componentDidUpdate(prevProps: Props) {
    // Auto-reset when resetKeys change
    if (!arraysAreEqual(prevProps.resetKeys, this.props.resetKeys) && this.state.hasError) {
      this.reset();
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: undefined }, () => this.props.onReset?.());
  };

  handleHardRefresh = () => {
    // Full reload – safest recovery path after unrecoverable UI state
    window.location.reload();
  };

  renderDefaultFallback() {
    const title = this.props.boundaryName ?? "Something went wrong";
    return (
      <div className="min-h-[50vh] flex items-center justify-center p-4 bg-background sm:p-4 md:p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <AlertTriangle className="h-12 w-12 text-destructive" aria-hidden="true" />
            </div>
            <CardTitle className="text-xl font-semibold">{title}</CardTitle>
            <CardDescription>An unexpected error occurred. You can try again or refresh.</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {process.env.NODE_ENV === "development" && this.state.error && (
              <details className="bg-muted p-3 rounded text-xs font-mono sm:text-sm md:text-base">
                <summary className="cursor-pointer font-sans font-medium">Error details</summary>
                <pre className="mt-2 whitespace-pre-wrap break-all">
                  {this.state.error.toString()}
                  {this.state.error.stack && (
                    <>
                      {"\n\nStack trace:\n"}
                      {this.state.error.stack}
                    </>
                  )}
                </pre>
              </details>
            )}

            <div className="flex gap-2">
              <Button onClick={this.reset} className="flex-1" aria-label="Try again">
                <RefreshCw className="h-4 w-4 mr-2" aria-hidden="true" />
                Try Again
              </Button>

              <Button
                variant="outline"
                onClick={this.handleHardRefresh}
                className="flex-1"
                aria-label="Refresh page"
              >
                Refresh Page
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  render() {
    if (this.state.hasError) {
      if (this.props.renderFallback) {
        return this.props.renderFallback({ error: this.state.error, reset: this.reset });
      }
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return this.renderDefaultFallback();
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
