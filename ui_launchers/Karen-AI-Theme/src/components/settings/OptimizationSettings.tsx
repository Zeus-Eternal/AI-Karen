"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, Cpu, Gauge, RefreshCw, Save, ServerCog, Zap } from "lucide-react";

import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

type OptimizationConfigResponse = {
  optimization_enabled: boolean;
  optimization_level: string;
  config_version: string;
  last_updated: string;
  components: Record<string, boolean>;
  reasoning_preservation: Record<string, boolean>;
  validation_status: boolean;
  auto_save_enabled: boolean;
};

type OptimizationStatusResponse = {
  configuration_summary?: {
    components?: Record<string, boolean>;
  };
  component_status?: Record<string, Record<string, unknown>>;
  gpu_runtime?: {
    snapshot?: {
      runtime?: {
        cuda_enabled?: boolean;
        initialized?: boolean;
        auto_detect_devices?: boolean;
        preferred_device_id?: number | null;
        memory_fraction?: number;
        memory_optimization_enabled?: boolean;
        batch_processing_enabled?: boolean;
        cpu_fallback_enabled?: boolean;
      };
      capabilities?: {
        torch_available?: boolean;
        cupy_available?: boolean;
        pynvml_available?: boolean;
      };
      cuda?: {
        available?: boolean;
        device_count?: number;
        cuda_version?: string | null;
        driver_version?: string | null;
        devices?: Array<{
          id: number;
          name: string;
          compute_capability?: string | null;
          memory_total?: number;
          memory_free?: number;
          memory_used?: number;
          utilization?: number;
          temperature?: number;
          power_usage?: number;
        }>;
      };
    };
    summary?: {
      cuda_available?: boolean;
      initialized?: boolean;
      device_count?: number;
      current_metrics?: {
        utilization?: number;
        memory_usage?: number;
        temperature?: number;
        power_usage?: number;
        inference_throughput?: number;
        batch_efficiency?: number;
      };
      cached_models?: number;
      memory_handles?: number;
      batch_queue_size?: number;
      error?: string;
    };
  };
};

type PerformanceOptimizationConfigResponse = {
  configuration?: {
    enable_optimization_system?: boolean;
    optimization_level?: string;
    cuda?: {
      enable_cuda?: boolean;
      auto_detect_devices?: boolean;
      preferred_device_id?: number | null;
      memory_fraction?: number;
      enable_memory_optimization?: boolean;
      enable_batch_processing?: boolean;
      fallback_to_cpu?: boolean;
    };
    performance?: {
      enable_optimization?: boolean;
      optimization_interval_seconds?: number;
      enable_performance_alerts?: boolean;
    };
    streaming?: {
      enable_streaming?: boolean;
      streaming_timeout_seconds?: number;
      enable_real_time_feedback?: boolean;
    };
    monitoring?: {
      enable_monitoring?: boolean;
      enable_real_time_alerts?: boolean;
      metrics_retention_hours?: number;
    };
  };
  deployment_profile?: string;
  validation_status?: unknown;
};

type OptimizationFormState = {
  enableOptimizationSystem: boolean;
  optimizationLevel: string;
  enableCuda: boolean;
  autoDetectDevices: boolean;
  preferredDeviceId: string;
  memoryFraction: string;
  enableMemoryOptimization: boolean;
  enableBatchProcessing: boolean;
  fallbackToCpu: boolean;
  enablePerformanceOptimization: boolean;
  optimizationIntervalSeconds: string;
  enablePerformanceAlerts: boolean;
  enableStreaming: boolean;
  streamingTimeoutSeconds: string;
  enableRealtimeFeedback: boolean;
  enableMonitoring: boolean;
  enableRealtimeAlerts: boolean;
  metricsRetentionHours: string;
};

