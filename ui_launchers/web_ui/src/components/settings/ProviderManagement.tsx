"use client";
import { useState, useEffect, useMemo } from 'react';
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
  ChevronUp,
  Activity,
  Settings
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { openaiPing } from '@/lib/providers-api';
import { handleApiError } from '@/lib/error-handler';
import ProviderStatusIndicator, { type ProviderStatus } from './ProviderStatusIndicator';
import ProviderTestingInterface from './ProviderTestingInterface';
import ProviderConfigurationGuide from './ProviderConfigurationGuide';
import ProviderDiagnosticsPage from './ProviderDiagnosticsPage';
import ErrorMessageDisplay from './ErrorMessageDisplay';
import { useProviderNotifications } from '@/hooks/useProviderNotifications';
// Model Recommendations Component
interface ModelRecommendationsProps {
  provider: LLMProvider;
}
function ModelRecommendations({ provider }: ModelRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const { toast } = useToast();
  const backend = getKarenBackend();
  const fetchRecommendations = async () => {
    if (!provider.is_llm_provider) return;
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic(`/api/providers/${provider.name}/model-recommendations`);
      setRecommendations(response);
    } catch (error) {
      const info = handleApiError(error as any, 'fetchRecommendations');
      toast({
        title: info.title,
        description: info.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    if (expanded && !recommendations && !loading) {
      fetchRecommendations();
    }
  }, [expanded]);
  if (!provider.is_llm_provider) {
    return null;
  }
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs text-muted-foreground flex items-center gap-2 sm:text-sm md:text-base">
          <Database className="h-3 w-3 sm:w-auto md:w-full" />
          Model Recommendations
        </Label>
        <button
          variant="ghost"
          size="sm"
          onClick={() = aria-label="Button"> setExpanded(!expanded)}
          className="h-6 px-2 text-xs sm:text-sm md:text-base"
        >
          {expanded ? <ChevronUp className="h-3 w-3 sm:w-auto md:w-full" /> : <ChevronDown className="h-3 w-3 sm:w-auto md:w-full" />}
        </Button>
      </div>
      {expanded && (
        <div className="space-y-2 p-3 bg-muted/30 rounded-lg sm:p-4 md:p-6">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground md:text-base lg:text-lg">
              <Loader2 className="h-4 w-4 animate-spin sm:w-auto md:w-full" />
              Loading recommendations...
            </div>
          ) : recommendations ? (
            <div className="space-y-3">
              {/* Validation Status */}
              {recommendations.validation && (
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={recommendations.validation.status === 'healthy' ? 'default' : 'destructive'}
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {recommendations.validation.status === 'healthy' ? 'Models Available' : 'Needs Models'}
                  </Badge>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {recommendations.validation.local_models_count} local, {recommendations.validation.available_for_download} available
                  </span>
                </div>
              )}
              {/* Recommendations by Category */}
              {recommendations.recommendations && (
                <div className="space-y-2">
                  {recommendations.recommendations.excellent && recommendations.recommendations.excellent.length > 0 && (
                    <div>
                      <Label className="text-xs font-medium text-green-600 sm:text-sm md:text-base">Excellent Matches</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {recommendations.recommendations.excellent.slice(0, 3).map((modelId: string) => (
                          <Badge key={modelId} variant="default" className="text-xs bg-green-100 text-green-800 sm:text-sm md:text-base">
                            {modelId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {recommendations.recommendations.good && recommendations.recommendations.good.length > 0 && (
                    <div>
                      <Label className="text-xs font-medium text-blue-600 sm:text-sm md:text-base">Good Matches</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {recommendations.recommendations.good.slice(0, 3).map((modelId: string) => (
                          <Badge key={modelId} variant="secondary" className="text-xs sm:text-sm md:text-base">
                            {modelId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {recommendations.recommendations.acceptable && recommendations.recommendations.acceptable.length > 0 && (
                    <div>
                      <Label className="text-xs font-medium text-yellow-600 sm:text-sm md:text-base">Acceptable Matches</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {recommendations.recommendations.acceptable.slice(0, 2).map((modelId: string) => (
                          <Badge key={modelId} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {modelId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              {/* Quick Actions */}
              {recommendations.validation && recommendations.validation.suggested_downloads && (
                <div className="flex gap-2 pt-2">
                  <button
                    variant="outline"
                    size="sm"
                    onClick={() = aria-label="Button"> {
                      // Navigate to Model Library with provider filter
                      toast({
                        title: "Opening Model Library",
                        description: `Showing models compatible with ${provider.name}`,
                      });
                    }}
                    className="text-xs h-7 sm:text-sm md:text-base"
                  >
                    <Database className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                    Browse Models
                  </Button>
                  <button
                    variant="outline"
                    size="sm"
                    onClick={fetchRecommendations}
                    className="text-xs h-7 sm:text-sm md:text-base"
                   aria-label="Button">
                    <RefreshCw className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                    Refresh
                  </Button>
                </div>
              )}
              {/* Error State */}
              {recommendations.error && (
                <Alert>
                  <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                  <AlertDescription className="text-xs sm:text-sm md:text-base">
                    {recommendations.error}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Click to load model recommendations
            </div>
          )}
        </div>
      )}
    </div>
  );
}
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
  const [showConfigGuide, setShowConfigGuide] = useState<string | null>(null);
  const [showTesting, setShowTesting] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState<string | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();
  // Provider notifications
  const {
    notifyProviderStatusChange,
    notifyError
  } = useProviderNotifications({ autoToast: false }); // Disable auto-toast to avoid duplicates
  // Load API keys from localStorage on mount
  useEffect(() => {
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
    }
  }, []);
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
        const previousStatus = providers.find(p => p.name === providerName)?.health_status;
        const updatedProviders = providers.map(p =>
          p.name === providerName
            ? {
                ...p,
                health_status: 'healthy' as const,
                last_health_check: Date.now(),
                cached_models_count: response.models_discovered || p.cached_models_count
              }
            : p
        );
        setProviders(updatedProviders);
        // Notify status change
        if (previousStatus !== 'healthy') {
          notifyProviderStatusChange(providerName, 'healthy', previousStatus);
        }
        toast({
          title: "API Key Valid",
          description: `${providerName} API key validated successfully. ${response.models_discovered || 0} models discovered.`,
        });
      } else {
        // Update provider health status
        const previousStatus = providers.find(p => p.name === providerName)?.health_status;
        const updatedProviders = providers.map(p =>
          p.name === providerName
            ? { ...p, health_status: 'unhealthy' as const, error_message: response.message, last_health_check: Date.now() }
            : p
        );
        setProviders(updatedProviders);
        // Notify error
        notifyError(providerName, response.message, 'API_KEY_INVALID');
      }
    } catch (error) {
      const errorMessage = (error as any)?.message || 'Validation failed - check network connection';
      setKeyValidationResults(prev => ({
        ...prev,
        [providerName]: {
          valid: false,
          message: errorMessage,
          provider: providerName
        }
      }));
      const previousStatus = providers.find(p => p.name === providerName)?.health_status;
      const updatedProviders = providers.map(p =>
        p.name === providerName
          ? { ...p, health_status: 'unhealthy' as const, error_message: errorMessage, last_health_check: Date.now() }
          : p
      );
      setProviders(updatedProviders);
      // Notify error
      notifyError(providerName, errorMessage, 'VALIDATION_FAILED');
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
      localStorage.setItem(LOCAL_STORAGE_KEYS.expandedProviders, JSON.stringify(Array.from(newSet)));
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
            health_status: (isHealthy ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy',
            error_message: healthResult.message,
            last_health_check: Date.now(),
            cached_models_count: healthResult.models_count || provider.cached_models_count
          };
        }
        return provider;
      });
      setProviders(updatedProviders);
      // Update provider stats
      if (providerStats) {
        setProviderStats({
          ...providerStats,
          healthy_providers: healthyCount,
          last_sync: Date.now()
        });
      }
      toast({
        title: "Health Check Complete",
        description: `${healthyCount}/${providers.length} providers are healthy.`,
      });
    } catch (error) {
      const info = (error as any)?.errorInfo || handleApiError(error as any, 'runHealthCheck');
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
      const updatedProviders = providers.map(p =>
        p.name === providerName
          ? { ...p, cached_models_count: models.length, last_discovery: Date.now() / 1000 }
          : p
      );
      setProviders(updatedProviders);
      toast({
        title: "Models Discovered",
        description: `Found ${models.length} models for ${providerName}.`,
      });
    } catch (error) {
      toast({
        title: "Discovery Failed",
        description: `Could not discover models for ${providerName}.`,
        variant: "destructive",
      });
    }
  };
  const testProvider = async (providerName: string) => {
    try {
      if (providerName === 'openai') {
        const res = await openaiPing();
        if (res?.ok) {
          toast({ title: 'OpenAI Connected', description: 'API key validated and reachable.' });
          // mark healthy on success
          setProviders(providers.map(p => p.name === providerName ? { ...p, health_status: 'healthy', last_health_check: Date.now() } : p));
          return;
        }
      }
      // Default/fallback path for providers without a specific ping yet
      await checkProviderHealth(providerName);
    } catch (error) {
      toast({ title: 'Test Failed', description: `Could not connect to ${providerName}.`, variant: 'destructive' });
      setProviders(providers.map(p => p.name === providerName ? { ...p, health_status: 'unhealthy', last_health_check: Date.now() } : p));
    }
  };
  const checkProviderHealth = async (providerName: string) => {
    try {
      const res = await backend.makeRequestPublic<any>(`/api/providers/${providerName}/health`);
      if (res) {
        const isHealthy = res.status === 'healthy';
        const updatedProviders = providers.map(p => p.name === providerName ? {
          ...p,
          health_status: (isHealthy ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy',
          error_message: res.message,
          last_health_check: Date.now()
        } : p);
        setProviders(updatedProviders);
        toast({
          title: isHealthy ? "Provider Healthy" : "Provider Issues",
          description: res.message || `${providerName} health check completed.`,
          variant: isHealthy ? "default" : "destructive",
        });
      }
    } catch (error) {
    }
  };
  const toggleProviderEnabled = async (providerName: string, enable: boolean) => {
    try {
      const res = await backend.makeRequestPublic<any>(`/api/providers/${providerName}/${enable ? 'enable' : 'disable'}`, {
        method: 'POST'
      });
      if (res?.success) {
        // Update local state; on disable, mark as unknown & disabled in message
        const updatedProviders = providers.map(p => p.name === providerName ? {
          ...p,
          health_status: enable ? p.health_status : 'unknown' as const,
          error_message: enable ? undefined : 'Provider disabled'
        } : p);
        setProviders(updatedProviders);
        toast({
          title: enable ? "Provider Enabled" : "Provider Disabled",
          description: `${providerName} has been ${enable ? 'enabled' : 'disabled'}.`,
        });
      }
    } catch (error) {
      toast({
        title: "Operation Failed",
        description: `Could not ${enable ? 'enable' : 'disable'} ${providerName}.`,
        variant: "destructive",
      });
    }
  };
  // Convert LLMProvider to ProviderStatus for the new components
  const convertToProviderStatus = (provider: LLMProvider): ProviderStatus => ({
    name: provider.name,
    status: provider.health_status as any,
    health_score: provider.health_status === 'healthy' ? 85 : provider.health_status === 'unhealthy' ? 25 : 50,
    last_successful_request: provider.last_health_check ? new Date(provider.last_health_check).toISOString() : undefined,
    error_count: 0,
    connectivity_status: provider.health_status === 'healthy' ? 'connected' : 'disconnected',
    model_availability: {},
    capability_status: provider.capabilities.reduce((acc, cap) => ({ ...acc, [cap]: true }), {}),
    performance_metrics: {
      average_response_time: 1500,
      success_rate: provider.health_status === 'healthy' ? 0.95 : 0.3,
      error_rate: provider.health_status === 'healthy' ? 0.05 : 0.7,
      requests_per_minute: 10,
      last_updated: new Date().toISOString()
    },
    last_error: provider.error_message,
    recovery_suggestions: provider.error_message ? ['Check API key configuration', 'Verify network connectivity'] : [],
    provider_type: provider.provider_type,
    requires_api_key: provider.requires_api_key,
    api_key_valid: provider.health_status === 'healthy',
    dependencies: {},
    configuration_issues: provider.error_message ? [provider.error_message] : []
  });
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400 sm:w-auto md:w-full" />;
    }
  };
  const getProviderTypeIcon = (type: string) => {
    switch (type) {
      case 'local':
        return <HardDrive className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />;
      case 'remote':
        return <Cloud className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'hybrid':
        return <Globe className="h-4 w-4 text-purple-600 sm:w-auto md:w-full" />;
      default:
        return <Database className="h-4 w-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5 sm:w-auto md:w-full" />
                Provider Management
              </CardTitle>
              <CardDescription>
                Configure and manage LLM providers, API keys, and health monitoring
              </CardDescription>
            </div>
            <button onClick={runHealthCheck} disabled={healthChecking} aria-label="Button">
              {healthChecking ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              )}
              Health Check
            </Button>
          </div>
        </CardHeader>
      </Card>
      {/* Provider Stats */}
      {providerStats && (
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{providerStats.healthy_providers}</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Healthy Providers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{providerStats.total_providers}</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Total Providers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{providerStats.total_models}</div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Available Models</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {providerStats.degraded_mode ? (
                    <Badge variant="destructive">Degraded</Badge>
                  ) : (
                    <Badge variant="default">Operational</Badge>
                  )}
                </div>
                <div className="text-sm text-muted-foreground md:text-base lg:text-lg">System Status</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      {/* Provider List */}
      <div className="space-y-4">
        {providers.map((provider) => (
          <Card key={provider.name} className="transition-all hover:shadow-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getProviderTypeIcon(provider.provider_type)}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{provider.name}</h3>
                      {getHealthIcon(provider.health_status)}
                      <Badge variant={provider.provider_type === 'local' ? 'secondary' : 'default'}>
                        {provider.provider_type}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground md:text-base lg:text-lg">{provider.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    variant="outline"
                    size="sm"
                    onClick={() = aria-label="Button"> checkProviderHealth(provider.name)}
                  >
                    <Activity className="h-4 w-4 sm:w-auto md:w-full" />
                  </Button>
                  <button
                    variant="outline"
                    size="sm"
                    onClick={() = aria-label="Button"> toggleProviderExpansion(provider.name)}
                  >
                    {expandedProviders.has(provider.name) ? (
                      <ChevronUp className="h-4 w-4 sm:w-auto md:w-full" />
                    ) : (
                      <ChevronDown className="h-4 w-4 sm:w-auto md:w-full" />
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            {expandedProviders.has(provider.name) && (
              <CardContent>
                <div className="space-y-4">
                  {/* API Key Configuration */}
                  {provider.requires_api_key && (
                    <div className="space-y-2">
                      <Label htmlFor={`api-key-${provider.name}`} className="flex items-center gap-2">
                        <Key className="h-4 w-4 sm:w-auto md:w-full" />
                        API Key
                      </Label>
                      <div className="flex gap-2">
                        <input
                          id={`api-key-${provider.name}`}
                          type="password"
                          placeholder="Enter API key..."
                          value={providerApiKeys[provider.name] || ''}
                          onChange={(e) = aria-label="Input"> handleApiKeyChange(provider.name, e.target.value)}
                        />
                        {validatingKeys[provider.name] && (
                          <button variant="outline" size="sm" disabled aria-label="Button">
                            <Loader2 className="h-4 w-4 animate-spin sm:w-auto md:w-full" />
                          </Button>
                        )}
                      </div>
                      {keyValidationResults[provider.name] && (
                        <Alert variant={keyValidationResults[provider.name].valid ? "default" : "destructive"}>
                          <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                          <AlertDescription>
                            {keyValidationResults[provider.name].message}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  )}
                  {/* Provider Info */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <Label className="text-xs text-muted-foreground sm:text-sm md:text-base">Capabilities</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {provider.capabilities.map((cap) => (
                          <Badge key={cap} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {cap}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground sm:text-sm md:text-base">Models Cached</Label>
                      <div className="font-medium">{provider.cached_models_count}</div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground sm:text-sm md:text-base">Last Check</Label>
                      <div className="font-medium">
                        {provider.last_health_check
                          ? new Date(provider.last_health_check).toLocaleString()
                          : 'Never'
                        }
                      </div>
                    </div>
                  </div>
                  {/* Error Message */}
                  {provider.error_message && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                      <AlertDescription>{provider.error_message}</AlertDescription>
                    </Alert>
                  )}
                  {/* Model Recommendations */}
                  <ModelRecommendations provider={provider} />
                  {/* Enhanced Provider Status */}
                  <ProviderStatusIndicator
                    provider={convertToProviderStatus(provider)}
                    onTest={async (name) => await testProvider(name)}
                    onRefresh={async (name) => await checkProviderHealth(name)}
                    showDetails={false}
                    realTimeUpdates={true}
                  />
                  {/* Actions */}
                  <div className="flex flex-wrap gap-2">
                    <button
                      variant="outline"
                      size="sm"
                      onClick={() = aria-label="Button"> discoverProviderModels(provider.name, true)}
                    >
                      <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      Discover Models
                    </Button>
                    <button
                      variant="outline"
                      size="sm"
                      onClick={() = aria-label="Button"> setShowTesting(showTesting === provider.name ? null : provider.name)}
                    >
                      <Activity className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      {showTesting === provider.name ? 'Hide Testing' : 'Test Provider'}
                    </Button>
                    <button
                      variant="outline"
                      size="sm"
                      onClick={() = aria-label="Button"> setShowConfigGuide(showConfigGuide === provider.name ? null : provider.name)}
                    >
                      <Settings className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      {showConfigGuide === provider.name ? 'Hide Guide' : 'Setup Guide'}
                    </Button>
                    <button
                      variant="outline"
                      size="sm"
                      onClick={() = aria-label="Button"> setShowDiagnostics(showDiagnostics === provider.name ? null : provider.name)}
                    >
                      <Eye className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      {showDiagnostics === provider.name ? 'Hide Diagnostics' : 'Diagnostics'}
                    </Button>
                    {provider.documentation_url && (
                      <button
                        variant="outline"
                        size="sm"
                        onClick={() = aria-label="Button"> window.open(provider.documentation_url, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        Documentation
                      </Button>
                    )}
                  </div>
                  {/* Provider Testing Interface */}
                  {showTesting === provider.name && (
                    <div className="mt-4">
                      <ProviderTestingInterface
                        providerName={provider.name}
                        providerType={provider.provider_type}
                        requiresApiKey={provider.requires_api_key}
                        onTestComplete={(result) => {
                          // Update provider status based on test results
                          const updatedProviders = providers.map(p =>
                            p.name === provider.name
                              ? {
                                  ...p,
                                  health_status: result.overall_status === 'passed' ? 'healthy' as const : 'unhealthy' as const,
                                  last_health_check: Date.now(),
                                  error_message: result.overall_status === 'failed' ? 'Validation failed' : undefined
                                }
                              : p
                          );
                          setProviders(updatedProviders);
                        }}
                      />
                    </div>
                  )}
                  {/* Configuration Guide */}
                  {showConfigGuide === provider.name && (
                    <div className="mt-4">
                      <ProviderConfigurationGuide
                        providerName={provider.name}
                        onStepComplete={(stepId) => {
                        }}
                        onConfigurationComplete={() => {
                          // Refresh provider status after configuration
                          checkProviderHealth(provider.name);
                          setShowConfigGuide(null);
                        }}
                      />
                    </div>
                  )}
                  {/* Diagnostics Page */}
                  {showDiagnostics === provider.name && (
                    <div className="mt-4">
                      <ProviderDiagnosticsPage
                        providerName={provider.name}
                        onClose={() => setShowDiagnostics(null)}
                      />
                    </div>
                  )}
                  {/* Error Display */}
                  {provider.error_message && (
                    <div className="mt-4">
                      <ErrorMessageDisplay
                        error={provider.error_message}
                        context={{
                          provider: provider.name,
                          timestamp: provider.last_health_check ? new Date(provider.last_health_check).toISOString() : new Date().toISOString()
                        }}
                        onRetry={() => checkProviderHealth(provider.name)}
                        showTechnicalDetails={false}
                        showSolutions={true}
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
      {/* Information */}
      <Alert>
        <Info className="h-4 w-4 sm:w-auto md:w-full" />
        <AlertTitle>Provider Management</AlertTitle>
        <AlertDescription className="text-sm space-y-2 md:text-base lg:text-lg">
          <p>• Configure API keys for remote providers to enable model access</p>
          <p>• Health checks verify provider connectivity and model availability</p>
          <p>• Local providers run on your machine and don't require API keys</p>
          <p>• Model discovery refreshes the available model list for each provider</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}
