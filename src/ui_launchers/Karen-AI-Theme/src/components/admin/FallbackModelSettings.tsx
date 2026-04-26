"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Bot, Cpu, RefreshCw, Save, Loader2, AlertTriangle, CheckCircle2, Globe, Clock } from "lucide-react";
import { getRuntimeDisplayName, isLocalRuntimeProvider } from "@/lib/chat-response";
import { normalizeModelSettingsResponse, type RuntimeSettingsResponse } from "@/lib/model-runtime-inventory";

type ModelSettingsResponse = RuntimeSettingsResponse;

export default function FallbackModelSettings() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [runtimeSource, setRuntimeSource] = useState<"host" | "container">("host");
  const [baseUrl, setBaseUrl] = useState("");
  const [timeoutSeconds, setTimeoutSeconds] = useState("45");
  const [autoDownload, setAutoDownload] = useState(false);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<ModelSettingsResponse>("/api/settings/model");
      const normalized = normalizeModelSettingsResponse(response);
      setSettings(response);
      setSelectedProvider(normalized.selected_provider || normalized.providers[0]?.id || "");
      setSelectedModel(normalized.selected_model || "");
      const provider = normalized.providers.find(p => p.id === normalized.selected_provider);
      if (isLocalRuntimeProvider(provider?.id)) {
        setRuntimeSource(provider.runtime_source === "container" ? "container" : "host");
      }
      setBaseUrl((provider?.base_url || provider?.default_base_url || "").replace(/\/api$/, ""));
    } catch {
      toast({
        title: "Failed to load model settings",
        description: "Could not reach the backend. Check that the API is running.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const normalizedSettings = settings ? normalizeModelSettingsResponse(settings) : null;
  const groupedProviders = useMemo(() => {
    if (!normalizedSettings) {
      return null;
    }
    return {
      builtInProviders: normalizedSettings.builtInProviders,
      localProviders: normalizedSettings.localProviders,
      thirdPartyProviders: normalizedSettings.thirdPartyProviders,
      customProviders: normalizedSettings.customProviders,
      systemFallbackProvider: normalizedSettings.systemFallbackProvider,
    };
  }, [normalizedSettings]);
  const currentProvider = normalizedSettings?.providers.find(p => p.id === selectedProvider);
  const availableModels = currentProvider?.models ?? [];
  const selectedRuntimeOption = isLocalRuntimeProvider(currentProvider?.id)
    ? currentProvider.runtime_options?.find((option) => option.source === runtimeSource)
    : null;

  useEffect(() => {
    if (!isLocalRuntimeProvider(currentProvider?.id)) return;
    const option = currentProvider.runtime_options?.find((item) => item.source === runtimeSource);
    if (option) {
      setBaseUrl((option.base_url || "").replace(/\/api$/, ""));
    }
  }, [currentProvider, runtimeSource]);

  const handleSave = async () => {
    if (!selectedProvider || !selectedModel) return;
    setIsSaving(true);
    try {
      const response = await apiClient.put<ModelSettingsResponse>("/api/settings/model", {
        provider: selectedProvider,
        model: selectedModel,
        base_url: baseUrl || undefined,
        runtime_source: isLocalRuntimeProvider(currentProvider?.id) ? runtimeSource : undefined,
      });
      const normalized = normalizeModelSettingsResponse(response);
      setSettings(response);
      setSelectedProvider(normalized.selected_provider);
      setSelectedModel(normalized.selected_model);
      toast({
        title: "Model settings saved",
        description: `Active model set to ${normalized.selected_model} via ${normalized.selected_provider}.`,
      });
    } catch {
      toast({
        title: "Save failed",
        description: "Could not update model settings.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Active Model */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            Active Model Configuration
          </CardTitle>
          <CardDescription>
            The currently active provider and model used for all AI responses.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">Runtime</Label>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-sm px-3 py-1">
                  {getRuntimeDisplayName(settings?.selected_provider || "", settings?.selected_provider || "Not set")}
                </Badge>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">Model</Label>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-sm px-3 py-1 font-mono">
                  {settings?.selected_model || "Not set"}
                </Badge>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">Available Runtimes</Label>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-sm px-3 py-1">
                  {normalizedSettings?.providers.length || 0} configured
                </Badge>
              </div>
            </div>
            {isLocalRuntimeProvider(currentProvider?.id) && selectedRuntimeOption && (
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground uppercase tracking-wider">Runtime Source</Label>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-sm px-3 py-1">
                    {selectedRuntimeOption.label}
                  </Badge>
                </div>
              </div>
            )}
            {groupedProviders?.systemFallbackProvider && (
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground uppercase tracking-wider">Automatic Fallback</Label>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-sm px-3 py-1">
                    {groupedProviders.systemFallbackProvider.runtime_display_name}
                  </Badge>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Edit Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bot className="h-5 w-5 text-primary" />
            Change Default Model
          </CardTitle>
          <CardDescription>
            Select the primary and fallback AI provider and model. Changes take effect immediately.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="admin-provider" className="flex items-center gap-1.5">
                <Bot className="h-3.5 w-3.5" /> Runtime
              </Label>
              <Select value={selectedProvider} onValueChange={(value) => {
                setSelectedProvider(value);
                const provider = normalizedSettings?.providers.find(p => p.id === value);
                if (isLocalRuntimeProvider(provider?.id)) {
                  setRuntimeSource(provider.runtime_source === "container" ? "container" : "host");
                }
                setSelectedModel(provider?.models[0]?.id || "");
                setBaseUrl((provider?.base_url || provider?.default_base_url || "").replace(/\/api$/, ""));
              }}>
                <SelectTrigger id="admin-provider">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {groupedProviders?.builtInProviders.length ? (
                    <SelectGroup>
                      <SelectLabel>Built-in Runtime</SelectLabel>
                      {groupedProviders.builtInProviders.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          {getRuntimeDisplayName(provider.id, provider.display_name)}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : null}
                  {groupedProviders?.localProviders.length ? (
                    <SelectGroup>
                      <SelectLabel>Local Providers</SelectLabel>
                      {groupedProviders.localProviders.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          {getRuntimeDisplayName(provider.id, provider.display_name)}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : null}
                  {groupedProviders?.thirdPartyProviders.length ? (
                    <SelectGroup>
                      <SelectLabel>Third-Party Providers</SelectLabel>
                      {groupedProviders.thirdPartyProviders.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          {getRuntimeDisplayName(provider.id, provider.display_name)}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : null}
                  {groupedProviders?.customProviders.length ? (
                    <SelectGroup>
                      <SelectLabel>Custom Integrations</SelectLabel>
                      {groupedProviders.customProviders.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          {getRuntimeDisplayName(provider.id, provider.display_name)}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : null}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-model" className="flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5" /> Model
              </Label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger id="admin-model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {isLocalRuntimeProvider(currentProvider?.id) && (
            <div className="space-y-3">
              <Label className="flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5" /> Runtime Source
              </Label>
              <Select value={runtimeSource} onValueChange={(value: "host" | "container") => setRuntimeSource(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select runtime source" />
                </SelectTrigger>
                <SelectContent>
                  {(currentProvider.runtime_options ?? []).map((option) => (
                    <SelectItem key={option.source} value={option.source}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedRuntimeOption && (
                <div className="rounded-xl border border-border/50 bg-muted/20 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold">{selectedRuntimeOption.label}</span>
                    <Badge variant={selectedRuntimeOption.available ? "secondary" : "outline"}>
                      {selectedRuntimeOption.available ? "Available" : "Setup Required"}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{selectedRuntimeOption.message}</p>
                  {selectedRuntimeOption.setup_command && (
                    <code className="block text-[10px] text-muted-foreground font-mono">{selectedRuntimeOption.setup_command}</code>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="admin-base-url" className="flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5" /> Base URL (optional)
            </Label>
            <Input
              id="admin-base-url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://host.docker.internal:11434"
              className="font-mono text-sm"
              readOnly={isLocalRuntimeProvider(currentProvider?.id)}
            />
            <p className="text-xs text-muted-foreground">
              {isLocalRuntimeProvider(currentProvider?.id)
                ? "For local runtimes, the runtime source determines the API endpoint."
                : "Override the provider&apos;s default API endpoint."}
            </p>
          </div>

          <Separator />

          {/* Timeout & Auto-Download */}
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="admin-timeout" className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" /> Response Timeout (seconds)
              </Label>
              <Input
                id="admin-timeout"
                type="number"
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(e.target.value)}
                min={5}
                max={300}
                className="max-w-[120px]"
              />
              <p className="text-xs text-muted-foreground">Max time before fallback kicks in (env: COPILOT_ASSIST_TIMEOUT_SECONDS).</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="admin-auto-download" className="flex items-center gap-1.5">
                  Auto-download models
                </Label>
                <Switch id="admin-auto-download" checked={autoDownload} onCheckedChange={setAutoDownload} />
              </div>
              <p className="text-xs text-muted-foreground">Automatically download missing models on demand (env: KARI_AUTO_DOWNLOAD_LLM).</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={isSaving || !selectedProvider || !selectedModel}>
              {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              Save Configuration
            </Button>
            <Button variant="outline" onClick={loadSettings} disabled={isLoading}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Reload
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Provider List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registered Providers</CardTitle>
          <CardDescription>All providers detected by the backend and their available models.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
          {groupedProviders?.builtInProviders.length ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Built-in Runtime</h4>
              {groupedProviders.builtInProviders.map((provider) => (
                <div key={provider.id} className="p-4 rounded-xl border border-border/50 bg-muted/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">{getRuntimeDisplayName(provider.id, provider.display_name)}</h4>
                      {provider.id === normalizedSettings?.selected_provider && (
                        <Badge className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                      )}
                    </div>
                    <code className="text-[10px] text-muted-foreground font-mono">{provider.id}</code>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {provider.models.map((model) => (
                      <Badge
                        key={model.id}
                        variant={model.id === normalizedSettings?.selected_model && provider.id === normalizedSettings?.selected_provider ? "default" : "outline"}
                        className="text-[10px] cursor-default"
                      >
                        {model.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {groupedProviders?.localProviders.length ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Local Providers</h4>
              {groupedProviders.localProviders.map((provider) => (
                <div key={provider.id} className="p-4 rounded-xl border border-border/50 bg-muted/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">{getRuntimeDisplayName(provider.id, provider.display_name)}</h4>
                      {provider.id === normalizedSettings?.selected_provider && (
                        <Badge className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                      )}
                    </div>
                    <code className="text-[10px] text-muted-foreground font-mono">{provider.id}</code>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {provider.models.map((model) => (
                      <Badge
                        key={model.id}
                        variant={model.id === normalizedSettings?.selected_model && provider.id === normalizedSettings?.selected_provider ? "default" : "outline"}
                        className="text-[10px] cursor-default"
                      >
                        {model.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {groupedProviders?.thirdPartyProviders.length ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Third-Party Providers</h4>
              {groupedProviders.thirdPartyProviders.map((provider) => (
                <div key={provider.id} className="p-4 rounded-xl border border-border/50 bg-muted/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">{getRuntimeDisplayName(provider.id, provider.display_name)}</h4>
                      {provider.id === normalizedSettings?.selected_provider && (
                        <Badge className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                      )}
                    </div>
                    <code className="text-[10px] text-muted-foreground font-mono">{provider.id}</code>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {provider.models.map((model) => (
                      <Badge
                        key={model.id}
                        variant={model.id === normalizedSettings?.selected_model && provider.id === normalizedSettings?.selected_provider ? "default" : "outline"}
                        className="text-[10px] cursor-default"
                      >
                        {model.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {groupedProviders?.customProviders.length ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Custom Integrations</h4>
              {groupedProviders.customProviders.map((provider) => (
                <div key={provider.id} className="p-4 rounded-xl border border-border/50 bg-muted/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">{getRuntimeDisplayName(provider.id, provider.display_name)}</h4>
                    {provider.id === normalizedSettings?.selected_provider && (
                      <Badge className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                    )}
                  </div>
                  <code className="text-[10px] text-muted-foreground font-mono">{provider.id}</code>
                </div>
                {(provider.base_url || provider.default_base_url) && (
                  <p className="text-xs text-muted-foreground font-mono">
                    {provider.base_url || provider.default_base_url}
                  </p>
                )}
                {isLocalRuntimeProvider(provider.id) && provider.runtime_options?.length ? (
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {provider.runtime_options.map((option) => (
                      <Badge key={option.source} variant="outline" className="text-[10px]">
                        {option.label}: {option.available ? "available" : "setup required"}
                      </Badge>
                    ))}
                  </div>
                ) : null}
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {provider.models.map((model) => (
                    <Badge
                      key={model.id}
                      variant={model.id === normalizedSettings?.selected_model && provider.id === normalizedSettings?.selected_provider ? "default" : "outline"}
                      className="text-[10px] cursor-default"
                    >
                      {model.name}
                    </Badge>
                  ))}
                  {provider.models.length === 0 && (
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3 text-amber-500" /> No models available
                    </span>
                  )}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
