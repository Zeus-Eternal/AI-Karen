"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  HardDrive,
  Loader2,
  Pause,
  Play,
  RefreshCw,
  Save,
  Shield,
  ShieldAlert,
  Square,
  TimerReset,
  Trash2,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type DownloadPolicy = {
  master_enabled: boolean;
  core_runtime_enabled: boolean;
  plugin_channels_enabled: boolean;
  image_channels_enabled: boolean;
  audio_channels_enabled: boolean;
  vision_channels_enabled: boolean;
  gguf_external_enabled: boolean;
  trust_remote_code: boolean;
  block_new_downloads: boolean;
  pause_active_downloads: boolean;
  quarantine_failed_models: boolean;
  require_license_acceptance: boolean;
  max_concurrent_downloads: number;
};

type DownloadChannel = {
  id: string;
  label: string;
  group: string;
  storage_key: string;
  enabled: boolean;
  effective_enabled: boolean;
  locked_by_master: boolean;
  description: string;
  model_families: string[];
  modalities: string[];
  admin_only: boolean;
};

type DownloadJob = {
  job_id: string;
  model_id: string;
  revision?: string | null;
  channel_id: string;
  storage_key?: string | null;
  status: string;
  progress: number;
  message: string;
  error?: string | null;
  result?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  requested_by?: string | null;
  trust_remote_code: boolean;
  license_accepted: boolean;
  include_patterns?: string[] | null;
  exclude_patterns?: string[] | null;
  pin: boolean;
  force_redownload: boolean;
  pause_requested: boolean;
  cancel_requested: boolean;
  warnings: string[];
  detected_runtime?: string | null;
  detected_modality?: string | null;
  install_path?: string | null;
  channel?: DownloadChannel | null;
};

type DownloadValidation = {
  allowed: boolean;
  channel_id: string;
  model_id: string;
  revision?: string | null;
  storage_key?: string | null;
  install_path?: string | null;
  detected_runtime?: string | null;
  detected_modality?: string | null;
  warnings: string[];
  blocking_reasons: string[];
  license_required: boolean;
  trust_remote_code_allowed: boolean;
  metadata: Record<string, unknown>;
};

type InstalledModelsResponse = {
  models: Array<Record<string, unknown>>;
  total: number;
  statistics: Record<string, unknown>;
};

type DiscoverySnapshot = {
  progress: Record<string, unknown>;
  statistics: Record<string, unknown>;
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    if (typeof error.details === "string" && error.details.trim()) {
      return error.details.trim();
    }
    if (error.message.trim()) {
      return error.message.trim();
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }
  return fallback;
}

function parseCsvList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function statusTone(status: string): string {
  switch (status) {
    case "completed":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700";
    case "running":
      return "border-blue-500/30 bg-blue-500/10 text-blue-700";
    case "queued":
    case "paused":
    case "pause_requested":
      return "border-amber-500/30 bg-amber-500/10 text-amber-700";
    case "failed":
    case "cancelled":
      return "border-red-500/30 bg-red-500/10 text-red-700";
    default:
      return "border-border/60 bg-muted/20 text-muted-foreground";
  }
}

function groupChannels(channels: DownloadChannel[]): Record<string, DownloadChannel[]> {
  return channels.reduce<Record<string, DownloadChannel[]>>((acc, channel) => {
    const bucket = channel.group || "other";
    acc[bucket] = acc[bucket] || [];
    acc[bucket].push(channel);
    return acc;
  }, {});
}

function isVllmCompatibleModel(model: Record<string, unknown>): boolean {
  const preferredRuntime = String(model.preferred_runtime || "").toLowerCase();
  if (preferredRuntime === "vllm" || preferredRuntime === "builtin_vllm") {
    return true;
  }
  const compatibleRuntimes = Array.isArray(model.compatible_runtimes)
    ? model.compatible_runtimes.map((runtime) => String(runtime).toLowerCase())
    : [];
  return compatibleRuntimes.includes("vllm") || compatibleRuntimes.includes("builtin_vllm");
}

