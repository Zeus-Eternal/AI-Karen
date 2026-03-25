"use client";

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Server, Search, Download, HardDrive, Loader2, List, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';

interface ProviderModel {
  id: string;
  name: string;
  family: string;
  source: string;
}

interface ProviderModelsResponse {
  provider: string;
  base_url?: string | null;
  models: ProviderModel[];
}

interface OllamaSearchResult {
  name: string;
  description: string;
}

interface OllamaTagsResponse {
  models?: Array<{
    name?: string;
    model?: string;
    details?: {
      family?: string;
    };
  }>;
}

interface OllamaModelManagerProps {
  ollamaAddress: string;
  selectedModel: string;
  onAddressChange: (value: string) => void;
  onModelSelect: (value: string) => void;
  onModelsDiscovered?: (models: ProviderModel[]) => void;
}

const POPULAR_OLLAMA_MODELS: OllamaSearchResult[] = [
  { name: 'llama3.2:latest', description: 'Meta Llama 3.2 general-purpose model.' },
  { name: 'llama3.1:8b', description: 'Balanced local inference for chat workloads.' },
  { name: 'qwen2.5:7b', description: 'Strong multilingual reasoning from Qwen.' },
  { name: 'deepseek-r1:8b', description: 'Compact reasoning-focused DeepSeek variant.' },
  { name: 'mistral:latest', description: 'Fast general-purpose Mistral model.' },
  { name: 'phi4:latest', description: 'Compact local model with strong instruction following.' },
  { name: 'codellama:13b', description: 'Code-focused local model.' },
  { name: 'llava:latest', description: 'Vision-capable local model for image understanding.' },
];

function normalizeBrowserOllamaAddress(address: string): string {
  const trimmed = address.trim() || 'http://localhost:11434';
  return trimmed.replace(/\/api\/?$/, '').replace(/\/$/, '');
}

function canUseLocalOllamaProxy(address: string): boolean {
  const normalized = normalizeBrowserOllamaAddress(address);
  try {
    const parsed = new URL(normalized);
    return ['localhost', '127.0.0.1'].includes(parsed.hostname);
  } catch {
    return normalized.startsWith('http://localhost') || normalized.startsWith('http://127.0.0.1');
  }
}

async function parseOllamaTagsResponse(response: Response): Promise<ProviderModel[]> {
  if (!response.ok) {
    throw new Error(`Ollama returned HTTP ${response.status}`);
  }

  const data = await response.json() as OllamaTagsResponse;
  const rawModels = Array.isArray(data.models) ? data.models : [];

  return rawModels
    .map((model) => {
      const id = model.name?.trim() || model.model?.trim() || '';
      if (!id) {
        return null;
      }

      return {
        id,
        name: id,
        family: model.details?.family || 'unknown',
        source: 'discovered',
      } satisfies ProviderModel;
    })
    .filter((model): model is ProviderModel => model !== null);
}

async function fetchModelsFromBrowser(address: string): Promise<ProviderModel[]> {
  const response = await fetch(`${normalizeBrowserOllamaAddress(address)}/api/tags`, {
    method: 'GET',
    cache: 'no-store',
  });

  return parseOllamaTagsResponse(response);
}

async function fetchModelsFromLocalProxy(address: string): Promise<ProviderModel[]> {
  const response = await fetch(`/api/ollama/tags?base_url=${encodeURIComponent(normalizeBrowserOllamaAddress(address))}`, {
    method: 'GET',
    cache: 'no-store',
  });

  return parseOllamaTagsResponse(response);
}

async function fetchModelsFromBestLocalSource(address: string): Promise<{ models: ProviderModel[]; source: 'browser' | 'proxy' }> {
  try {
    const models = await fetchModelsFromLocalProxy(address);
    return { models, source: 'proxy' };
  } catch {
    const models = await fetchModelsFromBrowser(address);
    return { models, source: 'browser' };
  }
}

