/**
 * Simplified Session-Aware Error Boundary (Production-Hardened)
 *
 * Catches authentication-related errors and redirects to login immediately.
 * Adds: robust auth-error detection, redirect debouncing, safe session clearing,
 * accessible fallback UI, and a typed HOC wrapper.
 *
 * Requirements: 5.2, 5.3, 5.5
 */
"use client";

import React, { Component, ReactNode } from "react";
import { AlertCircle, RefreshCw, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearSession } from "@/lib/auth/session";

export interface SessionErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback renderer (non-auth errors only) */
  fallback?: (error: Error, retry: () => void) => ReactNode;
  /** Callback when an authentication error is detected (pre-redirect) */
  onAuthError?: (error: Error) => void;
  /** Where to send the user when auth fails (defaults to /login) */
  loginPath?: string;
  /** Session storage key used to debounce auth redirects */
  redirectDebounceKey?: string;
  /** Minimum ms between automatic auth redirects to avoid loops */
  minRedirectIntervalMs?: number;
}

export interface SessionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class SessionErrorBoundary extends Component<
  SessionErrorBoundaryProps,
  SessionErrorBoundaryState
> {
  static defaultProps: Required<Pick<
    SessionErrorBoundaryProps,
    "loginPath" | "redirectDebounceKey" | "minRedirectIntervalMs"
  >> = {
    loginPath: "/login",
    redirectDebounceKey: "lastAuthRedirectAt",
    minRedirectIntervalMs: 3000,
  };

  constructor(props: SessionErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<SessionErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    // If this is an authentication error: purge session & bounce to login
    if (this.isAuthenticationError(error)) {
      try {
        this.props.onAuthError?.(error);

        // Debounce to prevent redirect loops (e.g., if login page throws)
        const { redirectDebounceKey, minRedirectIntervalMs, loginPath } = this.props;
        const last = Number(sessionStorage.getItem(redirectDebounceKey!)) || 0;
        const now = Date.now();
        if (now - last >= (minRedirectIntervalMs || 0)) {
          sessionStorage.setItem(redirectDebounceKey!, String(now));
          // Clear local session artifacts first
          try {
            clearSession();
          } catch {
            // non-fatal
          }
          if (typeof window !== "undefined") {
            // Remember route for post-login redirect
            try {
              sessionStorage.setItem("redirectAfterLogin", window.location.pathname + window.location.search);
            } catch {
              /* ignore */
            }
            window.location.replace(loginPath!);
          }
        }
      } catch {
        // Swallow to avoid secondary crashes; UI will still show fallback
      }
    }
  }

  /** Expanded detection for common auth failure shapes (HTTP libs, fetch, custom errors). */
  private isAuthenticationError(error: Error): boolean {
    const message = (error?.message || "").toLowerCase();

    // Common textual indicators
    if (
      message.includes("401") ||
      message.includes("403") ||
      message.includes("unauthorized") ||
      message.includes("forbidden") ||
      message.includes("authentication") ||
      message.includes("token") ||
      message.includes("jwt") ||
      message.includes("session") ||
      message.includes("expired")
    ) {
      return true;
    }

    // Shapes from fetch/axios-like errors
    const anyErr = error as unknown as Record<string, unknown>;
    const responseStatus = (anyErr?.response as Record<string, unknown>)?.status;
    const causeStatus = (anyErr?.cause as Record<string, unknown>)?.status;
    const status = anyErr?.status ?? responseStatus ?? causeStatus;
    if (status === 401 || status === 403) return true;

    // Custom error codes
    const responseData = (anyErr?.response as Record<string, unknown>)?.data as
      | Record<string, unknown>
      | undefined;
    const code =
      anyErr?.code || responseData?.code || "";
    const normalizedCode = String(code).toLowerCase();
    if (normalizedCode.includes("auth") || normalizedCode.includes("token") || normalizedCode.includes("unauthorized")) {
      return true;
    }

    return false;
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    // Optional: simple soft reload to retry client fetchers without a full navigation
    // window.location.reload(); // enable if your app prefers a hard refresh
  };

  private handleLogin = () => {
    if (typeof window !== "undefined") {
      try {
        sessionStorage.setItem("redirectAfterLogin", window.location.pathname + window.location.search);
      } catch {
        /* ignore */
      }
      window.location.assign(this.props.loginPath!);
    }
  };

  render() {
    const { children, fallback } = this.props;
    const { hasError, error } = this.state;

    if (!hasError) return children;

    const err = error ?? new Error("Unknown error");
    const isAuthError = this.isAuthenticationError(err);

    // If a custom fallback is provided, delegate (for non-auth errors only)
    if (fallback && !isAuthError) {
      return fallback(err, this.handleRetry);
    }

    // Minimal, accessible fallback. If it's an auth error, urge login.
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-6 max-w-md mx-auto p-6">
          <AlertCircle className="h-16 w-16 mx-auto text-red-500" aria-hidden="true" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold" role="heading" aria-level={2}>
              {isAuthError ? "Authentication Error" : "Something went wrong"}
            </h2>
            <p className="text-muted-foreground">
              {isAuthError ? "Please log in to continue." : "An unexpected error occurred."}
            </p>
            <details className="text-left">
              <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                Error details
              </summary>
              <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded overflow-auto">
                {err.message}
              </pre>
            </details>
          </div>

          <div className="space-y-3">
            {isAuthError ? (
              <Button
                onClick={this.handleLogin}
                className="inline-flex items-center gap-2"
                aria-label="Go to login"
              >
                <LogIn className="h-4 w-4" />
                Login
              </Button>
            ) : (
              <Button
                onClick={this.handleRetry}
                className="inline-flex items-center gap-2"
                aria-label="Retry"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }
}

/**
 * Higher-order component to wrap components with session error boundary.
 */
export function withSessionErrorBoundary<P extends object>(
  Wrapped: React.ComponentType<P>,
  errorBoundaryProps?: Omit<SessionErrorBoundaryProps, "children">
) {
  const ComponentWithBoundary = (props: P) => (
    <SessionErrorBoundary {...errorBoundaryProps}>
      <Wrapped {...props} />
    </SessionErrorBoundary>
  );
  ComponentWithBoundary.displayName = `withSessionErrorBoundary(${Wrapped.displayName || Wrapped.name || "Component"})`;
  return ComponentWithBoundary;
}
