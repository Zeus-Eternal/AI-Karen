/**
 * Session-Aware Error Boundary
 * 
 * Catches authentication-related errors and attempts session recovery
 * before showing error messages or redirecting to login.
 * 
 * Requirements: 5.2, 5.3, 5.5
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { AlertCircle, RefreshCw, LogIn } from 'lucide-react';
import { attemptSessionRecovery, type SessionRecoveryResult } from '@/lib/auth/session-recovery';

interface SessionErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
  onAuthError?: (error: Error) => void;
  onRecoveryAttempt?: (result: SessionRecoveryResult) => void;
}

interface SessionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  isRecovering: boolean;
  recoveryAttempted: boolean;
  recoveryResult: SessionRecoveryResult | null;
}

export class SessionErrorBoundary extends Component<
  SessionErrorBoundaryProps,
  SessionErrorBoundaryState
> {
  constructor(props: SessionErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      isRecovering: false,
      recoveryAttempted: false,
      recoveryResult: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<SessionErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('SessionErrorBoundary caught an error:', error, errorInfo);
    
    // Check if this is an authentication-related error
    if (this.isAuthenticationError(error)) {
      this.props.onAuthError?.(error);
      this.attemptRecovery();
    }
  }

  private isAuthenticationError(error: Error): boolean {
    const message = error.message.toLowerCase();
    return (
      message.includes('401') ||
      message.includes('unauthorized') ||
      message.includes('authentication') ||
      message.includes('token') ||
      message.includes('session')
    );
  }

  private attemptRecovery = async () => {
    if (this.state.isRecovering || this.state.recoveryAttempted) {
      return;
    }

    this.setState({ isRecovering: true });

    try {
      const result = await attemptSessionRecovery();
      
      this.setState({
        isRecovering: false,
        recoveryAttempted: true,
        recoveryResult: result,
      });

      this.props.onRecoveryAttempt?.(result);

      if (result.success) {
        // Recovery successful, reset error state
        this.setState({
          hasError: false,
          error: null,
          recoveryAttempted: false,
          recoveryResult: null,
        });
      }
    } catch (recoveryError) {
      console.error('Session recovery failed:', recoveryError);
      this.setState({
        isRecovering: false,
        recoveryAttempted: true,
        recoveryResult: {
          success: false,
          reason: 'invalid_session',
          shouldShowLogin: true,
          message: 'Session recovery failed. Please log in again.',
        },
      });
    }
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      recoveryAttempted: false,
      recoveryResult: null,
    });
  };

  private handleLogin = () => {
    if (typeof window !== 'undefined') {
      // Store current path for redirect after login
      sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
      window.location.href = '/login';
    }
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    // Use custom fallback if provided
    if (this.props.fallback) {
      return this.props.fallback(this.state.error!, this.handleRetry);
    }

    // Show recovery in progress
    if (this.state.isRecovering) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center space-y-4">
            <RefreshCw className="h-12 w-12 animate-spin mx-auto text-primary" />
            <div className="space-y-2">
              <h2 className="text-xl font-semibold">Recovering Session</h2>
              <p className="text-muted-foreground">
                Attempting to restore your session...
              </p>
            </div>
          </div>
        </div>
      );
    }

    // Show recovery result
    if (this.state.recoveryAttempted && this.state.recoveryResult) {
      const { recoveryResult } = this.state;

      if (recoveryResult.success) {
        // This shouldn't happen as successful recovery resets the error state
        return this.props.children;
      }

      // Recovery failed
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center space-y-6 max-w-md mx-auto p-6">
            <AlertCircle className="h-16 w-16 mx-auto text-red-500" />
            <div className="space-y-2">
              <h2 className="text-xl font-semibold">Session Error</h2>
              <p className="text-muted-foreground">
                {recoveryResult.message || 'An authentication error occurred.'}
              </p>
              {this.state.error && (
                <details className="text-left">
                  <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                    Technical details
                  </summary>
                  <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded overflow-auto">
                    {this.state.error.message}
                  </pre>
                </details>
              )}
            </div>
            <div className="space-y-3">
              {recoveryResult.shouldShowLogin ? (
                <button
                  onClick={this.handleLogin}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  <LogIn className="h-4 w-4" />
                  Go to Login
                </button>
              ) : (
                <button
                  onClick={this.handleRetry}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Show generic error with recovery option for auth errors
    const isAuthError = this.isAuthenticationError(this.state.error!);

    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-6 max-w-md mx-auto p-6">
          <AlertCircle className="h-16 w-16 mx-auto text-red-500" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">
              {isAuthError ? 'Authentication Error' : 'Something went wrong'}
            </h2>
            <p className="text-muted-foreground">
              {isAuthError 
                ? 'There was a problem with your session.'
                : 'An unexpected error occurred.'
              }
            </p>
            <details className="text-left">
              <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                Technical details
              </summary>
              <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded overflow-auto">
                {this.state.error!.message}
              </pre>
            </details>
          </div>
          <div className="space-y-3">
            {isAuthError ? (
              <button
                onClick={this.attemptRecovery}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Recover Session
              </button>
            ) : (
              <button
                onClick={this.handleRetry}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }
}

/**
 * Higher-order component to wrap components with session error boundary
 */
export function withSessionErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<SessionErrorBoundaryProps, 'children'>
) {
  return function WrappedComponent(props: P) {
    return (
      <SessionErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </SessionErrorBoundary>
    );
  };
}