"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Bot,
  CheckCircle2,
  ExternalLink,
  KeyRound,
  Loader2,
  RefreshCw,
  Save,
  Server,
  HardDrive,
  XCircle,
  PlusCircle,
  ShieldCheck,
  Settings2,
  Info,
  InfoIcon
} from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue, SelectSeparator } from '../ui/select';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { ApiError, apiClient } from '@/lib/api';
import { useIsMobile } from '@/hooks/use-mobile';
import { cn } from '@/lib/utils';

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
  selectable?: boolean;
  docs_url?: string | null;
  base_url?: string | null;
  default_base_url?: string | null;
  default_model?: string | null;
  selected_model?: string | null;
  models: ProviderModel[];
  requires_api_key: boolean;
  api_key_configured: boolean;
  api_key_masked?: string | null;
  api_key_header: string;
  api_key_prefix: string;
  custom_headers: Record<string, string>;
  supports_base_url_override: boolean;
  supports_model_discovery: boolean;
  supports_model_pull: boolean;
  supports_custom_auth: boolean;
  supports_manual_model_entry: boolean;
  runtime_source?: 'host' | 'container' | null;
  runtime_options?: Array<{
    source: 'host' | 'container';
    label: string;
    base_url: string;
    available: boolean;
    active?: boolean;
    status: string;
    message: string;
    setup_required?: boolean;
    setup_command?: string | null;
    install_supported?: boolean;
  }>;
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
  const localProviders = providers.filter((p) => p.provider_type === 'local');
  const customProviders = providers.filter((p) => p.id === 'custom' || p.provider_type === 'custom' || p.supports_custom_auth);
  const cloudProviders = providers.filter((p) => p.provider_type !== 'local' && !customProviders.some((custom) => custom.id === p.id));
  return { localProviders, cloudProviders, customProviders };
}

function formatErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function formatProviderCredentialMessage(providerName: string, message: string): string {
  const trimmed = message.trim();
  const lowered = trimmed.toLowerCase();

  if (lowered.includes('token expired') || lowered.includes('expired') || lowered.includes('incorrect') || lowered.includes('401') || lowered.includes('unauthorized')) {
    return `${providerName} rejected the saved credential. Replace the stored API key/token and try again.`;
  }

  if (lowered.includes('api key') || lowered.includes('credential') || lowered.includes('forbidden')) {
    return `${providerName} credential validation failed: ${trimmed}`;
  }

  return `${providerName} validation failed: ${trimmed}`;
}

function normalizeLocalOllamaAddress(address: string): string {
  return (address.trim() || 'http://localhost:11434').replace(/\/api\/?$/, '').replace(/\/$/, '');
}

function normalizeConfiguredOllamaAddress(address?: string | null): string {
  const normalized = normalizeLocalOllamaAddress(address || 'http://host.docker.internal:11434');
  try {
    const parsed = new URL(normalized);
    if (parsed.hostname === 'ollama') {
      return normalized.replace('://ollama', '://host.docker.internal');
    }
  } catch {
    if (normalized.startsWith('http://ollama')) {
      return normalized.replace('http://ollama', 'http://host.docker.internal');
    }
  }
  return normalized;
}

function canUseLocalOllamaAddress(address?: string): boolean {
  if (!address?.trim()) return false;
  try {
    const parsed = new URL(normalizeConfiguredOllamaAddress(address));
    return ['localhost', '127.0.0.1'].includes(parsed.hostname);
  } catch {
    const normalized = normalizeConfiguredOllamaAddress(address);
    return normalized.startsWith('http://localhost') || normalized.startsWith('http://127.0.0.1');
  }
}

async function parseOllamaModels(response: Response): Promise<ProviderModel[]> {
  if (!response.ok) throw new Error(`Ollama returned HTTP ${response.status}`);
  const data = await response.json() as OllamaTagsResponse;
  const rawModels = Array.isArray(data.models) ? data.models : [];
  return rawModels.map((m) => {
    const id = m.name?.trim() || m.model?.trim() || '';
    if (!id) return null;
    return { id, name: id, family: m.details?.family || 'unknown', source: 'discovered' } satisfies ProviderModel;
  }).filter((m): m is ProviderModel => m !== null);
}

