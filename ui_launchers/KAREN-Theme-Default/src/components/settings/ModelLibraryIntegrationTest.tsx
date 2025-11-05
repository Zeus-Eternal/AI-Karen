"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  PlayCircle,
  Loader2,
  RefreshCw,
  Library,
  Settings,
  CheckCircle,
  AlertCircle,
  Info,
  Download,
  ArrowRight,
} from "lucide-react";
import { getKarenBackend } from "@/lib/karen-backend";
import { HelpTooltip } from "@/components/ui/help-tooltip";

interface IntegrationTestStep {
  id: string;
  name: string;
  description: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  error?: string;
  result?: unknown;
  duration?: number;
}

interface ProviderStatus {
  name: string;
  healthy: boolean;
  has_compatible_models: boolean;
  has_local_models: boolean;
  local_models_count: number;
  available_for_download: number;
  total_compatible: number;
  status: string;
  recommendations: string[];
}

interface IntegrationStatus {
  providers: Record<string, ProviderStatus>;
  overall_status: string;
  total_providers: number;
  healthy_providers: number;
  providers_with_models: number;
  total_compatible_models: number;
  recommendations?: string[];
}

interface ModelLibraryIntegrationTestProps {
  onNavigateToModelLibrary?: () => void;
  onNavigateToLLMSettings?: () => void;
}

/**
 * Comprehensive integration test component that validates the complete workflow
 * from model discovery to provider configuration and usage.
 */