const DEFAULT_FORM_STATE: OptimizationFormState = {
  enableOptimizationSystem: true,
  optimizationLevel: "balanced",
  enableCuda: true,
  autoDetectDevices: true,
  preferredDeviceId: "auto",
  memoryFraction: "0.8",
  enableMemoryOptimization: true,
  enableBatchProcessing: true,
  fallbackToCpu: true,
  enablePerformanceOptimization: true,
  optimizationIntervalSeconds: "60",
  enablePerformanceAlerts: true,
  enableStreaming: true,
  streamingTimeoutSeconds: "30",
  enableRealtimeFeedback: true,
  enableMonitoring: true,
  enableRealtimeAlerts: true,
  metricsRetentionHours: "24",
};

function toFormState(config?: PerformanceOptimizationConfigResponse["configuration"]): OptimizationFormState {
  return {
    enableOptimizationSystem: config?.enable_optimization_system ?? DEFAULT_FORM_STATE.enableOptimizationSystem,
    optimizationLevel: config?.optimization_level ?? DEFAULT_FORM_STATE.optimizationLevel,
    enableCuda: config?.cuda?.enable_cuda ?? DEFAULT_FORM_STATE.enableCuda,
    autoDetectDevices: config?.cuda?.auto_detect_devices ?? DEFAULT_FORM_STATE.autoDetectDevices,
    preferredDeviceId: config?.cuda?.preferred_device_id == null ? "auto" : String(config.cuda.preferred_device_id),
    memoryFraction: String(config?.cuda?.memory_fraction ?? DEFAULT_FORM_STATE.memoryFraction),
    enableMemoryOptimization: config?.cuda?.enable_memory_optimization ?? DEFAULT_FORM_STATE.enableMemoryOptimization,
    enableBatchProcessing: config?.cuda?.enable_batch_processing ?? DEFAULT_FORM_STATE.enableBatchProcessing,
    fallbackToCpu: config?.cuda?.fallback_to_cpu ?? DEFAULT_FORM_STATE.fallbackToCpu,
    enablePerformanceOptimization: config?.performance?.enable_optimization ?? DEFAULT_FORM_STATE.enablePerformanceOptimization,
    optimizationIntervalSeconds: String(config?.performance?.optimization_interval_seconds ?? DEFAULT_FORM_STATE.optimizationIntervalSeconds),
    enablePerformanceAlerts: config?.performance?.enable_performance_alerts ?? DEFAULT_FORM_STATE.enablePerformanceAlerts,
    enableStreaming: config?.streaming?.enable_streaming ?? DEFAULT_FORM_STATE.enableStreaming,
    streamingTimeoutSeconds: String(config?.streaming?.streaming_timeout_seconds ?? DEFAULT_FORM_STATE.streamingTimeoutSeconds),
    enableRealtimeFeedback: config?.streaming?.enable_real_time_feedback ?? DEFAULT_FORM_STATE.enableRealtimeFeedback,
    enableMonitoring: config?.monitoring?.enable_monitoring ?? DEFAULT_FORM_STATE.enableMonitoring,
    enableRealtimeAlerts: config?.monitoring?.enable_real_time_alerts ?? DEFAULT_FORM_STATE.enableRealtimeAlerts,
    metricsRetentionHours: String(config?.monitoring?.metrics_retention_hours ?? DEFAULT_FORM_STATE.metricsRetentionHours),
  };
}

