"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Brain,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Settings,
  Key,
  ExternalLink,
  Info,
  Save,
  Loader2,
  Search,
  Filter,
  Zap,
  Shield,
  Eye
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';
import { API_ENDPOINTS } from '@/lib/extensions/constants';

interface LLMProvider {
  name: string;
  description: string;
  category: string;
  requires_api_key: boolean;
  capabilities: string[];
  is_llm_provider: boolean;
  provider_type: string;
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  error_message?: string;
  last_health_check?: number;
  cached_models_count: number;
  last_discovery?: number;
  api_base_url?: string;
}

interface ModelInfo {
  id: string;
  name: string;
  family: string;
  format?: string;
  size?: number;
  parameters?: string;
  quantization?: string;
  context_length?: number;
  capabilities: string[];
  local_path?: string;
  download_url?: string;
  downloads?: number;
  likes?: number;
}

interface LLMProfile {
  id: string;
  name: string;
  description: string;
  router_policy: string;
  providers: Record<string, {
    provider: string;
    model?: string;
    priority: number;
    max_cost_per_1k_tokens?: number;
    required_capabilities: string[];
    excluded_capabilities: string[];
  }>;
  fallback_provider: string;
  fallback_model?: string;
  is_valid: boolean;
  validation_errors: string[];
  created_at: number;
  updated_at: number;
}

interface ApiKeyValidationResult {
  valid: boolean;
  message: string;
  provider: string;
}

const LOCAL_STORAGE_KEYS = {
  selectedProfile: 'llm_selected_profile',
  providerApiKeys: 'llm_provider_api_keys',
  customModels: 'llm_custom_models',
};

/**
 * @file LLMSettings.tsx
 * @description Component for managing LLM provider settings and configuration.
 * Allows users to select providers, configure API keys, and manage LLM profiles.
 */
