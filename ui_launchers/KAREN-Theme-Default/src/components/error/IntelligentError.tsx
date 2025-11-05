// ui_launchers/KAREN-Theme-Default/src/components/error/IntelligentError.tsx
"use client";

/**
 * Intelligent Error Panel Examples
 * - Basic panel demo with selectable scenarios
 * - Hook usage for custom analysis flows
 * - API error hook demo
 * - HOC example for automatic component protection
 *
 * Requirements: 3.2, 3.3, 3.7, 4.4
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

import { IntelligentErrorPanel } from "./IntelligentErrorPanel";
import { withIntelligentError } from "./withIntelligentError";
import {
  useIntelligentError,
  useIntelligentApiError,
} from "@/hooks/use-intelligent-error";

/* ----------------------------- Scenarios ------------------------------ */

type ScenarioKey =
  | "api_key_missing"
  | "rate_limit"
  | "network_error"
  | "validation_error"
  | "system_error";

const ERROR_SCENARIOS: Record<
  ScenarioKey,
  {
    error: string;
    errorType:
      | "AuthenticationError"
      | "RateLimitError"
      | "NetworkError"
      | "ValidationError"
      | "DatabaseError"
      | string;
    statusCode: number;
    providerName: "openai" | "anthropic" | "system" | string;
    description: string;
  }
> = {
  api_key_missing: {
    error: "OpenAI API key not found",
    errorType: "AuthenticationError",
    statusCode: 401,
    providerName: "openai",
    description: "Missing API key error",
  },
  rate_limit: {
    error: "Rate limit exceeded for OpenAI API",
    errorType: "RateLimitError",
    statusCode: 429,
    providerName: "openai",
    description: "Rate limiting error",
  },
  network_error: {
    error: "Connection timeout while connecting to Anthropic",
    errorType: "NetworkError",
    statusCode: 504,
    providerName: "anthropic",
    description: "Network connectivity error",
  },
  validation_error: {
    error: "Invalid input: message cannot be empty",
    errorType: "ValidationError",
    statusCode: 400,
    providerName: "system",
    description: "Input validation error",
  },
  system_error: {
    error: "Database connection failed",
    errorType: "DatabaseError",
    statusCode: 500,
    providerName: "system",
    description: "System/database error",
  },
};

/* ----------------------------- Basic Panel ---------------------------- */

