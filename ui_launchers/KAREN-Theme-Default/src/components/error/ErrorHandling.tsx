"use client";

/**
 * Error Handling Example – Comprehensive demo of:
 * - Global & API error boundaries
 * - Service-layer retry/fallback handling
 * - Toast surfacing with retry actions
 */

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import GlobalErrorBoundary from "@/components/error/GlobalErrorBoundary";
import { ApiErrorBoundary } from "@/components/error/ApiErrorBoundary";
import {
  ErrorToastContainer,
  type ErrorToastProps,
} from "@/components/error/ErrorToast";
import { enhancedApiClient } from "@/lib/enhanced-api-client";
import { getServiceErrorHandler } from "@/services/errorHandler";

// Icons
import { AlertCircle, Network, ShieldX, RefreshCw, CheckCircle2, Info, Bug, Trash2, KeyRound } from "lucide-react";

// Example component that throws different error shapes
const ComponentThatThrows = ({ errorType }: { errorType: string }) => {
  switch (errorType) {
    case "generic": {
      throw new Error("Generic component error");
    }
    case "api": {
      const apiError = new Error("API request failed") as unknown;
      apiError.name = "ApiError";
      apiError.status = 500;
      apiError.endpoint = "/api/example";
      throw apiError;
    }
    case "network": {
      const networkError = new Error("Network connection failed") as unknown;
      networkError.isNetworkError = true;
      throw networkError;
    }
    case "auth": {
      const authError = new Error("Unauthorized access") as unknown;
      authError.status = 401;
      throw authError;
    }
    default:
      return <div>No error thrown</div>;
  }
};