function parseNumber(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export default function OptimizationSettings() {
  const { toast } = useToast();
  const [form, setForm] = useState<OptimizationFormState>(DEFAULT_FORM_STATE);
  const [configSummary, setConfigSummary] = useState<OptimizationConfigResponse | null>(null);
  const [status, setStatus] = useState<OptimizationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const [configSummaryResponse, performanceConfigResponse, statusResponse] = await Promise.all([
        apiClient.get<OptimizationConfigResponse>("/api/optimization/config"),
        apiClient.get<PerformanceOptimizationConfigResponse>("/api/performance/optimization/config"),
        apiClient.get<OptimizationStatusResponse>("/api/optimization/status"),
      ]);

      setConfigSummary(configSummaryResponse);
      setForm(toFormState(performanceConfigResponse.configuration));
      setStatus(statusResponse);
    } catch (error) {
      toast({
        title: "Unable to load optimization settings",
        description: error instanceof Error ? error.message : "Karen could not load acceleration settings.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  const availableRuntimeComponents = useMemo(() => {
    const summaryComponents = configSummary?.components ?? {};
    const statusComponents = status?.configuration_summary?.components ?? {};
    return {
      ...summaryComponents,
      ...statusComponents,
    };
  }, [configSummary, status]);

  const gpuRuntime = status?.gpu_runtime;
  const gpuSnapshot = gpuRuntime?.snapshot;
  const gpuSummary = gpuRuntime?.summary;
  const detectedDevices = gpuSnapshot?.cuda?.devices ?? [];
  const detectedDeviceIds = useMemo(() => new Set(detectedDevices.map((device) => String(device.id))), [detectedDevices]);
  const normalizedPreferredDeviceId =
    form.preferredDeviceId === "auto" || detectedDeviceIds.has(form.preferredDeviceId) ? form.preferredDeviceId : "auto";

  const handleSave = async () => {
    setSaving(true);
    try {
      const preferredDeviceIdForSave = normalizedPreferredDeviceId;
      const updates: Record<string, unknown> = {
        enable_optimization_system: form.enableOptimizationSystem,
        optimization_level: form.optimizationLevel,
        "cuda.enable_cuda": form.enableCuda,
        "cuda.auto_detect_devices": form.autoDetectDevices,
        "cuda.preferred_device_id": preferredDeviceIdForSave === "auto" ? null : parseNumber(preferredDeviceIdForSave, 0),
        "cuda.memory_fraction": parseNumber(form.memoryFraction, 0.8),
        "cuda.enable_memory_optimization": form.enableMemoryOptimization,
        "cuda.enable_batch_processing": form.enableBatchProcessing,
        "cuda.fallback_to_cpu": form.fallbackToCpu,
        "performance.enable_optimization": form.enablePerformanceOptimization,
        "performance.optimization_interval_seconds": parseNumber(form.optimizationIntervalSeconds, 60),
        "performance.enable_performance_alerts": form.enablePerformanceAlerts,
        "streaming.enable_streaming": form.enableStreaming,
        "streaming.streaming_timeout_seconds": parseNumber(form.streamingTimeoutSeconds, 30),
        "streaming.enable_real_time_feedback": form.enableRealtimeFeedback,
        "monitoring.enable_monitoring": form.enableMonitoring,
        "monitoring.enable_real_time_alerts": form.enableRealtimeAlerts,
        "monitoring.metrics_retention_hours": parseNumber(form.metricsRetentionHours, 24),
      };

      await apiClient.post("/api/optimization/config", {
        updates,
        validate: true,
      });

      toast({
        title: "Optimization settings saved",
        description: "CUDA and runtime acceleration settings were updated successfully.",
      });
      await loadSettings();
    } catch (error) {
      toast({
        title: "Save failed",
        description: error instanceof Error ? error.message : "Karen could not save optimization settings.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold tracking-tight">Runtime Optimization</h3>
          <p className="text-sm text-muted-foreground">
            Control CUDA acceleration, batch processing, performance monitoring, and production-safe fallbacks.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void loadSettings()} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {!configSummary?.validation_status && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Configuration requires attention</AlertTitle>
          <AlertDescription>
            One or more optimization values failed validation. Review CUDA memory fraction, timeouts, and monitoring thresholds.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              CUDA Acceleration
            </CardTitle>
            <CardDescription>
              Production runtime controls for GPU discovery, memory use, device preference, batching, and CPU fallback.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="optimization-level">Optimization profile</Label>
                <Select value={form.optimizationLevel} onValueChange={(value) => setForm((current) => ({ ...current, optimizationLevel: value }))}>
                  <SelectTrigger id="optimization-level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conservative">Conservative</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="aggressive">Aggressive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="preferred-device-id">Preferred GPU device</Label>
                <Select value={normalizedPreferredDeviceId} onValueChange={(value) => setForm((current) => ({ ...current, preferredDeviceId: value }))}>
                  <SelectTrigger id="preferred-device-id">
                    <SelectValue />
                  </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto select</SelectItem>
                      {detectedDevices.map((device) => (
                        <SelectItem key={device.id} value={String(device.id)}>
                          GPU {device.id}: {device.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gpu-memory-fraction">GPU memory fraction</Label>
                <Input
                  id="gpu-memory-fraction"
                  value={form.memoryFraction}
                  onChange={(event) => setForm((current) => ({ ...current, memoryFraction: event.target.value }))}
                  placeholder="0.8"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="optimization-interval">Optimization interval seconds</Label>
                <Input
                  id="optimization-interval"
                  value={form.optimizationIntervalSeconds}
                  onChange={(event) => setForm((current) => ({ ...current, optimizationIntervalSeconds: event.target.value }))}
                  placeholder="60"
                />
              </div>
            </div>

            <Separator />

            <div className="grid gap-4 md:grid-cols-2">
              {[
                ["enableOptimizationSystem", "Enable optimization system", "Master switch for runtime optimization and admin-managed performance controls."],
                ["enableCuda", "Enable CUDA acceleration", "Allow GPU acceleration when CUDA-capable devices and drivers are available."],
                ["autoDetectDevices", "Auto-detect GPU devices", "Continuously discover CUDA devices instead of pinning to a single GPU."],
                ["enableMemoryOptimization", "Enable GPU memory optimization", "Allow cache cleanup and controlled memory allocation for large inference workloads."],
                ["enableBatchProcessing", "Enable GPU batch processing", "Batch compatible requests for better throughput under concurrency."],
                ["fallbackToCpu", "Enable CPU fallback", "Keep production inference running if GPU resources are unavailable or fail."],
                ["enablePerformanceOptimization", "Enable performance optimization", "Allow background optimization logic to tune runtime behavior."],
                ["enablePerformanceAlerts", "Enable performance alerts", "Surface admin warnings when runtime thresholds are crossed."],
                ["enableStreaming", "Enable optimized streaming", "Keep streaming enabled for production response delivery paths."],
                ["enableRealtimeFeedback", "Enable real-time streaming feedback", "Send live progress and streaming feedback while generation is running."],
                ["enableMonitoring", "Enable monitoring", "Collect runtime metrics for admin review and operational health checks."],
                ["enableRealtimeAlerts", "Enable real-time monitoring alerts", "Emit operational alerts from monitoring when thresholds are exceeded."],
              ].map(([key, title, description]) => (
                <div key={key} className="flex items-start justify-between gap-4 rounded-xl border border-border/50 p-4">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-muted-foreground">{description}</p>
                  </div>
                  <Switch
                    checked={Boolean(form[key as keyof OptimizationFormState])}
                    onCheckedChange={(checked) => setForm((current) => ({ ...current, [key]: checked }))}
                  />
                </div>
              ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="streaming-timeout">Streaming timeout seconds</Label>
                <Input
                  id="streaming-timeout"
                  value={form.streamingTimeoutSeconds}
                  onChange={(event) => setForm((current) => ({ ...current, streamingTimeoutSeconds: event.target.value }))}
                  placeholder="30"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="metrics-retention">Metrics retention hours</Label>
                <Input
                  id="metrics-retention"
                  value={form.metricsRetentionHours}
                  onChange={(event) => setForm((current) => ({ ...current, metricsRetentionHours: event.target.value }))}
                  placeholder="24"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => void handleSave()} disabled={saving || loading}>
                <Save className={`mr-2 h-4 w-4 ${saving ? "animate-spin" : ""}`} />
                Save Runtime Settings
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Cpu className="h-4 w-4" />
                Runtime Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Config version</span>
                <span className="font-medium">{configSummary?.config_version || "unknown"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Validation</span>
                <span className="font-medium">{configSummary?.validation_status ? "Healthy" : "Needs review"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Auto save</span>
                <span className="font-medium">{configSummary?.auto_save_enabled ? "Enabled" : "Disabled"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last updated</span>
                <span className="font-medium text-right">{configSummary?.last_updated || "unknown"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">CUDA runtime</span>
                <span className="font-medium">{gpuSnapshot?.runtime?.cuda_enabled ? "Enabled" : "Disabled"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">CUDA detected</span>
                <span className="font-medium">{gpuSnapshot?.cuda?.available ? "Available" : "Unavailable"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Detected GPUs</span>
                <span className="font-medium">{gpuSnapshot?.cuda?.device_count ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Driver / CUDA</span>
                <span className="font-medium text-right">
                  {gpuSnapshot?.cuda?.driver_version || "unknown"} / {gpuSnapshot?.cuda?.cuda_version || "unknown"}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ServerCog className="h-4 w-4" />
                Enabled Components
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {Object.entries(availableRuntimeComponents).length === 0 && (
                <p className="text-muted-foreground">No runtime component summary available yet.</p>
              )}
              {Object.entries(availableRuntimeComponents).map(([key, enabled]) => (
                <div key={key} className="flex justify-between gap-4">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-medium">{enabled ? "On" : "Off"}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ServerCog className="h-4 w-4" />
                GPU Capabilities
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">PyTorch</span>
                <span className="font-medium">{gpuSnapshot?.capabilities?.torch_available ? "Available" : "Unavailable"}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">CuPy</span>
                <span className="font-medium">{gpuSnapshot?.capabilities?.cupy_available ? "Available" : "Unavailable"}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">NVML</span>
                <span className="font-medium">{gpuSnapshot?.capabilities?.pynvml_available ? "Available" : "Unavailable"}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">Auto detect</span>
                <span className="font-medium">{gpuSnapshot?.runtime?.auto_detect_devices ? "Enabled" : "Disabled"}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">CPU fallback</span>
                <span className="font-medium">{gpuSnapshot?.runtime?.cpu_fallback_enabled ? "Enabled" : "Disabled"}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Zap className="h-4 w-4" />
                GPU Telemetry
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {gpuSummary?.error && (
                <p className="text-destructive">{gpuSummary.error}</p>
              )}
              {detectedDevices.length === 0 && !gpuSummary?.error && (
                <p className="text-muted-foreground">No CUDA devices detected by the backend runtime.</p>
              )}
              {detectedDevices.map((device) => (
                <div key={device.id} className="rounded-xl border border-border/50 p-3 space-y-1">
                  <div className="flex justify-between gap-4">
                    <span className="font-medium">{device.name}</span>
                    <span className="text-muted-foreground">GPU {device.id}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Compute</span>
                    <span>{device.compute_capability || "unknown"}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Memory</span>
                    <span>
                      {device.memory_used != null && device.memory_total != null
                        ? `${(device.memory_used / 1024 ** 3).toFixed(1)} / ${(device.memory_total / 1024 ** 3).toFixed(1)} GB`
                        : "unknown"}
                    </span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Utilization</span>
                    <span>{device.utilization != null ? `${device.utilization}%` : "unknown"}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Temperature</span>
                    <span>{device.temperature != null ? `${device.temperature}C` : "unknown"}</span>
                  </div>
                </div>
              ))}
              <Separator />
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">Batch queue</span>
                <span className="font-medium">{gpuSummary?.batch_queue_size ?? 0}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">Cached models</span>
                <span className="font-medium">{gpuSummary?.cached_models ?? 0}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">Current utilization</span>
                <span className="font-medium">
                  {gpuSummary?.current_metrics?.utilization != null ? `${gpuSummary.current_metrics.utilization.toFixed(1)}%` : "unknown"}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-muted-foreground">Current memory usage</span>
                <span className="font-medium">
                  {gpuSummary?.current_metrics?.memory_usage != null ? `${gpuSummary.current_metrics.memory_usage.toFixed(1)}%` : "unknown"}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Gauge className="h-4 w-4" />
                Admin Guidance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>Use CUDA only when the host has stable NVIDIA drivers and production VRAM headroom.</p>
              <p>Keep CPU fallback enabled in production unless you explicitly want hard failures on GPU outages.</p>
              <p>Batch processing and memory optimization should stay enabled together for sustained multi-request workloads.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
