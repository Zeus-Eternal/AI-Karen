"use client";

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, OctagonAlert, RefreshCw, ShieldCheck } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import {
  getSystemExtensionHealth,
  listSystemExtensions,
  updateSystemExtensionState,
} from '@/services/extensions/systemExtensionService';
import type {
  ExtensionHealthSummary,
  ExtensionRegistryEntry,
} from '@/services/extensions/types';

export type ExtensionHealthState = 'green' | 'yellow' | 'red' | 'unknown';

export interface SystemExtensionCardData {
  id: string;
  internalName: string;
  displayName: string;
  description: string;
  category: string;
  version: string;
  status: string;
  enabled: boolean;
  loadedAt?: Date | null;
  lastHealthCheck?: Date | null;
  errorMessage?: string | null;
  capabilities: string[];
  tags: string[];
  resources: {
    memory?: number;
    cpu?: number;
    disk?: number;
  };
  health: ExtensionHealthState;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  active: 'default',
  inactive: 'secondary',
  loading: 'outline',
  error: 'destructive',
};

const healthBadgeStyles: Record<ExtensionHealthState, { label: string; className: string }> = {
  green: {
    label: 'Healthy',
    className: 'border-emerald-200 bg-emerald-100 text-emerald-700',
  },
  yellow: {
    label: 'Degraded',
    className: 'border-amber-200 bg-amber-100 text-amber-700',
  },
  red: {
    label: 'Critical',
    className: 'border-red-200 bg-red-100 text-red-700',
  },
  unknown: {
    label: 'Unknown',
    className: 'border-muted bg-muted text-muted-foreground',
  },
};

function toDate(value?: number | string | null): Date | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return new Date(value * 1000);
  }
  if (typeof value === 'string' && value.trim().length > 0) {
    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return new Date(parsed);
    }
  }
  return null;
}

function extractCapabilities(capabilities?: Record<string, boolean>): string[] {
  if (!capabilities) {
    return [];
  }

  const labels: Record<string, string> = {
    provides_ui: 'UI components',
    provides_api: 'API endpoints',
    provides_background_tasks: 'Background tasks',
    provides_webhooks: 'Webhooks',
    provides_mcp_tools: 'MCP tools',
  };

  return Object.entries(capabilities)
    .filter(([, enabled]) => Boolean(enabled))
    .map(([key]) => labels[key] ?? key.replace(/_/g, ' '));
}

function extractResources(resources?: Record<string, number>) {
  if (!resources) {
    return {} as SystemExtensionCardData['resources'];
  }

  return {
    memory: resources.max_memory_mb ?? resources.memory ?? undefined,
    cpu: resources.max_cpu_percent ?? resources.cpu ?? undefined,
    disk: resources.max_disk_mb ?? resources.disk ?? undefined,
  } satisfies SystemExtensionCardData['resources'];
}

function mapExtensions(
  records: Record<string, ExtensionRegistryEntry>,
  healthSummary: ExtensionHealthSummary | null,
): SystemExtensionCardData[] {
  const extensionHealth = healthSummary?.extension_health ?? {};
  const lastChecks = healthSummary?.last_check_times ?? {};

  return Object.values(records).map((record) => {
    const normalizedStatus = record.status?.toLowerCase?.() ?? 'unknown';

    return {
      id: record.name,
      internalName: record.name,
      displayName: record.manifest.display_name || record.name,
      description: record.manifest.description || 'No description provided.',
      category: record.manifest.category || 'uncategorized',
      version: record.version,
      status: normalizedStatus,
      enabled: normalizedStatus === 'active',
      loadedAt: toDate(record.loaded_at),
      lastHealthCheck: toDate(lastChecks[record.name]),
      errorMessage: record.error_message ?? null,
      capabilities: extractCapabilities(record.manifest.capabilities as Record<string, boolean> | undefined),
      tags: Array.isArray(record.manifest.tags) ? record.manifest.tags : [],
      resources: extractResources(record.manifest.resources as Record<string, number> | undefined),
      health: (extensionHealth[record.name] as ExtensionHealthState | undefined) ?? 'unknown',
    } satisfies SystemExtensionCardData;
  });
}

