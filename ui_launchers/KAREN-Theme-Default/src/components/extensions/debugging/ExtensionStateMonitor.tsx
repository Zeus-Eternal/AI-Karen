"use client";

/**
 * Extension State Monitor
 *
 * Real-time monitoring of extension state, configuration, and runtime environment
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  Database,
  Settings,
  Code,
  RefreshCw,
  Copy,
  CheckCircle,
  XCircle,
  Clock,
  HardDrive
} from 'lucide-react';

interface StateSnapshot {
  timestamp: string;
  state: Record<string, any>;
  memorySize: number;
  stateKeys: number;
}

interface ConfigEntry {
  key: string;
  value: any;
  type: string;
  isDefault: boolean;
}

interface EnvironmentVariable {
  key: string;
  value: string;
  source: 'system' | 'extension' | 'runtime';
}

interface RuntimeInfo {
  version: string;
  platform: string;
  nodeVersion: string;
  v8Version: string;
  uptime: number;
  pid: number;
}

export interface ExtensionStateMonitorProps {
  extensionId: string;
  refreshInterval?: number;
}

export default function ExtensionStateMonitor({
  extensionId,
  refreshInterval = 3000
}: ExtensionStateMonitorProps) {
  const [stateSnapshots, setStateSnapshots] = useState<StateSnapshot[]>([]);
  const [config, setConfig] = useState<ConfigEntry[]>([]);
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([]);
  const [runtime, setRuntime] = useState<RuntimeInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('state');

  const loadStateData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/extensions/${extensionId}/state`);
      if (response.ok) {
        const data = await response.json();
        setStateSnapshots(data.snapshots);
        setConfig(data.config);
        setEnvVars(data.environment);
        setRuntime(data.runtime);
      } else {
        // Fallback mock data
        const mockSnapshot: StateSnapshot = {
          timestamp: new Date().toISOString(),
          state: {
            initialized: true,
            activeConnections: 3,
            processingQueue: ['task-1', 'task-2'],
            lastHeartbeat: new Date(Date.now() - 1000).toISOString(),
            cache: {
              size: 1024,
              hits: 450,
              misses: 50
            },
            metrics: {
              requestsProcessed: 1250,
              errors: 3,
              averageResponseTime: 145
            }
          },
          memorySize: 2048,
          stateKeys: 6
        };

        const mockConfig: ConfigEntry[] = [
          { key: 'debug', value: true, type: 'boolean', isDefault: false },
          { key: 'timeout', value: 30000, type: 'number', isDefault: true },
          { key: 'apiEndpoint', value: 'https://api.example.com', type: 'string', isDefault: false },
          { key: 'maxRetries', value: 3, type: 'number', isDefault: true },
          { key: 'enableCache', value: true, type: 'boolean', isDefault: false },
          { key: 'logLevel', value: 'info', type: 'string', isDefault: false }
        ];

        const mockEnv: EnvironmentVariable[] = [
          { key: 'NODE_ENV', value: 'production', source: 'system' },
          { key: 'EXT_API_KEY', value: '***hidden***', source: 'extension' },
          { key: 'RUNTIME_MODE', value: 'optimized', source: 'runtime' },
          { key: 'MAX_MEMORY', value: '512MB', source: 'extension' }
        ];

        const mockRuntime: RuntimeInfo = {
          version: '1.0.0',
          platform: 'linux',
          nodeVersion: 'v20.11.0',
          v8Version: '11.3.244.8',
          uptime: Date.now() - 86400000 * 5,
          pid: 12345
        };

        setStateSnapshots([mockSnapshot, ...stateSnapshots.slice(0, 19)]);
        setConfig(mockConfig);
        setEnvVars(mockEnv);
        setRuntime(mockRuntime);
      }
    } catch (error) {
      console.error('Failed to load state data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStateData();
    const interval = setInterval(loadStateData, refreshInterval);
    return () => clearInterval(interval);
  }, [extensionId, refreshInterval]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatUptime = (ms: number) => {
    const days = Math.floor(ms / 86400000);
    const hours = Math.floor((ms % 86400000) / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const latestSnapshot = stateSnapshots[0];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Extension State Monitor
            </div>
            <Button onClick={loadStateData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Real-time state monitoring (Updates every {refreshInterval / 1000}s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="state">
                <Database className="h-4 w-4 mr-2" />
                State
              </TabsTrigger>
              <TabsTrigger value="config">
                <Settings className="h-4 w-4 mr-2" />
                Config
              </TabsTrigger>
              <TabsTrigger value="environment">
                <Code className="h-4 w-4 mr-2" />
                Environment
              </TabsTrigger>
              <TabsTrigger value="runtime">
                <Activity className="h-4 w-4 mr-2" />
                Runtime
              </TabsTrigger>
            </TabsList>

            {/* State Tab */}
            <TabsContent value="state" className="space-y-4">
              {latestSnapshot && (
                <>
                  <div className="grid md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Memory Size</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{latestSnapshot.memorySize} bytes</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">State Keys</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{latestSnapshot.stateKeys}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Last Update</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm">
                          {new Date(latestSnapshot.timestamp).toLocaleTimeString()}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm">Current State</CardTitle>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(JSON.stringify(latestSnapshot.state, null, 2))}
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[400px]">
                        <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
                          {JSON.stringify(latestSnapshot.state, null, 2)}
                        </pre>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">State History</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {stateSnapshots.slice(0, 5).map((snapshot, index) => (
                          <div key={snapshot.timestamp} className="flex items-center justify-between p-2 border rounded">
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">
                                {new Date(snapshot.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{snapshot.stateKeys} keys</Badge>
                              <Badge variant="outline">{snapshot.memorySize}B</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Config Tab */}
            <TabsContent value="config" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Configuration Settings</CardTitle>
                  <CardDescription>
                    {config.filter(c => !c.isDefault).length} custom • {config.filter(c => c.isDefault).length} default
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {config.map((entry) => (
                      <div key={entry.key} className="flex items-center justify-between p-3 border rounded">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm font-medium">{entry.key}</span>
                            {!entry.isDefault && (
                              <Badge variant="secondary" className="text-xs">Custom</Badge>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            Type: {entry.type}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {typeof entry.value === 'object'
                              ? JSON.stringify(entry.value)
                              : String(entry.value)}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(String(entry.value))}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Environment Tab */}
            <TabsContent value="environment" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Environment Variables</CardTitle>
                  <CardDescription>
                    Extension runtime environment configuration
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {envVars.map((envVar) => (
                      <div key={envVar.key} className="flex items-center justify-between p-3 border rounded">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm font-medium">{envVar.key}</span>
                            <Badge variant="outline" className="text-xs">
                              {envVar.source}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {envVar.value}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(envVar.value)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Runtime Tab */}
            <TabsContent value="runtime" className="space-y-4">
              {runtime && (
                <>
                  <div className="grid md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Version</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{runtime.version}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Platform</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{runtime.platform}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm text-muted-foreground">Uptime</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-xl font-bold">{formatUptime(runtime.uptime)}</div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Runtime Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 border rounded">
                          <span className="text-sm font-medium">Node.js Version</span>
                          <code className="text-sm bg-muted px-2 py-1 rounded">{runtime.nodeVersion}</code>
                        </div>
                        <div className="flex items-center justify-between p-3 border rounded">
                          <span className="text-sm font-medium">V8 Engine Version</span>
                          <code className="text-sm bg-muted px-2 py-1 rounded">{runtime.v8Version}</code>
                        </div>
                        <div className="flex items-center justify-between p-3 border rounded">
                          <span className="text-sm font-medium">Process ID</span>
                          <code className="text-sm bg-muted px-2 py-1 rounded">{runtime.pid}</code>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { ExtensionStateMonitor };
export type { ExtensionStateMonitorProps, StateSnapshot, ConfigEntry, EnvironmentVariable, RuntimeInfo };
