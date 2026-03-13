// ui_launchers/KAREN-Theme-Default/src/components/error/optimistic-error-boundary.tsx
"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
type WindowWithAnalytics = Window & {
  gtag?: (...args: unknown[]) => void;
  dataLayer?: Array<Record<string, unknown>>;
};
import { Button } from "@/components/ui/button";
// Keep the project’s UI store path as provided by you
import { useUIStore } from "../../store";

/** ------- Types ------- */
interface OptimisticErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
  errorId: string;
}

export interface OptimisticErrorBoundaryProps {
  children: ReactNode;

  /** Custom fallback renderer; receives error + retry/reset handlers */
  fallback?: (props: {
    error: Error | null;
    errorInfo: ErrorInfo | null;
    retry: () => void;
    reset: () => void;
    retryCount: number;
    canRetry: boolean;
  }) => ReactNode;

  /** Max auto/manual retries before disabling the Retry button (default 3) */
  maxRetries?: number;

  /** Delay before reset after triggering a retry (ms; default 120) */
  retryDelayMs?: number;

  /** Telemetry + lifecycle hooks */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: (retryCount: number) => void;
  onReset?: () => void;

  /**
   * When unknown value in this array changes (shallow equality), the boundary resets.
   * Mirrors react-error-boundary semantics to reduce surprises.
   */
  resetKeys?: Array<string | number | boolean | null | undefined>;

  /** Also reset when the children node identity changes */
  resetOnPropsChange?: boolean;

  /** Optional name for telemetry and debugging */
  boundaryName?: string;
}

/** Shallow array equality for resetKeys */
function arraysAreEqual(a?: unknown[], b?: unknown[]) {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

class OptimisticErrorBoundaryClass extends Component<
  OptimisticErrorBoundaryProps,
  OptimisticErrorBoundaryState
> {
  private resetTimeoutId: number | null = null;
  private readonly maxRetries: number;
  private readonly retryDelayMs: number;

  constructor(props: OptimisticErrorBoundaryProps) {
    super(props);
    this.maxRetries = props.maxRetries ?? 3;
    this.retryDelayMs = props.retryDelayMs ?? 120;
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      errorId: "",
    };
  }

  static getDerivedStateFromError(error: Error): Partial<OptimisticErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `err-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });

    // Log to UI store (no hooks in class components; Zustand getter is fine)
    try {
      const { setError } = useUIStore.getState();
      if (typeof setError === "function") {
        setError(this.state.errorId, error.message);
      }
    } catch {
      /* noop */
    }

    // User callback
    this.props.onError?.(error, errorInfo);

    // Best-effort telemetry
    try {
      const analyticsWindow = window as WindowWithAnalytics;
      if (typeof analyticsWindow.gtag === "function") {
        analyticsWindow.gtag("event", "exception", {
          description: error?.message ?? String(error),
          fatal: false,
          boundary: this.props.boundaryName ?? "OptimisticBoundary",
        });
      } else if (Array.isArray(analyticsWindow.dataLayer)) {
        analyticsWindow.dataLayer.push({
          event: "exception",
          description: error?.message ?? String(error),
          fatal: false,
          boundary: this.props.boundaryName ?? "OptimisticBoundary",
        });
      }
      window.dispatchEvent(
        new CustomEvent("kari:error", {
          detail: {
            boundary: this.props.boundaryName ?? "OptimisticBoundary",
            message: error?.message ?? String(error),
            stack: error?.stack ?? "",
          },
        })
      );
      // eslint-disable-next-line no-console
      console.error(
        `[OptimisticErrorBoundary] ${this.props.boundaryName ?? "Boundary"} caught:`,
        error,
        errorInfo
      );
    } catch {
      /* noop */
    }
  }

  componentDidUpdate(prevProps: OptimisticErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange, children } = this.props;
    const { hasError } = this.state;

    // Reset on children identity change if enabled
    if (hasError && resetOnPropsChange && prevProps.children !== children) {
      this.resetErrorBoundary();
      return;
    }

    // Reset on resetKeys changes (shallow compare)
    if (
      hasError &&
      (resetKeys || prevProps.resetKeys) &&
      !arraysAreEqual(prevProps.resetKeys, resetKeys)
    ) {
      this.resetErrorBoundary();
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    // Clear error from store
    try {
      const { clearError } = useUIStore.getState();
      if (typeof clearError === "function" && this.state.errorId) {
        clearError(this.state.errorId);
      }
    } catch {
      /* noop */
    }
  }

  resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    // Clear store record
    try {
      const { clearError } = useUIStore.getState();
      if (typeof clearError === "function" && this.state.errorId) {
        clearError(this.state.errorId);
      }
    } catch {
      /* noop */
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      errorId: "",
    });

    this.props.onReset?.();
  };

  retryRender = () => {
    const next = this.state.retryCount + 1;
    if (next <= this.maxRetries) {
      this.setState({ retryCount: next });
      this.props.onRetry?.(next);

      // Allow state to flush; then reset to attempt a clean re-render
      this.resetTimeoutId = window.setTimeout(() => {
        this.resetErrorBoundary();
      }, this.retryDelayMs);
    }
  };

  render() {
    const { hasError, error, errorInfo, retryCount } = this.state;
    const { fallback, children } = this.props;
    const canRetry = retryCount < this.maxRetries;

    if (hasError) {
      if (fallback) {
        return fallback({
          error,
          errorInfo,
          retry: this.retryRender,
          reset: this.resetErrorBoundary,
          retryCount,
          canRetry,
        });
      }
      return (
        <DefaultErrorFallback
          error={error}
          errorInfo={errorInfo}
          retry={this.retryRender}
          reset={this.resetErrorBoundary}
          retryCount={retryCount}
          canRetry={canRetry}
        />
      );
    }
    return children;
  }
}

/** ------- Default Fallback UI (minimal, accessible, theme-friendly) ------- */
function DefaultErrorFallback({
  error,
  retry,
  reset,
  retryCount,
  canRetry,
}: {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retry: () => void;
  reset: () => void;
  retryCount: number;
  canRetry: boolean;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center p-6 border rounded-lg bg-muted/30"
      role="alert"
      aria-live="polite"
    >
      <h3 className="text-lg font-semibold mb-1">Something went wrong</h3>
      <p className="text-sm text-muted-foreground mb-3">
        {error?.message ?? "An unexpected error occurred."}
      </p>

      {retryCount > 0 && (
        <p className="text-xs text-muted-foreground mb-3">
          Retry attempt: {retryCount}
        </p>
      )}

      <div className="flex gap-2">
        {canRetry && (
          <Button onClick={retry} aria-label="Retry render">
            Retry
          </Button>
        )}
        <Button variant="outline" onClick={reset} aria-label="Reset error boundary">
          Reset
        </Button>
      </div>

      {process.env.NODE_ENV === "development" && error?.stack && (
        <details className="mt-4 w-full max-w-2xl">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:underline">
            Error details (development)
          </summary>
          <pre className="mt-2 p-3 bg-background border rounded text-xs overflow-auto whitespace-pre-wrap break-words">
            {error.stack}
          </pre>
        </details>
      )}
    </div>
  );
}

/** ------- Public API ------- */
export function OptimisticErrorBoundary(props: OptimisticErrorBoundaryProps) {
  return <OptimisticErrorBoundaryClass {...props} />;
}

export default OptimisticErrorBoundary;
