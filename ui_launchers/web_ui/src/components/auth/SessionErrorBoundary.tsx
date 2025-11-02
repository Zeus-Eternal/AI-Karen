/**
 * Simplified Session-Aware Error Boundary
 * 
 * Catches authentication-related errors and redirects to login immediately.
 * No complex session recovery logic.
 * 
 * Requirements: 5.2, 5.3, 5.5
 */
"use client";

import React, { Component, ReactNode } from 'react';
import { AlertCircle, RefreshCw, LogIn } from 'lucide-react';
import { clearSession } from '@/lib/auth/session';
interface SessionErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
  onAuthError?: (error: Error) => void;
}
interface SessionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}
export class SessionErrorBoundary extends Component<
> {
  constructor(props: SessionErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }
  static getDerivedStateFromError(error: Error): Partial<SessionErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Check if this is an authentication-related error
    if (this.isAuthenticationError(error)) {
      this.props.onAuthError?.(error);
      // Clear session immediately and redirect to login
      clearSession();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
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
  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,

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
    // Show simple error with login option for auth errors
    const isAuthError = this.isAuthenticationError(this.state.error!);
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-6 max-w-md mx-auto p-6 sm:p-4 md:p-6">
          <AlertCircle className="h-16 w-16 mx-auto text-red-500 " />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">
              {isAuthError ? 'Authentication Error' : 'Something went wrong'}
            </h2>
            <p className="text-muted-foreground">
              {isAuthError 
                ? 'Please log in to continue.'
                : 'An unexpected error occurred.'
              }
            </p>
            <details className="text-left">
              <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground md:text-base lg:text-lg">
              </summary>
              <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded overflow-auto sm:text-sm md:text-base">
                {this.state.error!.message}
              </pre>
            </details>
          </div>
          <div className="space-y-3">
            {isAuthError ? (
              <button
                onClick={this.handleLogin}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
               aria-label="Button">
                <LogIn className="h-4 w-4 " />
              </button>
            ) : (
              <button
                onClick={this.handleRetry}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
               aria-label="Button">
                <RefreshCw className="h-4 w-4 " />
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
