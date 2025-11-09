// ui_launchers/KAREN-Theme-Default/src/components/chat/SafeChatWrapper.tsx
/**
 * Safe Chat Wrapper
 * Prevents console interceptor issues and isolates chat UI crashes.
 */

"use client";

import React, { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { safeError } from "@/lib/safe-console";

interface SafeChatWrapperProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface SafeChatWrapperState {
  hasError: boolean;
  error: Error | null;
}

export class SafeChatWrapper extends Component<
  SafeChatWrapperProps,
  SafeChatWrapperState
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
    // Log via safe console wrapper to avoid interceptor issues
    safeError(
      "SafeChatWrapper caught an error",
      {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      },
      {
        skipInProduction: false,
        useStructuredLogging: true,
      }
    );

    // Trigger external error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    const { hasError, error } = this.state;

    if (hasError) {
      return (
        <div className="flex items-center justify-center h-full p-6 sm:p-4 md:p-6 bg-background text-foreground">
          <div className="text-center space-y-4 max-w-md">
            <h3 className="text-lg font-semibold">Chat Interface Error</h3>
            <p className="text-sm text-muted-foreground">
              {error?.message ??
                "The chat interface encountered an unexpected error."}
              <br />
              Please refresh the page to continue.
            </p>
            <Button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default SafeChatWrapper;
