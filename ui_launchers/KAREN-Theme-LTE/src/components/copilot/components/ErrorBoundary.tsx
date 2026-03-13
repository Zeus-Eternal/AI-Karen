import * as React from 'react';
import ErrorHandlingService from '../services/ErrorHandlingService';
import UserErrorMessageService from '../services/UserErrorMessageService';
import { ErrorCategory, ErrorSeverity } from '../services/ErrorHandlingService';

/**
 * Error boundary props
 */
export interface ErrorBoundaryProps {
  /** Children to render */
  children: React.ReactNode;
  
  /** Fallback component to render when error occurs */
  fallback?: React.ComponentType<{ error: Error; errorInfo: React.ErrorInfo }>;
  
  /** Custom error message to display */
  errorMessage?: string;
  
  /** Whether to show error details to user */
  showErrorDetails?: boolean;
  
  /** Callback function to call when error occurs */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  
  /** Component name for error tracking */
  componentName?: string;
  
  /** Error category */
  errorCategory?: ErrorCategory;
  
  /** Error severity */
  errorSeverity?: ErrorSeverity;
}

/**
 * Error boundary state
 */
export interface ErrorBoundaryState {
  /** Whether an error has occurred */
  hasError: boolean;
  
  /** Error that occurred */
  error: Error | null;
  
  /** React error info */
  errorInfo: React.ErrorInfo | null;
}

/**
 * Default fallback component
 */
const DefaultFallback: React.FC<{ error: Error; errorInfo: React.ErrorInfo }> = ({ error, errorInfo }) => {
  const errorHandlingService = ErrorHandlingService.getInstance();
  const userErrorMessageService = UserErrorMessageService.getInstance();
  
  // Get user-friendly error message
  const userFriendlyError = userErrorMessageService.getUserFriendlyError(error, {
    component: errorInfo.componentStack?.split('\n')[0]?.trim() || 'Unknown Component'
  });
  
  return (
    <div className="error-boundary-fallback">
      <div className="error-boundary-content">
        <h2 className="error-boundary-title">Something went wrong</h2>
        <p className="error-boundary-message">
          {userFriendlyError.message}
        </p>
        
        {userFriendlyError.suggestedActions && userFriendlyError.suggestedActions.length > 0 && (
          <div className="error-boundary-actions">
            <h3>What you can try:</h3>
            <ul>
              {userFriendlyError.suggestedActions.map((action, index) => (
                <li key={index}>{action}</li>
              ))}
            </ul>
          </div>
        )}
        
        {(userFriendlyError.showTechnicalDetails || process.env.NODE_ENV === 'development') && (
          <details className="error-boundary-details">
            <summary>Error details</summary>
            <pre className="error-boundary-stack">
              {error.stack}
            </pre>
            <pre className="error-boundary-component-stack">
              {errorInfo.componentStack}
            </pre>
          </details>
        )}
        
        <div className="error-boundary-buttons">
          <button 
            className="error-boundary-button"
            onClick={() => window.location.reload()}
          >
            Reload Page
          </button>
          <button 
            className="error-boundary-button"
            onClick={() => window.history.back()}
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Error boundary component for catching React errors
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private errorHandlingService: ErrorHandlingService;
  private userErrorMessageService: UserErrorMessageService;
  
  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
    
    this.errorHandlingService = ErrorHandlingService.getInstance();
    this.userErrorMessageService = UserErrorMessageService.getInstance();
  }
  
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Update state with error info
    this.setState({
      error,
      errorInfo
    });
    
    // Handle error with error handling service
    this.errorHandlingService.handleError(
      error,
      this.props.errorCategory || ErrorCategory.UI,
      this.props.errorSeverity || ErrorSeverity.HIGH,
      {
        component: this.props.componentName || this.extractComponentName(errorInfo),
        function: 'componentDidCatch',
        componentStack: errorInfo.componentStack
      },
      undefined,
      {
        showNotification: true,
        notificationType: 'toast',
        message: this.props.errorMessage || 'An error occurred in the user interface'
      }
    );
    
    // Call error callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }
  
  /**
   * Extract component name from error info
   */
  private extractComponentName(errorInfo: React.ErrorInfo): string {
    if (!errorInfo.componentStack) return 'Unknown Component';
    const firstLine = errorInfo.componentStack.split('\n')[0];
    if (!firstLine) return 'Unknown Component';
    const match = firstLine.match(/in (\w+)/);
    return match && match[1] ? match[1] : 'Unknown Component';
  }
  
  /**
   * Reset error state
   */
  public resetErrorBoundary(): void {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  }
  
  render(): React.ReactNode {
    if (this.state.hasError && this.state.error) {
      // If custom fallback is provided, use it
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return (
          <FallbackComponent 
            error={this.state.error} 
            errorInfo={this.state.errorInfo || { componentStack: '' } as React.ErrorInfo} 
          />
        );
      }
      
      // Otherwise use default fallback
      return (
        <DefaultFallback 
          error={this.state.error} 
          errorInfo={this.state.errorInfo || { componentStack: '' } as React.ErrorInfo} 
        />
      );
    }
    
    return this.props.children;
  }
}

/**
 * Higher-order component for adding error boundary to a component
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.ComponentType<P> {
  const WrappedComponent: React.ComponentType<P> = (props: P) => {
    const errorProps: ErrorBoundaryProps = {
      children: <Component {...props} />,
      ...(errorBoundaryProps || {})
    };
    return React.createElement(ErrorBoundary, errorProps);
  };
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

/**
 * Hook for using error boundary in functional components
 */
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);
  const [errorInfo, setErrorInfo] = React.useState<React.ErrorInfo | null>(null);
  
  const errorHandlingService = ErrorHandlingService.getInstance();
  const userErrorMessageService = UserErrorMessageService.getInstance();
  
  const handleError = React.useCallback((
    err: Error,
    info?: React.ErrorInfo,
    options?: {
      componentName?: string;
      errorMessage?: string;
      errorCategory?: ErrorCategory;
      errorSeverity?: ErrorSeverity;
    }
  ) => {
    setError(err);
    setErrorInfo(info || null);
    
    // Handle error with error handling service
    errorHandlingService.handleError(
      err,
      options?.errorCategory || ErrorCategory.UI,
      options?.errorSeverity || ErrorSeverity.HIGH,
      {
        component: options?.componentName || 'Unknown Component',
        function: 'useErrorBoundary'
      },
      undefined,
      {
        showNotification: true,
        notificationType: 'toast',
        message: options?.errorMessage || 'An error occurred in the user interface'
      }
    );
  }, [errorHandlingService]);
  
  const resetError = React.useCallback(() => {
    setError(null);
    setErrorInfo(null);
  }, []);
  
  const getUserFriendlyError = React.useCallback((err: Error) => {
    return userErrorMessageService.getUserFriendlyError(err, {
      component: errorInfo?.componentStack?.split('\n')[0]?.trim() || 'Unknown Component'
    });
  }, [userErrorMessageService, errorInfo]);
  
  return {
    error,
    errorInfo,
    handleError,
    resetError,
    getUserFriendlyError
  };
}

export default ErrorBoundary;