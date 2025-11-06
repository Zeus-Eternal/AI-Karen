"use client";

/**
 * Plugin Registry
 *
 * Comprehensive plugin management interface for discovering, configuring, and managing
 * all types of plugins (LLM, Voice, Video, and Extensions)
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Puzzle,
  Search,
  RefreshCw,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Trash2,
  Plug,
  Volume2,
  Video,
  Cpu
} from 'lucide-react';

export interface Plugin {
  id: string;
  name: string;
  type: 'llm' | 'voice' | 'video' | 'extension';
  version: string;
  status: 'active' | 'inactive' | 'error';
  enabled: boolean;
  description: string;
  author: string;
  installed: boolean;
  configurable: boolean;
}

export interface PluginStats {
  totalInstalled: number;
  activePlugins: number;
  availableUpdates: number;
  errors: number;
}

export interface PluginRegistryProps {
  refreshInterval?: number;
}

export default function PluginRegistry({
  refreshInterval = 10000
}: PluginRegistryProps) {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [stats, setStats] = useState<PluginStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'llm' | 'voice' | 'video' | 'extension'>('all');
  const [isLoading, setIsLoading] = useState(false);

  const loadPlugins = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/plugins/registry');
      if (response.ok) {
        const data = await response.json();
        setPlugins(data.plugins);
        setStats(data.stats);
      } else {
        // Mock data
        const mockPlugins: Plugin[] = [
          {
            id: 'openai-plugin',
            name: 'OpenAI Provider',
            type: 'llm',
            version: '1.0.0',
            status: 'active',
            enabled: true,
            description: 'OpenAI GPT models provider',
            author: 'OpenAI',
            installed: true,
            configurable: true
          },
          {
            id: 'anthropic-plugin',
            name: 'Anthropic Provider',
            type: 'llm',
            version: '2.1.0',
            status: 'active',
            enabled: true,
            description: 'Claude models provider',
            author: 'Anthropic',
            installed: true,
            configurable: true
          },
          {
            id: 'elevenlabs-plugin',
            name: 'ElevenLabs Voice',
            type: 'voice',
            version: '1.5.0',
            status: 'active',
            enabled: true,
            description: 'High-quality text-to-speech',
            author: 'ElevenLabs',
            installed: true,
            configurable: true
          },
          {
            id: 'system-tts',
            name: 'System TTS',
            type: 'voice',
            version: '1.0.0',
            status: 'inactive',
            enabled: false,
            description: 'Built-in system text-to-speech',
            author: 'System',
            installed: true,
            configurable: false
          },
          {
            id: 'd-id-plugin',
            name: 'D-ID Video',
            type: 'video',
            version: '1.2.0',
            status: 'active',
            enabled: true,
            description: 'AI video generation platform',
            author: 'D-ID',
            installed: true,
            configurable: true
          },
          {
            id: 'heygen-plugin',
            name: 'HeyGen',
            type: 'video',
            version: '1.0.0',
            status: 'error',
            enabled: false,
            description: 'Video avatar generation',
            author: 'HeyGen',
            installed: true,
            configurable: true
          },
          {
            id: 'analytics-ext',
            name: 'Analytics Dashboard',
            type: 'extension',
            version: '2.0.0',
            status: 'active',
            enabled: true,
            description: 'Comprehensive analytics and reporting',
            author: 'Analytics Corp',
            installed: true,
            configurable: true
          }
        ];

        const mockStats: PluginStats = {
          totalInstalled: mockPlugins.length,
          activePlugins: mockPlugins.filter(p => p.status === 'active').length,
          availableUpdates: 2,
          errors: mockPlugins.filter(p => p.status === 'error').length
        };

        setPlugins(mockPlugins);
        setStats(mockStats);
      }
    } catch (error) {
      console.error('Failed to load plugins:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPlugins();
    const interval = setInterval(loadPlugins, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const filteredPlugins = plugins.filter(plugin => {
    const matchesSearch = plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plugin.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || plugin.type === filterType;
    return matchesSearch && matchesType;
  });

  const togglePlugin = (pluginId: string, enabled: boolean) => {
    setPlugins(prev =>
      prev.map(p =>
        p.id === pluginId
          ? { ...p, enabled, status: enabled ? 'active' : 'inactive' }
          : p
      )
    );
  };

  const uninstallPlugin = (pluginId: string) => {
    setPlugins(prev => prev.filter(p => p.id !== pluginId));
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'llm':
        return <Cpu className="h-4 w-4" />;
      case 'voice':
        return <Volume2 className="h-4 w-4" />;
      case 'video':
        return <Video className="h-4 w-4" />;
      case 'extension':
        return <Plug className="h-4 w-4" />;
      default:
        return <Puzzle className="h-4 w-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'inactive':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Puzzle className="h-5 w-5" />
              Plugin Registry
            </div>
            <Button onClick={loadPlugins} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage all plugins and integrations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          {stats && (
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Total Installed</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalInstalled}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Active</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.activePlugins}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Updates Available</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{stats.availableUpdates}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-muted-foreground">Errors</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
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
                placeholder="Search plugins..."
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
              <Button
                variant={filterType === 'extension' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterType('extension')}
              >
                <Plug className="h-3 w-3 mr-1" />
                Extension
              </Button>
            </div>
          </div>

          {/* Plugins List */}
          <ScrollArea className="h-[600px]">
            <div className="space-y-3 pr-4">
              {filteredPlugins.map((plugin) => (
                <Card key={plugin.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getTypeIcon(plugin.type)}
                          <h4 className="font-medium">{plugin.name}</h4>
                          <Badge variant="outline" className="capitalize">
                            {plugin.type}
                          </Badge>
                          {getStatusIcon(plugin.status)}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {plugin.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>v{plugin.version}</span>
                          <span>•</span>
                          <span>{plugin.author}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {plugin.configurable && (
                          <Button variant="ghost" size="sm">
                            <Settings className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => uninstallPlugin(plugin.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                        <Button
                          variant={plugin.enabled ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => togglePlugin(plugin.id, !plugin.enabled)}
                        >
                          {plugin.enabled ? 'Disable' : 'Enable'}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {filteredPlugins.length === 0 && (
                <div className="text-center py-12">
                  <Puzzle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No plugins found</h3>
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

export { PluginRegistry };
export type { PluginRegistryProps, Plugin, PluginStats };
