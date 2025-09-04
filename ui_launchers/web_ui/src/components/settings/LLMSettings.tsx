"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  Brain,
  AlertCircle,
  Loader2,
  Cloud,
  Database,
  Users,
  Activity,
  RefreshCw,
  Library,
  Download,
  HardDrive,
  CheckCircle
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { useAuth } from '@/contexts/AuthContext';
import {
  fetchProviderDiscovery,
  listLlamaModels,
  listTransformersModels,
  listOpenaiModels,
  type ProviderDiscoveryItem,
  type ContractModelInfo,
} from '@/lib/providers-api';
import { handleApiError } from '@/lib/error-handler';
import ProviderManagement from './ProviderManagement';
import ModelBrowser from './ModelBrowser';
import ProfileManager from './ProfileManager';
import ModelProviderIntegration from './ModelProviderIntegration';
import ModelWorkflowTest from './ModelWorkflowTest';
import ModelLibraryIntegrationTest from './ModelLibraryIntegrationTest';
import { HelpTooltip, HelpSection, QuickHelp } from '@/components/ui/help-tooltip';

interface LLMProvider {
  name: string;
  description: string;
  category: string;
  requires_api_key: boolean;
  capabilities: string[];
  is_llm_provider: boolean;
  provider_type: 'remote' | 'local' | 'hybrid';
  health_status: 'healthy' | 'unhealthy' | 'unknown';
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

interface ModelInfo {
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

interface LLMProfile {
  id: string;
  name: string;
  description: string;
  router_policy: 'balanced' | 'performance' | 'cost' | 'privacy' | 'custom';
  providers: Record<string, {
    provider: string;
    model?: string;
    priority: number;
    max_cost_per_1k_tokens?: number;
    required_capabilities: string[];
    excluded_capabilities: string[];
  }>;
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

interface ProviderStats {
  total_models: number;
  healthy_providers: number;
  total_providers: number;
  last_sync: number;
  degraded_mode: boolean;
}

const LOCAL_STORAGE_KEYS = {
  selectedProfile: 'llm_selected_profile',
  tabPreference: 'llm_settings_tab',
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
  const [activeTab, setActiveTab] = useState<string>('providers');
  const [degradedMode, setDegradedMode] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  const { toast } = useToast();
  const backend = getKarenBackend();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Load settings and preferences on mount, but wait for auth
  useEffect(() => {
    // Only load settings if auth is not loading and we're either authenticated or in development mode
    if (!authLoading && (isAuthenticated || process.env.NODE_ENV === 'development')) {
      loadSettings();
      loadSavedPreferences();
    } else if (!authLoading && !isAuthenticated) {
      // If not authenticated and not in development, show a message
      console.log('Not authenticated, skipping settings load');
      setLoading(false);
    }
  }, [isAuthenticated, authLoading]);

  // Set a timeout to prevent infinite loading
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('LLM Settings loading timeout - using fallback data');
        setLoading(false);
      }
    }, 10000); // 10 second timeout
    
