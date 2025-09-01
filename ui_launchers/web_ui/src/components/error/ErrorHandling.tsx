/**
 * Error Handling Example - Demonstrates comprehensive error handling system
 * Shows how to use error boundaries, toasts, and service error handling together
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  GlobalErrorBoundary, 
  ApiErrorBoundary, 
  ErrorToastContainer
} from './index';
import { getEnhancedApiClient } from '@/lib/enhanced-api-client';
import { getServiceErrorHandler } from '@/services/errorHandler';

// Example components that can throw different types of errors
const ComponentThatThrows = ({ errorType }: { errorType: string }) => {
  switch (errorType) {
    case 'generic':
      throw new Error('Generic component error');
    case 'api':
      const apiError = new Error('API request failed') as any;
      apiError.name = 'ApiError';
      apiError.status = 500;
      apiError.endpoint = '/api/example';
      throw apiError;
    case 'network':
      const networkError = new Error('Network connection failed') as any;
      networkError.isNetworkError = true;
      throw networkError;
    case 'auth':
      const authError = new Error('Unauthorized access') as any;
      authError.status = 401;
      throw authError;
    default:
      return <div>No error thrown</div>;
  }
};

const ErrorHandlingExample: React.FC = () => {
  const [errorType, setErrorType] = useState<string>('none');
  const [showApiError, setShowApiError] = useState(false);
  const [toasts, setToasts] = useState<any[]>([]);
  
  // Mock implementation of toast functions - replace with actual useErrorToast hook
  const showError = (message: string, options?: any) => {
    const toast = { id: Date.now().toString(), message, type: 'error', ...options };
    setToasts(prev => [...prev, toast]);
  };
  
  const showServiceError = (error: any, options?: any) => {
    const toast = { id: Date.now().toString(), message: error.message || 'Service error', type: 'error', ...options };
    setToasts(prev => [...prev, toast]);
  };
  
  const showWarning = (message: string, options?: any) => {
    const toast = { id: Date.now().toString(), message, type: 'warning', ...options };
    setToasts(prev => [...prev, toast]);
  };
  
  const showInfo = (message: string, options?: any) => {
    const toast = { id: Date.now().toString(), message, type: 'info', ...options };
    setToasts(prev => [...prev, toast]);
  };
  
  const showSuccess = (message: string, options?: any) => {
    const toast = { id: Date.now().toString(), message, type: 'success', ...options };
    setToasts(prev => [...prev, toast]);
  };
  
  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };
  
  const enhancedApiClient = getEnhancedApiClient();
  const errorHandler = getServiceErrorHandler();

  const handleApiCall = async (shouldFail: boolean = false) => {
    try {
      if (shouldFail) {
        // Simulate API failure
        throw new Error('Simulated API failure');
      }
      
      // Simulate successful API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      showSuccess('API call completed successfully!');
    } catch (error) {
      const serviceError = errorHandler.handleError(error, {
        service: 'ExampleService',
        method: 'handleApiCall',
        endpoint: '/api/example',
      });
      
      showServiceError(serviceError, {
        enableRetry: true,
        onRetry: async () => {
          await handleApiCall(false); // Retry with success
        },
      });
    }
  };

  const handleServiceCall = async () => {
    try {
      await errorHandler.withRetry(
        async () => {
          // Simulate service that fails twice then succeeds
          const random = Math.random();
          if (random < 0.7) {
            throw new Error('Service temporarily unavailable');
          }
          return 'Service call successful';
        },
        {
          service: 'ExampleService',
          method: 'handleServiceCall',
        }
      );
      
      showSuccess('Service call completed with retry logic!');
    } catch (error) {
      showError('Service call failed after retries', {
        error: error instanceof Error ? error : new Error('Unknown error'),
        showIntelligentResponse: true,
      });
    }
  };

  const handleFallbackCall = async () => {
    const result = await errorHandler.withFallback(
      async () => {
        throw new Error('This always fails');
      },
      'Fallback data used',
      {
        service: 'ExampleService',
        method: 'handleFallbackCall',
      }
    );
    
    showInfo(`Result: ${result}`, {
      title: 'Fallback Used',
    });
  };

  const resetErrors = () => {
    setErrorType('none');
    setShowApiError(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Error Handling System Demo</CardTitle>
          <CardDescription>
            Comprehensive demonstration of error boundaries, toast notifications, and service error handling
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Error Boundary Examples */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Error Boundaries</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Global Error Boundary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Global Error Boundary</CardTitle>
                  <CardDescription>Catches all unhandled React errors</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setErrorType('generic')}
                      >
                        Generic Error
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setErrorType('auth')}
                      >
                        Auth Error
                      </Button>
                      <Button 
                        size="sm" 
                        variant="secondary"
                        onClick={resetErrors}
                      >
                        Reset
                      </Button>
                    </div>
                    
                    <div className="min-h-[100px] border rounded p-3">
                      <GlobalErrorBoundary 
                        showIntelligentResponse={true}
                        enableSessionRecovery={true}
                      >
                        <ComponentThatThrows errorType={errorType} />
                      </GlobalErrorBoundary>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* API Error Boundary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">API Error Boundary</CardTitle>
                  <CardDescription>Specialized for API-related errors</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setShowApiError(true)}
                      >
                        API Error
                      </Button>
                      <Button 
                        size="sm" 
                        variant="secondary"
                        onClick={() => setShowApiError(false)}
                      >
                        Reset
                      </Button>
                    </div>
                    
                    <div className="min-h-[100px] border rounded p-3">
                      <ApiErrorBoundary 
                        showNetworkStatus={true}
                        autoRetry={true}
                        maxRetries={3}
                      >
                        {showApiError ? (
                          <ComponentThatThrows errorType="api" />
                        ) : (
                          <div>API component working normally</div>
                        )}
                      </ApiErrorBoundary>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <Separator />

          {/* Toast Notifications */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Toast Notifications</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Button 
                variant="destructive" 
                onClick={() => showError('This is an error message', {
                  title: 'Error Occurred',
                  enableRetry: true,
                  onRetry: async () => {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    showSuccess('Retry successful!');
                  },
                })}
              >
                Show Error
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => showWarning('This is a warning message', {
                  title: 'Warning',
                  persistent: true,
                })}
              >
                Show Warning
              </Button>
              
              <Button 
                variant="secondary" 
                onClick={() => showInfo('This is an info message', {
                  title: 'Information',
                })}
              >
                Show Info
              </Button>
              
              <Button 
                variant="default" 
                onClick={() => showSuccess('This is a success message', {
                  title: 'Success',
                })}
              >
                Show Success
              </Button>
            </div>
          </div>

          <Separator />

          {/* Service Error Handling */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Service Error Handling</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button 
                onClick={() => handleApiCall(true)}
                className="flex flex-col items-center p-4 h-auto"
              >
                <span className="font-medium">API Call with Retry</span>
                <span className="text-xs opacity-75">Shows service error with retry option</span>
              </Button>
              
              <Button 
                onClick={handleServiceCall}
                className="flex flex-col items-center p-4 h-auto"
                variant="outline"
              >
                <span className="font-medium">Service with Auto-Retry</span>
                <span className="text-xs opacity-75">Automatic retry logic in service layer</span>
              </Button>
              
              <Button 
                onClick={handleFallbackCall}
                className="flex flex-col items-center p-4 h-auto"
                variant="secondary"
              >
                <span className="font-medium">Service with Fallback</span>
                <span className="text-xs opacity-75">Uses fallback value on error</span>
              </Button>
            </div>
          </div>

          <Separator />

          {/* System Status */}
          <div>
            <h3 className="text-lg font-semibold mb-3">System Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Active Toasts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{toasts.length} active</Badge>
                    {toasts.length > 0 && (
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => {
                          // Clear all toasts (implementation depends on your toast manager)
                          window.location.reload();
                        }}
                      >
                        Clear All
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Error Handler Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Total Errors:</span>
                      <Badge variant="outline">
                        {errorHandler.getErrorStats().total}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Circuit Breakers:</span>
                      <Badge variant="outline">
                        {enhancedApiClient.getCircuitBreakerStates().size}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Toast Container */}
      <ErrorToastContainer 
        toasts={toasts} 
        onRemove={removeToast}
        position="top-right"
        maxToasts={5}
      />
    </div>
  );
};

export default ErrorHandlingExample;