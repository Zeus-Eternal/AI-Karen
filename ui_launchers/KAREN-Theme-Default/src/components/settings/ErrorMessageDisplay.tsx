"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useToast } from "@/hooks/use-toast";

import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Info,
  Lightbulb,
  RefreshCw,
  Search,
  Wrench,
} from "lucide-react";

export interface ErrorContext {
  provider: string;
  model?: string;
  request_type?: string;
  timestamp: string;
  user_action?: string;
  system_state?: Record<string, unknown>;
}

export interface ErrorSolution {
  id: string;
  title: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  estimated_time: string;
  success_rate: number;
  steps: Array<{
    step_number: number;
    title: string;
    description: string;
    command?: string;
    warning?: string;
    verification?: string;
  }>;
  related_links?: Array<{
    title: string;
    url: string;
    type: "documentation" | "tutorial" | "community";
  }>;
  prerequisites?: string[];
}

export interface ErrorInfo {
  error_type: string;
  error_code?: string;
  message?: string;
  user_friendly_message: string;
  technical_details?: string;
  context?: ErrorContext;
  possible_causes: string[];
  solutions: ErrorSolution[];
  related_errors?: string[];
  prevention_tips: string[];
}

export interface ErrorMessageDisplayProps {
  error: Error | string;
  context?: Partial<ErrorContext>;
  onRetry?: () => void;
  onDismiss?: () => void;
  showTechnicalDetails?: boolean;
  showSolutions?: boolean;
}

// Mock error database - in real implementation, fetch from backend
const ERROR_DATABASE: Record<string, Partial<ErrorInfo>> = {
  API_KEY_INVALID: {
    error_type: "Authentication Error",
    error_code: "API_KEY_INVALID",
    user_friendly_message: "Your API key is invalid or has expired.",
    possible_causes: [
      "API key was copied incorrectly",
      "API key has expired or been revoked",
      "API key doesn't have the required permissions",
      "Wrong API key for the selected provider",
    ],
    solutions: [
      {
        id: "verify_api_key",
        title: "Verify and Update API Key",
        description: "Check and update your API key configuration",
        difficulty: "easy",
        estimated_time: "2-3 minutes",
        success_rate: 95,
        steps: [
          {
            step_number: 1,
            title: "Check API Key Format",
            description: "Ensure your API key follows the correct format for your provider",
            verification: "API key should start with the provider-specific prefix",
          },
          {
            step_number: 2,
            title: "Verify API Key in Provider Dashboard",
            description: "Log into your provider dashboard and verify the API key is active",
            warning: "API keys are only shown once when created",
          },
          {
            step_number: 3,
            title: "Update API Key in Settings",
            description: "Copy the correct API key and paste it in the provider settings",
            verification: "Wait for the green checkmark indicating successful validation",
          },
        ],
        related_links: [
          {
            title: "OpenAI API Keys",
            url: "https://platform.openai.com/api-keys",
            type: "documentation",
          },
        ],
      },
    ],
    prevention_tips: [
      "Store API keys securely and never share them",
      "Regularly rotate API keys for security",
      "Monitor API key usage in provider dashboards",
      "Set up billing alerts to avoid service interruptions",
    ],
  },
  NETWORK_TIMEOUT: {
    error_type: "Network Error",
    error_code: "NETWORK_TIMEOUT",
    user_friendly_message: "The request timed out while trying to connect to the provider.",
    possible_causes: [
      "Slow internet connection",
      "Provider service is experiencing high load",
      "Firewall or proxy blocking the connection",
      "DNS resolution issues",
    ],
    solutions: [
      {
        id: "check_connectivity",
        title: "Check Network Connectivity",
        description: "Verify your internet connection and network settings",
        difficulty: "easy",
        estimated_time: "1-2 minutes",
        success_rate: 80,
        steps: [
          {
            step_number: 1,
            title: "Test Internet Connection",
            description: "Open a web browser and visit a reliable website",
            verification: "Confirm you can access external websites",
          },
          {
            step_number: 2,
            title: "Check Provider Status",
            description: "Visit the provider's status page to check for outages",
            verification: "Confirm all services are operational",
          },
          {
            step_number: 3,
            title: "Retry Request",
            description: "Wait a moment and try your request again",
            verification: "Request completes successfully",
          },
        ],
      },
    ],
    prevention_tips: [
      "Implement retries with backoff",
      "Use a resilient DNS provider",
      "Whitelist provider endpoints through your firewall/proxy",
    ],
  },
  RATE_LIMIT_EXCEEDED: {
    error_type: "Rate Limit Error",
    error_code: "RATE_LIMIT_EXCEEDED",
    user_friendly_message: "You have exceeded the rate limit for this provider.",
    possible_causes: [
      "Too many requests sent in a short time period",
      "Exceeded monthly usage quota",
      "Using a free tier with limited requests",
      "Multiple applications using the same API key",
    ],
    solutions: [
      {
        id: "wait_and_retry",
        title: "Wait and Retry",
        description: "Wait for the rate limit to reset and try again",
        difficulty: "easy",
        estimated_time: "1-60 minutes",
        success_rate: 100,
        steps: [
          {
            step_number: 1,
            title: "Check Rate Limit Headers",
            description: "Look for rate limit reset time in the error details",
            verification: "Note when the rate limit will reset",
          },
          {
            step_number: 2,
            title: "Wait for Reset",
            description: "Wait until the rate limit reset time has passed",
            warning: "Rate limits typically reset every minute or hour",
          },
          {
            step_number: 3,
            title: "Retry Request",
            description: "Try your request again after the reset time",
            verification: "Request completes successfully",
          },
        ],
      },
    ],
    prevention_tips: [
      "Implement request throttling in your applications",
      "Monitor your API usage regularly",
      "Consider upgrading to a higher tier plan",
      "Use caching to reduce API calls",
    ],
  },
};

