import React, { Component, ErrorInfo, ReactNode } from 'react';
import { telemetryService } from '../../lib/telemetry';

interface Props {
  children: ReactNode;
  onStreamingError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: () => void;
  correlationId?: string;
  streamId?: string;
  preservePartialContent?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
  canRetry: boolean;
}

export class StreamingErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
      canRetry: true,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `stream_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { correlationId, streamId, onStreamingError } = this.props;
    const { errorId } = this.state;

    // Track streaming-specific error
    telemetryService.track('error.streaming.boundary_caught', {
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
      streamId,
      preservePartialContent: this.props.preservePartialContent,
    }, correlationId);

    // Call custom streaming error handler
    if (onStreamingError) {
      onStreamingError(error, errorInfo);
    }

    console.error('StreamingErrorBoundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    const { onRetry, correlationId, streamId } = this.props;
    const { errorId } = this.state;

    telemetryService.track('error.streaming.retry_attempted', {
      errorId,
      correlationId,
      streamId,
    }, correlationId);

    if (onRetry) {
      onRetry();
    }

    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorId: null,
      canRetry: true,
    });
  };

  handleAbort = () => {
    const { correlationId, streamId } = this.props;
    const { errorId } = this.state;

    telemetryService.track('error.streaming.aborted', {
      errorId,
      correlationId,
      streamId,
    }, correlationId);

    this.setState({ canRetry: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <StreamingErrorFallback
          error={this.state.error}
          errorId={this.state.errorId}
          canRetry={this.state.canRetry}
          preservePartialContent={this.props.preservePartialContent}
          onRetry={this.handleRetry}
          onAbort={this.handleAbort}
        />
      );
    }

    return this.props.children;
  }
}

interface StreamingErrorFallbackProps {
  error: Error | null;
  errorId: string | null;
  canRetry: boolean;
  preservePartialContent?: boolean;
  onRetry: () => void;
  onAbort: () => void;
}

const StreamingErrorFallback: React.FC<StreamingErrorFallbackProps> = ({
  error,
  errorId,
  canRetry,
  preservePartialContent,
  onRetry,
  onAbort,
}) => {
  return (
    <div className="streaming-error-boundary" role="alert">
      <div className="streaming-error-content">
        <div className="streaming-error-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        
        <div className="streaming-error-message">
          <span className="streaming-error-title">Streaming interrupted</span>
          {preservePartialContent && (
            <span className="streaming-error-subtitle">
              Partial content has been preserved
            </span>
          )}
        </div>

        <div className="streaming-error-actions">
          {canRetry && (
            <button
              onClick={onRetry}
              className="streaming-retry-button"
              type="button"
              title="Retry streaming"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"/>
                <polyline points="1 20 1 14 7 14"/>
                <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Retry
            </button>
          )}
          
          <button
            onClick={onAbort}
            className="streaming-abort-button"
            type="button"
            title="Stop streaming"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
            Stop
          </button>
        </div>

        {errorId && process.env.NODE_ENV === 'development' && (
          <div className="streaming-error-id">
            Error ID: <code>{errorId}</code>
          </div>
        )}
      </div>
    </div>
  );
};

export default StreamingErrorBoundary;