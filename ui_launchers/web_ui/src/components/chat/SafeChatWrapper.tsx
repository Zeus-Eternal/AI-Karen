/**
 * Safe Chat Wrapper - Prevents console interceptor issues
 */

"use client";

import React, { Component, ReactNode } from 'react';
import { safeError } from '@/lib/safe-console';

interface SafeChatWrapperProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface SafeChatWrapperState {
  hasError: boolean;
  error: Error | null;
}

export class SafeChatWrapper extends Component<
> {
  constructor(props: SafeChatWrapperProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<SafeChatWrapperState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Use safe console to prevent interceptor issues
    safeError('SafeChatWrapper caught an error', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    }, {
      skipInProduction: false,
      useStructuredLogging: true,

    // Call the onError callback if provided
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-full p-4 sm:p-4 md:p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Chat Interface Error</h3>
            <p className="text-muted-foreground mb-4">
              The chat interface encountered an error. Please refresh the page to continue.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default SafeChatWrapper;