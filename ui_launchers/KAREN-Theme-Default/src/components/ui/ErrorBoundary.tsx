/**
 * Enhanced Error Boundary with AG-UI and CopilotKit Fallbacks
 * 
 * Provides comprehensive error handling for React components with
 * intelligent fallback strategies and recovery mechanisms.
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { agUIErrorHandler, FallbackStrategy, type FallbackResponse } from '../../lib/ag-ui-error-handler';
export interface Props {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<any>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  componentName?: string;
  enableRetry?: boolean;
}
export interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  fallbackResponse: FallbackResponse | null;
  retryCount: number;
}
export class ErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;
  private retryTimeout: ReturnType<typeof setTimeout> | null = null;
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      fallbackResponse: null,
      retryCount: 0
    };
  }
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    this.setState({
      errorInfo,
    });

    const componentName = this.props.componentName || 'unknown';

    void agUIErrorHandler
      .handleComponentError(error, componentName)
      .then((fallbackResponse) => {
        this.setState({ fallbackResponse });
      })
      .catch(() => {
        this.setState({ fallbackResponse: null });
      });
  }
  handleRetry = async () => {
    if (this.state.retryCount >= this.maxRetries) {
      return;
    }
    this.setState(prevState => ({
      retryCount: prevState.retryCount + 1
    }));
    // Clear error state after a short delay to allow re-rendering
    this.retryTimeout = setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        fallbackResponse: null
      });
    }, 1000);
  };
  handleReset = () => {
    const componentName = this.props.componentName || 'unknown';
    agUIErrorHandler.resetComponent(componentName);
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      fallbackResponse: null,
      retryCount: 0
    });
  };
  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
  }
  render() {
    if (this.state.hasError) {
      const { fallbackResponse } = this.state;
      const { fallbackComponent: FallbackComponent, enableRetry = true } = this.props;
      // Use custom fallback component if provided
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            fallbackResponse={fallbackResponse}
            onRetry={this.handleRetry}
            onReset={this.handleReset}
            retryCount={this.state.retryCount}
            maxRetries={this.maxRetries}
          />
        );
      }
      // Default error UI based on fallback strategy
      return this.renderDefaultErrorUI(fallbackResponse, enableRetry);
    }
    return this.props.children;
  }
  private renderDefaultErrorUI(
    fallbackResponse: FallbackResponse | null,
    enableRetry: boolean
  ) {
    const { error, retryCount } = this.state;
    const componentName = this.props.componentName || 'Component';
    if (!fallbackResponse) {
      return (
        <div className="error-boundary-container">
          <div className="error-boundary-content">
            <div className="error-icon">⚠️</div>
            <h3>Something went wrong</h3>
            <p>{componentName} encountered an error and couldn't be displayed.</p>
            {enableRetry && retryCount < this.maxRetries && (
              <Button
                onClick={this.handleRetry}
                className="retry-button"
                disabled={retryCount >= this.maxRetries}
                aria-label="Retry Button"
              >
                Retry ({retryCount}/{this.maxRetries})
              </Button>
            )}
            <Button onClick={this.handleReset} className="reset-button" aria-label="Reset Button">
              Reset
            </Button>
          </div>
        </div>
      );
    }
    switch (fallbackResponse.strategy) {
      case FallbackStrategy.SIMPLE_TABLE:
        return this.renderSimpleTableFallback(fallbackResponse, enableRetry);
      case FallbackStrategy.CACHED_DATA:
        return this.renderCachedDataFallback(fallbackResponse, enableRetry);
      case FallbackStrategy.LOADING_STATE:
        return this.renderLoadingStateFallback(fallbackResponse, enableRetry);
      case FallbackStrategy.ERROR_MESSAGE:
        return this.renderErrorMessageFallback(fallbackResponse, enableRetry);
      default:
        return this.renderGenericFallback(fallbackResponse, enableRetry);
    }
  }
  private renderSimpleTableFallback(
    fallbackResponse: FallbackResponse,
    enableRetry: boolean
  ) {
    const { data, columns, message, degradedFeatures } = fallbackResponse;
    return (
      <div className="error-boundary-container">
        <div className="fallback-warning">
          <div className="warning-icon">⚠️</div>
          <div className="warning-content">
            <p>{message}</p>
            {degradedFeatures.length > 0 && (
              <p className="degraded-features">
                Disabled features: {degradedFeatures.join(', ')}
              </p>
            )}
          </div>
        </div>
        <div className="simple-table-container">
          {data && data.length > 0 ? (
            <table className="simple-table">
              <thead>
                <tr>
                  {columns.map((col: any, index: number) => (
                    <th key={index}>{col.headerName || col.field}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row: any, rowIndex: number) => (
                  <tr key={rowIndex}>
                    {columns.map((col: any, colIndex: number) => (
                      <td key={colIndex}>{row[col.field] || '-'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="no-data">No data available</div>
          )}
        </div>
        {enableRetry && (
          <div className="fallback-actions">
            <Button
              onClick={this.handleRetry}
              className="retry-button"
              aria-label="Retry"
            >
              Retry ({this.state.retryCount}/{this.maxRetries})
            </Button>
            <Button
              onClick={this.handleReset}
              className="reset-button"
              aria-label="Reset"
            >
              Reset Component
            </Button>
          </div>
        )}
      </div>
    );
  }
  private renderCachedDataFallback(
    fallbackResponse: FallbackResponse,
    enableRetry: boolean
  ) {
    const { message, degradedFeatures } = fallbackResponse;
    return (
      <div className="error-boundary-container">
        <div className="fallback-warning cached-data">
          <div className="warning-icon">📋</div>
          <div className="warning-content">
            <p>{message}</p>
            {degradedFeatures.length > 0 && (
              <p className="degraded-features">
                Disabled features: {degradedFeatures.join(', ')}
              </p>
            )}
          </div>
        </div>
        {enableRetry && (
          <div className="fallback-actions">
            <Button
              onClick={this.handleRetry}
              className="retry-button"
              aria-label="Retry"
            >
              Retry ({this.state.retryCount}/{this.maxRetries})
            </Button>
            <Button
              onClick={this.handleReset}
              className="reset-button"
              aria-label="Reset"
            >
              Reset Component
            </Button>
          </div>
        )}
      </div>
    );
  }
  private renderLoadingStateFallback(
    fallbackResponse: FallbackResponse,
    enableRetry: boolean
  ) {
    const { message } = fallbackResponse;
    return (
      <div className="error-boundary-container">
        <div className="loading-fallback">
          <div className="loading-spinner">⏳</div>
          <p>{message}</p>
          {enableRetry && (
            <Button
              onClick={this.handleRetry}
              className="retry-button"
              aria-label="Retry"
            >
              Retry ({this.state.retryCount}/{this.maxRetries})
            </Button>
          )}
        </div>
      </div>
    );
  }
  private renderErrorMessageFallback(
    fallbackResponse: FallbackResponse,
    enableRetry: boolean
  ) {
    const { message } = fallbackResponse;
    return (
      <div className="error-boundary-container">
        <div className="error-message-fallback">
          <div className="error-icon">❌</div>
          <p>{message}</p>
          {enableRetry && (
            <div className="fallback-actions">
              <Button
                onClick={this.handleRetry}
                className="retry-button"
                aria-label="Retry"
              >
                Retry ({this.state.retryCount}/{this.maxRetries})
              </Button>
              <Button
                onClick={this.handleReset}
                className="reset-button"
                aria-label="Reset"
              >
                Reset Component
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }
  private renderGenericFallback(
    fallbackResponse: FallbackResponse,
    enableRetry: boolean
  ) {
    const { message } = fallbackResponse;
    const componentName = this.props.componentName || 'Component';
    return (
      <div className="error-boundary-container">
        <div className="generic-fallback">
          <div className="error-icon">⚠️</div>
          <h3>{componentName} Error</h3>
          <p>{message || 'An unexpected error occurred.'}</p>
          {enableRetry && (
            <div className="fallback-actions">
              <Button
                onClick={this.handleRetry}
                className="retry-button"
                aria-label="Retry"
              >
                Retry ({this.state.retryCount}/{this.maxRetries})
              </Button>
              <Button
                onClick={this.handleReset}
                className="reset-button"
                aria-label="Reset"
              >
                Reset Component
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }
}
// Higher-order component for easy wrapping
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WithErrorBoundaryComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  );
  WithErrorBoundaryComponent.displayName = 
    `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithErrorBoundaryComponent;
}
// Hook for error boundary context
export function useErrorBoundary() {
  return {
    resetComponent: (componentName: string) => {
      agUIErrorHandler.resetComponent(componentName);
    },
    getComponentHealth: (componentName: string) => {
      return agUIErrorHandler.getComponentHealth(componentName);
    }
  };
}
