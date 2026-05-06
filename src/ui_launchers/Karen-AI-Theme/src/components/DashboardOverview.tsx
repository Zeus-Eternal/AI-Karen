"use client";

import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  BarChart,
  Bot,
  Brain,
  CheckCircle2,
  Database,
  Info,
  Layers,
  LayoutDashboard,
  Loader2,
  Puzzle,
  RefreshCw,
  Server,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { NormalizedRuntimeInventory } from '@/lib/model-runtime-inventory';

interface SystemHealthSummary {
  status: string;
  expression_engine: {
    active: string;
    healthy: boolean;
    fallback_level: number;
    degraded: boolean;
  };
  providers: {
    total: number;
    healthy: number;
    configured: number;
  };
  memory: {
    status: string;
    usage_percent: number;
  };
  database: {
    status: string;
    total_operations: number;
  };
  plugins: {
    active: number;
    failed: number;
  };
}

export default function DashboardOverview() {
  const [health, setHealth] = useState<SystemHealthSummary | null>(null);
  const [modelSettings, setModelSettings] = useState<NormalizedRuntimeInventory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch real data from backend endpoints
      const [settingsRes, runtimeRes, dbRes, pluginsRes] = await Promise.all([
        apiClient.get<any>('/api/settings/model'),
        apiClient.get<any>('/api/admin/runtime/status').catch(() => ({})),
        apiClient.get<any>('/api/admin/database/overview').catch(() => ({})),
        apiClient.get<any>('/api/plugins/management/').catch(() => ({ plugins: [] })),
      ]);

      setModelSettings(settingsRes);

      // Extract provider health from model settings
      const providers = settingsRes.providers || [];
      const configuredProviders = providers.filter((p: any) => p.is_configured);
      const healthyProviders = providers.filter((p: any) => p.healthy);
      const unconfiguredProviders = providers.filter((p: any) => !p.is_configured);
      const unhealthyProviders = configuredProviders.filter((p: any) => !p.healthy);

      // ... (rest of data extraction)

  useEffect(() => {
    void loadData();
    const interval = setInterval(() => void loadData(), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (isLoading && !health) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive/20 bg-destructive/5">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p className="font-semibold">{error}</p>
          </div>
          <Button variant="outline" size="sm" className="mt-4" onClick={() => void loadData()}>
            Retry Connection
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
          <p className="text-muted-foreground italic">Real-time status of Karen's cognitive and runtime infrastructure.</p>
        </div>
        <Button variant="ghost" size="sm" className="gap-2" onClick={() => void loadData()}>
          <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Expression Engine Health */}
        <Card className="bg-gradient-to-br from-background to-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Logic Engine</CardTitle>
            <Zap className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold truncate uppercase">{health?.expression_engine.active}</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={health?.expression_engine.healthy ? "default" : "destructive"} className="h-4 text-[8px]">
                {health?.expression_engine.healthy ? "HEALTHY" : "UNHEALTHY"}
              </Badge>
              {health?.expression_engine.degraded && (
                <Badge variant="outline" className="h-4 text-[8px] border-amber-500 text-amber-600 bg-amber-50">
                  DEGRADED
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Provider Availability */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Providers</CardTitle>
            <Server className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health?.providers.healthy} / {health?.providers.configured}</div>
            <p className="text-[10px] text-muted-foreground mt-1 uppercase font-semibold">
              {health?.providers.total} Total Registered
            </p>
            <Progress value={(health?.providers.healthy || 0) / (health?.providers.configured || 1) * 100} className="h-1 mt-2" />
          </CardContent>
        </Card>

        {/* Memory Health */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Cognitive Memory</CardTitle>
            <Brain className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold uppercase">{health?.memory.status}</div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-muted-foreground uppercase">Usage</span>
              <span className="text-[10px] font-mono">{health?.memory.usage_percent}%</span>
            </div>
            <Progress value={health?.memory.usage_percent} className="h-1 mt-2" />
          </CardContent>
        </Card>

        {/* Database Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Storage Tiers</CardTitle>
            <Database className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold uppercase">{health?.database.status}</div>
            <p className="text-[10px] text-muted-foreground mt-1 uppercase font-semibold">
              {health?.database.total_operations.toLocaleString()} Ops handled
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-7">
        {/* Selected Provider/Model Details */}
        <Card className="md:col-span-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" /> Active Runtime Truth
            </CardTitle>
            <CardDescription>Primary model and fallback hierarchy currently being used for chat.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border p-4 bg-muted/10">
                <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest mb-1">Active Provider</p>
                <p className="text-lg font-bold uppercase">{modelSettings?.selected_provider}</p>
              </div>
              <div className="rounded-xl border p-4 bg-muted/10">
                <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest mb-1">Active Model</p>
                <p className="text-lg font-bold truncate" title={modelSettings?.selected_model}>{modelSettings?.selected_model}</p>
              </div>
            </div>

            <div className="space-y-2">
               <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest flex items-center gap-1">
                 <Activity className="h-3 w-3" /> Fallback Hierarchy
               </p>
               <div className="flex flex-wrap gap-2">
                 {(modelSettings as any)?.fallback_hierarchy?.map((p: string, i: number) => (
                   <div key={p} className="flex items-center gap-2">
                     <Badge variant={i === 0 ? "default" : "outline"} className="h-6 font-mono text-[10px]">
                       {p}
                     </Badge>
                     {i < (modelSettings as any).fallback_hierarchy.length - 1 && (
                       <span className="text-muted-foreground">→</span>
                     )}
                   </div>
                 )) || (
                   <span className="text-xs text-muted-foreground">Default system policy active</span>
                 )}
               </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="space-y-2">
                <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-green-500" /> Configured
                </p>
                <div className="flex flex-wrap gap-1">
                  {modelSettings?.providers?.filter(p => p.is_configured).map(p => (
                    <Badge key={p.id} variant="secondary" className="text-[8px] h-4 uppercase">
                      {p.display_name}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest flex items-center gap-1">
                  <AlertCircle className="h-3 w-3 text-muted-foreground" /> Needs Setup
                </p>
                <div className="flex flex-wrap gap-1">
                  {modelSettings?.providers?.filter(p => !p.is_configured).map(p => (
                    <Badge key={p.id} variant="outline" className="text-[8px] h-4 uppercase opacity-60">
                      {p.display_name}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Plugin/Tool Status */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Puzzle className="h-5 w-5 text-primary" /> Extension Ecosystem
            </CardTitle>
            <CardDescription>Status of loaded plugins and automated tools.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
             <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-bold">Active Plugins</p>
                  <p className="text-[10px] text-muted-foreground">Extensions successfully loaded</p>
                </div>
                <div className="text-2xl font-bold">{health?.plugins.active}</div>
             </div>
             <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-bold">Failed Loads</p>
                  <p className="text-[10px] text-muted-foreground">Plugins requiring attention</p>
                </div>
                <div className="text-2xl font-bold text-destructive">{health?.plugins.failed}</div>
             </div>
             
             <div className="rounded-lg bg-primary/5 p-3 flex items-start gap-3">
               <Info className="h-4 w-4 text-primary mt-0.5" />
               <p className="text-[10px] leading-relaxed italic">
                 Tools are automatically discovered from the `src/ai_karen_engine/tools` registry and mapped to active agent capabilities.
               </p>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