    return () => clearTimeout(timeout);
  }, [loading]);

  // Auto-save tab preference when it changes
  useEffect(() => {
    saveTabPreference();
  }, [activeTab]);

  const loadSavedPreferences = () => {
    try {
      const savedTab = localStorage.getItem(LOCAL_STORAGE_KEYS.tabPreference);
      if (savedTab && ['providers', 'models', 'profiles'].includes(savedTab)) {
        setActiveTab(savedTab);
      }
    } catch (error) {
      console.warn('Failed to load saved preferences:', error);
    }
  };

  const saveTabPreference = useCallback(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEYS.tabPreference, activeTab);
    } catch (error) {
      console.warn('Failed to save tab preference:', error);
    }
  }, [activeTab]);

  const loadSettings = async () => {
    try {
      setLoading(true);

      // Load all data from backend in parallel
      await Promise.all([
        loadProviders(),
        loadProfiles(),
        loadAllModels(),
        loadProviderStats(),
        checkDegradedMode()
      ]);

    } catch (error) {
      console.error('Failed to load LLM settings:', error);
      
      // Check if it's an authentication error
      if ((error as any)?.status === 401 || (error as any)?.message?.includes('401')) {
        console.log('Authentication required for LLM settings, waiting for login...');
        // Don't show error toast for auth errors in development mode
        if (process.env.NODE_ENV !== 'development') {
          toast({
            title: "Authentication Required",
            description: "Please log in to access LLM settings.",
            variant: "destructive",
          });
        }
      } else {
        const info = (error as any)?.errorInfo || handleApiError(error as any, 'loadSettings');
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
    } catch (error) {
      console.error('Failed to load providers:', error);
      setProviders(getFallbackProviders());
    }
  };

  const loadProfiles = async () => {
    try {
      // Try to load profiles with individual error handling
      let profilesResponse: LLMProfile[] | null = null;
      let activeProfileResponse: LLMProfile | null = null;
      
      try {
        profilesResponse = await backend.makeRequestPublic<LLMProfile[]>('/api/providers/profiles');
      } catch (error) {
        console.warn('Profiles endpoint not available:', error);
        try {
          profilesResponse = await backend.makeRequestPublic<LLMProfile[]>('/api/profiles');
        } catch (fallbackErr) {
          console.warn('Fallback /api/profiles endpoint not available:', fallbackErr);
        }
      }
      
      try {
        activeProfileResponse = await backend.makeRequestPublic<LLMProfile | null>('/api/providers/profiles/active');
      } catch (error) {
        console.warn('Active profile endpoint not available:', error);
        try {
          activeProfileResponse = await backend.makeRequestPublic<LLMProfile | null>('/api/profiles/active');
        } catch (fallbackErr) {
          console.warn('Fallback /api/profiles/active endpoint not available:', fallbackErr);
        }
      }
      
      const fallbackProfiles = getFallbackProfiles();
      setProfiles(profilesResponse || fallbackProfiles);
      setActiveProfile(activeProfileResponse || fallbackProfiles[0]);
    } catch (error) {
      console.warn('Provider profiles endpoints not available, using fallback data:', error);
      const fallbackProfiles = getFallbackProfiles();
      setProfiles(fallbackProfiles);
      setActiveProfile(fallbackProfiles[0]);
    }
  };

  const loadAllModels = async () => {
    try {
      // Fetch in parallel from new endpoints with better error handling
      const [llama, tf, openai, spacy] = await Promise.all([
        listLlamaModels().catch(() => []).then(result => Array.isArray(result) ? result : []),
        listTransformersModels().catch(() => []).then(result => Array.isArray(result) ? result : []),
        listOpenaiModels().catch(() => []).then(result => Array.isArray(result) ? result : []),
        // Bring spaCy pipelines as synthetic models
        (async () => {
          try {
            const pipes = await (await import('@/lib/providers-api')).listSpacyPipelines();
            const validPipes = Array.isArray(pipes) ? pipes : [];
            return validPipes.map((p) => ({
              id: `spacy:${p}`,
              provider: 'spacy',
              displayName: p,
              family: 'spacy',
              installed: true,
              remote: false,
              tags: ['pipeline'],
            } as ContractModelInfo));
          } catch {
            return [] as ContractModelInfo[];
          }
        })(),
      ]);
      
      // Ensure all results are arrays before spreading
      const safeResults = [llama, tf, openai, spacy].map(result => Array.isArray(result) ? result : []);
      const merged = safeResults.flat();
      const mapped = merged.map(mapContractModelToModelInfo);
      setAllModels(mapped);
    } catch (error) {
      console.error('Failed to load all models:', error);
      setAllModels([]);
    }
  };

  const mapDiscoveryToLLMProvider = (p: ProviderDiscoveryItem): LLMProvider => {
    const isCloud = p.group === 'cloud';
    return {
      name: p.id,
      description: p.title,
      category: 'LLM',
      requires_api_key: isCloud,
      capabilities: p.canListModels ? ['streaming'] : [],
      is_llm_provider: true,
      provider_type: isCloud ? 'remote' : 'local',
      health_status: p.available ? 'healthy' : 'unknown',
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

  const loadProviderStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ProviderStats>('/api/providers/stats');
      setProviderStats(response);
    } catch (error) {
      console.warn('Provider stats endpoint not available, using fallback data:', error);
      // Create fallback stats based on available providers
      const fallbackStats = {
        total_models: providers.length * 2, // Estimate 2 models per provider
        healthy_providers: Math.max(1, Math.floor(providers.length * 0.8)), // Assume 80% healthy
        total_providers: providers.length,
        last_sync: Date.now(),
        degraded_mode: false
      };
      setProviderStats(fallbackStats);
    }
  };

  const checkDegradedMode = async () => {
    try {
      const response = await backend.makeRequestPublic<{ degraded_mode: boolean }>('/api/health/degraded-mode');
      setDegradedMode(response?.degraded_mode || false);
    } catch (error) {
      console.error('Failed to check degraded mode:', error);
      setDegradedMode(false);
    }
  };

  const getFallbackProviders = (): LLMProvider[] => [
    {
      name: 'openai',
      description: 'OpenAI GPT models via API',
      category: 'LLM',
      requires_api_key: true,
      capabilities: ['streaming', 'embeddings', 'function_calling', 'vision'],
      is_llm_provider: true,
      provider_type: 'remote',
      health_status: 'unknown',
      cached_models_count: 0,
      api_base_url: 'https://api.openai.com/v1',
      documentation_url: 'https://platform.openai.com/docs',
      pricing_info: { input_cost_per_1k: 0.03, output_cost_per_1k: 0.06, currency: 'USD' }
    },
    {
      name: 'gemini',
      description: 'Google Gemini models via API',
      category: 'LLM',
      requires_api_key: true,
      capabilities: ['streaming', 'embeddings', 'vision'],
      is_llm_provider: true,
      provider_type: 'remote',
      health_status: 'unknown',
      cached_models_count: 0,
      api_base_url: 'https://generativelanguage.googleapis.com/v1beta',
      documentation_url: 'https://ai.google.dev/docs'
    },
    {
      name: 'deepseek',
      description: 'DeepSeek models optimized for coding and reasoning',
      category: 'LLM',
      requires_api_key: true,
      capabilities: ['streaming', 'function_calling'],
      is_llm_provider: true,
      provider_type: 'remote',
      health_status: 'unknown',
      cached_models_count: 0,
      api_base_url: 'https://api.deepseek.com',
      documentation_url: 'https://platform.deepseek.com/docs'
    },
    {
      name: 'local',
      description: 'Local model files (GGUF, safetensors, etc.)',
      category: 'LLM',
      requires_api_key: false,
      capabilities: ['local_execution', 'privacy'],
      is_llm_provider: true,
      provider_type: 'local',
      health_status: 'unknown',
      cached_models_count: 0
    }
  ];

  const getFallbackProfiles = (): LLMProfile[] => [
    {
      id: 'balanced',
      name: 'Balanced',
      description: 'Balanced configuration for general use',
      router_policy: 'balanced',
      providers: {
        chat: {
          provider: 'gemini',
          priority: 80,
          required_capabilities: ['streaming'],
          excluded_capabilities: []
        },
        code: {
          provider: 'deepseek',
          priority: 85,
          required_capabilities: ['streaming'],
          excluded_capabilities: []
        },
        reasoning: {
          provider: 'openai',
          priority: 75,
          required_capabilities: [],
          excluded_capabilities: []
        }
      },
      fallback_provider: 'local',
      is_valid: true,
      validation_errors: [],
      created_at: Date.now(),
      updated_at: Date.now(),
      settings: {
        temperature: 0.7,
        max_tokens: 4000,
        top_p: 0.9
      }
    }
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadSettings();
      toast({
        title: "Settings Refreshed",
        description: "All provider and model data has been updated.",
      });
    } catch (error) {
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
      await backend.makeRequestPublic('/api/health/retry-full-mode', {
        method: 'POST'
      });
      await checkDegradedMode();
      toast({
        title: "Retrying Full Mode",
        description: "Attempting to restore full functionality...",
      });
    } catch (error) {
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
              <p className="text-sm text-muted-foreground">
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
          <p className="text-muted-foreground">
            Manage language model providers, profiles, and model library
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
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
          <AlertDescription>
            System is running with limited functionality. Core helper models are being used as fallback.
            <Button 
              variant="outline" 
              size="sm" 
              className="ml-2"
              onClick={handleRetryFullMode}
            >
              Retry Full Mode
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabbed Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="providers" className="flex items-center gap-2">
            <Cloud className="h-4 w-4" />
            Providers
            <HelpTooltip helpKey="providerManagement" category="llmSettings" variant="inline" size="sm" />
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Model Library
            <HelpTooltip helpKey="modelBrowser" category="llmSettings" variant="inline" size="sm" />
          </TabsTrigger>
          <TabsTrigger value="profiles" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Profiles
            <HelpTooltip helpKey="profileManagement" category="llmSettings" variant="inline" size="sm" />
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
                      Model Library Integration
                    </CardTitle>
                    <CardDescription>
                      Discover, download, and manage models for your configured providers
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => {
                      window.dispatchEvent(new CustomEvent('navigate-to-model-library'));
                    }}
                    className="gap-2"
                  >
                    <Library className="h-4 w-4" />
                    Open Model Library
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <Download className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Discover Models</h3>
                    <p className="text-sm text-muted-foreground">
                      Browse available models from various providers
                    </p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <HardDrive className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Download & Manage</h3>
                    <p className="text-sm text-muted-foreground">
                      Download models locally and manage storage
                    </p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-primary" />
                    <h3 className="font-medium">Auto-Configure</h3>
                    <p className="text-sm text-muted-foreground">
                      Automatically configure providers with compatible models
                    </p>
                  </div>
                </div>
                
                {/* Quick Stats */}
                {providerStats && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Total Models: {providerStats.total_models}</span>
                      <span>Healthy Providers: {providerStats.healthy_providers}/{providerStats.total_providers}</span>
                    </div>
                    <Badge variant="outline" className="gap-1">
                      <Activity className="h-3 w-3" />
                      {providerStats.degraded_mode ? 'Degraded Mode' : 'Full Mode'}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Integration Workflow Test */}
            <ModelWorkflowTest
              onNavigateToModelLibrary={() => {
                window.dispatchEvent(new CustomEvent('navigate-to-model-library'));
              }}
              onNavigateToProviders={() => setActiveTab('providers')}
            />
            
            {/* Comprehensive Integration Test */}
            <ModelLibraryIntegrationTest
              onNavigateToModelLibrary={() => {
                window.dispatchEvent(new CustomEvent('navigate-to-model-library'));
              }}
              onNavigateToLLMSettings={() => setActiveTab('providers')}
            />
            
            {/* Model-Provider Integration */}
            <ModelProviderIntegration
              providers={providers}
              onNavigateToModelLibrary={() => {
                // Navigate to Model Library tab in main settings
                window.dispatchEvent(new CustomEvent('navigate-to-model-library'));
              }}
            />
            
            {/* Existing Model Browser */}
            <ModelBrowser
              models={allModels as any}
              setModels={setAllModels as any}
              providers={providers}
            />
          </div>
        </TabsContent>

        <TabsContent value="profiles" className="space-y-6">
          <ProfileManager
            profiles={profiles as any}
            setProfiles={setProfiles as any}
            activeProfile={activeProfile}
            setActiveProfile={setActiveProfile as any}
            providers={providers}
          />
        </TabsContent>
      </Tabs>

      {/* Quick Help Section */}
      <QuickHelp
        helpKeys={[
          'providerManagement',
          'modelCompatibility',
          'integrationWorkflow',
          'apiKeyManagement'
        ]}
        category="llmSettings"
        title="LLM Settings Help"
        className="mt-6"
      />
    </div>
  );
}
