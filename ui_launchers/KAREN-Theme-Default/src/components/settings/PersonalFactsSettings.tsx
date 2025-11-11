"use client";

import React, { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, PlusCircle, Info, ThumbsUp, XCircle, MessageSquarePlus } from "lucide-react";
import type { KarenSettings } from "@/lib/types";
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS, KAREN_SUGGESTED_FACTS_LS_KEY } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";

/**
 * @file PersonalFactsSettings.tsx
 * @description Manage personal facts Karen should remember + review AI-suggested facts.
 * Fully localStorage-driven with resilient parsing and merge logic.
 */

const MAX_FACT_LEN = 512;

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
    notifications: { ...base.notifications, ...(p as unknown).notifications },
    personalFacts: Array.isArray((p as unknown).personalFacts) ? (p as unknown).personalFacts : base.personalFacts,
    ttsVoiceURI: (p as unknown).ttsVoiceURI === undefined ? base.ttsVoiceURI : (p as unknown).ttsVoiceURI,
    customPersonaInstructions:
      typeof (p as unknown).customPersonaInstructions === "string"
        ? (p as unknown).customPersonaInstructions
        : base.customPersonaInstructions,
    memoryDepth: (p as unknown).memoryDepth ?? base.memoryDepth,
    personalityTone: (p as unknown).personalityTone ?? base.personalityTone,
    personalityVerbosity: (p as unknown).personalityVerbosity ?? base.personalityVerbosity,
    activeListenMode: typeof (p as unknown).activeListenMode === "boolean" ? (p as unknown).activeListenMode : base.activeListenMode,
    temperatureUnit: (p as unknown).temperatureUnit ?? base.temperatureUnit,
    weatherService: (p as unknown).weatherService ?? base.weatherService,
    weatherApiKey: (p as unknown).weatherApiKey === undefined ? base.weatherApiKey : (p as unknown).weatherApiKey,
    defaultWeatherLocation:
      (p as unknown).defaultWeatherLocation === undefined ? base.defaultWeatherLocation : (p as unknown).defaultWeatherLocation,
  };
}

