"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Cpu,
  HardDrive,
  Loader2,
  RefreshCw,
  Server,
  Shield,
  XCircle,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
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
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

type ServiceHealthValue =
  | boolean
  | string
  | {
      status?: string;
      connected?: boolean;
      healthy?: boolean;
      ready?: boolean;
      message?: string | null;
      reason?: string | null;
      error?: string | null;
      response_time_ms?: number | null;
      latency_ms?: number | null;
      checked_at?: string | null;
      [key: string]: unknown;
    };

type NlpAssetsHealth = {
  spacy_installed: boolean;
  spacy_model_name: string;
  spacy_model_installed: boolean;
  nltk_installed: boolean;
  nltk_resources: Record<string, boolean>;
  runtime_downloads_enabled: boolean;
  ready: boolean;
};

type ResourceMetric = {
  used?: number | null;
  total?: number | null;
  percent?: number | null;
  unit?: string | null;
  label?: string | null;
  status?: string | null;
};

type SystemMetrics = {
  memory?: ResourceMetric | null;
  cpu?: ResourceMetric | null;
  disk?: ResourceMetric | null;
  gpu?: ResourceMetric | null;
  [key: string]: ResourceMetric | null | undefined;
};

type EnvironmentConfigValue = {
  key: string;
  description?: string | null;
  value?: string | boolean | number | null;
  default_value?: string | boolean | number | null;
  source?: string | null;
  editable?: boolean | null;
  secret?: boolean | null;
};

