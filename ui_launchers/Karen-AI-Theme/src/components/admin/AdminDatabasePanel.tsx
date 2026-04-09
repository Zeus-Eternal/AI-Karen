"use client";

import { useEffect, useState } from "react";
import { apiClient, ApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, AlertCircle, Loader2, ShieldAlert, HardDrive, Layers3, Workflow } from "lucide-react";

type HealthSnapshot = {
  status: string;
  timestamp?: string;
  services?: Record<string, unknown>;
  components?: Record<string, unknown>;
};

type ObservabilitySnapshot = {
  generated_at: string;
  memory: {
    available: boolean;
    pending_writebacks: number;
    active_shard_links: number;
    feedback_metrics: Record<string, unknown>;
    service_metrics: Record<string, unknown>;
  };
  alerts: Array<{
    id: string;
    title: string;
    description: string;
    type: "info" | "warning" | "update";
    timestamp: string;
  }>;
};

function getComponentStatus(payload: Record<string, unknown> | undefined, key: string): string {
  const value = payload?.[key];
  if (value == null) {
    return "Unknown";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "boolean") {
    return value ? "healthy" : "unavailable";
  }
  if (typeof value === "object" && value !== null) {
    if (typeof (value as { status?: unknown }).status === "string") {
      return (value as { status: string }).status;
    }
    if (typeof (value as { connected?: unknown }).connected === "boolean") {
      return (value as { connected: boolean }).connected ? "connected" : "disconnected";
    }
  }
  return "Unknown";
}

function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  const normalized = status.toLowerCase();
  if (normalized === "healthy" || normalized === "ok" || normalized === "connected") {
    return "secondary";
  }
  if (normalized === "unhealthy" || normalized === "error" || normalized === "disconnected" || normalized === "unavailable") {
    return "destructive";
  }
  return "outline";
}

export default function AdminDatabasePanel() {
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [observability, setObservability] = useState<ObservabilitySnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [observabilityAccessDenied, setObservabilityAccessDenied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
      setIsLoading(true);
      setAuthRequired(false);
      setObservabilityAccessDenied(false);
      try {
        const [healthResponse, observabilityResponse] = await Promise.all([
          apiClient.get<HealthSnapshot>("/api/health"),
          apiClient.get<ObservabilitySnapshot>("/api/communications-center/observability"),
        ]);
        if (!mounted) {
          return;
        }
        setHealth(healthResponse);
        setObservability(observabilityResponse);
        setLoadError(null);
      } catch (error) {
        if (!mounted) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          setAuthRequired(true);
          setLoadError(null);
        } else if (error instanceof ApiError && error.status === 403) {
          setObservabilityAccessDenied(true);
          setLoadError(null);
        } else {
          setLoadError(error instanceof Error ? error.message : "Karen could not load backend database operations state.");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void loadData();
    return () => {
      mounted = false;
    };
  }, []);

  const services = health?.services || health?.components || {};
  const storageTiers = [
    { label: "PostgreSQL", key: "postgres" },
    { label: "Redis", key: "redis" },
    { label: "Milvus", key: "milvus" },
    { label: "Elasticsearch", key: "elasticsearch" },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            Database Operations
          </CardTitle>
          <CardDescription>
            Backend-derived view of Karen&apos;s storage tiers, memory writeback state, and operational health. This panel does not bypass service boundaries with raw store access.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {authRequired && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                Backend storage and memory observability is live, but this session is not authenticated. Sign in to inspect operational state.
              </AlertDescription>
            </Alert>
          )}
          {observabilityAccessDenied && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Database Observability Restricted</AlertTitle>
              <AlertDescription>
                Backend storage and memory observability is available, but this session is not authorized to inspect the full operational surface.
              </AlertDescription>
            </Alert>
          )}
          {loadError && (
            <Alert className="border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Database Operations Unavailable</AlertTitle>
              <AlertDescription>{loadError}</AlertDescription>
            </Alert>
          )}
          {isLoading ? (
            <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading backend storage operations.
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {storageTiers.map((tier) => {
                  const status = getComponentStatus(services, tier.key);
                  return (
                    <Card key={tier.key} className="border-border/70">
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center justify-between text-sm font-medium">
                          <span>{tier.label}</span>
                          <HardDrive className="h-4 w-4 text-primary" />
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Badge variant={getStatusVariant(status)}>{status}</Badge>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Workflow className="h-4 w-4 text-primary" />
                      Memory Writeback
                    </CardTitle>
                    <CardDescription>Governed persistence handoff from the backend memory layer.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Memory service</span>
                      <Badge variant={observability?.memory.available ? "secondary" : "outline"}>
                        {observability?.memory.available ? "Available" : "Unavailable"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pending writebacks</span>
                      <span>{observability?.memory.pending_writebacks ?? 0}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Active shard links</span>
                      <span>{observability?.memory.active_shard_links ?? 0}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Layers3 className="h-4 w-4 text-primary" />
                      Tier Separation
                    </CardTitle>
                    <CardDescription>Storage tiers remain visible as backend services, not direct UI clients.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm text-muted-foreground">
                    <div>Redis: transient/session speed layer</div>
                    <div>PostgreSQL: durable relational system-of-record</div>
                    <div>Milvus: semantic recall and vector retrieval</div>
                    <div>Elasticsearch: indexed search augmentation</div>
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <AlertCircle className="h-4 w-4 text-primary" />
                      Operational Alerts
                    </CardTitle>
                    <CardDescription>Recent backend-generated alerts touching storage or memory flow.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {observability?.alerts?.slice(0, 4).length ? (
                      observability.alerts.slice(0, 4).map((alert) => (
                        <div key={alert.id} className="rounded-md border bg-muted/40 p-3">
                          <div className="font-medium">{alert.title}</div>
                          <div className="mt-1 text-muted-foreground">{alert.description}</div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-md border border-dashed p-4 text-muted-foreground">
                        No recent backend alerts affecting storage operations.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