export default function LLMSettings() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [profiles, setProfiles] = useState<LLMProfile[]>([]);
  const [activeProfile, setActiveProfile] = useState<LLMProfile | null>(null);
  const [providerApiKeys, setProviderApiKeys] = useState<Record<string, string>>({});
  const [customModels, setCustomModels] = useState<Record<string, string>>({});
  const [providerModels, setProviderModels] = useState<Record<string, ModelInfo[]>>({});
  const [loading, setLoading] = useState(true);
  const [healthChecking, setHealthChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validatingKeys, setValidatingKeys] = useState<Record<string, boolean>>({});
  const [keyValidationResults, setKeyValidationResults] = useState<Record<string, ApiKeyValidationResult>>({});
  const [activeTab, setActiveTab] = useState<string>('providers');
  const [providerWarning, setProviderWarning] = useState<string | null>(null);
  const { toast } = useToast();

  const backend = getKarenBackend();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);

      // Load from localStorage
      const storedProfile = localStorage.getItem(LOCAL_STORAGE_KEYS.selectedProfile);
      const storedApiKeys = localStorage.getItem(LOCAL_STORAGE_KEYS.providerApiKeys);
      const storedModels = localStorage.getItem(LOCAL_STORAGE_KEYS.customModels);

      if (storedProfile) setSelectedProfile(storedProfile);
      if (storedApiKeys) setProviderApiKeys(JSON.parse(storedApiKeys));
      if (storedModels) setCustomModels(JSON.parse(storedModels));

      // Load providers and profiles from backend
      await Promise.all([
        loadProviders(),
        loadProfiles()
      ]);

    } catch (error) {
      console.error('Failed to load LLM settings:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'loadSettings');
      toast({
        title: info.title || "Error Loading Settings",
        description: info.message || "Could not load LLM provider settings. Using defaults.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await backend.makeRequestPublic<LLMProvider[]>('/api/providers?llm_only=true');
      setProviders(response || []);
      setProviderWarning(null);
    } catch (error) {
      console.error('Failed to load providers:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'loadProviders');
      const status = (error as any)?.status || (error as any)?.response?.status;
      toast({
        variant: 'destructive',
        title: info.title,
        description: `${info.message} (status: ${status ?? 'unknown'})`
      });
      console.warn('Using fallback providers due to backend error');
      // Use fallback providers if backend is unavailable
      setProviderWarning('Using fallback providers due to backend error.');
      setProviders([
          {
            name: 'openai',
            description: 'OpenAI GPT models via API',
            category: 'LLM',
            requires_api_key: true,
            capabilities: ['streaming', 'embeddings', 'function_calling', 'vision'],
            is_llm_provider: true,
            provider_type: 'remote',
            health_status: 'unknown',
            cached_models_count: 0,
            api_base_url: 'https://api.openai.com/v1'
          },
          {
            name: 'gemini',
            description: 'Google Gemini models via API',
            category: 'LLM',
            requires_api_key: true,
            capabilities: ['streaming', 'embeddings', 'vision'],
            is_llm_provider: true,
            provider_type: 'remote',
            health_status: 'unknown',
            cached_models_count: 0,
            api_base_url: 'https://generativelanguage.googleapis.com/v1beta'
          },
          {
            name: 'deepseek',
            description: 'DeepSeek models optimized for coding and reasoning',
            category: 'LLM',
            requires_api_key: true,
            capabilities: ['streaming', 'function_calling'],
            is_llm_provider: true,
            provider_type: 'remote',
            health_status: 'unknown',
            cached_models_count: 0,
            api_base_url: 'https://api.deepseek.com'
          },
          {
            name: 'local',
            description: 'Local model files (GGUF, safetensors, etc.)',
            category: 'LLM',
            requires_api_key: false,
            capabilities: ['local_execution', 'privacy'],
            is_llm_provider: true,
            provider_type: 'local',
            health_status: 'unknown',
            cached_models_count: 0
          }
        ]);
    }
  };

  const loadProfiles = async () => {
    try {
      const [profilesResponse, activeProfileResponse] = await Promise.all([
        backend.makeRequestPublic<LLMProfile[]>('/api/providers/profiles'),
        backend.makeRequestPublic<LLMProfile | null>('/api/providers/profiles/active')
      ]);
      
      setProfiles(profilesResponse || []);
      setActiveProfile(activeProfileResponse);
    } catch (error) {
      console.error('Failed to load profiles:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'loadProfiles');
      toast({ variant: 'destructive', title: info.title, description: info.message });
      
      // Use fallback profiles
      const fallbackProfiles: LLMProfile[] = [
        {
          id: 'balanced',
          name: 'Balanced',
          description: 'Balanced configuration for general use',
          router_policy: 'balanced',
          providers: {
            chat: {
              provider: 'gemini',
              priority: 80,
              required_capabilities: ['streaming'],
              excluded_capabilities: []
            },
            code: {
              provider: 'deepseek',
              priority: 85,
              required_capabilities: ['streaming'],
              excluded_capabilities: []
            },
            reasoning: {
              provider: 'openai',
              priority: 75,
              required_capabilities: [],
              excluded_capabilities: []
            }
          },
          fallback_provider: 'local',
          is_valid: true,
          validation_errors: [],
          created_at: Date.now(),
          updated_at: Date.now()
        }
      ];
      
      setProfiles(fallbackProfiles);
      setActiveProfile(fallbackProfiles[0]);
    }
  };

  const handleProfileChange = async (profileId: string) => {
    try {
      const response = await backend.makeRequestPublic<LLMProfile>(`/api/providers/profiles/${profileId}/activate`, {
        method: 'POST'
      });
      
      setActiveProfile(response);
      localStorage.setItem(LOCAL_STORAGE_KEYS.selectedProfile, profileId);

      toast({
        title: "Profile Activated",
        description: `Switched to ${response.name} LLM profile.`,
      });
    } catch (error) {
      console.error('Failed to switch profile:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'switchProfile');
      toast({
        variant: 'destructive',
        title: info.title || "Profile Switch Failed",
        description: info.message || "Could not switch to the selected profile.",
      });
    }
  };

  const handleApiKeyChange = async (providerName: string, apiKey: string) => {
    const updatedKeys = { ...providerApiKeys, [providerName]: apiKey };
    setProviderApiKeys(updatedKeys);
    
    // Clear previous validation result
    setKeyValidationResults(prev => {
      const updated = { ...prev };
      delete updated[providerName];
      return updated;
    });
    
    // Validate API key if provided
    if (apiKey.trim()) {
      validateApiKey(providerName, apiKey);
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
        // Discover models for this provider
        discoverProviderModels(providerName);
      }
    } catch (error) {
      console.error(`Failed to validate API key for ${providerName}:`, error);
      setKeyValidationResults(prev => ({ 
        ...prev, 
        [providerName]: {
          valid: false,
          message: 'Validation failed',
          provider: providerName
        }
      }));
    } finally {
      setValidatingKeys(prev => ({ ...prev, [providerName]: false }));
    }
  };

  const discoverProviderModels = async (providerName: string, forceRefresh: boolean = false) => {
    try {
      const response = await backend.makeRequestPublic<ModelInfo[]>(`/api/providers/${providerName}/models?force_refresh=${forceRefresh}`);
      setProviderModels(prev => ({ ...prev, [providerName]: response || [] }));
    } catch (error) {
      console.error(`Failed to discover models for ${providerName}:`, error);
    }
  };

  const handleModelChange = (providerName: string, model: string) => {
    const updatedModels = { ...customModels, [providerName]: model };
    setCustomModels(updatedModels);
  };

  const saveSettings = async () => {
    try {
      setSaving(true);

      // Save to localStorage
      localStorage.setItem(LOCAL_STORAGE_KEYS.providerApiKeys, JSON.stringify(providerApiKeys));
      localStorage.setItem(LOCAL_STORAGE_KEYS.customModels, JSON.stringify(customModels));

      // Save to backend
      await backend.makeRequestPublic('/api/llm/settings', {
        method: 'POST',
        body: JSON.stringify({
          selected_profile: selectedProfile,
          provider_api_keys: providerApiKeys,
          custom_models: customModels,
        }),
      });

      toast({
        title: "Settings Saved",
        description: "Your LLM provider settings have been saved successfully.",
      });

    } catch (error) {
      console.error('Failed to save settings:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'saveSettings');
      toast({
        title: info.title || "Error Saving Settings",
        description: info.message || "Could not save LLM settings. They are saved locally in your browser.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const runHealthCheck = async () => {
    try {
      setHealthChecking(true);

      const response = await backend.makeRequestPublic<Record<string, any>>('/api/providers/health-check-all', {
        method: 'POST'
      });

      // Update provider health status
      const updatedProviders = providers.map(provider => {
        const healthResult = response[provider.name];
        if (healthResult) {
          return {
            ...provider,
            health_status: (healthResult.status === 'healthy' ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'unknown',
            error_message: healthResult.message,
            last_health_check: Date.now()
          };
        }
        return provider;
      });

      setProviders(updatedProviders);

      toast({
        title: "Health Check Complete",
        description: "Provider health status has been updated.",
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
        return <Badge variant="default" className="bg-green-100 text-green-800">Healthy</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
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
        return <Settings className="h-3 w-3" />;
      case 'local_execution':
        return <Shield className="h-3 w-3" />;
      default:
        return <Info className="h-3 w-3" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Loading LLM settings...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {providerWarning && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Provider Endpoint Missing</AlertTitle>
          <AlertDescription>{providerWarning}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="profiles">Profiles</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-6">
          {/* Provider Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    LLM Provider Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure API keys and settings for each LLM provider. CopilotKit is excluded as it's a UI framework, not an LLM provider.
                  </CardDescription>
                </div>
                <Button
                  onClick={runHealthCheck}
                  variant="outline"
                  size="sm"
                  disabled={healthChecking}
                >
                  {healthChecking ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Health Check
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {providers.filter(p => p.is_llm_provider).map((provider) => (
                <div key={provider.name} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getHealthStatusIcon(provider.health_status)}
                        <h4 className="font-medium capitalize">{provider.name}</h4>
                        <Badge variant="secondary" className="text-xs">{provider.provider_type}</Badge>
                      </div>
                      {getHealthStatusBadge(provider.health_status)}
                    </div>
                    <div className="flex gap-1 flex-wrap">
                      {provider.capabilities.map((capability) => (
                        <Badge key={capability} variant="outline" className="text-xs flex items-center gap-1">
                          {getCapabilityIcon(capability)}
                          {capability.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground">{provider.description}</p>

                  {provider.error_message && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Provider Error</AlertTitle>
                      <AlertDescription className="text-xs">
                        {provider.error_message}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {provider.requires_api_key && (
                      <div className="space-y-2">
                        <Label htmlFor={`${provider.name}-api-key`} className="flex items-center gap-2">
                          <Key className="h-4 w-4" />
                          API Key
                          {getValidationIcon(provider.name)}
                        </Label>
                        <Input
                          id={`${provider.name}-api-key`}
                          type="password"
                          value={providerApiKeys[provider.name] || ''}
                          onChange={(e) => handleApiKeyChange(provider.name, e.target.value)}
                          placeholder={`Enter ${provider.name} API key`}
                          className="text-sm"
                        />
                        {keyValidationResults[provider.name] && (
                          <p className={`text-xs ${keyValidationResults[provider.name].valid ? 'text-green-600' : 'text-red-600'}`}>
                            {keyValidationResults[provider.name].message}
                          </p>
                        )}
                      </div>
                    )}

                    <div className="space-y-2">
                      <Label htmlFor={`${provider.name}-model`}>Default Model</Label>
                      <Select
                        value={customModels[provider.name] || ''}
                        onValueChange={(value) => handleModelChange(provider.name, value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a model" />
                        </SelectTrigger>
                        <SelectContent>
                          {providerModels[provider.name]?.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              <div className="flex flex-col">
                                <span className="font-medium">{model.name}</span>
                                <span className="text-xs text-muted-foreground">
                                  {model.parameters && `${model.parameters} • `}
                                  {model.context_length && `${model.context_length.toLocaleString()} tokens`}
                                </span>
                              </div>
                            </SelectItem>
                          )) || []}
                        </SelectContent>
                      </Select>
                      {provider.cached_models_count > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {provider.cached_models_count} models available
                          {provider.last_discovery && (
                            <> • Last updated {new Date(provider.last_discovery * 1000).toLocaleString()}</>
                          )}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Provider-specific help links */}
                  {provider.name === 'openai' && (
                    <div className="text-xs text-muted-foreground">
                      <ExternalLink className="inline h-3 w-3 mr-1" />
                      <a
                        href="https://platform.openai.com/api-keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline"
                      >
                        Get OpenAI API Key
                      </a>
                    </div>
                  )}

                  {provider.name === 'gemini' && (
                    <div className="text-xs text-muted-foreground">
                      <ExternalLink className="inline h-3 w-3 mr-1" />
                      <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline"
                      >
                        Get Google AI API Key
                      </a>
                    </div>
                  )}

                  {provider.name === 'deepseek' && (
                    <div className="text-xs text-muted-foreground">
                      <ExternalLink className="inline h-3 w-3 mr-1" />
                      <a
                        href="https://platform.deepseek.com/api_keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline"
                      >
                        Get DeepSeek API Key
                      </a>
                    </div>
                  )}

                  {provider.name === 'local' && (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        Local provider uses models stored on your machine. No API key required.
                        Models are discovered automatically from your local model directory.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              ))}
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button onClick={saveSettings} disabled={saving}>
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Save Configuration
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="profiles" className="space-y-6">
          {/* Profile Management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                LLM Profile Management
              </CardTitle>
              <CardDescription>
                Manage LLM profiles that determine which providers are used for different tasks.
                Profiles include router policies, guardrails, and provider preferences.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="profile-select">Active Profile</Label>
                <Select 
                  value={activeProfile?.id || ''} 
                  onValueChange={handleProfileChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an LLM profile" />
                  </SelectTrigger>
                  <SelectContent>
                    {profiles.map((profile) => (
                      <SelectItem key={profile.id} value={profile.id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{profile.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {profile.description} • {profile.router_policy}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {activeProfile && (
                <div className="mt-4 p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">Current Profile: {activeProfile.name}</h4>
                    <div className="flex items-center gap-2">
                      <Badge variant={activeProfile.is_valid ? "default" : "destructive"}>
                        {activeProfile.is_valid ? "Valid" : "Invalid"}
                      </Badge>
                      <Badge variant="outline">{activeProfile.router_policy}</Badge>
                    </div>
                  </div>
                  
                  {activeProfile.description && (
                    <p className="text-sm text-muted-foreground mb-3">{activeProfile.description}</p>
                  )}
                  
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(activeProfile.providers).map(([useCase, config]) => (
                      <div key={useCase}>
                        <span className="capitalize">{useCase.replace('_', ' ')}: </span>
                        <Badge variant="outline">{config.provider}</Badge>
                        {config.model && (
                          <span className="text-xs text-muted-foreground ml-1">({config.model})</span>
                        )}
                      </div>
                    ))}
                    <div>
                      Fallback: <Badge variant="outline">{activeProfile.fallback_provider}</Badge>
                    </div>
                  </div>
                  
                  {activeProfile.validation_errors.length > 0 && (
                    <Alert variant="destructive" className="mt-3">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Profile Issues</AlertTitle>
                      <AlertDescription className="text-xs">
                        <ul className="list-disc list-inside">
                          {activeProfile.validation_errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          {/* Model Browser */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Model Browser
              </CardTitle>
              <CardDescription>
                Browse and manage available models from all providers.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(providerModels).map(([providerName, models]) => (
                  <div key={providerName} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium capitalize">{providerName} Models</h4>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => discoverProviderModels(providerName, true)}
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh
                      </Button>
                    </div>
                    
                    {models.length > 0 ? (
                      <div className="grid gap-2">
                        {models.slice(0, 5).map((model) => (
                          <div key={model.id} className="border rounded p-3 text-sm">
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="font-medium">{model.name}</span>
                                {model.parameters && (
                                  <Badge variant="secondary" className="ml-2 text-xs">
                                    {model.parameters}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex gap-1">
                                {model.capabilities.map((cap) => (
                                  <Badge key={cap} variant="outline" className="text-xs">
                                    {cap}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            {model.context_length && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Context: {model.context_length.toLocaleString()} tokens
                              </p>
                            )}
                          </div>
                        ))}
                        {models.length > 5 && (
                          <p className="text-xs text-muted-foreground text-center">
                            ... and {models.length - 5} more models
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No models discovered yet. Configure API key to discover models.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Information */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Configuration Notes</AlertTitle>
        <AlertDescription className="text-sm space-y-2">
          <p>• API keys are validated in real-time and stored locally for convenience</p>
          <p>• CopilotKit is excluded from LLM providers as it's a UI framework</p>
          <p>• Profile changes take effect immediately for new conversations</p>
          <p>• Models are discovered automatically when valid API keys are provided</p>
          <p>• Local providers don't require API keys and scan for local model files</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}