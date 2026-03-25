'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class AgentErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Agent UI Error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="p-6 h-full flex flex-col items-center justify-center bg-background border rounded-xl">
          <Alert variant="destructive" className="max-w-md w-full">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Agent UI crashed</AlertTitle>
            <AlertDescription className="mt-2 space-y-4">
              <p className="text-sm opacity-90">
                {this.state.error?.message || 'An unexpected error occurred while rendering the agent interface.'}
              </p>
              <Button onClick={this.handleReset} variant="outline" size="sm" className="w-full gap-2">
                <RefreshCw className="h-4 w-4" />
                Retry connection
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

export function AgentChatSkeleton() {
  return (
    <div className="flex flex-col h-full bg-background border rounded-xl animate-pulse">
      {/* Skeleton Header */}
      <div className="flex items-center gap-3 p-4 border-b">
        <div className="h-10 w-10 bg-muted rounded-full" />
        <div className="space-y-2 flex-1">
          <div className="h-4 w-32 bg-muted rounded" />
          <div className="h-3 w-48 bg-muted rounded" />
        </div>
      </div>
      
      {/* Skeleton Messages */}
      <div className="flex-1 p-4 space-y-6">
        <div className="flex justify-end pr-8">
          <div className="h-12 w-64 bg-primary/20 rounded-xl rounded-tr-none" />
        </div>
        <div className="flex gap-3 pr-12">
          <div className="h-8 w-8 bg-muted rounded-full shrink-0" />
          <div className="h-24 w-full max-w-md bg-muted rounded-xl rounded-tl-none" />
        </div>
        <div className="flex justify-end pr-8">
          <div className="h-10 w-48 bg-primary/20 rounded-xl rounded-tr-none" />
        </div>
      </div>
      
      {/* Skeleton Input */}
      <div className="p-4 border-t flex gap-2">
        <div className="h-10 flex-1 bg-muted rounded-md" />
        <div className="h-10 w-12 bg-muted rounded-md shrink-0" />
      </div>
    </div>
  );
}
