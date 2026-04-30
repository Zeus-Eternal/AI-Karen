"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock,
  Cpu,
  Globe,
  Loader2,
  RefreshCw,
  Save,
  ShieldAlert,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { getRuntimeDisplayName } from "@/lib/chat-response";
import {
  normalizeModelSettingsResponse,
  type RuntimeSettingsResponse,
} from "@/lib/model-runtime-inventory";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

type ModelSettingsResponse = RuntimeSettingsResponse;

type RuntimeSource = "host" | "container";

type NormalizedSettings = ReturnType<typeof normalizeModelSettingsResponse>;
type NormalizedProvider = NormalizedSettings["providers"][number];
type NormalizedModel = NormalizedProvider["models"][number];

type ProviderGroupDefinition = {
  label: string;
  providers: NormalizedProvider[];
};

type EditableModelForm = {
  provider: string;
  model: string;
  runtimeSource: RuntimeSource;
  baseUrl: string;
  timeoutSeconds: string;
  autoDownload: boolean;
};

const DEFAULT_FORM: EditableModelForm = {
  provider: "",
  model: "",
  runtimeSource: "host",
  baseUrl: "",
  timeoutSeconds: "45",
  autoDownload: false,
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in before changing model settings.";
    }

    if (error.status === 403) {
      return "This session is not authorized to change model settings.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

const stripTrailingApi = (value: string | null | undefined) => {
  return (value || "").trim().replace(/\/api\/?$/, "");
};

const isValidHttpUrl = (value: string) => {
  const trimmed = value.trim();

  if (!trimmed) {
    return true;
  }

  try {
    const parsed = new URL(trimmed);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
};

const getProviderBaseUrl = (provider: NormalizedProvider | undefined | null) => {
  return stripTrailingApi(provider?.base_url || provider?.default_base_url || "");
};

const getInitialRuntimeSource = (
  provider: NormalizedProvider | undefined,
  fallback: RuntimeSource = "host",
): RuntimeSource => {
  if (!provider?.runtime_options?.length) {
    return fallback;
  }

  if (provider.runtime_source === "container") {
    return "container";
  }

  if (provider.runtime_source === "host") {
    return "host";
  }

  const firstSource = provider.runtime_options[0]?.source;
  return firstSource === "container" ? "container" : "host";
};

const providerHasRuntimeSource = (provider: NormalizedProvider | undefined, source: RuntimeSource) => {
  if (!provider?.runtime_options?.length) {
    return false;
  }

  return provider.runtime_options.some((option) => option.source === source);
};

const getFormValidationError = ({
  form,
  provider,
  models,
  usesRuntimeOptions,
}: {
  form: EditableModelForm;
  provider: NormalizedProvider | undefined;
  models: NormalizedModel[];
  usesRuntimeOptions: boolean;
}) => {
  if (!form.provider) {
    return "Select a runtime provider.";
  }

  if (!provider) {
    return "Selected provider is not present in the backend registry.";
  }

  if (models.length === 0) {
    return "Selected provider has no backend-reported models.";
  }

  if (!form.model) {
    return "Select a model.";
  }

  if (!models.some((model) => model.id === form.model)) {
    return "Selected model is not available for the selected provider.";
  }

  if (usesRuntimeOptions && !providerHasRuntimeSource(provider, form.runtimeSource)) {
    return "Selected runtime source is not available for this provider.";
  }

  if (!isValidHttpUrl(form.baseUrl)) {
    return "Base URL must be empty or a valid http/https URL.";
  }

  const timeout = Number.parseInt(form.timeoutSeconds, 10);

  if (!Number.isInteger(timeout) || timeout < 5 || timeout > 300) {
    return "Response timeout must be an integer between 5 and 300 seconds.";
  }

  return null;
};

const buildFormFromSettings = (normalized: NormalizedSettings): EditableModelForm => {
  const selectedProviderId = normalized.selected_provider || normalized.providers[0]?.id || "";
  const selectedProvider = normalized.providers.find(
    (provider) => provider.id === selectedProviderId,
  );

  const selectedModelId =
    normalized.selected_model ||
    selectedProvider?.models[0]?.id ||
    "";

  const runtimeSource = getInitialRuntimeSource(selectedProvider);

  const runtimeOption = selectedProvider?.runtime_options?.find(
    (option) => option.source === runtimeSource,
  );

  return {
    provider: selectedProviderId,
    model: selectedModelId,
    runtimeSource,
    baseUrl: stripTrailingApi(runtimeOption?.base_url || getProviderBaseUrl(selectedProvider)),
    timeoutSeconds:
      typeof normalized.timeout_seconds === "number"
        ? String(normalized.timeout_seconds)
        : "45",
    autoDownload: Boolean(normalized.auto_download),
  };
};

const ProviderModelBadges = ({
  provider,
  activeProvider,
  activeModel,
}: {
  provider: NormalizedProvider;
  activeProvider: string | undefined;
  activeModel: string | undefined;
}) => {
  if (provider.models.length === 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <AlertTriangle className="h-3 w-3 text-amber-500" />
        No models available
      </span>
    );
  }

  return (
    <div className="mt-1 flex flex-wrap gap-1.5">
      {provider.models.map((model) => (
        <Badge
          key={model.id}
          variant={
            model.id === activeModel && provider.id === activeProvider
              ? "default"
              : "outline"
          }
          className="cursor-default text-[10px]"
        >
          {model.name}
        </Badge>
      ))}
    </div>
  );
};

const ProviderGroup = ({
  label,
  providers,
  selectedProvider,
  selectedModel,
}: {
  label: string;
  providers: NormalizedProvider[];
  selectedProvider: string | undefined;
  selectedModel: string | undefined;
}) => {
  if (providers.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </h4>

      {providers.map((provider) => (
        <div
          key={provider.id}
          className="space-y-2 rounded-xl border border-border/50 bg-muted/20 p-4"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <h4 className="truncate text-sm font-semibold">
                {getRuntimeDisplayName(provider.id, provider.display_name)}
              </h4>

              {provider.id === selectedProvider && (
                <Badge className="border-emerald-500/20 bg-emerald-500/10 text-[10px] text-emerald-500">
                  Active
                </Badge>
              )}
            </div>

            <code className="shrink-0 font-mono text-[10px] text-muted-foreground">
              {provider.id}
            </code>
          </div>

          {(provider.base_url || provider.default_base_url) && (
            <p className="break-all font-mono text-xs text-muted-foreground">
              {provider.base_url || provider.default_base_url}
            </p>
          )}

          {provider.runtime_options?.length ? (
            <div className="mt-1 flex flex-wrap gap-1.5">
              {provider.runtime_options.map((option) => (
                <Badge key={option.source} variant="outline" className="text-[10px]">
                  {option.label}: {option.available ? "available" : "setup required"}
                </Badge>
              ))}
            </div>
          ) : null}

          <ProviderModelBadges
            provider={provider}
            activeProvider={selectedProvider}
            activeModel={selectedModel}
          />
        </div>
      ))}
    </div>
  );
};

export default function FallbackModelSettings() {
  const { toast } = useToast();

  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [form, setForm] = useState<EditableModelForm>(DEFAULT_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const normalizedSettings = useMemo(() => {
    return settings ? normalizeModelSettingsResponse(settings) : null;
  }, [settings]);

  const providerGroups: ProviderGroupDefinition[] = useMemo(() => {
    if (!normalizedSettings) {
      return [];
    }

    return [
      {
        label: "Built-in Runtime",
        providers: normalizedSettings.builtInProviders,
      },
      {
        label: "Local Providers",
        providers: normalizedSettings.localProviders,
      },
      {
        label: "Cloud Providers",
        providers: normalizedSettings.thirdPartyProviders,
      },
      {
        label: "Custom Integrations",
        providers: normalizedSettings.customProviders,
      },
    ];
  }, [normalizedSettings]);

  const currentProvider = useMemo(() => {
    return normalizedSettings?.providers.find((provider) => provider.id === form.provider);
  }, [form.provider, normalizedSettings?.providers]);

  const availableModels = currentProvider?.models ?? [];
  const usesRuntimeOptions = Boolean(currentProvider?.runtime_options?.length);

  const selectedRuntimeOption = useMemo(() => {
    if (!usesRuntimeOptions) {
      return null;
    }

    return (
      currentProvider?.runtime_options?.find(
        (option) => option.source === form.runtimeSource,
      ) || null
    );
  }, [currentProvider?.runtime_options, form.runtimeSource, usesRuntimeOptions]);

  const formValidationError = useMemo(() => {
    return getFormValidationError({
      form,
      provider: currentProvider,
      models: availableModels,
      usesRuntimeOptions,
    });
  }, [availableModels, currentProvider, form, usesRuntimeOptions]);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    setSaveError(null);

    try {
      const response = await apiClient.get<ModelSettingsResponse>("/api/settings/model");
      const normalized = normalizeModelSettingsResponse(response);

      setSettings(response);
      setForm(buildFormFromSettings(normalized));
    } catch (error) {
      const message = getErrorMessage(
        error,
        "Could not reach the backend model settings service.",
      );

      setSettings(null);
      setForm(DEFAULT_FORM);
      setLoadError(message);

      toast({
        title: "Failed to load model settings",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const updateForm = useCallback((patch: Partial<EditableModelForm>) => {
    setForm((current) => ({
      ...current,
      ...patch,
    }));
  }, []);

  const handleProviderChange = useCallback(
    (providerId: string) => {
      const provider = normalizedSettings?.providers.find((item) => item.id === providerId);
      const runtimeSource = getInitialRuntimeSource(provider, form.runtimeSource);
      const runtimeOption = provider?.runtime_options?.find(
        (option) => option.source === runtimeSource,
      );

      updateForm({
        provider: providerId,
        model: provider?.models[0]?.id || "",
        runtimeSource,
        baseUrl: stripTrailingApi(runtimeOption?.base_url || getProviderBaseUrl(provider)),
      });
    },
    [form.runtimeSource, normalizedSettings?.providers, updateForm],
  );

  const handleRuntimeSourceChange = useCallback(
    (value: string) => {
      const runtimeSource: RuntimeSource = value === "container" ? "container" : "host";
      const runtimeOption = currentProvider?.runtime_options?.find(
        (option) => option.source === runtimeSource,
      );

      updateForm({
        runtimeSource,
        baseUrl: stripTrailingApi(runtimeOption?.base_url || getProviderBaseUrl(currentProvider)),
      });
    },
    [currentProvider, updateForm],
  );

  const handleSave = useCallback(async () => {
    if (formValidationError) {
      toast({
        title: "Model settings need attention",
        description: formValidationError,
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const response = await apiClient.put<ModelSettingsResponse>("/api/settings/model", {
        provider: form.provider,
        model: form.model,
        base_url: form.baseUrl.trim() || undefined,
        runtime_source: usesRuntimeOptions ? form.runtimeSource : undefined,
        timeout_seconds: Number.parseInt(form.timeoutSeconds, 10),
        auto_download: form.autoDownload,
      });

      const normalized = normalizeModelSettingsResponse(response);

      setSettings(response);
      setForm(buildFormFromSettings(normalized));

      toast({
        title: "Model settings saved",
        description: `Active model set to ${normalized.selected_model} via ${normalized.selected_provider}.`,
      });
    } catch (error) {
      const message = getErrorMessage(error, "Could not update model settings.");
      setSaveError(message);

      toast({
        title: "Save failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  }, [form, formValidationError, toast, usesRuntimeOptions]);

  if (isLoading && !settings) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {loadError && (
        <Alert className="border-yellow-500/30 bg-yellow-500/5">
          <AlertCircle className="h-4 w-4 !text-yellow-600" />
          <AlertTitle>Model Settings Unavailable</AlertTitle>
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}

      {saveError && (
        <Alert className="border-yellow-500/30 bg-yellow-500/5">
          <AlertCircle className="h-4 w-4 !text-yellow-600" />
          <AlertTitle>Model Settings Save Failed</AlertTitle>
          <AlertDescription>{saveError}</AlertDescription>
        </Alert>
      )}

      {formValidationError && (
        <Alert className="border-yellow-500/30 bg-yellow-500/5">
          <ShieldAlert className="h-4 w-4 !text-yellow-600" />
          <AlertTitle>Configuration Needs Attention</AlertTitle>
          <AlertDescription>{formValidationError}</AlertDescription>
        </Alert>
      )}

      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            Active Model Configuration
          </CardTitle>
          <CardDescription>
            Backend-reported active provider, model, runtime source, and fallback metadata.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Runtime
              </Label>
              <Badge variant="secondary" className="px-3 py-1 text-sm">
                {getRuntimeDisplayName(
                  normalizedSettings?.selected_provider || "",
                  normalizedSettings?.selected_provider || "Not set",
                )}
              </Badge>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Model
              </Label>
              <Badge variant="outline" className="px-3 py-1 font-mono text-sm">
                {normalizedSettings?.selected_model || "Not set"}
              </Badge>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Available Runtimes
              </Label>
              <Badge variant="outline" className="px-3 py-1 text-sm">
                {normalizedSettings?.providers.length || 0} configured
              </Badge>
            </div>

            {usesRuntimeOptions && selectedRuntimeOption && (
              <div className="space-y-1.5">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                  Runtime Source
                </Label>
                <Badge variant="secondary" className="px-3 py-1 text-sm">
                  {selectedRuntimeOption.label}
                </Badge>
              </div>
            )}

            {normalizedSettings?.systemFallbackProvider && (
              <div className="space-y-1.5">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                  Automatic Fallback
                </Label>
                <Badge variant="outline" className="px-3 py-1 text-sm">
                  {normalizedSettings.systemFallbackProvider.runtime_display_name}
                </Badge>
              </div>
            )}

            {typeof normalizedSettings?.timeout_seconds === "number" && (
              <div className="space-y-1.5">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                  Timeout
                </Label>
                <Badge variant="outline" className="px-3 py-1 text-sm">
                  {normalizedSettings.timeout_seconds}s
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bot className="h-5 w-5 text-primary" />
            Change Default Model
          </CardTitle>
          <CardDescription>
            Select the default AI provider and model. The backend runtime remains the source of
            truth for routing and fallback order.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {!normalizedSettings || normalizedSettings.providers.length === 0 ? (
            <Alert className="border-yellow-500/30 bg-yellow-500/5">
              <AlertTriangle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>No Providers Registered</AlertTitle>
              <AlertDescription>
                The backend did not return any model providers. Check provider registry,
                runtime configuration, and model inventory services.
              </AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="admin-provider" className="flex items-center gap-1.5">
                <Bot className="h-3.5 w-3.5" />
                Runtime
              </Label>

              <Select value={form.provider} onValueChange={handleProviderChange}>
                <SelectTrigger id="admin-provider">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>

                <SelectContent>
                  {providerGroups.map((group) =>
                    group.providers.length ? (
                      <SelectGroup key={group.label}>
                        <SelectLabel>{group.label}</SelectLabel>
                        {group.providers.map((provider) => (
                          <SelectItem key={provider.id} value={provider.id}>
                            {getRuntimeDisplayName(provider.id, provider.display_name)}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ) : null,
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-model" className="flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5" />
                Model
              </Label>

              <Select
                value={form.model}
                onValueChange={(value) => updateForm({ model: value })}
                disabled={!currentProvider || availableModels.length === 0}
              >
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

          {usesRuntimeOptions && (
            <div className="space-y-3">
              <Label className="flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5" />
                Runtime Source
              </Label>

              <Select value={form.runtimeSource} onValueChange={handleRuntimeSourceChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select runtime source" />
                </SelectTrigger>

                <SelectContent>
                  {(currentProvider?.runtime_options ?? []).map((option) => (
                    <SelectItem key={option.source} value={option.source}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedRuntimeOption && (
                <div className="space-y-2 rounded-xl border border-border/50 bg-muted/20 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold">
                      {selectedRuntimeOption.label}
                    </span>
                    <Badge
                      variant={selectedRuntimeOption.available ? "secondary" : "outline"}
                    >
                      {selectedRuntimeOption.available ? "Available" : "Setup Required"}
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground">
                    {selectedRuntimeOption.message}
                  </p>

                  {selectedRuntimeOption.setup_command && (
                    <code className="block break-all font-mono text-[10px] text-muted-foreground">
                      {selectedRuntimeOption.setup_command}
                    </code>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="admin-base-url" className="flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5" />
              Base URL
            </Label>

            <Input
              id="admin-base-url"
              value={form.baseUrl}
              onChange={(event) => updateForm({ baseUrl: event.target.value })}
              placeholder="http://host.docker.internal:11434"
              className="font-mono text-sm"
              readOnly={usesRuntimeOptions}
            />

            <p className="text-xs text-muted-foreground">
              {usesRuntimeOptions
                ? "For local runtime options, the selected runtime source determines the API endpoint."
                : "Optional backend endpoint override for providers that support it."}
            </p>
          </div>

          <Separator />

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="admin-timeout" className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                Response Timeout
              </Label>

              <Input
                id="admin-timeout"
                type="number"
                value={form.timeoutSeconds}
                onChange={(event) => updateForm({ timeoutSeconds: event.target.value })}
                min={5}
                max={300}
                className="max-w-[120px]"
              />

              <p className="text-xs text-muted-foreground">
                Backend-persisted timeout for model response handling when supported.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <Label htmlFor="admin-auto-download" className="flex items-center gap-1.5">
                  Auto-download models
                </Label>

                <Switch
                  id="admin-auto-download"
                  checked={form.autoDownload}
                  onCheckedChange={(value) => updateForm({ autoDownload: value })}
                />
              </div>

              <p className="text-xs text-muted-foreground">
                Backend policy flag for downloading missing local models. The backend must
                enforce safety, storage, and registry rules.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button
              onClick={() => void handleSave()}
              disabled={isSaving || !!formValidationError}
            >
              {isSaving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Configuration
            </Button>

            <Button
              variant="outline"
              onClick={() => void loadSettings()}
              disabled={isLoading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Reload
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registered Providers</CardTitle>
          <CardDescription>
            Providers and models reported by the backend registry.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {providerGroups.every((group) => group.providers.length === 0) ? (
            <div className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
              No registered providers were returned by the backend.
            </div>
          ) : (
            <div className="space-y-4">
              {providerGroups.map((group) => (
                <ProviderGroup
                  key={group.label}
                  label={group.label}
                  providers={group.providers}
                  selectedProvider={normalizedSettings?.selected_provider}
                  selectedModel={normalizedSettings?.selected_model}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}