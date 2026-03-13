import React, { Component, useCallback, useState } from 'react';
import {
  ErrorInfo as ErrorHandlingInfo,
  ErrorBoundaryProps,
  UseErrorBoundaryReturn,
  ErrorType,
  ErrorCategory,
  ErrorSeverity,
  type ErrorReport,
  type RecoveryAttempt,
  type RecoveryResult,
} from './types';
import { generateId } from '@/lib/id-generator';

type BoundaryState = {
  hasError: boolean;
  error: ErrorHandlingInfo | null;
  rawError: Error | null;
  componentStack: string[];
  retryCount: number;
  isRecovering: boolean;
  recoveryAttempts: RecoveryAttempt[];
};

type RecoveryApiResponse = RecoveryResult & {
  success?: boolean;
};

type BrowserWindow = Window & {
  authContext?: {
    userId?: string;
  };
  errorLogger?: {
    logError?: (errorInfo: ErrorHandlingInfo, originalError: Error, componentStack: string[]) => void;
  };
};

const INITIAL_STATE: BoundaryState = {
  hasError: false,
  error: null,
  rawError: null,
  componentStack: [],
  retryCount: 0,
  isRecovering: false,
  recoveryAttempts: [],
};

const wait = (delayMs: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, delayMs));

const getBrowserWindow = (): BrowserWindow | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return window as BrowserWindow;
};

const createBaseErrorInfo = (error: Error, component?: string): ErrorHandlingInfo => ({
  id: generateId('error'),
  type: ErrorType.COMPONENT_ERROR,
  category: ErrorCategory.UI_COMPONENT,
  severity: ErrorSeverity.HIGH,
  title: 'Component Error',
  message: error.message || 'An unexpected error occurred.',
  technicalDetails: error.stack || error.message,
  resolutionSteps: [
    'Try the operation again',
    'Refresh the page if the problem persists',
    'Contact support if this keeps happening',
  ],
  retryPossible: true,
  userActionRequired: false,
  timestamp: new Date().toISOString(),
  context: {
    component,
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
    url: typeof window !== 'undefined' ? window.location.href : 'Unknown',
  },
  metadata: {
    originalError: error.name,
  },
  stackTrace: error.stack,
  component,
  operation: 'render',
});

const parseComponentStack = (errorInfo: React.ErrorInfo): string[] =>
  (errorInfo.componentStack || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

const buildErrorReport = (
  errorInfo: ErrorHandlingInfo,
  componentStack: string[],
  component?: string,
  userFeedback?: string
): ErrorReport => ({
  id: generateId('report'),
  errorId: errorInfo.id,
  userId:
    getBrowserWindow()?.authContext?.userId ||
    (typeof localStorage !== 'undefined' ? localStorage.getItem('userId') || undefined : undefined),
  sessionId:
    typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('sessionId') || undefined : undefined,
  component,
  operation: errorInfo.operation,
  errorInfo,
  userFeedback,
  timestamp: new Date().toISOString(),
  status: 'pending',
  metadata: {
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
    url: typeof window !== 'undefined' ? window.location.href : 'Unknown',
    componentStack,
  },
});

const sendErrorReport = async (report: ErrorReport): Promise<void> => {
  if (typeof fetch === 'undefined') {
    return;
  }

  await fetch('/api/error-reports', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(report),
  });
};

const attemptErrorRecovery = async (error: ErrorHandlingInfo): Promise<RecoveryResult> => {
  try {
    const response = await fetch('/api/error-recovery', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        errorId: error.id,
        category: error.category,
        type: error.type,
        component: error.component,
      }),
    });

    if (!response.ok) {
      throw new Error('Recovery request failed');
    }

    const result = (await response.json()) as RecoveryApiResponse;
    if (result.finalStatus) {
      return result;
    }

    return {
      finalStatus: result.success ? 'success' : 'failed',
      failedActions: [],
      successfulActions: [],
      totalDuration: 0,
      finalResult: result,
      finalError: result.success ? undefined : 'Recovery request failed',
    };
  } catch (recoveryError) {
    const message =
      recoveryError instanceof Error ? recoveryError.message : 'Unknown recovery error';

    return {
      finalStatus: 'failed',
      failedActions: [],
      successfulActions: [],
      totalDuration: 0,
      finalError: message,
    };
  }
};

