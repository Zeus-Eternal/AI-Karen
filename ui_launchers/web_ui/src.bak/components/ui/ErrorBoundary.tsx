/**
 * Enhanced Error Boundary with AG-UI and CopilotKit Fallbacks
 * 
 * Provides comprehensive error handling for React components with
 * intelligent fallback strategies and recovery mechanisms.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { agUIErrorHandler, AGUIErrorType, FallbackStrategy } from '../../lib/ag-ui-error-handler';

interface Props {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<any>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  componentName?: string;
  enableRetry?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  fallbackResponse: any;
  retryCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;
  private retryTimeout: NodeJS.Timeout | null = null;

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

  async componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Handle the error with AG-UI error handler
    const componentName = this.props.componentName || 'unknown';
    const fallbackResponse = await agUIErrorHandler.handleComponentError(
      error,
      componentName
    );

    this.setState({
      errorInfo,
      fallbackResponse
    });
  }

  handleRetry = async () => {
    if (this.state.retryCount >= this.maxRetries) {
      console.warn('Maximum retry attempts reached');
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

  private renderDefaultErrorUI(fallbackResponse: any, enableRetry: boolean) {
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
              <button 
                onClick={this.handleRetry}
                className="retry-button"
                disabled={retryCount >= this.maxRetries}
              >
                Retry ({retryCount}/{this.maxRetries})
              </button>
            )}
            <button onClick={this.handleReset} className="reset-button">
              Reset Component
            </button>
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

  private renderSimpleTableFallback(fallbackResponse: any, enableRetry: boolean) {
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
            <button onClick={this.handleRetry} className="retry-button">
              Try Advanced View Again
            </button>
            <button onClick={this.handleReset} className="reset-button">
              Reset Component
            </button>
          </div>
        )}
      </div>
    );
  }

  private renderCachedDataFallback(fallbackResponse: any, enableRetry: boolean) {
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
            <button onClick={this.handleRetry} className="retry-button">
              Refresh Data
            </button>
            <button onClick={this.handleReset} className="reset-button">
              Reset Component
            </button>
          </div>
        )}
      </div>
    );
  }

  private renderLoadingStateFallback(fallbackResponse: any, enableRetry: boolean) {
    const { message } = fallbackResponse;

    return (
      <div className="error-boundary-container">
        <div className="loading-fallback">
          <div className="loading-spinner">⏳</div>
          <p>{message}</p>
          {enableRetry && (
            <button onClick={this.handleRetry} className="retry-button">
              Retry Loading
            </button>
          )}
        </div>
      </div>
    );
  }

  private renderErrorMessageFallback(fallbackResponse: any, enableRetry: boolean) {
    const { message } = fallbackResponse;

    return (
      <div className="error-boundary-container">
        <div className="error-message-fallback">
          <div className="error-icon">❌</div>
          <p>{message}</p>
          {enableRetry && (
            <div className="fallback-actions">
              <button onClick={this.handleRetry} className="retry-button">
                Retry
              </button>
              <button onClick={this.handleReset} className="reset-button">
                Reset
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  private renderGenericFallback(fallbackResponse: any, enableRetry: boolean) {
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
              <button onClick={this.handleRetry} className="retry-button">
                Retry
              </button>
              <button onClick={this.handleReset} className="reset-button">
                Reset
              </button>
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