async function loadLocalOllamaModels(address: string): Promise<ProviderModel[]> {
  const normalized = normalizeConfiguredOllamaAddress(address);
  try {
    return parseOllamaModels(await fetch(`/api/ollama/tags?base_url=${encodeURIComponent(normalized)}`, { cache: 'no-store' }));
  } catch {
    return await parseOllamaModels(await fetch(`${normalized}/api/tags`, { cache: 'no-store' }));
  }
}

export default function ModelSettings() {
  const isMobile = useIsMobile();
  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('ollama');
  const [selectedModel, setSelectedModel] = useState('');
  const [runtimeSource, setRuntimeSource] = useState<'host' | 'container'>('host');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isEditingApiKey, setIsEditingApiKey] = useState(false);
  const [apiKeyHeader, setApiKeyHeader] = useState('Authorization');
  const [apiKeyPrefix, setApiKeyPrefix] = useState('Bearer');
  const [availableModels, setAvailableModels] = useState<ProviderModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isClearingKey, setIsClearingKey] = useState(false);
  
  // Custom Provider State
  const [isCustomDialogOpen, setIsCustomDialogOpen] = useState(false);
  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [customProviderForm, setCustomProviderForm] = useState({
    name: '',
    displayName: '',
    description: '',
    baseUrl: '',
    model: '',
    authHeader: 'Authorization',
    authPrefix: 'Bearer',
  });

  const [apiKeyValidationState, setApiKeyValidationState] = useState<'idle' | 'validating' | 'valid' | 'invalid'>('idle');
  const [apiKeyValidationMessage, setApiKeyValidationMessage] = useState('');
  const validationRequestId = useRef(0);
  const { toast } = useToast();

  const selectedProviderDetails = useMemo(() => {
    return settings?.providers.find((p) => p.id === selectedProvider) ?? null;
  }, [selectedProvider, settings]);

  const providerGroups = useMemo(() => {
    return buildProviderGroups(settings?.providers ?? []);
  }, [settings]);

  const selectedRuntimeOption = useMemo(() => {
    if (selectedProviderDetails?.id !== 'ollama') return null;
    return selectedProviderDetails.runtime_options?.find((option) => option.source === runtimeSource) ?? null;
  }, [selectedProviderDetails, runtimeSource]);

  const loadSettings = useCallback(async () => {
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
  }, [toast]);

  const loadProviderModels = useCallback(async (providerId: string, providerBaseUrl?: string) => {
    if (!providerId) return;
    setIsLoadingModels(true);
    try {
      if (providerId === 'ollama' && canUseLocalOllamaAddress(providerBaseUrl)) {
        const models = await loadLocalOllamaModels(providerBaseUrl || '');
        setAvailableModels(models);
        return;
      }
      const query = providerBaseUrl?.trim() ? `?base_url=${encodeURIComponent(providerBaseUrl.trim())}` : '';
      const response = await apiClient.get<ProviderModelsResponse>(`/api/settings/model/providers/${providerId}/models${query}`);
      setAvailableModels(response.models);
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
  }, [toast, selectedProviderDetails?.models]);

  useEffect(() => { void loadSettings(); }, [loadSettings]);

  useEffect(() => {
    if (!selectedProviderDetails) return;
    const providerDefaultModel = selectedProviderDetails.selected_model || selectedProviderDetails.default_model || selectedProviderDetails.models[0]?.id || '';
    const providerBaseUrl = selectedProviderDetails.id === 'ollama'
      ? normalizeConfiguredOllamaAddress(selectedProviderDetails.base_url || selectedProviderDetails.default_base_url || '')
      : (selectedProviderDetails.base_url || selectedProviderDetails.default_base_url || '');
    if (selectedProviderDetails.id === 'ollama') {
      setRuntimeSource(selectedProviderDetails.runtime_source === 'container' ? 'container' : 'host');
    }
    setBaseUrl(selectedProviderDetails.id === 'ollama' ? providerBaseUrl.replace(/\/api$/, '') : providerBaseUrl);
    setApiKey('');
    setIsEditingApiKey(false);
    setApiKeyValidationState('idle');
    setApiKeyValidationMessage('');
    setApiKeyHeader(selectedProviderDetails.api_key_header || 'Authorization');
    setApiKeyPrefix(selectedProviderDetails.api_key_prefix ?? 'Bearer');
    setAvailableModels(selectedProviderDetails.models);
    setSelectedModel(providerDefaultModel);
    void loadProviderModels(selectedProviderDetails.id, providerBaseUrl);
  }, [selectedProviderDetails, loadProviderModels]);

  useEffect(() => {
    if (selectedProviderDetails?.id !== 'ollama') return;
    if (!selectedRuntimeOption) return;
    const derivedBaseUrl = normalizeConfiguredOllamaAddress(selectedRuntimeOption.base_url);
    setBaseUrl(derivedBaseUrl.replace(/\/api$/, ''));
  }, [selectedProviderDetails, selectedRuntimeOption]);

  useEffect(() => {
    if (!selectedProviderDetails?.requires_api_key) {
      setApiKeyValidationState('idle');
      setApiKeyValidationMessage('');
      return;
    }
    const candidateKey = apiKey.trim();
    if (!candidateKey) {
      setApiKeyValidationState(selectedProviderDetails.api_key_configured ? 'valid' : 'idle');
      setApiKeyValidationMessage(selectedProviderDetails.api_key_configured ? `${selectedProviderDetails.display_name} key is stored.` : '');
      return;
    }
    const currentRequestId = ++validationRequestId.current;
    setApiKeyValidationState('validating');
    setApiKeyValidationMessage(`Validating ${selectedProviderDetails.display_name} key...`);

    const timeoutId = window.setTimeout(async () => {
      try {
        const response = await apiClient.post<{ valid: boolean; message: string; }>('/api/settings/model/validate', {
          provider: selectedProviderDetails.id,
          model: selectedModel,
          api_key: candidateKey,
          base_url: selectedProviderDetails.supports_base_url_override ? baseUrl.trim() || undefined : undefined,
        });
        if (validationRequestId.current !== currentRequestId) return;
        setApiKeyValidationState(response.valid ? 'valid' : 'invalid');
        setApiKeyValidationMessage(
          response.valid
            ? response.message
            : formatProviderCredentialMessage(selectedProviderDetails.display_name, response.message),
        );
      } catch (error) {
        if (validationRequestId.current !== currentRequestId) return;
        setApiKeyValidationState('invalid');
        setApiKeyValidationMessage(
          formatProviderCredentialMessage(
            selectedProviderDetails.display_name,
            formatErrorMessage(error, `Unable to validate ${selectedProviderDetails.display_name} key.`),
          ),
        );
      }
    }, 450);
    return () => { window.clearTimeout(timeoutId); };
  }, [apiKey, baseUrl, selectedModel, selectedProviderDetails]);

  const validateProviderCredentialsBeforeSave = async (): Promise<boolean> => {
    if (!selectedProviderDetails?.requires_api_key) return true;

    if (apiKeyValidationState === 'validating') {
      const message = `Validation for ${selectedProviderDetails.display_name} is still in progress. Wait for it to finish before saving.`;
      setApiKeyValidationState('invalid');
      setApiKeyValidationMessage(message);
      toast({ title: 'Credential check still running', description: message, variant: 'destructive' });
      return false;
    }

    try {
      const response = await apiClient.post<{ valid: boolean; message: string; }>('/api/settings/model/validate', {
        provider: selectedProviderDetails.id,
        model: selectedModel.trim(),
        api_key: apiKey.trim() || undefined,
        base_url: selectedProviderDetails.supports_base_url_override ? baseUrl.trim() || undefined : undefined,
      });

      if (!response.valid) {
        const message = formatProviderCredentialMessage(selectedProviderDetails.display_name, response.message);
        setApiKeyValidationState('invalid');
        setApiKeyValidationMessage(message);
        setIsEditingApiKey(true);
        toast({
          title: `${selectedProviderDetails.display_name} credential rejected`,
          description: message,
          variant: 'destructive',
        });
        return false;
      }

      setApiKeyValidationState('valid');
      setApiKeyValidationMessage(response.message);
      return true;
    } catch (error) {
      const message = formatProviderCredentialMessage(
        selectedProviderDetails.display_name,
        formatErrorMessage(error, `Unable to validate ${selectedProviderDetails.display_name} key.`),
      );
      setApiKeyValidationState('invalid');
      setApiKeyValidationMessage(message);
      setIsEditingApiKey(true);
      toast({
        title: `${selectedProviderDetails.display_name} credential rejected`,
        description: message,
        variant: 'destructive',
      });
      return false;
    }
  };

  const handleSave = async () => {
    if (!selectedProviderDetails) return;
    if (!selectedModel.trim()) {
      toast({ title: 'Model required', description: 'Select or enter the model Karen should use.', variant: 'destructive' });
      return;
    }
    setIsSaving(true);
    try {
      const submittedApiKey = apiKey.trim();
      if (selectedProviderDetails.requires_api_key) {
        const credentialsValid = await validateProviderCredentialsBeforeSave();
        if (!credentialsValid) return;
      } else if (submittedApiKey && apiKeyValidationState === 'invalid') {
        throw new Error(apiKeyValidationMessage || `${selectedProviderDetails.display_name} API key validation failed.`);
      }
      const response = await apiClient.put<ModelSettingsResponse>('/api/settings/model', {
        provider: selectedProvider,
        model: selectedModel.trim(),
        base_url: selectedProviderDetails.supports_base_url_override ? baseUrl.trim() : undefined,
        runtime_source: selectedProviderDetails.id === 'ollama' ? runtimeSource : undefined,
        api_key: submittedApiKey || undefined,
        api_key_header: selectedProviderDetails.supports_custom_auth ? apiKeyHeader.trim() : undefined,
        api_key_prefix: selectedProviderDetails.supports_custom_auth ? apiKeyPrefix : undefined,
      });
      setSettings(response);
      toast({ title: 'Model settings saved', description: `${selectedProviderDetails.display_name} is configured.` });
    } catch (error) {
      const message = formatProviderCredentialMessage(
        selectedProviderDetails.display_name,
        formatErrorMessage(error, 'Karen could not save configuration.'),
      );
      setApiKeyValidationState('invalid');
      setApiKeyValidationMessage(message);
      setIsEditingApiKey(true);
      toast({ title: `Save failed for ${selectedProviderDetails.display_name}`, description: message, variant: 'destructive' });
    } finally { setIsSaving(false); }
  };

  const handleClearApiKey = async () => {
    if (!selectedProviderDetails?.api_key_configured) return;
    setIsClearingKey(true);
    try {
      const response = await apiClient.put<ModelSettingsResponse>('/api/settings/model', {
        provider: selectedProvider,
        model: selectedModel.trim(),
        runtime_source: selectedProviderDetails?.id === 'ollama' ? runtimeSource : undefined,
        clear_api_key: true,
      });
      setSettings(response);
      setApiKey('');
      toast({ title: 'API key removed', description: `${selectedProviderDetails.display_name} credentials cleared.` });
    } catch (error) {
      toast({ title: 'Unable to clear API key', description: formatErrorMessage(error, 'Failed to clear credential.'), variant: 'destructive' });
    } finally { setIsClearingKey(false); }
  };

  const handleCreateCustomProvider = async () => {
    if (!customProviderForm.name.trim() || !customProviderForm.displayName.trim() || !customProviderForm.baseUrl.trim() || !customProviderForm.model.trim()) {
      toast({ title: 'Missing details', description: 'All fields except description are required.', variant: 'destructive' });
      return;
    }
    setIsAddingCustom(true);
    try {
      const response = await apiClient.post<ModelSettingsResponse>('/api/settings/model/providers/custom', {
        name: customProviderForm.name.trim(),
        display_name: customProviderForm.displayName.trim(),
        description: customProviderForm.description.trim() || undefined,
        base_url: customProviderForm.baseUrl.trim(),
        model: customProviderForm.model.trim(),
        api_key_header: customProviderForm.authHeader.trim() || undefined,
        api_key_prefix: customProviderForm.authPrefix,
      });
      setSettings(response);
      setSelectedProvider(response.selected_provider);
      setIsCustomDialogOpen(false);
      setCustomProviderForm({ name: '', displayName: '', description: '', baseUrl: '', model: '', authHeader: 'Authorization', authPrefix: 'Bearer' });
      toast({ title: 'Custom provider added', description: `${customProviderForm.displayName} is now available.` });
    } catch (error) {
      toast({ title: 'Failed to add provider', description: formatErrorMessage(error, 'Could not create provider.'), variant: 'destructive' });
    } finally { setIsAddingCustom(false); }
  };

  if (isLoading) {
    return (
      <Card className="border-none bg-transparent shadow-none">
        <CardContent className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Initializing Model Intelligence...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className={cn("grid gap-8 pb-32", !isMobile && "grid-cols-12")}>
        {/* Main Configuration Card */}
        <div className={cn("space-y-6", !isMobile ? "col-span-12 xl:col-span-8" : "w-full")}>
          <Card className="border-border/40 shadow-sm transition-all hover:shadow-md">
            <CardHeader className="border-b bg-muted/20 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" /> Model Selection
                  </CardTitle>
                  <CardDescription>Select the brain and runtime environment for Karen.</CardDescription>
                </div>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="outline" size="icon" className="rounded-full">
                        <InfoIcon className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      Changing providers affects response latency, creativity, and cost. Cloud models are frontier while Local models ensure privacy.
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-8">
              {/* Provider Selection */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="ai-provider" className="text-sm font-semibold uppercase tracking-wider text-muted-foreground/80">Active Provider</Label>
                  <Dialog open={isCustomDialogOpen} onOpenChange={setIsCustomDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 text-primary hover:text-primary hover:bg-primary/5">
                        <PlusCircle className="mr-2 h-4 w-4" /> Add Custom
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                      <DialogHeader>
                        <DialogTitle>Add Custom AI Provider</DialogTitle>
                        <DialogDescription>Add any OpenAI-compatible endpoint that Karen should communicate with.</DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="c-p-id">Unique ID</Label>
                            <Input id="c-p-id" value={customProviderForm.name} onChange={(e) => setCustomProviderForm({...customProviderForm, name: e.target.value})} placeholder="e.g. together-ai" />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="c-p-display">Display Name</Label>
                            <Input id="c-p-display" value={customProviderForm.displayName} onChange={(e) => setCustomProviderForm({...customProviderForm, displayName: e.target.value})} placeholder="Together AI" />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="c-p-url">Base URL</Label>
                          <Input id="c-p-url" value={customProviderForm.baseUrl} onChange={(e) => setCustomProviderForm({...customProviderForm, baseUrl: e.target.value})} placeholder="https://api.together.xyz/v1" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="c-p-model">Default Model</Label>
                            <Input id="c-p-model" value={customProviderForm.model} onChange={(e) => setCustomProviderForm({...customProviderForm, model: e.target.value})} placeholder="mistralai/Mixtral-8x7B" />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="c-p-header">Auth Header</Label>
                            <Input id="c-p-header" value={customProviderForm.authHeader} onChange={(e) => setCustomProviderForm({...customProviderForm, authHeader: e.target.value})} />
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsCustomDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleCreateCustomProvider} disabled={isAddingCustom}>
                          {isAddingCustom ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />} Create Provider
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
                
                <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                  <SelectTrigger id="ai-provider" className="h-12 border-border/60 bg-muted/10 text-base font-medium transition-all hover:border-primary/40 focus:ring-primary/20">
                    <SelectValue placeholder="Identify your AI runtime..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-[min(80vh,500px)]">
                    <SelectGroup>
                      <SelectLabel className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><ShieldCheck className="h-3 w-3" /> Managed Cloud</SelectLabel>
                      {providerGroups.cloudProviders.map((p) => (
                        <SelectItem key={p.id} value={p.id} className="cursor-pointer py-3 hover:bg-primary/5">
                          <div className="flex items-center gap-3">
                            <span className="font-semibold">{p.display_name}</span>
                            <Badge variant="outline" className="h-5 text-[9px] font-bold uppercase tracking-widest text-primary/70">Frontier</Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectGroup>
                    <SelectSeparator className="my-2" />
                    <SelectGroup>
                      <SelectLabel className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><HardDrive className="h-3 w-3" /> Local Runtimes</SelectLabel>
                      {providerGroups.localProviders.map((p) => (
                        <SelectItem key={p.id} value={p.id} className="cursor-pointer py-3">
                          <div className="flex items-center gap-3">
                            <span className="font-semibold">{p.display_name}</span>
                            <Badge variant="outline" className="h-5 text-[9px] font-bold uppercase tracking-widest text-emerald-600/70">Private</Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectGroup>
                    {providerGroups.customProviders.length > 0 && (
                      <>
                        <SelectSeparator className="my-2" />
                        <SelectGroup>
                          <SelectLabel className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground"><Settings2 className="h-3 w-3" /> Custom Integrations</SelectLabel>
                          {providerGroups.customProviders.map((p) => (
                            <SelectItem key={p.id} value={p.id} className="cursor-pointer py-3">
                              <div className="flex items-center gap-3">
                                <span className="font-semibold">{p.display_name}</span>
                                <Badge variant="outline" className="h-5 text-[9px] font-bold uppercase tracking-widest text-purple-600/70">API</Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>

              <Separator className="bg-border/30" />

              {/* Dynamic Contextual Configuration */}
              {selectedProviderDetails && (
                <div className="animate-in fade-in slide-in-from-top-4 duration-500 space-y-8">
                  <div className="grid gap-8">
                    {/* Endpoint & Discovery Row */}
                      <div className="grid gap-6 md:grid-cols-2">
                        {selectedProviderDetails.id === 'ollama' ? (
                          <div className="space-y-3 md:col-span-2">
                            <Label htmlFor="ollama-runtime-source" className="flex items-center gap-2 font-semibold">
                              <Server className="h-4 w-4 text-primary" /> Ollama Runtime Source
                            </Label>
                            <Select
                              value={runtimeSource}
                              onValueChange={(value: 'host' | 'container') => {
                                setRuntimeSource(value);
                                const nextOption = selectedProviderDetails.runtime_options?.find((option) => option.source === value);
                                if (nextOption) {
                                  const nextBaseUrl = normalizeConfiguredOllamaAddress(nextOption.base_url);
                                  setBaseUrl(nextBaseUrl.replace(/\/api$/, ''));
                                  void loadProviderModels('ollama', nextBaseUrl);
                                }
                              }}
                            >
                              <SelectTrigger id="ollama-runtime-source" className="h-11 bg-muted/20">
                                <SelectValue placeholder="Choose Ollama runtime" />
                              </SelectTrigger>
                              <SelectContent>
                                {(selectedProviderDetails.runtime_options ?? []).map((option) => (
                                  <SelectItem key={option.source} value={option.source}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>

                            <div className="grid gap-3 lg:grid-cols-2">
                              {(selectedProviderDetails.runtime_options ?? []).map((option) => (
                                <div
                                  key={option.source}
                                  className={cn(
                                    "rounded-2xl border p-4 transition-all",
                                    option.source === runtimeSource ? "border-primary/40 bg-primary/5" : "border-border/40 bg-muted/10",
                                  )}
                                >
                                  <div className="flex items-center justify-between gap-3">
                                    <div className="space-y-1">
                                      <p className="text-sm font-semibold">{option.label}</p>
                                      <p className="text-[10px] uppercase tracking-widest text-muted-foreground">{option.status}</p>
                                    </div>
                                    <Badge variant="outline" className={cn("text-[10px] uppercase", option.available ? "text-emerald-600" : "text-amber-600")}>
                                      {option.available ? "Available" : "Setup Required"}
                                    </Badge>
                                  </div>
                                  <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{option.message}</p>
                                  <div className="mt-3 rounded-lg border border-border/40 bg-background/60 px-3 py-2 font-mono text-[11px] text-muted-foreground">
                                    {option.base_url}
                                  </div>
                                  {option.setup_command && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="mt-3 h-8 text-[10px] uppercase tracking-widest"
                                      onClick={async () => {
                                        await navigator.clipboard.writeText(option.setup_command || '');
                                        toast({ title: 'Setup command copied', description: option.setup_command || '' });
                                      }}
                                    >
                                      Copy Setup Command
                                    </Button>
                                  )}
                                </div>
                              ))}
                            </div>

                            <div className="space-y-3">
                              <Label htmlFor="base-url" className="flex items-center gap-2 font-semibold">
                                <Server className="h-4 w-4 text-primary" /> Derived API Endpoint
                              </Label>
                              <Input id="base-url" value={baseUrl} readOnly className="h-11 bg-muted/20 font-mono" />
                            </div>
                          </div>
                        ) : selectedProviderDetails.supports_base_url_override && (
                          <div className="space-y-3">
                            <Label htmlFor="base-url" className="flex items-center gap-2 font-semibold">
                              <Server className="h-4 w-4 text-primary" /> API Endpoint
                            </Label>
                            <Input id="base-url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder={selectedProviderDetails.default_base_url || "https://..."} className="h-11 bg-muted/20" />
                          </div>
                        )}
                        
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="model-picker" className="font-semibold">Model Identification</Label>
                            {selectedProviderDetails.supports_model_discovery && (
                              <Button variant="outline" size="sm" onClick={() => loadProviderModels(selectedProvider, baseUrl)} disabled={isLoadingModels} className="h-7 px-2 text-[10px] uppercase font-bold tracking-widest">
                                {isLoadingModels ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <RefreshCw className="mr-1 h-3 w-3" />} Discovery
                              </Button>
                            )}
                          </div>
                          {availableModels.length > 0 ? (
                            <Select value={selectedModel} onValueChange={setSelectedModel}>
                              <SelectTrigger id="model-picker" className="h-11 bg-muted/20">
                                <SelectValue placeholder="Discovering models..." />
                              </SelectTrigger>
                              <SelectContent>
                                {availableModels.map(m => <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          ) : (
                            <Input id="model-picker" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} placeholder="Type model id (e.g. gpt-4o)" className="h-11 bg-muted/20 font-mono" />
                          )}
                        </div>
                      </div>

                      {/* API Key Section */}
                      {selectedProviderDetails.requires_api_key && (
                        <div className="rounded-2xl border border-border/50 bg-muted/5 p-6 space-y-4">
                          <div className="flex items-center justify-between gap-4">
                            <div className="space-y-1">
                              <Label htmlFor="api-key" className="flex items-center gap-2 font-semibold">
                                <KeyRound className="h-4 w-4 text-primary" /> Credentials
                              </Label>
                              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Encrypted Backend Storage</p>
                            </div>
                            {selectedProviderDetails.api_key_configured && (
                              <Button variant="outline" size="sm" onClick={handleClearApiKey} disabled={isClearingKey} className="h-7 text-[10px] font-bold border-destructive/40 bg-destructive/5 text-destructive hover:bg-destructive/10">
                                Clear Secret
                              </Button>
                            )}
                          </div>
                          
                          <div className="relative">
                            <Input
                              id="api-key"
                              type="password"
                              value={isEditingApiKey ? apiKey : (apiKey || selectedProviderDetails.api_key_masked || '')}
                              onFocus={() => setIsEditingApiKey(true)}
                              onChange={(e) => setApiKey(e.target.value)}
                              placeholder={`Enter ${selectedProviderDetails.display_name} API Secret...`}
                              className="h-12 border-border/60 bg-background/50 pr-10 font-mono text-sm leading-relaxed tracking-widest transition-all focus:border-primary/40 focus:ring-primary/10"
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                              {apiKeyValidationState === 'validating' && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                              {apiKeyValidationState === 'valid' && <CheckCircle2 className="h-4 w-4 text-emerald-500 shadow-sm" />}
                              {apiKeyValidationState === 'invalid' && <XCircle className="h-4 w-4 text-destructive" />}
                            </div>
                          </div>
                          
                          {apiKeyValidationMessage && (
                            <div className={cn("flex items-center gap-2 text-xs font-medium px-2 py-1.5 rounded-lg border", 
                              apiKeyValidationState === 'valid' ? "bg-emerald-50/10 border-emerald-500/20 text-emerald-600" : "bg-destructive/5 border-destructive/20 text-destructive")}>
                              <Info className="h-3 w-3 shrink-0" /> {apiKeyValidationMessage}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                  <div className="flex justify-end pt-4">
                    <Button onClick={handleSave} disabled={isSaving} className="h-11 w-full sm:w-auto px-8 font-bold shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] active:scale-95">
                      {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-5 w-5" />}
                      Finalize Intelligence Settings
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Context Card */}
        {!isMobile && selectedProviderDetails && (
          <div className="xl:col-span-4 space-y-6 animate-in fade-in slide-in-from-right-8 duration-700">
            <Card className="border-border/40 shadow-sm sticky top-6">
              <CardHeader className="bg-muted/10">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <ShieldCheck className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-bold uppercase tracking-widest">{selectedProviderDetails.display_name}</CardTitle>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">Active Node Status</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-6">
                <div className="space-y-4">
                  <div className="rounded-xl border border-border/60 bg-muted/5 px-4 py-3">
                    <p className="text-xs leading-relaxed text-muted-foreground/90 font-medium italic">&quot;{selectedProviderDetails.description}&quot;</p>
                  </div>
                  
                  <div className="grid gap-2">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-muted-foreground">Type</span>
                      <span className="uppercase tracking-widest text-primary/80">{selectedProviderDetails.provider_type}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-muted-foreground">Auth</span>
                      <span className={cn("uppercase tracking-widest", selectedProviderDetails.requires_api_key ? "text-amber-600" : "text-emerald-600")}>
                        {selectedProviderDetails.requires_api_key ? "Restricted" : "Open"}
                      </span>
                    </div>
                    {selectedProviderDetails.selected_model && (
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-muted-foreground">Active Model</span>
                        <span className="max-w-[120px] truncate font-mono text-primary/70">{selectedProviderDetails.selected_model}</span>
                      </div>
                    )}
                    {selectedProviderDetails.id === 'ollama' && selectedRuntimeOption && (
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-muted-foreground">Runtime Source</span>
                        <span className="uppercase tracking-widest text-primary/80">{selectedRuntimeOption.label}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/80">Capabilities</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedProviderDetails.supports_model_discovery && <Badge variant="outline" className="h-6 text-[9px] font-bold bg-primary/5 uppercase">Discovery</Badge>}
                    {selectedProviderDetails.supports_model_pull && <Badge variant="outline" className="h-6 text-[9px] font-bold bg-emerald-50/10 uppercase">Local Pull</Badge>}
                    {selectedProviderDetails.supports_manual_model_entry && <Badge variant="outline" className="h-6 text-[9px] font-bold bg-blue-50/10 uppercase">Manual Node</Badge>}
                  </div>
                </div>

                {selectedProviderDetails.docs_url && (
                  <Button variant="secondary" className="w-full text-xs font-bold gap-2" asChild>
                    <a href={selectedProviderDetails.docs_url} target="_blank" rel="noreferrer">
                      Integration Protocol <ExternalLink className="h-3 w-3" />
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>

            <Alert className="bg-primary/5 border-primary/20">
              <InfoIcon className="h-4 w-4 !text-primary" />
              <AlertDescription className="text-[10px] font-semibold leading-relaxed text-primary/80">
                Karen intelligently routes prompts based on your selection. Cloud providers offer greater reasoning capabilities, while Local ensures 100% data sovereignity.
              </AlertDescription>
            </Alert>
          </div>
        )}
      </div>
    </div>
  );
}
