"use client";

import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Bot, ExternalLink, KeyRound, Loader2, RefreshCw, Save, Server } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import OllamaModelManager from './OllamaModelManager';
import { useToast } from '@/hooks/use-toast';
import { ApiError, apiClient } from '@/lib/api';

interface ProviderModel {
  id: string;
  name: string;
  family: string;
  source: string;
}

interface ProviderDetails {
  id: string;
  display_name: string;
  description: string;
  provider_type: string;
  docs_url?: string | null;
  base_url?: string | null;
  default_base_url?: string | null;
  default_model?: string | null;
  selected_model?: string | null;
  models: ProviderModel[];
  requires_api_key: boolean;
  api_key_configured: boolean;
  api_key_header: string;
  api_key_prefix: string;
  custom_headers: Record<string, string>;
  supports_base_url_override: boolean;
  supports_model_discovery: boolean;
  supports_model_pull: boolean;
  supports_custom_auth: boolean;
  supports_manual_model_entry: boolean;
}

interface ModelSettingsResponse {
  selected_provider: string;
  selected_model: string;
  providers: ProviderDetails[];
}

interface ProviderModelsResponse {
  provider: string;
  base_url?: string | null;
  models: ProviderModel[];
}

interface OllamaTagsResponse {
  models?: Array<{
    name?: string;
    model?: string;
    details?: {
      family?: string;
    };
  }>;
}

function buildProviderGroups(providers: ProviderDetails[]) {
  const cloudProviders = providers.filter((provider) => provider.provider_type !== 'local');
  const localProviders = providers.filter((provider) => provider.provider_type === 'local');
  return { cloudProviders, localProviders };
}

function providerTypeLabel(provider: ProviderDetails): string {
  return provider.provider_type === 'local' ? 'Local' : 'Cloud';
}

function formatErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function normalizeLocalOllamaAddress(address: string): string {
  return (address.trim() || 'http://localhost:11434').replace(/\/api\/?$/, '').replace(/\/$/, '');
}

function canUseLocalOllamaAddress(address?: string): boolean {
  if (!address?.trim()) {
    return false;
  }

  try {
    const parsed = new URL(normalizeLocalOllamaAddress(address));
    return ['localhost', '127.0.0.1'].includes(parsed.hostname);
  } catch {
    const normalized = normalizeLocalOllamaAddress(address);
    return normalized.startsWith('http://localhost') || normalized.startsWith('http://127.0.0.1');
  }
}

async function parseOllamaModels(response: Response): Promise<ProviderModel[]> {
  if (!response.ok) {
    throw new Error(`Ollama returned HTTP ${response.status}`);
  }

  const data = await response.json() as OllamaTagsResponse;
  const rawModels = Array.isArray(data.models) ? data.models : [];

  return rawModels
    .map((model) => {
      const id = model.name?.trim() || model.model?.trim() || '';
      if (!id) {
        return null;
      }

      return {
        id,
        name: id,
        family: model.details?.family || 'unknown',
        source: 'discovered',
      } satisfies ProviderModel;
    })
    .filter((model): model is ProviderModel => model !== null);
}

async function loadLocalOllamaModels(address: string): Promise<ProviderModel[]> {
  const normalized = normalizeLocalOllamaAddress(address);

  try {
    return parseOllamaModels(
      await fetch(`/api/ollama/tags?base_url=${encodeURIComponent(normalized)}`, { cache: 'no-store' }),
    );
  } catch {
    return await parseOllamaModels(await fetch(`${normalized}/api/tags`, { cache: 'no-store' }));
  }
}

