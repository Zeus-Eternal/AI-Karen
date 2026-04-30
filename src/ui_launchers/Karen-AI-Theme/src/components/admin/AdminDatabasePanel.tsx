"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Database,
  HardDrive,
  Layers3,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Workflow,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ComponentHealthValue =
  | boolean
  | string
  | {
      status?: string | null;
      connected?: boolean | null;
      healthy?: boolean | null;
      ready?: boolean | null;
      available?: boolean | null;
      message?: string | null;
      reason?: string | null;
      error?: string | null;
      response_time_ms?: number | null;
      latency_ms?: number | null;
      checked_at?: string | null;
      [key: string]: unknown;
    };

type HealthSnapshot = {
  status: string;
  timestamp?: string;
  services?: Record<string, ComponentHealthValue>;
  components?: Record<string, ComponentHealthValue>;
};

type ObservabilityAlert = {
  id: string;
  title: string;
  description: string;
  type: "info" | "warning" | "update" | "error";
  timestamp: string;
};

type ObservabilitySnapshot = {
  generated_at: string;
  memory?: {
    available: boolean;
    pending_writebacks: number;
    active_shard_links: number;
    feedback_metrics: Record<string, unknown>;
    service_metrics: Record<string, unknown>;
  };
  alerts?: ObservabilityAlert[];
};

type StorageTier = {
  label: string;
  key: string;
  aliases: string[];
  description: string;
};

type NormalizedComponentStatus = {
  status: string;
  message: string | null;
  responseTimeMs: number | null;
  checkedAt: string | null;
};

