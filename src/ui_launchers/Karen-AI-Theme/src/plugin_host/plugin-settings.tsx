"use client";

/**
 * Plugin Settings UI - Configuration interface for plugins.
 *
 * Provides:
 * - PluginSettingsProvider for managing plugin settings
 * - usePluginSettings hook for accessing plugin settings
 * - PluginSettingsForm component for rendering settings
 * - Settings persistence with backend integration
 * - Schema-based form generation
 * - Type-safe settings access
 *
 * Requirements: 4.3
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Save, RotateCcw, AlertCircle, CheckCircle2 } from 'lucide-react';
import apiClient from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

/** Supported setting types */
export type SettingType = 'string' | 'number' | 'boolean' | 'text' | 'select' | 'password' | 'json';

/** Setting schema definition */
export interface SettingSchema {
  /** Setting key */
  key: string;
  /** Display label */
  label: string;
  /** Description/tooltip */
  description?: string;
  /** Setting type */
  type: SettingType;
  /** Default value */
  defaultValue?: unknown;
  /** Validation options */
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    minLength?: number;
    maxLength?: number;
  };
  /** Options for select type */
  options?: Array<{
    value: string;
    label: string;
    description?: string;
  }>;
  /** Whether setting is read-only */
  readOnly?: boolean;
  /** Whether setting requires plugin restart */
  requiresRestart?: boolean;
  /** Category for grouping */
  category?: string;
  /** Order within category */
  order?: number;
}

/** Plugin settings configuration */
export interface PluginSettingsConfig {
  /** Plugin ID */
  pluginId: string;
  /** Settings schema */
  schema: SettingSchema[];
  /** Current settings values */
  values: Record<string, unknown>;
  /** Whether settings are loaded */
  loaded: boolean;
  /** Whether settings are modified */
  modified: boolean;
  /** Error state */
  error: string | null;
}

