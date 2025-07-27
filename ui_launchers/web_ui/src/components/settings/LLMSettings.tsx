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
  Loader2
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

interface LLMProvider {
  name: string;
  provider_class: string;
  description: string;
  supports_streaming: boolean;
  supports_embeddings: boolean;
  requires_api_key: boolean;
  default_model: string;
  health_status: 'healthy' | 'unhealthy' | 'unknown';
  last_health_check?: number;
  error_message?: string;
}

interface LLMProfile {
  name: string;
  providers: {
    chat: string;
    conversation_processing: string;
    code: string;
    generic: string;
  };
  fallback: string;
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
  const [selectedProfile, setSelectedProfile] = useState<string>('default');
  const [providerApiKeys, setProviderApiKeys] = useState<Record<string, string>>({});
  const [customModels, setCustomModels] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [healthChecking, setHealthChecking] = useState(false);
  const [saving, setSaving] = useState(false);
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
      toast({
        title: "Error Loading Settings",
        description: "Could not load LLM provider settings. Using defaults.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await backend.makeRequestPublic<{ providers: LLMProvider[] }>('/api/llm/providers');
      setProviders(response.providers || []);
    } catch (error) {
      console.error('Failed to load providers:', error);
      // Use fallback providers if backend is unavailable
      setProviders([
        {
          name: 'ollama',
          provider_class: 'OllamaProvider',
          description: 'Local Ollama server for running open-source models',
          supports_streaming: true,
          supports_embeddings: true,
          requires_api_key: false,
          default_model: 'llama3.2:latest',
          health_status: 'unknown'
        },
        {
          name: 'openai',
          provider_class: 'OpenAIProvider',
          description: 'OpenAI GPT models via API',
          supports_streaming: true,
          supports_embeddings: true,
          requires_api_key: true,
          default_model: 'gpt-3.5-turbo',
          health_status: 'unknown'
        },
        {
          name: 'gemini',
          provider_class: 'GeminiProvider',
          description: 'Google Gemini models via API',
          supports_streaming: true,
          supports_embeddings: true,
          requires_api_key: true,
          default_model: 'gemini-1.5-flash',
          health_status: 'unknown'
        }
      ]);
    }
  };

  const loadProfiles = async () => {
    try {
      const response = await backend.makeRequestPublic<{ profiles: LLMProfile[] }>('/api/llm/profiles');
      setProfiles(response.profiles || []);
    } catch (error) {
      console.error('Failed to load profiles:', error);
      // Use fallback profiles
      setProfiles([
        {
          name: 'default',
          providers: {
            chat: 'ollama',
            conversation_processing: 'ollama',
            code: 'deepseek',
            generic: 'ollama'
          },
          fallback: 'openai'
        },
        {
          name: 'enterprise',
          providers: {
            chat: 'openai',
            conversation_processing: 'openai',
            code: 'openai',
            generic: 'openai'
          },
          fallback: 'openai'
        }
      ]);
    }
  };

  const handleProfileChange = (profileName: string) => {
    setSelectedProfile(profileName);
    localStorage.setItem(LOCAL_STORAGE_KEYS.selectedProfile, profileName);

    toast({
      title: "Profile Updated",
      description: `Switched to ${profileName} LLM profile.`,
    });
  };

  const handleApiKeyChange = (providerName: string, apiKey: string) => {
    const updatedKeys = { ...providerApiKeys, [providerName]: apiKey };
    setProviderApiKeys(updatedKeys);
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
      toast({
        title: "Error Saving Settings",
        description: "Could not save LLM settings. They are saved locally in your browser.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const runHealthCheck = async () => {
    try {
      setHealthChecking(true);

      const response = await backend.makeRequestPublic<{ results: Record<string, any> }>('/api/llm/health-check', {
        method: 'POST'
      });

      // Update provider health status
      const updatedProviders = providers.map(provider => {
        const healthResult = response.results[provider.name];
        if (healthResult) {
          return {
            ...provider,
            health_status: (healthResult.status === 'healthy' ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'unknown',
            error_message: healthResult.error,
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
      toast({
        title: "Health Check Failed",
        description: "Could not check provider health status.",
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

  const currentProfile = profiles.find(p => p.name === selectedProfile);

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
      {/* Profile Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            LLM Profile Selection
          </CardTitle>
          <CardDescription>
            Choose a pre-configured LLM profile that determines which providers are used for different tasks.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="profile-select">Active Profile</Label>
            <Select value={selectedProfile} onValueChange={handleProfileChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select an LLM profile" />
              </SelectTrigger>
              <SelectContent>
                {profiles.map((profile) => (
                  <SelectItem key={profile.name} value={profile.name}>
                    <div className="flex flex-col">
                      <span className="font-medium capitalize">{profile.name}</span>
                      <span className="text-xs text-muted-foreground">
                        Chat: {profile.providers.chat} | Code: {profile.providers.code}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {currentProfile && (
            <div className="mt-4 p-4 bg-muted/30 rounded-lg">
              <h4 className="font-medium mb-2">Current Profile Configuration</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Chat: <Badge variant="outline">{currentProfile.providers.chat}</Badge></div>
                <div>Code: <Badge variant="outline">{currentProfile.providers.code}</Badge></div>
                <div>Processing: <Badge variant="outline">{currentProfile.providers.conversation_processing}</Badge></div>
                <div>Fallback: <Badge variant="outline">{currentProfile.fallback}</Badge></div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Provider Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Provider Configuration
              </CardTitle>
              <CardDescription>
                Configure API keys and models for each LLM provider.
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
          {providers.map((provider) => (
            <div key={provider.name} className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {getHealthStatusIcon(provider.health_status)}
                    <h4 className="font-medium capitalize">{provider.name}</h4>
                  </div>
                  {getHealthStatusBadge(provider.health_status)}
                </div>
                <div className="flex gap-2">
                  {provider.supports_streaming && (
                    <Badge variant="secondary" className="text-xs">Streaming</Badge>
                  )}
                  {provider.supports_embeddings && (
                    <Badge variant="secondary" className="text-xs">Embeddings</Badge>
                  )}
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
                    </Label>
                    <Input
                      id={`${provider.name}-api-key`}
                      type="password"
                      value={providerApiKeys[provider.name] || ''}
                      onChange={(e) => handleApiKeyChange(provider.name, e.target.value)}
                      placeholder={`Enter ${provider.name} API key`}
                      className="text-sm"
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor={`${provider.name}-model`}>Default Model</Label>
                  <Input
                    id={`${provider.name}-model`}
                    value={customModels[provider.name] || provider.default_model}
                    onChange={(e) => handleModelChange(provider.name, e.target.value)}
                    placeholder={provider.default_model}
                    className="text-sm"
                  />
                </div>
              </div>

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

              {provider.name === 'ollama' && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    Ollama runs locally on your machine. Make sure Ollama is installed and running.
                    <a
                      href="https://ollama.ai"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block mt-1 text-primary underline"
                    >
                      Download Ollama <ExternalLink className="inline h-3 w-3 ml-0.5" />
                    </a>
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

      {/* Information */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Configuration Notes</AlertTitle>
        <AlertDescription className="text-sm space-y-2">
          <p>• API keys are stored locally in your browser for convenience</p>
          <p>• Server-side configuration may be required for full functionality</p>
          <p>• Health checks verify provider availability and authentication</p>
          <p>• Profile changes take effect immediately for new conversations</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}