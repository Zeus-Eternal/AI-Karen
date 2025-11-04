"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

import {
  Activity,
  RefreshCw,
  CheckCircle2,
  HardDrive,
  Loader2,
  AlertCircle,
  XCircle,
  Square,
  Pause,
  Play,
  Clock,
  ChevronDown,
  ChevronRight,
  Settings,
  Layers,
  GitMerge,
  Download,
  Upload,
  Cpu,
  MemoryStick,
  FileText,
  Calendar,
  Timer,
} from "lucide-react";

import { getKarenBackend } from "@/lib/karen-backend";
import { handleApiError } from "@/lib/error-handler";

interface Job {
  id: string;
  kind: "convert" | "quantize" | "lora_merge" | "download" | "upload";
  status: "queued" | "running" | "paused" | "completed" | "error" | "cancelled";
  progress: number; // may be 0..1 or 0..100 (we normalize below)
  title: string;
  description?: string;
  source_path?: string;
  target_path?: string;
  parameters: Record<string, any>;
  logs: string[];
  created_at: number;
  updated_at: number;
  started_at?: number;
  completed_at?: number;
  error_message?: string;
  estimated_duration?: number; // ms
  resource_usage?: {
    cpu_percent: number;
    memory_mb: number;
    disk_io_mb: number;
  };
}

interface JobStats {
  total: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  active_jobs: Job[];
}

interface StorageInfo {
  total_space_gb: number;
  used_space_gb: number;
  available_space_gb: number;
  model_count: number;
  largest_model_gb: number;
  cleanup_candidates: Array<{
    path: string;
    size_gb: number;
    last_accessed: number;
    type: "temp" | "cache" | "old_model";
  }>;
}

interface JobManagerProps {
  onJobUpdate?: (job: Job) => void;
}

function normalizeProgress(p: number): number {
  // Accept 0..1 or 0..100 from backend; convert to 0..100 for UI
  if (p <= 1) return Math.max(0, Math.min(100, p * 100));
  return Math.max(0, Math.min(100, p));
}

function formatDuration(ms: number) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function formatFileSizeGB(gb: number) {
  if (gb < 1) return `${(gb * 1024).toFixed(1)} MB`;
  return `${gb.toFixed(1)} GB`;
}