export default function PersonalFactsSettings() {
  const { toast } = useToast();
  const [personalFacts, setPersonalFacts] = useState<string[]>(DEFAULT_KAREN_SETTINGS.personalFacts);
  const [newFact, setNewFact] = useState("");
  const [suggestedFactsForReview, setSuggestedFactsForReview] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Initial load: merge + normalize settings & suggested facts
  useEffect(() => {
    setLoading(true);
    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      const parsedSettings = safeParse<KarenSettings>(storedSettingsStr);
      const fullSettings = mergeSettings(DEFAULT_KAREN_SETTINGS, parsedSettings ?? undefined);

      if (storedSettingsStr !== JSON.stringify(fullSettings)) {
        try {
          localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(fullSettings));
        } catch {
          /* ignore quota issues */
        }
      }
      setPersonalFacts(fullSettings.personalFacts || []);
    } catch {
      setPersonalFacts(DEFAULT_KAREN_SETTINGS.personalFacts);
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch {
        /* ignore */
      }
    }

    try {
      const storedSuggestedFacts = localStorage.getItem(KAREN_SUGGESTED_FACTS_LS_KEY);
      const parsed = safeParse<string[]>(storedSuggestedFacts);
      setSuggestedFactsForReview(Array.isArray(parsed) ? (parsed as string[]) : []);
    } catch {
      setSuggestedFactsForReview([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const getFullCurrentSettingsFromStorage = useCallback((): KarenSettings => {
    const stored = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
    const parsed = safeParse<KarenSettings>(stored);
    return mergeSettings(DEFAULT_KAREN_SETTINGS, parsed ?? undefined);
  }, []);

  const saveMainPersonalFactsToLocalStorage = useCallback(
    (updatedFacts: string[]) => {
      try {
        const currentSettings = getFullCurrentSettingsFromStorage();
        const newSettings: KarenSettings = { ...currentSettings, personalFacts: updatedFacts };
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newSettings));
        setPersonalFacts(updatedFacts);
      } catch {
        toast({
          title: "Error Saving Facts",
          description: "Could not save personal facts. localStorage might be disabled or full.",
          variant: "destructive",
        });
      }
    },
    [getFullCurrentSettingsFromStorage, toast]
  );

  const saveSuggestedFactsToLocalStorage = useCallback(
    (updatedSuggestedFacts: string[]) => {
      try {
        localStorage.setItem(KAREN_SUGGESTED_FACTS_LS_KEY, JSON.stringify(updatedSuggestedFacts));
        setSuggestedFactsForReview(updatedSuggestedFacts);
        window.dispatchEvent(new CustomEvent("karen-suggested-facts-updated"));
      } catch {
        toast({
          title: "Error Updating Suggested Facts",
          description: "Could not update the list of suggested facts.",
          variant: "destructive",
        });
      }
    },
    [toast]
  );

  const sanitizedNewFact = useMemo(() => newFact.trim().slice(0, MAX_FACT_LEN), [newFact]);

  const handleAddFact = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const value = sanitizedNewFact;
    if (!value) return;

    const deduped = Array.from(new Set([...personalFacts, value]));
    saveMainPersonalFactsToLocalStorage(deduped);
    setNewFact("");
    toast({ title: "Fact Added", description: "Karen will now remember this fact." });
  };

  const handleDeleteFact = (indexToDelete: number) => {
    const updatedFacts = personalFacts.filter((_, index) => index !== indexToDelete);
    saveMainPersonalFactsToLocalStorage(updatedFacts);
    toast({ title: "Fact Deleted", description: "Karen will no longer remember this fact." });
  };

  const handleClearAllFacts = () => {
    saveMainPersonalFactsToLocalStorage([]);
    toast({
      title: "All Manually Added Facts Cleared",
      description: "Karen has forgotten all facts you've manually added.",
    });
  };

  const handleConfirmSuggestedFact = (factToConfirm: string) => {
    const trimmed = factToConfirm.trim().slice(0, MAX_FACT_LEN);
    const updatedMainFacts = Array.from(new Set([...personalFacts, trimmed]));
    saveMainPersonalFactsToLocalStorage(updatedMainFacts);

    const updatedSuggestedFacts = suggestedFactsForReview.filter((f) => f !== factToConfirm);
    saveSuggestedFactsToLocalStorage(updatedSuggestedFacts);

    toast({
      title: "Fact Confirmed & Saved",
      description: `"${trimmed.substring(0, 30)}..." is now part of Karen's long-term knowledge.`,
    });
  };

  const handleDismissSuggestedFact = (factToDismiss: string) => {
    const updatedSuggestedFacts = suggestedFactsForReview.filter((f) => f !== factToDismiss);
    saveSuggestedFactsToLocalStorage(updatedSuggestedFacts);
    toast({
      title: "Suggestion Dismissed",
      description: `Suggestion "${factToDismiss.substring(0, 30)}..." was dismissed from review.`,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Karen&apos;s Personal Knowledge Base</CardTitle>
        <CardDescription>
          Manage facts Karen remembers. Add your own, or review what Karen has learned from conversations.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Manual facts */}
        <div>
          <h3 className="text-base font-semibold mb-2">My Saved Facts for Karen</h3>
          <p className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            These are facts you&apos;ve explicitly told Karen to remember. She will use these to personalize interactions.
          </p>

          <form onSubmit={handleAddFact} className="space-y-2 mb-4">
            <Label htmlFor="newFact">Add a new fact for Karen</Label>
            <div className="flex gap-2">
              <Input
                id="newFact"
                type="text"
                value={newFact}
                onChange={(e) => setNewFact(e.target.value)}
                placeholder="e.g., My favorite color is blue"
                className="text-sm md:text-base lg:text-lg"
                maxLength={MAX_FACT_LEN}
                disabled={loading}
                aria-label="New personal fact"
              />
              <Button type="submit" size="icon" aria-label="Add fact" title="Add fact" disabled={!sanitizedNewFact || loading}>
                <PlusCircle className="h-5 w-5" />
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              {sanitizedNewFact.length}/{MAX_FACT_LEN}
            </div>
          </form>

          {personalFacts.length > 0 ? (
            <div className="space-y-3">
              <ScrollArea className="h-[150px] w-full rounded-md border p-3 bg-muted/50 sm:p-4 md:p-6">
                <ul className="space-y-2">
                  {personalFacts.map((fact, index) => (
                    <li
                      key={`pf-${index}-${fact.slice(0, 16)}`}
                      className="flex justify-between items-center text-sm p-2 rounded-md bg-background hover:bg-accent/50 group md:text-base lg:text-lg"
                    >
                      <span className="truncate pr-2">{fact}</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteFact(index)}
                        className="h-6 w-6 opacity-50 group-hover:opacity-100 text-muted-foreground hover:text-destructive"
                        aria-label="Delete fact"
                        title="Delete fact"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </div>
          ) : (
            <Alert variant="default" className="bg-muted/30">
              <Info className="h-4 w-4 !text-accent-foreground" />
              <AlertTitle className="font-semibold text-accent-foreground text-sm md:text-base lg:text-lg">
                No Saved Facts Yet
              </AlertTitle>
              <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
                Teach Karen something new using the input above!
              </AlertDescription>
            </Alert>
          )}
        </div>

        {personalFacts.length > 0 && (
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={handleClearAllFacts} title="Clear all saved facts" disabled={loading}>
              <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Clear All Saved Facts
            </Button>
          </div>
        )}

        <Separator />

        {/* Suggested facts */}
        <div className="space-y-3">
          <h3 className="text-base font-semibold mb-2 flex items-center">
            <MessageSquarePlus className="h-5 w-5 mr-2 text-primary/80" />
            Karen&apos;s Suggested Facts (For Your Review)
          </h3>
          <p className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            During conversations, Karen might identify new information about you. Review her suggestions here and decide
            if you want her to remember them long-term.
          </p>

          {suggestedFactsForReview.length > 0 ? (
            <ScrollArea className="h-[150px] w-full rounded-md border p-3 bg-muted/50 sm:p-4 md:p-6">
              <ul className="space-y-2">
                {suggestedFactsForReview.map((fact, index) => (
                  <li
                    key={`sf-${index}-${fact.slice(0, 16)}`}
                    className="flex justify-between items-center text-sm p-2 rounded-md bg-background group md:text-base lg:text-lg"
                  >
                    <span className="truncate pr-2 flex-1">{fact}</span>
                    <div className="flex gap-1 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleConfirmSuggestedFact(fact)}
                        className="border-green-500/50 hover:bg-green-500/10 text-green-600 hover:text-green-700 px-2 py-1 h-auto"
                        aria-label="Confirm and save fact"
                        title="Confirm and save fact"
                        disabled={loading}
                      >
                        <ThumbsUp className="h-3.5 w-3.5 mr-1" /> Save
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDismissSuggestedFact(fact)}
                        className="border-red-500/50 hover:bg-red-500/10 text-red-600 hover:text-red-700 px-2 py-1 h-auto"
                        aria-label="Dismiss suggestion"
                        title="Dismiss suggestion"
                        disabled={loading}
                      >
                        <XCircle className="h-3.5 w-3.5 mr-1" /> Dismiss
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </ScrollArea>
          ) : (
            <Alert variant="default" className="bg-muted/30">
              <Info className="h-4 w-4 !text-accent-foreground" />
              <AlertTitle className="font-semibold text-accent-foreground text-sm md:text-base lg:text-lg">
                No New Suggestions
              </AlertTitle>
              <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
                Karen hasn&apos;t suggested any new facts to remember from recent conversations. As you chat, new
                suggestions may appear here.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
