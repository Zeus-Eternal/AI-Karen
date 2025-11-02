/**
 * Demo component showing comprehensive error handling in action
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

'use client';

import React, { useState, useCallback } from 'react';
import { 
  errorHandler, 
  handleError, 
  withErrorHandling, 
  ErrorCategory,
  ErrorSeverity,
  type CategorizedError,
  type ErrorHandlingResult 
} from '@/lib/errors';

interface ErrorDemoState {
  isLoading: boolean;
  lastError: ErrorHandlingResult | null;
  successMessage: string;
  errorHistory: CategorizedError[];
}

export function ErrorHandlingDemo() {
  const [state, setState] = useState<ErrorDemoState>({
    isLoading: false,
    lastError: null,
    successMessage: '',
    errorHistory: []
  });

  const updateState = useCallback((updates: Partial<ErrorDemoState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Demo functions that simulate different types of errors
  const simulateNetworkError = withErrorHandling(async () => {
    throw new Error('ECONNREFUSED: Connection refused');
  }, {
    maxRetryAttempts: 3,
    enableRecovery: true,
    context: { demo: 'network-error' }
  });

  const simulateAuthError = withErrorHandling(async () => {
    throw new Error('Session expired - please log in again');
  }, {
    maxRetryAttempts: 2,
    enableRecovery: true,
    context: { demo: 'auth-error' }
  });

  const simulateDatabaseError = withErrorHandling(async () => {
    throw new Error('Database connection pool exhausted');
  }, {
    maxRetryAttempts: 5,
    enableRecovery: true,
    context: { demo: 'database-error' }
  });

  const simulateTimeoutError = withErrorHandling(async () => {
    throw new Error('Request timed out after 30 seconds');
  }, {
    maxRetryAttempts: 3,
    enableRecovery: true,
    context: { demo: 'timeout-error' }
  });

  const simulateValidationError = async () => {
    const result = await handleError(new Error('Validation failed: required field missing'), {
      enableRecovery: false,
      context: { demo: 'validation-error' }
    });
    return result;
  };

  const simulateConfigError = async () => {
    const result = await handleError(new Error('Invalid backend URL configuration'), {
      enableRecovery: false,
      context: { demo: 'config-error' }
    });
    return result;
  };

  const handleErrorDemo = async (demoFunction: () => Promise<any>, errorType: string) => {
    updateState({ isLoading: true, lastError: null, successMessage: '' });

    try {
      const result = await demoFunction();
      updateState({
        isLoading: false,
        successMessage: `${errorType} demo completed successfully!`,
        lastError: null
      });
    } catch (error) {
      const errorResult = await handleError(error as Error, {
        enableRecovery: true,
        context: { demo: errorType }
      });

      setState(prev => ({
        ...prev,
        isLoading: false,
        lastError: errorResult,
        errorHistory: [...prev.errorHistory.slice(-9), errorResult.categorizedError]
      }));
    }
  };

  const handleDirectErrorDemo = async (demoFunction: () => Promise<ErrorHandlingResult>, errorType: string) => {
    updateState({ isLoading: true, lastError: null, successMessage: '' });

    const errorResult = await demoFunction();
    setState(prev => ({
      ...prev,
      isLoading: false,
      lastError: errorResult,
      errorHistory: [...prev.errorHistory.slice(-9), errorResult.categorizedError]
    }));
  };

  const clearHistory = () => {
    updateState({ errorHistory: [], lastError: null, successMessage: '' });
  };

  const getSeverityColor = (severity: ErrorSeverity) => {
    switch (severity) {
      case ErrorSeverity.CRITICAL: return 'text-red-600 bg-red-50';
      case ErrorSeverity.HIGH: return 'text-orange-600 bg-orange-50';
      case ErrorSeverity.MEDIUM: return 'text-yellow-600 bg-yellow-50';
      case ErrorSeverity.LOW: return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getCategoryColor = (category: ErrorCategory) => {
    switch (category) {
      case ErrorCategory.NETWORK: return 'bg-purple-100 text-purple-800';
      case ErrorCategory.AUTHENTICATION: return 'bg-red-100 text-red-800';
      case ErrorCategory.DATABASE: return 'bg-orange-100 text-orange-800';
      case ErrorCategory.CONFIGURATION: return 'bg-gray-100 text-gray-800';
      case ErrorCategory.TIMEOUT: return 'bg-yellow-100 text-yellow-800';
      case ErrorCategory.VALIDATION: return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Comprehensive Error Handling Demo
        </h1>
        <p className="text-gray-600 mb-6">
          This demo showcases the comprehensive error handling system with categorization, 
          recovery strategies, and user-friendly messaging.
        </p>

        {/* Demo Controls */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <button
            onClick={() => handleErrorDemo(simulateNetworkError, 'Network Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            Network Error
          </button>
          
          <button
            onClick={() => handleErrorDemo(simulateAuthError, 'Auth Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            Auth Error
          </button>
          
          <button
            onClick={() => handleErrorDemo(simulateDatabaseError, 'Database Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50"
          >
            Database Error
          </button>
          
          <button
            onClick={() => handleErrorDemo(simulateTimeoutError, 'Timeout Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50"
          >
            Timeout Error
          </button>
          
          <button
            onClick={() => handleDirectErrorDemo(simulateValidationError, 'Validation Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            Validation Error
          </button>
          
          <button
            onClick={() => handleDirectErrorDemo(simulateConfigError, 'Config Error')}
            disabled={state.isLoading}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
          >
            Config Error
          </button>
        </div>

        {/* Loading State */}
        {state.isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Processing error demo...</span>
          </div>
        )}

        {/* Success Message */}
        {state.successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">
                  {state.successMessage}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Current Error Display */}
        {state.lastError && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Latest Error Result</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Error Details</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Category:</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getCategoryColor(state.lastError.categorizedError.category)}`}>
                      {state.lastError.categorizedError.category}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Severity:</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getSeverityColor(state.lastError.categorizedError.severity)}`}>
                      {state.lastError.categorizedError.severity}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Code:</span>
                    <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                      {state.lastError.categorizedError.code}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Retryable:</span>
                    <span className={`ml-2 ${state.lastError.categorizedError.retryable ? 'text-green-600' : 'text-red-600'}`}>
                      {state.lastError.categorizedError.retryable ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Recovery & User Experience</h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">User Message:</span>
                    <p className="mt-1 text-gray-600 italic">"{state.lastError.userMessage}"</p>
                  </div>
                  <div>
                    <span className="font-medium">Requires User Action:</span>
                    <span className={`ml-2 ${state.lastError.requiresUserAction ? 'text-orange-600' : 'text-green-600'}`}>
                      {state.lastError.requiresUserAction ? 'Yes' : 'No'}
                    </span>
                  </div>
                  {state.lastError.recoveryResult && (
                    <div>
                      <span className="font-medium">Recovery Action:</span>
                      <span className="ml-2 font-mono text-xs bg-blue-100 px-2 py-1 rounded">
                        {state.lastError.recoveryResult.actionTaken}
                      </span>
                    </div>
                  )}
                  {state.lastError.retryDelay && (
                    <div>
                      <span className="font-medium">Retry Delay:</span>
                      <span className="ml-2">{state.lastError.retryDelay}ms</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error History */}
        {state.errorHistory.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Error History</h3>
              <button
                onClick={clearHistory}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
              >
                Clear History
              </button>
            </div>
            
            <div className="space-y-2">
              {state.errorHistory.map((error, index) => (
                <div key={error.code} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-500">#{state.errorHistory.length - index}</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getCategoryColor(error.category)}`}>
                      {error.category}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getSeverityColor(error.severity)}`}>
                      {error.severity}
                    </span>
                    <span className="text-sm text-gray-700 truncate max-w-md">
                      {error.message}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span>{error.timestamp.toLocaleTimeString()}</span>
                    <span className="font-mono">{error.code.slice(-8)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}