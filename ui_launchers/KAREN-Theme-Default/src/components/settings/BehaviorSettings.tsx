// ui_launchers/KAREN-Theme-Default/src/components/settings/BehaviorSettings.tsx
"use client";

import React, { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';

import { } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch'; // Added Switch import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import type { KarenSettings, MemoryDepth, PersonalityTone, PersonalityVerbosity } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { Button } from '../ui/button';
import { useToast } from '@/hooks/use-toast';

/**
 * @file BehaviorSettings.tsx
 * @description Component for managing Karen AI's behavior settings.
 * Allows users to customize memory depth, personality tone, verbosity, and active listening.
 * Settings are saved to local storage.
 */
export default function BehaviorSettings() {
  const [settings, setSettings] = useState<Pick<KarenSettings, 'memoryDepth' | 'personalityTone' | 'personalityVerbosity' | 'activeListenMode'>>({
    memoryDepth: DEFAULT_KAREN_SETTINGS.memoryDepth,
    personalityTone: DEFAULT_KAREN_SETTINGS.personalityTone,
    personalityVerbosity: DEFAULT_KAREN_SETTINGS.personalityVerbosity,
    activeListenMode: DEFAULT_KAREN_SETTINGS.activeListenMode,
  });

  const { toast } = useToast();
  useEffect(() => {
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      let fullSettings: KarenSettings;
      if (storedSettingsStr) {
        const parsedSettings = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
        fullSettings = {
          ...DEFAULT_KAREN_SETTINGS,
          ...parsedSettings,
          notifications: { 
            ...DEFAULT_KAREN_SETTINGS.notifications,
            ...(parsedSettings.notifications || {}),
          },
          personalFacts: Array.isArray(parsedSettings.personalFacts)
            ? parsedSettings.personalFacts
            : DEFAULT_KAREN_SETTINGS.personalFacts,
          ttsVoiceURI: parsedSettings.ttsVoiceURI === undefined 
            ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI 
            : parsedSettings.ttsVoiceURI,
          customPersonaInstructions: typeof parsedSettings.customPersonaInstructions === 'string'
            ? parsedSettings.customPersonaInstructions
            : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
          activeListenMode: typeof parsedSettings.activeListenMode === 'boolean'
            ? parsedSettings.activeListenMode
            : DEFAULT_KAREN_SETTINGS.activeListenMode,
        };
        if (storedSettingsStr !== JSON.stringify(fullSettings)) {
            localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(fullSettings));
        }
      } else {
        fullSettings = DEFAULT_KAREN_SETTINGS;
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      }
      setSettings({
        memoryDepth: fullSettings.memoryDepth,
        personalityTone: fullSettings.personalityTone,
        personalityVerbosity: fullSettings.personalityVerbosity,
        activeListenMode: fullSettings.activeListenMode,
      });
    } catch (error) {
      setSettings({
        memoryDepth: DEFAULT_KAREN_SETTINGS.memoryDepth,
        personalityTone: DEFAULT_KAREN_SETTINGS.personalityTone,
        personalityVerbosity: DEFAULT_KAREN_SETTINGS.personalityVerbosity,
        activeListenMode: DEFAULT_KAREN_SETTINGS.activeListenMode,
      });
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch (lsError) {
      }
    }
  }, []);
  const handleSettingChange = (key: keyof typeof settings, value: string | boolean) => {
    setSettings(prevSettings => ({ ...prevSettings, [key]: value }));
  };
  const getFullCurrentSettingsFromStorage = (): KarenSettings => {
    let currentFullSettings = { ...DEFAULT_KAREN_SETTINGS };
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      if (storedSettingsStr) {
        const parsed = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
        currentFullSettings = {
          ...DEFAULT_KAREN_SETTINGS,
          ...parsed,
          notifications: { ...DEFAULT_KAREN_SETTINGS.notifications, ...(parsed.notifications || {}) },
          personalFacts: Array.isArray(parsed.personalFacts) ? parsed.personalFacts : DEFAULT_KAREN_SETTINGS.personalFacts,
          ttsVoiceURI: parsed.ttsVoiceURI === undefined ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI : parsed.ttsVoiceURI,
          customPersonaInstructions: typeof parsed.customPersonaInstructions === 'string' ? parsed.customPersonaInstructions : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
          temperatureUnit: parsed.temperatureUnit || DEFAULT_KAREN_SETTINGS.temperatureUnit,
          weatherService: parsed.weatherService || DEFAULT_KAREN_SETTINGS.weatherService,
          weatherApiKey: parsed.weatherApiKey === undefined ? DEFAULT_KAREN_SETTINGS.weatherApiKey : parsed.weatherApiKey,
          defaultWeatherLocation: parsed.defaultWeatherLocation === undefined ? DEFAULT_KAREN_SETTINGS.defaultWeatherLocation : parsed.defaultWeatherLocation,
          activeListenMode: typeof parsed.activeListenMode === 'boolean' ? parsed.activeListenMode : DEFAULT_KAREN_SETTINGS.activeListenMode,
        };
      }
    } catch (e) {
    }
    return currentFullSettings;
  };
  const saveSettingsToLocalStorage = () => {
    try {
      const currentFullSettings = getFullCurrentSettingsFromStorage();
      const updatedFullSettings: KarenSettings = {
        ...currentFullSettings,
        memoryDepth: settings.memoryDepth,
        personalityTone: settings.personalityTone,
        personalityVerbosity: settings.personalityVerbosity,
        activeListenMode: settings.activeListenMode,
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(updatedFullSettings));
      toast({
        title: "Behavior Settings Saved",
        description: "Karen's behavior settings have been updated.",
      });
    } catch (error) {
      toast({
        title: "Error Saving Settings",
        description: "Could not save behavior settings. localStorage might be disabled or full.",
        variant: "destructive",
      });
    }
  };
  const resetToDefaults = () => {
    const defaultBehaviorSettings = {
        memoryDepth: DEFAULT_KAREN_SETTINGS.memoryDepth,
        personalityTone: DEFAULT_KAREN_SETTINGS.personalityTone,
        personalityVerbosity: DEFAULT_KAREN_SETTINGS.personalityVerbosity,
        activeListenMode: DEFAULT_KAREN_SETTINGS.activeListenMode,
    };
    setSettings(defaultBehaviorSettings);
    try {
      const currentFullSettings = getFullCurrentSettingsFromStorage();
      const newFullSettings: KarenSettings = {
          ...currentFullSettings,
          ...defaultBehaviorSettings,
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newFullSettings));
      toast({
        title: "Behavior Settings Reset",
        description: "Karen's behavior settings have been reset to defaults.",
      });
    } catch (error) {
        toast({
            title: "Error Resetting Settings",
            description: "Could not reset behavior settings.",
            variant: "destructive",
        });
    }
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Customize Karen's Behavior</CardTitle>
        <CardDescription>
          Adjust how Karen interacts, remembers, and listens. Changes will apply to new interactions.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="divide-y divide-border">
          <div className="px-6 py-4">
            <div className="space-y-2">
              <Label htmlFor="memoryDepth">Memory Depth</Label>
              <Select
                value={settings.memoryDepth}
                onValueChange={(value) => handleSettingChange('memoryDepth', value as MemoryDepth)}
              >
                <SelectTrigger id="memoryDepth" aria-label="Select option">
                  <SelectValue placeholder="Select memory depth" />
                </SelectTrigger>
                <SelectContent aria-label="Select option">
                  <SelectItem value="short" aria-label="Select option">Short (Recent context)</SelectItem>
                  <SelectItem value="medium" aria-label="Select option">Medium (Key topics from session)</SelectItem>
                  <SelectItem value="long" aria-label="Select option">Long (Broader understanding)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Controls how far back Karen considers conversation history.</p>
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-2">
              <Label htmlFor="personalityTone">Personality Tone</Label>
              <Select
                value={settings.personalityTone}
                onValueChange={(value) => handleSettingChange('personalityTone', value as PersonalityTone)}
              >
                <SelectTrigger id="personalityTone" aria-label="Select option">
                  <SelectValue placeholder="Select tone" />
                </SelectTrigger>
                <SelectContent aria-label="Select option">
                  <SelectItem value="neutral" aria-label="Select option">Neutral</SelectItem>
                  <SelectItem value="friendly" aria-label="Select option">Friendly</SelectItem>
                  <SelectItem value="formal" aria-label="Select option">Formal</SelectItem>
                  <SelectItem value="humorous" aria-label="Select option">Humorous</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Influences the style of Karen's responses.</p>
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-2">
              <Label htmlFor="personalityVerbosity">Personality Verbosity</Label>
              <Select
                value={settings.personalityVerbosity}
                onValueChange={(value) => handleSettingChange('personalityVerbosity', value as PersonalityVerbosity)}
              >
                <SelectTrigger id="personalityVerbosity" aria-label="Select option">
                  <SelectValue placeholder="Select verbosity" />
                </SelectTrigger>
                <SelectContent aria-label="Select option">
                  <SelectItem value="concise" aria-label="Select option">Concise (To the point)</SelectItem>
                  <SelectItem value="balanced" aria-label="Select option">Balanced (Detailed but not overly long)</SelectItem>
                  <SelectItem value="detailed" aria-label="Select option">Detailed (Thorough explanations)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">Determines the length and detail of Karen's answers.</p>
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-2">
               <div className="flex items-center space-x-2">
                <Switch
                    id="active-listen-mode"
                    checked={settings.activeListenMode}
                    onCheckedChange={(checked) => handleSettingChange('activeListenMode', checked)}
                />
                <Label htmlFor="active-listen-mode" className="cursor-pointer">Active Listen Mode</Label>
              </div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                When enabled, if you use voice input, Karen will automatically try to listen again after she finishes speaking.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
            <Button variant="outline" onClick={resetToDefaults} >Reset to Defaults</Button>
            <Button onClick={saveSettingsToLocalStorage} >Save Settings</Button>
      </CardFooter>
    </Card>
  );
}