function detectErrorType(message: string): string {
  const lowerMessage = (message || "").toLowerCase();
  if (lowerMessage.includes("api key") || lowerMessage.includes("unauthorized") || lowerMessage.includes("401")) {
    return "API_KEY_INVALID";
  }
  if (lowerMessage.includes("timeout") || lowerMessage.includes("connection timed out")) {
    return "NETWORK_TIMEOUT";
  }
  if (lowerMessage.includes("rate limit") || lowerMessage.includes("429")) {
    return "RATE_LIMIT_EXCEEDED";
  }
  return "UNKNOWN_ERROR";
}

function createFallbackErrorInfo(message: string): Partial<ErrorInfo> {
  return {
    error_type: "Unknown Error",
    user_friendly_message: "An unexpected error occurred.",
    technical_details: message,
    possible_causes: ["Unknown cause"],
    solutions: [
      {
        id: "generic_retry",
        title: "Retry Operation",
        description: "Try the operation again after a short wait",
        difficulty: "easy",
        estimated_time: "1 minute",
        success_rate: 50,
        steps: [
          {
            step_number: 1,
            title: "Wait a Moment",
            description: "Wait 10-30 seconds before retrying",
            verification: "Allow time for temporary issues to resolve",
          },
          {
            step_number: 2,
            title: "Retry Operation",
            description: "Try the same operation again",
            verification: "Operation completes successfully",
          },
        ],
      },
    ],
    prevention_tips: ["Check system logs for more details"],
  };
}

