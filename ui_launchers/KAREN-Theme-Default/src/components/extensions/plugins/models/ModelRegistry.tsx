"use client";

/**
 * Model Registry
 *
 * Comprehensive model management interface for discovering, configuring,
 * and managing LLM models across all providers
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Cpu,
  Search,
  RefreshCw,
  Settings,
  CheckCircle,
  XCircle,
  Star,
  TrendingUp,
  Zap,
  DollarSign
} from 'lucide-react';

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  version: string;
  type: 'chat' | 'completion' | 'embedding' | 'image' | 'audio';
  status: 'available' | 'unavailable' | 'deprecated';
  enabled: boolean;
  contextWindow: number;
  pricing: {
    input: number;
    output: number;
    unit: string;
  };
  capabilities: string[];
  rating: number;
  downloads: number;
  description: string;
}

export interface ModelStats {
  totalModels: number;
  availableModels: number;
  enabledModels: number;
  providers: number;
}

export interface ModelRegistryProps {
  refreshInterval?: number;
}

export default function ModelRegistry({
  refreshInterval = 15000
}: ModelRegistryProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [stats, setStats] = useState<ModelStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'rating' | 'downloads' | 'provider'>('name');
  const [isLoading, setIsLoading] = useState(false);

  const loadModels = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/models/registry');
      if (response.ok) {
        const data = await response.json();
        setModels(data.models);
        setStats(data.stats);
      } else {
        // Mock data
        const mockModels: ModelInfo[] = [
          {
            id: 'gpt-4-turbo',
            name: 'GPT-4 Turbo',
            provider: 'OpenAI',
            version: '2024-01',
            type: 'chat',
            status: 'available',
            enabled: true,
            contextWindow: 128000,
            pricing: {
              input: 0.01,
              output: 0.03,
              unit: '1K tokens'
            },
            capabilities: ['function-calling', 'vision', 'json-mode'],
            rating: 4.8,
            downloads: 125000,
            description: 'Most capable GPT-4 model with extended context'
          },
          {
            id: 'claude-3-opus',
            name: 'Claude 3 Opus',
            provider: 'Anthropic',
            version: '2024-02',
            type: 'chat',
            status: 'available',
            enabled: true,
            contextWindow: 200000,
            pricing: {
              input: 0.015,
              output: 0.075,
              unit: '1K tokens'
            },
            capabilities: ['extended-context', 'analysis', 'coding'],
            rating: 4.9,
            downloads: 98000,
            description: 'Most powerful Claude model for complex tasks'
          },
          {
            id: 'gpt-3.5-turbo',
            name: 'GPT-3.5 Turbo',
            provider: 'OpenAI',
            version: '2024-01',
            type: 'chat',
            status: 'available',
            enabled: true,
            contextWindow: 16385,
            pricing: {
              input: 0.0005,
              output: 0.0015,
              unit: '1K tokens'
            },
            capabilities: ['function-calling', 'fast-response'],
            rating: 4.5,
            downloads: 450000,
            description: 'Fast and efficient model for most tasks'
          },
          {
            id: 'claude-3-sonnet',
            name: 'Claude 3 Sonnet',
            provider: 'Anthropic',
            version: '2024-02',
            type: 'chat',
            status: 'available',
            enabled: false,
            contextWindow: 200000,
            pricing: {
              input: 0.003,
              output: 0.015,
              unit: '1K tokens'
            },
            capabilities: ['balanced-performance', 'extended-context'],
            rating: 4.7,
            downloads: 87000,
            description: 'Balanced performance and speed'
          },
          {
            id: 'text-embedding-3-large',
            name: 'Text Embedding 3 Large',
            provider: 'OpenAI',
            version: '2024-01',
            type: 'embedding',
            status: 'available',
            enabled: true,
            contextWindow: 8191,
            pricing: {
              input: 0.00013,
              output: 0,
              unit: '1K tokens'
            },
            capabilities: ['semantic-search', 'clustering'],
            rating: 4.6,
            downloads: 210000,
            description: 'High-quality text embeddings'
          },
          {
            id: 'dalle-3',
            name: 'DALL-E 3',
            provider: 'OpenAI',
            version: '2023-11',
            type: 'image',
            status: 'available',
            enabled: false,
            contextWindow: 0,
            pricing: {
              input: 0.04,
              output: 0,
              unit: 'per image'
            },
            capabilities: ['image-generation', 'high-quality'],
            rating: 4.4,
            downloads: 65000,
            description: 'Advanced image generation model'
          },
          {
            id: 'whisper-large-v3',
            name: 'Whisper Large V3',
            provider: 'OpenAI',
            version: '2023-11',
            type: 'audio',
            status: 'available',
            enabled: true,
            contextWindow: 0,
            pricing: {
              input: 0.006,
              output: 0,
              unit: 'per minute'
            },
            capabilities: ['speech-to-text', 'multilingual'],
            rating: 4.7,
            downloads: 145000,
            description: 'State-of-the-art speech recognition'
          }
        ];

        const mockStats: ModelStats = {
          totalModels: mockModels.length,
          availableModels: mockModels.filter(m => m.status === 'available').length,
          enabledModels: mockModels.filter(m => m.enabled).length,
          providers: new Set(mockModels.map(m => m.provider)).size
        };

        setModels(mockModels);
        setStats(mockStats);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
    const interval = setInterval(loadModels, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const filteredAndSortedModels = models
    .filter(model => {
      const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesProvider = filterProvider === 'all' || model.provider === filterProvider;
      const matchesType = filterType === 'all' || model.type === filterType;
      return matchesSearch && matchesProvider && matchesType;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return b.rating - a.rating;
        case 'downloads':
          return b.downloads - a.downloads;
        case 'provider':
          return a.provider.localeCompare(b.provider);
        case 'name':
        default:
          return a.name.localeCompare(b.name);
      }
    });

  const toggleModel = (modelId: string, enabled: boolean) => {
    setModels(prev =>
      prev.map(m =>
        m.id === modelId ? { ...m, enabled } : m
      )
    );
  };

  const providers = Array.from(new Set(models.map(m => m.provider)));
  const types = Array.from(new Set(models.map(m => m.type)));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Model Registry
            </div>
            <Button onClick={loadModels} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Browse and manage LLM models across all providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          {stats && (
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Total Models</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalModels}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Available</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.availableModels}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Enabled</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{stats.enabledModels}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Providers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.providers}</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Search and Filters */}
          <div className="space-y-4 mb-6">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 z-10" />
                <Input
                  type="text"
                  placeholder="Search models..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Select value={filterProvider} onValueChange={setFilterProvider}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Providers</SelectItem>
                  {providers.map(provider => (
                    <SelectItem key={provider} value={provider}>{provider}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {types.map(type => (
                    <SelectItem key={type} value={type} className="capitalize">{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={(value) => setSortBy(value as any)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="rating">Rating</SelectItem>
                  <SelectItem value="downloads">Downloads</SelectItem>
                  <SelectItem value="provider">Provider</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Models List */}
          <ScrollArea className="h-[600px]">
            <div className="space-y-3 pr-4">
              {filteredAndSortedModels.map((model) => (
                <Card key={model.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="font-medium">{model.name}</h4>
                          <Badge variant="outline">{model.provider}</Badge>
                          <Badge variant="outline" className="capitalize">{model.type}</Badge>
                          {model.status === 'available' ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {model.description}
                        </p>

                        <div className="grid md:grid-cols-2 gap-4 mb-3">
                          <div className="space-y-2 text-sm">
                            {model.contextWindow > 0 && (
                              <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">Context:</span>
                                <span className="font-medium">{model.contextWindow.toLocaleString()} tokens</span>
                              </div>
                            )}
                            <div className="flex items-center gap-2">
                              <Star className="h-3 w-3 text-yellow-500" />
                              <span className="font-medium">{model.rating}</span>
                              <span className="text-muted-foreground">•</span>
                              <TrendingUp className="h-3 w-3" />
                              <span className="text-muted-foreground">{model.downloads.toLocaleString()} downloads</span>
                            </div>
                          </div>

                          <div className="space-y-2 text-sm">
                            <div className="flex items-center gap-2">
                              <DollarSign className="h-3 w-3" />
                              <span className="text-muted-foreground">Input:</span>
                              <span className="font-medium">${model.pricing.input}/{model.pricing.unit}</span>
                            </div>
                            {model.pricing.output > 0 && (
                              <div className="flex items-center gap-2">
                                <DollarSign className="h-3 w-3" />
                                <span className="text-muted-foreground">Output:</span>
                                <span className="font-medium">${model.pricing.output}/{model.pricing.unit}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {model.capabilities.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {model.capabilities.map(cap => (
                              <Badge key={cap} variant="secondary" className="text-xs">
                                {cap}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button
                          variant={model.enabled ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => toggleModel(model.id, !model.enabled)}
                          disabled={model.status !== 'available'}
                        >
                          {model.enabled ? 'Enabled' : 'Enable'}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {filteredAndSortedModels.length === 0 && (
                <div className="text-center py-12">
                  <Cpu className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No models found</h3>
                  <p className="text-muted-foreground">Try adjusting your search or filters</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

export { ModelRegistry };
export type { ModelRegistryProps, ModelInfo, ModelStats };
