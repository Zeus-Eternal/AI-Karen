"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Bot, Cpu, RefreshCw, Save, Loader2, AlertTriangle, CheckCircle2, Globe, Clock } from "lucide-react";

type ProviderInfo = {
  id: string;
  display_name: string;
  base_url?: string | null;
  default_base_url?: string | null;
  models: Array<{
    id: string;
    name: string;
  }>;
};

type ModelSettingsResponse = {
  selected_provider: string;
  selected_model: string;
  providers: ProviderInfo[];
};

export default function FallbackModelSettings() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [timeoutSeconds, setTimeoutSeconds] = useState("45");
  const [autoDownload, setAutoDownload] = useState(false);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<ModelSettingsResponse>("/api/settings/model");
      setSettings(response);
      setSelectedProvider(response.selected_provider || response.providers[0]?.id || "");
      setSelectedModel(response.selected_model || "");
      const provider = response.providers.find(p => p.id === response.selected_provider);
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

  const currentProvider = settings?.providers.find(p => p.id === selectedProvider);
  const availableModels = currentProvider?.models ?? [];

  const handleSave = async () => {
    if (!selectedProvider || !selectedModel) return;
    setIsSaving(true);
    try {
      const response = await apiClient.put<ModelSettingsResponse>("/api/settings/model", {
        provider: selectedProvider,
        model: selectedModel,
        base_url: baseUrl || undefined,
      });
      setSettings(response);
      setSelectedProvider(response.selected_provider);
      setSelectedModel(response.selected_model);
      toast({
        title: "Model settings saved",
        description: `Active model set to ${response.selected_model} via ${response.selected_provider}.`,
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
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">Provider</Label>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-sm px-3 py-1">
                  {settings?.selected_provider || "Not set"}
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
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">Available Providers</Label>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-sm px-3 py-1">
                  {settings?.providers.length || 0} configured
                </Badge>
              </div>
            </div>
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
                <Bot className="h-3.5 w-3.5" /> Provider
              </Label>
              <Select value={selectedProvider} onValueChange={(value) => {
                setSelectedProvider(value);
                const provider = settings?.providers.find(p => p.id === value);
                setSelectedModel(provider?.models[0]?.id || "");
                setBaseUrl((provider?.base_url || provider?.default_base_url || "").replace(/\/api$/, ""));
              }}>
                <SelectTrigger id="admin-provider">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {settings?.providers.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      {provider.display_name}
                    </SelectItem>
                  ))}
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

          <div className="space-y-2">
            <Label htmlFor="admin-base-url" className="flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5" /> Base URL (optional)
            </Label>
            <Input
              id="admin-base-url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8080"
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">Override the provider's default API endpoint.</p>
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
            {settings?.providers.map((provider) => (
              <div key={provider.id} className="p-4 rounded-xl border border-border/50 bg-muted/20 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm">{provider.display_name}</h4>
                    {provider.id === settings.selected_provider && (
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
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {provider.models.map((model) => (
                    <Badge
                      key={model.id}
                      variant={model.id === settings.selected_model && provider.id === settings.selected_provider ? "default" : "outline"}
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
        </CardContent>
      </Card>
    </div>
  );
}
