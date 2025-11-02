"use client";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  Library,
  CheckCircle,
  AlertCircle,
  Download,
  ExternalLink,
  Loader2,
  RefreshCw,
  Info
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
interface ModelCompatibility {
  model_id: string;
  provider: string;
  compatible: boolean;
  compatibility_score: number;
  reasons: string[];
  requirements: Record<string, any>;
  recommendations: string[];
}
interface ProviderModelSuggestions {
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
  compatibility_details: Record<string, {
    score: number;
    reasons: string[];
    recommendations: string[];
  }>;
}
interface ModelProviderIntegrationProps {
  providers: Array<{
    name: string;
    description: string;
    provider_type: 'remote' | 'local' | 'hybrid';
    health_status: 'healthy' | 'unhealthy' | 'unknown';
  }>;
  onNavigateToModelLibrary?: () => void;
}
/**
 * Component that shows the integration between Model Library and LLM providers,
 * displaying compatibility information and recommendations.
 */
export default function ModelProviderIntegration({ 
  providers, 
  onNavigateToModelLibrary 
}: ModelProviderIntegrationProps) {
  const [suggestions, setSuggestions] = useState<Record<string, ProviderModelSuggestions>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();
  useEffect(() => {
    loadProviderModelSuggestions();
  }, [providers]);
  const loadProviderModelSuggestions = async () => {
    try {
      setLoading(true);
      const newSuggestions: Record<string, ProviderModelSuggestions> = {};
      // Load suggestions for each provider
      await Promise.all(
        providers.map(async (provider) => {
          try {
            const response = await backend.makeRequestPublic<ProviderModelSuggestions>(
              `/api/providers/${provider.name}/suggestions`
            );
            if (response) {
              newSuggestions[provider.name] = response;
            }
          } catch (error) {
          }
        })
      );
      setSuggestions(newSuggestions);
    } catch (error) {
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
    } catch (error) {
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
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center space-y-2">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary sm:w-auto md:w-full" />
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
                <Library className="h-5 w-5 sm:w-auto md:w-full" />
                Model-Provider Integration
              </CardTitle>
              <CardDescription>
                Model compatibility and recommendations for your configured providers
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
               aria-label="Button">
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              {onNavigateToModelLibrary && (
                <button
                  variant="default"
                  size="sm"
                  onClick={onNavigateToModelLibrary}
                  className="gap-2"
                 aria-label="Button">
                  <Library className="h-4 w-4 sm:w-auto md:w-full" />
                  Model Library
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Provider Compatibility Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map((provider) => {
          const suggestion = suggestions[provider.name];
          const hasModels = suggestion && suggestion.total_compatible_models > 0;
          const excellentCount = suggestion?.recommendations.excellent.length || 0;
          const goodCount = suggestion?.recommendations.good.length || 0;
          const acceptableCount = suggestion?.recommendations.acceptable.length || 0;
          return (
            <Card 
              key={provider.name}
              className={`cursor-pointer transition-colors ${
                selectedProvider === provider.name ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => setSelectedProvider(
                selectedProvider === provider.name ? null : provider.name
              )}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{provider.name}</CardTitle>
                  <div className="flex items-center gap-1">
                    {provider.health_status === 'healthy' ? (
                      <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-yellow-500 sm:w-auto md:w-full" />
                    )}
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      {provider.provider_type}
                    </Badge>
                  </div>
                </div>
                <CardDescription className="text-xs sm:text-sm md:text-base">
                  {provider.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                {suggestion ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium md:text-base lg:text-lg">Compatible Models</span>
                      <Badge variant="secondary">
                        {suggestion.total_compatible_models}
                      </Badge>
                    </div>
                    {hasModels ? (
                      <div className="space-y-1">
                        {excellentCount > 0 && (
                          <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                            <span className="text-muted-foreground">Excellent</span>
                            <Badge variant="default" className="h-5 text-xs sm:text-sm md:text-base">
                              {excellentCount}
                            </Badge>
                          </div>
                        )}
                        {goodCount > 0 && (
                          <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                            <span className="text-muted-foreground">Good</span>
                            <Badge variant="secondary" className="h-5 text-xs sm:text-sm md:text-base">
                              {goodCount}
                            </Badge>
                          </div>
                        )}
                        {acceptableCount > 0 && (
                          <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                            <span className="text-muted-foreground">Compatible</span>
                            <Badge variant="outline" className="h-5 text-xs sm:text-sm md:text-base">
                              {acceptableCount}
                            </Badge>
                          </div>
                        )}
                      </div>
                    ) : (
                      <Alert>
                        <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                        <AlertDescription className="text-xs sm:text-sm md:text-base">
                          No compatible models found
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-2">
                    <Loader2 className="h-4 w-4 animate-spin mx-auto text-muted-foreground sm:w-auto md:w-full" />
                    <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">Loading...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      {/* Detailed Provider Information */}
      {selectedProvider && suggestions[selectedProvider] && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5 sm:w-auto md:w-full" />
              {selectedProvider} Model Recommendations
            </CardTitle>
            <CardDescription>
              Detailed compatibility information and model recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(() => {
              const suggestion = suggestions[selectedProvider];
              return (
                <>
                  {/* Provider Capabilities */}
                  <div>
                    <h4 className="font-medium mb-2">Provider Capabilities</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Supported Formats:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {suggestion.provider_capabilities.supported_formats.map(format => (
                            <Badge key={format} variant="outline" className="text-xs sm:text-sm md:text-base">
                              {format}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Performance Type:</span>
                        <Badge variant="secondary" className="ml-2 text-xs sm:text-sm md:text-base">
                          {suggestion.provider_capabilities.performance_type}
                        </Badge>
                      </div>
                      <div>
                        <span className="font-medium">Required Capabilities:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {suggestion.provider_capabilities.required_capabilities.map(cap => (
                            <Badge key={cap} variant="default" className="text-xs sm:text-sm md:text-base">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Quantization Support:</span>
                        <Badge variant="outline" className="ml-2 text-xs sm:text-sm md:text-base">
                          {suggestion.provider_capabilities.quantization_support}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  {/* Model Recommendations */}
                  <div>
                    <h4 className="font-medium mb-2">Recommended Models</h4>
                    <div className="space-y-3">
                      {/* Excellent Models */}
                      {suggestion.recommendations.excellent.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-green-700 dark:text-green-400 mb-1 md:text-base lg:text-lg">
                            Excellent Compatibility
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {suggestion.recommendations.excellent.map(modelId => (
                              <Badge key={modelId} variant="default" className="text-xs sm:text-sm md:text-base">
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Good Models */}
                      {suggestion.recommendations.good.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-blue-700 dark:text-blue-400 mb-1 md:text-base lg:text-lg">
                            Good Compatibility
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {suggestion.recommendations.good.map(modelId => (
                              <Badge key={modelId} variant="secondary" className="text-xs sm:text-sm md:text-base">
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Acceptable Models */}
                      {suggestion.recommendations.acceptable.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-yellow-700 dark:text-yellow-400 mb-1 md:text-base lg:text-lg">
                            Compatible
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {suggestion.recommendations.acceptable.map(modelId => (
                              <Badge key={modelId} variant="outline" className="text-xs sm:text-sm md:text-base">
                                {modelId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  {/* Detailed Compatibility Information */}
                  {Object.keys(suggestion.compatibility_details).length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Top Model Details</h4>
                      <div className="space-y-2">
                        {Object.entries(suggestion.compatibility_details).map(([modelId, details]) => (
                          <Card key={modelId} className="p-3 sm:p-4 md:p-6">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-sm md:text-base lg:text-lg">{modelId}</span>
                              <Badge 
                                variant={getCompatibilityBadgeVariant(details.score)}
                                className="text-xs sm:text-sm md:text-base"
                              >
                                {getCompatibilityLabel(details.score)} ({Math.round(details.score * 100)}%)
                              </Badge>
                            </div>
                            {details.reasons.length > 0 && (
                              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                <span className="font-medium">Reasons:</span>
                                <ul className="list-disc list-inside mt-1">
                                  {details.reasons.map((reason, idx) => (
                                    <li key={idx}>{reason}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {details.recommendations.length > 0 && (
                              <div className="text-xs text-muted-foreground mt-2 sm:text-sm md:text-base">
                                <span className="font-medium">Recommendations:</span>
                                <ul className="list-disc list-inside mt-1">
                                  {details.recommendations.map((rec, idx) => (
                                    <li key={idx}>{rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {onNavigateToModelLibrary && (
                      <button
                        variant="default"
                        size="sm"
                        onClick={onNavigateToModelLibrary}
                        className="gap-2"
                       aria-label="Button">
                        <Library className="h-4 w-4 sm:w-auto md:w-full" />
                        Browse Models
                      </Button>
                    )}
                    <button
                      variant="outline"
                      size="sm"
                      onClick={() = aria-label="Button"> {
                        // Open provider documentation if available
                        const provider = providers.find(p => p.name === selectedProvider);
                        if (provider) {
                          toast({
                            title: "Provider Information",
                            description: `${provider.name}: ${provider.description}`,
                          });
                        }
                      }}
                      className="gap-2"
                    >
                      <ExternalLink className="h-4 w-4 sm:w-auto md:w-full" />
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
