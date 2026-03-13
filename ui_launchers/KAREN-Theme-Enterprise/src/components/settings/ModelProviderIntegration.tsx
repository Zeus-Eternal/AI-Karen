"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from "@/lib/karen-backend";
import {
  Loader2,
  Library,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Info,
  ExternalLink,
} from "lucide-react";

export interface ProviderModelSuggestions {
  provider: string;
  provider_capabilities: {
    supported_formats: string[];
    required_capabilities: string[];
    optional_capabilities: string[];
    performance_type: string;
    quantization_support: string;
  };
  recommendations: {
    excellent: string[];
    good: string[];
    acceptable: string[];
  };
  total_compatible_models: number;
  compatibility_details: Record<
    string,
    {
      score: number;
      reasons: string[];
      recommendations: string[];
    }
  >;
}

export interface ModelProviderIntegrationProps {
  providers: Array<{
    name: string;
    description: string;
    provider_type: "remote" | "local" | "hybrid";
    health_status: "healthy" | "unhealthy" | "unknown";
  }>;
  onNavigateToModelLibrary?: () => void;
}

/**
 * Model-Provider Integration dashboard:
 * - Fetches compatibility suggestions per provider
 * - Summarizes counts (excellent / good / acceptable)
 * - Shows capabilities + compatibility details for a selected provider
 */
