"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";

import { getKarenBackend } from "@/lib/karen-backend";
import { useAuth } from "@/hooks/use-auth";
import { handleApiError } from "@/lib/error-handler";

import ProviderManagement from "./ProviderManagement";
import ModelBrowser from "./ModelBrowser";
import ProfileManager from "./ProfileManager";
import ModelProviderIntegration from "./ModelProviderIntegration";
// NOTE: Test components removed for production readiness
// import ModelWorkflowTest from "./ModelWorkflowTest";
// import ModelLibraryIntegrationTest from "./ModelLibraryIntegrationTest";
import { HelpTooltip, QuickHelp } from "@/components/ui/help-tooltip";
import ProviderNotificationSystem from "./ProviderNotificationSystem";
import { useProviderNotifications } from "@/hooks/useProviderNotifications";

import {
  fetchProviderDiscovery,
  listLlamaModels,
  listTransformersModels,
  listOpenaiModels,
  type ProviderDiscoveryItem,
  type ContractModelInfo,
} from "@/lib/providers-api";

// Icons
import {
  Activity,
  AlertCircle,
  Brain,
  CheckCircle,
  Cloud,
  Database,
  Download,
  HardDrive,
  Library,
  Loader2,
  RefreshCw,
  Users,
} from "lucide-react";

export interface LLMProvider {
  name: string;
  description: string;
  category: string;
  requires_api_key: boolean;
  capabilities: string[];
  is_llm_provider: boolean;
  provider_type: "remote" | "local" | "hybrid";
  health_status: "healthy" | "unhealthy" | "unknown";
  error_message?: string;
  last_health_check?: number;
  cached_models_count: number;
  last_discovery?: number;
  api_base_url?: string;
  icon?: string;
  documentation_url?: string;
  pricing_info?: {
    input_cost_per_1k?: number;
    output_cost_per_1k?: number;
    currency?: string;
  };
}

export interface ModelInfo {
  id: string;
  name: string;
  family: string;
  format?: string;
  size?: number;
  parameters?: string;
  quantization?: string;
  context_length?: number;
  capabilities: string[];
  local_path?: string;
  download_url?: string;
  downloads?: number;
  likes?: number;
  provider: string;
  runtime_compatibility?: string[];
  tags?: string[];
  license?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LLMProfile {
  id: string;
  name: string;
  description: string;
  router_policy: "balanced" | "performance" | "cost" | "privacy" | "custom";
  providers: Record<
    string,
    {
      provider: string;
      model?: string;
      priority: number;
      max_cost_per_1k_tokens?: number;
      required_capabilities: string[];
      excluded_capabilities: string[];
    }
  >;
  fallback_provider: string;
  fallback_model?: string;
  is_valid: boolean;
  validation_errors: string[];
  created_at: number;
  updated_at: number;
  settings?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  };
}

export interface ProviderStats {
  total_models: number;
  healthy_providers: number;
  total_providers: number;
  last_sync: number;
  degraded_mode: boolean;
}

const LOCAL_STORAGE_KEYS = {
  selectedProfile: "llm_selected_profile",
  tabPreference: "llm_settings_tab",
};

/**
 * @file LLMSettings.tsx
 * @description Enhanced LLM Settings component with tabbed interface, real-time validation,
 * and comprehensive model management. Separates providers, profiles, and models for better UX.
 */
