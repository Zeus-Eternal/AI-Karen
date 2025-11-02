"use client";

import React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { Label } from '@/components/ui/label';

import { } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import type { KarenSettings } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { Button } from '../ui/button';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
const DEFAULT_VOICE_SENTINEL = "_DEFAULT_VOICE_";
/**
 * @file VoiceSettings.tsx
 * @description Component for selecting a preferred Text-To-Speech (TTS) voice.
 * Fetches available system voices and allows users to save their preference to local storage.
 */
export default function VoiceSettings() {
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState<string | null>(
    DEFAULT_KAREN_SETTINGS.ttsVoiceURI
  );
  const [isLoadingVoices, setIsLoadingVoices] = useState(true);
  const { toast } = useToast();
  const populateVoiceList = useCallback(() => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        setAvailableVoices(voices);
        setIsLoadingVoices(false);
      } else {
        // Voices might load asynchronously. If no voices found, try again after a short delay.
        // This timeout is a common workaround for browsers where getVoices() is initially empty.
        setTimeout(() => {
            const currentVoices = window.speechSynthesis.getVoices();
            if(currentVoices.length === 0) {
                 // Still no voices after delay
                 setIsLoadingVoices(false);
            } else {
                setAvailableVoices(currentVoices);
                setIsLoadingVoices(false);
            }
        }, 500); // Adjust delay as needed, 500ms is a reasonable starting point
      }
    } else {
      setIsLoadingVoices(false); // Speech synthesis not supported
    }
  }, []); // Empty dependency array: populateVoiceList reference is stable
  useEffect(() => {
    populateVoiceList(); // Initial call
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // Listen for changes in available voices
      window.speechSynthesis.addEventListener('voiceschanged', populateVoiceList);
      return () => {
        window.speechSynthesis.removeEventListener('voiceschanged', populateVoiceList);
      };
    }
  }, [populateVoiceList]); // populateVoiceList is stable due to its own empty dep array
  useEffect(() => {
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      let fullSettings: KarenSettings;
      if (storedSettingsStr) {
        const parsedSettings = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
         fullSettings = { // Ensure all fields are present by merging with defaults
            ...DEFAULT_KAREN_SETTINGS,
            ...parsedSettings,
            notifications: { // Deep merge for nested objects
                ...DEFAULT_KAREN_SETTINGS.notifications,
                ...(parsedSettings.notifications || {}),
            },
            personalFacts: Array.isArray(parsedSettings.personalFacts)
              ? parsedSettings.personalFacts
              : DEFAULT_KAREN_SETTINGS.personalFacts,
            // Ensure new fields are handled even if not in old stored settings
            ttsVoiceURI: parsedSettings.ttsVoiceURI === undefined // Check explicitly for undefined
              ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI
              : parsedSettings.ttsVoiceURI,
            customPersonaInstructions: typeof parsedSettings.customPersonaInstructions === 'string'
              ? parsedSettings.customPersonaInstructions
              : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
        };
        // If the stored string doesn't exactly match the fully formed settings, update localStorage
        // This helps in migrating old settings or correcting partially formed ones.
        if (storedSettingsStr !== JSON.stringify(fullSettings)) {
            localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(fullSettings));
        }
      } else {
        // If no settings are found in localStorage, initialize with defaults
        fullSettings = DEFAULT_KAREN_SETTINGS;
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      }
      setSelectedVoiceURI(fullSettings.ttsVoiceURI);
    } catch (error) {
      setSelectedVoiceURI(DEFAULT_KAREN_SETTINGS.ttsVoiceURI);
      // Attempt to ensure localStorage is initialized with defaults if an error occurred
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch (lsError) {
      }
    }
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

    } catch (error) {
      toast({
        title: "Error Saving Voice Settings",
        description: "Could not save voice preferences. localStorage might be disabled or full.",
        variant: "destructive",

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

    } catch (error) {
       toast({
          title: "Error Resetting Voice Settings",
          description: "Could not reset voice preferences.",
          variant: "destructive",

    }
  };
  if (typeof window !== 'undefined' && !window.speechSynthesis) {
    return (
      <Card variant="elevated">
        <CardHeader>
          <CardTitle className="text-lg">Text-to-Speech Voice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4 " />
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
    <Card variant="elevated" className="interactive">
      <CardHeader>
        <CardTitle className="text-lg">Text-to-Speech Voice</CardTitle>
        <CardDescription>
          Choose a preferred voice for Karen AI's spoken responses. Availability depends on your browser and operating system.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="divide-y divide-border">
            <div className="px-6 py-4">
                {isLoadingVoices && (
                <div className="flex items-center space-x-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin " />
                    <span>Loading available voices...</span>
                </div>
                )}
                {!isLoadingVoices && availableVoices.length === 0 && (
                <Alert variant="default" className="bg-muted/30">
                    <AlertCircle className="h-4 w-4 !text-accent-foreground " />
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
                    <select
                    value={selectedVoiceURI || DEFAULT_VOICE_SENTINEL} 
                    onValueChange={(value) = aria-label="Select option"> setSelectedVoiceURI(value === DEFAULT_VOICE_SENTINEL ? null : value)}
                    disabled={availableVoices.length === 0 || isLoadingVoices}
                    >
                    <selectTrigger id="tts-voice" aria-label="Select option">
                        <selectValue placeholder="Default system voice" />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                        <selectItem value={DEFAULT_VOICE_SENTINEL} aria-label="Select option">Default system voice</SelectItem>
                        {availableVoices.map((voice, index) => (
                        <selectItem
                            key={`voice-option-${voice.voiceURI}-${index}`} // Ensures unique key
                            value={voice.voiceURI} // Value should still be voice.voiceURI
                         aria-label="Select option">
                            {voice.name} ({voice.lang}) {voice.default ? "[System Default]" : ""}
                        </SelectItem>
                        ))}
                    </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    If no voice is selected, or the selected voice is unavailable, the browser's default will be used.
                    </p>
                </div>
                )}
            </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
          <Button variant="outline" onClick={resetToDefaults} >Reset to Default</Button>
          <Button onClick={saveSettings} >Save Settings</Button>
      </CardFooter>
    </Card>
  );
}