export default function JobManager({ onJobUpdate }: JobManagerProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobStats, setJobStats] = useState<JobStats | null>(null);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"active" | "completed" | "storage">("active");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { toast } = useToast();
  const backend = getKarenBackend();

  const loadJobs = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<Job[]>("/api/models/jobs");
      setJobs(response || []);
      if (onJobUpdate && Array.isArray(response)) {
        response.forEach((j) => onJobUpdate(j));
      }
    } catch {
      setJobs([]);
    }
  }, [backend, onJobUpdate]);

  const loadJobStats = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<JobStats>("/api/models/jobs/stats");
      setJobStats(response);
    } catch {
      setJobStats(null);
    } finally {
      setLoading(false);
    }
  }, [backend]);

  const loadStorageInfo = useCallback(async () => {
    try {
      const response = await backend.makeRequestPublic<StorageInfo>("/api/models/storage");
      setStorageInfo(response);
    } catch {
      setStorageInfo(null);
    }
  }, [backend]);

  useEffect(() => {
    // initial load
    loadJobs();
    loadJobStats();
    loadStorageInfo();
  }, [loadJobs, loadJobStats, loadStorageInfo]);

  // Auto refresh while there are active jobs
  const activeJobsNow = useMemo(
    () => jobs.filter((j) => j.status === "queued" || j.status === "running" || j.status === "paused"),
    [jobs]
  );

  useEffect(() => {
    if (!autoRefresh) return;
    const anyRunning = (jobStats?.running ?? 0) > 0 || activeJobsNow.length > 0;
    if (!anyRunning) return;

    const interval = setInterval(() => {
      loadJobs();
      loadJobStats();
    }, 2000);

    return () => clearInterval(interval);
  }, [autoRefresh, jobStats?.running, activeJobsNow.length, loadJobs, loadJobStats]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([loadJobs(), loadJobStats(), loadStorageInfo()]);
      toast({
        title: "Refreshed",
        description: "Job status and storage info updated.",
      });
    } catch {
      toast({
        variant: "destructive",
        title: "Refresh Failed",
        description: "Could not refresh job information.",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const controlJob = async (jobId: string, action: "pause" | "resume" | "cancel") => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}/${action}`, { method: "POST" });
      toast({
        title: "Job Updated",
        description: `Job ${action}${action.endsWith("e") ? "d" : action === "cancel" ? "led" : "ed"}.`,
      });
      await loadJobs();
      await loadJobStats();
    } catch (error) {
      const info = handleApiError(error as any, `${action}Job`);
      toast({
        variant: "destructive",
        title: info.title || `${action.charAt(0).toUpperCase() + action.slice(1)} Failed`,
        description: info.message || `Could not ${action} job.`,
      });
    }
  };

  const deleteJob = async (jobId: string) => {
    try {
      await backend.makeRequestPublic(`/api/models/jobs/${jobId}`, { method: "DELETE" });
      toast({
        title: "Job Deleted",
        description: "Job removed from history.",
      });
      await loadJobs();
      await loadJobStats();
    } catch (error) {
      const info = handleApiError(error as any, "deleteJob");
      toast({
        variant: "destructive",
        title: info.title || "Delete Failed",
        description: info.message || "Could not delete job.",
      });
    }
  };

  const cleanupStorage = async (paths: string[]) => {
    try {
      await backend.makeRequestPublic("/api/models/storage/cleanup", {
        method: "POST",
        body: JSON.stringify({ paths }),
      });
      toast({
        title: "Cleanup Started",
        description: `Cleaning up ${paths.length} item${paths.length !== 1 ? "s" : ""}.`,
      });
      await loadStorageInfo();
    } catch (error) {
      const info = handleApiError(error as any, "cleanupStorage");
      toast({
        variant: "destructive",
        title: info.title || "Cleanup Failed",
        description: info.message || "Could not cleanup storage.",
      });
    }
  };

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) next.delete(jobId);
      else next.add(jobId);
      return next;
    });
  };

  const getJobIcon = (job: Job) => {
    switch (job.kind) {
      case "convert":
        return <Settings className="h-4 w-4" />;
      case "quantize":
        return <Layers className="h-4 w-4" />;
      case "lora_merge":
        return <GitMerge className="h-4 w-4" />;
      case "download":
        return <Download className="h-4 w-4" />;
      case "upload":
        return <Upload className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getStatusIcon = (status: Job["status"]) => {
    switch (status) {
      case "queued":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case "paused":
        return <Pause className="h-4 w-4 text-orange-600" />;
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "cancelled":
        return <Square className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (status: Job["status"]) => {
    switch (status) {
      case "completed":
        return "default";
      case "running":
        return "secondary";
      case "error":
        return "destructive";
      case "cancelled":
        return "outline";
      default:
        return "secondary";
    }
  };

  const activeJobs = useMemo(
    () => jobs.filter((j) => ["queued", "running", "paused"].includes(j.status)),
    [jobs]
  );
  const completedJobs = useMemo(
    () => jobs.filter((j) => ["completed", "error", "cancelled"].includes(j.status)),
    [jobs]
  );

  if (loading) {
    return (
      <ErrorBoundary fallback={<div>Something went wrong in JobManager</div>}>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Loading job information...
              </p>
            </div>
          </CardContent>
        </Card>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary fallback={<div>Something went wrong in JobManager</div>}>
      <div className="space-y-6">
        {/* Header with Stats */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Job Manager
                </CardTitle>
                <CardDescription></CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAutoRefresh((v) => !v)}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`} />
                  Auto-refresh: {autoRefresh ? "On" : "Off"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshing}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>

          {jobStats && (
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{jobStats.total}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Total Jobs
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{jobStats.running}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Running
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{jobStats.queued}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Queued
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{jobStats.completed}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Completed
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{jobStats.failed}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Failed
                  </div>
                </div>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="active" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Active ({activeJobs.length})
            </TabsTrigger>
            <TabsTrigger value="completed" className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              History ({completedJobs.length})
            </TabsTrigger>
            <TabsTrigger value="storage" className="flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              Storage
            </TabsTrigger>
          </TabsList>

          {/* Active Jobs */}
          <TabsContent value="active" className="space-y-4">
            {activeJobs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">No Active Jobs</p>
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    All jobs are completed. Start a new operation to see it here.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {activeJobs.map((job) => {
                  const p = normalizeProgress(job.progress);
                  return (
                    <Card key={job.id} className="overflow-hidden">
                      <CardContent className="p-0 sm:p-4 md:p-6">
                        <div>
                          <Button
                            className="w-full p-6 text-left hover:bg-muted/50 transition-colors sm:p-4 md:p-6"
                            onClick={() => toggleJobExpansion(job.id)}
                          >
                            <div className="flex items-center justify-between w-full">
                              <div className="flex items-center gap-3">
                                {getJobIcon(job)}
                                <div>
                                  <div className="font-medium">{job.title}</div>
                                  {job.description && (
                                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                                      {job.description}
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <Badge
                                  variant={getStatusBadgeVariant(job.status)}
                                  className="flex items-center gap-1"
                                >
                                  {getStatusIcon(job.status)}
                                  {job.status}
                                </Badge>
                                {expandedJobs.has(job.id) ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </div>
                            </div>

                            {/* Progress */}
                            {job.status === "running" && (
                              <div className="mt-4">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                                    Progress
                                  </span>
                                  <span className="text-sm font-medium md:text-base lg:text-lg">
                                    {p.toFixed(1)}%
                                  </span>
                                </div>
                                <Progress value={p} className="h-2" />
                              </div>
                            )}
                          </Button>

                          {expandedJobs.has(job.id) && (
                            <div className="px-6 pb-6 space-y-4 border-t bg-muted/20">
                              {/* Job Details */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                                <div>
                                  <h5 className="font-medium mb-2">Job Information</h5>
                                  <div className="space-y-1 text-sm md:text-base lg:text-lg">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">ID:</span>
                                      <span className="font-mono">{job.id.slice(0, 8)}...</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Type:</span>
                                      <span>{job.kind}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Created:</span>
                                      <span>{new Date(job.created_at).toLocaleString()}</span>
                                    </div>
                                    {job.started_at && (
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">Started:</span>
                                        <span>{new Date(job.started_at).toLocaleString()}</span>
                                      </div>
                                    )}
                                    {job.estimated_duration && (
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">Est. Duration:</span>
                                        <span>{formatDuration(job.estimated_duration)}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {/* Resource Usage */}
                                {job.resource_usage && (
                                  <div>
                                    <h5 className="font-medium mb-2">Resource Usage</h5>
                                    <div className="space-y-2">
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                          <Cpu className="h-4 w-4" />
                                          <span className="text-sm md:text-base lg:text-lg">CPU</span>
                                        </div>
                                        <span className="text-sm font-medium md:text-base lg:text-lg">
                                          {job.resource_usage.cpu_percent.toFixed(1)}%
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                          <MemoryStick className="h-4 w-4" />
                                          <span className="text-sm md:text-base lg:text-lg">Memory</span>
                                        </div>
                                        <span className="text-sm font-medium md:text-base lg:text-lg">
                                          {job.resource_usage.memory_mb.toFixed(0)} MB
                                        </span>
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                          <HardDrive className="h-4 w-4" />
                                          <span className="text-sm md:text-base lg:text-lg">Disk I/O</span>
                                        </div>
                                        <span className="text-sm font-medium md:text-base lg:text-lg">
                                          {job.resource_usage.disk_io_mb.toFixed(1)} MB/s
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Job Controls */}
                              <div className="flex gap-2">
                                {job.status === "running" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => controlJob(job.id, "pause")}
                                  >
                                    <Pause className="h-4 w-4 mr-2" />
                                    Pause
                                  </Button>
                                )}
                                {job.status === "paused" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => controlJob(job.id, "resume")}
                                  >
                                    <Play className="h-4 w-4 mr-2" />
                                    Resume
                                  </Button>
                                )}
                                {["running", "paused", "queued"].includes(job.status) && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => controlJob(job.id, "cancel")}
                                  >
                                    <Square className="h-4 w-4 mr-2" />
                                    Cancel
                                  </Button>
                                )}
                              </div>

                              {/* Recent Logs */}
                              {job.logs.length > 0 && (
                                <div>
                                  <h5 className="font-medium mb-2">Recent Logs</h5>
                                  <ScrollArea className="h-32 w-full border rounded-md p-3 bg-background sm:p-4 md:p-6">
                                    <div className="space-y-1">
                                      {job.logs.slice(-10).map((log, idx) => (
                                        <div
                                          key={`${job.id}-log-${idx}`}
                                          className="text-xs font-mono text-muted-foreground sm:text-sm md:text-base"
                                        >
                                          {log}
                                        </div>
                                      ))}
                                    </div>
                                  </ScrollArea>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>

          {/* Completed (History) */}
          <TabsContent value="completed" className="space-y-4">
            {completedJobs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">No Job History</p>
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Completed jobs will appear here for review and cleanup.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {completedJobs.map((job) => (
                  <Card key={job.id}>
                    <CardContent className="p-6 sm:p-4 md:p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getJobIcon(job)}
                          <div>
                            <div className="font-medium">{job.title}</div>
                            {job.description && (
                              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                                {job.description}
                              </div>
                            )}
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground sm:text-sm md:text-base">
                              <div className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {new Date(job.created_at).toLocaleDateString()}
                              </div>
                              {job.completed_at && job.started_at && (
                                <div className="flex items-center gap-1">
                                  <Timer className="h-3 w-3" />
                                  {formatDuration(job.completed_at - job.started_at)}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge
                            variant={getStatusBadgeVariant(job.status)}
                            className="flex items-center gap-1"
                          >
                            {getStatusIcon(job.status)}
                            {job.status}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteJob(job.id)}
                            aria-label="Delete job"
                          >
                            <Square className="sr-only h-0 w-0" />
                            {/* using Trash2 styling, but Square was imported earlier; keep icons minimal */}
                            <span className="inline-flex">
                              <XCircle className="h-4 w-4" />
                            </span>
                          </Button>
                        </div>
                      </div>

                      {job.error_message && (
                        <Alert variant="destructive" className="mt-4">
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>Error</AlertTitle>
                          <AlertDescription>{job.error_message}</AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Storage */}
          <TabsContent value="storage" className="space-y-4">
            {storageInfo ? (
              <>
                {/* Storage Overview */}
                <Card>
                  <CardHeader>
                    <CardTitle>Storage Overview</CardTitle>
                    <CardDescription></CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Disk Usage */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium md:text-base lg:text-lg">Disk Usage</span>
                          <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            {formatFileSizeGB(storageInfo.used_space_gb)} /{" "}
                            {formatFileSizeGB(storageInfo.total_space_gb)}
                          </span>
                        </div>
                        <Progress
                          value={(storageInfo.used_space_gb / storageInfo.total_space_gb) * 100}
                          className="h-3"
                        />
                      </div>

                      {/* Storage Stats */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="text-lg font-bold">
                            {formatFileSizeGB(storageInfo.available_space_gb)}
                          </div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            Available
                          </div>
                        </div>
                        <div className="text-center p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="text-lg font-bold">{storageInfo.model_count}</div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            Models
                          </div>
                        </div>
                        <div className="text-center p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="text-lg font-bold">
                            {formatFileSizeGB(storageInfo.largest_model_gb)}
                          </div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            Largest Model
                          </div>
                        </div>
                        <div className="text-center p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="text-lg font-bold">
                            {storageInfo.cleanup_candidates.length}
                          </div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            Cleanup Items
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Cleanup Candidates */}
                {storageInfo.cleanup_candidates.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Storage Cleanup</CardTitle>
                      <CardDescription></CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {storageInfo.cleanup_candidates.map((c, idx) => (
                          <div
                            key={`${c.path}-${idx}`}
                            className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                          >
                            <div className="flex items-center gap-3">
                              <FileText className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <div className="font-medium text-sm md:text-base lg:text-lg">
                                  {c.path.split("/").pop()}
                                </div>
                                <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                                  {c.type} • {formatFileSizeGB(c.size_gb)} • Last accessed{" "}
                                  {new Date(c.last_accessed).toLocaleDateString()}
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => cleanupStorage([c.path])}
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Remove
                            </Button>
                          </div>
                        ))}
                        {storageInfo.cleanup_candidates.length > 1 && (
                          <Button
                            variant="outline"
                            className="w-full"
                            onClick={() =>
                              cleanupStorage(storageInfo.cleanup_candidates.map((c) => c.path))
                            }
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            Clean All (
                            {formatFileSizeGB(
                              storageInfo.cleanup_candidates.reduce((sum, c) => sum + c.size_gb, 0)
                            )}
                            )
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <HardDrive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">Storage Information Unavailable</p>
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    Could not load storage information. Try refreshing the page.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </ErrorBoundary>
  );
}