export default function LLMSettings() {
  // Core state
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [profiles, setProfiles] = useState<LLMProfile[]>([]);
  const [activeProfile, setActiveProfile] = useState<LLMProfile | null>(null);
  const [allModels, setAllModels] = useState<ModelInfo[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats | null>(null);

  // UI state
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>("providers");
  const [degradedMode, setDegradedMode] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const { toast } = useToast();
  const backend = getKarenBackend();
  const { isAuthenticated } = useAuth();

  // Provider notifications
  const { unreadCount, criticalCount } = useProviderNotifications({
    realTimeUpdates: true,
    autoToast: true,
  });

  // Load settings and preferences on mount, but wait for auth
  useEffect(() => {
    if (isAuthenticated || process.env.NODE_ENV === "development") {
      loadSettings();
      loadSavedPreferences();
    } else if (!isAuthenticated) {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // Safety timeout to prevent spinner lock
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) setLoading(false);
    }, 10000);
    return () => clearTimeout(timeout);
  }, [loading]);

  const saveTabPreference = useCallback(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEYS.tabPreference, activeTab);
    } catch {
      /* ignore */
    }
  }, [activeTab]);

  const loadSavedPreferences = () => {
    try {
      const savedTab = localStorage.getItem(LOCAL_STORAGE_KEYS.tabPreference);
      if (savedTab && ["providers", "models", "profiles", "notifications"].includes(savedTab)) {
        setActiveTab(savedTab);
      }
    } catch {
      /* ignore */
    }
  };

  // Auto-save tab preference when it changes
  useEffect(() => {
    saveTabPreference();
  }, [activeTab, saveTabPreference]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadProviders(),
        loadProfiles(),
        loadAllModels(),
        loadProviderStats(),
        checkDegradedMode(),
      ]);
    } catch (error) {
      if ((error as unknown)?.status === 401 || (error as unknown)?.message?.includes("401")) {
        if (process.env.NODE_ENV !== "development") {
          toast({
            title: "Authentication Required",
            description: "Please log in to access LLM settings.",
            variant: "destructive",
          });
        }
      } else {
        const info = (error as unknown)?.errorInfo || handleApiError(error as unknown, "loadSettings");
        toast({
          title: info.title || "Error Loading Settings",
          description: info.message || "Could not load LLM provider settings. Using defaults.",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const discovery = await fetchProviderDiscovery();
      const mapped: LLMProvider[] = discovery.map(mapDiscoveryToLLMProvider);
      setProviders(mapped.length ? mapped : getFallbackProviders());
    } catch {
      setProviders(getFallbackProviders());
    }
  };

  const loadProfiles = async () => {
    try {
      let profilesResponse: LLMProfile[] | null = null;
      let activeProfileResponse: LLMProfile | null = null;

      try {
        profilesResponse = await backend.makeRequestPublic<LLMProfile[]>("/api/providers/profiles");
      } catch {
        try {
          profilesResponse = await backend.makeRequestPublic<LLMProfile[]>("/api/profiles");
        } catch {
          /* ignore */
        }
      }

      try {
        activeProfileResponse = await backend.makeRequestPublic<LLMProfile | null>(
          "/api/providers/profiles/active"
        );
      } catch {
        try {
          activeProfileResponse = await backend.makeRequestPublic<LLMProfile | null>(
            "/api/profiles/active"
          );
        } catch {
          /* ignore */
        }
      }

      const fallbackProfiles = getFallbackProfiles();
      const validProfiles = Array.isArray(profilesResponse) ? profilesResponse : fallbackProfiles;

      setProfiles(validProfiles);
      setActiveProfile(activeProfileResponse || validProfiles[0] || null);
    } catch {
      const fallbackProfiles = getFallbackProfiles();
      setProfiles(fallbackProfiles);
      setActiveProfile(fallbackProfiles[0] || null);
    }
  };

  const loadAllModels = async () => {
    try {
      const [llama, tf, openai, spacy] = await Promise.all([
        listLlamaModels().catch(() => []).then((r) => (Array.isArray(r) ? r : [])),
        listTransformersModels().catch(() => []).then((r) => (Array.isArray(r) ? r : [])),
        listOpenaiModels().catch(() => []).then((r) => (Array.isArray(r) ? r : [])),
        (async () => {
          try {
            const { listSpacyPipelines } = await import("@/lib/providers-api");
            const pipes = await listSpacyPipelines();
            const valid = Array.isArray(pipes) ? pipes : [];
            return valid.map(
              (p) =>
                ({
                  id: `spacy:${p}`,
                  provider: "spacy",
                  displayName: p,
                  family: "spacy",
                  installed: true,
                  remote: false,
                  tags: ["pipeline"],
                } as ContractModelInfo)
            );
          } catch {
            return [] as ContractModelInfo[];
          }
        })(),
      ]);

      const merged: ContractModelInfo[] = [
        ...(Array.isArray(llama) ? llama : []),
        ...(Array.isArray(tf) ? tf : []),
        ...(Array.isArray(openai) ? openai : []),
        ...(Array.isArray(spacy) ? spacy : []),
      ];

      const mapped = merged.map(mapContractModelToModelInfo);
      setAllModels(mapped);
    } catch {
      setAllModels([]);
    }
  };

  const loadProviderStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ProviderStats>("/api/providers/stats");
      setProviderStats(response);
    } catch {
      const fallbackStats: ProviderStats = {
        total_models: providers.length * 2,
        healthy_providers: Math.max(1, Math.floor(providers.length * 0.8)),
        total_providers: providers.length,
        last_sync: Date.now(),
        degraded_mode: false,
      };
      setProviderStats(fallbackStats);
    }
  };

  const checkDegradedMode = async () => {
    try {
      const response = await backend.makeRequestPublic<{ degraded_mode: boolean }>(
        "/api/health/degraded-mode"
      );
      setDegradedMode(response?.degraded_mode || false);
    } catch {
      setDegradedMode(false);
    }
  };

  const mapDiscoveryToLLMProvider = (p: ProviderDiscoveryItem): LLMProvider => {
    const isCloud = p.group === "cloud";
    return {
      name: p.id,
      description: p.title,
      category: "LLM",
      requires_api_key: isCloud,
      capabilities: p.canListModels ? ["streaming"] : [],
      is_llm_provider: true,
      provider_type: isCloud ? "remote" : "local",
      health_status: p.available ? "healthy" : "unknown",
      cached_models_count: 0,
      documentation_url: undefined,
      api_base_url: undefined,
    } as LLMProvider;
  };

  const mapContractModelToModelInfo = (m: ContractModelInfo): ModelInfo => ({
    id: m.id,
    name: m.displayName,
    family: m.family,
    format: undefined,
    size: undefined,
    parameters: undefined,
    quantization: m.quant,
    context_length: m.contextWindow,
    capabilities: m.tags || [],
    local_path: undefined,
    download_url: undefined,
    downloads: undefined,
    likes: undefined,
    provider: m.provider,
    runtime_compatibility: undefined,
    tags: m.tags,
    license: undefined,
    description: undefined,
    created_at: undefined,
    updated_at: undefined,
  });

  const getFallbackProviders = (): LLMProvider[] => [
    {
      name: "openai",
      description: "OpenAI GPT models via API",
      category: "LLM",
      requires_api_key: true,
      capabilities: ["streaming", "embeddings", "function_calling", "vision"],
      is_llm_provider: true,
      provider_type: "remote",
      health_status: "unknown",
      cached_models_count: 0,
      api_base_url: "https://api.openai.com/v1",
      documentation_url: "https://platform.openai.com/docs",
      pricing_info: { input_cost_per_1k: 0.03, output_cost_per_1k: 0.06, currency: "USD" },
    },
    {
      name: "gemini",
      description: "Google Gemini models via API",
      category: "LLM",
      requires_api_key: true,
      capabilities: ["streaming", "embeddings", "vision"],
      is_llm_provider: true,
      provider_type: "remote",
      health_status: "unknown",
      cached_models_count: 0,
      api_base_url: "https://generativelanguage.googleapis.com/v1beta",
      documentation_url: "https://ai.google.dev/docs",
    },
    {
      name: "deepseek",
      description: "DeepSeek models optimized for coding and reasoning",
      category: "LLM",
      requires_api_key: true,
      capabilities: ["streaming", "function_calling"],
      is_llm_provider: true,
      provider_type: "remote",
      health_status: "unknown",
      cached_models_count: 0,
      api_base_url: "https://api.deepseek.com",
      documentation_url: "https://platform.deepseek.com/docs",
    },
    {
      name: "local",
      description: "Local model files (GGUF, safetensors, etc.)",
      category: "LLM",
      requires_api_key: false,
      capabilities: ["local_execution", "privacy"],
      is_llm_provider: true,
      provider_type: "local",
      health_status: "unknown",
      cached_models_count: 0,
    },
  ];

  const getFallbackProfiles = (): LLMProfile[] => [
    {
      id: "balanced",
      name: "Balanced",
      description: "Balanced configuration for general use",
      router_policy: "balanced",
      providers: {
        chat: {
          provider: "gemini",
          priority: 80,
          required_capabilities: ["streaming"],
          excluded_capabilities: [],
        },
        code: {
          provider: "deepseek",
          priority: 85,
          required_capabilities: ["streaming"],
          excluded_capabilities: [],
        },
        reasoning: {
          provider: "openai",
          priority: 75,
          required_capabilities: [],
          excluded_capabilities: [],
        },
      },
      fallback_provider: "local",
      is_valid: true,
      validation_errors: [],
      created_at: Date.now(),
      updated_at: Date.now(),
      settings: {
        temperature: 0.7,
        max_tokens: 4000,
        top_p: 0.9,
      },
    },
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadSettings();
      toast({
        title: "Settings Refreshed",
        description: "All provider and model data has been updated.",
      });
    } catch {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleRetryFullMode = async () => {
    try {
      await backend.makeRequestPublic("/api/health/retry-full-mode", {
        method: "POST",
      });
      await checkDegradedMode();
      toast({
        title: "Retrying Full Mode",
        description: "Attempting to restore full functionality...",
      });
    } catch {
      toast({
        title: "Retry Failed",
        description: "Could not exit degraded mode. Check system health.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <div className="space-y-2">
              <p className="text-lg font-medium">Loading LLM Settings</p>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Discovering providers, models, and profiles...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight">LLM Settings</h2>
            <HelpTooltip helpKey="llmSettings" category="llmSettings" />
          </div>
          <p className="text-muted-foreground"></p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          {providerStats && (
            <Badge variant="outline" className="gap-1">
              <Activity className="h-3 w-3" />
              {providerStats.healthy_providers}/{providerStats.total_providers} healthy
            </Badge>
          )}
          {activeProfile && (
            <Badge variant="secondary" className="gap-1">
              <Brain className="h-3 w-3" />
              {activeProfile.name}
            </Badge>
          )}
        </div>
      </div>

      {/* System Status Alerts */}
      {degradedMode && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Degraded Mode Active</AlertTitle>
          <AlertDescription className="flex items-center flex-wrap gap-2">
            System is running with limited functionality. Core helper models are being used as fallback.
            <Button variant="outline" size="sm" className="ml-2" onClick={handleRetryFullMode}>
              Retry Full Mode
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabbed Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="providers" className="flex items-center gap-2">
            <Cloud className="h-4 w-4" />
            <HelpTooltip helpKey="providerManagement" category="llmSettings" variant="inline" size="sm" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            <HelpTooltip helpKey="modelBrowser" category="llmSettings" variant="inline" size="sm" />
            Models
          </TabsTrigger>
          <TabsTrigger value="profiles" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <HelpTooltip helpKey="profileManagement" category="llmSettings" variant="inline" size="sm" />
            Profiles
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            {(unreadCount > 0 || criticalCount > 0) && (
              <Badge variant="destructive" className="text-xs ml-1 sm:text-sm md:text-base">
                {criticalCount > 0 ? criticalCount : unreadCount}
              </Badge>
            )}
            Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-6">
          <ProviderManagement
            providers={providers}
            setProviders={setProviders}
            providerStats={providerStats}
            setProviderStats={setProviderStats}
          />
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <div className="space-y-6">
            {/* Model Library Integration Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Library className="h-5 w-5" />
                      Model Library
                    </CardTitle>
                    <CardDescription>Discover, download, and auto-configure models.</CardDescription>
                  </div>
                  <Button
                    onClick={() => {
                      window.dispatchEvent(new CustomEvent("navigate-to-model-library"));
                    }}
                    className="gap-2"
                  >
                    <Library className="h-4 w-4" />
                    Open Library
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <Download className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Discover Models</h3>
                    <p className="text-sm text-muted-foreground">
                      Browse cloud and local catalogs with compatibility hints.
                    </p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <HardDrive className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Download & Manage</h3>
                    <p className="text-sm text-muted-foreground">
                      Queue downloads, track progress, and manage storage.
                    </p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Auto-Configure</h3>
                    <p className="text-sm text-muted-foreground">
                      Apply tested runtime settings per model family automatically.
                    </p>
                  </div>
                </div>

                {/* Quick Stats */}
                {providerStats && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Total Models: {providerStats.total_models}</span>
                      <span>
                        Healthy Providers: {providerStats.healthy_providers}/
                        {providerStats.total_providers}
                      </span>
                    </div>
                    <Badge variant="outline" className="gap-1">
                      <Activity className="h-3 w-3" />
                      {providerStats.degraded_mode ? "Degraded Mode" : "Full Mode"}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Model-Provider Integration */}
            <ModelProviderIntegration
              providers={providers}
              onNavigateToModelLibrary={() => {
                window.dispatchEvent(new CustomEvent("navigate-to-model-library"));
              }}
            />

            {/* Existing Model Browser */}
            <ModelBrowser models={allModels as unknown} setModels={setAllModels as unknown} providers={providers} />
          </div>
        </TabsContent>

        <TabsContent value="profiles" className="space-y-6">
          <ProfileManager
            profiles={profiles as unknown}
            setProfiles={setProfiles as unknown}
            activeProfile={activeProfile}
            setActiveProfile={setActiveProfile as unknown}
            providers={providers}
          />
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <ProviderNotificationSystem
            onNotificationAction={(notificationId, actionId) => {
              if (actionId === "retry") {
                handleRefresh();
              }
              if (actionId === "configure") {
                setActiveTab("providers");
              }
            }}
            realTimeUpdates={true}
          />
        </TabsContent>
      </Tabs>

      {/* Quick Help Section */}
      <QuickHelp
        helpKeys={["providerManagement", "modelCompatibility", "integrationWorkflow", "apiKeyManagement"]}
        category="llmSettings"
        title="LLM Settings Help"
        className="mt-6"
      />
    </div>
  );
}