/** Settings context value */
export interface PluginSettingsContextValue {
  /** Get settings for a plugin */
  getPluginSettings: (pluginId: string) => PluginSettingsConfig | undefined;
  /** Save settings for a plugin */
  savePluginSettings: (pluginId: string) => Promise<boolean>;
  /** Reset settings to defaults */
  resetPluginSettings: (pluginId: string) => Promise<boolean>;
  /** Update a setting value */
  updateSetting: (pluginId: string, key: string, value: unknown) => void;
  /** Refresh settings from backend */
  refreshSettings: (pluginId: string) => Promise<void>;
  /** Load all plugins' settings */
  loadAllSettings: () => Promise<void>;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const PluginSettingsContext = createContext<PluginSettingsContextValue | null>(null);

// ─── Provider ──────────────────────────────────────────────────────────────────

export function PluginSettingsProvider({ children }: { children: React.ReactNode }) {
  const [pluginSettings, setPluginSettings] = useState<Map<string, PluginSettingsConfig>>(new Map());

  const getPluginSettings = useCallback((pluginId: string): PluginSettingsConfig | undefined => {
    return pluginSettings.get(pluginId);
  }, [pluginSettings]);

  const updateSetting = useCallback((pluginId: string, key: string, value: unknown) => {
    setPluginSettings((prev) => {
      const config = prev.get(pluginId);
      if (!config) return prev;

      return new Map(prev).set(pluginId, {
        ...config,
        values: { ...config.values, [key]: value },
        modified: true,
      });
    });
  }, []);

  const refreshSettings = useCallback(async (pluginId: string) => {
    try {
      setPluginSettings((prev) => {
        const config = prev.get(pluginId);
        if (config) {
          return new Map(prev).set(pluginId, { ...config, loaded: false, error: null });
        }
        return prev;
      });

      const response = await apiClient.get<{
        plugin_id: string;
        settings: Record<string, unknown>;
        schema: SettingSchema[];
      }>(`/api/extensions/${pluginId}/settings`);

      const settings = response || { plugin_id: pluginId, settings: {}, schema: [] };

      setPluginSettings((prev) => {
        const newConfig: PluginSettingsConfig = {
          pluginId: settings.plugin_id || pluginId,
          schema: settings.schema || [],
          values: settings.settings || {},
          loaded: true,
          modified: false,
          error: null,
        };
        return new Map(prev).set(pluginId, newConfig);
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load settings';
      setPluginSettings((prev) => {
        const config = prev.get(pluginId);
        if (config) {
          return new Map(prev).set(pluginId, { ...config, loaded: true, error: message });
        }
        return prev;
      });
    }
  }, []);

  const savePluginSettings = useCallback(async (pluginId: string): Promise<boolean> => {
    const config = pluginSettings.get(pluginId);
    if (!config || !config.modified) return true;

    try {
      await apiClient.post(`/api/extensions/${pluginId}/settings`, {
        settings: config.values,
      });

      setPluginSettings((prev) => {
        const updated = prev.get(pluginId);
        if (updated) {
          return new Map(prev).set(pluginId, { ...updated, modified: false });
        }
        return prev;
      });

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save settings';
      setPluginSettings((prev) => {
        const updated = prev.get(pluginId);
        if (updated) {
          return new Map(prev).set(pluginId, { ...updated, error: message });
        }
        return prev;
      });
      return false;
    }
  }, [pluginSettings]);

  const resetPluginSettings = useCallback(async (pluginId: string): Promise<boolean> => {
    try {
      await apiClient.delete(`/api/extensions/${pluginId}/settings`);

      setPluginSettings((prev) => {
        const config = prev.get(pluginId);
        if (config) {
          const defaultValues: Record<string, unknown> = {};
          config.schema.forEach((s) => {
            if (s.defaultValue !== undefined) {
              defaultValues[s.key] = s.defaultValue;
            }
          });
          return new Map(prev).set(pluginId, {
            ...config,
            values: defaultValues,
            modified: false,
            error: null,
          });
        }
        return prev;
      });

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reset settings';
      setPluginSettings((prev) => {
        const config = prev.get(pluginId);
        if (config) {
          return new Map(prev).set(pluginId, { ...config, error: message });
        }
        return prev;
      });
      return false;
    }
  }, []);

  const loadAllSettings = useCallback(async () => {
    try {
      const response = await apiClient.get<Array<{
        plugin_id: string;
        settings: Record<string, unknown>;
        schema: SettingSchema[];
      }>>('/api/extensions/settings');

      const settingsList = response || [];
      const newMap = new Map<string, PluginSettingsConfig>();

      for (const item of settingsList) {
        newMap.set(item.plugin_id, {
          pluginId: item.plugin_id,
          schema: item.schema || [],
          values: item.settings || {},
          loaded: true,
          modified: false,
          error: null,
        });
      }

      setPluginSettings(newMap);
    } catch (err) {
      console.error('Failed to load all settings:', err);
    }
  }, []);

  const value: PluginSettingsContextValue = {
    getPluginSettings,
    savePluginSettings,
    resetPluginSettings,
    updateSetting,
    refreshSettings,
    loadAllSettings,
  };

  return React.createElement(PluginSettingsContext.Provider, { value }, children);
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function usePluginSettings(pluginId: string): PluginSettingsConfig {
  const context = useContext(PluginSettingsContext);
  if (!context) {
    throw new Error('usePluginSettings must be used within a PluginSettingsProvider');
  }

  const config = context.getPluginSettings(pluginId);
  if (!config) {
    return {
      pluginId,
      schema: [],
      values: {},
      loaded: false,
      modified: false,
      error: 'Settings not loaded',
    };
  }

  return config;
}

export function usePluginSettingsManager(): PluginSettingsContextValue {
  const context = useContext(PluginSettingsContext);
  if (!context) {
    throw new Error('usePluginSettingsManager must be used within a PluginSettingsProvider');
  }
  return context;
}

// ─── Components ───────────────────────────────────────────────────────────────

/** Form field for a single setting */
function SettingField({
  setting,
  value,
  onChange,
  readOnly,
}: {
  setting: SettingSchema;
  value: unknown;
  onChange: (value: unknown) => void;
  readOnly?: boolean;
}) {
  const id = `setting-${setting.key}`;

  switch (setting.type) {
    case 'boolean':
      return (
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor={id}>{setting.label}</Label>
            {setting.description && (
              <p className="text-xs text-muted-foreground">{setting.description}</p>
            )}
          </div>
          <Switch
            id={id}
            checked={Boolean(value)}
            onCheckedChange={onChange}
            disabled={readOnly}
          />
        </div>
      );

    case 'select':
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Select value={String(value)} onValueChange={onChange} disabled={readOnly}>
            <SelectTrigger id={id}>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {setting.options?.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );

    case 'number':
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Input
            id={id}
            type="number"
            value={value !== undefined ? String(value) : ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
            disabled={readOnly}
            min={setting.validation?.min}
            max={setting.validation?.max}
          />
        </div>
      );

    case 'text':
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Textarea
            id={id}
            value={String(value || '')}
            onChange={(e) => onChange(e.target.value)}
            disabled={readOnly}
            rows={3}
            maxLength={setting.validation?.maxLength}
          />
        </div>
      );

    case 'password':
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Input
            id={id}
            type="password"
            value={String(value || '')}
            onChange={(e) => onChange(e.target.value)}
            disabled={readOnly}
          />
        </div>
      );

    case 'json':
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Textarea
            id={id}
            value={value !== undefined ? JSON.stringify(value, null, 2) : ''}
            onChange={(e) => {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            }}
            disabled={readOnly}
            rows={5}
            className="font-mono text-xs"
          />
        </div>
      );

    case 'string':
    default:
      return (
        <div className="space-y-2">
          <Label htmlFor={id}>{setting.label}</Label>
          {setting.description && (
            <p className="text-xs text-muted-foreground">{setting.description}</p>
          )}
          <Input
            id={id}
            type="text"
            value={String(value || '')}
            onChange={(e) => onChange(e.target.value)}
            disabled={readOnly}
            maxLength={setting.validation?.maxLength}
          />
        </div>
      );
  }
}

/** Form for editing a plugin's settings */
export function PluginSettingsForm({
  pluginId,
  onClose,
}: {
  pluginId: string;
  onClose?: () => void;
}) {
  const { values: settings, schema, loaded, modified, error } = usePluginSettings(pluginId);
  const { updateSetting, savePluginSettings, resetPluginSettings } = usePluginSettingsManager();
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    const success = await savePluginSettings(pluginId);
    setSaving(false);
    if (success) {
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        onClose?.();
      }, 1500);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    await resetPluginSettings(pluginId);
    setResetting(false);
  };

  // Group settings by category
  const groupedSettings = React.useMemo(() => {
    const groups: Record<string, SettingSchema[]> = {};
    for (const s of schema) {
      const category = s.category || 'General';
      if (!groups[category]) groups[category] = [];
      groups[category].push(s);
    }
    // Sort within each group
    for (const category of Object.keys(groups)) {
      groups[category].sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
    }
    return groups;
  }, [schema]);

  if (!loaded) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="ml-2 text-sm text-muted-foreground">Loading settings...</span>
        </CardContent>
      </Card>
    );
  }

  if (error && schema.length === 0) {
    return (
      <Card>
        <CardContent className="p-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {saveSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>Settings saved successfully!</AlertDescription>
        </Alert>
      )}

      {Object.entries(groupedSettings).map(([category, categoryFields]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="text-lg">{category}</CardTitle>
            <CardDescription>
              Configure {category.toLowerCase()} settings for this plugin
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {categoryFields.map((setting) => (
              <SettingField
                key={setting.key}
                setting={setting}
                value={settings[setting.key]}
                onChange={(value) => updateSetting(pluginId, setting.key, value)}
                readOnly={setting.readOnly}
              />
            ))}
          </CardContent>
        </Card>
      ))}

      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={resetting || !modified}
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          {resetting ? 'Resetting...' : 'Reset to Defaults'}
        </Button>
        <Button onClick={handleSave} disabled={saving || !modified}>
          <Save className="mr-2 h-4 w-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
    </div>
  );
}

/** Badge showing restart requirement */
export function RestartRequiredBadge() {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 px-2 py-0.5 rounded-full">
      <AlertCircle className="h-3 w-3" />
      restart required
    </span>
  );
}