import React, { Component, ErrorInfo, ReactNode } from 'react';
import { getTelemetryService } from '@/lib/telemetry';
interface Props {
  children: ReactNode;
  onStreamingError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: () => void;
  onAbort?: () => void;
  correlationId?: string;
  streamId?: string;
  preservePartialContent?: boolean;
  maxRetries?: number;
  enableRecovery?: boolean;
  className?: string;
}
interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  canRetry: boolean;
  retryCount: number;
  isRetrying: boolean;
  streamAborted: boolean;
}
export class StreamingErrorBoundary extends Component<Props, State> {
  private telemetryService = getTelemetryService();
  private maxRetries: number;
  private retryTimeout: NodeJS.Timeout | null = null;
  constructor(props: Props) {
    super(props);
    this.maxRetries = props.maxRetries ?? 3;
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      canRetry: true,
      retryCount: 0,
      isRetrying: false,
      streamAborted: false,
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
    const { correlationId, streamId, onStreamingError, preservePartialContent } = this.props;
    const { errorId } = this.state;
    // Store error info
    this.setState({ errorInfo });
    // Determine error type and severity
    const errorType = this.categorizeStreamingError(error);
    const isRecoverable = this.isRecoverableError(error);
    // Track streaming-specific error with comprehensive context
    this.telemetryService.track('error.streaming.boundary_caught', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
        type: errorType,
        isRecoverable,
      },
      errorInfo: {
        componentStack: errorInfo.componentStack,
      },
      errorId,
      correlationId,
      streamId,
      preservePartialContent,
      retryCount: this.state.retryCount,
      context: {
        timestamp: new Date().toISOString(),
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
        connectionType: this.getConnectionType(),
        streamingSupported: this.checkStreamingSupport(),
      }
    }, correlationId);
    // Update retry capability based on error type
    this.setState({ 
      canRetry: isRecoverable && this.state.retryCount < this.maxRetries 

    // Call custom streaming error handler
    if (onStreamingError) {
      try {
        onStreamingError(error, errorInfo);
      } catch (handlerError) {
        this.telemetryService.track('error.streaming.handler_failed', {
          originalError: error.message,
          handlerError: handlerError instanceof Error ? handlerError.message : 'Unknown',
          errorId,

      }
    }
  }
  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
    this.telemetryService.track('error.streaming.boundary_unmounted', {
      hadError: this.state.hasError,
      retryCount: this.state.retryCount,
      streamAborted: this.state.streamAborted,
      errorId: this.state.errorId,

  }
  private categorizeStreamingError(error: Error): string {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();
    if (name.includes('network') || message.includes('network')) return 'network';
    if (name.includes('abort') || message.includes('abort')) return 'aborted';
    if (name.includes('timeout') || message.includes('timeout')) return 'timeout';
    if (name.includes('parse') || message.includes('parse')) return 'parsing';
    if (name.includes('stream') || message.includes('stream')) return 'streaming';
    if (name.includes('fetch') || message.includes('fetch')) return 'fetch';
    return 'unknown';
  }
  private isRecoverableError(error: Error): boolean {
    const errorType = this.categorizeStreamingError(error);
    const recoverableTypes = ['network', 'timeout', 'fetch', 'streaming'];
    // Don't retry if explicitly aborted
    if (errorType === 'aborted' || this.state.streamAborted) {
      return false;
    }
    return recoverableTypes.includes(errorType);
  }
  private getConnectionType(): string {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      return connection?.effectiveType || connection?.type || 'unknown';
    }
    return 'unknown';
  }
  private checkStreamingSupport(): boolean {
    return typeof ReadableStream !== 'undefined' && 
           typeof fetch !== 'undefined' &&
           'body' in Response.prototype;
  }
  handleRetry = () => {
    const { onRetry, correlationId, streamId, enableRecovery = true } = this.props;
    const { errorId, retryCount } = this.state;
    if (!enableRecovery || retryCount >= this.maxRetries || this.state.streamAborted) {
      return;
    }
    this.setState({ isRetrying: true });
    this.telemetryService.track('error.streaming.retry_attempted', {
      errorId,
      correlationId,
      streamId,
      retryCount: retryCount + 1,
      maxRetries: this.maxRetries,
    }, correlationId);
    // Exponential backoff with jitter
    const baseDelay = Math.pow(2, retryCount) * 1000;
    const jitter = Math.random() * 500;
    const delay = baseDelay + jitter;
    this.retryTimeout = setTimeout(() => {
      if (onRetry) {
        onRetry();
      }
      // Reset error state
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        canRetry: true,
        retryCount: retryCount + 1,
        isRetrying: false,

    }, delay);
  };
  handleAbort = () => {
    const { onAbort, correlationId, streamId } = this.props;
    const { errorId } = this.state;
    this.telemetryService.track('error.streaming.aborted', {
      errorId,
      correlationId,
      streamId,
      retryCount: this.state.retryCount,
    }, correlationId);
    this.setState({ 
      canRetry: false, 
      streamAborted: true,
      isRetrying: false 

    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = null;
    }
    if (onAbort) {
      onAbort();
    }
  };
  handleContinue = () => {
    const { correlationId, streamId } = this.props;
    const { errorId } = this.state;
    this.telemetryService.track('error.streaming.continued_with_partial', {
      errorId,
      correlationId,
      streamId,
    }, correlationId);
    // Clear error state but keep partial content
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      canRetry: false,

  };
  render() {
    if (this.state.hasError) {
      return (
        <StreamingErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          canRetry={this.state.canRetry && !this.state.streamAborted}
          retryCount={this.state.retryCount}
          maxRetries={this.maxRetries}
          isRetrying={this.state.isRetrying}
          preservePartialContent={this.props.preservePartialContent}
          streamAborted={this.state.streamAborted}
          onRetry={this.handleRetry}
          onAbort={this.handleAbort}
          onContinue={this.handleContinue}
          className={this.props.className}
        />
      );
    }
    return this.props.children;
  }
}
interface StreamingErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  canRetry: boolean;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  preservePartialContent?: boolean;
  streamAborted: boolean;
  onRetry: () => void;
  onAbort: () => void;
  onContinue: () => void;
  className?: string;
}
const StreamingErrorFallback: React.FC<StreamingErrorFallbackProps> = ({
  error,
  errorInfo,
  errorId,
  canRetry,
  retryCount,
  maxRetries,
  isRetrying,
  preservePartialContent,
  streamAborted,
  onRetry,
  onAbort,
  onContinue,
  className = '',
}) => {
  const getErrorMessage = () => {
    if (streamAborted) return 'Stream was stopped';
    if (error?.message.toLowerCase().includes('network')) return 'Network connection lost';
    if (error?.message.toLowerCase().includes('timeout')) return 'Request timed out';
    if (error?.message.toLowerCase().includes('abort')) return 'Stream was interrupted';
    return 'Streaming error occurred';
  };
  const getErrorIcon = () => {
    if (streamAborted) {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="6" y="6" width="12" height="12" rx="2"/>
        </svg>
      );
    }
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    );
  };
  return (
    <div 
      className={`inline-flex items-center gap-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md text-yellow-800 dark:text-yellow-200 text-sm ${className}`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex-shrink-0 text-yellow-600 dark:text-yellow-400">
        {getErrorIcon()}
      </div>
      <div className="flex-1 min-w-0 ">
        <span className="font-medium">{getErrorMessage()}</span>
        {preservePartialContent && !streamAborted && (
          <span className="ml-1 text-xs opacity-75 sm:text-sm md:text-base">
            (partial content preserved)
          </span>
        )}
      </div>
      <div className="flex items-center gap-1 ml-2">
        {canRetry && !streamAborted && (
          <Button
            onClick={onRetry}
            disabled={isRetrying}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-yellow-800 dark:text-yellow-200 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed sm:text-sm md:text-base"
            type="button"
            title={`Retry streaming (${retryCount}/${maxRetries})`}
          >
            {isRetrying ? (
              <>
                <svg className="animate-spin w-3 h-3 " fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Retrying...
              </>
            ) : (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <polyline points="1 20 1 14 7 14"/>
                  <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                </svg>
              </>
            )}
          </Button>
        )}
        {preservePartialContent && !streamAborted && (
          <Button
            onClick={onContinue}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-yellow-800 dark:text-yellow-200 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded transition-colors sm:text-sm md:text-base"
            type="button"
            title="Continue with partial content"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </Button>
        )}
        {!streamAborted && (
          <Button
            onClick={onAbort}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-yellow-800 dark:text-yellow-200 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded transition-colors sm:text-sm md:text-base"
            type="button"
            title="Stop streaming"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
          </Button>
        )}
      </div>
      {process.env.NODE_ENV === 'development' && errorId && (
        <div className="text-xs opacity-50 font-mono ml-2 sm:text-sm md:text-base">
          {errorId.split('_').pop()}
        </div>
      )}
    </div>
  );
};
export default StreamingErrorBoundary;
