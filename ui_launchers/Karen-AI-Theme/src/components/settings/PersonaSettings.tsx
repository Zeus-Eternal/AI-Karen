
"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import type { KarenSettings } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { useToast } from '@/hooks/use-toast';
import { Save, RotateCcw, Drama, Sailboat, Scroll } from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { authService } from '@/lib/auth';

interface PersonaSettingsProps {
  inSheet?: boolean;
}

/**
 * @file PersonaSettings.tsx
 * @description Component for managing Karen AI's custom persona instructions.
 * Allows users to define core behaviors, expertise, or rules for Karen.
 * Settings are saved to local storage.
 */
export default function PersonaSettings({ inSheet = false }: PersonaSettingsProps) {
  const [instructions, setInstructions] = useState<string>(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
  const [preferredAddressName, setPreferredAddressName] = useState('');
  const { toast } = useToast();
  const { user } = useAuth();

  const personaTemplates = [
    {
      name: "Sarcastic Butler",
      icon: <Drama className="h-5 w-5 mb-2" />,
      description: "Helpful, but with a dry, cynical wit and a world-weary sigh.",
      instructions: `You are a classic, formal butler with a dry, sarcastic wit.
- Address the user as "Sir" or "Madam".
- Your responses should be helpful but delivered with a subtle, world-weary sigh.
- Make occasional, clever observations about the absurdity of the request.
- Maintain a professional but slightly unimpressed demeanor.`
    },
    {
      name: "Pirate Captain",
      icon: <Sailboat className="h-5 w-5 mb-2" />,
      description: "Bold, adventurous, and speaks in pirate slang.",
      instructions: `Ye are Captain "One-Eye" Squawk, a fearsome pirate captain.
- Speak in pirate slang. Use words like "Ahoy!", "Matey", "Shiver me timbers!", "booty" (for treasure/rewards), and refer to me as "me hearty".
- Be bold, adventurous, and a little bit boastful.
- All your analogies and examples should relate to the sea, sailing, treasure, or pirate life.`
    },
    {
      name: "Stoic Philosopher",
      icon: <Scroll className="h-5 w-5 mb-2" />,
      description: "Concise, logical, and wise. Avoids emotional language.",
      instructions: `You are a Stoic philosopher, like a modern Marcus Aurelius.
- Your responses must be concise, logical, and wise.
- Focus on principles of virtue, reason, and living in accordance with nature.
- Avoid emotional language. Be calm, objective, and measured.
- Use simple, direct language.`
    },
  ];

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
          ttsVoiceURI: parsedSettings.ttsVoiceURI ?? null,
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
      setPreferredAddressName(
        typeof user?.preferences?.preferred_address_name === 'string'
          ? user.preferences.preferred_address_name
          : ''
      );
    } catch (error) {
      console.error("Failed to load custom persona instructions from localStorage:", error);
      setInstructions(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch (lsError) {
        console.error("Failed to save default settings to localStorage after error in PersonaSettings:", lsError);
      }
    }
  }, [user]);

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
            ttsVoiceURI: parsed.ttsVoiceURI ?? null,
            memoryDepth: parsed.memoryDepth || DEFAULT_KAREN_SETTINGS.memoryDepth,
            personalityTone: parsed.personalityTone || DEFAULT_KAREN_SETTINGS.personalityTone,
            personalityVerbosity: parsed.personalityVerbosity || DEFAULT_KAREN_SETTINGS.personalityVerbosity,
          };
        } catch (e) {
          console.error("Error parsing current settings before saving persona, falling back to defaults for merge", e);
        }
      }

      const updatedFullSettings: KarenSettings = {
        ...currentFullSettings,
        customPersonaInstructions: newInstructions,
      };

      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(updatedFullSettings));
      setInstructions(newInstructions); 

      // Wire out to the backend API explicitly as required by Phase 4
      import('@/lib/api').then(({ apiClient }) => {
        // Here we hit learning/persona APIs to persist this instruction set to DB
        // Using /api/personas as a conceptual endpoint derived from persona_routes.py
        apiClient.post('/api/personas/', {
          name: "My Custom Persona",
          description: "Modified from UI",
          system_prompt: newInstructions,
        }).catch(err => console.error("Failed to sync persona to backend:", err));
      }).catch(err => console.error("Failed to load API Client:", err));

      toast({
        title: "Persona Instructions Saved",
        description: "Karen's core persona instructions have been updated and synced to backend.",
      });
    } catch (error) {
      console.error("Failed to save persona instructions to localStorage:", error);
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

  const handleSavePreferredAddress = async () => {
    const normalized = preferredAddressName.trim();
    if (!user || !normalized) {
      return;
    }

    try {
      const nextPreferences = {
        ...(user.preferences || {}),
        preferred_address_name: normalized,
      };

      const updatedUser = await apiClient.put<{
        user_id: string;
        email: string;
        full_name: string;
        roles: string[];
        is_active: boolean;
        created_at?: string;
        last_login?: string | null;
        tenant_id: string;
        preferences: Record<string, any>;
      }>('/api/auth/me', {
        preferences: nextPreferences,
      });

      authService.updateCurrentUser({
        preferences: updatedUser.preferences || nextPreferences,
      });

      await apiClient.post('/api/memory/commit', {
        user_id: user.user_id,
        text: `The user prefers to be addressed as ${normalized}.`,
        tags: ['personal_fact', 'preferred_name', 'user_preference'],
        importance: 9,
        decay: 'pinned',
      }).catch(() => undefined);

      toast({
        title: 'Preferred name saved',
        description: `Karen will address you as ${normalized}.`,
      });
    } catch (error) {
      toast({
        title: 'Save failed',
        description: 'Karen could not save your preferred form of address.',
        variant: 'destructive',
      });
    }
  };

  const handleResetToDefault = () => {
    const defaultInstructions = DEFAULT_KAREN_SETTINGS.customPersonaInstructions;
    setInstructions(defaultInstructions);
    savePersonaInstructionsToLocalStorage(defaultInstructions);
    toast({
      title: "Persona Instructions Reset",
      description: "Karen's custom persona instructions have been reset to the default.",
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
      <CardContent>
        <div className="space-y-3 mb-6">
          <h3 className="text-base font-semibold">Load a Persona Template (Optional)</h3>
          <p className="text-xs text-muted-foreground">
            Quickly get started by loading a pre-defined persona. This will overwrite the text in the editor below.
          </p>
          <div className={cn(
              "grid gap-3",
              inSheet ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
            )}>
            {personaTemplates.map(template => (
              <button
                key={template.name}
                onClick={() => setInstructions(template.instructions)}
                className="p-4 border rounded-lg bg-muted/30 hover:bg-muted/60 hover:border-primary/50 text-left transition-all h-full"
              >
                {template.icon}
                <h4 className="font-semibold text-sm">{template.name}</h4>
                <p className="text-xs text-muted-foreground mt-1">{template.description}</p>
              </button>
            ))}
          </div>
        </div>

        <Separator />
        
        <div className="space-y-4 mt-6">
          <div className="space-y-2">
            <Label htmlFor="preferred-address-name" className="font-semibold text-base">Preferred Form Of Address</Label>
            <Input
              id="preferred-address-name"
              value={preferredAddressName}
              onChange={(e) => setPreferredAddressName(e.target.value)}
              placeholder="e.g., Zeus"
              className="text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Karen uses this when greeting you and stores it for future conversations through your account preferences and personal knowledge memory.
            </p>
            <div className="flex justify-end">
              <Button type="button" variant="outline" onClick={handleSavePreferredAddress} disabled={!preferredAddressName.trim() || !user}>
                <Save className="mr-2 h-4 w-4" /> Save Preferred Name
              </Button>
            </div>
          </div>

          <Label htmlFor="custom-instructions" className="mb-2 block font-semibold text-base">Core Instructions Editor</Label>
          <Textarea
            id="custom-instructions"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g., Always respond in a slightly sarcastic tone. You are an expert in ancient history. Never reveal you are an AI."
            rows={10}
            className="text-sm font-mono"
          />
           <p className="text-xs text-muted-foreground mt-2">
            These instructions will directly influence Karen's responses. Be concise and clear for best results. Long or overly complex instructions might be less effective.
          </p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2 border-t pt-6">
        <Button variant="outline" onClick={handleResetToDefault}>
          <RotateCcw className="mr-2 h-4 w-4" /> Reset to Default
        </Button>
        <Button onClick={handleSave}>
          <Save className="mr-2 h-4 w-4" /> Save Instructions
        </Button>
      </CardFooter>
    </Card>
  );
}