const DefaultErrorFallback: React.FC<{
  error: Error;
  errorInfo: ErrorHandlingInfo | null;
  onRetry: () => Promise<void>;
  onRecovery: () => Promise<void>;
  onReport: (feedback?: string) => Promise<void>;
  retryCount: number;
  maxRetries: number;
  isRecovering: boolean;
  componentStack: string[];
  reset: () => void;
}> = ({
  error,
  errorInfo,
  onRetry,
  onRecovery,
  onReport,
  retryCount,
  maxRetries,
  isRecovering,
  componentStack,
  reset,
}) => (
  <div
    className="error-boundary-fallback"
    style={{
      padding: '20px',
      border: '1px solid #ff6b6b',
      borderRadius: '8px',
      backgroundColor: '#ffe6e6',
      color: '#d63031',
      margin: '10px 0',
    }}
  >
    <h3 style={{ margin: '0 0 10px 0' }}>{errorInfo?.title || 'Something went wrong'}</h3>
    <p style={{ margin: '0 0 10px 0' }}>{errorInfo?.message || error.message}</p>

    {errorInfo?.resolutionSteps && errorInfo.resolutionSteps.length > 0 && (
      <ol style={{ margin: '0 0 16px 0', paddingLeft: '20px' }}>
        {errorInfo.resolutionSteps.map((step, index) => (
          <li key={index} style={{ margin: '4px 0' }}>
            {step}
          </li>
        ))}
      </ol>
    )}

    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
      {retryCount < maxRetries && errorInfo?.retryPossible && (
        <button onClick={onRetry} disabled={isRecovering}>
          {isRecovering ? 'Retrying...' : 'Retry'}
        </button>
      )}
      <button onClick={onRecovery} disabled={isRecovering}>
        {isRecovering ? 'Recovering...' : 'Recover'}
      </button>
      <button onClick={() => onReport('Reported from error boundary')} disabled={isRecovering}>
        Report
      </button>
      <button onClick={reset} disabled={isRecovering}>
        Reset
      </button>
    </div>

    {componentStack.length > 0 && (
      <details style={{ marginTop: '16px' }}>
        <summary>Component Stack</summary>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{componentStack.join('\n')}</pre>
      </details>
    )}
  </div>
);

export class ErrorBoundary extends Component<ErrorBoundaryProps, BoundaryState> {
  state: BoundaryState = INITIAL_STATE;

