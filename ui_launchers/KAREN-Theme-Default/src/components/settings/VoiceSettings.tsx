"use client";

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import type { KarenSettings } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { Button } from '../ui/button';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const DEFAULT_VOICE_SENTINEL = "_DEFAULT_VOICE_";

const normalizeSettingsFromStorage = (): KarenSettings => {
  if (typeof window === 'undefined') {
    return DEFAULT_KAREN_SETTINGS;
  }

  try {
    const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
    if (!storedSettingsStr) {
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      return DEFAULT_KAREN_SETTINGS;
    }

    const parsedSettings = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
    const normalized: KarenSettings = {
      ...DEFAULT_KAREN_SETTINGS,
      ...parsedSettings,
      notifications: {
        ...DEFAULT_KAREN_SETTINGS.notifications,
        ...(parsedSettings.notifications || {}),
      },
      personalFacts: Array.isArray(parsedSettings.personalFacts)
        ? parsedSettings.personalFacts
        : DEFAULT_KAREN_SETTINGS.personalFacts,
      ttsVoiceURI:
        parsedSettings.ttsVoiceURI === undefined
          ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI
          : parsedSettings.ttsVoiceURI,
      customPersonaInstructions: typeof parsedSettings.customPersonaInstructions === 'string'
        ? parsedSettings.customPersonaInstructions
        : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
    };

    const normalizedString = JSON.stringify(normalized);
    if (storedSettingsStr !== normalizedString) {
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, normalizedString);
    }

    return normalized;
  } catch (error) {
    console.error('Failed to read voice settings from storage:', error);
    try {
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
    } catch (lsError) {
      console.error('Failed to reset voice settings in storage:', lsError);
    }
    return DEFAULT_KAREN_SETTINGS;
  }
};

const getInitialVoices = (): SpeechSynthesisVoice[] => {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    return [];
  }
  return window.speechSynthesis.getVoices();
};

/**
 * @file VoiceSettings.tsx
 * @description Component for selecting a preferred Text-To-Speech (TTS) voice.
 * Fetches available system voices and allows users to save their preference to local storage.
 */