const ErrorHandlingExample: React.FC = () => {
  const [errorType, setErrorType] = useState<string>("none");
  const [showApiError, setShowApiError] = useState(false);
  const [toasts, setToasts] = useState<ErrorToastProps[]>([]);

  // ---- Toast helpers (replace with your useErrorToast / toast hook) ----
  const pushToast = (
    payload: Omit<ErrorToastProps, "id"> & { id?: string }
  ) => {
    const id =
      payload.id ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { ...payload, id }]);
  };
  const removeToast = (id: string) =>
    setToasts((prev) => prev.filter((toast) => toast.id !== id));

  const showError = (message: string, options?: Partial<ErrorToastProps>) =>
    pushToast({
      message,
      type: "error",
      ...options,
    });
  const showServiceError = (
    error: unknown,
    options?: Partial<ErrorToastProps>
  ) =>
    pushToast({
      message: error instanceof Error ? error.message : "Service error",
      type: "error",
      ...options,
    });
  const showWarning = (message: string, options?: Partial<ErrorToastProps>) =>
    pushToast({ message, type: "warning", ...options });
  const showInfo = (message: string, options?: Partial<ErrorToastProps>) =>
    pushToast({ message, type: "info", ...options });
  const showSuccess = (
    message: string,
    options?: Partial<ErrorToastProps>
  ) =>
    pushToast({ message, type: "success", ...options });

  // -------------------------------------------------------------------------
  const apiClient = enhancedApiClient; // ensure import is used for lint; not strictly required here
  void apiClient;

  const errorHandler = getServiceErrorHandler();

  const handleApiCall = async (shouldFail: boolean = false) => {
    try {
      if (shouldFail) {
        // Simulated API failure path
        throw new Error("Simulated API failure");
      }
      // Simulated success
      await new Promise((resolve) => setTimeout(resolve, 750));
      showSuccess("API call completed successfully!", { title: "Success" });
    } catch (err) {
      const serviceError = errorHandler.handleError(err, {
        service: "ExampleService",
        method: "handleApiCall",
        endpoint: "/api/example",
      });

      showServiceError(serviceError, {
        title: "API Error",
        actionLabel: "Retry",
        onAction: () => {
          void handleApiCall(false);
        },
      });
    }
  };

  const handleServiceCall = async () => {
    try {
      await errorHandler.withRetry(
        async () => {
          // Simulate a flaky service that often fails before succeeding
          const random = Math.random();
          if (random < 0.7) {
            throw new Error("Service temporarily unavailable");
          }
          return "Service call successful";
        },
        {
          service: "ExampleService",
          method: "handleServiceCall",
        }
      );

      showSuccess("Service call completed with retry logic!", { title: "Retried Successfully" });
    } catch (err) {
      showError("Service call failed after retries", {
        title: "Service Error",
        actionLabel: "Retry now",
        onAction: () => {
          void handleServiceCall();
        },
      });
    }
  };

  const handleFallbackCall = async () => {
    const result = await errorHandler.withFallback(
      async () => {
        throw new Error("This always fails");
      },
      "Fallback data used",
      {
        service: "ExampleService",
        method: "handleFallbackCall",
      }
    );

    showInfo(`Result: ${result}`, { title: "Fallback Used" });
  };

  const resetErrors = () => {
    setErrorType("none");
    setShowApiError(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Error Handling System Demo</CardTitle>
          <CardDescription>Boundaries, service strategies, and toasts working together.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Error Boundaries */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Error Boundaries</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Global Error Boundary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2"><Bug className="h-4 w-4"/> Global Error Boundary</CardTitle>
                  <CardDescription>Catches unhandled React errors</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => setErrorType("generic")}>
                        <AlertCircle className="h-4 w-4 mr-2"/> Throw Generic
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setErrorType("auth")}>
                        <KeyRound className="h-4 w-4 mr-2"/> Throw Auth (401)
                      </Button>
                      <Button size="sm" variant="secondary" onClick={resetErrors}>
                        <CheckCircle2 className="h-4 w-4 mr-2"/> Reset
                      </Button>
                    </div>

                    <div className="min-h-[100px] border rounded p-3">
                      <GlobalErrorBoundary showIntelligentResponse enableSessionRecovery>
                        <ComponentThatThrows errorType={errorType} />
                      </GlobalErrorBoundary>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* API Error Boundary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2"><ShieldX className="h-4 w-4"/> API Error Boundary</CardTitle>
                  <CardDescription>Specialized for API-related errors</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => setShowApiError(true)}>
                        <AlertCircle className="h-4 w-4 mr-2"/> Trigger API Error
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setShowApiError(false)}>
                        <CheckCircle2 className="h-4 w-4 mr-2"/> Clear
                      </Button>
                    </div>

                    <div className="min-h-[100px] border rounded p-3">
                      <ApiErrorBoundary showNetworkStatus autoRetry maxRetries={3}>
                        {showApiError ? (
                          <ComponentThatThrows errorType="api" />
                        ) : (
                          <div className="text-sm text-muted-foreground flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4"/> API component working normally
                          </div>
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
                onClick={() =>
                  showError("This is an error message", {
                    title: "Error Occurred",
                    actionLabel: "Retry",
                    onAction: () => {
                      void (async () => {
                        await new Promise((resolve) => setTimeout(resolve, 600));
                        showSuccess("Retry successful!", { title: "Recovered" });
                      })();
                    },
                  })
                }
              >
                <AlertCircle className="h-4 w-4 mr-2"/> Error
              </Button>

              <Button
                variant="outline"
                onClick={() =>
                  showWarning("This is a warning message", { title: "Warning", persistent: true })
                }
              >
                <Network className="h-4 w-4 mr-2"/> Warning
              </Button>

              <Button
                variant="secondary"
                onClick={() => showInfo("This is an info message", { title: "Information" })}
              >
                <Info className="h-4 w-4 mr-2"/> Info
              </Button>

              <Button variant="default" onClick={() => showSuccess("This is a success message", { title: "Success" })}>
                <CheckCircle2 className="h-4 w-4 mr-2"/> Success
              </Button>
            </div>
          </div>

          <Separator />

          {/* Service Error Handling */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Service Error Handling</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button onClick={() => handleApiCall(true)} className="flex flex-col items-center p-4 h-auto">
                <span className="font-medium flex items-center gap-2"><RefreshCw className="h-4 w-4"/> API Call with Retry</span>
                <span className="text-xs opacity-75">Shows service error with retry option</span>
              </Button>

              <Button onClick={handleServiceCall} className="flex flex-col items-center p-4 h-auto" variant="outline">
                <span className="font-medium flex items-center gap-2"><RefreshCw className="h-4 w-4"/> Service with Auto-Retry</span>
                <span className="text-xs opacity-75">Automatic retry logic in service layer</span>
              </Button>

              <Button onClick={handleFallbackCall} className="flex flex-col items-center p-4 h-auto" variant="secondary">
                <span className="font-medium flex items-center gap-2"><Trash2 className="h-4 w-4"/> Service with Fallback</span>
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
                          // NOTE: In your real app, use the toast manager's clear() method.
                          setToasts([]);
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
                      <Badge variant="outline">{errorHandler.getErrorStats().total}</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Circuit Breakers:</span>
                      <Badge variant="outline">{0}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Toast Container */}
      <ErrorToastContainer toasts={toasts} onRemove={removeToast} position="top-right" maxToasts={5} />
    </div>
  );
};

export default ErrorHandlingExample;
