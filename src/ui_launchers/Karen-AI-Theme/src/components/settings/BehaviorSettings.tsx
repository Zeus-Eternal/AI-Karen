'use client';

/**
 * @file BehaviorSettings.tsx
 * @description Live-backed behavior settings for Karen.
 *
 * Backend ownership:
 * - Runtime behavior settings must persist through backend settings/profile APIs.
 * - UI may keep a temporary draft cache, but localStorage is not runtime truth.
 * - Success toast only fires after backend save succeeds.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Loader2, RotateCcw, Save } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';

import { useToast } from '@/hooks/use-toast';
import { ApiError, apiClient } from '@/lib/api';
import { DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import type {
  KarenSettings,
  MemoryDepth,
  PersonalityTone,
  PersonalityVerbosity,
} from '@/lib/types';

type BehaviorSettingsState = Pick<
  KarenSettings,
  | 'memoryDepth'
  | 'personalityTone'
  | 'personalityVerbosity'
  | 'activeListenMode'
>;

type BehaviorSettingsResponse = Partial<BehaviorSettingsState> & {
  behavior?: Partial<BehaviorSettingsState>;
  settings?: Partial<BehaviorSettingsState>;
};

type BackendStatus = 'checking' | 'available' | 'unavailable';

const BEHAVIOR_SETTINGS_ENDPOINT = '/api/settings/behavior';
const BEHAVIOR_DRAFT_CACHE_KEY = 'karen_behavior_settings_draft_v1';

const DEFAULT_BEHAVIOR_SETTINGS: BehaviorSettingsState = {
  memoryDepth: DEFAULT_KAREN_SETTINGS.memoryDepth,
  personalityTone: DEFAULT_KAREN_SETTINGS.personalityTone,
  personalityVerbosity: DEFAULT_KAREN_SETTINGS.personalityVerbosity,
  activeListenMode: DEFAULT_KAREN_SETTINGS.activeListenMode,
};

const MEMORY_DEPTH_VALUES: MemoryDepth[] = ['short', 'medium', 'long'];
const PERSONALITY_TONE_VALUES: PersonalityTone[] = [
  'neutral',
  'friendly',
  'formal',
  'humorous',
];
const PERSONALITY_VERBOSITY_VALUES: PersonalityVerbosity[] = [
  'concise',
  'balanced',
  'detailed',
];

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const getErrorMessage = (
  error: unknown,
  fallback = 'Behavior settings request failed.',
): string => {
  if (error instanceof ApiError && error.message.trim()) {
    return error.message.trim();
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  if (typeof error === 'string' && error.trim()) {
    return error.trim();
  }

  return fallback;
};

const isUnavailableError = (error: unknown): boolean => {
  return (
    error instanceof ApiError &&
    (error.status === 404 || error.status === 405 || error.status === 501)
  );
};

const normalizeMemoryDepth = (value: unknown): MemoryDepth => {
  const normalized = cleanString(value) as MemoryDepth;

  return MEMORY_DEPTH_VALUES.includes(normalized)
    ? normalized
    : DEFAULT_BEHAVIOR_SETTINGS.memoryDepth;
};

const normalizePersonalityTone = (value: unknown): PersonalityTone => {
  const normalized = cleanString(value) as PersonalityTone;

  return PERSONALITY_TONE_VALUES.includes(normalized)
    ? normalized
    : DEFAULT_BEHAVIOR_SETTINGS.personalityTone;
};

const normalizePersonalityVerbosity = (
  value: unknown,
): PersonalityVerbosity => {
  const normalized = cleanString(value) as PersonalityVerbosity;

  return PERSONALITY_VERBOSITY_VALUES.includes(normalized)
    ? normalized
    : DEFAULT_BEHAVIOR_SETTINGS.personalityVerbosity;
};

const normalizeBehaviorSettings = (
  value: unknown,
): BehaviorSettingsState => {
  const raw =
    value && typeof value === 'object'
      ? (value as BehaviorSettingsResponse)
      : {};

  const source =
    raw.behavior && typeof raw.behavior === 'object'
      ? raw.behavior
      : raw.settings && typeof raw.settings === 'object'
        ? raw.settings
        : raw;

  return {
    memoryDepth: normalizeMemoryDepth(source.memoryDepth),
    personalityTone: normalizePersonalityTone(source.personalityTone),
    personalityVerbosity: normalizePersonalityVerbosity(
      source.personalityVerbosity,
    ),
    activeListenMode:
      typeof source.activeListenMode === 'boolean'
        ? source.activeListenMode
        : DEFAULT_BEHAVIOR_SETTINGS.activeListenMode,
  };
};

const readDraftSettings = (): BehaviorSettingsState | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(BEHAVIOR_DRAFT_CACHE_KEY);

    if (!raw) {
      return null;
    }

    return normalizeBehaviorSettings(JSON.parse(raw));
  } catch {
    return null;
  }
};

const writeDraftSettings = (settings: BehaviorSettingsState): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(
      BEHAVIOR_DRAFT_CACHE_KEY,
      JSON.stringify(settings),
    );
  } catch {
    // Draft cache failure must not masquerade as backend persistence.
  }
};

const clearDraftSettings = (): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.removeItem(BEHAVIOR_DRAFT_CACHE_KEY);
  } catch {
    // Non-critical cleanup.
  }
};

export default function BehaviorSettings() {
  const [settings, setSettings] = useState<BehaviorSettingsState>(
    DEFAULT_BEHAVIOR_SETTINGS,
  );
  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>('checking');
  const [loadError, setLoadError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const { toast } = useToast();

  const hasDraft = useMemo(() => Boolean(readDraftSettings()), []);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    setLoadError('');

    const draft = readDraftSettings();

    if (draft) {
      setSettings(draft);
    }

    try {
      const response = await apiClient.get<BehaviorSettingsResponse>(
        BEHAVIOR_SETTINGS_ENDPOINT,
      );
      const liveSettings = normalizeBehaviorSettings(response);

      setSettings(liveSettings);
      setBackendStatus('available');
      clearDraftSettings();
    } catch (error) {
      setBackendStatus('unavailable');

      if (!draft) {
        setSettings(DEFAULT_BEHAVIOR_SETTINGS);
      }

      setLoadError(
        isUnavailableError(error)
          ? 'Behavior settings endpoint is not available yet.'
          : getErrorMessage(error, 'Karen could not load behavior settings.'),
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleSettingChange = useCallback(
    <K extends keyof BehaviorSettingsState>(
      key: K,
      value: BehaviorSettingsState[K],
    ) => {
      setSettings((current) => {
        const next = {
          ...current,
          [key]: value,
        };

        writeDraftSettings(next);
        return next;
      });
    },
    [],
  );

  const saveSettings = useCallback(
    async (nextSettings: BehaviorSettingsState) => {
      if (isSaving) {
        return;
      }

      setIsSaving(true);
      writeDraftSettings(nextSettings);

      try {
        const response = await apiClient.put<BehaviorSettingsResponse>(
          BEHAVIOR_SETTINGS_ENDPOINT,
          nextSettings,
        );
        const liveSettings = normalizeBehaviorSettings(response);

        setSettings(liveSettings);
        setBackendStatus('available');
        setLoadError('');
        clearDraftSettings();

        toast({
          title: 'Behavior Settings Saved',
          description: "Karen's behavior settings were synced to backend.",
        });
      } catch (error) {
        setBackendStatus('unavailable');
        setLoadError(
          isUnavailableError(error)
            ? 'Behavior settings endpoint is unavailable. Your changes remain a local draft only.'
            : getErrorMessage(error, 'Karen could not save behavior settings.'),
        );

        toast({
          title: 'Behavior Save Failed',
          description:
            isUnavailableError(error)
              ? 'Backend behavior settings are unavailable. Draft was kept locally but is not active runtime truth.'
              : getErrorMessage(error, 'Could not save behavior settings to backend.'),
          variant: 'destructive',
        });
      } finally {
        setIsSaving(false);
      }
    },
    [isSaving, toast],
  );

  const handleSave = useCallback(async () => {
    await saveSettings(settings);
  }, [saveSettings, settings]);

  const resetToDefaults = useCallback(async () => {
    setSettings(DEFAULT_BEHAVIOR_SETTINGS);
    writeDraftSettings(DEFAULT_BEHAVIOR_SETTINGS);
    await saveSettings(DEFAULT_BEHAVIOR_SETTINGS);
  }, [saveSettings]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Customize Karen&apos;s Behavior</CardTitle>
        <CardDescription>
          Adjust how Karen interacts, remembers, and listens. Changes apply after
          they sync to Karen&apos;s backend settings.
        </CardDescription>
      </CardHeader>

      <CardContent className="p-0">
        {backendStatus === 'unavailable' && (
          <div className="px-6 pb-4">
            <Alert className="border-amber-500/30 bg-amber-500/10">
              <AlertCircle
                className="h-4 w-4 !text-amber-600"
                aria-hidden="true"
              />
              <AlertTitle>Behavior Backend Unavailable</AlertTitle>
              <AlertDescription>
                {loadError ||
                  'Karen could not reach the live behavior settings endpoint.'}
                {hasDraft && (
                  <span className="mt-1 block">
                    A local draft may exist, but it is not active backend runtime
                    configuration until save succeeds.
                  </span>
                )}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {isLoading ? (
          <div
            className="flex items-center gap-2 px-6 py-6 text-sm text-muted-foreground"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading behavior settings.
          </div>
        ) : (
          <div className="divide-y divide-border">
            <div className="px-6 py-4">
              <div className="space-y-2">
                <Label htmlFor="memoryDepth">Memory Depth</Label>
                <Select
                  value={settings.memoryDepth}
                  onValueChange={(value) =>
                    handleSettingChange(
                      'memoryDepth',
                      normalizeMemoryDepth(value),
                    )
                  }
                >
                  <SelectTrigger id="memoryDepth">
                    <SelectValue placeholder="Select memory depth" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="short">Short (Recent context)</SelectItem>
                    <SelectItem value="medium">
                      Medium (Key topics from session)
                    </SelectItem>
                    <SelectItem value="long">
                      Long (Broader understanding)
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Controls how far back Karen considers conversation history.
                </p>
              </div>
            </div>

            <div className="px-6 py-4">
              <div className="space-y-2">
                <Label htmlFor="personalityTone">Personality Tone</Label>
                <Select
                  value={settings.personalityTone}
                  onValueChange={(value) =>
                    handleSettingChange(
                      'personalityTone',
                      normalizePersonalityTone(value),
                    )
                  }
                >
                  <SelectTrigger id="personalityTone">
                    <SelectValue placeholder="Select tone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="formal">Formal</SelectItem>
                    <SelectItem value="humorous">Humorous</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Influences the style of Karen&apos;s responses.
                </p>
              </div>
            </div>

            <div className="px-6 py-4">
              <div className="space-y-2">
                <Label htmlFor="personalityVerbosity">
                  Personality Verbosity
                </Label>
                <Select
                  value={settings.personalityVerbosity}
                  onValueChange={(value) =>
                    handleSettingChange(
                      'personalityVerbosity',
                      normalizePersonalityVerbosity(value),
                    )
                  }
                >
                  <SelectTrigger id="personalityVerbosity">
                    <SelectValue placeholder="Select verbosity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="concise">
                      Concise (To the point)
                    </SelectItem>
                    <SelectItem value="balanced">
                      Balanced (Detailed but not overly long)
                    </SelectItem>
                    <SelectItem value="detailed">
                      Detailed (Thorough explanations)
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Determines the length and detail of Karen&apos;s answers.
                </p>
              </div>
            </div>

            <div className="px-6 py-4">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="active-listen-mode"
                    checked={settings.activeListenMode}
                    onCheckedChange={(checked) =>
                      handleSettingChange('activeListenMode', checked)
                    }
                  />
                  <Label htmlFor="active-listen-mode" className="cursor-pointer">
                    Active Listen Mode
                  </Label>
                </div>
                <p className="text-xs text-muted-foreground">
                  When enabled, voice input can automatically listen again after
                  Karen finishes speaking, if the voice runtime supports it.
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-end space-x-2">
        <Button
          type="button"
          variant="outline"
          onClick={() => void resetToDefaults()}
          disabled={isLoading || isSaving}
        >
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <RotateCcw className="mr-2 h-4 w-4" aria-hidden="true" />
          )}
          Reset to Defaults
        </Button>

        <Button
          type="button"
          onClick={() => void handleSave()}
          disabled={isLoading || isSaving}
        >
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Save className="mr-2 h-4 w-4" aria-hidden="true" />
          )}
          Save Settings
        </Button>
      </CardFooter>
    </Card>
  );
}