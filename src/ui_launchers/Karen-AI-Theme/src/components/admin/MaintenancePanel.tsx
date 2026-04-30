"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Info,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Trash2,
  Zap,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

interface CleanupAction {
  action_type: string;
  target: string;
  description: string;
  size_bytes?: number | null;
  count?: number | null;
  timestamp: string;
}

interface CleanupReport {
  timestamp: string;
  dry_run: boolean;
  total_actions: number;
  successful_actions: number;
  failed_actions: number;
  bytes_cleaned: number;
  summary: Record<string, number>;
  actions: CleanupAction[];
  errors: string[];
}

interface RecommendationResponse {
  recommendations: string[];
  timestamp: string;
}

interface RuntimeDependencyStatus {
  status: string;
  reason?: string | null;
  response_time_ms: number;
  consecutive_successes: number;
  consecutive_failures: number;
  checked_at?: string | null;
}

interface RuntimeStatusResponse {
  mode: string;
  maintenance_active: boolean;
  maintenance_message?: string | null;
  estimated_completion_time?: string | null;
  normal_ready: boolean;
  degraded_ready: boolean;
  dependencies: Record<string, RuntimeDependencyStatus>;
}

interface NotificationSubscription {
  id: string;
  user_id?: string | null;
  session_id?: string | null;
  channel: string;
  status: string;
  requested_at?: string | null;
  dispatched_at?: string | null;
}

interface NotificationSubscriptionResponse {
  subscriptions: NotificationSubscription[];
  count: number;
}

type MaintenanceAction = "enable" | "update" | "disable";

const DEFAULT_MAINTENANCE_REASON = "planned_maintenance";
const DEFAULT_MAINTENANCE_MESSAGE = "Scheduled maintenance is in progress.";

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in before using admin maintenance controls.";
    }

    if (error.status === 403) {
      return "This session is not authorized to use admin maintenance controls.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
};

const sanitizeRuntimeError = (message: string): string => {
  const trimmed = message.trim();
  if (!trimmed) return "Runtime control endpoint is unavailable.";

  if (trimmed.startsWith('<!DOCTYPE html>') || trimmed.startsWith('<html')) {
    return "Runtime control endpoint returned an HTML 404 page. Verify backend admin runtime routes are enabled.";
  }

  return trimmed;
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

const formatDateTimeForInput = (value: string | null | undefined) => {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const offsetMs = parsed.getTimezoneOffset() * 60_000;
  const localDate = new Date(parsed.getTime() - offsetMs);

  return localDate.toISOString().slice(0, 16);
};

const normalizeEtaForApi = (value: string) => {
  const trimmed = value.trim();

  if (!trimmed) {
    return null;
  }

  const parsed = new Date(trimmed);

  if (Number.isNaN(parsed.getTime())) {
    return trimmed;
  }

  return parsed.toISOString();
};

const formatSize = (bytes: number | null | undefined) => {
  if (!Number.isFinite(bytes ?? NaN) || !bytes || bytes <= 0) {
    return "0 B";
  }

  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const sizeIndex = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    sizes.length - 1,
  );

  const value = bytes / Math.pow(1024, sizeIndex);

  return `${value.toFixed(value >= 10 || sizeIndex === 0 ? 0 : 2)} ${sizes[sizeIndex]}`;
};

const getDependencyBadgeVariant = (status: string) => {
  const normalized = status.toLowerCase();

  if (normalized === "healthy" || normalized === "ready" || normalized === "ok") {
    return "default" as const;
  }

  if (normalized === "degraded" || normalized === "warning") {
    return "secondary" as const;
  }

  return "destructive" as const;
};

const getModeBadgeVariant = (mode: string | undefined) => {
  const normalized = (mode || "").toLowerCase();

  if (normalized === "normal" || normalized === "ready") {
    return "default" as const;
  }

  if (normalized === "maintenance" || normalized === "degraded") {
    return "secondary" as const;
  }

  return "outline" as const;
};