type HealthData = {
  status: string;
  timestamp?: string;
  services?: Record<string, ServiceHealthValue>;
  nlp_assets?: NlpAssetsHealth;
  system_metrics?: SystemMetrics;
  environment_config?: EnvironmentConfigValue[];
  config?: {
    environment?: EnvironmentConfigValue[];
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

type ConfigReference = {
  key: string;
  description: string;
  defaultValue: string;
};

type NormalizedService = {
  name: string;
  healthy: boolean;
  status: string;
  message: string | null;
  responseTimeMs: number | null;
  checkedAt: string | null;
};

const DEFAULT_ENV_CONFIG: ConfigReference[] = [
  {
    key: "AUTH_MODE",
    description: "Authentication mode",
    defaultValue: "hybrid",
  },
  {
    key: "CORS_ORIGINS",
    description: "Allowed CORS origins",
    defaultValue: "auto-detected",
  },
  {
    key: "ENABLE_RATE_LIMITING",
    description: "Rate limiting enabled",
    defaultValue: "false",
  },
  {
    key: "COPILOT_ASSIST_TIMEOUT_SECONDS",
    description: "LLM response timeout",
    defaultValue: "45",
  },
  {
    key: "KARI_AUTO_DOWNLOAD_LLM",
    description: "Auto-download models",
    defaultValue: "false",
  },
  {
    key: "KARI_FAST_STARTUP",
    description: "Skip heavy init on startup",
    defaultValue: "true",
  },
  {
    key: "WARMUP_LLM",
    description: "Warm up LLM on startup",
    defaultValue: "false",
  },
  {
    key: "AI_KAREN_ENABLE_MODEL_LIBRARY",
    description: "Enable model library",
    defaultValue: "false",
  },
  {
    key: "KARI_ENABLE_NLTK_DOWNLOADS",
    description: "Allow runtime NLTK downloads",
    defaultValue: "false",
  },
];

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in before using admin system controls.";
    }

    if (error.status === 403) {
      return "This session is not authorized to use admin system controls.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
};

const isHealthyStatus = (status: string | undefined | null) => {
  const normalized = (status || "").toLowerCase();

  return (
    normalized === "healthy" ||
    normalized === "ok" ||
    normalized === "ready" ||
    normalized === "online" ||
    normalized === "connected"
  );
};

const isWarningStatus = (status: string | undefined | null) => {
  const normalized = (status || "").toLowerCase();

  return normalized === "degraded" || normalized === "warning" || normalized === "partial";
};

const getStatusBadgeVariant = (status: string | undefined | null, healthy?: boolean) => {
  if (healthy || isHealthyStatus(status)) {
    return "default" as const;
  }

  if (isWarningStatus(status)) {
    return "secondary" as const;
  }

  return "destructive" as const;
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

const formatPercent = (value: number | null | undefined) => {
  if (!Number.isFinite(value ?? NaN)) {
    return null;
  }

  return Math.max(0, Math.min(100, Number(value)));
};

const formatMetricValue = (value: number | null | undefined, unit?: string | null) => {
  if (!Number.isFinite(value ?? NaN)) {
    return "unknown";
  }

  const normalizedUnit = unit || "";

  if (normalizedUnit.toLowerCase() === "bytes") {
    return formatBytes(Number(value));
  }

  if (normalizedUnit === "%") {
    return `${Number(value).toFixed(1)}%`;
  }

  return `${Number(value).toLocaleString()}${normalizedUnit ? ` ${normalizedUnit}` : ""}`;
};

const formatBytes = (bytes: number) => {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, unitIndex);

  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`;
};

const normalizeService = ([name, value]: [string, ServiceHealthValue]): NormalizedService => {
  if (typeof value === "boolean") {
    return {
      name,
      healthy: value,
      status: value ? "healthy" : "unhealthy",
      message: null,
      responseTimeMs: null,
      checkedAt: null,
    };
  }

  if (typeof value === "string") {
    return {
      name,
      healthy: isHealthyStatus(value),
      status: value,
      message: null,
      responseTimeMs: null,
      checkedAt: null,
    };
  }

  if (value && typeof value === "object") {
    const status =
      typeof value.status === "string"
        ? value.status
        : value.connected || value.healthy || value.ready
          ? "healthy"
          : "unknown";

    return {
      name,
      healthy:
        isHealthyStatus(status) ||
        value.connected === true ||
        value.healthy === true ||
        value.ready === true,
      status,
      message:
        value.message ||
        value.reason ||
        value.error ||
        null,
      responseTimeMs:
        typeof value.response_time_ms === "number"
          ? value.response_time_ms
          : typeof value.latency_ms === "number"
            ? value.latency_ms
            : null,
      checkedAt: typeof value.checked_at === "string" ? value.checked_at : null,
    };
  }

  return {
    name,
    healthy: false,
    status: "unknown",
    message: null,
    responseTimeMs: null,
    checkedAt: null,
  };
};

const normalizeEnvironmentConfig = (health: HealthData | null): EnvironmentConfigValue[] => {
  const backendConfig = health?.environment_config || health?.config?.environment;

  if (Array.isArray(backendConfig) && backendConfig.length > 0) {
    return backendConfig.map((item) => ({
      key: item.key,
      description: item.description || "Backend configuration value",
      value: item.secret ? "••••••••" : item.value,
      default_value: item.default_value,
      source: item.source || "backend",
      editable: item.editable ?? false,
      secret: item.secret ?? false,
    }));
  }

  return DEFAULT_ENV_CONFIG.map((item) => ({
    key: item.key,
    description: item.description,
    value: null,
    default_value: item.defaultValue,
    source: "reference_default",
    editable: false,
    secret: false,
  }));
};

const ResourceMetricCard = ({
  title,
  icon,
  metric,
}: {
  title: string;
  icon: React.ReactNode;
  metric: ResourceMetric | null | undefined;
}) => {
  const percent = formatPercent(metric?.percent);
  const status = metric?.status || (percent == null ? "unknown" : percent >= 90 ? "warning" : "ok");
  const displayLabel = metric?.label || title;

  return (
    <div className="space-y-2 rounded-xl border p-4">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="flex items-center gap-1.5">
          {icon}
          {displayLabel}
        </span>
        <Badge variant={getStatusBadgeVariant(status)}>{status}</Badge>
      </div>

      {percent == null ? (
        <div className="rounded-lg border border-dashed p-3 text-xs text-muted-foreground">
          No backend metric reported.
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {formatMetricValue(metric?.used, metric?.unit)}
              {Number.isFinite(metric?.total ?? NaN)
                ? ` / ${formatMetricValue(metric?.total, metric?.unit)}`
                : ""}
            </span>
            <span className="font-mono">{percent.toFixed(1)}%</span>
          </div>
          <Progress value={percent} className="h-2" />
        </>
      )}
    </div>
  );
};

export default function SystemConfigPanel() {
  const { toast } = useToast();

  const [health, setHealth] = useState<HealthData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [isInstallingNlpAssets, setIsInstallingNlpAssets] = useState(false);

  const loadHealth = useCallback(async () => {
    setIsLoading(true);
    setHealthError(null);

    try {
      const response = await apiClient.get<HealthData>("/api/health");
      setHealth(response);
      setLastRefreshed(new Date());
    } catch (error) {
      const message = getErrorMessage(error, "Karen backend health is unreachable.");

      setHealth({
        status: "unreachable",
      });
      setHealthError(message);
      setLastRefreshed(new Date());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  const isHealthy = isHealthyStatus(health?.status);

  const services = useMemo(() => {
    return Object.entries(health?.services || {})
      .map(normalizeService)
      .sort((left, right) => left.name.localeCompare(right.name));
  }, [health?.services]);

  const environmentConfig = useMemo(() => {
    return normalizeEnvironmentConfig(health);
  }, [health]);

  const installNlpAssets = useCallback(async () => {
    setIsInstallingNlpAssets(true);

    try {
      await apiClient.post("/api/health/nlp-assets/install", {});
      await loadHealth();

      toast({
        title: "NLP assets install requested",
        description: "The backend completed the NLP asset install action and health was refreshed.",
      });
    } catch (error) {
      const message = getErrorMessage(error, "Could not install missing NLP assets.");

      toast({
        title: "NLP asset install failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsInstallingNlpAssets(false);
    }
  }, [loadHealth, toast]);

  return (
    <div className="space-y-6">
      <Card className={`border-2 ${isHealthy ? "border-emerald-500/30" : "border-rose-500/30"}`}>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className={`h-5 w-5 ${isHealthy ? "text-emerald-500" : "text-rose-500"}`} />
              System Health
            </CardTitle>

            <div className="flex items-center gap-2">
              {lastRefreshed && (
                <span className="text-[10px] text-muted-foreground">
                  Updated {lastRefreshed.toLocaleTimeString()}
                </span>
              )}

              <Button
                variant="ghost"
                size="icon"
                onClick={() => void loadHealth()}
                disabled={isLoading}
                className="h-8 w-8"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>

          <CardDescription>Live status of the Karen AI backend and its services.</CardDescription>
        </CardHeader>

        <CardContent>
          {healthError && (
            <Alert className="mb-4 border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Health Check Warning</AlertTitle>
              <AlertDescription>{healthError}</AlertDescription>
            </Alert>
          )}

          {isLoading && !health ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                {isHealthy ? (
                  <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                ) : (
                  <XCircle className="h-8 w-8 text-rose-500" />
                )}

                <div>
                  <p className="text-lg font-semibold capitalize">
                    {health?.status || "Unknown"}
                  </p>
                  {health?.timestamp && (
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(health.timestamp)}
                    </p>
                  )}
                </div>
              </div>

              {services.length === 0 ? (
                <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                  No service health records were returned by the backend.
                </div>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {services.map((service) => (
                    <div
                      key={service.name}
                      className={`rounded-xl border p-3 ${
                        service.healthy
                          ? "border-emerald-500/20 bg-emerald-500/5"
                          : "border-rose-500/20 bg-rose-500/5"
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {service.healthy ? (
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                        ) : (
                          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
                        )}

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-sm font-medium capitalize">
                              {service.name.replace(/_/g, " ")}
                            </p>
                            <Badge variant={getStatusBadgeVariant(service.status, service.healthy)}>
                              {service.status}
                            </Badge>
                          </div>

                          {service.message && (
                            <p className="mt-1 text-[10px] text-muted-foreground">
                              {service.message}
                            </p>
                          )}

                          <div className="mt-2 grid gap-1 text-[10px] text-muted-foreground">
                            {service.responseTimeMs != null && (
                              <span>Response: {service.responseTimeMs}ms</span>
                            )}
                            {service.checkedAt && (
                              <span>Checked: {formatDateTime(service.checkedAt)}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Server className="h-5 w-5 text-primary" />
            Resource Metrics
          </CardTitle>
          <CardDescription>
            Backend-reported resource usage. This panel no longer invents CPU or memory values.
          </CardDescription>
        </CardHeader>

        <CardContent className="grid gap-4 md:grid-cols-2">
          <ResourceMetricCard
            title="Memory Usage"
            icon={<HardDrive className="h-3.5 w-3.5" />}
            metric={health?.system_metrics?.memory}
          />

          <ResourceMetricCard
            title="CPU Usage"
            icon={<Cpu className="h-3.5 w-3.5" />}
            metric={health?.system_metrics?.cpu}
          />

          <ResourceMetricCard
            title="Disk Usage"
            icon={<HardDrive className="h-3.5 w-3.5" />}
            metric={health?.system_metrics?.disk}
          />

          <ResourceMetricCard
            title="GPU Usage"
            icon={<Cpu className="h-3.5 w-3.5" />}
            metric={health?.system_metrics?.gpu}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Cpu className="h-5 w-5 text-primary" />
            NLP Assets
          </CardTitle>
          <CardDescription>
            Availability of local spaCy and NLTK assets used by context preprocessing.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {!health?.nlp_assets ? (
            <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
              No NLP asset health data was returned by the backend.
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium">spaCy Model</span>
                  <Badge
                    variant={
                      health.nlp_assets.spacy_model_installed ? "default" : "destructive"
                    }
                  >
                    {health.nlp_assets.spacy_model_installed ? "Ready" : "Missing"}
                  </Badge>
                </div>

                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  {health.nlp_assets.spacy_model_name || "en_core_web_sm"}
                </p>

                <p className="mt-1 text-[10px] text-muted-foreground">
                  spaCy package: {health.nlp_assets.spacy_installed ? "installed" : "missing"}
                </p>
              </div>

              <div className="rounded-xl border p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium">NLTK Resources</span>
                  <Badge variant={health.nlp_assets.ready ? "default" : "secondary"}>
                    {health.nlp_assets.ready ? "Ready" : "Partial"}
                  </Badge>
                </div>

                <p className="mt-1 text-xs text-muted-foreground">
                  {health.nlp_assets.nltk_resources
                    ? Object.entries(health.nlp_assets.nltk_resources)
                        .map(([name, ready]) => `${name}:${ready ? "ok" : "missing"}`)
                        .join("  ")
                    : "No resource data"}
                </p>

                <p className="mt-1 text-[10px] text-muted-foreground">
                  NLTK package: {health.nlp_assets.nltk_installed ? "installed" : "missing"}
                </p>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between gap-4 rounded-xl border p-3">
            <div>
              <p className="text-sm font-medium">Admin Install Action</p>
              <p className="text-xs text-muted-foreground">
                Runtime downloads:{" "}
                {health?.nlp_assets?.runtime_downloads_enabled ? "enabled" : "disabled or unknown"}.
                The backend must enforce RBAC and download policy.
              </p>
            </div>

            <Button
              onClick={() => void installNlpAssets()}
              disabled={isInstallingNlpAssets || health?.nlp_assets?.runtime_downloads_enabled === false}
            >
              {isInstallingNlpAssets ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Install Assets
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Shield className="h-5 w-5 text-primary" />
            Environment Configuration
          </CardTitle>
          <CardDescription>
            Read-only backend configuration visibility. Secret values must stay redacted.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {environmentConfig.length === 0 ? (
            <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
              No environment configuration metadata is available.
            </div>
          ) : (
            <div className="space-y-1">
              {environmentConfig.map((env) => (
                <div
                  key={env.key}
                  className="group flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/30"
                >
                  <div className="min-w-0 flex-1">
                    <code className="font-mono text-xs font-semibold text-primary/80">
                      {env.key}
                    </code>

                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      {env.description || "Backend configuration value"}
                    </p>

                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      Source: {env.source || "unknown"}
                      {env.editable ? " · editable" : " · read-only"}
                    </p>
                  </div>

                  <div className="ml-4 flex shrink-0 flex-col items-end gap-1">
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {env.value != null && env.value !== ""
                        ? String(env.value)
                        : env.default_value != null
                          ? String(env.default_value)
                          : "unset"}
                    </Badge>

                    {env.value == null && env.default_value != null && (
                      <span className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        reference default
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <Separator className="my-4" />

          <Alert>
            <InfoIcon />
            <AlertTitle className="text-xs">Configuration ownership</AlertTitle>
            <AlertDescription className="text-[10px]">
              Change runtime configuration through the backend-approved config source,
              environment files, or deployment manifests. The admin UI must not invent or override
              provider, model, auth, CORS, or security settings.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}

function InfoIcon() {
  return <Shield className="h-4 w-4" />;
}