export default function OllamaModelManager({
  ollamaAddress,
  selectedModel,
  onAddressChange,
  onModelSelect,
  onModelsDiscovered,
}: OllamaModelManagerProps) {
  const [isFetchingLocal, setIsFetchingLocal] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);
  const [localModels, setLocalModels] = useState<ProviderModel[]>([]);
  const [searchResults, setSearchResults] = useState<OllamaSearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const { toast } = useToast();

  const handleFetchLocalModels = async () => {
    setIsFetchingLocal(true);
    try {
      let discoveredModels: ProviderModel[] = [];
      let localSource: 'browser' | 'proxy' | null = null;

      if (canUseLocalOllamaProxy(ollamaAddress)) {
        const localResult = await fetchModelsFromBestLocalSource(ollamaAddress);
        discoveredModels = localResult.models;
        localSource = localResult.source;
      } else {
        const query = ollamaAddress ? `?base_url=${encodeURIComponent(ollamaAddress)}` : '';
        const response = await apiClient.get<ProviderModelsResponse>(`/api/settings/model/providers/ollama/models${query}`);
        discoveredModels = response.models;
      }

      setLocalModels(discoveredModels);
      onModelsDiscovered?.(discoveredModels);

      if (discoveredModels.length > 0) {
        const activeModel = discoveredModels.find((model) => model.id === selectedModel) ?? discoveredModels[0];
        onModelSelect(activeModel.id);
      }

      toast({
        title: 'Local models loaded',
        description: discoveredModels.length > 0
          ? `Discovered ${discoveredModels.length} Ollama model(s)${
              localSource === 'browser' ? ' via direct browser access' :
              localSource === 'proxy' ? ' via local proxy access' : ''
            }.`
          : 'No local Ollama models were reported by the server.',
      });
    } catch (error) {
      if (canUseLocalOllamaProxy(ollamaAddress)) {
        try {
          const localResult = await fetchModelsFromBestLocalSource(ollamaAddress);
          const discoveredModels = localResult.models;
          setLocalModels(discoveredModels);
          onModelsDiscovered?.(discoveredModels);

          if (discoveredModels.length > 0) {
            const activeModel = discoveredModels.find((model) => model.id === selectedModel) ?? discoveredModels[0];
            onModelSelect(activeModel.id);
          }

          toast({
            title: 'Local models loaded',
            description: discoveredModels.length > 0
              ? `Discovered ${discoveredModels.length} Ollama model(s) via ${
                  localResult.source === 'browser' ? 'direct browser access' : 'local proxy access'
                }.`
              : 'No local Ollama models were returned by the configured address.',
          });
          return;
        } catch {
          // Fall through to the existing destructive toast.
        }
      }

      toast({
        title: 'Unable to reach Ollama',
        description: 'Karen could not load models from the configured Ollama server.',
        variant: 'destructive',
      });
    } finally {
      setIsFetchingLocal(false);
    }
  };

  const handleSearchModels = async () => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    const filtered = POPULAR_OLLAMA_MODELS.filter((model) => {
      return model.name.toLowerCase().includes(query) || model.description.toLowerCase().includes(query);
    });

    const results = filtered.length > 0
      ? filtered
      : [{ name: searchQuery.trim(), description: 'Pull this exact Ollama tag from the configured server.' }];

    setSearchResults(results);
    setIsSearching(false);
  };

  const handleDownloadModel = async (modelName: string) => {
    setIsDownloading(modelName);
    try {
      await apiClient.post('/api/settings/model/providers/ollama/pull', {
        model: modelName,
        base_url: ollamaAddress,
      });
      await handleFetchLocalModels();
      onModelSelect(modelName);
      toast({
        title: 'Model pulled',
        description: `"${modelName}" is now available for Karen to use locally.`,
      });
    } catch (error) {
      toast({
        title: 'Model pull failed',
        description: `Karen could not pull "${modelName}" from Ollama.`,
        variant: 'destructive',
      });
    } finally {
      setIsDownloading(null);
    }
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
          onChange={(event) => onAddressChange(event.target.value)}
          placeholder="e.g., http://localhost:11434"
        />
      </div>

      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="space-y-2">
            <h4 className="flex items-center font-semibold text-sm">
              <HardDrive className="mr-2 h-4 w-4" /> My Local Models
            </h4>
            <Button onClick={handleFetchLocalModels} disabled={isFetchingLocal} variant="outline" className="w-full">
              {isFetchingLocal ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <List className="mr-2 h-4 w-4" />}
              {isFetchingLocal ? 'Fetching...' : 'Fetch Downloaded Models'}
            </Button>
            {localModels.length > 0 && (
              <ScrollArea className="mt-2 h-32 w-full rounded-md border bg-muted/50 p-2">
                <ul className="space-y-1">
                  {localModels.map((model) => {
                    const isSelected = model.id === selectedModel;
                    return (
                      <li key={model.id}>
                        <button
                          type="button"
                          onClick={() => onModelSelect(model.id)}
                          className={`flex w-full items-center justify-between rounded-md bg-background px-2 py-1.5 text-left text-xs ${
                            isSelected ? 'border border-primary/40' : 'border border-transparent'
                          }`}
                        >
                          <span>{model.name}</span>
                          {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </ScrollArea>
            )}
          </div>

          <div className="space-y-2">
            <h4 className="flex items-center font-semibold text-sm">
              <Search className="mr-2 h-4 w-4" /> Find New Models
            </h4>
            <div className="flex gap-2">
              <Input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search or enter an Ollama tag"
              />
              <Button onClick={handleSearchModels} disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                Search
              </Button>
            </div>
            {searchResults.length > 0 && (
              <ScrollArea className="mt-2 h-40 w-full rounded-md border bg-muted/50 p-2">
                <ul className="space-y-2">
                  {searchResults.map((model) => (
                    <li key={model.name} className="flex items-center justify-between rounded-md bg-background p-2 text-sm">
                      <div className="flex-1 pr-2">
                        <p className="text-xs font-medium">{model.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{model.description}</p>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleDownloadModel(model.name)}
                        disabled={isDownloading !== null}
                      >
                        {isDownloading === model.name ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
                        {isDownloading === model.name ? 'Pulling...' : 'Pull'}
                      </Button>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            )}
          </div>
        </CardContent>
      </Card>

      <Alert>
        <AlertDescription className="text-xs">
          Karen will try backend discovery first. For local addresses like `localhost`, model discovery can fall back to the web app&apos;s local proxy, while the selected model still feeds directly into Karen&apos;s saved model settings.
        </AlertDescription>
      </Alert>
    </div>
  );
}
