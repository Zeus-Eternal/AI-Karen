"use client";
import { useState, useEffect, FormEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Trash2, PlusCircle, Info, ThumbsUp, XCircle, MessageSquarePlus } from 'lucide-react';
import type { KarenSettings } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS, KAREN_SUGGESTED_FACTS_LS_KEY } from '@/lib/constants';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
/**
 * @file PersonalFactsSettings.tsx
 * @description Component for managing personal facts that Karen AI should remember.
 * Allows users to add, view, and delete manually entered facts.
 * Also allows users to review, confirm, or dismiss facts dynamically suggested by Karen AI during conversations.
 * Facts are stored in local storage.
 */
export default function PersonalFactsSettings() {
  const [personalFacts, setPersonalFacts] = useState<string[]>(DEFAULT_KAREN_SETTINGS.personalFacts);
  const [newFact, setNewFact] = useState('');
  const [suggestedFactsForReview, setSuggestedFactsForReview] = useState<string[]>([]);
  const { toast } = useToast();
  useEffect(() => {
    // Load manually managed personal facts
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
          temperatureUnit: parsedSettings.temperatureUnit || DEFAULT_KAREN_SETTINGS.temperatureUnit,
          weatherService: parsedSettings.weatherService || DEFAULT_KAREN_SETTINGS.weatherService,
          weatherApiKey: parsedSettings.weatherApiKey === undefined ? DEFAULT_KAREN_SETTINGS.weatherApiKey : parsedSettings.weatherApiKey,
          defaultWeatherLocation: parsedSettings.defaultWeatherLocation === undefined ? DEFAULT_KAREN_SETTINGS.defaultWeatherLocation : parsedSettings.defaultWeatherLocation,
        };
         if (storedSettingsStr !== JSON.stringify(fullSettings)) {
            localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(fullSettings));
        }
      } else {
        fullSettings = DEFAULT_KAREN_SETTINGS;
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      }
      setPersonalFacts(fullSettings.personalFacts || []);
    } catch (error) {
      setPersonalFacts(DEFAULT_KAREN_SETTINGS.personalFacts);
      try {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(DEFAULT_KAREN_SETTINGS));
      } catch (lsError) {
      }
    }
    // Load suggested facts for review
    try {
      const storedSuggestedFacts = localStorage.getItem(KAREN_SUGGESTED_FACTS_LS_KEY);
      if (storedSuggestedFacts) {
        setSuggestedFactsForReview(JSON.parse(storedSuggestedFacts));
      }
    } catch (error) {
      setSuggestedFactsForReview([]);
    }
  }, []);
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
          ttsVoiceURI: parsed.ttsVoiceURI === undefined ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI : parsed.ttsVoiceURI,
          customPersonaInstructions: typeof parsed.customPersonaInstructions === 'string' ? parsed.customPersonaInstructions : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
          memoryDepth: parsed.memoryDepth || DEFAULT_KAREN_SETTINGS.memoryDepth,
          personalityTone: parsed.personalityTone || DEFAULT_KAREN_SETTINGS.personalityTone,
          personalityVerbosity: parsed.personalityVerbosity || DEFAULT_KAREN_SETTINGS.personalityVerbosity,
          activeListenMode: typeof parsed.activeListenMode === 'boolean' ? parsed.activeListenMode : DEFAULT_KAREN_SETTINGS.activeListenMode,
          temperatureUnit: parsed.temperatureUnit || DEFAULT_KAREN_SETTINGS.temperatureUnit,
          weatherService: parsed.weatherService || DEFAULT_KAREN_SETTINGS.weatherService,
          weatherApiKey: parsed.weatherApiKey === undefined ? DEFAULT_KAREN_SETTINGS.weatherApiKey : parsed.weatherApiKey,
          defaultWeatherLocation: parsed.defaultWeatherLocation === undefined ? DEFAULT_KAREN_SETTINGS.defaultWeatherLocation : parsed.defaultWeatherLocation,
        };
      }
    } catch (e) {
    }
    return currentFullSettings;
  };
  const saveMainPersonalFactsToLocalStorage = (updatedFacts: string[]) => {
    try {
      const currentSettings = getFullCurrentSettingsFromStorage();
      const newSettings: KarenSettings = { ...currentSettings, personalFacts: updatedFacts };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newSettings));
      setPersonalFacts(updatedFacts);
    } catch (error) {
      toast({
          title: "Error Saving Facts",
          description: "Could not save personal facts. localStorage might be disabled or full.",
          variant: "destructive",
        });
    }
  };
  const saveSuggestedFactsToLocalStorage = (updatedSuggestedFacts: string[]) => {
    try {
      localStorage.setItem(KAREN_SUGGESTED_FACTS_LS_KEY, JSON.stringify(updatedSuggestedFacts));
      setSuggestedFactsForReview(updatedSuggestedFacts);
      window.dispatchEvent(new CustomEvent('karen-suggested-facts-updated')); // Notify other components
    } catch (error) {
      toast({
        title: "Error Updating Suggested Facts",
        description: "Could not update the list of suggested facts.",
        variant: "destructive",
      });
    }
  };
  const handleAddFact = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (newFact.trim()) {
      const updatedFacts = [...personalFacts, newFact.trim()];
      saveMainPersonalFactsToLocalStorage(updatedFacts);
      setNewFact('');
      toast({
        title: "Fact Added",
        description: "Karen will now remember this new fact.",
      });
    }
  };
  const handleDeleteFact = (indexToDelete: number) => {
    const updatedFacts = personalFacts.filter((_, index) => index !== indexToDelete);
    saveMainPersonalFactsToLocalStorage(updatedFacts);
    toast({
      title: "Fact Deleted",
      description: "Karen will no longer remember this fact.",
    });
  };
  const handleClearAllFacts = () => {
    saveMainPersonalFactsToLocalStorage([]);
     toast({
        title: "All Manually Added Facts Cleared",
        description: "Karen has forgotten all facts you've manually added.",
      });
  };
  const handleConfirmSuggestedFact = (factToConfirm: string) => {
    if (!personalFacts.includes(factToConfirm)) {
      const updatedMainFacts = [...personalFacts, factToConfirm];
      saveMainPersonalFactsToLocalStorage(updatedMainFacts);
    }
    const updatedSuggestedFacts = suggestedFactsForReview.filter(fact => fact !== factToConfirm);
    saveSuggestedFactsToLocalStorage(updatedSuggestedFacts);
    toast({
      title: "Fact Confirmed & Saved",
      description: `"${factToConfirm.substring(0,30)}..." is now part of Karen's long-term knowledge.`,
    });
  };
  const handleDismissSuggestedFact = (factToDismiss: string) => {
    const updatedSuggestedFacts = suggestedFactsForReview.filter(fact => fact !== factToDismiss);
    saveSuggestedFactsToLocalStorage(updatedSuggestedFacts);
     toast({
      title: "Suggestion Dismissed",
      description: `Suggestion "${factToDismiss.substring(0,30)}..." was dismissed from review.`,
    });
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Karen's Personal Knowledge Base</CardTitle>
        <CardDescription>
          Manage facts Karen remembers. Add your own, or review what Karen has learned from conversations.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-base font-semibold mb-2">My Saved Facts for Karen</h3>
          <p className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            These are facts you've explicitly told Karen to remember. She will use these to personalize interactions.
          </p>
          <form onSubmit={handleAddFact} className="space-y-2 mb-4">
            <Label htmlFor="newFact">Add a new fact for Karen</Label>
            <div className="flex space-x-2">
              <input
                id="newFact"
                type="text"
                value={newFact}
                onChange={(e) = aria-label="Input"> setNewFact(e.target.value)}
                placeholder="e.g., My favorite color is blue"
                className="text-sm md:text-base lg:text-lg"
              />
              <Button type="submit" size="icon" aria-label="Add fact" disabled={!newFact.trim()}>
                <PlusCircle className="h-5 w-5 sm:w-auto md:w-full" />
              </Button>
            </div>
          </form>
          {personalFacts.length > 0 ? (
            <div className="space-y-3">
              <ScrollArea className="h-[150px] w-full rounded-md border p-3 bg-muted/50 sm:p-4 md:p-6">
                <ul className="space-y-2">
                  {personalFacts.map((fact, index) => (
                    <li key={index} className="flex justify-between items-center text-sm p-2 rounded-md bg-background hover:bg-accent/50 group md:text-base lg:text-lg">
                      <span className="truncate pr-2">{fact}</span>
                      <button
                        variant="ghost"
                        size="icon"
                        onClick={() = aria-label="Button"> handleDeleteFact(index)}
                        className="h-6 w-6 opacity-50 group-hover:opacity-100 text-muted-foreground hover:text-destructive sm:w-auto md:w-full"
                        aria-label="Delete fact"
                      >
                        <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />
                      </Button>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </div>
          ) : (
             <Alert variant="default" className="bg-muted/30">
              <Info className="h-4 w-4 !text-accent-foreground sm:w-auto md:w-full" />
              <AlertTitle className="font-semibold text-accent-foreground text-sm md:text-base lg:text-lg">No Saved Facts Yet</AlertTitle>
              <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
                Teach Karen something new using the input above!
              </AlertDescription>
            </Alert>
          )}
        </div>
        {personalFacts.length > 0 && (
            <div className="flex justify-end">
                 <button variant="outline" size="sm" onClick={handleClearAllFacts} aria-label="Button">
                    <Trash2 className="mr-1.5 h-3.5 w-3.5 sm:w-auto md:w-full" /> Clear All Saved Facts
                </Button>
            </div>
        )}
        <Separator />
        <div className="space-y-3">
            <h3 className="text-base font-semibold mb-2 flex items-center">
                <MessageSquarePlus className="h-5 w-5 mr-2 text-primary/80 sm:w-auto md:w-full" />
                Karen's Suggested Facts (For Your Review)
            </h3>
            <p className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
              During conversations, Karen might identify new information about you. Review her suggestions here and decide if you want her to remember them long-term.
            </p>
            {suggestedFactsForReview.length > 0 ? (
                <ScrollArea className="h-[150px] w-full rounded-md border p-3 bg-muted/50 sm:p-4 md:p-6">
                <ul className="space-y-2">
                    {suggestedFactsForReview.map((fact, index) => (
                    <li key={`suggested-${index}-${fact.slice(0,10)}`} className="flex justify-between items-center text-sm p-2 rounded-md bg-background group md:text-base lg:text-lg">
                        <span className="truncate pr-2 flex-1">{fact}</span>
                        <div className="flex space-x-1 shrink-0">
                        <button
                            variant="outline"
                            size="sm" // Made button slightly larger for easier clicking
                            onClick={() = aria-label="Button"> handleConfirmSuggestedFact(fact)}
                            className="border-green-500/50 hover:bg-green-500/10 text-green-600 hover:text-green-700 px-2 py-1 h-auto"
                            aria-label="Confirm and save fact"
                        >
                            <ThumbsUp className="h-3.5 w-3.5 mr-1 sm:w-auto md:w-full" /> Save
                        </Button>
                        <button
                            variant="outline"
                            size="sm" // Made button slightly larger
                            onClick={() = aria-label="Button"> handleDismissSuggestedFact(fact)}
                            className="border-red-500/50 hover:bg-red-500/10 text-red-600 hover:text-red-700 px-2 py-1 h-auto"
                            aria-label="Dismiss suggestion"
                        >
                            <XCircle className="h-3.5 w-3.5 mr-1 sm:w-auto md:w-full" /> Dismiss
                        </Button>
                        </div>
                    </li>
                    ))}
                </ul>
                </ScrollArea>
            ) : (
                <Alert variant="default" className="bg-muted/30">
                    <Info className="h-4 w-4 !text-accent-foreground sm:w-auto md:w-full" />
                    <AlertTitle className="font-semibold text-accent-foreground text-sm md:text-base lg:text-lg">No New Suggestions</AlertTitle>
                    <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
                    Karen hasn't suggested any new facts to remember from recent conversations. As you chat, new suggestions may appear here.
                    </AlertDescription>
                </Alert>
            )}
        </div>
      </CardContent>
      {/* CardFooter for global actions on this page might not be needed if "Clear All" is specific to manual facts */}
    </Card>
  );
}