export function ErrorMessageDisplay({
  error,
  context,
  onRetry,
  onDismiss,
  showTechnicalDetails = false,
  showSolutions = true,
}: ErrorMessageDisplayProps) {
  const [expandedSolution, setExpandedSolution] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(showTechnicalDetails);
  const { toast } = useToast();

  const errorMessage = typeof error === "string" ? error : error.message || "Unknown error";
  const errorType = detectErrorType(errorMessage);
  const errorInfo: Partial<ErrorInfo> =
    ERROR_DATABASE[errorType] || createFallbackErrorInfo(errorMessage);

  const copyToClipboard = (text: string) => {
    try {
      navigator.clipboard.writeText(text);
      toast({
        title: "Copied to Clipboard",
        description: "Error details copied successfully.",
      });
    } catch {
      toast({
        variant: "destructive",
        title: "Copy failed",
        description: "Could not copy to clipboard.",
      });
    }
  };

  const searchForSolution = (query: string) => {
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(`${query} solution`)}`;
    window.open(searchUrl, "_blank", "noopener,noreferrer");
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 80) return "text-green-600";
    if (rate >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-4">
      {/* Main Error Alert */}
      <Alert variant="destructive" role="alert">
        <AlertCircle className="h-4 w-4" aria-hidden="true" />
        <AlertTitle className="flex items-center justify-between">
          <span>{errorInfo.error_type || "Error"}</span>
          <div className="flex items-center gap-2">
            {onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry} aria-label="Retry">
                <RefreshCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(errorMessage)}
              aria-label="Copy error"
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => searchForSolution(errorMessage)}
              aria-label="Search solution"
            >
              <Search className="h-3 w-3 mr-1" />
              Search
            </Button>
          </div>
        </AlertTitle>

        <AlertDescription className="space-y-2">
          <p>{errorInfo.user_friendly_message || errorMessage}</p>

          {/* Error Context */}
          {!!context && (
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {"provider" in context && context?.provider && <p>Provider: {context.provider}</p>}
              {"model" in context && context?.model && <p>Model: {context.model}</p>}
              {"timestamp" in context && context?.timestamp && (
                <p>Time: {new Date(context.timestamp).toLocaleString()}</p>
              )}
            </div>
          )}

          {/* Technical Details Toggle */}
          <Button
            variant="link"
            size="sm"
            className="p-0 h-auto text-xs sm:text-sm md:text-base"
            onClick={() => setShowDetails((v) => !v)}
          >
            {showDetails ? "Hide" : "Show"} Technical Details
            {showDetails ? <ChevronDown className="h-3 w-3 ml-1" /> : <ChevronRight className="h-3 w-3 ml-1" />}
          </Button>

          {showDetails && (
            <div className="mt-2 p-2 bg-muted rounded text-xs sm:text-sm md:text-base">
              <p>
                <strong>Error Code:</strong> {(errorInfo as ErrorInfo).error_code || "N/A"}
              </p>
              <p>
                <strong>Technical Details:</strong>{" "}
                {(errorInfo as ErrorInfo).technical_details || errorMessage}
              </p>
              {typeof error === "object" && "stack" in error && (error as Error).stack && (
                <details className="mt-2">
                  <summary className="cursor-pointer">Stack Trace</summary>
                  <pre className="mt-1 text-xs overflow-x-auto sm:text-sm md:text-base">
                    {(error as Error).stack}
                  </pre>
                </details>
              )}
            </div>
          )}
        </AlertDescription>
      </Alert>

      {/* Possible Causes */}
      {Array.isArray((errorInfo as ErrorInfo).possible_causes) &&
        (errorInfo as ErrorInfo).possible_causes.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                <Info className="h-4 w-4" />
                Possible Causes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1 text-sm md:text-base lg:text-lg">
                {(errorInfo as ErrorInfo).possible_causes.map((cause, index) => (
                  <li key={index}>{cause}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

      {/* Solutions */}
      {showSolutions &&
        Array.isArray((errorInfo as ErrorInfo).solutions) &&
        (errorInfo as ErrorInfo).solutions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                <Wrench className="h-4 w-4" />
                Solutions
              </CardTitle>
              <CardDescription>Step-by-step solutions to resolve this error</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(errorInfo as ErrorInfo).solutions.map((solution) => (
                <Collapsible
                  key={solution.id}
                  open={expandedSolution === solution.id}
                  onOpenChange={(open) => setExpandedSolution(open ? solution.id : null)}
                >
                  <CollapsibleTrigger asChild>
                    <div className="flex items-center justify-between p-3 border rounded-lg cursor-pointer hover:bg-muted/50 sm:p-4 md:p-6">
                      <div>
                        <h4 className="font-medium">{solution.title}</h4>
                        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          {solution.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getDifficultyColor(solution.difficulty)}>{solution.difficulty}</Badge>
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {solution.estimated_time}
                        </Badge>
                        <span className={`text-xs ${getSuccessRateColor(solution.success_rate)}`}>
                          {solution.success_rate}% success
                        </span>
                        {expandedSolution === solution.id ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent className="px-3 pb-3">
                    <div className="space-y-4 mt-3">
                      {/* Prerequisites */}
                      {!!solution.prerequisites?.length && (
                        <div>
                          <h5 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Prerequisites:</h5>
                          <ul className="list-disc list-inside text-sm space-y-1 md:text-base lg:text-lg">
                            {solution.prerequisites.map((prereq, index) => (
                              <li key={index}>{prereq}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Steps */}
                      <div>
                        <h5 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Steps:</h5>
                        <div className="space-y-3">
                          {solution.steps.map((step) => (
                            <div key={step.step_number} className="border-l-2 border-primary pl-4">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                                  {step.step_number}
                                </span>
                                <h6 className="text-sm font-medium md:text-base lg:text-lg">{step.title}</h6>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                                {step.description}
                              </p>

                              {step.command && (
                                <div className="bg-muted p-2 rounded text-xs font-mono mb-2 sm:text-sm md:text-base">
                                  {step.command}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="ml-2 h-auto p-1"
                                    onClick={() => copyToClipboard(step.command!)}
                                    aria-label="Copy command"
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              )}

                              {step.warning && (
                                <Alert className="mb-2">
                                  <AlertCircle className="h-3 w-3" />
                                  <AlertDescription className="text-xs sm:text-sm md:text-base">
                                    <strong>Warning:</strong> {step.warning}
                                  </AlertDescription>
                                </Alert>
                              )}

                              {step.verification && (
                                <div className="text-xs text-green-600 bg-green-50 p-2 rounded sm:text-sm md:text-base">
                                  <strong>Verification:</strong> {step.verification}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Related Links */}
                      {!!solution.related_links?.length && (
                        <div>
                          <h5 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Related Links:</h5>
                          <div className="space-y-1">
                            {solution.related_links.map((link, index) => (
                              <Button
                                key={`${link.title}-${index}`}
                                variant="link"
                                size="sm"
                                className="p-0 h-auto text-xs sm:text-sm md:text-base"
                                onClick={() => window.open(link.url, "_blank", "noopener,noreferrer")}
                                aria-label={`Open ${link.title}`}
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                {link.title}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              ))}
            </CardContent>
          </Card>
        )}

      {/* Prevention Tips */}
      {Array.isArray((errorInfo as ErrorInfo).prevention_tips) &&
        (errorInfo as ErrorInfo).prevention_tips.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                <Lightbulb className="h-4 w-4" />
                Prevention Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1 text-sm md:text-base lg:text-lg">
                {(errorInfo as ErrorInfo).prevention_tips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

      {/* Dismiss Button */}
      {onDismiss && (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={onDismiss} aria-label="Dismiss">
            Dismiss
          </Button>
        </div>
      )}
    </div>
  );
}

export default ErrorMessageDisplay;
