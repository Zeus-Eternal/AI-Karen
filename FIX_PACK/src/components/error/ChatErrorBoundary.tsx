import React, { Component, ErrorInfo, ReactNode } from 'react';
import { telemetryService } from '../../lib/telemetry';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  correlationId?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
  retryCount: number;
}

export class ChatErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;
  private retryTimeouts: NodeJS.Timeout[] = [];

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { correlationId, onError } = this.props;
    const { errorId } = this.state;

    // Track error with telemetry
    telemetryService.track('error.boundary.caught', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      errorInfo: {
        componentStack: errorInfo.componentStack,
      },
      errorId,
      correlationId,
      retryCount: this.state.retryCount,
    }, correlationId);

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    console.error('ChatErrorBoundary caught an error:', error, errorInfo);
  }

  componentWillUnmount() {
    // Clear any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
  }

  handleRetry = () => {
    const { retryCount } = this.state;
    
    if (retryCount >= this.maxRetries) {
      telemetryService.track('error.boundary.max_retries_exceeded', {
        errorId: this.state.errorId,
        retryCount,
        correlationId: this.props.correlationId,
      }, this.props.correlationId);
      return;
    }

    // Exponential backoff: 1s, 2s, 4s
    const delay = Math.pow(2, retryCount) * 1000;
    
    telemetryService.track('error.boundary.retry_attempted', {
      errorId: this.state.errorId,
      retryCount: retryCount + 1,
      delay,
      correlationId: this.props.correlationId,
    }, this.props.correlationId);

    const timeout = setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorId: null,
        retryCount: retryCount + 1,
      });
    }, delay);

    this.retryTimeouts.push(timeout);
  };

  handleReload = () => {
    telemetryService.track('error.boundary.page_reload', {
      errorId: this.state.errorId,
      correlationId: this.props.correlationId,
    }, this.props.correlationId);
    
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallbackUI
          error={this.state.error}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          maxRetries={this.maxRetries}
          onRetry={this.handleRetry}
          onReload={this.handleReload}
        />
      );
    }

    return this.props.children;
  }
}

interface ErrorFallbackUIProps {
  error: Error | null;
  errorId: string | null;
  retryCount: number;
  maxRetries: number;
  onRetry: () => void;
  onReload: () => void;
}

const ErrorFallbackUI: React.FC<ErrorFallbackUIProps> = ({
  error,
  errorId,
  retryCount,
  maxRetries,
  onRetry,
  onReload,
}) => {
  const canRetry = retryCount < maxRetries;

  return (
    <div className="error-boundary-fallback" role="alert">
      <div className="error-content">
        <div className="error-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        
        <h2 className="error-title">Something went wrong</h2>
        
        <p className="error-message">
          We encountered an unexpected error. This has been automatically reported to our team.
        </p>

        {process.env.NODE_ENV === 'development' && error && (
          <details className="error-details">
            <summary>Error Details (Development)</summary>
            <pre className="error-stack">
              <code>{error.message}</code>
              {error.stack && (
                <code className="stack-trace">{error.stack}</code>
              )}
            </pre>
          </details>
        )}

        <div className="error-actions">
          {canRetry && (
            <button
              onClick={onRetry}
              className="retry-button"
              type="button"
            >
              Try Again {retryCount > 0 && `(${retryCount}/${maxRetries})`}
            </button>
          )}
          
          <button
            onClick={onReload}
            className="reload-button"
            type="button"
          >
            Reload Page
          </button>
        </div>

        {errorId && (
          <p className="error-id">
            Error ID: <code>{errorId}</code>
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatErrorBoundary;