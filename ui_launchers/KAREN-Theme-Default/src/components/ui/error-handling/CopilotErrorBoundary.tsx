import React, { Component, ReactNode } from 'react';
import { Button } from '../button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../card';

interface CopilotErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  isRetryable: boolean;
}

interface CopilotErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  isRetryable?: boolean;
}

/**
 * CopilotErrorBoundary - Error boundary component for Copilot features
 * Catches JavaScript errors anywhere in child component tree and displays a fallback UI
 */
export class CopilotErrorBoundary extends Component<CopilotErrorBoundaryProps, CopilotErrorBoundaryState> {
  constructor(props: CopilotErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isRetryable: props.isRetryable ?? true
    };
  }

  static getDerivedStateFromError(error: Error): Partial<CopilotErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // If a custom fallback is provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Otherwise, use the default error UI
      return (
        <Card className="copilot-error-boundary">
          <CardHeader>
            <CardTitle className="text-destructive">Copilot Error</CardTitle>
            <CardDescription>
              Something went wrong with the Copilot interface
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="copilot-error-boundary__content">
              <p className="copilot-error-boundary__message">
                {this.state.error?.message || 'An unknown error occurred'}
              </p>
              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <details className="copilot-error-boundary__details">
                  <summary className="copilot-error-boundary__summary">
                    Error Details
                  </summary>
                  <pre className="copilot-error-boundary__stack">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </div>
          </CardContent>
          {this.state.isRetryable && (
            <CardFooter>
              <Button onClick={this.handleRetry} variant="outline">
                Retry
              </Button>
            </CardFooter>
          )}
        </Card>
      );
    }

    return this.props.children;
  }
}

// Set display name for component
(CopilotErrorBoundary as React.ComponentType).displayName = 'CopilotErrorBoundary';