"use client";

/**
 * Extension Dashboard Component
 *
 * Comprehensive dashboard for managing and monitoring system extensions
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Puzzle,
  Play,
  Square,
  RefreshCw,
  Settings,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Download,
  Package
} from 'lucide-react';

interface Extension {
  id: string;
  name: string;
  version: string;
  status: 'active' | 'inactive' | 'error';
  category: string;
  description: string;
  author: string;
  lastUpdated: string;
  memoryUsage?: number;
  cpuUsage?: number;
}

interface ExtensionStats {
  total: number;
  active: number;
  inactive: number;
  errors: number;
  categories: Record<string, number>;
}

interface ExtensionDashboardProps {
  onExtensionToggle?: (id: string, enabled: boolean) => void;
  onExtensionSettings?: (id: string) => void;
  refreshInterval?: number;
}

export default function ExtensionDashboard({
  onExtensionToggle,
  onExtensionSettings,
  refreshInterval = 10000
}: ExtensionDashboardProps) {
  const [extensions, setExtensions] = useState<Extension[]>([]);
  const [stats, setStats] = useState<ExtensionStats>({
    total: 0,
    active: 0,
    inactive: 0,
    errors: 0,
    categories: {}
  });
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const loadExtensions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/list');
      if (response.ok) {
        const data = await response.json();
        setExtensions(data.extensions);
        setStats(data.stats);
      } else {
        // Fallback mock data
        const mockExtensions: Extension[] = [
          {
            id: 'ext_auth',
            name: 'Authentication Extension',
            version: '2.1.0',
            status: 'active',
            category: 'Security',
            description: 'Provides advanced authentication mechanisms',
            author: 'System',
            lastUpdated: new Date().toISOString(),
            memoryUsage: 45,
            cpuUsage: 2
          },
          {
            id: 'ext_analytics',
            name: 'Analytics Engine',
            version: '1.5.2',
            status: 'active',
            category: 'Monitoring',
            description: 'Real-time analytics and reporting',
            author: 'Analytics Team',
            lastUpdated: new Date(Date.now() - 86400000).toISOString(),
            memoryUsage: 78,
            cpuUsage: 5
          },
          {
            id: 'ext_llm',
            name: 'LLM Provider Manager',
            version: '3.0.1',
            status: 'active',
            category: 'AI',
            description: 'Manages multiple LLM providers',
            author: 'AI Team',
            lastUpdated: new Date(Date.now() - 172800000).toISOString(),
            memoryUsage: 120,
            cpuUsage: 8
          },
          {
            id: 'ext_cache',
            name: 'Cache Optimizer',
            version: '1.2.0',
            status: 'inactive',
            category: 'Performance',
            description: 'Intelligent caching system',
            author: 'Performance Team',
            lastUpdated: new Date(Date.now() - 259200000).toISOString()
          },
          {
            id: 'ext_backup',
            name: 'Auto Backup',
            version: '2.0.0',
            status: 'error',
            category: 'System',
            description: 'Automated backup and recovery',
            author: 'System Team',
            lastUpdated: new Date(Date.now() - 345600000).toISOString()
          }
        ];

        setExtensions(mockExtensions);

        const active = mockExtensions.filter(e => e.status === 'active').length;
        const inactive = mockExtensions.filter(e => e.status === 'inactive').length;
        const errors = mockExtensions.filter(e => e.status === 'error').length;

        const categories: Record<string, number> = {};
        mockExtensions.forEach(e => {
          categories[e.category] = (categories[e.category] || 0) + 1;
        });

        setStats({
          total: mockExtensions.length,
          active,
          inactive,
          errors,
          categories
        });
      }
    } catch (error) {
      console.error('Failed to load extensions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadExtensions();
    const interval = setInterval(loadExtensions, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'inactive':
        return <Square className="h-4 w-4 text-gray-400" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-600">Active</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Inactive</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const filteredExtensions = activeTab === 'all'
    ? extensions
    : extensions.filter(e => e.status === activeTab);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Puzzle className="h-5 w-5" />
              Extension Dashboard
            </div>
            <Button onClick={loadExtensions} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage and monitor all system extensions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Stats Overview */}
          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Total Extensions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Active</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Inactive</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-600">{stats.inactive}</div>
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

          {/* Categories Breakdown */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-sm">Extensions by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats.categories).map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{category}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-32 bg-muted rounded-full h-2">
                        <div
                          className="bg-primary rounded-full h-2"
                          style={{ width: `${(count / stats.total) * 100}%` }}
                        />
                      </div>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Extensions List */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All ({stats.total})</TabsTrigger>
              <TabsTrigger value="active">Active ({stats.active})</TabsTrigger>
              <TabsTrigger value="inactive">Inactive ({stats.inactive})</TabsTrigger>
              <TabsTrigger value="error">Errors ({stats.errors})</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="space-y-3 mt-4">
              <ScrollArea className="h-[400px]">
                {filteredExtensions.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center text-muted-foreground">
                      No extensions found
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {filteredExtensions.map((ext) => (
                      <Card key={ext.id}>
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-sm flex items-center gap-2">
                                {getStatusIcon(ext.status)}
                                {ext.name}
                                <Badge variant="outline" className="ml-2">{ext.version}</Badge>
                              </CardTitle>
                              <CardDescription className="mt-1">
                                {ext.description}
                              </CardDescription>
                              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                <span>By {ext.author}</span>
                                <span>•</span>
                                <span>Category: {ext.category}</span>
                                <span>•</span>
                                <span>Updated: {new Date(ext.lastUpdated).toLocaleDateString()}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {getStatusBadge(ext.status)}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              {ext.memoryUsage !== undefined && (
                                <div className="text-sm">
                                  <span className="text-muted-foreground">Memory: </span>
                                  <span className="font-medium">{ext.memoryUsage}MB</span>
                                </div>
                              )}
                              {ext.cpuUsage !== undefined && (
                                <div className="text-sm">
                                  <span className="text-muted-foreground">CPU: </span>
                                  <span className="font-medium">{ext.cpuUsage}%</span>
                                </div>
                              )}
                            </div>
                            <div className="flex gap-2">
                              {ext.status === 'active' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => onExtensionToggle?.(ext.id, false)}
                                >
                                  <Square className="h-4 w-4 mr-2" />
                                  Stop
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => onExtensionToggle?.(ext.id, true)}
                                >
                                  <Play className="h-4 w-4 mr-2" />
                                  Start
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => onExtensionSettings?.(ext.id)}
                              >
                                <Settings className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Compact Extension Dashboard - Minimal version for sidebar/widgets
 */
export function CompactExtensionDashboard() {
  const [stats, setStats] = useState({ total: 0, active: 0, errors: 0 });

  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetch('/api/extensions/stats');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        } else {
          setStats({ total: 5, active: 3, errors: 1 });
        }
      } catch (error) {
        setStats({ total: 5, active: 3, errors: 1 });
      }
    };

    loadStats();
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Package className="h-4 w-4" />
          Extensions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Total</span>
            <Badge variant="outline">{stats.total}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Active</span>
            <Badge variant="default" className="bg-green-600">{stats.active}</Badge>
          </div>
          {stats.errors > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Errors</span>
              <Badge variant="destructive">{stats.errors}</Badge>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export { ExtensionDashboard };
export type { ExtensionDashboardProps };
