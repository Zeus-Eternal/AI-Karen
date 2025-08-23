/**
 * Higher-Order Component for Intelligent Error Detection
 * 
 * Wraps components with automatic error detection and intelligent response display.
 * Provides seamless integration of intelligent error handling into existing components.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

import React, { ComponentType, useEffect, useState } from 'react';
import { IntelligentErrorPanel, IntelligentErrorPanelProps } from './IntelligentErrorPanel';
import { useIntelligentError, UseIntelligentErrorOptions } from '@/hooks/use-intelligent-error';

export interface WithIntelligentErrorOptions extends UseIntelligentErrorOptions {
  /**
   * Whether to show the error panel automatically when an error is detected
   */
  autoShow?: boolean;
  
  /**
   * Position of the error panel relative to the wrapped component
   */
  position?: 'top' | 'bottom' | 'overlay';
  
  /**
   * Whether to replace the component content with the error panel when an error occurs
   */
  replaceOnError?: boolean;
  
  /**
   * Custom error panel props
   */
  errorPanelProps?: Partial<IntelligentErrorPanelProps>;
  
  /**
   * Custom error detection function
   */
  detectError?: (props: any, prevProps?: any) => Error | string | null;
  
  /**
   * Whether to monitor prop changes for errors
   */
  monitorProps?: boolean;
  
  /**
   * Props to monitor for error conditions
   */
  errorProps?: string[];
}

export interface WithIntelligentErrorProps {
  /**
   * Error to analyze (can be passed as prop)
   */
  error?: Error | string;
  
  /**
   * Whether to show the intelligent error panel
   */
  showIntelligentError?: boolean;
  
  /**
   * Callback when error panel is dismissed
   */
  onErrorDismiss?: () => void;
  
  /**
   * Additional context for error analysis
   */
  errorContext?: Record<string, any>;
}

/**
 * Higher-order component that adds intelligent error detection and display
 */
export function withIntelligentError<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: WithIntelligentErrorOptions = {}
) {
  const {
    autoShow = true,
    position = 'top',
    replaceOnError = false,
    errorPanelProps = {},
    detectError,
    monitorProps = true,
    errorProps = ['error', 'errorMessage', 'hasError'],
    ...intelligentErrorOptions
  } = options;

  const WithIntelligentErrorComponent: React.FC<P & WithIntelligentErrorProps> = (props) => {
    const {
      error: propError,
      showIntelligentError,
      onErrorDismiss,
      errorContext,
      ...wrappedProps
    } = props as P & WithIntelligentErrorProps;

    const [showPanel, setShowPanel] = useState(false);
    const [detectedError, setDetectedError] = useState<Error | string | null>(null);

    const intelligentError = useIntelligentError({
      ...intelligentErrorOptions,
      onAnalysisComplete: (analysis) => {
        if (autoShow) {
          setShowPanel(true);
        }
        intelligentErrorOptions.onAnalysisComplete?.(analysis);
      },
    });

    /**
     * Detect errors from props
     */
    useEffect(() => {
      let errorToAnalyze: Error | string | null = null;

      // Check explicit error prop
      if (propError) {
        errorToAnalyze = propError;
      }
      // Use custom error detection function
      else if (detectError) {
        errorToAnalyze = detectError(props);
      }
      // Monitor specific error props
      else if (monitorProps && errorProps.length > 0) {
        for (const errorProp of errorProps) {
          const value = (props as any)[errorProp];
          if (value) {
            if (typeof value === 'string' || value instanceof Error) {
              errorToAnalyze = value;
              break;
            } else if (typeof value === 'boolean' && value === true) {
              // Look for associated error message
              const messageProp = errorProp.replace(/^(has|is)/, '').toLowerCase() + 'Message';
              const message = (props as any)[messageProp];
              if (message) {
                errorToAnalyze = message;
                break;
              } else {
                errorToAnalyze = `Error detected in ${errorProp}`;
                break;
              }
            }
          }
        }
      }

      // Analyze error if detected and different from previous
      if (errorToAnalyze && errorToAnalyze !== detectedError) {
        setDetectedError(errorToAnalyze);
        intelligentError.analyzeError(errorToAnalyze, {
          user_context: {
            component: WrappedComponent.displayName || WrappedComponent.name,
            props: errorContext,
            ...errorContext,
          },
        });
      } else if (!errorToAnalyze && detectedError) {
        // Clear error if no longer present
        setDetectedError(null);
        setShowPanel(false);
        intelligentError.clearAnalysis();
      }
    }, [props, propError, detectError, monitorProps, errorProps, detectedError, errorContext, intelligentError]);

    /**
     * Handle error panel dismissal
     */
    const handleDismiss = () => {
      setShowPanel(false);
      onErrorDismiss?.();
    };

    /**
     * Handle retry from error panel
     */
    const handleRetry = () => {
      // Clear the detected error to allow re-detection
      setDetectedError(null);
      setShowPanel(false);
      intelligentError.clearAnalysis();
      
      // If the wrapped component has a retry mechanism, we could call it here
      // This would need to be passed as a prop or option
    };

    // Determine if we should show the error panel
    const shouldShowPanel = (showIntelligentError !== undefined ? showIntelligentError : showPanel) && 
                           (intelligentError.analysis || intelligentError.isAnalyzing);

    // If replaceOnError is true and we have an error, show only the error panel
    if (replaceOnError && shouldShowPanel) {
      return (
        <IntelligentErrorPanel
          error={detectedError || 'Unknown error'}
          onDismiss={handleDismiss}
          onRetry={handleRetry}
          autoFetch={false} // We're already handling analysis
          {...errorPanelProps}
        />
      );
    }

    // Render component with error panel positioned as specified
    return (
      <div className="relative">
        {/* Error panel at top */}
        {position === 'top' && shouldShowPanel && (
          <div className="mb-4">
            <IntelligentErrorPanel
              error={detectedError || 'Unknown error'}
              onDismiss={handleDismiss}
              onRetry={handleRetry}
              autoFetch={false} // We're already handling analysis
              {...errorPanelProps}
            />
          </div>
        )}

        {/* Overlay error panel */}
        {position === 'overlay' && shouldShowPanel && (
          <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-2xl">
              <IntelligentErrorPanel
                error={detectedError || 'Unknown error'}
                onDismiss={handleDismiss}
                onRetry={handleRetry}
                autoFetch={false} // We're already handling analysis
                {...errorPanelProps}
              />
            </div>
          </div>
        )}

        {/* Wrapped component */}
        <WrappedComponent {...(wrappedProps as P)} />

        {/* Error panel at bottom */}
        {position === 'bottom' && shouldShowPanel && (
          <div className="mt-4">
            <IntelligentErrorPanel
              error={detectedError || 'Unknown error'}
              onDismiss={handleDismiss}
              onRetry={handleRetry}
              autoFetch={false} // We're already handling analysis
              {...errorPanelProps}
            />
          </div>
        )}
      </div>
    );
  };

  WithIntelligentErrorComponent.displayName = `withIntelligentError(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithIntelligentErrorComponent;
}

/**
 * Decorator version for class components
 */
export function intelligentErrorDecorator(options: WithIntelligentErrorOptions = {}) {
  return function <P extends object>(WrappedComponent: ComponentType<P>) {
    return withIntelligentError(WrappedComponent, options);
  };
}

export default withIntelligentError;