export const BasicErrorPanelExample: React.FC = () => {
  const [selectedScenario, setSelectedScenario] =
    useState<ScenarioKey>("api_key_missing");
  const [showPanel, setShowPanel] = useState(false);
  const scenario = ERROR_SCENARIOS[selectedScenario];

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Basic Intelligent Error Panel</CardTitle>
        <CardDescription>
          Select an error scenario to see how the intelligent panel analyzes and
          guides remediation.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Select
            value={selectedScenario}
            onValueChange={(v) => setSelectedScenario(v as ScenarioKey)}
          >
            <SelectTrigger className="w-72">
              <SelectValue placeholder="Choose an error scenario..." />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(ERROR_SCENARIOS).map(([key, sc]) => (
                <SelectItem key={key} value={key}>
                  {sc.description}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {!showPanel ? (
            <Button onClick={() => setShowPanel(true)}>Show Panel</Button>
          ) : (
            <Button variant="outline" onClick={() => setShowPanel(false)}>
              Hide Panel
            </Button>
          )}
        </div>

        {showPanel && (
          <IntelligentErrorPanel
            error={scenario.error}
            errorType={scenario.errorType}
            statusCode={scenario.statusCode}
            providerName={scenario.providerName}
            requestPath="/api/example"
            userContext={{ feature: "example", userId: "demo" }}
            onRetry={() => console.log("Retry clicked")}
            onDismiss={() => setShowPanel(false)}
            showTechnicalDetails
          />
        )}
      </CardContent>
    </Card>
  );
};

/* ----------------------------- Hook Usage ----------------------------- */

export const HookUsageExample: React.FC = () => {
  const intelligentError = useIntelligentError({
    onAnalysisComplete: (analysis: any) => {
      // Optional: toast/log
      console.debug("Analysis complete:", analysis);
    },
    onAnalysisError: (e: any) => {
      console.warn("Analysis failed:", e);
    },
  });

  const [selectedScenario, setSelectedScenario] =
    useState<ScenarioKey>("api_key_missing");

  const triggerError = () => {
    const scenario = ERROR_SCENARIOS[selectedScenario];
    intelligentError.analyzeError(scenario.error, {
      error_type: scenario.errorType,
      status_code: scenario.statusCode,
      provider_name: scenario.providerName,
      request_path: "/api/hook-example",
    });
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Hook Usage Example</CardTitle>
        <CardDescription>
          Demonstrates using the{" "}
          <Badge variant="outline">useIntelligentError</Badge> hook for custom
          error analysis flows.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Select
            value={selectedScenario}
            onValueChange={(v) => setSelectedScenario(v as ScenarioKey)}
          >
            <SelectTrigger className="w-72">
              <SelectValue placeholder="Choose an error scenario..." />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(ERROR_SCENARIOS).map(([key, sc]) => (
                <SelectItem key={key} value={key}>
                  {sc.description}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={triggerError} disabled={!!intelligentError.isAnalyzing}>
            {intelligentError.isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              "Analyze Error"
            )}
          </Button>

          {intelligentError.analysis && (
            <Button variant="outline" onClick={intelligentError.clearAnalysis}>
              Clear Analysis
            </Button>
          )}
        </div>

        {intelligentError.isAnalyzing && (
          <div className="text-sm text-muted-foreground">Analyzing error…</div>
        )}

        {intelligentError.analysisError && (
          <div className="text-sm text-red-600">
            Analysis failed: {String(intelligentError.analysisError)}
            <Button
              variant="link"
              size="sm"
              onClick={intelligentError.retryAnalysis}
              className="ml-2"
            >
              Retry
            </Button>
          </div>
        )}

        {intelligentError.analysis && (
          <div className="bg-muted/50 rounded-lg p-4">
            <h4 className="font-medium mb-2">Analysis Result</h4>
            <div className="space-y-2 text-sm">
              <div>
                <strong>Title:</strong> {intelligentError.analysis.title}
              </div>
              <div>
                <strong>Summary:</strong> {intelligentError.analysis.summary}
              </div>
              <div>
                <strong>Severity:</strong> {intelligentError.analysis.severity}
              </div>
              <div>
                <strong>Category:</strong> {intelligentError.analysis.category}
              </div>
              <div>
                <strong>Next Steps:</strong>
                <ul className="list-disc list-inside ml-4 mt-1">
                  {intelligentError.analysis.next_steps?.map(
                    (step: string, idx: number) => <li key={idx}>{step}</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/* --------------------------- API Error Example ------------------------ */

export const ApiErrorExample: React.FC = () => {
  const apiError = useIntelligentApiError();

  const simulateApiError = () => {
    const mockApiError = {
      message: "Request failed with status 500",
      status: 500,
      name: "ApiError",
      isNetworkError: false,
      isCorsError: false,
      isTimeoutError: false,
      responseTime: 2500,
    };
    apiError.handleApiError(mockApiError as any, {
      endpoint: "/api/chat/completions",
      method: "POST",
      provider: "openai",
    });
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>API Error Hook Example</CardTitle>
        <CardDescription>
          Demonstrates automatic API error detection and analysis with{" "}
          <Badge variant="outline">useIntelligentApiError</Badge>.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <Button onClick={simulateApiError} disabled={!!apiError.isAnalyzing}>
          {apiError.isAnalyzing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing…
            </>
          ) : (
            "Simulate API Error"
          )}
        </Button>

        {apiError.analysis && (
          <IntelligentErrorPanel
            error="API request failed"
            autoFetch={false}
            onDismiss={apiError.clearAnalysis}
            // We can pass analysis details through props if panel supports it;
            // leaving minimal to rely on panel's internal fetching/formatting.
          />
        )}
      </CardContent>
    </Card>
  );
};

/* ------------------------------ HOC Example --------------------------- */

const ProblematicComponent: React.FC<{ shouldError: boolean }> = ({
  shouldError,
}) => {
  if (shouldError) {
    throw new Error("This component intentionally failed");
  }
  return (
    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
      <p className="text-green-800">Component is working correctly!</p>
    </div>
  );
};

const EnhancedProblematicComponent = withIntelligentError(ProblematicComponent, {
  position: "top",
  replaceOnError: false,
  errorPanelProps: {
    showTechnicalDetails: true,
  },
});

export const HOCExample: React.FC = () => {
  const [shouldError, setShouldError] = useState(false);

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Higher-Order Component Example</CardTitle>
        <CardDescription>
          Automatic error detection and overlay using the{" "}
          <Badge variant="outline">withIntelligentError</Badge> HOC.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Button
            variant={shouldError ? "destructive" : "default"}
            onClick={() => setShouldError((v) => !v)}
          >
            {shouldError ? "Fix Component" : "Break Component"}
          </Button>
        </div>

        <EnhancedProblematicComponent shouldError={shouldError} />
      </CardContent>
    </Card>
  );
};

/* --------------------------- Page of Examples ------------------------- */

export const IntelligentErrorExamples: React.FC = () => {
  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">
          Intelligent Error Panel Examples
        </h1>
        <p className="text-muted-foreground">
          Comprehensive examples showing different ways to use the intelligent
          error handling system.
        </p>
      </div>

      <BasicErrorPanelExample />
      <HookUsageExample />
      <ApiErrorExample />
      <HOCExample />
    </div>
  );
};

export default IntelligentErrorExamples;