export default function ModelProviderIntegration({
  providers,
  onNavigateToModelLibrary,
}: ModelProviderIntegrationProps) {
  const [suggestions, setSuggestions] = useState<
    Record<string, ProviderModelSuggestions>
  >({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();

  const providerNames = useMemo(
    () => providers.map((p) => p.name),
    [providers]
  );

  useEffect(() => {
    loadProviderModelSuggestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(providerNames)]); // stable trigger when provider list changes

  const loadProviderModelSuggestions = async () => {
    setLoading(true);
    try {
      const newSuggestions: Record<string, ProviderModelSuggestions> = {};

      await Promise.all(
        providers.map(async (provider) => {
          try {
            const response =
              await backend.makeRequestPublic<ProviderModelSuggestions>(
                `/api/providers/${encodeURIComponent(
                  provider.name
                )}/suggestions`
              );
            if (response) newSuggestions[provider.name] = response;
          } catch (error) {
            console.error(`Failed to load model suggestions for provider ${provider.name}`, error);
            // Soft-fail per provider; surface a toast once at the end
          }
        })
      );

      setSuggestions(newSuggestions);

      // If the previously selected provider no longer exists, clear selection
      if (selectedProvider && !newSuggestions[selectedProvider]) {
        setSelectedProvider(null);
      }
    } catch {
      toast({
        title: "Failed to Load Model Compatibility",
        description: "Could not load model compatibility information.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadProviderModelSuggestions();
      toast({
        title: "Compatibility Refreshed",
        description: "Model compatibility information has been updated.",
      });
    } catch {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh compatibility information.",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const getCompatibilityBadgeVariant = (score: number) => {
    if (score >= 0.9) return "default";
    if (score >= 0.7) return "secondary";
    if (score >= 0.5) return "outline";
    return "destructive";
  };

  const getCompatibilityLabel = (score: number) => {
    if (score >= 0.9) return "Excellent";
    if (score >= 0.7) return "Good";
    if (score >= 0.5) return "Compatible";
    return "Limited";
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <Loader2 className="h-7 w-7 animate-spin mx-auto text-primary" />
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Loading model compatibility information...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Library className="h-5 w-5" />
                Model-Provider Integration
              </CardTitle>
              <CardDescription>
                See which local/remote models fit each provider’s capabilities
                and performance profile.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                aria-label="Refresh"
              >
                <RefreshCw
                  className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                <span className="sr-only">Refresh</span>
              </Button>
              {onNavigateToModelLibrary && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={onNavigateToModelLibrary}
                  className="gap-2"
                >
                  <Library className="h-4 w-4" />
                  Open Model Library
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Provider Compatibility Overview */}
      {providers.length === 0 ? (
        <Alert>
          <AlertTitle>No Providers Found</AlertTitle>
          <AlertDescription>
            Add or enable at least one provider in settings to see compatibility
            recommendations.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {providers.map((provider) => {
            const suggestion = suggestions[provider.name];
            const hasModels =
              !!suggestion && suggestion.total_compatible_models > 0;
            const excellentCount =
              suggestion?.recommendations.excellent.length ?? 0;
            const goodCount = suggestion?.recommendations.good.length ?? 0;
            const acceptableCount =
              suggestion?.recommendations.acceptable.length ?? 0;

            return (
              <Card
                key={provider.name}
                className={`cursor-pointer transition-shadow hover:shadow-md ${
                  selectedProvider === provider.name
                    ? "ring-2 ring-primary"
                    : ""
                }`}
                onClick={() =>
                  setSelectedProvider(
                    selectedProvider === provider.name ? null : provider.name
                  )
                }
                aria-label={`Select ${provider.name}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{provider.name}</CardTitle>
                    <div className="flex items-center gap-1">
                      {provider.health_status === "healthy" ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <Badge variant="outline" className="text-xs capitalize">
                        {provider.provider_type}
                      </Badge>
                    </div>
                  </div>
                  <CardDescription className="text-xs sm:text-sm">
                    {provider.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  {suggestion ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          Compatible Models
                        </span>
                        <Badge variant="secondary">
                          {suggestion.total_compatible_models}
                        </Badge>
                      </div>

                      {hasModels ? (
                        <div className="space-y-1">
                          {excellentCount > 0 && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">
                                Excellent
                              </span>
                              <Badge variant="default" className="h-5">
                                {excellentCount}
                              </Badge>
                            </div>
                          )}
                          {goodCount > 0 && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">
                                Good
                              </span>
                              <Badge variant="secondary" className="h-5">
                                {goodCount}
                              </Badge>
                            </div>
                          )}
                          {acceptableCount > 0 && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">
                                Compatible
                              </span>
                              <Badge variant="outline" className="h-5">
                                {acceptableCount}
                              </Badge>
                            </div>
                          )}
                        </div>
                      ) : (
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription className="text-sm">
                            No compatible models discovered yet for this
                            provider.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-2">
                      <Loader2 className="h-4 w-4 animate-spin mx-auto text-muted-foreground" />
                      <p className="text-xs text-muted-foreground mt-1">
                        Loading…
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detailed Provider Information */}
      {selectedProvider && suggestions[selectedProvider] && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              {selectedProvider} Model Recommendations
            </CardTitle>
            <CardDescription>
              Capabilities, best-fit models, and detailed compatibility
              rationale.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(() => {
              const sug = suggestions[selectedProvider];

              return (
                <>
                  {/* Provider Capabilities */}
                  <div>
                    <h4 className="font-medium mb-2">Provider Capabilities</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Supported Formats:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {sug.provider_capabilities.supported_formats.map(
                            (format) => (
                              <Badge
                                key={format}
                                variant="outline"
                                className="text-xs"
                              >
                                {format}
                              </Badge>
                            )
                          )}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Performance Type:</span>
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {sug.provider_capabilities.performance_type}
                        </Badge>
                      </div>
                      <div>
                        <span className="font-medium">
                          Required Capabilities:
                        </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {sug.provider_capabilities.required_capabilities.map(
                            (cap) => (
                              <Badge
                                key={cap}
                                variant="default"
                                className="text-xs"
                              >
                                {cap}
                              </Badge>
                            )
                          )}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">
                          Quantization Support:
                        </span>
                        <Badge variant="outline" className="ml-2 text-xs">
                          {sug.provider_capabilities.quantization_support}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {/* Model Recommendations */}
                  <div>
                    <h4 className="font-medium mb-2">Recommended Models</h4>
                    <div className="space-y-3">
                      {sug.recommendations.excellent.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-green-700 dark:text-green-400 mb-1">
                            Excellent
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {sug.recommendations.excellent.map((modelId) => (
                              <Badge
                                key={modelId}
                                variant="default"
                                className="text-xs"
                              >
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {sug.recommendations.good.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-blue-700 dark:text-blue-400 mb-1">
                            Good
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {sug.recommendations.good.map((modelId) => (
                              <Badge
                                key={modelId}
                                variant="secondary"
                                className="text-xs"
                              >
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {sug.recommendations.acceptable.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-yellow-700 dark:text-yellow-400 mb-1">
                            Compatible
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {sug.recommendations.acceptable.map((modelId) => (
                              <Badge
                                key={modelId}
                                variant="outline"
                                className="text-xs"
                              >
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Detailed Compatibility Information */}
                  {Object.keys(sug.compatibility_details).length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Top Model Details</h4>
                      <div className="space-y-2">
                        {Object.entries(sug.compatibility_details).map(
                          ([modelId, details]) => (
                            <Card key={modelId} className="p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-sm">
                                  {modelId}
                                </span>
                                <Badge
                                  variant={getCompatibilityBadgeVariant(
                                    details.score
                                  )}
                                  className="text-xs"
                                >
                                  {getCompatibilityLabel(details.score)} (
                                  {Math.round(details.score * 100)}%)
                                </Badge>
                              </div>

                              {details.reasons.length > 0 && (
                                <div className="text-xs text-muted-foreground">
                                  <span className="font-medium">Reasons:</span>
                                  <ul className="list-disc list-inside mt-1 space-y-0.5">
                                    {details.reasons.map((reason, idx) => (
                                      <li key={idx}>{reason}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {details.recommendations.length > 0 && (
                                <div className="text-xs text-muted-foreground mt-2">
                                  <span className="font-medium">
                                    Recommendations:
                                  </span>
                                  <ul className="list-disc list-inside mt-1 space-y-0.5">
                                    {details.recommendations.map((rec, idx) => (
                                      <li key={idx}>{rec}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </Card>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {onNavigateToModelLibrary && (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={onNavigateToModelLibrary}
                        className="gap-2"
                      >
                        <Library className="h-4 w-4" />
                        Open Model Library
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const provider = providers.find(
                          (p) => p.name === selectedProvider
                        );
                        if (provider) {
                          toast({
                            title: provider.name,
                            description:
                              provider.description || "No additional info.",
                          });
                        }
                      }}
                      className="gap-2"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Provider Info
                    </Button>
                  </div>
                </>
              );
            })()}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
