"use client";

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from './button';
import { AlertTriangle, RefreshCw, Home, Bug, Copy, Mail } from 'lucide-react';

export interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  enableReport?: boolean;
  reportEndpoint?: string;
  title?: string;
  description?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  reportSent?: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log the error to the console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      reportSent: false,
    });
  };

  handleCopyError = () => {
    if (this.state.error) {
      const errorText = `Error: ${this.state.error.name}\n\nMessage: ${this.state.error.message}\n\nStack: ${this.state.error.stack}\n\nComponent Stack: ${this.state.errorInfo?.componentStack || 'N/A'}`;
      navigator.clipboard.writeText(errorText);
    }
  };

  handleReportError = async () => {
    if (!this.state.error || !this.props.enableReport || !this.props.reportEndpoint) return;

    try {
      const errorReport = {
        name: this.state.error.name,
        message: this.state.error.message,
        stack: this.state.error.stack,
        componentStack: this.state.errorInfo?.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        location: window.location.href
      };

      const response = await fetch(this.props.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
      });

      if (response.ok) {
        this.setState({ reportSent: true });
      }
    } catch (err) {
      console.error('Failed to report error:', err);
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const showDetails = this.props.showDetails ?? process.env.NODE_ENV === 'development';

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <div className="w-full max-w-md">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700">
              <div className="p-6 text-center">
                <div className="flex justify-center mb-4">
                  <div className="rounded-full bg-red-100 dark:bg-red-900/20 p-3">
                    <AlertTriangle className="h-12 w-12 text-red-600 dark:text-red-400" />
                  </div>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {this.props.title || 'Something went wrong'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
                  {this.props.description || 'We apologize for the inconvenience. An unexpected error has occurred.'}
                </p>
                
                <div className="flex flex-col sm:flex-row gap-3 mb-6">
                  <Button
                    onClick={this.handleReset}
                    className="flex-1 gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                  </Button>
                  
                  <Button
                    onClick={() => window.location.href = '/'}
                    variant="outline"
                    className="flex-1 gap-2"
                  >
                    <Home className="h-4 w-4" />
                    Go Home
                  </Button>
                </div>

                {showDetails && this.state.error && (
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm font-medium text-gray-600 dark:text-gray-300">
                        <Bug className="mr-1 h-4 w-4" />
                        Error Details
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={this.handleCopyError}
                        className="h-8 px-2"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md text-xs font-mono overflow-auto max-h-40">
                      <div className="font-bold text-gray-900 dark:text-white">{this.state.error.name}:</div>
                      <div className="text-gray-700 dark:text-gray-300">{this.state.error.message}</div>
                      {this.state.errorInfo?.componentStack && (
                        <div className="mt-2">
                          <div className="font-bold text-gray-900 dark:text-white">Component Stack:</div>
                          <pre className="whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {this.props.enableReport && this.props.reportEndpoint && (
                  <Button
                    variant="outline"
                    onClick={this.handleReportError}
                    disabled={this.state.reportSent}
                    className="w-full gap-2"
                  >
                    <Mail className="h-4 w-4" />
                    {this.state.reportSent ? 'Report Sent' : 'Report Error'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