export default function ModelSettings() {
  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('ollama');
  const [selectedModel, setSelectedModel] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiKeyHeader, setApiKeyHeader] = useState('Authorization');
  const [apiKeyPrefix, setApiKeyPrefix] = useState('Bearer');
  const [availableModels, setAvailableModels] = useState<ProviderModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isClearingKey, setIsClearingKey] = useState(false);
  const { toast } = useToast();

  const selectedProviderDetails = useMemo(() => {
    return settings?.providers.find((provider) => provider.id === selectedProvider) ?? null;
  }, [selectedProvider, settings]);

  const providerGroups = useMemo(() => {
    return buildProviderGroups(settings?.providers ?? []);
  }, [settings]);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<ModelSettingsResponse>('/api/settings/model');
      setSettings(response);
      setSelectedProvider(response.selected_provider || response.providers[0]?.id || 'ollama');
      setSelectedModel(response.selected_model || '');
    } catch (error) {
      toast({
        title: 'Unable to load model settings',
        description: formatErrorMessage(error, 'Karen could not load the saved model configuration.'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadProviderModels = async (providerId: string, providerBaseUrl?: string) => {
    if (!providerId) {
      return;
    }

    setIsLoadingModels(true);
    try {
      if (providerId === 'ollama' && canUseLocalOllamaAddress(providerBaseUrl)) {
        const models = await loadLocalOllamaModels(providerBaseUrl || '');
        setAvailableModels(models);
        setSelectedModel((previousModel) => {
          if (models.length === 0) {
            return previousModel;
          }
          if (models.some((model) => model.id === previousModel)) {
            return previousModel;
          }
          return models[0].id;
        });
        return;
      }

      const query = providerBaseUrl?.trim() ? `?base_url=${encodeURIComponent(providerBaseUrl.trim())}` : '';
      const response = await apiClient.get<ProviderModelsResponse>(`/api/settings/model/providers/${providerId}/models${query}`);
      setAvailableModels(response.models);

      setSelectedModel((previousModel) => {
        if (response.models.length === 0) {
          return previousModel;
        }
        if (response.models.some((model) => model.id === previousModel)) {
          return previousModel;
        }
        return response.models[0].id;
      });
    } catch (error) {
      setAvailableModels(selectedProviderDetails?.models ?? []);
      toast({
        title: 'Model discovery failed',
        description: formatErrorMessage(error, `Karen could not refresh models for ${providerId}.`),
        variant: 'destructive',
      });
    } finally {
      setIsLoadingModels(false);
    }
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  useEffect(() => {
    if (!selectedProviderDetails) {
      return;
    }

    const providerDefaultModel = selectedProviderDetails.selected_model
      || selectedProviderDetails.default_model
      || selectedProviderDetails.models[0]?.id
      || '';
    const providerBaseUrl = selectedProviderDetails.base_url || selectedProviderDetails.default_base_url || '';
    const displayBaseUrl = selectedProviderDetails.id === 'ollama'
      ? providerBaseUrl.replace(/\/api$/, '')
      : providerBaseUrl;

    setBaseUrl(displayBaseUrl);
    setApiKey('');
    setApiKeyHeader(selectedProviderDetails.api_key_header || 'Authorization');
    setApiKeyPrefix(selectedProviderDetails.api_key_prefix ?? 'Bearer');
    setAvailableModels(selectedProviderDetails.models);
    setSelectedModel(providerDefaultModel);

    void loadProviderModels(selectedProviderDetails.id, providerBaseUrl);
  }, [selectedProviderDetails]);

  const handleSave = async () => {
    if (!selectedProviderDetails) {
      return;
    }

    if (!selectedModel.trim()) {
      toast({
        title: 'Model required',
        description: 'Select or enter the model Karen should use.',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);
    try {
      const response = await apiClient.put<ModelSettingsResponse>('/api/settings/model', {
        provider: selectedProvider,
        model: selectedModel.trim(),
        base_url: baseUrl.trim(),
        api_key: apiKey.trim() || undefined,
        api_key_header: selectedProviderDetails.supports_custom_auth ? apiKeyHeader.trim() : undefined,
        api_key_prefix: selectedProviderDetails.supports_custom_auth ? apiKeyPrefix : undefined,
      });

      setSettings(response);
      setSelectedProvider(response.selected_provider);
      setSelectedModel(response.selected_model);
      setApiKey('');

      toast({
        title: 'Model settings saved',
        description: `${selectedProviderDetails.display_name} is now configured for Karen.`,
      });
    } catch (error) {
      toast({
        title: 'Save failed',
        description: formatErrorMessage(error, 'Karen could not save the model configuration.'),
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearApiKey = async () => {
    if (!selectedProviderDetails || !selectedProviderDetails.api_key_configured) {
      return;
    }

    setIsClearingKey(true);
    try {
      const response = await apiClient.put<ModelSettingsResponse>('/api/settings/model', {
        provider: selectedProvider,
        model: selectedModel.trim(),
        base_url: baseUrl.trim(),
        clear_api_key: true,
        api_key_header: selectedProviderDetails.supports_custom_auth ? apiKeyHeader.trim() : undefined,
        api_key_prefix: selectedProviderDetails.supports_custom_auth ? apiKeyPrefix : undefined,
      });

      setSettings(response);
      setApiKey('');
      toast({
        title: 'API key removed',
        description: `${selectedProviderDetails.display_name} credentials were cleared from Karen.`,
      });
    } catch (error) {
      toast({
        title: 'Unable to clear API key',
        description: formatErrorMessage(error, 'Karen could not clear the saved credential.'),
        variant: 'destructive',
      });
    } finally {
      setIsClearingKey(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-lg">
            <Bot className="mr-2 h-5 w-5" /> AI Model Configuration
          </CardTitle>
          <CardDescription>Loading the current provider configuration.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="h-10 animate-pulse rounded-md bg-muted" />
          <div className="h-10 animate-pulse rounded-md bg-muted" />
          <div className="h-24 animate-pulse rounded-md bg-muted" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center text-lg">
          <Bot className="mr-2 h-5 w-5" /> AI Model Configuration
        </CardTitle>
        <CardDescription>
          Configure the AI provider and model Karen should use for generating responses.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="ai-provider">AI Provider</Label>
          <Select value={selectedProvider} onValueChange={setSelectedProvider}>
            <SelectTrigger id="ai-provider">
              <SelectValue placeholder="Select an AI provider" />
            </SelectTrigger>
            <SelectContent>
              {providerGroups.cloudProviders.map((provider) => (
                <SelectItem key={provider.id} value={provider.id}>
                  {provider.display_name} (Cloud)
                </SelectItem>
              ))}
              {providerGroups.localProviders.map((provider) => (
                <SelectItem key={provider.id} value={provider.id}>
                  {provider.display_name} (Local)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedProviderDetails && (
          <div className="space-y-6 border-l-2 border-primary/20 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">{providerTypeLabel(selectedProviderDetails)}</Badge>
              {selectedProviderDetails.api_key_configured && (
                <Badge variant="outline">Credential Stored</Badge>
              )}
              {selectedProviderDetails.supports_model_discovery && (
                <Badge variant="outline">Model Discovery</Badge>
              )}
            </div>

            <Alert>
              <AlertTitle>{selectedProviderDetails.display_name}</AlertTitle>
              <AlertDescription className="space-y-2 text-xs">
                <p>{selectedProviderDetails.description}</p>
                {selectedProviderDetails.docs_url && (
                  <a
                    href={selectedProviderDetails.docs_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center text-primary hover:underline"
                  >
                    Provider setup documentation <ExternalLink className="ml-1 h-3.5 w-3.5" />
                  </a>
                )}
              </AlertDescription>
            </Alert>

            {selectedProvider === 'ollama' && (
              <OllamaModelManager
                ollamaAddress={baseUrl}
                selectedModel={selectedModel}
                onAddressChange={setBaseUrl}
                onModelSelect={setSelectedModel}
                onModelsDiscovered={setAvailableModels}
              />
            )}

            {selectedProvider !== 'ollama' && (
              <>
                {selectedProviderDetails.supports_base_url_override && (
                  <div className="space-y-2">
                    <Label htmlFor="provider-base-url" className="flex items-center">
                      <Server className="mr-2 h-4 w-4 text-primary/80" /> Endpoint
                    </Label>
                    <Input
                      id="provider-base-url"
                      value={baseUrl}
                      onChange={(event) => setBaseUrl(event.target.value)}
                      placeholder={selectedProviderDetails.default_base_url || 'Enter the provider base URL'}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <Label htmlFor="cloud-model">Select Model</Label>
                    {selectedProviderDetails.supports_model_discovery && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => loadProviderModels(selectedProviderDetails.id, baseUrl)}
                        disabled={isLoadingModels}
                      >
                        {isLoadingModels ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                        Refresh Models
                      </Button>
                    )}
                  </div>

                  {availableModels.length > 0 && selectedProvider !== 'custom' ? (
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                      <SelectTrigger id="cloud-model">
                        <SelectValue placeholder="Select a model" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input
                      id="cloud-model"
                      value={selectedModel}
                      onChange={(event) => setSelectedModel(event.target.value)}
                      placeholder="Enter the exact model identifier"
                    />
                  )}
                </div>

                {selectedProviderDetails.requires_api_key && (
                  <div className="space-y-2">
                    <Label htmlFor="provider-api-key" className="flex items-center">
                      <KeyRound className="mr-2 h-4 w-4 text-primary/80" /> API Key
                    </Label>
                    <Input
                      id="provider-api-key"
                      type="password"
                      value={apiKey}
                      onChange={(event) => setApiKey(event.target.value)}
                      placeholder={`Enter your ${selectedProviderDetails.display_name} API key`}
                    />
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>
                        {selectedProviderDetails.api_key_configured
                          ? 'A credential is already stored securely. Enter a new key only if you want to replace it.'
                          : 'Karen stores provider credentials on the backend, not in the browser.'}
                      </span>
                      {selectedProviderDetails.api_key_configured && (
                        <Button type="button" variant="outline" size="sm" onClick={handleClearApiKey} disabled={isClearingKey}>
                          {isClearingKey ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                          Clear Saved Key
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                {selectedProviderDetails.supports_custom_auth && (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="provider-auth-header">Auth Header</Label>
                      <Input
                        id="provider-auth-header"
                        value={apiKeyHeader}
                        onChange={(event) => setApiKeyHeader(event.target.value)}
                        placeholder="Authorization"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="provider-auth-prefix">Auth Prefix</Label>
                      <Input
                        id="provider-auth-prefix"
                        value={apiKeyPrefix}
                        onChange={(event) => setApiKeyPrefix(event.target.value)}
                        placeholder="Bearer"
                      />
                    </div>
                  </div>
                )}
              </>
            )}

            {Object.keys(selectedProviderDetails.custom_headers).length > 0 && (
              <Alert>
                <AlertDescription className="text-xs">
                  Required provider headers: {Object.entries(selectedProviderDetails.custom_headers).map(([key, value]) => `${key}: ${value}`).join(', ')}
                </AlertDescription>
              </Alert>
            )}

            {selectedProvider === 'llama-cpp' && (
              <Alert>
                <AlertDescription className="text-xs">
                  Karen can use either discovered local GGUF files or models served by a local llama.cpp-compatible endpoint.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Model Settings
              </Button>
            </div>

            <Alert variant="default">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Production Provider Coverage</AlertTitle>
              <AlertDescription className="text-xs">
                This settings flow is wired for OpenAI, Gemini, Anthropic, DeepSeek, Mistral, Groq, xAI, Qwen, Z.ai, Hugging Face, Ollama, llama.cpp, and custom OpenAI-compatible endpoints.
              </AlertDescription>
            </Alert>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
