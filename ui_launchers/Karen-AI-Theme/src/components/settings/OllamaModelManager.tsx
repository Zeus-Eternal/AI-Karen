"use client";

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Server, Search, Download, HardDrive, Loader2, List } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// This is a placeholder for a real model search result from Ollama's library
interface OllamaSearchResult {
  name: string;
  description: string;
  pulls: number;
}

/**
 * @file OllamaModelManager.tsx
 * @description UI component for managing a local Ollama instance.
 * Provides conceptual UI for fetching local models, searching the Ollama library, and downloading new models.
 * This component is for demonstration and requires backend/server-action implementation to be functional.
 */
export default function OllamaModelManager() {
  const [ollamaAddress, setOllamaAddress] = useState('http://localhost:11434');
  const [isFetchingLocal, setIsFetchingLocal] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isDownloading, setIsDownloading] = useState<string | null>(null); // Track which model is "downloading"
  const [localModels, setLocalModels] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<OllamaSearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const { toast } = useToast();

  const handleFetchLocalModels = async () => {
    setIsFetchingLocal(true);
    // MOCK: In a real implementation, this would be an API call to a server action.
    await new Promise(resolve => setTimeout(resolve, 800));
    setLocalModels(['llama3:8b-instruct-q5_K_M', 'codegemma:7b-instruct', 'llava:latest']);
    toast({
      title: "Local Models Fetched (Mock)",
      description: "Successfully fetched the list of locally available Ollama models.",
    });
    setIsFetchingLocal(false);
  };

  const handleSearchModels = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    // MOCK: In a real implementation, this would call a server action that queries the Ollama library.
    await new Promise(resolve => setTimeout(resolve, 1200));
    setSearchResults([
      { name: 'gemma:7b', description: 'A lightweight, state-of-the-art open model from Google.', pulls: 1000000 },
      { name: 'mistral:latest', description: 'The 7B model from Mistral AI, a powerful and versatile model.', pulls: 2500000 },
      { name: 'phi3:mini', description: 'A lightweight, state-of-the-art open model by Microsoft.', pulls: 500000 },
    ]);
    toast({
      title: "Search Complete (Mock)",
      description: `Found results for "${searchQuery}".`,
    });
    setIsSearching(false);
  };
  
  const handleDownloadModel = async (modelName: string) => {
    setIsDownloading(modelName);
    // MOCK: In a real implementation, this would trigger a long-running server action.
    await new Promise(resolve => setTimeout(resolve, 5000));
    setLocalModels(prev => [...prev, modelName]);
    toast({
      title: "Download Complete (Mock)",
      description: `Model "${modelName}" is now available locally.`,
    });
    setIsDownloading(null);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="ollama-address" className="flex items-center">
          <Server className="mr-2 h-4 w-4 text-primary/80" /> Ollama Server Address
        </Label>
        <Input
          id="ollama-address"
          value={ollamaAddress}
          onChange={(e) => setOllamaAddress(e.target.value)}
          placeholder="e.g., http://localhost:11434"
        />
      </div>

      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center"><HardDrive className="mr-2 h-4 w-4" /> My Local Models</h4>
            <Button onClick={handleFetchLocalModels} disabled={isFetchingLocal} variant="outline" className="w-full">
              {isFetchingLocal ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <List className="mr-2 h-4 w-4" />}
              {isFetchingLocal ? 'Fetching...' : 'Fetch Downloaded Models'}
            </Button>
            {localModels.length > 0 && (
              <ScrollArea className="h-28 mt-2 w-full rounded-md border p-2 bg-muted/50">
                <ul className="space-y-1">
                  {localModels.map(model => (
                    <li key={model} className="text-xs p-1.5 rounded-md bg-background">{model}</li>
                  ))}
                </ul>
              </ScrollArea>
            )}
          </div>
          
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center"><Search className="mr-2 h-4 w-4" /> Find New Models</h4>
            <div className="flex gap-2">
              <Input 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a model (e.g., gemma)"
              />
              <Button onClick={handleSearchModels} disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                Search
              </Button>
            </div>
            {searchResults.length > 0 && (
               <ScrollArea className="h-40 mt-2 w-full rounded-md border p-2 bg-muted/50">
                 <ul className="space-y-2">
                   {searchResults.map(model => (
                     <li key={model.name} className="flex justify-between items-center text-sm p-2 rounded-md bg-background">
                       <div className="flex-1 pr-2">
                         <p className="font-medium text-xs">{model.name}</p>
                         <p className="text-xs text-muted-foreground truncate">{model.description}</p>
                       </div>
                       <Button 
                         variant="secondary" 
                         size="sm"
                         onClick={() => handleDownloadModel(model.name)}
                         disabled={isDownloading !== null}
                       >
                         {isDownloading === model.name ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
                         {isDownloading === model.name ? 'Downloading...' : 'Download'}
                       </Button>
                     </li>
                   ))}
                 </ul>
               </ScrollArea>
            )}
          </div>

        </CardContent>
      </Card>
      
      <Alert variant="destructive">
        <AlertDescription className="text-xs">
           Ollama integration is conceptual. All actions on this page are mocked and do not connect to a real Ollama instance. Full implementation requires server-side actions to interact with the Ollama REST API.
        </AlertDescription>
      </Alert>
    </div>
  );
}