function sortInstalledModels(models: Array<Record<string, unknown>>): Array<Record<string, unknown>> {
  return [...models].sort((left, right) => {
    const leftVllm = isVllmCompatibleModel(left) ? 0 : 1;
    const rightVllm = isVllmCompatibleModel(right) ? 0 : 1;
    if (leftVllm !== rightVllm) return leftVllm - rightVllm;
    const leftRuntime = String(left.preferred_runtime || left.model_format || "").toLowerCase();
    const rightRuntime = String(right.preferred_runtime || right.model_format || "").toLowerCase();
    if (leftRuntime !== rightRuntime) return leftRuntime.localeCompare(rightRuntime);
    const leftName = String(left.display_name || left.name || left.model_id || "").toLowerCase();
    const rightName = String(right.display_name || right.name || right.model_id || "").toLowerCase();
    return leftName.localeCompare(rightName);
  });
}

interface ModelDownloadsProps {
  adminMode?: boolean;
}

export default function ModelDownloads({ adminMode = false }: ModelDownloadsProps) {
  const { toast } = useToast();
  const [policy, setPolicy] = useState<DownloadPolicy | null>(null);
  const [channels, setChannels] = useState<DownloadChannel[]>([]);
  const [jobs, setJobs] = useState<DownloadJob[]>([]);
  const [installed, setInstalled] = useState<InstalledModelsResponse | null>(null);
  const [discovery, setDiscovery] = useState<DiscoverySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingPolicy, setSavingPolicy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [startingDownload, setStartingDownload] = useState(false);
  const [validation, setValidation] = useState<DownloadValidation | null>(null);

  const [modelId, setModelId] = useState("");
  const [revision, setRevision] = useState("");
  const [channelId, setChannelId] = useState("");
  const [includePatterns, setIncludePatterns] = useState("");
  const [excludePatterns, setExcludePatterns] = useState("");
  const [acceptLicense, setAcceptLicense] = useState(false);
  const [trustRemoteCode, setTrustRemoteCode] = useState(false);

  const loadState = useCallback(async () => {
    setLoading(true);
    try {
      const [policyResponse, channelsResponse, jobsResponse, installedResponse, discoveryResponse] = await Promise.all([
        apiClient.get<DownloadPolicy>("/api/models/download/policy"),
        apiClient.get<{ policy: DownloadPolicy; channels: DownloadChannel[] }>("/api/models/download/channels"),
        apiClient.get<DownloadJob[]>("/api/models/download/jobs?limit=50"),
        apiClient.get<InstalledModelsResponse>("/api/models/installed?force_refresh=false"),
        apiClient.get<DiscoverySnapshot>("/api/models/discovery?force_refresh=false"),
      ]);

      setPolicy(policyResponse);
      setChannels(Array.isArray(channelsResponse.channels) ? channelsResponse.channels : []);
      setJobs(Array.isArray(jobsResponse) ? jobsResponse : []);
      setInstalled(installedResponse);
      setDiscovery(discoveryResponse);
      setChannelId((current) => current || channelsResponse.channels?.[0]?.id || current);
    } catch (error) {
      toast({
        title: "Unable to load model downloads",
        description: getErrorMessage(error, "Karen could not load the model downloads control plane."),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadState();
  }, [loadState]);

  const groupedChannels = useMemo(() => groupChannels(channels), [channels]);
  const currentChannel = useMemo(
    () => channels.find((channel) => channel.id === channelId) ?? channels[0] ?? null,
    [channels, channelId],
  );
  const queueCount = useMemo(() => jobs.filter((job) => job.status === "queued" || job.status === "running" || job.status === "paused" || job.status === "pause_requested").length, [jobs]);

  const updatePolicyField = <K extends keyof DownloadPolicy>(key: K, value: DownloadPolicy[K]) => {
    setPolicy((current) => (current ? { ...current, [key]: value } : current));
  };

  const savePolicy = async () => {
    if (!policy) return;
    setSavingPolicy(true);
    try {
      const response = await apiClient.put<DownloadPolicy>("/api/models/download/policy", policy);
      setPolicy(response);
      toast({
        title: "Download policy saved",
        description: "Model download safety settings were updated.",
      });
    } catch (error) {
      toast({
        title: "Unable to save policy",
        description: getErrorMessage(error, "Karen could not save the model download policy."),
        variant: "destructive",
      });
    } finally {
      setSavingPolicy(false);
    }
  };

  const refreshAll = async () => {
    setRefreshing(true);
    try {
      await loadState();
    } finally {
      setRefreshing(false);
    }
  };

  const validateDownload = async () => {
    if (!modelId.trim()) {
      toast({
        title: "Model ID required",
        description: "Enter a Hugging Face model identifier like owner/repo.",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await apiClient.post<DownloadValidation>("/api/models/download/validate", {
        model_id: modelId.trim(),
        revision: revision.trim() || null,
        channel_id: channelId || null,
        trust_remote_code: trustRemoteCode,
        accept_license: acceptLicense,
        include_patterns: parseCsvList(includePatterns),
        exclude_patterns: parseCsvList(excludePatterns),
      });
      setValidation(response);
      toast({
        title: response.allowed ? "Validation passed" : "Validation blocked",
        description: response.allowed
          ? `Model will install to ${response.install_path ?? "the configured channel"}.`
          : response.blocking_reasons.join("; "),
        variant: response.allowed ? "default" : "destructive",
      });
    } catch (error) {
      toast({
        title: "Validation failed",
        description: getErrorMessage(error, "Karen could not validate the requested download."),
        variant: "destructive",
      });
    }
  };

  const startDownload = async () => {
    if (!modelId.trim()) {
      toast({
        title: "Model ID required",
        description: "Enter a Hugging Face model identifier before starting a download.",
        variant: "destructive",
      });
      return;
    }

    setStartingDownload(true);
    try {
      const response = await apiClient.post<{ job_id: string; message: string; status: string }>("/api/models/download", {
        model_id: modelId.trim(),
        revision: revision.trim() || null,
        channel_id: channelId || null,
        include_patterns: parseCsvList(includePatterns),
        exclude_patterns: parseCsvList(excludePatterns),
        trust_remote_code: trustRemoteCode,
        accept_license: acceptLicense,
      });

      toast({
        title: "Download queued",
        description: `${response.job_id} is now ${response.status}.`,
      });
      await refreshAll();
    } catch (error) {
      toast({
        title: "Download failed",
        description: getErrorMessage(error, "Karen could not queue the model download."),
        variant: "destructive",
      });
    } finally {
      setStartingDownload(false);
    }
  };

  const actOnJob = async (jobId: string, action: "cancel" | "pause" | "resume") => {
    try {
      await apiClient.post(`/api/models/download/jobs/${jobId}/${action}`, {});
      await refreshAll();
      toast({
        title: action === "cancel" ? "Job cancelled" : action === "pause" ? "Job paused" : "Job resumed",
        description: `Download job ${jobId} was updated.`,
      });
    } catch (error) {
      toast({
        title: `Unable to ${action} job`,
        description: getErrorMessage(error, `Karen could not ${action} the download job.`),
        variant: "destructive",
      });
    }
  };

  const renderPolicyRow = (
    label: string,
    description: string,
    key: keyof DownloadPolicy,
    disabled?: boolean,
  ) => {
    if (!policy) return null;
    const value = policy[key];
    return (
      <div className="flex items-start justify-between gap-4 rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-foreground">{label}</div>
          <div className="text-xs text-muted-foreground">{description}</div>
        </div>
        <Switch
          checked={Boolean(value)}
          disabled={disabled}
          onCheckedChange={(checked) => updatePolicyField(key, checked as never)}
        />
      </div>
    );
  };

  const installedModels = useMemo(() => sortInstalledModels(installed?.models ?? []), [installed]);
  const vllmInstalledModels = useMemo(
    () => installedModels.filter((model) => isVllmCompatibleModel(model)),
    [installedModels],
  );
  const otherInstalledModels = useMemo(
    () => installedModels.filter((model) => !isVllmCompatibleModel(model)),
    [installedModels],
  );
  const discoveryProgress = discovery?.progress ?? {};
  const discoveryStats = discovery?.statistics ?? {};

  return (
    <div className="space-y-6">
      <Card className="border-border/50 bg-gradient-to-br from-card via-card to-muted/20">
        <CardHeader>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <HardDrive className="h-5 w-5 text-primary" />
                Model Downloads
              </CardTitle>
              <CardDescription>
                Core download policy, plugin channel gates, queue state, and installed model inventory.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{queueCount} queued</Badge>
              <Badge variant="outline">{installedModels.length} installed</Badge>
              <Button variant="outline" size="sm" onClick={() => void refreshAll()} disabled={refreshing}>
                {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="h-4 w-4 text-primary" />
              Download Safety Panel
            </CardTitle>
            <CardDescription>Master gate first, then category switches, then channel-specific overrides.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading || !policy ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading policy...
              </div>
            ) : (
              <>
                {renderPolicyRow("Master Downloads", "Disable all download activity across runtime and plugin channels.", "master_enabled")}
                {renderPolicyRow("Core Runtime Models", "Transformers, embeddings, rerankers, ONNX, and GGUF channels.", "core_runtime_enabled")}
                {renderPolicyRow("Plugin Channels", "Image, audio, vision, and plugin-private model channels.", "plugin_channels_enabled")}
                <div className="grid gap-3 md:grid-cols-2">
                  {renderPolicyRow("Image Models", "SD, FLUX, and diffusion pipelines.", "image_channels_enabled")}
                  {renderPolicyRow("Audio Models", "TTS and STT downloads.", "audio_channels_enabled")}
                  {renderPolicyRow("Vision / OCR", "OCR, document understanding, and multimodal helpers.", "vision_channels_enabled")}
                  {renderPolicyRow("GGUF External Only", "Allow external GGUF snapshots for local inference.", "gguf_external_enabled")}
                </div>
                <div className="flex items-start justify-between gap-4 rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                  <div className="space-y-1">
                    <div className="text-sm font-semibold text-foreground">trust_remote_code</div>
                    <div className="text-xs text-muted-foreground">
                      {adminMode ? "Admin-only. Locked off by default." : "Locked by admin policy."}
                    </div>
                  </div>
                  <Switch
                    checked={policy.trust_remote_code}
                    disabled={!adminMode}
                    onCheckedChange={(checked) => updatePolicyField("trust_remote_code", checked)}
                  />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {renderPolicyRow("Block New Downloads", "Prevent new jobs from entering the queue.", "block_new_downloads")}
                  {renderPolicyRow("Pause Active Downloads", "Best-effort pause gate for active jobs.", "pause_active_downloads")}
                  {renderPolicyRow("Quarantine Failed Models", "Mark failed artifacts as quarantined in discovery.", "quarantine_failed_models")}
                  {renderPolicyRow("Require License Acceptance", "Record acceptance before the executor starts.", "require_license_acceptance")}
                </div>
                <div className="space-y-2 rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                  <Label htmlFor="max-concurrent-downloads">Max concurrent downloads</Label>
                  <Input
                    id="max-concurrent-downloads"
                    type="number"
                    min={1}
                    max={8}
                    value={policy.max_concurrent_downloads}
                    onChange={(event) => updatePolicyField("max_concurrent_downloads", Number(event.target.value) || 1)}
                  />
                </div>
                <div className="flex justify-end">
                  <Button onClick={() => void savePolicy()} disabled={savingPolicy}>
                    {savingPolicy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Policy
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Download className="h-4 w-4 text-primary" />
              Start Download
            </CardTitle>
            <CardDescription>Validate first, then queue the model through the control plane.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="model-id">Hugging Face model ID</Label>
              <Input
                id="model-id"
                placeholder="owner/repo"
                value={modelId}
                onChange={(event) => setModelId(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="revision">Revision</Label>
              <Input
                id="revision"
                placeholder="main, commit SHA, or tag"
                value={revision}
                onChange={(event) => setRevision(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="channel">Channel</Label>
              <Select value={channelId} onValueChange={setChannelId}>
                <SelectTrigger id="channel">
                  <SelectValue placeholder="Select download channel" />
                </SelectTrigger>
                <SelectContent>
                  {channels.map((channel) => (
                    <SelectItem key={channel.id} value={channel.id}>
                      {channel.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {currentChannel && (
                <p className="text-xs text-muted-foreground">
                  {currentChannel.description} Storage root: <span className="font-mono">{currentChannel.storage_key}</span>
                </p>
              )}
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="include-patterns">Include patterns</Label>
                <Input
                  id="include-patterns"
                  placeholder="*.safetensors, *.json"
                  value={includePatterns}
                  onChange={(event) => setIncludePatterns(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="exclude-patterns">Exclude patterns</Label>
                <Input
                  id="exclude-patterns"
                  placeholder="*.bin, *.msgpack"
                  value={excludePatterns}
                  onChange={(event) => setExcludePatterns(event.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="flex items-start justify-between gap-4 rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                <div className="space-y-1">
                  <div className="text-sm font-semibold">Accept license</div>
                  <div className="text-xs text-muted-foreground">Required when policy marks the model as gated.</div>
                </div>
                <Switch checked={acceptLicense} onCheckedChange={setAcceptLicense} />
              </div>
              <div className="flex items-start justify-between gap-4 rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                <div className="space-y-1">
                  <div className="text-sm font-semibold">trust_remote_code</div>
                  <div className="text-xs text-muted-foreground">
                    {adminMode ? "Admin-controlled execution of remote code." : "Locked off until admin enables it."}
                  </div>
                </div>
                <Switch checked={trustRemoteCode} disabled={!adminMode} onCheckedChange={setTrustRemoteCode} />
              </div>
            </div>
            {validation && (
              <div
                className={[
                  "rounded-xl border px-4 py-3",
                  validation.allowed ? "border-emerald-500/30 bg-emerald-500/10" : "border-red-500/30 bg-red-500/10",
                ].join(" ")}
              >
                <div className="flex items-center gap-2 text-sm font-semibold">
                  {validation.allowed ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <ShieldAlert className="h-4 w-4 text-red-600" />}
                  {validation.allowed ? "Validation passed" : "Validation blocked"}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {validation.install_path ? `Install path: ${validation.install_path}` : "No install path resolved."}
                </div>
                {validation.warnings.length > 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">{validation.warnings.join(" • ")}</p>
                )}
                {validation.blocking_reasons.length > 0 && (
                  <p className="mt-2 text-xs font-medium text-red-700">{validation.blocking_reasons.join(" • ")}</p>
                )}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => void validateDownload()}>
                Validate
              </Button>
              <Button onClick={() => void startDownload()} disabled={startingDownload}>
                {startingDownload ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
                Queue Download
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Pause and cancel are best-effort once the executor is already running.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Square className="h-4 w-4 text-primary" />
              Download Queue
            </CardTitle>
            <CardDescription>Queued, running, paused, cancelled, and completed jobs.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {jobs.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border/50 p-4 text-sm text-muted-foreground">
                No download jobs yet.
              </div>
            ) : (
              jobs.map((job) => (
                <div key={job.job_id} className="rounded-xl border border-border/50 bg-muted/20 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-sm font-semibold text-foreground">{job.model_id}</div>
                        <Badge variant="outline" className={statusTone(job.status)}>
                          {job.status}
                        </Badge>
                        {job.channel?.label && <Badge variant="secondary">{job.channel.label}</Badge>}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Job {job.job_id} • {job.requested_by || "unknown"} • {job.revision || "main"}
                      </div>
                      <div className="text-xs text-muted-foreground">{job.message}</div>
                      {job.error && <div className="text-xs font-medium text-red-600">{job.error}</div>}
                      <div className="text-xs text-muted-foreground">
                        {job.install_path ? `Path: ${job.install_path}` : ""} {job.install_path ? " • " : ""} {job.detected_runtime || "runtime pending"}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => void actOnJob(job.job_id, "pause")}>
                        <Pause className="mr-2 h-3.5 w-3.5" />
                        Pause
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => void actOnJob(job.job_id, "resume")}>
                        <Play className="mr-2 h-3.5 w-3.5" />
                        Resume
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => void actOnJob(job.job_id, "cancel")}>
                        <Trash2 className="mr-2 h-3.5 w-3.5" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(Math.max(job.progress * 100, 0), 100)}%` }} />
                  </div>
                  {job.warnings.length > 0 && <p className="mt-2 text-xs text-muted-foreground">{job.warnings.join(" • ")}</p>}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <HardDrive className="h-4 w-4 text-primary" />
              Installed Models
            </CardTitle>
            <CardDescription>What discovery found on disk after downloads and local scans.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
              <div>
                <div className="text-sm font-semibold">{installedModels.length} models</div>
                <div className="text-xs text-muted-foreground">
                  {formatBytes(Number(discoveryStats?.total_disk_usage_bytes || 0))} total disk usage from local inventory.
                </div>
              </div>
              <Badge variant="outline">{String(discoveryStats?.status || "unknown")}</Badge>
            </div>
            <Separator className="bg-border/40" />
            <div className="space-y-4 max-h-[28rem] overflow-auto pr-1">
              {installedModels.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/50 p-4 text-sm text-muted-foreground">
                  No installed models discovered yet.
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground">vLLM Compatible</div>
                    {vllmInstalledModels.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border/50 p-4 text-sm text-muted-foreground">
                        No vLLM-compatible models discovered yet.
                      </div>
                    ) : (
                      vllmInstalledModels.map((model) => {
                        const modelIdValue = String(model.model_id || model.display_name || model.name || "unknown");
                        return (
                          <div key={modelIdValue} className="rounded-xl border border-border/50 bg-muted/20 p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-1">
                                <div className="text-sm font-semibold">{String(model.display_name || model.name || modelIdValue)}</div>
                                <div className="text-xs text-muted-foreground font-mono">{modelIdValue}</div>
                              </div>
                              <Badge variant="secondary">{String(model.preferred_runtime || model.model_format || "unknown")}</Badge>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {Array.isArray(model.capabilities) && model.capabilities.map((capability) => (
                                <Badge key={String(capability)} variant="outline">{String(capability)}</Badge>
                              ))}
                            </div>
                            <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                              <div>Runtime: {String(model.preferred_runtime || "unknown")}</div>
                              <div>Compatible: {Array.isArray(model.compatible_runtimes) ? model.compatible_runtimes.join(", ") : "n/a"}</div>
                              <div>Size: {formatBytes(Number(model.size_bytes || model.size || 0))}</div>
                              <div>Path: {String(model.path || model.relative_path || "n/a")}</div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Other Installed Models</div>
                    {otherInstalledModels.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border/50 p-4 text-sm text-muted-foreground">
                        No non-vLLM installed models discovered.
                      </div>
                    ) : (
                      otherInstalledModels.map((model) => {
                        const modelIdValue = String(model.model_id || model.display_name || model.name || "unknown");
                        return (
                          <div key={modelIdValue} className="rounded-xl border border-border/50 bg-muted/20 p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-1">
                                <div className="text-sm font-semibold">{String(model.display_name || model.name || modelIdValue)}</div>
                                <div className="text-xs text-muted-foreground font-mono">{modelIdValue}</div>
                              </div>
                              <Badge variant="secondary">{String(model.model_format || "unknown")}</Badge>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {Array.isArray(model.capabilities) && model.capabilities.map((capability) => (
                                <Badge key={String(capability)} variant="outline">{String(capability)}</Badge>
                              ))}
                            </div>
                            <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                              <div>Runtime: {String(model.preferred_runtime || "unknown")}</div>
                              <div>Compatible: {Array.isArray(model.compatible_runtimes) ? model.compatible_runtimes.join(", ") : "n/a"}</div>
                              <div>Size: {formatBytes(Number(model.size_bytes || model.size || 0))}</div>
                              <div>Status: {String(model.status || "available")}</div>
                              <div>Path: {String(model.path || model.relative_path || "n/a")}</div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TimerReset className="h-4 w-4 text-primary" />
              Discovery Snapshot
            </CardTitle>
            <CardDescription>Core discovery is the source of truth for installed models and runtime compatibility.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
              <div className="text-sm font-semibold">Status: {String(discoveryProgress.status || "unknown")}</div>
              <div className="text-xs text-muted-foreground">
                Scanned {String(discoveryProgress.total_scanned || 0)} roots, discovered {String(discoveryProgress.discovered_models || 0)} models.
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Formats</div>
                <div className="mt-1 text-sm font-semibold">{Object.keys((discoveryStats.formats as Record<string, unknown>) || {}).join(", ") || "None"}</div>
              </div>
              <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Runtimes</div>
                <div className="mt-1 text-sm font-semibold">{Object.keys((discoveryStats.runtimes as Record<string, unknown>) || {}).join(", ") || "None"}</div>
              </div>
            </div>
            <Button variant="outline" className="w-full" onClick={() => void refreshAll()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh discovery and queue
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <AlertTriangle className="h-4 w-4 text-primary" />
              Channel Structure
            </CardTitle>
            <CardDescription>Relative categories reflect core runtime and plugin-specific download lanes.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(groupedChannels).map(([group, groupChannelsList]) => (
              <div key={group} className="space-y-2">
                <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground">{group.replace("_", " ")}</div>
                <div className="grid gap-2">
                  {groupChannelsList.map((channel) => (
                    <div key={channel.id} className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold">{channel.label}</div>
                          <div className="text-xs text-muted-foreground">{channel.description}</div>
                        </div>
                        <Badge variant={channel.effective_enabled ? "default" : "outline"}>{channel.effective_enabled ? "ON" : "OFF"}</Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {channel.model_families.map((family) => (
                          <Badge key={family} variant="outline">
                            {family}
                          </Badge>
                        ))}
                        {channel.admin_only && <Badge variant="secondary">admin only</Badge>}
                        {channel.locked_by_master && <Badge variant="destructive">master locked</Badge>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