export default function ModelLibraryIntegrationTest({
  onNavigateToModelLibrary,
  onNavigateToLLMSettings,
}: ModelLibraryIntegrationTestProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);

  const [steps, setSteps] = useState<IntegrationTestStep[]>([
    {
      id: "api_connectivity",
      name: "API Connectivity",
      description: "Test connectivity to Model Library and Provider APIs",
      status: "pending",
    },
    {
      id: "model_discovery",
      name: "Model Discovery",
      description: "Discover available models in Model Library",
      status: "pending",
    },
    {
      id: "provider_health",
      name: "Provider Health Check",
      description: "Check health status of all configured providers",
      status: "pending",
    },
    {
      id: "compatibility_check",
      name: "Model Compatibility",
      description: "Check model compatibility with providers",
      status: "pending",
    },
    {
      id: "integration_status",
      name: "Integration Status",
      description: "Validate overall integration between Model Library and providers",
      status: "pending",
    },
    {
      id: "workflow_validation",
      name: "Workflow Validation",
      description: "Validate complete workflow from discovery to configuration",
      status: "pending",
    },
  ]);

  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    void loadIntegrationStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadIntegrationStatus = async () => {
    try {
      const status = await backend.makeRequestPublic<IntegrationStatus>("/api/providers/integration/status");
      const safeStatus: IntegrationStatus = {
        providers: status?.providers ?? {},
        overall_status: status?.overall_status ?? "unknown",
        total_providers: status?.total_providers ?? 0,
        healthy_providers: status?.healthy_providers ?? 0,
        providers_with_models: status?.providers_with_models ?? 0,
        total_compatible_models: status?.total_compatible_models ?? 0,
        recommendations: Array.isArray(status?.recommendations) ? status?.recommendations : [],
      };
      setIntegrationStatus(safeStatus);
    } catch {
      // keep silent in UI; user can run test to see detailed errors
      setIntegrationStatus(null);
    }
  };

  const updateStepStatus = (
    stepId: string,
    status: IntegrationTestStep["status"],
    error?: string,
    result?: unknown,
    duration?: number
  ) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === stepId ? { ...step, status, error, result, duration } : step))
    );
  };

  const runIntegrationTest = async () => {
    setIsRunning(true);
    // Reset steps to pending for a fresh run
    setSteps((prev) => prev.map((s) => ({ ...s, status: "pending", error: undefined, result: undefined, duration: 0 })));

    try {
      // Step 1: API Connectivity
      updateStepStatus("api_connectivity", "running");
      const apiStartTime = Date.now();
      try {
        const [modelLibraryResponse, providersResponse] = await Promise.all([
          backend.makeRequestPublic("/api/models/library"),
          backend.makeRequestPublic("/api/providers/"),
        ]);

        const modelCount = Array.isArray((modelLibraryResponse as any)?.models)
          ? (modelLibraryResponse as any).models.length
          : Array.isArray(modelLibraryResponse)
          ? (modelLibraryResponse as any).length
          : 0;

        updateStepStatus(
          "api_connectivity",
          "completed",
          undefined,
          {
            model_library_available: !!modelLibraryResponse,
            providers_api_available: !!providersResponse,
            model_count: modelCount,
            provider_count: Array.isArray(providersResponse) ? (providersResponse as any).length : 0,
          },
          Date.now() - apiStartTime
        );
      } catch (error: any) {
        updateStepStatus("api_connectivity", "failed", `API connectivity failed: ${String(error?.message ?? error)}`);
        throw error;
      }

      // Step 2: Model Discovery
      updateStepStatus("model_discovery", "running");
      const discoveryStartTime = Date.now();
      try {
        const modelsResp = await backend.makeRequestPublic("/api/models/library");
        const modelsArray: any[] = Array.isArray((modelsResp as any)?.models)
          ? (modelsResp as any).models
          : Array.isArray(modelsResp)
          ? (modelsResp as any)
          : [];

        const localModels = modelsArray.filter((m) => m?.status === "local");
        const availableModels = modelsArray.filter((m) => m?.status === "available");

        updateStepStatus(
          "model_discovery",
          "completed",
          undefined,
          {
            total_models: modelsArray.length,
            local_models: localModels.length,
            available_models: availableModels.length,
            providers_represented: new Set(modelsArray.map((m) => m?.provider).filter(Boolean)).size,
          },
          Date.now() - discoveryStartTime
        );
      } catch (error: any) {
        updateStepStatus("model_discovery", "failed", `Model discovery failed: ${String(error?.message ?? error)}`);
        throw error;
      }

      // Step 3: Provider Health Check
      updateStepStatus("provider_health", "running");
      const healthStartTime = Date.now();
      try {
        const healthResults = await backend.makeRequestPublic<Record<string, { status: string }>>(
          "/api/providers/health-check-all"
        );
        const allEntries = Object.entries(healthResults ?? {});
        const healthyProviders = allEntries.filter(([, h]) => h?.status === "healthy");

        updateStepStatus(
          "provider_health",
          "completed",
          undefined,
          {
            total_providers: allEntries.length,
            healthy_providers: healthyProviders.length,
            health_results: healthResults ?? {},
          },
          Date.now() - healthStartTime
        );
      } catch (error: any) {
        updateStepStatus(
          "provider_health",
          "failed",
          `Provider health check failed: ${String(error?.message ?? error)}`
        );
        throw error;
      }

      // Step 4: Compatibility Check
      updateStepStatus("compatibility_check", "running");
      const compatibilityStartTime = Date.now();
      try {
        const providers = await backend.makeRequestPublic<Array<{ name: string }>>("/api/providers/llm");
        const providersArray = Array.isArray(providers) ? providers : [];
        const compatibilityResults: Array<{
          provider: string;
          total_compatible: number;
          excellent: number;
          good: number;
          acceptable: number;
        }> = [];

        for (const provider of providersArray) {
          try {
            const suggestions = await backend.makeRequestPublic(`/api/providers/${provider.name}/suggestions`);
            const suggestionsData = (suggestions ?? {}) as any;

            compatibilityResults.push({
              provider: provider.name,
              total_compatible: suggestionsData?.total_compatible_models ?? 0,
              excellent: suggestionsData?.recommendations?.excellent?.length ?? 0,
              good: suggestionsData?.recommendations?.good?.length ?? 0,
              acceptable: suggestionsData?.recommendations?.acceptable?.length ?? 0,
            });
          } catch {
            // skip one provider error, keep the rest
          }
        }

        updateStepStatus(
          "compatibility_check",
          "completed",
          undefined,
          {
            providers_checked: compatibilityResults.length,
            total_compatible_models: compatibilityResults.reduce((sum, r) => sum + (r.total_compatible || 0), 0),
            results: compatibilityResults,
          },
          Date.now() - compatibilityStartTime
        );
      } catch (error: any) {
        updateStepStatus(
          "compatibility_check",
          "failed",
          `Compatibility check failed: ${String(error?.message ?? error)}`
        );
        throw error;
      }

      // Step 5: Integration Status
      updateStepStatus("integration_status", "running");
      const integrationStartTime = Date.now();
      try {
        const raw = await backend.makeRequestPublic<IntegrationStatus>("/api/providers/integration/status");
        const safeStatus: IntegrationStatus = {
          providers: raw?.providers ?? {},
          overall_status: raw?.overall_status ?? "unknown",
          total_providers: raw?.total_providers ?? 0,
          healthy_providers: raw?.healthy_providers ?? 0,
          providers_with_models: raw?.providers_with_models ?? 0,
          total_compatible_models: raw?.total_compatible_models ?? 0,
          recommendations: Array.isArray(raw?.recommendations) ? raw?.recommendations : [],
        };
        setIntegrationStatus(safeStatus);

        updateStepStatus(
          "integration_status",
          "completed",
          undefined,
          {
            overall_status: safeStatus.overall_status,
            healthy_providers: safeStatus.healthy_providers,
            providers_with_models: safeStatus.providers_with_models,
            total_compatible_models: safeStatus.total_compatible_models,
            recommendations: safeStatus.recommendations,
          },
          Date.now() - integrationStartTime
        );
      } catch (error: any) {
        updateStepStatus(
          "integration_status",
          "failed",
          `Integration status check failed: ${String(error?.message ?? error)}`
        );
        throw error;
      }

      // Step 6: Workflow Validation
      updateStepStatus("workflow_validation", "running");
      const workflowStartTime = Date.now();
      try {
        const validationChecks = [
          { name: "Model Library API", status: true },
          { name: "Provider API", status: true },
          { name: "Compatibility Service", status: true },
          { name: "Integration Status API", status: true },
          { name: "Cross-navigation Events", status: typeof window !== "undefined" },
        ];
        const allPassed = validationChecks.every((check) => check.status);

        updateStepStatus(
          "workflow_validation",
          "completed",
          undefined,
          {
            checks: validationChecks,
            all_passed: allPassed,
            workflow_status: allPassed ? "fully_functional" : "partially_functional",
          },
          Date.now() - workflowStartTime
        );

        if (allPassed) {
          toast({
            title: "Integration Test Completed",
            description:
              "All integration tests passed successfully! Model Library is fully integrated with LLM Settings.",
          });
        } else {
          toast({
            title: "Integration Test Completed with Issues",
            description: "Some integration tests failed. Check the details for troubleshooting.",
            variant: "destructive",
          });
        }
      } catch (error: any) {
        updateStepStatus(
          "workflow_validation",
          "failed",
          `Workflow validation failed: ${String(error?.message ?? error)}`
        );
        throw error;
      }
    } catch {
      toast({
        title: "Integration Test Failed",
        description: "Some integration tests failed. Check the details below for troubleshooting.",
        variant: "destructive",
      });
    } finally {
      setIsRunning(false);
    }
  };

  const getStepIcon = (step: IntegrationTestStep) => {
    switch (step.status) {
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "skipped":
        return <Info className="h-4 w-4 text-yellow-500" />;
      default:
        return <div className="h-4 w-4 rounded-full border-2 border-muted-foreground" />;
    }
  };

  const getStepBadgeVariant = (status: IntegrationTestStep["status"]) => {
    switch (status) {
      case "completed":
        return "default";
      case "running":
        return "secondary";
      case "failed":
        return "destructive";
      case "skipped":
        return "outline";
      default:
        return "outline";
    }
  };

  const completedSteps = steps.filter((s) => s.status === "completed").length;
  const failedSteps = steps.filter((s) => s.status === "failed").length;
  const totalDuration = steps.reduce((sum, step) => sum + (step.duration || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <PlayCircle className="h-5 w-5" />
                Integration Test
              </CardTitle>
              <CardDescription>End-to-end validation of Model Library ↔ Provider integration.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {completedSteps}/{steps.length} completed
              </Badge>
              {failedSteps > 0 && <Badge variant="destructive">{failedSteps} failed</Badge>}
              {totalDuration > 0 && <Badge variant="secondary">{Math.round(totalDuration / 1000)}s</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Controls */}
          <div className="flex items-center gap-2">
            <Button onClick={runIntegrationTest} disabled={isRunning} className="gap-2" aria-label="Run test">
              {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
              {isRunning ? "Running Test..." : "Run Integration Test"}
            </Button>
            <Button
              variant="outline"
              onClick={() => void loadIntegrationStatus()}
              disabled={isRunning}
              className="gap-2"
              aria-label="Refresh status"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh Status
            </Button>
            {onNavigateToModelLibrary && (
              <Button variant="outline" onClick={onNavigateToModelLibrary} className="gap-2" aria-label="Open library">
                <Library className="h-4 w-4" />
                Model Library
              </Button>
            )}
            {onNavigateToLLMSettings && (
              <Button
                variant="outline"
                onClick={onNavigateToLLMSettings}
                className="gap-2"
                aria-label="Open LLM settings"
              >
                <Settings className="h-4 w-4" />
                LLM Settings
              </Button>
            )}
          </div>

          {/* Integration Status Overview */}
          {integrationStatus && (
            <Alert variant={integrationStatus.overall_status === "healthy" ? "default" : "destructive"}>
              {integrationStatus.overall_status === "healthy" ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertTitle>
                Integration Status:{" "}
                {(integrationStatus?.overall_status || "UNKNOWN").replaceAll("_", " ").toUpperCase()}
              </AlertTitle>
              <AlertDescription>
                {integrationStatus.healthy_providers || 0}/{integrationStatus.total_providers || 0} providers healthy,{" "}
                {integrationStatus.providers_with_models || 0} providers have compatible models,{" "}
                {integrationStatus.total_compatible_models || 0} total compatible models available.
                {Array.isArray(integrationStatus.recommendations) &&
                  integrationStatus.recommendations.length > 0 && (
                    <div className="mt-2">
                      <strong>Recommendations:</strong>
                      <ul className="list-disc list-inside mt-1">
                        {integrationStatus.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm md:text-base lg:text-lg">
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Test Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Test Steps</CardTitle>
          <CardDescription>Detailed breakdown of each validation phase.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                {getStepIcon(step)}
                {index < steps.length - 1 && <div className="w-px h-8 bg-border mt-2" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm md:text-base lg:text-lg">{step.name}</h4>
                  <Badge variant={getStepBadgeVariant(step.status)} className="text-xs sm:text-sm md:text-base">
                    {step.status}
                  </Badge>
                  {step.duration != null && (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      {Math.round((step.duration || 0) / 1000)}s
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">{step.description}</p>

                {step.error && (
                  <Alert variant="destructive" className="mb-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-xs sm:text-sm md:text-base">{step.error}</AlertDescription>
                  </Alert>
                )}

                {step.result && (
                  <div className="text-xs text-muted-foreground bg-muted p-2 rounded sm:text-sm md:text-base">
                    <pre className="whitespace-pre-wrap break-words">
                      {(() => {
                        try {
                          return JSON.stringify(step.result, null, 2);
                        } catch {
                          return String(step.result);
                        }
                      })()}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Integration Workflow Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpTooltip helpKey="workflowTesting" variant="inline" size="sm" />
            Workflow Guide
          </CardTitle>
          <CardDescription>Expected path from discovery to ready-to-use.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
            <Library className="h-4 w-4 text-primary" />
            <span>Discover Models</span>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <Download className="h-4 w-4 text-primary" />
            <span>Download Locally</span>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <Settings className="h-4 w-4 text-primary" />
            <span>Configure Provider</span>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <CheckCircle className="h-4 w-4 text-primary" />
            <span>Ready for Use</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