export default function MaintenancePanel() {
  const { toast } = useToast();

  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null);
  const [lastCheck, setLastCheck] = useState<string | null>(null);

  const [cleaning, setCleaning] = useState(false);
  const [report, setReport] = useState<CleanupReport | null>(null);

  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatusResponse | null>(null);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);

  const [subscriptions, setSubscriptions] = useState<NotificationSubscription[]>([]);
  const [submittingMaintenance, setSubmittingMaintenance] = useState(false);

  const [maintenanceReason, setMaintenanceReason] = useState(DEFAULT_MAINTENANCE_REASON);
  const [maintenanceMessage, setMaintenanceMessage] = useState(DEFAULT_MAINTENANCE_MESSAGE);
  const [maintenanceEta, setMaintenanceEta] = useState("");

  const dependencyEntries = useMemo(() => {
    return Object.entries(runtimeStatus?.dependencies || {}).sort(([left], [right]) =>
      left.localeCompare(right),
    );
  }, [runtimeStatus?.dependencies]);

  const maintenanceFormError = useMemo(() => {
    if (!maintenanceReason.trim()) {
      return "Maintenance reason is required.";
    }

    if (!maintenanceMessage.trim()) {
      return "Maintenance message is required.";
    }

    if (maintenanceEta.trim()) {
      const parsedEta = new Date(maintenanceEta);

      if (Number.isNaN(parsedEta.getTime())) {
        return "Maintenance ETA must be a valid date and time.";
      }
    }

    return null;
  }, [maintenanceEta, maintenanceMessage, maintenanceReason]);

  const fetchRuntimeStatus = useCallback(async () => {
    setRuntimeLoading(true);
    setRuntimeError(null);

    try {
      const [statusResponse, notificationsResponse] = await Promise.all([
        apiClient.get<RuntimeStatusResponse>("/api/admin/runtime/status"),
        apiClient.get<NotificationSubscriptionResponse>(
          "/api/admin/runtime/maintenance/notifications",
        ),
      ]);

      setRuntimeStatus(statusResponse);
      setSubscriptions(Array.isArray(notificationsResponse.subscriptions) ? notificationsResponse.subscriptions : []);

      setMaintenanceMessage(
        statusResponse.maintenance_message?.trim() || DEFAULT_MAINTENANCE_MESSAGE,
      );
      setMaintenanceEta(formatDateTimeForInput(statusResponse.estimated_completion_time));
    } catch (error) {
      const message = sanitizeRuntimeError(getErrorMessage(error, "Could not load runtime control data."));
      setRuntimeError(message);

      toast({
        title: "Runtime status unavailable",
        description: message,
        variant: "destructive",
      });
    } finally {
      setRuntimeLoading(false);
    }
  }, [toast]);

  const triggerHealthCheck = useCallback(async () => {
    setRuntimeLoading(true);

    try {
      await apiClient.post("/api/admin/runtime/check-health", {});
      await fetchRuntimeStatus();

      toast({
        title: "Health check completed",
        description: "Runtime dependency status was refreshed.",
      });
    } catch (error) {
      const message = getErrorMessage(error, "Could not refresh runtime health.");

      toast({
        title: "Health check failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setRuntimeLoading(false);
    }
  }, [fetchRuntimeStatus, toast]);

  const submitMaintenanceAction = useCallback(
    async (action: MaintenanceAction) => {
      if (action !== "disable" && maintenanceFormError) {
        toast({
          title: "Maintenance form incomplete",
          description: maintenanceFormError,
          variant: "destructive",
        });
        return;
      }

      setSubmittingMaintenance(true);

      try {
        const estimatedCompletionTime = normalizeEtaForApi(maintenanceEta);
        const autoEndPolicy = estimatedCompletionTime ? "at_time" : "manual";

        if (action === "enable") {
          await apiClient.post("/api/admin/runtime/maintenance/enable", {
            reason: maintenanceReason.trim(),
            message: maintenanceMessage.trim(),
            estimated_completion_time: estimatedCompletionTime,
            auto_end_policy: autoEndPolicy,
          });
        }

        if (action === "update") {
          await apiClient.put("/api/admin/runtime/maintenance/update", {
            message: maintenanceMessage.trim(),
            estimated_completion_time: estimatedCompletionTime,
            auto_end_policy: autoEndPolicy,
          });
        }

        if (action === "disable") {
          await apiClient.post("/api/admin/runtime/maintenance/disable", {});
        }

        await fetchRuntimeStatus();

        toast({
          title:
            action === "enable"
              ? "Maintenance enabled"
              : action === "update"
                ? "Maintenance updated"
                : "Maintenance disabled",
          description: "Operator runtime controls were applied by the backend.",
        });
      } catch (error) {
        const message = getErrorMessage(error, "Could not update maintenance state.");

        toast({
          title: "Maintenance action failed",
          description: message,
          variant: "destructive",
        });
      } finally {
        setSubmittingMaintenance(false);
      }
    },
    [
      fetchRuntimeStatus,
      maintenanceEta,
      maintenanceFormError,
      maintenanceMessage,
      maintenanceReason,
      toast,
    ],
  );

  const fetchRecommendations = useCallback(async () => {
    setLoadingRecommendations(true);
    setRecommendationsError(null);

    try {
      const response = await apiClient.get<RecommendationResponse>(
        "/api/maintenance/recommendations",
      );

      setRecommendations(Array.isArray(response.recommendations) ? response.recommendations : []);
      setLastCheck(formatDateTime(response.timestamp));
    } catch (error) {
      const message = getErrorMessage(error, "Could not retrieve system recommendations.");
      setRecommendationsError(message);

      toast({
        title: "Diagnostics failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoadingRecommendations(false);
    }
  }, [toast]);

  const runCleanup = useCallback(
    async (dryRun: boolean) => {
      setCleaning(true);
      setReport(null);

      try {
        const response = await apiClient.post<CleanupReport>(
          `/api/maintenance/cleanup?dry_run=${dryRun ? "true" : "false"}`,
          {},
        );

        setReport({
          ...response,
          actions: Array.isArray(response.actions) ? response.actions : [],
          errors: Array.isArray(response.errors) ? response.errors : [],
          summary: response.summary || {},
        });

        toast({
          title: dryRun ? "Dry-run complete" : "Cleanup complete",
          description: `Processed ${response.total_actions} actions. See report for details.`,
        });

        if (!dryRun) {
          void fetchRecommendations();
        }
      } catch (error) {
        const message = getErrorMessage(error, "System cleanup encountered an error.");

        toast({
          title: "Maintenance failed",
          description: message,
          variant: "destructive",
        });
      } finally {
        setCleaning(false);
      }
    },
    [fetchRecommendations, toast],
  );

  useEffect(() => {
    void fetchRecommendations();
  }, [fetchRecommendations]);

  useEffect(() => {
    void fetchRuntimeStatus();
  }, [fetchRuntimeStatus]);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle className="text-xl">Runtime Control Plane</CardTitle>
                <CardDescription>
                  Authoritative runtime mode, maintenance controls, and dependency visibility.
                </CardDescription>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => void fetchRuntimeStatus()}
                disabled={runtimeLoading}
              >
                {runtimeLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh
              </Button>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {runtimeError && (
              <Alert className="border-yellow-500/30 bg-yellow-500/5">
                <AlertCircle className="h-4 w-4 !text-yellow-600" />
                <AlertTitle>Runtime Control Unavailable</AlertTitle>
                <AlertDescription>{runtimeError}</AlertDescription>
              </Alert>
            )}

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Current mode
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Badge variant={getModeBadgeVariant(runtimeStatus?.mode)}>
                    {runtimeStatus?.mode || "unknown"}
                  </Badge>
                  {runtimeStatus?.maintenance_active ? (
                    <Badge variant="secondary">maintenance active</Badge>
                  ) : null}
                </div>
              </div>

              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Normal ready
                </div>
                <div className="mt-2 text-lg font-semibold">
                  {runtimeStatus ? (runtimeStatus.normal_ready ? "yes" : "no") : "unknown"}
                </div>
              </div>

              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  Degraded ready
                </div>
                <div className="mt-2 text-lg font-semibold">
                  {runtimeStatus ? (runtimeStatus.degraded_ready ? "yes" : "no") : "unknown"}
                </div>
              </div>
            </div>

            {runtimeStatus?.maintenance_active && (
              <Alert className="border-primary/20 bg-primary/5">
                <Info className="h-4 w-4 !text-primary" />
                <AlertTitle>Maintenance mode is active</AlertTitle>
                <AlertDescription>
                  {runtimeStatus.maintenance_message || "Maintenance is currently active."}
                  {runtimeStatus.estimated_completion_time ? (
                    <span className="block pt-1">
                      Estimated completion:{" "}
                      {formatDateTime(runtimeStatus.estimated_completion_time)}
                    </span>
                  ) : null}
                </AlertDescription>
              </Alert>
            )}

            {maintenanceFormError && (
              <Alert className="border-yellow-500/30 bg-yellow-500/5">
                <AlertCircle className="h-4 w-4 !text-yellow-600" />
                <AlertTitle>Maintenance form needs attention</AlertTitle>
                <AlertDescription>{maintenanceFormError}</AlertDescription>
              </Alert>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="maintenance-reason">Reason</Label>
                <Input
                  id="maintenance-reason"
                  value={maintenanceReason}
                  onChange={(event) => setMaintenanceReason(event.target.value)}
                  disabled={submittingMaintenance}
                  placeholder="planned_maintenance"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="maintenance-eta">ETA</Label>
                <Input
                  id="maintenance-eta"
                  type="datetime-local"
                  value={maintenanceEta}
                  onChange={(event) => setMaintenanceEta(event.target.value)}
                  disabled={submittingMaintenance}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maintenance-message">Message</Label>
              <Textarea
                id="maintenance-message"
                value={maintenanceMessage}
                onChange={(event) => setMaintenanceMessage(event.target.value)}
                rows={3}
                disabled={submittingMaintenance}
                placeholder="Scheduled maintenance is in progress."
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => void submitMaintenanceAction("enable")}
                disabled={submittingMaintenance || !!maintenanceFormError}
              >
                {submittingMaintenance ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Enable maintenance
              </Button>

              <Button
                variant="outline"
                onClick={() => void submitMaintenanceAction("update")}
                disabled={
                  submittingMaintenance ||
                  !runtimeStatus?.maintenance_active ||
                  !!maintenanceFormError
                }
              >
                Update maintenance
              </Button>

              <Button
                variant="secondary"
                onClick={() => void submitMaintenanceAction("disable")}
                disabled={submittingMaintenance || !runtimeStatus?.maintenance_active}
              >
                Disable maintenance
              </Button>

              <Button
                variant="outline"
                onClick={() => void triggerHealthCheck()}
                disabled={runtimeLoading}
              >
                {runtimeLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Trigger health check
              </Button>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-semibold">Dependency health</div>

              {dependencyEntries.length === 0 ? (
                <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                  No dependency health records were returned by the runtime control plane.
                </div>
              ) : (
                <div className="grid gap-2 md:grid-cols-2">
                  {dependencyEntries.map(([name, dependency]) => (
                    <div key={name} className="rounded-lg border p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{name}</span>
                        <Badge variant={getDependencyBadgeVariant(dependency.status)}>
                          {dependency.status}
                        </Badge>
                      </div>

                      <div className="mt-2 text-xs text-muted-foreground">
                        {dependency.reason || "No issues reported"}
                      </div>

                      <div className="mt-2 grid gap-1 text-[11px] text-muted-foreground">
                        <div>Response: {dependency.response_time_ms}ms</div>
                        <div>
                          Successes: {dependency.consecutive_successes} · Failures:{" "}
                          {dependency.consecutive_failures}
                        </div>
                        <div>Checked: {formatDateTime(dependency.checked_at)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Maintenance notifications</CardTitle>
            <CardDescription>
              Current subscription state from the authoritative runtime control plane.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              Subscriptions: {subscriptions.length}
            </div>

            <ScrollArea className="h-[360px]">
              <div className="space-y-2">
                {subscriptions.map((subscription) => (
                  <div key={subscription.id} className="rounded-lg border p-3 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{subscription.channel}</span>
                      <Badge variant="outline">{subscription.status}</Badge>
                    </div>

                    <div className="mt-2 break-all text-muted-foreground">
                      {subscription.user_id || subscription.session_id || subscription.id}
                    </div>

                    <div className="mt-2 grid gap-1 text-[11px] text-muted-foreground">
                      <div>Requested: {formatDateTime(subscription.requested_at)}</div>
                      <div>Dispatched: {formatDateTime(subscription.dispatched_at)}</div>
                    </div>
                  </div>
                ))}

                {subscriptions.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-4 text-xs text-muted-foreground">
                    No maintenance notification subscriptions found.
                  </div>
                ) : null}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  System Diagnostics
                </CardTitle>
                <CardDescription>
                  Automated analysis of system hygiene and resource usage.
                </CardDescription>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => void fetchRecommendations()}
                disabled={loadingRecommendations}
              >
                {loadingRecommendations ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            {recommendationsError && (
              <Alert className="mb-4 border-yellow-500/30 bg-yellow-500/5">
                <AlertCircle className="h-4 w-4 !text-yellow-600" />
                <AlertTitle>Diagnostics Unavailable</AlertTitle>
                <AlertDescription>{recommendationsError}</AlertDescription>
              </Alert>
            )}

            {loadingRecommendations ? (
              <div className="flex flex-col items-center justify-center space-y-3 py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">
                  Karen is analyzing system resources...
                </p>
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((recommendation, index) => (
                  <div
                    key={`${recommendation}-${index}`}
                    className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/40 p-3"
                  >
                    <Info className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                    <p className="text-sm">{recommendation}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2 py-12 text-center">
                <CheckCircle2 className="mx-auto h-10 w-10 text-green-500 opacity-80" />
                <p className="text-sm font-medium">No recommendations returned.</p>
                <p className="text-xs text-muted-foreground">
                  The backend did not identify maintenance tasks for this scan.
                </p>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex h-12 justify-between border-t bg-muted/30 py-0">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Scan source: backend diagnostics
            </p>

            {lastCheck && (
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Last checked: {lastCheck}
              </p>
            )}
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Trash2 className="h-5 w-5 text-destructive" />
              Quick Actions
            </CardTitle>
            <CardDescription>Automated cleanup and resource optimization.</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="space-y-3 rounded-xl border border-destructive/20 bg-destructive/5 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-destructive">
                <ShieldAlert className="h-4 w-4" />
                Data Hygiene
              </div>

              <p className="text-xs leading-relaxed text-muted-foreground">
                Cleanup requests are executed only by the backend maintenance service.
                Dry-run previews planned actions. Clean Now requires confirmation.
              </p>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void runCleanup(true)}
                  disabled={cleaning}
                >
                  {cleaning ? <Loader2 className="mr-2 h-3 w-3 animate-spin" /> : null}
                  Dry Run
                </Button>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button size="sm" variant="destructive" disabled={cleaning}>
                      {cleaning ? (
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                      ) : (
                        <Trash2 className="mr-2 h-3 w-3" />
                      )}
                      Clean Now
                    </Button>
                  </AlertDialogTrigger>

                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Run destructive cleanup?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will ask the backend maintenance service to perform cleanup with
                        dry_run=false. Only continue if backend backups, RBAC checks, and audit
                        logging are active.
                      </AlertDialogDescription>
                    </AlertDialogHeader>

                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-destructive hover:bg-destructive/90"
                        onClick={() => void runCleanup(false)}
                      >
                        Run Cleanup
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertTitle className="text-xs">Backend ownership</AlertTitle>
              <AlertDescription className="text-[10px]">
                The UI only requests maintenance actions. Backups, file selection,
                destructive execution, audit logs, and rollback safety must be enforced by the
                backend.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      {report && (
        <Card className="animate-in slide-in-from-top-4 overflow-hidden border-primary/20 shadow-lg shadow-primary/5 duration-500">
          <CardHeader className="border-b bg-primary/5 pb-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  Maintenance Report: {report.dry_run ? "Simulation" : "Execution"}
                </CardTitle>
                <CardDescription>{formatDateTime(report.timestamp)}</CardDescription>
              </div>

              <Badge
                variant={report.dry_run ? "outline" : "default"}
                className={
                  report.dry_run
                    ? "border-yellow-500/30 bg-yellow-500/10 text-yellow-600"
                    : "bg-green-500 text-white"
                }
              >
                {report.dry_run ? "DRY RUN MODE" : "EXECUTED"}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            <div className="grid grid-cols-2 divide-x divide-border border-b bg-muted/20 md:grid-cols-4">
              <div className="p-4 text-center">
                <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Actions
                </div>
                <div className="text-2xl font-bold">{report.total_actions}</div>
              </div>

              <div className="p-4 text-center">
                <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Successful
                </div>
                <div className="text-2xl font-bold text-green-500">
                  {report.successful_actions}
                </div>
              </div>

              <div className="p-4 text-center">
                <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Cleaned
                </div>
                <div className="text-2xl font-bold text-primary">
                  {formatSize(report.bytes_cleaned)}
                </div>
              </div>

              <div className="p-4 text-center">
                <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Errors
                </div>
                <div className="text-2xl font-bold text-destructive">
                  {report.failed_actions}
                </div>
              </div>
            </div>

            <ScrollArea className="h-[300px]">
              <div className="space-y-1 p-4">
                {report.actions.map((action, index) => (
                  <div
                    key={`${action.action_type}-${action.target}-${index}`}
                    className="flex items-center justify-between border-b border-border/20 p-2 text-sm transition-colors last:border-0 hover:bg-muted/50"
                  >
                    <div className="flex min-w-0 items-center gap-4">
                      <Badge
                        variant="outline"
                        className="h-5 min-w-[100px] justify-center text-[10px] opacity-80"
                      >
                        {action.action_type.replace(/_/g, " ")}
                      </Badge>

                      <div className="min-w-0">
                        <span className="block truncate font-medium">
                          {action.description}
                        </span>
                        <span className="block truncate text-[11px] text-muted-foreground">
                          {action.target}
                        </span>
                      </div>
                    </div>

                    <div className="shrink-0 pl-4 font-mono text-xs text-muted-foreground">
                      {action.size_bytes
                        ? formatSize(action.size_bytes)
                        : action.count
                          ? `${action.count} items`
                          : "--"}
                    </div>
                  </div>
                ))}

                {report.actions.length === 0 && (
                  <div className="py-12 text-center text-muted-foreground">
                    No actions were triggered in this cleanup cycle.
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>

          {report.errors.length > 0 && (
            <CardFooter className="flex-col items-start gap-4 border-t bg-destructive/5 p-4">
              <div className="flex items-center gap-2 text-sm font-bold text-destructive">
                <AlertCircle className="h-4 w-4" />
                Execution Errors
              </div>

              <div className="w-full space-y-2">
                {report.errors.map((error, index) => (
                  <div
                    key={`${error}-${index}`}
                    className="rounded border border-destructive/20 bg-destructive/10 p-2 text-xs text-destructive"
                  >
                    {error}
                  </div>
                ))}
              </div>
            </CardFooter>
          )}
        </Card>
      )}
    </div>
  );
}