const STORAGE_TIERS: StorageTier[] = [
  {
    label: "PostgreSQL",
    key: "postgres",
    aliases: ["postgres", "postgresql", "database", "db"],
    description: "Durable relational system-of-record",
  },
  {
    label: "Redis",
    key: "redis",
    aliases: ["redis", "cache"],
    description: "Transient/session speed layer",
  },
  {
    label: "Milvus",
    key: "milvus",
    aliases: ["milvus", "vector", "vector_db", "vectordb"],
    description: "Semantic recall and vector retrieval",
  },
  {
    label: "Elasticsearch",
    key: "elasticsearch",
    aliases: ["elasticsearch", "elastic", "search"],
    description: "Indexed search augmentation",
  },
];

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in to inspect backend database operations.";
    }

    if (error.status === 403) {
      return "This session is not authorized to inspect backend database operations.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

const formatDateTime = (value: string | null | undefined) => {
  if (!value) {
    return "Not recorded";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

const normalizeStatusValue = (value: ComponentHealthValue | undefined): NormalizedComponentStatus => {
  if (value == null) {
    return {
      status: "unknown",
      message: null,
      responseTimeMs: null,
      checkedAt: null,
    };
  }

  if (typeof value === "string") {
    return {
      status: value,
      message: null,
      responseTimeMs: null,
      checkedAt: null,
    };
  }

  if (typeof value === "boolean") {
    return {
      status: value ? "healthy" : "unavailable",
      message: null,
      responseTimeMs: null,
      checkedAt: null,
    };
  }

  const status =
    typeof value.status === "string" && value.status.trim()
      ? value.status
      : value.connected || value.healthy || value.ready || value.available
        ? "healthy"
        : "unknown";

  return {
    status,
    message: value.message || value.reason || value.error || null,
    responseTimeMs:
      typeof value.response_time_ms === "number"
        ? value.response_time_ms
        : typeof value.latency_ms === "number"
          ? value.latency_ms
          : null,
    checkedAt: typeof value.checked_at === "string" ? value.checked_at : null,
  };
};

const getStatusVariant = (
  status: string,
): "default" | "secondary" | "destructive" | "outline" => {
  const normalized = status.toLowerCase();

  if (
    normalized === "healthy" ||
    normalized === "ok" ||
    normalized === "connected" ||
    normalized === "ready" ||
    normalized === "available"
  ) {
    return "secondary";
  }

  if (
    normalized === "unhealthy" ||
    normalized === "error" ||
    normalized === "failed" ||
    normalized === "disconnected" ||
    normalized === "unavailable"
  ) {
    return "destructive";
  }

  if (normalized === "degraded" || normalized === "warning" || normalized === "partial") {
    return "default";
  }

  return "outline";
};

const getAlertVariantClassName = (type: ObservabilityAlert["type"] | undefined) => {
  switch (type) {
    case "warning":
      return "border-yellow-500/30 bg-yellow-500/5";
    case "error":
      return "border-destructive/30 bg-destructive/5";
    case "update":
      return "border-primary/20 bg-primary/5";
    case "info":
    default:
      return "bg-muted/40";
  }
};

const findTierValue = (
  services: Record<string, ComponentHealthValue>,
  tier: StorageTier,
): ComponentHealthValue | undefined => {
  for (const alias of tier.aliases) {
    if (services[alias] !== undefined) {
      return services[alias];
    }
  }

  const entry = Object.entries(services).find(([key]) => {
    const normalizedKey = key.toLowerCase();
    return tier.aliases.some((alias) => normalizedKey.includes(alias));
  });

  return entry?.[1];
};

export default function AdminDatabasePanel() {
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [observability, setObservability] = useState<ObservabilitySnapshot | null>(null);

  const [isLoadingHealth, setIsLoadingHealth] = useState(true);
  const [isLoadingObservability, setIsLoadingObservability] = useState(true);

  const [healthAuthRequired, setHealthAuthRequired] = useState(false);
  const [healthAccessDenied, setHealthAccessDenied] = useState(false);
  const [observabilityAuthRequired, setObservabilityAuthRequired] = useState(false);
  const [observabilityAccessDenied, setObservabilityAccessDenied] = useState(false);

  const [healthError, setHealthError] = useState<string | null>(null);
  const [observabilityError, setObservabilityError] = useState<string | null>(null);

  const isLoading = isLoadingHealth || isLoadingObservability;

  const services = useMemo(() => {
    return health?.services || health?.components || {};
  }, [health?.components, health?.services]);

  const storageTierStatuses = useMemo(() => {
    return STORAGE_TIERS.map((tier) => ({
      ...tier,
      health: normalizeStatusValue(findTierValue(services, tier)),
    }));
  }, [services]);

  const loadHealth = useCallback(async () => {
    setIsLoadingHealth(true);
    setHealthAuthRequired(false);
    setHealthAccessDenied(false);
    setHealthError(null);

    try {
      const response = await apiClient.get<HealthSnapshot>("/api/health");
      setHealth(response);
    } catch (error) {
      setHealth(null);

      if (error instanceof ApiError && error.status === 401) {
        setHealthAuthRequired(true);
        return;
      }

      if (error instanceof ApiError && error.status === 403) {
        setHealthAccessDenied(true);
        return;
      }

      setHealthError(
        getErrorMessage(error, "Karen could not load backend health state."),
      );
    } finally {
      setIsLoadingHealth(false);
    }
  }, []);

  const loadObservability = useCallback(async () => {
    setIsLoadingObservability(true);
    setObservabilityAuthRequired(false);
    setObservabilityAccessDenied(false);
    setObservabilityError(null);

    try {
      const response = await apiClient.get<ObservabilitySnapshot>(
        "/api/communications-center/observability",
      );
      setObservability(response);
    } catch (error) {
      setObservability(null);

      if (error instanceof ApiError && error.status === 401) {
        setObservabilityAuthRequired(true);
        return;
      }

      if (error instanceof ApiError && error.status === 403) {
        setObservabilityAccessDenied(true);
        return;
      }

      setObservabilityError(
        getErrorMessage(
          error,
          "Karen could not load backend database operations observability.",
        ),
      );
    } finally {
      setIsLoadingObservability(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    await Promise.all([loadHealth(), loadObservability()]);
  }, [loadHealth, loadObservability]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Database Operations
            </CardTitle>
            <CardDescription>
              Backend-derived view of Karen&apos;s storage tiers, memory writeback state,
              and operational health. This panel does not bypass service boundaries with
              raw store access.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => void loadData()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </CardHeader>

        <CardContent className="space-y-4">
          {healthAuthRequired && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                Backend health is live, but this session is not authenticated.
              </AlertDescription>
            </Alert>
          )}

          {healthAccessDenied && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Health Access Restricted</AlertTitle>
              <AlertDescription>
                Backend health is available, but this session is not authorized to inspect it.
              </AlertDescription>
            </Alert>
          )}

          {observabilityAuthRequired && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                Database observability is live, but this session is not authenticated.
              </AlertDescription>
            </Alert>
          )}

          {observabilityAccessDenied && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Database Observability Restricted</AlertTitle>
              <AlertDescription>
                Backend storage and memory observability is available, but this session is
                not authorized to inspect the full operational surface.
              </AlertDescription>
            </Alert>
          )}

          {healthError && (
            <Alert className="border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Health Snapshot Unavailable</AlertTitle>
              <AlertDescription>{healthError}</AlertDescription>
            </Alert>
          )}

          {observabilityError && (
            <Alert className="border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Database Observability Unavailable</AlertTitle>
              <AlertDescription>{observabilityError}</AlertDescription>
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
                {storageTierStatuses.map((tier) => (
                  <Card key={tier.key} className="border-border/70">
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center justify-between gap-3 text-sm font-medium">
                        <span>{tier.label}</span>
                        <HardDrive className="h-4 w-4 text-primary" />
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="space-y-2">
                      <Badge variant={getStatusVariant(tier.health.status)}>
                        {tier.health.status}
                      </Badge>

                      <p className="text-xs text-muted-foreground">{tier.description}</p>

                      {tier.health.message && (
                        <p className="text-xs text-muted-foreground">
                          {tier.health.message}
                        </p>
                      )}

                      <div className="grid gap-1 text-[10px] text-muted-foreground">
                        {tier.health.responseTimeMs != null && (
                          <span>Response: {tier.health.responseTimeMs}ms</span>
                        )}
                        {tier.health.checkedAt && (
                          <span>Checked: {formatDateTime(tier.health.checkedAt)}</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {Object.keys(services).length === 0 && (
                <div className="rounded-xl border border-dashed border-border/70 p-4 text-sm text-muted-foreground">
                  No backend service/component health records were returned.
                </div>
              )}

              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Workflow className="h-4 w-4 text-primary" />
                      Memory Writeback
                    </CardTitle>
                    <CardDescription>
                      Governed persistence handoff from the backend memory layer.
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Memory service</span>
                      <Badge variant={observability?.memory?.available ? "secondary" : "outline"}>
                        {observability?.memory?.available ? "Available" : "Unavailable"}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Pending writebacks</span>
                      <span>
                        {observability?.memory?.pending_writebacks?.toLocaleString() ?? "unknown"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Active shard links</span>
                      <span>
                        {observability?.memory?.active_shard_links?.toLocaleString() ??
                          "unknown"}
                      </span>
                    </div>

                    {observability?.generated_at && (
                      <div className="pt-2 text-[10px] text-muted-foreground">
                        Generated: {formatDateTime(observability.generated_at)}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Layers3 className="h-4 w-4 text-primary" />
                      Tier Separation
                    </CardTitle>
                    <CardDescription>
                      Storage tiers remain visible as backend services, not direct UI clients.
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm text-muted-foreground">
                    {STORAGE_TIERS.map((tier) => (
                      <div key={tier.key}>
                        {tier.label}: {tier.description}
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <AlertCircle className="h-4 w-4 text-primary" />
                      Operational Alerts
                    </CardTitle>
                    <CardDescription>
                      Recent backend-generated alerts touching storage or memory flow.
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    {observability?.alerts?.slice(0, 4).length ? (
                      observability.alerts.slice(0, 4).map((alert) => (
                        <div
                          key={alert.id}
                          className={`rounded-md border p-3 ${getAlertVariantClassName(
                            alert.type,
                          )}`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="font-medium">{alert.title}</div>
                              <div className="mt-1 text-muted-foreground">
                                {alert.description}
                              </div>
                            </div>
                            <Badge variant="outline" className="text-[10px]">
                              {alert.type}
                            </Badge>
                          </div>

                          <div className="mt-2 text-[10px] text-muted-foreground">
                            {formatDateTime(alert.timestamp)}
                          </div>
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