  static getDerivedStateFromError(error: Error): Partial<BoundaryState> {
    return {
      hasError: true,
      rawError: error,
      error: createBaseErrorInfo(error),
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    const componentStack = parseComponentStack(errorInfo);
    const classifiedError = this.classifyError(error);

    this.setState({
      hasError: true,
      rawError: error,
      error: classifiedError,
      componentStack,
      isRecovering: false,
    });

    this.props.onError?.(classifiedError, error, componentStack);
    this.logError(classifiedError, error, componentStack);

    if (this.props.enableReporting !== false) {
      void sendErrorReport(buildErrorReport(classifiedError, componentStack, this.props.component));
    }
  }

  private classifyError(error: Error): ErrorHandlingInfo {
    const errorInfo = createBaseErrorInfo(error, this.props.component);
    const message = error.message.toLowerCase();

    if (message.includes('fetch') || message.includes('network') || message.includes('connection')) {
      return {
        ...errorInfo,
        type: ErrorType.CONNECTION_ERROR,
        category: ErrorCategory.NETWORK,
        severity: ErrorSeverity.HIGH,
        title: 'Connection Failed',
        message: 'Unable to connect to the service. Please check your internet connection.',
      };
    }

    if (message.includes('timeout') || message.includes('timed out')) {
      return {
        ...errorInfo,
        type: ErrorType.TIMEOUT_ERROR,
        category: ErrorCategory.TIMEOUT,
        severity: ErrorSeverity.MEDIUM,
        title: 'Request Timeout',
        message: 'The request took too long to complete. Please try again.',
      };
    }

    if (message.includes('validation') || message.includes('invalid')) {
      return {
        ...errorInfo,
        type: ErrorType.VALIDATION_ERROR,
        category: ErrorCategory.VALIDATION,
        severity: ErrorSeverity.LOW,
        title: 'Validation Error',
        message: 'Invalid input provided. Please review your data and try again.',
        retryPossible: false,
        userActionRequired: true,
      };
    }

    if (
      message.includes('permission') ||
      message.includes('unauthorized') ||
      message.includes('forbidden')
    ) {
      return {
        ...errorInfo,
        type: ErrorType.PERMISSION_ERROR,
        category: ErrorCategory.AUTHORIZATION,
        severity: ErrorSeverity.HIGH,
        title: 'Permission Denied',
        message: "You don't have permission to perform this action.",
        retryPossible: false,
        userActionRequired: true,
      };
    }

    if (message.includes('memory') || message.includes('space')) {
      return {
        ...errorInfo,
        type: ErrorType.MEMORY_ERROR,
        category: ErrorCategory.RESOURCE_EXHAUSTION,
        severity: ErrorSeverity.CRITICAL,
        title: 'Resource Exhaustion',
        message: 'System resources are exhausted. Please try again later.',
      };
    }

    return errorInfo;
  }

  private logError(errorInfo: ErrorHandlingInfo, originalError: Error, componentStack: string[]): void {
    if (this.props.enableLogging === false) {
      return;
    }

    console.group(`Error Boundary: ${errorInfo.title}`);
    console.error('Error Info:', errorInfo);
    console.error('Original Error:', originalError);
    console.error('Component Stack:', componentStack);
    console.groupEnd();

    getBrowserWindow()?.errorLogger?.logError?.(errorInfo, originalError, componentStack);
  }

  private handleRetry = async (): Promise<void> => {
    const { error, retryCount, isRecovering } = this.state;
    const maxRetries = this.props.maxRetries || 3;

    if (!error || isRecovering || retryCount >= maxRetries) {
      return;
    }

    this.setState({ isRecovering: true });

    try {
      this.props.onRetry?.(error, retryCount + 1);

      if ((this.props.retryDelay || 0) > 0) {
        await wait(this.props.retryDelay || 0);
      }

      this.setState((prevState) => ({
        ...INITIAL_STATE,
        retryCount: prevState.retryCount + 1,
      }));
    } catch (retryError) {
      console.error('Retry callback failed:', retryError);
      this.setState({ isRecovering: false });
    }
  };

  private handleRecovery = async (): Promise<void> => {
    const { error, isRecovering } = this.state;

    if (!error || isRecovering) {
      return;
    }

    this.setState({ isRecovering: true });

    try {
      const recoveryResult = await attemptErrorRecovery(error);
      this.props.onRecovery?.(error, recoveryResult);

      if (recoveryResult.finalStatus === 'success') {
        this.setState(INITIAL_STATE);
        return;
      }

      this.setState((prevState) => ({
        ...prevState,
        isRecovering: false,
        recoveryAttempts: [
          ...prevState.recoveryAttempts,
          ...recoveryResult.failedActions,
          ...recoveryResult.successfulActions,
        ],
      }));
    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
      this.setState({ isRecovering: false });
    }
  };

  private handleReport = async (feedback?: string): Promise<void> => {
    const { error, componentStack } = this.state;

    if (!error) {
      return;
    }

    try {
      await sendErrorReport(buildErrorReport(error, componentStack, this.props.component, feedback));
    } catch (reportError) {
      console.error('Error reporting failed:', reportError);
    }
  };

  private resetError = (): void => {
    this.setState(INITIAL_STATE);
  };

  render(): React.ReactNode {
    const { children, fallback: FallbackComponent } = this.props;
    const { hasError, error, rawError, retryCount, isRecovering, componentStack } = this.state;

    if (hasError && rawError) {
      const Fallback = FallbackComponent || DefaultErrorFallback;

      return (
        <Fallback
          error={rawError}
          errorInfo={error}
          onRetry={this.handleRetry}
          onRecovery={this.handleRecovery}
          onReport={this.handleReport}
          retryCount={retryCount}
          maxRetries={this.props.maxRetries || 3}
          isRecovering={isRecovering}
          componentStack={componentStack}
          reset={this.resetError}
        />
      );
    }

    return children;
  }
}

export const useErrorBoundary = (): UseErrorBoundaryReturn => {
  const [error, setError] = useState<ErrorHandlingInfo | null>(null);
  const [componentStack, setComponentStack] = useState<string[]>([]);
  const [retryCount, setRetryCount] = useState(0);
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryAttempts, setRecoveryAttempts] = useState<RecoveryAttempt[]>([]);

  const reset = useCallback(() => {
    setError(null);
    setComponentStack([]);
    setRetryCount(0);
    setIsRecovering(false);
    setRecoveryAttempts([]);
  }, []);

  const retry = useCallback(async () => {
    if (!error || isRecovering) {
      return;
    }

    setIsRecovering(true);

    try {
      await wait(1000);
      setError(null);
      setComponentStack([]);
      setRetryCount((prev) => prev + 1);
      setIsRecovering(false);
      setRecoveryAttempts([]);
    } catch (retryError) {
      console.error('Retry failed:', retryError);
      setIsRecovering(false);
    }
  }, [error, isRecovering, reset]);

  const recover = useCallback(async () => {
    if (!error || isRecovering) {
      return;
    }

    setIsRecovering(true);

    try {
      const result = await attemptErrorRecovery(error);
      setRecoveryAttempts([
        ...result.failedActions,
        ...result.successfulActions,
      ]);

      if (result.finalStatus === 'success') {
        reset();
      } else {
        setIsRecovering(false);
      }
    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
      setIsRecovering(false);
    }
  }, [error, isRecovering, reset]);

  return {
    error,
    reset,
    retry,
    recover,
    componentStack,
    retryCount,
    isRecovering,
    recoveryAttempts,
  };
};

export default ErrorBoundary;
