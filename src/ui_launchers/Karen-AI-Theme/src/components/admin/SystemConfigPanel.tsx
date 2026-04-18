"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { apiClient } from "@/lib/api";
import {
  Activity, CheckCircle2, XCircle, RefreshCw, Loader2,
  Cpu, HardDrive, Shield, Server
} from "lucide-react";
import { Progress } from "@/components/ui/progress";

type HealthData = {
  status: string;
  timestamp?: string;
  services?: Record<string, unknown>;
  nlp_assets?: {
    spacy_installed: boolean;
    spacy_model_name: string;
    spacy_model_installed: boolean;
    nltk_installed: boolean;
    nltk_resources: Record<string, boolean>;
    runtime_downloads_enabled: boolean;
    ready: boolean;
  };
  [key: string]: unknown;
};

export default function SystemConfigPanel() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [isInstallingNlpAssets, setIsInstallingNlpAssets] = useState(false);

  const loadHealth = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<HealthData>("/api/health");
      setHealth(response);
      setLastRefreshed(new Date());
    } catch {
      setHealth({ status: "unreachable" });
      setLastRefreshed(new Date());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  const isHealthy = health?.status === "healthy" || health?.status === "ok";

  // Environment variables info (read-only display of known config)
  const envConfig = [
    { key: "AUTH_MODE", description: "Authentication mode", defaultValue: "hybrid" },
    { key: "CORS_ORIGINS", description: "Allowed CORS origins", defaultValue: "auto-detected" },
    { key: "ENABLE_RATE_LIMITING", description: "Rate limiting enabled", defaultValue: "false" },
    { key: "COPILOT_ASSIST_TIMEOUT_SECONDS", description: "LLM response timeout", defaultValue: "45" },
    { key: "KARI_AUTO_DOWNLOAD_LLM", description: "Auto-download models", defaultValue: "false" },
    { key: "KARI_FAST_STARTUP", description: "Skip heavy init on startup", defaultValue: "true" },
    { key: "WARMUP_LLM", description: "Warm up LLM on startup", defaultValue: "false" },
    { key: "AI_KAREN_ENABLE_MODEL_LIBRARY", description: "Enable model library", defaultValue: "false" },
    { key: "KARI_ENABLE_NLTK_DOWNLOADS", description: "Allow runtime NLTK downloads", defaultValue: "false" },
  ];

  const installNlpAssets = useCallback(async () => {
    setIsInstallingNlpAssets(true);
    try {
      await apiClient.post("/api/health/nlp-assets/install", {});
      await loadHealth();
    } finally {
      setIsInstallingNlpAssets(false);
    }
  }, [loadHealth]);

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <Card className={`border-2 ${isHealthy ? 'border-emerald-500/30' : 'border-rose-500/30'}`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className={`h-5 w-5 ${isHealthy ? 'text-emerald-500' : 'text-rose-500'}`} />
              System Health
            </CardTitle>
            <div className="flex items-center gap-2">
              {lastRefreshed && (
                <span className="text-[10px] text-muted-foreground">
                  Updated {lastRefreshed.toLocaleTimeString()}
                </span>
              )}
              <Button variant="ghost" size="icon" onClick={loadHealth} disabled={isLoading} className="h-8 w-8">
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
          <CardDescription>
            Live status of the Karen AI backend and its services.
          </CardDescription>
        </CardHeader>
        <CardContent>
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
                  <p className="font-semibold text-lg capitalize">{health?.status || "Unknown"}</p>
                  {health?.timestamp && (
                    <p className="text-xs text-muted-foreground">{health.timestamp}</p>
                  )}
                </div>
              </div>

              {/* Service Status Grid */}
              {health?.services && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mt-4">
                  {Object.entries(health.services).map(([name, info]) => {
                    const svcHealthy = typeof info === 'object' && info !== null
                      ? (info as { status?: string; connected?: boolean }).status === 'healthy' || (info as { status?: string; connected?: boolean }).status === 'ok' || (info as { status?: string; connected?: boolean }).connected === true
                      : info === true;
                    return (
                      <div key={name} className={`flex items-center gap-2 p-3 rounded-xl border ${
                        svcHealthy ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-rose-500/20 bg-rose-500/5'
                      }`}>
                        {svcHealthy ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                        ) : (
                          <XCircle className="h-4 w-4 text-rose-500 shrink-0" />
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium capitalize truncate">{name.replace(/_/g, ' ')}</p>
                          {typeof info === 'object' && info !== null && (info as { status?: string }).status && (
                            <p className="text-[10px] text-muted-foreground">{(info as { status: string }).status}</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resource Monitoring */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Server className="h-5 w-5 text-primary" />
            Resource Estimates
          </CardTitle>
          <CardDescription>Approximate resource usage based on known container limits.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5"><HardDrive className="h-3.5 w-3.5" /> Memory Usage</span>
              <span className="text-muted-foreground font-mono">~5.0 GB / 6.0 GB</span>
            </div>
            <Progress value={83} className="h-2" />
            <p className="text-[10px] text-amber-500">⚠ High memory usage — consider reducing loaded models</p>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5"><Cpu className="h-3.5 w-3.5" /> CPU Usage</span>
              <span className="text-muted-foreground font-mono">~25-30%</span>
            </div>
            <Progress value={28} className="h-2" />
          </div>
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
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">spaCy Model</span>
                <Badge variant={health?.nlp_assets?.spacy_model_installed ? "default" : "destructive"}>
                  {health?.nlp_assets?.spacy_model_installed ? "Ready" : "Missing"}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground font-mono">
                {health?.nlp_assets?.spacy_model_name || "en_core_web_sm"}
              </p>
            </div>
            <div className="rounded-xl border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">NLTK Resources</span>
                <Badge variant={health?.nlp_assets?.ready ? "default" : "secondary"}>
                  {health?.nlp_assets?.ready ? "Ready" : "Partial"}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {health?.nlp_assets?.nltk_resources
                  ? Object.entries(health.nlp_assets.nltk_resources)
                      .map(([name, ready]) => `${name}:${ready ? "ok" : "missing"}`)
                      .join("  ")
                  : "No resource data"}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl border p-3">
            <div>
              <p className="text-sm font-medium">Admin Install Action</p>
              <p className="text-xs text-muted-foreground">
                Use this when the environment is allowed to download missing NLP assets.
              </p>
            </div>
            <Button onClick={installNlpAssets} disabled={isInstallingNlpAssets}>
              {isInstallingNlpAssets ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Install Assets
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Environment Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Shield className="h-5 w-5 text-primary" />
            Environment Configuration
          </CardTitle>
          <CardDescription>
            Key environment variables that control backend behavior. These are set in docker-compose.yml.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {envConfig.map((env) => (
              <div key={env.key} className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 transition-colors group">
                <div className="min-w-0 flex-1">
                  <code className="text-xs font-mono font-semibold text-primary/80">{env.key}</code>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{env.description}</p>
                </div>
                <Badge variant="outline" className="ml-4 font-mono text-[10px] shrink-0">
                  {env.defaultValue}
                </Badge>
              </div>
            ))}
          </div>
          <Separator className="my-4" />
          <p className="text-xs text-muted-foreground">
            To change these values, update your <code className="text-[10px] bg-muted px-1 py-0.5 rounded font-mono">docker-compose.yml</code> and restart the containers.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
