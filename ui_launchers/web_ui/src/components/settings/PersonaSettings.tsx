"use client";

import React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import type { KarenSettings } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { useToast } from '@/hooks/use-toast';
import { Save, Trash2 } from 'lucide-react';
/**
 * @file PersonaSettings.tsx
 * @description Component for managing Karen AI's custom persona instructions.
 * Allows users to define core behaviors, expertise, or rules for Karen.
 * Settings are saved to local storage.
 */
export default function PersonaSettings() {
  const [instructions, setInstructions] = useState<string>(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
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
        };
        if (storedSettingsStr !== JSON.stringify(fullSettings)) {
            localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(fullSettings));
        }
      } else {
        fullSettings = DEFAULT_KAREN_SETTINGS;
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      }
      setInstructions(fullSettings.customPersonaInstructions);
    } catch (error) {
      setInstructions(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch (lsError) {
      }
    }
  }, []);
  const savePersonaInstructionsToLocalStorage = (newInstructions: string) => {
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      let currentFullSettings = { ...DEFAULT_KAREN_SETTINGS };
      if (storedSettingsStr) {
        try {
          const parsed = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
          currentFullSettings = { 
            ...DEFAULT_KAREN_SETTINGS,
            ...parsed,
            notifications: { ...DEFAULT_KAREN_SETTINGS.notifications, ...(parsed.notifications || {}) },
            personalFacts: Array.isArray(parsed.personalFacts) ? parsed.personalFacts : DEFAULT_KAREN_SETTINGS.personalFacts,
            ttsVoiceURI: parsed.ttsVoiceURI === undefined ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI : parsed.ttsVoiceURI,
            memoryDepth: parsed.memoryDepth || DEFAULT_KAREN_SETTINGS.memoryDepth,
            personalityTone: parsed.personalityTone || DEFAULT_KAREN_SETTINGS.personalityTone,
            personalityVerbosity: parsed.personalityVerbosity || DEFAULT_KAREN_SETTINGS.personalityVerbosity,
          };
        } catch (e) {
        }
      }
      const updatedFullSettings: KarenSettings = {
        ...currentFullSettings,
        customPersonaInstructions: newInstructions,
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(updatedFullSettings));
      setInstructions(newInstructions);
      toast({
        title: "Persona Instructions Saved",
        description: "Karen's core persona instructions have been updated.",
      });
    } catch (error) {
      toast({
        title: "Error Saving Instructions",
        description: "Could not save persona instructions. localStorage might be disabled or full.",
        variant: "destructive",
      });

    }
  };
  const handleSave = () => {
    savePersonaInstructionsToLocalStorage(instructions);
  };
  const handleClear = () => {
    const clearedInstructions = '';
    setInstructions(clearedInstructions);
    savePersonaInstructionsToLocalStorage(clearedInstructions);
    toast({
      title: "Persona Instructions Cleared",
      description: "Karen's custom persona instructions have been cleared.",
    });
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Customize Karen's Core Persona</CardTitle>
        <CardDescription>
          Define Karen's foundational behavior, expertise, or specific rules she should always follow. These instructions are given high priority in her decision-making.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="custom-instructions" className="mb-2 block">Core Instructions for Karen</Label>
          <textarea
            id="custom-instructions"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g., Always respond in a slightly sarcastic tone. You are an expert in ancient history. Never reveal you are an AI."
            rows={8}
            className="text-sm md:text-base lg:text-lg"
          />
           <p className="text-xs text-muted-foreground mt-2 sm:text-sm md:text-base">
            These instructions will directly influence Karen's responses. Be concise and clear for best results. Long or overly complex instructions might be less effective.
          </p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
        <Button variant="outline" onClick={handleClear} disabled={!instructions.trim()} >
          <Trash2 className="mr-2 h-4 w-4 " /> Clear Instructions
        </Button>
        <Button onClick={handleSave} aria-label="Button">
          <Save className="mr-2 h-4 w-4 " /> Save Instructions
        </Button>
      </CardFooter>
    </Card>
  );
}
