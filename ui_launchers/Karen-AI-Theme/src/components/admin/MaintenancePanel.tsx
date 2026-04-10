"use client";

import { useEffect, useState, useCallback } from "react";
import { AlertCircle, CheckCircle2, Info, Loader2, RefreshCw, ShieldAlert, Trash2, Zap } from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface CleanupAction {
  action_type: string;
  target: string;
  description: string;
  size_bytes?: number;
  count?: number;
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

interface RuntimeStatusResponse {
  mode: string;
  maintenance_active: boolean;
  maintenance_message?: string | null;
  estimated_completion_time?: string | null;
  normal_ready: boolean;
  degraded_ready: boolean;
  dependencies: Record<string, {
    status: string;
    reason?: string | null;
    response_time_ms: number;
    consecutive_successes: number;
    consecutive_failures: number;
    checked_at?: string | null;
  }>;
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

export default function MaintenancePanel() {
  const { toast } = useToast();
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [report, setReport] = useState<CleanupReport | null>(null);
  const [lastCheck, setLastCheck] = useState<string | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatusResponse | null>(null);
  const [subscriptions, setSubscriptions] = useState<NotificationSubscription[]>([]);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [submittingMaintenance, setSubmittingMaintenance] = useState(false);
  const [maintenanceReason, setMaintenanceReason] = useState("planned_maintenance");
  const [maintenanceMessage, setMaintenanceMessage] = useState("Scheduled maintenance is in progress.");
  const [maintenanceEta, setMaintenanceEta] = useState("");

  const fetchRuntimeStatus = useCallback(async () => {
    setRuntimeLoading(true);
    try {
      const [statusResponse, notificationsResponse] = await Promise.all([
        apiClient.get<RuntimeStatusResponse>("/admin/runtime/status"),
        apiClient.get<NotificationSubscriptionResponse>("/admin/runtime/maintenance/notifications"),
      ]);
      setRuntimeStatus(statusResponse);
      setSubscriptions(notificationsResponse.subscriptions || []);
    } catch (error) {
      toast({
        title: "Runtime status unavailable",
        description: error instanceof Error ? error.message : "Could not load runtime control data.",
        variant: "destructive",
      });
    } finally {
      setRuntimeLoading(false);
    }
  }, [toast]);

  const triggerHealthCheck = useCallback(async () => {
    try {
      await apiClient.post("/admin/runtime/check-health", {});
      await fetchRuntimeStatus();
      toast({ title: "Health check completed", description: "Runtime dependency status was refreshed." });
    } catch (error) {
      toast({
        title: "Health check failed",
        description: error instanceof Error ? error.message : "Could not refresh runtime health.",
        variant: "destructive",
      });
    }
  }, [fetchRuntimeStatus, toast]);

  const submitMaintenanceAction = useCallback(async (action: "enable" | "update" | "disable") => {
    setSubmittingMaintenance(true);
    try {
      if (action === "enable") {
        await apiClient.post("/admin/runtime/maintenance/enable", {
          reason: maintenanceReason,
          message: maintenanceMessage,
          estimated_completion_time: maintenanceEta || null,
          auto_end_policy: maintenanceEta ? "at_time" : "manual",
        });
      } else if (action === "update") {
        await apiClient.put("/admin/runtime/maintenance/update", {
          message: maintenanceMessage,
          estimated_completion_time: maintenanceEta || null,
          auto_end_policy: maintenanceEta ? "at_time" : "manual",
        });
      } else {
        await apiClient.post("/admin/runtime/maintenance/disable", {});
      }
      await fetchRuntimeStatus();
      toast({
        title:
          action === "enable"
            ? "Maintenance enabled"
            : action === "update"
              ? "Maintenance updated"
              : "Maintenance disabled",
        description: "Operator runtime controls have been applied.",
      });
    } catch (error) {
      toast({
        title: "Maintenance action failed",
        description: error instanceof Error ? error.message : "Could not update maintenance state.",
        variant: "destructive",
      });
    } finally {
      setSubmittingMaintenance(false);
    }
  }, [fetchRuntimeStatus, maintenanceEta, maintenanceMessage, maintenanceReason, toast]);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<RecommendationResponse>("/api/maintenance/recommendations");
      setRecommendations(response.recommendations);
      setLastCheck(new Date(response.timestamp).toLocaleString());
    } catch (error) {
      console.error("Failed to load recommendations:", error);
      toast({
        title: "Diagnostics failed",
        description: error instanceof Error ? error.message : "Could not retrieve system recommendations.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const runCleanup = async (dryRun: boolean = true) => {
    setCleaning(true);
    setReport(null);
    try {
      const query = dryRun ? "?dry_run=true" : "?dry_run=false";
      const response = await apiClient.post<CleanupReport>(`/api/maintenance/cleanup${query}`, {});
      setReport(response);
      
      toast({
        title: dryRun ? "Dry-run complete" : "Cleanup complete",
        description: `Processed ${response.total_actions} actions. See report for details.`,
      });
      
      // Refresh recommendations if we actually did something
      if (!dryRun) {
        void fetchRecommendations();
      }
    } catch (error) {
      console.error("Cleanup failed:", error);
      toast({
        title: "Maintenance failed",
        description: error instanceof Error ? error.message : "System cleanup encountered an error.",
        variant: "destructive",
      });
    } finally {
      setCleaning(false);
    }
  };

  useEffect(() => {
    void fetchRecommendations();
  }, [fetchRecommendations]);

  useEffect(() => {
    void fetchRuntimeStatus();
  }, [fetchRuntimeStatus]);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle className="text-xl">Runtime Control Plane</CardTitle>
                <CardDescription>Authoritative runtime mode, maintenance controls, and dependency visibility.</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={() => void fetchRuntimeStatus()} disabled={runtimeLoading}>
                {runtimeLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Current mode</div>
                <div className="mt-2 flex items-center gap-2">
                  <Badge>{runtimeStatus?.mode || "unknown"}</Badge>
                  {runtimeStatus?.maintenance_active ? <Badge variant="secondary">maintenance active</Badge> : null}
                </div>
              </div>
              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Normal ready</div>
                <div className="mt-2 text-lg font-semibold">{runtimeStatus?.normal_ready ? "yes" : "no"}</div>
              </div>
              <div className="rounded-xl border p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Degraded ready</div>
                <div className="mt-2 text-lg font-semibold">{runtimeStatus?.degraded_ready ? "yes" : "no"}</div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="maintenance-reason">Reason</Label>
                <Input id="maintenance-reason" value={maintenanceReason} onChange={(e) => setMaintenanceReason(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maintenance-eta">ETA</Label>
                <Input id="maintenance-eta" type="datetime-local" value={maintenanceEta} onChange={(e) => setMaintenanceEta(e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="maintenance-message">Message</Label>
              <Textarea id="maintenance-message" value={maintenanceMessage} onChange={(e) => setMaintenanceMessage(e.target.value)} rows={3} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void submitMaintenanceAction("enable")} disabled={submittingMaintenance}>
                Enable maintenance
              </Button>
              <Button variant="outline" onClick={() => void submitMaintenanceAction("update")} disabled={submittingMaintenance || !runtimeStatus?.maintenance_active}>
                Update maintenance
              </Button>
              <Button variant="secondary" onClick={() => void submitMaintenanceAction("disable")} disabled={submittingMaintenance || !runtimeStatus?.maintenance_active}>
                Disable maintenance
              </Button>
              <Button variant="outline" onClick={() => void triggerHealthCheck()} disabled={runtimeLoading}>
                Trigger health check
              </Button>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-semibold">Dependency health</div>
              <div className="grid gap-2 md:grid-cols-2">
                {Object.entries(runtimeStatus?.dependencies || {}).map(([name, dependency]) => (
                  <div key={name} className="rounded-lg border p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{name}</span>
                      <Badge variant={dependency.status === "healthy" ? "default" : "secondary"}>{dependency.status}</Badge>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {dependency.reason || "No issues reported"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Maintenance notifications</CardTitle>
            <CardDescription>Current subscription state from the authoritative runtime control plane.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">Subscriptions: {subscriptions.length}</div>
            <ScrollArea className="h-[360px]">
              <div className="space-y-2">
                {subscriptions.map((subscription) => (
                  <div key={subscription.id} className="rounded-lg border p-3 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{subscription.channel}</span>
                      <Badge variant="outline">{subscription.status}</Badge>
                    </div>
                    <div className="mt-2 text-muted-foreground break-all">
                      {subscription.user_id || subscription.session_id || subscription.id}
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
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl flex items-center gap-2">
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
                disabled={loading}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Karen is analyzing system resources...</p>
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/40 border border-border/50">
                    <Info className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                    <p className="text-sm">{rec}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center space-y-2">
                <CheckCircle2 className="h-10 w-10 text-green-500 mx-auto opacity-80" />
                <p className="text-sm font-medium">System is clean!</p>
                <p className="text-xs text-muted-foreground">No critical maintenance tasks identified.</p>
              </div>
            )}
          </CardContent>
          <CardFooter className="bg-muted/30 border-t flex justify-between h-12 py-0">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
              Scan Reliability: High
            </p>
            {lastCheck && (
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                Last checked: {lastCheck}
              </p>
            )}
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-destructive" />
              Quick Actions
            </CardTitle>
            <CardDescription>
              Automated cleanup and resource optimization.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-xl border border-destructive/20 bg-destructive/5 space-y-3">
              <div className="flex items-center gap-2 text-destructive font-semibold text-sm">
                <ShieldAlert className="h-4 w-4" />
                Data Hygiene
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Running cleanup will remove demo data, expired cache files, and older logs to optimize disk space and system performance.
              </p>
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => void runCleanup(true)}
                  disabled={cleaning}
                >
                  Dry Run
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  onClick={() => void runCleanup(false)}
                  disabled={cleaning}
                >
                  {cleaning ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <Trash2 className="h-3 w-3 mr-2" />}
                  Clean Now
                </Button>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertTitle className="text-xs">Note</AlertTitle>
              <AlertDescription className="text-[10px]">
                Backups are automatically created for critical JSON and DB files before any destructive action.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      {report && (
        <Card className="animate-in slide-in-from-top-4 duration-500 overflow-hidden border-primary/20 shadow-lg shadow-primary/5">
          <CardHeader className="bg-primary/5 border-b pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  Maintenance Report: {report.dry_run ? "Simulation" : "Execution"}
                </CardTitle>
                <CardDescription>
                  {new Date(report.timestamp).toLocaleString()}
                </CardDescription>
              </div>
              <Badge variant={report.dry_run ? "outline" : "default"} className={report.dry_run ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/30" : "bg-green-500 text-white"}>
                {report.dry_run ? "DRY RUN MODE" : "EXECUTED"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-border border-b bg-muted/20">
              <div className="p-4 text-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Actions</div>
                <div className="text-2xl font-bold">{report.total_actions}</div>
              </div>
              <div className="p-4 text-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Successful</div>
                <div className="text-2xl font-bold text-green-500">{report.successful_actions}</div>
              </div>
              <div className="p-4 text-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Cleaned</div>
                <div className="text-2xl font-bold text-primary">{formatSize(report.bytes_cleaned)}</div>
              </div>
              <div className="p-4 text-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Errors</div>
                <div className="text-2xl font-bold text-destructive">{report.failed_actions}</div>
              </div>
            </div>

            <ScrollArea className="h-[300px]">
              <div className="p-4 space-y-1">
                {report.actions.map((action, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded hover:bg-muted/50 transition-colors text-sm border-b border-border/20 last:border-0">
                    <div className="flex items-center gap-4">
                      <Badge variant="outline" className="text-[10px] h-5 min-w-[100px] justify-center opacity-80">
                        {action.action_type.replace(/_/g, ' ')}
                      </Badge>
                      <span className="font-medium truncate max-w-[400px]">{action.description}</span>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {action.size_bytes ? formatSize(action.size_bytes) : action.count ? `${action.count} items` : '--'}
                    </div>
                  </div>
                ))}
                {report.actions.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No actions were triggered in this cleanup cycle.
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
          {report.errors.length > 0 && (
            <CardFooter className="bg-destructive/5 border-t p-4 flex-col items-start gap-4">
              <div className="flex items-center gap-2 text-destructive font-bold text-sm">
                <AlertCircle className="h-4 w-4" />
                Execution Errors
              </div>
              <div className="w-full space-y-2">
                {report.errors.map((err, i) => (
                  <div key={i} className="text-xs text-destructive bg-destructive/10 p-2 rounded border border-destructive/20">
                    {err}
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