export default function SystemExtensionsList() {
  const { toast } = useToast();
  const [extensions, setExtensions] = useState<SystemExtensionCardData[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [totalCount, setTotalCount] = useState(0);
  const [health, setHealth] = useState<ExtensionHealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const dateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      }),
    [],
  );

  const summaryEntries = useMemo(() => {
    const preferredOrder = ['active', 'inactive', 'loading', 'error'];
    const remaining = Object.keys(summary).filter((key) => !preferredOrder.includes(key));
    return [...preferredOrder, ...remaining].map((key) => ({
      key,
      label: key.replace(/_/g, ' '),
      value: summary[key] ?? 0,
    }));
  }, [summary]);

  const fetchExtensions = useCallback(async () => {
    setLoading(true);
    try {
      const [registryRes, healthRes] = await Promise.all([
        listSystemExtensions(),
        getSystemExtensionHealth(),
      ]);

      if (!registryRes.success || !registryRes.data) {
        throw new Error(
          registryRes.error?.message ?? 'Unable to load system extensions.',
        );
      }

      const registryData = registryRes.data;
      const healthData = healthRes.success ? healthRes.data ?? null : null;

      if (!healthRes.success && healthRes.error) {
        toast({
          variant: 'destructive',
          title: 'Extension health unavailable',
          description:
            healthRes.error.message ?? 'Unable to load extension health status.',
        });
      }

      setSummary(registryData.summary ?? {});
      setTotalCount(registryData.total_count ?? 0);
      setHealth(healthData);
      setExtensions(mapExtensions(registryData.extensions ?? {}, healthData));
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load system extensions.';
      setError(message);
      setExtensions([]);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const handleToggle = useCallback(
    async (extension: SystemExtensionCardData, nextEnabled: boolean) => {
      setUpdating(extension.id);
      try {
        const response = await updateSystemExtensionState(
          extension.internalName,
          nextEnabled,
        );

        if (!response.success) {
          throw new Error(
            response.error?.message ?? 'Unable to update extension state.',
          );
        }

        toast({
          title: nextEnabled ? 'Extension enabled' : 'Extension disabled',
          description: `${extension.displayName} is now ${
            nextEnabled ? 'active' : 'inactive'
          }.`,
        });

        await fetchExtensions();
      } catch (err) {
        toast({
          variant: 'destructive',
          title: 'Extension update failed',
          description:
            err instanceof Error
              ? err.message
              : 'Unable to update extension state.',
        });
      } finally {
        setUpdating(null);
      }
    },
    [fetchExtensions, toast],
  );

  useEffect(() => {
    fetchExtensions();
  }, [fetchExtensions]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold">System extensions</h2>
          <p className="text-sm text-muted-foreground">
            Monitor Kari’s core extension health, lifecycle state, and resource
            allocations.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchExtensions}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Refreshing
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </>
          )}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Unable to load extensions</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {(totalCount > 0 || (health && extensions.length > 0)) && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">
              Production health overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs uppercase text-muted-foreground">Total</p>
                <p className="text-2xl font-semibold">{totalCount}</p>
              </div>
              {summaryEntries.map((entry) => (
                <div key={entry.key}>
                  <p className="text-xs uppercase text-muted-foreground">
                    {entry.label}
                  </p>
                  <p className="text-2xl font-semibold">{entry.value}</p>
                </div>
              ))}
            </div>

            {health && (
              <div>
                <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                  <span>Healthy extensions</span>
                  <span>{Math.round(health.health_percentage)}%</span>
                </div>
                <Progress
                  value={Math.min(100, Math.max(0, health.health_percentage))}
                  className="mt-2"
                />
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    {health.healthy_extensions} healthy
                  </span>
                  <span className="flex items-center gap-1">
                    <OctagonAlert className="h-3.5 w-3.5" />
                    {health.unhealthy_extensions} attention needed
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[0, 1].map((index) => (
            <Card key={index} className="border-dashed">
              <CardHeader className="space-y-3">
                <Skeleton className="h-5 w-1/2" />
                <Skeleton className="h-4 w-3/4" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-3/5" />
              </CardContent>
              <CardFooter className="flex items-center justify-between">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-8 w-24" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : extensions.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">
              No system extensions detected
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Register an extension or deploy one from the marketplace to see it in
            this dashboard.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {extensions.map((extension) => {
            const healthVariant = healthBadgeStyles[extension.health];
            const statusVariant =
              statusVariantMap[extension.status] ?? 'secondary';

            return (
              <Card key={extension.id} className="flex flex-col justify-between">
                <CardHeader className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <CardTitle className="text-base font-semibold">
                      {extension.displayName}
                    </CardTitle>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant={statusVariant}
                        className="capitalize"
                      >
                        {extension.status.replace(/_/g, ' ')}
                      </Badge>
                      <Badge variant="outline" className={healthVariant.className}>
                        {healthVariant.label}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {extension.description}
                  </p>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span>v{extension.version}</span>
                    <span>•</span>
                    <span className="capitalize">{extension.category}</span>
                    {extension.loadedAt && (
                      <>
                        <span>•</span>
                        <span>
                          Loaded {dateFormatter.format(extension.loadedAt)}
                        </span>
                      </>
                    )}
                    {extension.lastHealthCheck && (
                      <>
                        <span>•</span>
                        <span>
                          Health check {dateFormatter.format(extension.lastHealthCheck)}
                        </span>
                      </>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  {extension.capabilities.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
                        Capabilities
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {extension.capabilities.map((capability) => (
                          <Badge key={capability} variant="outline" className="text-xs">
                            {capability}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {(extension.resources.memory ||
                    extension.resources.cpu ||
                    extension.resources.disk) && (
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div>
                        <p className="text-xs uppercase text-muted-foreground">
                          Memory
                        </p>
                        <p className="font-medium">
                          {extension.resources.memory
                            ? `${extension.resources.memory} MB`
                            : '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs uppercase text-muted-foreground">
                          CPU
                        </p>
                        <p className="font-medium">
                          {extension.resources.cpu
                            ? `${extension.resources.cpu}%`
                            : '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs uppercase text-muted-foreground">
                          Storage
                        </p>
                        <p className="font-medium">
                          {extension.resources.disk
                            ? `${extension.resources.disk} MB`
                            : '—'}
                        </p>
                      </div>
                    </div>
                  )}

                  {extension.tags.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
                        Tags
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {extension.tags.map((tag) => (
                          <Badge
                            key={tag}
                            variant="secondary"
                            className="text-xs capitalize"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {extension.errorMessage && (
                    <Alert variant="destructive">
                      <AlertTitle>Startup issue</AlertTitle>
                      <AlertDescription>{extension.errorMessage}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
                <CardFooter className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-muted-foreground">Enabled</span>
                    <Switch
                      checked={extension.enabled}
                      disabled={updating === extension.id}
                      onCheckedChange={(checked) => handleToggle(extension, checked)}
                      aria-label={`Toggle ${extension.displayName}`}
                    />
                    {updating === extension.id && (
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    )}
                  </div>
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/extensions/${encodeURIComponent(extension.internalName)}`}>
                      Manage
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
