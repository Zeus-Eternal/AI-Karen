"use client";

/**
 * Provider Registry
 *
 * Comprehensive provider management interface for managing all types of providers
 * (LLM, Voice, Video) including configuration, health monitoring, and API key management
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plug,
  Search,
  RefreshCw,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Key,
  Activity,
  Cpu,
  Volume2,
  Video
} from 'lucide-react';

export interface ProviderConfig {
  id: string;
  name: string;
  type: 'llm' | 'voice' | 'video';
  status: 'healthy' | 'degraded' | 'down' | 'unconfigured';
  enabled: boolean;
  hasApiKey: boolean;
  apiKeyMasked?: string;
  modelsAvailable: number;
  description: string;
  healthCheck: {
    lastCheck: string;
    responseTime: number;
    successRate: number;
  };
  usage: {
    requestsToday: number;
    costToday: number;
    quotaRemaining: number;
  };
}

export interface ProviderStats {
  totalProviders: number;
  healthyProviders: number;
  enabledProviders: number;
  totalRequests: number;
  totalCost: number;
}

export interface ProviderRegistryProps {
  refreshInterval?: number;
}

export default function ProviderRegistry({
  refreshInterval = 10000
}: ProviderRegistryProps) {
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [stats, setStats] = useState<ProviderStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'llm' | 'voice' | 'video'>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [configuringProvider, setConfiguringProvider] = useState<string | null>(null);

  const loadProviders = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/providers/registry');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers);
        setStats(data.stats);
      } else {
        // Mock data
        const mockProviders: ProviderConfig[] = [
          {
            id: 'openai',
            name: 'OpenAI',
            type: 'llm',
            status: 'healthy',
            enabled: true,
            hasApiKey: true,
            apiKeyMasked: 'sk-...Xy9Z',
            modelsAvailable: 15,
            description: 'GPT-4, GPT-3.5, DALL-E, Whisper, and Embeddings',
            healthCheck: {
              lastCheck: new Date(Date.now() - 300000).toISOString(),
              responseTime: 245,
              successRate: 99.8
            },
            usage: {
              requestsToday: 1247,
              costToday: 12.45,
              quotaRemaining: 85
            }
          },
          {
            id: 'anthropic',
            name: 'Anthropic',
            type: 'llm',
            status: 'healthy',
            enabled: true,
            hasApiKey: true,
            apiKeyMasked: 'sk-ant-...AbC1',
            modelsAvailable: 3,
            description: 'Claude 3 Opus, Sonnet, and Haiku',
            healthCheck: {
              lastCheck: new Date(Date.now() - 180000).toISOString(),
              responseTime: 312,
              successRate: 99.5
            },
            usage: {
              requestsToday: 892,
              costToday: 15.67,
              quotaRemaining: 92
            }
          },
          {
            id: 'elevenlabs',
            name: 'ElevenLabs',
            type: 'voice',
            status: 'healthy',
            enabled: true,
            hasApiKey: true,
            apiKeyMasked: '***...***',
            modelsAvailable: 8,
            description: 'High-quality text-to-speech voices',
            healthCheck: {
              lastCheck: new Date(Date.now() - 420000).toISOString(),
              responseTime: 189,
              successRate: 98.9
            },
            usage: {
              requestsToday: 342,
              costToday: 3.42,
              quotaRemaining: 67
            }
          },
          {
            id: 'google-tts',
            name: 'Google Text-to-Speech',
            type: 'voice',
            status: 'degraded',
            enabled: true,
            hasApiKey: true,
            apiKeyMasked: 'AIza...def',
            modelsAvailable: 12,
            description: 'Google Cloud TTS with WaveNet voices',
            healthCheck: {
              lastCheck: new Date(Date.now() - 120000).toISOString(),
              responseTime: 456,
              successRate: 92.3
            },
            usage: {
              requestsToday: 156,
              costToday: 0.78,
              quotaRemaining: 45
            }
          },
          {
            id: 'd-id',
            name: 'D-ID',
            type: 'video',
            status: 'healthy',
            enabled: true,
            hasApiKey: true,
            apiKeyMasked: 'Basic ...ghi',
            modelsAvailable: 5,
            description: 'AI video generation with digital avatars',
            healthCheck: {
              lastCheck: new Date(Date.now() - 600000).toISOString(),
              responseTime: 892,
              successRate: 97.6
            },
            usage: {
              requestsToday: 45,
              costToday: 22.50,
              quotaRemaining: 78
            }
          },
          {
            id: 'heygen',
            name: 'HeyGen',
            type: 'video',
            status: 'unconfigured',
            enabled: false,
            hasApiKey: false,
            modelsAvailable: 0,
            description: 'Video avatar generation platform',
            healthCheck: {
              lastCheck: new Date(Date.now() - 3600000).toISOString(),
              responseTime: 0,
              successRate: 0
            },
            usage: {
              requestsToday: 0,
              costToday: 0,
              quotaRemaining: 0
            }
          }
        ];

        const mockStats: ProviderStats = {
          totalProviders: mockProviders.length,
          healthyProviders: mockProviders.filter(p => p.status === 'healthy').length,
          enabledProviders: mockProviders.filter(p => p.enabled).length,
          totalRequests: mockProviders.reduce((sum, p) => sum + p.usage.requestsToday, 0),
          totalCost: mockProviders.reduce((sum, p) => sum + p.usage.costToday, 0)
        };

        setProviders(mockProviders);
        setStats(mockStats);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProviders();
    const interval = setInterval(loadProviders, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const filteredProviders = providers.filter(provider => {
    const matchesSearch = provider.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      provider.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || provider.type === filterType;
    return matchesSearch && matchesType;
  });

  const toggleProvider = (providerId: string, enabled: boolean) => {
    setProviders(prev =>
      prev.map(p =>
        p.id === providerId ? { ...p, enabled } : p
      )
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'down':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'unconfigured':
        return <Settings className="h-4 w-4 text-gray-400" />;
      default:
        return null;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'llm':
        return <Cpu className="h-4 w-4" />;
      case 'voice':
        return <Volume2 className="h-4 w-4" />;
      case 'video':
        return <Video className="h-4 w-4" />;
      default:
        return <Plug className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Plug className="h-5 w-5" />
              Provider Registry
            </div>
            <Button onClick={loadProviders} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage all AI provider connections and configurations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          {stats && (
            <div className="grid md:grid-cols-5 gap-4 mb-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Total Providers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalProviders}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Healthy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.healthyProviders}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Enabled</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{stats.enabledProviders}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Requests Today</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalRequests.toLocaleString()}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Cost Today</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${stats.totalCost.toFixed(2)}</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Search and Filter */}
          <div className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 z-10" />
              <Input
                type="text"
                placeholder="Search providers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={filterType === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterType('all')}
              >
                All
              </Button>
              <Button
                variant={filterType === 'llm' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterType('llm')}
              >
                <Cpu className="h-3 w-3 mr-1" />
                LLM
              </Button>
              <Button
                variant={filterType === 'voice' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterType('voice')}
              >
                <Volume2 className="h-3 w-3 mr-1" />
                Voice
              </Button>
              <Button
                variant={filterType === 'video' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterType('video')}
              >
                <Video className="h-3 w-3 mr-1" />
                Video
              </Button>
            </div>
          </div>

          {/* Providers List */}
          <ScrollArea className="h-[600px]">
            <div className="space-y-3 pr-4">
              {filteredProviders.map((provider) => (
                <Card key={provider.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getTypeIcon(provider.type)}
                          <h4 className="font-medium">{provider.name}</h4>
                          <Badge variant="outline" className="capitalize">{provider.type}</Badge>
                          {getStatusIcon(provider.status)}
                          <Badge
                            variant={
                              provider.status === 'healthy' ? 'default' :
                              provider.status === 'degraded' ? 'secondary' :
                              'destructive'
                            }
                            className={provider.status === 'healthy' ? 'bg-green-600' : ''}
                          >
                            {provider.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {provider.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={provider.enabled}
                          onCheckedChange={(checked) => toggleProvider(provider.id, checked)}
                          disabled={!provider.hasApiKey}
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 mb-3">
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Key className="h-3 w-3" />
                          <span className="text-muted-foreground">API Key:</span>
                          {provider.hasApiKey ? (
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {provider.apiKeyMasked}
                            </code>
                          ) : (
                            <Badge variant="destructive" className="text-xs">Not configured</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Models:</span>
                          <span className="font-medium">{provider.modelsAvailable}</span>
                        </div>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Activity className="h-3 w-3" />
                          <span className="text-muted-foreground">Response Time:</span>
                          <span className="font-medium">{provider.healthCheck.responseTime}ms</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Success Rate:</span>
                          <span className="font-medium">{provider.healthCheck.successRate}%</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-3 gap-4 p-3 bg-muted/50 rounded-lg text-sm">
                      <div>
                        <span className="text-muted-foreground">Requests Today:</span>
                        <span className="ml-2 font-medium">{provider.usage.requestsToday.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Cost Today:</span>
                        <span className="ml-2 font-medium">${provider.usage.costToday.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Quota:</span>
                        <span className="ml-2 font-medium">{provider.usage.quotaRemaining}%</span>
                      </div>
                    </div>

                    <div className="flex gap-2 mt-3">
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4 mr-2" />
                        Configure
                      </Button>
                      <Button variant="outline" size="sm">
                        <Activity className="h-4 w-4 mr-2" />
                        View Metrics
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {filteredProviders.length === 0 && (
                <div className="text-center py-12">
                  <Plug className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No providers found</h3>
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

export { ProviderRegistry };
export type { ProviderRegistryProps, ProviderConfig, ProviderStats };
