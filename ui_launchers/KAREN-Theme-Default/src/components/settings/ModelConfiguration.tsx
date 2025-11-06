"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, RefreshCw, RotateCcw, Save, ShieldCheck } from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';

export interface SystemModelConfig {
  defaultModel?: string;
  fallbackModel?: string;
  autoSelectEnabled?: boolean;
  preferLocalModels?: boolean;
  allowedProviders?: string[];
  maxConcurrentModels?: number;
  modelSelectionTimeout?: number;
  enableModelCaching?: boolean;
  cacheExpirationTime?: number;
}

export interface SystemModelSummary {
  id: string;
  name: string;
  family?: string;
  format?: string;
  status?: string;
  capabilities?: string[];
  runtime_compatibility?: string[];
  configuration?: Record<string, unknown>;
  last_health_check?: number | string;
  error_message?: string;
  parameters?: string;
  size?: number;
}

export interface ModelConfigurationProps {
  modelId?: string;
  onModelChange?: (modelId: string) => void;
}

const CONFIG_DEFAULTS: Required<SystemModelConfig> = {
  defaultModel: '',
  fallbackModel: '',
  autoSelectEnabled: true,
  preferLocalModels: true,
  allowedProviders: [],
  maxConcurrentModels: 1,
  modelSelectionTimeout: 60000,
  enableModelCaching: true,
  cacheExpirationTime: 300000,
};

const ALLOWED_FIELDS: (keyof SystemModelConfig)[] = [
  'defaultModel',
  'fallbackModel',
  'autoSelectEnabled',
  'preferLocalModels',
  'allowedProviders',
  'maxConcurrentModels',
  'modelSelectionTimeout',
  'enableModelCaching',
  'cacheExpirationTime',
];

const WELL_KNOWN_PROVIDERS = [
  'openai',
  'anthropic',
  'local',
  'huggingface',
  'ollama',
  'gemini',
  'azure',
  'google',
];

const REQUEST_TIMEOUT_MS = 15000;

function normalizeConfig(config?: SystemModelConfig | null): SystemModelConfig {
  if (!config) {
    return { ...CONFIG_DEFAULTS };
  }

  const normalized: SystemModelConfig = {
    ...CONFIG_DEFAULTS,
    ...config,
  };

  normalized.allowedProviders = Array.from(
    new Set((normalized.allowedProviders ?? []).filter(Boolean)),
  );

  return normalized;
}

function cloneConfig(config?: SystemModelConfig | null): SystemModelConfig {
  return normalizeConfig(
    config ? (JSON.parse(JSON.stringify(config)) as SystemModelConfig) : undefined,
  );
}

function sanitizeConfig(config: SystemModelConfig): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {};

  for (const field of ALLOWED_FIELDS) {
    const value = config[field];

    if (value === undefined || value === null) {
      continue;
    }

    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed) {
        sanitized[field] = trimmed;
      }
      continue;
    }

    if (Array.isArray(value)) {
      const filtered = value
        .map((entry) => (typeof entry === 'string' ? entry.trim() : ''))
        .filter(Boolean);
      sanitized[field] = filtered;
      continue;
    }

    if (typeof value === 'number') {
      if (Number.isFinite(value)) {
        sanitized[field] = value;
      }
      continue;
    }

    sanitized[field] = value;
  }

  return sanitized;
}

function formatConfigValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }

  if (typeof value === 'boolean') {
    return value ? 'Enabled' : 'Disabled';
  }

  if (Array.isArray(value)) {
    return value.map((entry) => String(entry)).join(', ');
  }

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      logger.warn('Failed to stringify configuration value', error);
      return String(value);
    }
  }

  return String(value);
}