export default function VoiceSettings() {
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>(() => getInitialVoices());
  const [selectedVoiceURI, setSelectedVoiceURI] = useState<string | null>(() => {
    const settings = normalizeSettingsFromStorage();
    return settings.ttsVoiceURI;
  });
  const [isLoadingVoices, setIsLoadingVoices] = useState(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return false;
    }
    return window.speechSynthesis.getVoices().length === 0;
  });
  const { toast } = useToast();

  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return;
    }

    let cancelled = false;

    const updateVoices = () => {
      if (cancelled) {
        return;
      }
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices);
      setIsLoadingVoices(voices.length === 0);
    };

    const handleVoicesChanged = () => {
      updateVoices();
    };

    const initialTimeout = window.setTimeout(updateVoices, 0);
    const fallbackTimeout =
      window.speechSynthesis.getVoices().length === 0
        ? window.setTimeout(updateVoices, 500)
        : undefined;

    window.speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged);

    return () => {
      cancelled = true;
      window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
      if (initialTimeout !== undefined) {
        window.clearTimeout(initialTimeout);
      }
      if (fallbackTimeout !== undefined) {
        window.clearTimeout(fallbackTimeout);
      }
    };
  }, []);

  const getFullCurrentSettingsFromStorage = (): KarenSettings => {
    let currentFullSettings = { ...DEFAULT_KAREN_SETTINGS };
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      if (storedSettingsStr) {
        const parsed = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
        // Robust merging with defaults to handle potentially incomplete stored settings
        currentFullSettings = {
          ...DEFAULT_KAREN_SETTINGS,
          ...parsed,
          notifications: { ...DEFAULT_KAREN_SETTINGS.notifications, ...(parsed.notifications || {}) },
          personalFacts: Array.isArray(parsed.personalFacts) ? parsed.personalFacts : DEFAULT_KAREN_SETTINGS.personalFacts,
          customPersonaInstructions: typeof parsed.customPersonaInstructions === 'string' ? parsed.customPersonaInstructions : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
          // ensure behavior settings are also preserved if this component saves
          memoryDepth: parsed.memoryDepth || DEFAULT_KAREN_SETTINGS.memoryDepth,
          personalityTone: parsed.personalityTone || DEFAULT_KAREN_SETTINGS.personalityTone,
          personalityVerbosity: parsed.personalityVerbosity || DEFAULT_KAREN_SETTINGS.personalityVerbosity,
        };
      }
    } catch (e) {
      console.error('Error reading settings from storage:', e);
    }
    return currentFullSettings;
  };

  const saveSettings = () => {
    try {
      const currentFullSettings = getFullCurrentSettingsFromStorage();
      const newSettings: KarenSettings = {
        ...currentFullSettings, // Preserve settings from other tabs
        ttsVoiceURI: selectedVoiceURI,
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newSettings));
      toast({
        title: "Voice Settings Saved",
        description: "Your preferred voice has been updated.",
      });
    } catch (error) {
      console.error('Error saving voice settings:', error);
      toast({
        title: "Error Saving Voice Settings",
        description: "Could not save voice preferences. localStorage might be disabled or full.",
        variant: "destructive",
      });
    }
  };

  const resetToDefaults = () => {
    setSelectedVoiceURI(DEFAULT_KAREN_SETTINGS.ttsVoiceURI);
    try {
      const currentFullSettings = getFullCurrentSettingsFromStorage();
      const newSettings: KarenSettings = {
        ...currentFullSettings, // Preserve settings from other tabs
        ttsVoiceURI: DEFAULT_KAREN_SETTINGS.ttsVoiceURI // Reset only voice
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newSettings));
      toast({
        title: "Voice Settings Reset",
        description: "Voice preference has been reset to default.",
      });
    } catch (error) {
       console.error('Error resetting voice settings:', error);
       toast({
          title: "Error Resetting Voice Settings",
          description: "Could not reset voice preferences.",
          variant: "destructive",
       });
    }
  };

  if (typeof window !== 'undefined' && !window.speechSynthesis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Text-to-Speech Voice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Speech Synthesis Not Supported</AlertTitle>
            <AlertDescription>
              Your browser does not support the Web Speech API, which is required for changing voices.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="interactive">
      <CardHeader>
        <CardTitle className="text-lg">Text-to-Speech Voice</CardTitle>
        <CardDescription>
          Choose a preferred voice for Karen AI&rsquo;s spoken responses. Availability depends on your browser and operating system.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="divide-y divide-border">
            <div className="px-6 py-4">
                {isLoadingVoices && (
                <div className="flex items-center space-x-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Loading available voices...</span>
                </div>
                )}
                {!isLoadingVoices && availableVoices.length === 0 && (
                <Alert variant="default" className="bg-muted/30">
                    <AlertCircle className="h-4 w-4 !text-accent-foreground" />
                    <AlertTitle className="font-semibold text-accent-foreground">No Voices Found</AlertTitle>
                    <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
                    No speech synthesis voices were found in your browser. Voice selection is not available.
                    Karen will use the default system voice if TTS is attempted.
                    </AlertDescription>
                </Alert>
                )}
                {availableVoices.length > 0 && (
                <div className="space-y-2">
                    <Label htmlFor="tts-voice">Select Voice</Label>
                    <Select
                      value={selectedVoiceURI || DEFAULT_VOICE_SENTINEL} 
                      onValueChange={(value) => setSelectedVoiceURI(value === DEFAULT_VOICE_SENTINEL ? null : value)}
                      disabled={availableVoices.length === 0 || isLoadingVoices}
                    >
                      <SelectTrigger id="tts-voice">
                        <SelectValue placeholder="Default system voice" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={DEFAULT_VOICE_SENTINEL}>Default system voice</SelectItem>
                        {availableVoices.map((voice, index) => (
                          <SelectItem
                            key={`voice-option-${voice.voiceURI}-${index}`}
                            value={voice.voiceURI}
                          >
                            {voice.name} ({voice.lang}) {voice.default ? "[System Default]" : ""}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    If no voice is selected, or the selected voice is unavailable, the browser&rsquo;s default will be used.
                    </p>
                </div>
                )}
            </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
          <Button variant="outline" onClick={resetToDefaults}>Reset to Default</Button>
          <Button onClick={saveSettings}>Save Settings</Button>
      </CardFooter>
    </Card>
  );
}
