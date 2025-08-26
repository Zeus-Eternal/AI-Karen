"use client";

import { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Switch } from '@/components/ui/switch';
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Key,
  ExternalLink,
  Info,
  Loader2,
  Zap,
  Shield,
  Eye,
  Database,
  Cloud,
  HardDrive,
  Globe,
  Lock,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

interface LLMProvider {
  name: string;
  description: string;
  category: string;
  requires_api_key: boolean;
  capabilities: string[];
  is_llm_provider: boolean;
  provider_type: 'remote' | 'local' | 'hybrid';
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  error_message?: string;
  last_health_check?: number;
  cached_models_count: number;
  last_discovery?: number;
  api_base_url?: string;
  icon?: string;
  documentation_url?: string;
  pricing_info?: {
    input_cost_per_1k?: number;
    output_cost_per_1k?: number;
    currency?: string;
  };
}

interface ProviderStats {
  total_models: number;
  healthy_providers: number;
  total_providers: number;
  last_sync: number;
  degraded_mode: boolean;
}

interface ApiKeyValidationResult {
  valid: boolean;
  message: string;
  provider: string;
  models_discovered?: number;
  capabilities_detected?: string[];
}

interface ProviderManagementProps {
  providers: LLMProvider[];
  setProviders: (providers: LLMProvider[]) => void;
  providerStats: ProviderStats | null;
  setProviderStats: (stats: ProviderStats | null) => void;
}

const LOCAL_STORAGE_KEYS = {
  providerApiKeys: 'llm_provider_api_keys',
  expandedProviders: 'llm_expanded_providers',
};

