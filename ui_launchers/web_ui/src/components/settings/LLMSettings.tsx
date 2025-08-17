"use client";

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import {
  Brain,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Settings,
  Key,
  ExternalLink,
  Info,
  Save,
  Loader2,
  Search,
  Filter,
  Zap,
  Shield,
  Eye,
  Database,
  Cloud,
  HardDrive,
  Users,
  Download,
  Upload,
  Trash2,
  Edit,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Globe,
  Lock
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';
import { API_ENDPOINTS } from '@/lib/extensions/constants';
import ModelBrowser from './ModelBrowser';
import ProfileManager from './ProfileManager';

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

interface ApiKeyValidationResult {
  valid: boolean;
  message: string;
  provider: string;
  models_discovered?: number;
  capabilities_detected?: string[];
}

interface ModelFilters {
  provider?: string;
  format?: string;
  size_range?: [number, number];
  capabilities?: string[];
  local_only?: boolean;
  search_query?: string;
  sort_by?: 'name' | 'size' | 'downloads' | 'likes' | 'updated';
  sort_order?: 'asc' | 'desc';
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
  providerApiKeys: 'llm_provider_api_keys',
  customModels: 'llm_custom_models',
  modelFilters: 'llm_model_filters',
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
  
  // Configuration state
  const [providerApiKeys, setProviderApiKeys] = useState<Record<string, string>>({});
  const [customModels, setCustomModels] = useState<Record<string, string>>({});
  const [providerModels, setProviderModels] = useState<Record<string, ModelInfo[]>>({});
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [healthChecking, setHealthChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('providers');
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  
  // Validation state
  const [validatingKeys, setValidatingKeys] = useState<Record<string, boolean>>({});
  const [keyValidationResults, setKeyValidationResults] = useState<Record<string, ApiKeyValidationResult>>({});
  
  // Model browser state
  const [modelFilters, setModelFilters] = useState<ModelFilters>({
    sort_by: 'name',
    sort_order: 'asc'
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Error and warning state
  const [providerWarning, setProviderWarning] = useState<string | null>(null);
  const [degradedMode, setDegradedMode] = useState(false);
  
  const { toast } = useToast();

  const backend = getKarenBackend();

  // Load settings and preferences on mount
  useEffect(() => {
    loadSettings();
    loadSavedPreferences();
  }, []);

  // Auto-save preferences when they change
  useEffect(() => {
    savePreferences();
  }, [activeTab, modelFilters]);

  const loadSavedPreferences = () => {
    try {
      const savedTab = localStorage.getItem(LOCAL_STORAGE_KEYS.tabPreference);
      const savedFilters = localStorage.getItem(LOCAL_STORAGE_KEYS.modelFilters);
      
      if (savedTab) setActiveTab(savedTab);
      if (savedFilters) setModelFilters(JSON.parse(savedFilters));
    } catch (error) {
      console.warn('Failed to load saved preferences:', error);
    }
  };

  const savePreferences = useCallback(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEYS.tabPreference, activeTab);
      localStorage.setItem(LOCAL_STORAGE_KEYS.modelFilters, JSON.stringify(modelFilters));
    } catch (error) {
      console.warn('Failed to save preferences:', error);
    }
  }, [activeTab, modelFilters]);

  const loadSettings = async () => {
    try {
      setLoading(true);

      // Load from localStorage
      const storedApiKeys = localStorage.getItem(LOCAL_STORAGE_KEYS.providerApiKeys);
      const storedModels = localStorage.getItem(LOCAL_STORAGE_KEYS.customModels);

      if (storedApiKeys) setProviderApiKeys(JSON.parse(storedApiKeys));
      if (storedModels) setCustomModels(JSON.parse(storedModels));

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
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'loadSettings');
      toast({
        title: info.title || "Error Loading Settings",
        description: info.message || "Could not load LLM provider settings. Using defaults.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await backend.makeRequestPublic<LLMProvider[]>('/api/providers?llm_only=true');
      setProviders(response || []);
      setProviderWarning(null);
    } catch (error) {
      console.error('Failed to load providers:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'loadProviders');
      const status = (error as any)?.status || (error as any)?.response?.status;
      
      // Use fallback providers if backend is unavailable
      setProviderWarning('Backend unavailable. Using fallback provider configuration.');
      setProviders(getFallbackProviders());
      
      // Only show toast for unexpected errors, not for expected backend unavailability
      if (status !== 404 && status !== 503) {
        toast({
          variant: 'destructive',
          title: info.title,
          description: `${info.message} (status: ${status ?? 'unknown'})`
        });
      }
    }
  };

  const loadAllModels = async () => {
    try {
      const response = await backend.makeRequestPublic<ModelInfo[]>('/api/models/all');
      setAllModels(response || []);
    } catch (error) {
      console.error('Failed to load all models:', error);
      setAllModels([]);
    }
  };

  const loadProviderStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ProviderStats>('/api/providers/stats');
      setProviderStats(response);
    } catch (error) {
      console.error('Failed to load provider stats:', error);
      setProviderStats(null);
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

  const loadProfiles = async () => {
    try {
      const [profilesResponse, activeProfileResponse] = await Promise.all([
        backend.makeRequestPublic<LLMProfile[]>('/api/providers/profiles'),
        backend.makeRequestPublic<LLMProfile | null>('/api/providers/profiles/active')
      ]);
      
      setProfiles(profilesResponse || []);
      setActiveProfile(activeProfileResponse);
    } catch (error) {
      console.error('Failed to load profiles:', error);
      
      // Use fallback profiles without showing error toast for expected failures
      const fallbackProfiles = getFallbackProfiles();
      setProfiles(fallbackProfiles);
      setActiveProfile(fallbackProfiles[0]);
    }
  };

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
    },
    {
      id: 'performance',
      name: 'Performance',
      description: 'Optimized for speed and responsiveness',
      router_policy: 'performance',
      providers: {
        chat: {
          provider: 'openai',
          priority: 90,
          required_capabilities: ['streaming'],
          excluded_capabilities: []
        },
        code: {
          provider: 'deepseek',
          priority: 95,
          required_capabilities: ['streaming', 'function_calling'],
          excluded_capabilities: []
        }
      },
      fallback_provider: 'local',
      is_valid: true,
      validation_errors: [],
      created_at: Date.now(),
      updated_at: Date.now(),
      settings: {
        temperature: 0.3,
        max_tokens: 2000,
        top_p: 0.8
      }
    },
    {
      id: 'privacy',
      name: 'Privacy First',
      description: 'Local-only processing for maximum privacy',
      router_policy: 'privacy',
      providers: {
        chat: {
          provider: 'local',
          priority: 100,
          required_capabilities: ['local_execution'],
          excluded_capabilities: []
        },
        code: {
          provider: 'local',
          priority: 100,
          required_capabilities: ['local_execution'],
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

  const handleProfileChange = async (profileId: string) => {
    try {
      const response = await backend.makeRequestPublic<LLMProfile>(`/api/providers/profiles/${profileId}/activate`, {
        method: 'POST'
      });
      
      setActiveProfile(response);
      localStorage.setItem(LOCAL_STORAGE_KEYS.selectedProfile, profileId);

      toast({
        title: "Profile Activated",
        description: `Switched to ${response.name} profile. Changes take effect immediately.`,
      });
    } catch (error) {
      console.error('Failed to switch profile:', error);
      
      // Fallback to local profile switching if backend is unavailable
      const profile = profiles.find(p => p.id === profileId);
      if (profile) {
        setActiveProfile(profile);
        localStorage.setItem(LOCAL_STORAGE_KEYS.selectedProfile, profileId);
        toast({
          title: "Profile Activated (Local)",
          description: `Switched to ${profile.name} profile locally.`,
        });
      } else {
        const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'switchProfile');
        toast({
          variant: 'destructive',
          title: info.title || "Profile Switch Failed",
          description: info.message || "Could not switch to the selected profile.",
        });
      }
    }
  };

  // Debounced API key validation
  const validationTimeouts = useMemo(() => new Map<string, NodeJS.Timeout>(), []);

  const handleApiKeyChange = (providerName: string, apiKey: string) => {
    const updatedKeys = { ...providerApiKeys, [providerName]: apiKey };
    setProviderApiKeys(updatedKeys);
    
    // Clear previous validation result
    setKeyValidationResults(prev => {
      const updated = { ...prev };
      delete updated[providerName];
      return updated;
    });
    
    // Clear existing timeout
    const existingTimeout = validationTimeouts.get(providerName);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }
    
    // Validate API key with debouncing
    if (apiKey.trim()) {
      const timeout = setTimeout(() => {
        validateApiKey(providerName, apiKey);
      }, 1000); // 1 second debounce
      
      validationTimeouts.set(providerName, timeout);
    }
  };

  const validateApiKey = async (providerName: string, apiKey: string) => {
    setValidatingKeys(prev => ({ ...prev, [providerName]: true }));
    
    try {
      const response = await backend.makeRequestPublic<ApiKeyValidationResult>('/api/providers/validate-api-key', {
        method: 'POST',
        body: JSON.stringify({
          provider: providerName,
          api_key: apiKey
        })
      });
      
      setKeyValidationResults(prev => ({ ...prev, [providerName]: response }));
      
      if (response.valid) {
        // Discover models for this provider
        await discoverProviderModels(providerName);
        
        // Update provider health status
        setProviders(prev => prev.map(p => 
          p.name === providerName 
            ? { ...p, health_status: 'healthy', last_health_check: Date.now() }
            : p
        ));
        
        toast({
          title: "API Key Valid",
          description: `${providerName} API key validated successfully. ${response.models_discovered || 0} models discovered.`,
        });
      } else {
        // Update provider health status
        setProviders(prev => prev.map(p => 
          p.name === providerName 
            ? { ...p, health_status: 'unhealthy', error_message: response.message, last_health_check: Date.now() }
            : p
        ));
      }
    } catch (error) {
      console.error(`Failed to validate API key for ${providerName}:`, error);
      const errorMessage = (error as any)?.message || 'Validation failed - check network connection';
      
      setKeyValidationResults(prev => ({ 
        ...prev, 
        [providerName]: {
          valid: false,
          message: errorMessage,
          provider: providerName
        }
      }));
      
      setProviders(prev => prev.map(p => 
        p.name === providerName 
          ? { ...p, health_status: 'unhealthy', error_message: errorMessage, last_health_check: Date.now() }
          : p
      ));
    } finally {
      setValidatingKeys(prev => ({ ...prev, [providerName]: false }));
    }
  };

  const discoverProviderModels = async (providerName: string, forceRefresh: boolean = false) => {
    try {
      const response = await backend.makeRequestPublic<ModelInfo[]>(`/api/providers/${providerName}/models?force_refresh=${forceRefresh}`);
      const models = response || [];
      
      setProviderModels(prev => ({ ...prev, [providerName]: models }));
      
      // Update provider cached model count
      setProviders(prev => prev.map(p => 
        p.name === providerName 
          ? { ...p, cached_models_count: models.length, last_discovery: Date.now() / 1000 }
          : p
      ));
      
      // Update all models list
      setAllModels(prev => {
        const filtered = prev.filter(m => m.provider !== providerName);
        return [...filtered, ...models];
      });
      
    } catch (error) {
      console.error(`Failed to discover models for ${providerName}:`, error);
      setProviderModels(prev => ({ ...prev, [providerName]: [] }));
    }
  };

  const toggleProviderExpansion = (providerName: string) => {
    setExpandedProviders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(providerName)) {
        newSet.delete(providerName);
      } else {
        newSet.add(providerName);
      }
      return newSet;
    });
  };

  const handleModelChange = (providerName: string, model: string) => {
    const updatedModels = { ...customModels, [providerName]: model };
    setCustomModels(updatedModels);
    
    // Save immediately to localStorage
    localStorage.setItem(LOCAL_STORAGE_KEYS.customModels, JSON.stringify(updatedModels));
  };

  // Computed filtered models for the model browser
  const filteredModels = useMemo(() => {
    let filtered = [...allModels];
    
    // Apply search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(query) ||
        model.description?.toLowerCase().includes(query) ||
        model.family.toLowerCase().includes(query) ||
        model.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    // Apply filters
    if (modelFilters.provider) {
      filtered = filtered.filter(model => model.provider === modelFilters.provider);
    }
    
    if (modelFilters.format) {
      filtered = filtered.filter(model => model.format === modelFilters.format);
    }
    
    if (modelFilters.capabilities?.length) {
      filtered = filtered.filter(model => 
        modelFilters.capabilities!.every(cap => model.capabilities.includes(cap))
      );
    }
    
    if (modelFilters.local_only) {
      filtered = filtered.filter(model => model.local_path);
    }
    
    if (modelFilters.size_range) {
      const [min, max] = modelFilters.size_range;
      filtered = filtered.filter(model => {
        if (!model.size) return false;
        return model.size >= min && model.size <= max;
      });
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      const { sort_by = 'name', sort_order = 'asc' } = modelFilters;
      let comparison = 0;
      
      switch (sort_by) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'size':
          comparison = (a.size || 0) - (b.size || 0);
          break;
        case 'downloads':
          comparison = (a.downloads || 0) - (b.downloads || 0);
          break;
        case 'likes':
          comparison = (a.likes || 0) - (b.likes || 0);
          break;
        case 'updated':
          comparison = new Date(a.updated_at || 0).getTime() - new Date(b.updated_at || 0).getTime();
          break;
      }
      
      return sort_order === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  }, [allModels, searchQuery, modelFilters]);

  const saveSettings = async () => {
    try {
      setSaving(true);

      // Save to localStorage first (always works)
      localStorage.setItem(LOCAL_STORAGE_KEYS.providerApiKeys, JSON.stringify(providerApiKeys));
      localStorage.setItem(LOCAL_STORAGE_KEYS.customModels, JSON.stringify(customModels));

      // Try to save to backend
      try {
        await backend.makeRequestPublic('/api/llm/settings', {
          method: 'POST',
          body: JSON.stringify({
            selected_profile: activeProfile?.id,
            provider_api_keys: providerApiKeys,
            custom_models: customModels,
          }),
        });

        toast({
          title: "Settings Saved",
          description: "Your LLM provider settings have been saved successfully.",
        });
      } catch (backendError) {
        console.warn('Backend save failed, using local storage:', backendError);
        toast({
          title: "Settings Saved Locally",
          description: "Settings saved to browser storage. Backend sync will retry automatically.",
        });
      }

    } catch (error) {
      console.error('Failed to save settings:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'saveSettings');
      toast({
        title: info.title || "Error Saving Settings",
        description: info.message || "Could not save LLM settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const runHealthCheck = async () => {
    try {
      setHealthChecking(true);

      const response = await backend.makeRequestPublic<Record<string, any>>('/api/providers/health-check-all', {
        method: 'POST'
      });

      let healthyCount = 0;
      const updatedProviders = providers.map(provider => {
        const healthResult = response[provider.name];
        if (healthResult) {
          const isHealthy = healthResult.status === 'healthy';
          if (isHealthy) healthyCount++;
          
          return {
            ...provider,
            health_status: (isHealthy ? 'healthy' : 'unhealthy') as 'healthy' | 'unhealthy' | 'unknown',
            error_message: healthResult.message,
            last_health_check: Date.now(),
            cached_models_count: healthResult.models_count || provider.cached_models_count
          };
        }
        return provider;
      });

      setProviders(updatedProviders);

      // Update provider stats
      setProviderStats(prev => prev ? {
        ...prev,
        healthy_providers: healthyCount,
        last_sync: Date.now()
      } : null);

      toast({
        title: "Health Check Complete",
        description: `${healthyCount}/${providers.length} providers are healthy.`,
      });

    } catch (error) {
      console.error('Health check failed:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'runHealthCheck');
      toast({
        title: info.title || "Health Check Failed",
        description: info.message || "Could not check provider health status.",
        variant: "destructive",
      });
    } finally {
      setHealthChecking(false);
    }
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getHealthStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">Healthy</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getProviderTypeIcon = (type: string) => {
    switch (type) {
      case 'remote':
        return <Cloud className="h-4 w-4" />;
      case 'local':
        return <HardDrive className="h-4 w-4" />;
      case 'hybrid':
        return <Globe className="h-4 w-4" />;
      default:
        return <Database className="h-4 w-4" />;
    }
  };

  const getValidationIcon = (providerName: string) => {
    const isValidating = validatingKeys[providerName];
    const result = keyValidationResults[providerName];
    
    if (isValidating) {
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    }
    
    if (result) {
      return result.valid 
        ? <CheckCircle2 className="h-4 w-4 text-green-500" />
        : <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    
    return null;
  };

  const getCapabilityIcon = (capability: string) => {
    switch (capability) {
      case 'streaming':
        return <Zap className="h-3 w-3" />;
      case 'vision':
        return <Eye className="h-3 w-3" />;
      case 'function_calling':
        return <Settings className="h-3 w-3" />;
      case 'local_execution':
        return <Shield className="h-3 w-3" />;
      case 'embeddings':
        return <Database className="h-3 w-3" />;
      case 'privacy':
        return <Lock className="h-3 w-3" />;
      default:
        return <Info className="h-3 w-3" />;
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getRouterPolicyIcon = (policy: string) => {
    switch (policy) {
      case 'performance':
        return <Zap className="h-4 w-4" />;
      case 'cost':
        return <Database className="h-4 w-4" />;
      case 'privacy':
        return <Shield className="h-4 w-4" />;
      case 'balanced':
        return <Settings className="h-4 w-4" />;
      default:
        return <Brain className="h-4 w-4" />;
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
      {/* System Status Alerts */}
      {degradedMode && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Degraded Mode Active</AlertTitle>
          <AlertDescription>
            System is running in degraded mode with limited functionality. Some providers may be unavailable.
          </AlertDescription>
        </Alert>
      )}

      {providerWarning && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Provider Configuration Notice</AlertTitle>
          <AlertDescription>{providerWarning}</AlertDescription>
        </Alert>
      )}

      {/* Provider Stats Summary */}
      {providerStats && (
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-primary">{providerStats.healthy_providers}</div>
                <div className="text-xs text-muted-foreground">Healthy Providers</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{providerStats.total_models}</div>
                <div className="text-xs text-muted-foreground">Available Models</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{providers.filter(p => p.requires_api_key && providerApiKeys[p.name]).length}</div>
                <div className="text-xs text-muted-foreground">Configured APIs</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{activeProfile ? '1' : '0'}</div>
                <div className="text-xs text-muted-foreground">Active Profile</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="providers" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="profiles" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Profiles
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Models
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-6">
          {/* Provider Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    LLM Provider Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure API keys and settings for each LLM provider. Real-time validation ensures your keys work correctly.
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={runHealthCheck}
                    variant="outline"
                    size="sm"
                    disabled={healthChecking}
                  >
                    {healthChecking ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Health Check
                  </Button>
                  <Button onClick={saveSettings} disabled={saving} size="sm">
                    {saving ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save All
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {providers.filter(p => p.is_llm_provider).map((provider) => (
                <Card key={provider.name} className="border-l-4 border-l-primary/20">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          {getProviderTypeIcon(provider.provider_type)}
                          {getHealthStatusIcon(provider.health_status)}
                          <h4 className="font-semibold capitalize text-lg">{provider.name}</h4>
                        </div>
                        <div className="flex items-center gap-2">
                          {getHealthStatusBadge(provider.health_status)}
                          <Badge variant="outline" className="text-xs">
                            {provider.provider_type}
                          </Badge>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleProviderExpansion(provider.name)}
                      >
                        {expandedProviders.has(provider.name) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    
                    <p className="text-sm text-muted-foreground">{provider.description}</p>
                    
                    <div className="flex gap-1 flex-wrap">
                      {provider.capabilities.map((capability) => (
                        <Badge key={capability} variant="outline" className="text-xs flex items-center gap-1">
                          {getCapabilityIcon(capability)}
                          {capability.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </CardHeader>

                  {expandedProviders.has(provider.name) && (
                    <CardContent className="pt-0 space-y-4">
                      {provider.error_message && (
                        <Alert variant="destructive">
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>Provider Error</AlertTitle>
                          <AlertDescription className="text-sm">
                            {provider.error_message}
                          </AlertDescription>
                        </Alert>
                      )}

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {provider.requires_api_key && (
                          <div className="space-y-3">
                            <Label htmlFor={`${provider.name}-api-key`} className="flex items-center gap-2 text-sm font-medium">
                              <Key className="h-4 w-4" />
                              API Key Configuration
                              {getValidationIcon(provider.name)}
                            </Label>
                            <Input
                              id={`${provider.name}-api-key`}
                              type="password"
                              value={providerApiKeys[provider.name] || ''}
                              onChange={(e) => handleApiKeyChange(provider.name, e.target.value)}
                              placeholder={`Enter ${provider.name} API key`}
                              className="font-mono text-sm"
                            />
                            {keyValidationResults[provider.name] && (
                              <div className={`text-sm p-2 rounded ${keyValidationResults[provider.name].valid ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                                {keyValidationResults[provider.name].message}
                                {keyValidationResults[provider.name].models_discovered && (
                                  <div className="text-xs mt-1">
                                    {keyValidationResults[provider.name].models_discovered} models discovered
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}

                        <div className="space-y-3">
                          <Label htmlFor={`${provider.name}-model`} className="text-sm font-medium">Default Model</Label>
                          <Select
                            value={customModels[provider.name] || ''}
                            onValueChange={(value) => handleModelChange(provider.name, value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select a model" />
                            </SelectTrigger>
                            <SelectContent>
                              {providerModels[provider.name]?.map((model) => (
                                <SelectItem key={model.id} value={model.id}>
                                  <div className="flex flex-col">
                                    <span className="font-medium">{model.name}</span>
                                    <span className="text-xs text-muted-foreground">
                                      {model.parameters && `${model.parameters} • `}
                                      {model.context_length && `${model.context_length.toLocaleString()} tokens`}
                                    </span>
                                  </div>
                                </SelectItem>
                              )) || []}
                            </SelectContent>
                          </Select>
                          
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>
                              {provider.cached_models_count > 0 ? (
                                `${provider.cached_models_count} models available`
                              ) : (
                                'No models discovered yet'
                              )}
                            </span>
                            {provider.cached_models_count > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => discoverProviderModels(provider.name, true)}
                                className="h-6 px-2 text-xs"
                              >
                                <RefreshCw className="h-3 w-3 mr-1" />
                                Refresh
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Provider-specific information and links */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-4 border-t">
                        <div className="space-y-2">
                          {provider.pricing_info && (
                            <div className="text-xs text-muted-foreground">
                              <strong>Pricing:</strong> ${provider.pricing_info.input_cost_per_1k}/1K input, 
                              ${provider.pricing_info.output_cost_per_1k}/1K output tokens
                            </div>
                          )}
                          {provider.last_health_check && (
                            <div className="text-xs text-muted-foreground">
                              <strong>Last checked:</strong> {new Date(provider.last_health_check).toLocaleString()}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          {provider.documentation_url && (
                            <Button variant="outline" size="sm" asChild>
                              <a href={provider.documentation_url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-3 w-3 mr-1" />
                                Docs
                              </a>
                            </Button>
                          )}
                          
                          {provider.name === 'openai' && (
                            <Button variant="outline" size="sm" asChild>
                              <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">
                                <Key className="h-3 w-3 mr-1" />
                                Get API Key
                              </a>
                            </Button>
                          )}
                          
                          {provider.name === 'gemini' && (
                            <Button variant="outline" size="sm" asChild>
                              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">
                                <Key className="h-3 w-3 mr-1" />
                                Get API Key
                              </a>
                            </Button>
                          )}
                          
                          {provider.name === 'deepseek' && (
                            <Button variant="outline" size="sm" asChild>
                              <a href="https://platform.deepseek.com/api_keys" target="_blank" rel="noopener noreferrer">
                                <Key className="h-3 w-3 mr-1" />
                                Get API Key
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>

                      {provider.name === 'local' && (
                        <Alert>
                          <HardDrive className="h-4 w-4" />
                          <AlertTitle>Local Provider</AlertTitle>
                          <AlertDescription className="text-sm">
                            This provider uses models stored locally on your machine. No API key is required.
                            Models are automatically discovered from your local model directory.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  )}
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="profiles" className="space-y-6">
          <ProfileManager
            profiles={profiles}
            providers={providers}
            activeProfile={activeProfile}
            onProfileChange={handleProfileChange}
            onProfileUpdate={loadProfiles}
          />
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <ModelBrowser
            providers={providers}
            onModelSelect={(model) => {
              // Handle model selection for configuration
              console.log('Selected model:', model);
            }}
            selectedModels={[]}
            allowMultiSelect={false}
            showDownloadActions={true}
          />
        </TabsContent>
      </Tabs>

      {/* Information */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Configuration Notes</AlertTitle>
        <AlertDescription className="text-sm space-y-2">
          <p>• API keys are validated in real-time and stored locally for convenience</p>
          <p>• CopilotKit is excluded from LLM providers as it's a UI framework</p>
          <p>• Profile changes take effect immediately for new conversations</p>
          <p>• Models are discovered automatically when valid API keys are provided</p>
          <p>• Local providers don't require API keys and scan for local model files</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}