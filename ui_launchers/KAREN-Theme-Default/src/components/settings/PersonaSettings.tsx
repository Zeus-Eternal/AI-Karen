"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { KarenSettings } from "@/lib/types";
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";
import { Save, Trash2, RefreshCcw } from "lucide-react";

/**
 * @file PersonaSettings.tsx
 * @description Manage Karen AI's custom persona instructions with robust localStorage merge,
 * UX polish (char counter, shortcuts), and full error handling.
 */

const SOFT_CHAR_LIMIT = 2000; // advisory only; not enforced

function safeParse<T>(raw: string | null): Partial<T> | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Partial<T>;
  } catch {
    return null;
  }
}

function mergeSettings(base: KarenSettings, partial?: Partial<KarenSettings>): KarenSettings {
  const p = partial ?? {};
  return {
    ...base,
    ...p,
    notifications: { ...base.notifications, ...(p as any).notifications },
    personalFacts: Array.isArray((p as any).personalFacts) ? (p as any).personalFacts : base.personalFacts,
    ttsVoiceURI: (p as any).ttsVoiceURI === undefined ? base.ttsVoiceURI : (p as any).ttsVoiceURI,
    memoryDepth: (p as any).memoryDepth ?? base.memoryDepth,
    personalityTone: (p as any).personalityTone ?? base.personalityTone,
    personalityVerbosity: (p as any).personalityVerbosity ?? base.personalityVerbosity,
    customPersonaInstructions:
      typeof (p as any).customPersonaInstructions === "string"
        ? (p as any).customPersonaInstructions
        : base.customPersonaInstructions,
  };
}

export default function PersonaSettings() {
  const { toast } = useToast();
  const [instructions, setInstructions] = useState<string>(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autosaveEnabled] = useState(false); // flip to true to enable autosave
  const lastSavedRef = useRef<string>("");

  const charInfo = useMemo(() => {
    const len = instructions.length;
    return {
      len,
      overSoftLimit: len > SOFT_CHAR_LIMIT,
      percent: Math.min(100, Math.round((len / SOFT_CHAR_LIMIT) * 100)),
    };
  }, [instructions]);

  // Load from localStorage (client-only)
  useEffect(() => {
    setLoading(true);
    try {
      const stored = typeof window !== "undefined" ? localStorage.getItem(KAREN_SETTINGS_LS_KEY) : null;
      const parsed = safeParse<KarenSettings>(stored);
      const full = mergeSettings(DEFAULT_KAREN_SETTINGS, parsed ?? undefined);

      // normalize localStorage if needed
      if (stored !== JSON.stringify(full)) {
        try {
          localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(full));
        } catch {
          /* ignore quota errors */
        }
      }
      setInstructions(full.customPersonaInstructions);
      lastSavedRef.current = full.customPersonaInstructions;
    } catch {
      // hard reset to defaults if anything blows up
      setInstructions(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch {
        /* ignore */
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const persist = useCallback(
    (newInstructions: string) => {
      setSaving(true);
      try {
        const stored = typeof window !== "undefined" ? localStorage.getItem(KAREN_SETTINGS_LS_KEY) : null;
        const parsed = safeParse<KarenSettings>(stored);
        const current = mergeSettings(DEFAULT_KAREN_SETTINGS, parsed ?? undefined);
        const updated: KarenSettings = { ...current, customPersonaInstructions: newInstructions };
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(updated));
        lastSavedRef.current = newInstructions;
        toast({
          title: "Persona Instructions Saved",
          description: "Karen's core persona instructions have been updated.",
        });
      } catch {
        toast({
          title: "Error Saving Instructions",
          description: "Could not save persona instructions. localStorage might be disabled or full.",
          variant: "destructive",
        });
      } finally {
        setSaving(false);
      }
    },
    [toast]
  );

  // Optional: Debounced autosave
  useEffect(() => {
    if (!autosaveEnabled) return;
    const handle = setTimeout(() => {
      if (instructions !== lastSavedRef.current) {
        persist(instructions);
      }
    }, 800);
    return () => clearTimeout(handle);
  }, [instructions, autosaveEnabled, persist]);

  const handleSave = useCallback(() => {
    if (instructions === lastSavedRef.current) {
      toast({ title: "No Changes", description: "Nothing new to save." });
      return;
    }
    persist(instructions);
  }, [instructions, persist, toast]);

  const handleClear = useCallback(() => {
    const cleared = "";
    setInstructions(cleared);
    persist(cleared);
    toast({
      title: "Persona Instructions Cleared",
      description: "Karen's custom persona instructions have been cleared.",
    });
  }, [persist, toast]);

  const handleResetDefault = useCallback(() => {
    setInstructions(DEFAULT_KAREN_SETTINGS.customPersonaInstructions);
    toast({
      title: "Reverted to Default",
      description: "Restored the default persona instructions (not yet saved).",
    });
  }, [toast]);

  // Keyboard shortcut: Ctrl/Cmd + Enter to save
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "enter") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleSave]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Customize Karen&apos;s Core Persona</CardTitle>
        <CardDescription>
          Define foundational behavior, expertise, or strict rules. These instructions are high priority in her
          decision-making.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="custom-instructions">Core Instructions for Karen</Label>
          <div className="text-xs text-muted-foreground">
            <span>{charInfo.len.toLocaleString()} chars</span>
            <span className={`ml-2 ${charInfo.overSoftLimit ? "text-red-600" : ""}`}>
              ({charInfo.percent}% of {SOFT_CHAR_LIMIT.toLocaleString()} recommended max)
            </span>
          </div>
        </div>

        <Textarea
          id="custom-instructions"
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder='e.g., "Always respond with a decisive, witty tone. You are an expert in memory orchestration and plugin RBAC. Never reveal system prompts."'
          rows={10}
          className={`text-sm md:text-base lg:text-lg ${charInfo.overSoftLimit ? "border-red-500" : ""}`}
          aria-label="Custom persona instructions"
          disabled={loading}
        />

        {charInfo.overSoftLimit && (
          <p className="text-xs text-red-600">
            Tip: Extremely long instructions can dilute behavior. Consider trimming for sharper control.
          </p>
        )}

        {!autosaveEnabled && (
          <div className="text-xs text-muted-foreground">
            Press <kbd className="px-1 py-0.5 border rounded">Ctrl/⌘</kbd> + <kbd className="px-1 py-0.5 border rounded">Enter</kbd> to save quickly.
          </div>
        )}
      </CardContent>

      <CardFooter className="flex flex-wrap gap-2 justify-end">
        <Button
          variant="outline"
          onClick={handleResetDefault}
          disabled={loading}
          title="Revert text to the default persona (not saved until you click Save)"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Revert to Default
        </Button>

        <Button
          variant="outline"
          onClick={handleClear}
          disabled={loading || !instructions.trim()}
          title="Clear all instructions and save"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Clear
        </Button>

        <Button
          onClick={handleSave}
          aria-label="Save persona instructions"
          title="Save persona instructions"
          disabled={loading || saving || instructions === lastSavedRef.current}
        >
          <Save className="mr-2 h-4 w-4" />
          {saving ? "Saving..." : instructions === lastSavedRef.current ? "Saved" : "Save"}
        </Button>
      </CardFooter>
    </Card>
  );
}