function toDate(value?: number | string | null): Date | null {
  if (value === undefined || value === null) {
    return null;
  }

  if (typeof value === 'string') {
    const timestamp = Number(value);
    if (!Number.isNaN(timestamp)) {
      return toDate(timestamp);
    }
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  if (!Number.isFinite(value)) {
    return null;
  }

  const asNumber = Number(value);
  const millis = asNumber > 1_000_000_000_000 ? asNumber : asNumber * 1000;
  const parsed = new Date(millis);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

const ModelConfiguration: React.FC<ModelConfigurationProps> = ({
  modelId,
  onModelChange,
}) => {
  const backend = useMemo(() => getKarenBackend(), []);
  const { toast } = useToast();

  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<SystemModelConfig | null>(null);
  const [workingConfig, setWorkingConfig] = useState<SystemModelConfig | null>(
    null,
  );
  const [models, setModels] = useState<SystemModelSummary[]>([]);
  const [activeModelId, setActiveModelId] = useState<string | undefined>(modelId);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    if (modelId) {
      setActiveModelId(modelId);
    }
  }, [modelId]);

  const loadConfiguration = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [configResponse, modelsResponse] = await Promise.all([
        backend.makeRequestPublic<SystemModelConfig>('/api/system/config/models', {
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        }),
        backend.makeRequestPublic<SystemModelSummary[] | { models: SystemModelSummary[] }>(
          '/api/models/system',
          {
            signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
          },
        ),
      ]);

      const normalizedConfig = normalizeConfig(configResponse);
      const normalizedModels = Array.isArray(modelsResponse)
        ? modelsResponse
        : modelsResponse?.models ?? [];

      setConfig(normalizedConfig);
      setWorkingConfig(cloneConfig(normalizedConfig));
      setModels(normalizedModels);
      setLastUpdated(new Date());

      if (!modelId && normalizedConfig.defaultModel) {
        setActiveModelId(normalizedConfig.defaultModel);
        onModelChange?.(normalizedConfig.defaultModel);
      }

      logger.info('Loaded system model configuration', {
        modelCount: normalizedModels.length,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      logger.error(
        'Failed to load system configuration',
        { message },
        { rateLimitKey: 'system-config-load' },
      );
      setError(
        'Unable to load system configuration from the Kari backend. Please verify the backend service is reachable and you have sufficient permissions.',
      );
    } finally {
      setLoading(false);
    }
  }, [backend, modelId, onModelChange]);

  useEffect(() => {
    void loadConfiguration();
  }, [loadConfiguration]);

  const availableProviders = useMemo(() => {
    const providers = new Set<string>([...WELL_KNOWN_PROVIDERS]);

    (workingConfig?.allowedProviders ?? []).forEach((provider) => {
      if (provider) {
        providers.add(provider);
      }
    });

    models.forEach((model) => {
      const compatibility = model.runtime_compatibility ?? [];
      compatibility.forEach((provider) => {
        if (provider) {
          providers.add(provider);
        }
      });
    });

    return Array.from(providers).sort();
  }, [models, workingConfig?.allowedProviders]);

  const selectedModel = useMemo(() => {
    if (!activeModelId) {
      return undefined;
    }
    return models.find((model) => model.id === activeModelId);
  }, [activeModelId, models]);

  const hasChanges = useMemo(() => {
    if (!config && !workingConfig) {
      return false;
    }
    return (
      JSON.stringify(normalizeConfig(workingConfig)) !==
      JSON.stringify(normalizeConfig(config))
    );
  }, [config, workingConfig]);

  const updateConfig = useCallback(
    <K extends keyof SystemModelConfig>(key: K, value: SystemModelConfig[K]) => {
      setWorkingConfig((previous) => {
        if (!previous) {
          return previous;
        }
        return {
          ...previous,
          [key]: value,
        };
      });
    },
    [],
  );

  const handleDefaultModelChange = useCallback(
    (value: string) => {
      updateConfig('defaultModel', value);
      setActiveModelId(value || undefined);
      if (value) {
        onModelChange?.(value);
      }
    },
    [onModelChange, updateConfig],
  );

  const handleFallbackModelChange = useCallback(
    (value: string) => {
      updateConfig('fallbackModel', value);
    },
    [updateConfig],
  );

  const toggleProvider = useCallback(
    (provider: string) => {
      setWorkingConfig((previous) => {
        if (!previous) {
          return previous;
        }

        const current = new Set(previous.allowedProviders ?? []);
        if (current.has(provider)) {
          current.delete(provider);
        } else {
          current.add(provider);
        }

        return {
          ...previous,
          allowedProviders: Array.from(current).sort(),
        };
      });
    },
    [],
  );

  const handleNumberChange = useCallback(
    (key: 'maxConcurrentModels' | 'modelSelectionTimeout' | 'cacheExpirationTime') =>
      (event: React.ChangeEvent<HTMLInputElement>) => {
        const rawValue = event.target.value;
        const numeric = Number(rawValue);
        if (Number.isFinite(numeric)) {
          updateConfig(key, Math.max(0, Math.floor(numeric)));
        } else if (rawValue === '') {
          updateConfig(key, undefined);
        }
      },
    [updateConfig],
  );

  const handleSave = useCallback(async () => {
    if (!workingConfig) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = sanitizeConfig(workingConfig);

      const response = await backend.makeRequestPublic('/api/system/config/models', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      });

      const updated = normalizeConfig({ ...workingConfig, ...response });
      setConfig(updated);
      setWorkingConfig(cloneConfig(updated));
      setLastUpdated(new Date());

      toast({
        title: 'Configuration updated',
        description: 'System model routing preferences were saved successfully.',
      });
      logger.info('System configuration saved successfully');
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      logger.error('Failed to save system configuration', { message });
      setError(
        'Unable to save the current configuration. Please review your changes and try again.',
      );
    } finally {
      setSaving(false);
    }
  }, [backend, toast, workingConfig]);

  const handleReset = useCallback(() => {
    if (!config) {
      return;
    }
    setWorkingConfig(cloneConfig(config));
  }, [config]);

  const handleRefresh = useCallback(() => {
    void loadConfiguration();
  }, [loadConfiguration]);

  if (loading && !workingConfig) {
    return (
      <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 p-8 text-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">
            Loading system configuration…
          </p>
          <p className="text-xs text-muted-foreground">
            Connecting to the Kari orchestration backend.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            Model Configuration
          </h3>
          <p className="text-sm text-muted-foreground">
            Configure Kari's default reasoning models, fallbacks, and routing
            preferences for production traffic.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={loading || saving}
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={!hasChanges || saving}
          >
            <RotateCcw className="mr-2 h-4 w-4" /> Reset
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Configuration issue detected</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Routing preferences</CardTitle>
          <CardDescription>
            Configure default models and fallback models.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="default-model">Primary model</Label>
              <Select
                value={workingConfig?.defaultModel ?? ''}
                onValueChange={handleDefaultModelChange}
              >
                <SelectTrigger id="default-model">
                  <SelectValue placeholder="Select a default model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name || model.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Persona overrides the selection.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="fallback-model">Fallback model</Label>
              <Select
                value={workingConfig?.fallbackModel ?? ''}
                onValueChange={handleFallbackModelChange}
              >
                <SelectTrigger id="fallback-model">
                  <SelectValue placeholder="Select a fallback model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name || model.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Used when primary model is unhealthy.
              </p>
            </div>
          </div>

          <Separator />

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium">Intelligent routing</p>
                  <p className="text-sm text-muted-foreground">
                    Use live telemetry for model selection.
                  </p>
                </div>
                <Switch
                  checked={workingConfig?.autoSelectEnabled ?? true}
                  onCheckedChange={(checked) =>
                    updateConfig('autoSelectEnabled', checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium">Prefer local runtimes</p>
                  <p className="text-sm text-muted-foreground">
                    Route requests to on-premise models before cloud providers
                    when available.
                  </p>
                </div>
                <Switch
                  checked={workingConfig?.preferLocalModels ?? true}
                  onCheckedChange={(checked) =>
                    updateConfig('preferLocalModels', checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium">Response caching</p>
                  <p className="text-sm text-muted-foreground">
                    Cache model responses for similar queries.
                  </p>
                </div>
                <Switch
                  checked={workingConfig?.enableModelCaching ?? true}
                  onCheckedChange={(checked) =>
                    updateConfig('enableModelCaching', checked)
                  }
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="max-concurrent">Concurrent models</Label>
                <Input
                  id="max-concurrent"
                  type="number"
                  min={1}
                  value={workingConfig?.maxConcurrentModels ?? 1}
                  onChange={handleNumberChange('maxConcurrentModels')}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum number of models to run concurrently.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="routing-timeout">Routing timeout (ms)</Label>
                <Input
                  id="routing-timeout"
                  type="number"
                  min={1000}
                  step={500}
                  value={workingConfig?.modelSelectionTimeout ?? 60000}
                  onChange={handleNumberChange('modelSelectionTimeout')}
                />
                <p className="text-xs text-muted-foreground">
                  Timeout for model selection and fallback chain.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="cache-ttl">Cache expiration (ms)</Label>
                <Input
                  id="cache-ttl"
                  type="number"
                  min={1000}
                  step={1000}
                  value={workingConfig?.cacheExpirationTime ?? 300000}
                  onChange={handleNumberChange('cacheExpirationTime')}
                />
                <p className="text-xs text-muted-foreground">
                  Time before cached responses expire and fresh inference is required.
                </p>
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-3">
            <p className="font-medium">Allowed providers</p>
            <p className="text-sm text-muted-foreground">
              Configure allowed providers based on security and residency policies.
            </p>
            <div className="flex flex-wrap gap-2">
              {availableProviders.map((provider) => {
                const isEnabled = workingConfig?.allowedProviders?.includes(
                  provider,
                );
                return (
                  <Button
                    key={provider}
                    type="button"
                    variant={isEnabled ? 'secondary' : 'outline'}
                    size="sm"
                    onClick={() => toggleProvider(provider)}
                  >
                    {provider}
                  </Button>
                );
              })}
              {availableProviders.length === 0 && (
                <span className="text-sm text-muted-foreground">
                  No providers detected. Configure models to populate this list.
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>Active model insight</CardTitle>
            <CardDescription>
              Detailed information about the selected system model.
            </CardDescription>
          </div>
          <Select
            value={activeModelId ?? ''}
            onValueChange={(value) => {
              setActiveModelId(value || undefined);
              if (value) {
                onModelChange?.(value);
              }
            }}
          >
            <SelectTrigger className="w-full sm:w-[240px]">
              <SelectValue placeholder="Select a system model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None selected</SelectItem>
              {models.map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  {model.name || model.id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent className="space-y-4">
          {selectedModel ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Badge
                  variant={
                    selectedModel.status === 'healthy' ? 'secondary' : 'destructive'
                  }
                >
                  {selectedModel.status ? selectedModel.status.toUpperCase() : 'UNKNOWN'}
                </Badge>
                {selectedModel.parameters && (
                  <Badge variant="outline">{selectedModel.parameters}</Badge>
                )}
                {selectedModel.format && (
                  <Badge variant="outline">{selectedModel.format}</Badge>
                )}
                {selectedModel.size && (
                  <Badge variant="outline">{`${selectedModel.size} bytes`}</Badge>
                )}
              </div>

              <div>
                <p className="font-medium text-foreground">
                  {selectedModel.name || selectedModel.id}
                </p>
                {selectedModel.capabilities && selectedModel.capabilities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedModel.capabilities.map((capability) => (
                      <Badge key={capability} variant="secondary">
                        {capability}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {selectedModel.error_message && (
                <Alert variant="destructive">
                  <AlertTitle>Health warnings detected</AlertTitle>
                  <AlertDescription>
                    {selectedModel.error_message}
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid gap-3 md:grid-cols-2">
                {selectedModel.runtime_compatibility && (
                  <div className="rounded-lg border p-3">
                    <p className="text-sm font-medium">Runtime compatibility</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedModel.runtime_compatibility ?? []).join(', ') || 'N/A'}
                    </p>
                  </div>
                )}
                {selectedModel.last_health_check && (
                  <div className="rounded-lg border p-3">
                    <p className="text-sm font-medium">Last health check</p>
                    <p className="text-sm text-muted-foreground">
                      {(() => {
                        const parsed = toDate(selectedModel.last_health_check);
                        return parsed ? parsed.toLocaleString() : 'N/A';
                      })()}
                    </p>
                  </div>
                )}
              </div>

              {selectedModel.configuration && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-500" />
                    <p className="font-medium">Runtime configuration</p>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {Object.entries(selectedModel.configuration).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="rounded-lg border bg-muted/40 p-3"
                        >
                          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className="mt-1 text-sm text-foreground whitespace-pre-wrap">
                            {formatConfigValue(value)}
                          </p>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed p-6 text-center">
              <p className="font-medium text-foreground">
                Select a model to view detailed signals.
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                You can validate capacity before promoting updates to production.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {lastUpdated && (
        <p className="text-xs text-muted-foreground">
          Last synced {lastUpdated.toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default ModelConfiguration;