export default function ProviderManagement({
  providers,
  setProviders,
  providerStats,
  setProviderStats
}: ProviderManagementProps) {
  // State
  const [providerApiKeys, setProviderApiKeys] = useState<Record<string, string>>({});
  const [validatingKeys, setValidatingKeys] = useState<Record<string, boolean>>({});
  const [keyValidationResults, setKeyValidationResults] = useState<Record<string, ApiKeyValidationResult>>({});
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  const [healthChecking, setHealthChecking] = useState(false);
  const [saving, setSaving] = useState(false);

  const { toast } = useToast();
  const backend = getKarenBackend();

  // Load API keys from localStorage on mount
  useState(() => {
    try {
      const storedApiKeys = localStorage.getItem(LOCAL_STORAGE_KEYS.providerApiKeys);
      const storedExpanded = localStorage.getItem(LOCAL_STORAGE_KEYS.expandedProviders);

      if (storedApiKeys) {
        setProviderApiKeys(JSON.parse(storedApiKeys));
      }
      if (storedExpanded) {
        setExpandedProviders(new Set(JSON.parse(storedExpanded)));
      }
    } catch (error) {
      console.warn('Failed to load provider settings:', error);
    }
  });

  // Debounced API key validation
  const validationTimeouts = useMemo(() => new Map<string, NodeJS.Timeout>(), []);

  const handleApiKeyChange = (providerName: string, apiKey: string) => {
    const updatedKeys = { ...providerApiKeys, [providerName]: apiKey };
    setProviderApiKeys(updatedKeys);

    // Save to localStorage immediately
    localStorage.setItem(LOCAL_STORAGE_KEYS.providerApiKeys, JSON.stringify(updatedKeys));

    // Clear previous validation result
    setKeyValidationResults(prev => {
      const updated = { ...prev };
      delete updated[providerName];
      return updated;
    });

    // Clear existing timeout
    const existingTimeout = validationTimeouts.get(providerName);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Validate API key with debouncing
    if (apiKey.trim()) {
      const timeout = setTimeout(() => {
        validateApiKey(providerName, apiKey);
      }, 1000); // 1 second debounce

      validationTimeouts.set(providerName, timeout);
    }
  };

  const validateApiKey = async (providerName: string, apiKey: string) => {
    setValidatingKeys(prev => ({ ...prev, [providerName]: true }));

    try {
      const response = await backend.makeRequestPublic<ApiKeyValidationResult>('/api/providers/validate-api-key', {
        method: 'POST',
        body: JSON.stringify({
          provider: providerName,
          api_key: apiKey
        })
      });

      setKeyValidationResults(prev => ({ ...prev, [providerName]: response }));

      if (response.valid) {
        // Update provider health status
        setProviders(prev => prev.map(p =>
          p.name === providerName
            ? {
                ...p,
                health_status: 'healthy',
                last_health_check: Date.now(),
                cached_models_count: response.models_discovered || p.cached_models_count
              }
            : p
        ));

        toast({
          title: "API Key Valid",
          description: `${providerName} API key validated successfully. ${response.models_discovered || 0} models discovered.`,
        });
      } else {
        // Update provider health status
        setProviders(prev => prev.map(p =>
          p.name === providerName
            ? { ...p, health_status: 'unhealthy', error_message: response.message, last_health_check: Date.now() }
            : p
        ));
      }
    } catch (error) {
      console.error(`Failed to validate API key for ${providerName}:`, error);
      const errorMessage = (error as any)?.message || 'Validation failed - check network connection';

      setKeyValidationResults(prev => ({
        ...prev,
        [providerName]: {
          valid: false,
          message: errorMessage,
          provider: providerName
        }
      }));

      setProviders(prev => prev.map(p =>
        p.name === providerName
          ? { ...p, health_status: 'unhealthy', error_message: errorMessage, last_health_check: Date.now() }
          : p
      ));
    } finally {
      setValidatingKeys(prev => ({ ...prev, [providerName]: false }));
    }
  };

  const toggleProviderExpansion = (providerName: string) => {
    setExpandedProviders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(providerName)) {
        newSet.delete(providerName);
      } else {
        newSet.add(providerName);
      }

      // Save to localStorage
      localStorage.setItem(LOCAL_STORAGE_KEYS.expandedProviders, JSON.stringify([...newSet]));
      return newSet;
    });
  };

  const runHealthCheck = async () => {
    try {
      setHealthChecking(true);

      const response = await backend.makeRequestPublic<Record<string, any>>('/api/providers/health-check-all', {
        method: 'POST'
      }) || {};

      let healthyCount = 0;
      const updatedProviders = providers.map(provider => {
        const healthResult = response[provider.name];
        if (healthResult) {
          const isHealthy = healthResult.status === 'healthy';
          if (isHealthy) healthyCount++;

          return {
            ...provider,
            health_status: (isHealthy ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'unknown',
            error_message: healthResult.message,
            last_health_check: Date.now(),
            cached_models_count: healthResult.models_count || provider.cached_models_count
          };
        }
        return provider;
      });

      setProviders(updatedProviders);

      // Update provider stats
      setProviderStats(prev => prev ? {
        ...prev,
        healthy_providers: healthyCount,
        last_sync: Date.now()
      } : null);

      toast({
        title: "Health Check Complete",
        description: `${healthyCount}/${providers.length} providers are healthy.`,
      });

    } catch (error) {
      console.error('Health check failed:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'runHealthCheck');
      toast({
        title: info.title || "Health Check Failed",
        description: info.message || "Could not check provider health status.",
        variant: "destructive",
      });
    } finally {
      setHealthChecking(false);
    }
  };

  const discoverProviderModels = async (providerName: string, forceRefresh: boolean = false) => {
    try {
      const response = await backend.makeRequestPublic<any[]>(`/api/providers/${providerName}/models?force_refresh=${forceRefresh}`);
      const models = response || [];

      // Update provider cached model count
      setProviders(prev => prev.map(p =>
        p.name === providerName
          ? { ...p, cached_models_count: models.length, last_discovery: Date.now() / 1000 }
          : p
      ));

      toast({
        title: "Models Discovered",
        description: `Found ${models.length} models for ${providerName}.`,
      });

    } catch (error) {
      console.error(`Failed to discover models for ${providerName}:`, error);
      toast({
        title: "Discovery Failed",
        description: `Could not discover models for ${providerName}.`,
        variant: "destructive",
      });
    }
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getHealthStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">Healthy</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getProviderTypeIcon = (type: string) => {
    switch (type) {
      case 'remote':
        return <Cloud className="h-4 w-4" />;
      case 'local':
        return <HardDrive className="h-4 w-4" />;
      case 'hybrid':
        return <Globe className="h-4 w-4" />;
      default:
        return <Database className="h-4 w-4" />;
    }
  };

  const getValidationIcon = (providerName: string) => {
    const isValidating = validatingKeys[providerName];
    const result = keyValidationResults[providerName];

    if (isValidating) {
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    }

    if (result) {
      return result.valid
        ? <CheckCircle2 className="h-4 w-4 text-green-500" />
        : <AlertCircle className="h-4 w-4 text-red-500" />;
    }

    return null;
  };

  const getCapabilityIcon = (capability: string) => {
    switch (capability) {
      case 'streaming':
        return <Zap className="h-3 w-3" />;
      case 'vision':
        return <Eye className="h-3 w-3" />;
      case 'function_calling':
        return <Database className="h-3 w-3" />;
      case 'local_execution':
        return <Shield className="h-3 w-3" />;
      case 'embeddings':
        return <Database className="h-3 w-3" />;
      case 'privacy':
        return <Lock className="h-3 w-3" />;
      default:
        return <Info className="h-3 w-3" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Provider Stats and Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5" />
                Provider Management
              </CardTitle>
              <CardDescription>
                Configure API keys and manage LLM provider connections
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={runHealthCheck}
              disabled={healthChecking}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${healthChecking ? 'animate-spin' : ''}`} />
              Health Check
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {providerStats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{providerStats.total_providers}</div>
                <div className="text-sm text-muted-foreground">Total Providers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{providerStats.healthy_providers}</div>
                <div className="text-sm text-muted-foreground">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{providerStats.total_models}</div>
                <div className="text-sm text-muted-foreground">Total Models</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {new Date(providerStats.last_sync).toLocaleDateString()}
                </div>
                <div className="text-sm text-muted-foreground">Last Sync</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Provider List */}
      <div className="space-y-4">
        {providers.map((provider) => (
          <Card key={provider.name} className="transition-all duration-200 hover:shadow-md">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getProviderTypeIcon(provider.provider_type)}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold capitalize">{provider.name}</h3>
                      {getHealthStatusBadge(provider.health_status)}
                    </div>
                    <p className="text-sm text-muted-foreground">{provider.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {provider.cached_models_count} models
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleProviderExpansion(provider.name)}
                  >
                    {expandedProviders.has(provider.name) ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>

            {expandedProviders.has(provider.name) && (
              <CardContent className="pt-0 space-y-4">
                {/* API Key Configuration */}
                {provider.requires_api_key && (
                  <div className="space-y-2">
                    <Label htmlFor={`${provider.name}-api-key`} className="flex items-center gap-2">
                      <Key className="h-4 w-4" />
                      API Key
                    </Label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Input
                          id={`${provider.name}-api-key`}
                          type="password"
                          placeholder={`Enter ${provider.name} API key`}
                          value={providerApiKeys[provider.name] || ''}
                          onChange={(e) => handleApiKeyChange(provider.name, e.target.value)}
                          className="pr-10"
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          {getValidationIcon(provider.name)}
                        </div>
                      </div>
                      {provider.cached_models_count > 0 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => discoverProviderModels(provider.name, true)}
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      )}
                    </div>

                    {/* Validation Result */}
                    {keyValidationResults[provider.name] && (
                      <Alert variant={keyValidationResults[provider.name].valid ? "default" : "destructive"}>
                        {keyValidationResults[provider.name].valid ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : (
                          <AlertCircle className="h-4 w-4" />
                        )}
                        <AlertDescription>
                          {keyValidationResults[provider.name].message}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}

                {/* Provider Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Capabilities</h4>
                    <div className="flex flex-wrap gap-1">
                      {provider.capabilities.map((capability) => (
                        <Badge key={capability} variant="secondary" className="text-xs gap-1">
                          {getCapabilityIcon(capability)}
                          {capability.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Status</h4>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm">
                        {getHealthStatusIcon(provider.health_status)}
                        <span className="capitalize">{provider.health_status}</span>
                      </div>
                      {provider.last_health_check && (
                        <div className="text-xs text-muted-foreground">
                          Last checked: {new Date(provider.last_health_check).toLocaleString()}
                        </div>
                      )}
                      {provider.error_message && (
                        <div className="text-xs text-red-600">{provider.error_message}</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Provider Links */}
                <div className="flex flex-wrap gap-2 pt-2 border-t">
                  {provider.documentation_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={provider.documentation_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        Documentation
                      </a>
                    </Button>
                  )}

                  {provider.name === 'openai' && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">
                        <Key className="h-3 w-3 mr-1" />
                        Get API Key
                      </a>
                    </Button>
                  )}

                  {provider.name === 'gemini' && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">
                        <Key className="h-3 w-3 mr-1" />
                        Get API Key
                      </a>
                    </Button>
                  )}

                  {provider.name === 'deepseek' && (
                    <Button variant="outline" size="sm" asChild>
                      <a href="https://platform.deepseek.com/api_keys" target="_blank" rel="noopener noreferrer">
                        <Key className="h-3 w-3 mr-1" />
                        Get API Key
                      </a>
                    </Button>
                  )}
                </div>

                {/* Local Provider Info */}
                {provider.name === 'local' && (
                  <Alert>
                    <HardDrive className="h-4 w-4" />
                    <AlertTitle>Local Provider</AlertTitle>
                    <AlertDescription className="text-sm">
                      This provider uses models stored locally on your machine. No API key is required.
                      Models are automatically discovered from your local model directory.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            )}
          </Card>
        ))}
      </div>

      {/* Information */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Provider Configuration</AlertTitle>
        <AlertDescription className="text-sm space-y-2">
          <p>• API keys are validated in real-time and stored locally for convenience</p>
          <p>• CopilotKit is excluded from LLM providers as it's a UI framework (configure it in the CopilotKit settings tab)</p>
          <p>• Local providers don't require API keys and scan for local model files</p>
          <p>• Provider health is checked automatically and can be refreshed manually</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}
