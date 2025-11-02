"use client";
import { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { CheckCircle2, ExternalLink, RotateCcw, AlertCircle, Info, Save, Copy } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Separator } from '@/components/ui/separator';
const LOCAL_STORAGE_KEY = 'googleApiKey';
/**
 * @file ApiKeyManager.tsx
 * @description Component for managing the Google AI API key.
 * Allows users to save their API key to the browser's local storage for convenience
 * and provides guidance on server-side configuration.
 */
export default function ApiKeyManager() {
  const [apiKey, setApiKey] = useState('');
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const { toast } = useToast();
  useEffect(() => {
    try {
      const storedKey = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (storedKey) {
        setApiKey(storedKey);
        setSavedKey(storedKey);
      }
    } catch (error) {
    }
  }, []);
  const handleSaveKey = () => {
    const keyToSave = (typeof apiKey === 'string' && apiKey) ? apiKey.trim() : "";
    if (keyToSave) {
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, keyToSave);
        setSavedKey(keyToSave);
        toast({
          title: "API Key Saved",
          description: "Your Google AI API key has been saved to your browser's local storage.",
        });
      } catch (error) {
        toast({
          title: "Error Saving API Key",
          description: "Could not save API key to browser storage. localStorage might be disabled or full.",
          variant: "destructive",
        });
      }
    }
  };
  const handleReloadFromStorage = () => {
    try {
      const storedKeyFromStorage = localStorage.getItem(LOCAL_STORAGE_KEY);
      const keyToLoad = storedKeyFromStorage || '';
      setApiKey(keyToLoad);
      setSavedKey(storedKeyFromStorage);
      if (storedKeyFromStorage !== null) {
        toast({
          title: "API Key Reloaded",
          description: "The API key has been reloaded from browser storage.",
        });
      } else {
        toast({
          title: "No API Key in Storage",
          description: "There was no API key found in browser storage to reload.",
        });
      }
    } catch (error) {
      toast({
        title: "Error Reloading API Key",
        description: "Could not reload API key from browser storage.",
        variant: "destructive",
      });
    }
  };
  const currentApiKeyIsSaved = !!(savedKey !== null && typeof apiKey === 'string' && apiKey.trim() === savedKey);
  const displayApiKey = typeof apiKey === 'string' ? apiKey : "";
  return (
    <ErrorBoundary fallback={<div>Something went wrong in ApiKeyManager</div>}>
      <Card>
      <CardHeader>
        <CardTitle className="text-lg">Google AI API Key</CardTitle>
        <CardDescription>
          Enter your Google AI API key. This key is stored locally in your browser for convenience. AI functionality relies on a separate server-side configuration.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="apiKey">API Key (stored in browser)</Label>
          <input
            id="apiKey"
            type="password"
            value={displayApiKey}
            onChange={(e) = aria-label="Input"> setApiKey(e.target.value)}
            placeholder="Enter your Google AI API Key"
            className="text-sm md:text-base lg:text-lg"
          />
        </div>
        {!displayApiKey.trim() && (
          <Alert variant="default" className="bg-muted/30">
            <Info className="h-4 w-4 !text-accent-foreground sm:w-auto md:w-full" />
            <AlertTitle className="font-semibold text-accent-foreground">Setup API Key</AlertTitle>
            <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
              Enter your Google AI API key above and save it to your browser. For Karen AI to function, this key also needs to be set up on the server.
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="block mt-2 text-primary underline">
                Get a Google AI API Key <ExternalLink className="inline-block h-3 w-3 ml-0.5 sm:w-auto md:w-full" />
              </a>
            </AlertDescription>
          </Alert>
        )}
        {displayApiKey.trim() && (
          <Alert variant="default" className="bg-muted/30">
            <AlertCircle className="h-4 w-4 !text-accent-foreground sm:w-auto md:w-full" />
            <AlertTitle className="font-semibold text-accent-foreground">Server Configuration Reminder</AlertTitle>
            <AlertDescription className="text-muted-foreground text-xs sm:text-sm md:text-base">
              The API key (starting with <code>{displayApiKey.substring(0,7)}...</code>) is {currentApiKeyIsSaved ? "saved in your browser" : "currently entered"}.
              For Karen AI's features to function, this key must also be configured on the server (typically via an <code>.env</code> file and a Genkit server restart).
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="block mt-2 text-primary underline">
                Get a Google AI API Key <ExternalLink className="inline-block h-3 w-3 ml-0.5 sm:w-auto md:w-full" />
              </a>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
        <button onClick={handleReloadFromStorage} variant="outline" size="sm" aria-label="Button">
          <RotateCcw className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
          Reload from Storage
        </Button>
        <button onClick={handleSaveKey} className="text-sm md:text-base lg:text-lg" disabled={!displayApiKey.trim() || currentApiKeyIsSaved} size="sm" aria-label="Button">
          {currentApiKeyIsSaved ? <CheckCircle2 className="mr-2 h-4 w-4 sm:w-auto md:w-full" /> : <Save className="mr-2 h-4 w-4 sm:w-auto md:w-full" />}
          {currentApiKeyIsSaved ? 'Key Saved' : 'Save to Browser'}
        </Button>
      </CardFooter>
    </Card>
    </ErrorBoundary>
  );
}
