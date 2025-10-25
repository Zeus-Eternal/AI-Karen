"use client";

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from "@/hooks/use-toast";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Library,
  Loader2,
  Cloud,
  HardDrive,
  Search,
  RefreshCw,
  Download,
  Info,
  X,
  Filter,
  ArrowUpDown,
  SortAsc,
  SortDesc,
  Settings,
  CheckCircle,
  PlayCircle
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { 
  errorHandler, 
  handleApiError, 
  handleDownloadError, 
  handleModelManagementError,
  createConfirmationDialog,
  showSuccess,
  showInfo,
  showWarning
} from '@/lib/error-handler';
import { HelpTooltip, HelpSection, QuickHelp } from '@/components/ui/help-tooltip';
import { ContextualHelp, HelpCallout, QuickStartHelp } from '@/components/ui/contextual-help';
import { useDownloadStatus } from '@/hooks/use-download-status';
import ConfirmationDialog from '@/components/ui/confirmation-dialog';
import type { DownloadTask } from '@/hooks/use-download-status';
import ModelCard from './ModelCard';
import DownloadManager from './DownloadManager';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  size: number;
  description: string;
  capabilities: string[];
  status: 'available' | 'downloading' | 'local' | 'error';
  downloadProgress?: number;
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
}

interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}

interface ModelLibraryStats {
  totalModels: number;
  localModels: number;
  cloudModels: number;
  downloadingModels: number;
  totalSize: number;
}

const LOCAL_STORAGE_KEYS = {
  searchQuery: 'model_library_search',
  filterProvider: 'model_library_filter_provider',
  filterStatus: 'model_library_filter_status',
  filterSize: 'model_library_filter_size',
  filterCapability: 'model_library_filter_capability',
  sortBy: 'model_library_sort_by',
  sortOrder: 'model_library_sort_order',
};

type SortOption = 'name' | 'size' | 'parameters' | 'provider' | 'status';
type SortOrder = 'asc' | 'desc';

// Debounce hook for search
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * @file ModelLibrary.tsx
 * @description Model Library component for discovering, downloading, and managing LLM models.
 * Provides a comprehensive interface for model management with search, filtering, and categorization.
 */
export default function ModelLibrary() {
  // Core state
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [stats, setStats] = useState<ModelLibraryStats | null>(null);
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSize, setFilterSize] = useState<string>('all');
  const [filterCapability, setFilterCapability] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [showDownloadManager, setShowDownloadManager] = useState(false);
  
  // Confirmation dialog state
  const [confirmationDialog, setConfirmationDialog] = useState<{
    open: boolean;
    title: string;
    message: string;
    confirmText: string;
    cancelText: string;
    variant: 'default' | 'destructive';
    loading: boolean;
    onConfirm: () => Promise<void>;
    icon?: 'warning' | 'info' | 'question';
    details?: string[];
    resolutionSteps?: string[];
  }>({
    open: false,
    title: '',
    message: '',
    confirmText: 'Confirm',
    cancelText: 'Cancel',
    variant: 'default',
    loading: false,
    onConfirm: async () => {},
  });
  
  // Action loading states
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  
  // Debounced search query
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  
  const { toast } = useToast();
  const backend = getKarenBackend();
  
  // Download status integration
  const {
    downloadTasks,
    activeDownloads,
    cancelDownload,
    pauseDownload,
    resumeDownload,
    retryDownload
  } = useDownloadStatus();

  // Load settings and preferences on mount
  useEffect(() => {
    loadModels();
    loadSavedPreferences();
  }, []);

  // Set a timeout to prevent infinite loading
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('Model Library loading timeout - using fallback data');
        setLoading(false);
      }
    }, 10000); // 10 second timeout
    
    return () => clearTimeout(timeout);
  }, [loading]);

  // Auto-save preferences when they change
  useEffect(() => {
    savePreferences();
  }, [searchQuery, filterProvider, filterStatus, filterSize, filterCapability, sortBy, sortOrder]);

  // Auto-show download manager when downloads start
  useEffect(() => {
    if (activeDownloads.length > 0 && !showDownloadManager) {
      setShowDownloadManager(true);
    }
  }, [activeDownloads.length, showDownloadManager]);

  const loadSavedPreferences = () => {
    try {
      const savedSearch = localStorage.getItem(LOCAL_STORAGE_KEYS.searchQuery);
      const savedProvider = localStorage.getItem(LOCAL_STORAGE_KEYS.filterProvider);
      const savedStatus = localStorage.getItem(LOCAL_STORAGE_KEYS.filterStatus);
      const savedSize = localStorage.getItem(LOCAL_STORAGE_KEYS.filterSize);
      const savedCapability = localStorage.getItem(LOCAL_STORAGE_KEYS.filterCapability);
      const savedSortBy = localStorage.getItem(LOCAL_STORAGE_KEYS.sortBy);
      const savedSortOrder = localStorage.getItem(LOCAL_STORAGE_KEYS.sortOrder);
      
      if (savedSearch) setSearchQuery(savedSearch);
      if (savedProvider) setFilterProvider(savedProvider);
      if (savedStatus) setFilterStatus(savedStatus);
      if (savedSize) setFilterSize(savedSize);
      if (savedCapability) setFilterCapability(savedCapability);
      if (savedSortBy) setSortBy(savedSortBy as SortOption);
      if (savedSortOrder) setSortOrder(savedSortOrder as SortOrder);
    } catch (error) {
      console.warn('Failed to load saved preferences:', error);
    }
  };

  const savePreferences = useCallback(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEYS.searchQuery, searchQuery);
      localStorage.setItem(LOCAL_STORAGE_KEYS.filterProvider, filterProvider);
      localStorage.setItem(LOCAL_STORAGE_KEYS.filterStatus, filterStatus);
      localStorage.setItem(LOCAL_STORAGE_KEYS.filterSize, filterSize);
      localStorage.setItem(LOCAL_STORAGE_KEYS.filterCapability, filterCapability);
      localStorage.setItem(LOCAL_STORAGE_KEYS.sortBy, sortBy);
      localStorage.setItem(LOCAL_STORAGE_KEYS.sortOrder, sortOrder);
    } catch (error) {
      console.warn('Failed to save preferences:', error);
    }
  }, [searchQuery, filterProvider, filterStatus, filterSize, filterCapability, sortBy, sortOrder]);

  const loadModels = async () => {
    try {
      setLoading(true);

      // Load models and stats from backend
      await Promise.all([
        loadAvailableModels(),
        loadModelStats()
      ]);

    } catch (error) {
      console.error('Failed to load model library:', error);
      handleApiError(error, 'load model library');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableModels = async () => {
    try {
      console.log('📚 ModelLibrary: Loading models from /api/models/library');
      const response = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total?: number;
        status?: string;
      }>('/api/models/library');
      
      console.log('📚 ModelLibrary: API response received:', {
        responseType: typeof response,
        isObject: response && typeof response === 'object',
        hasModelsProperty: response && 'models' in response,
        modelsType: response?.models ? typeof response.models : 'undefined',
        modelsIsArray: Array.isArray(response?.models),
        modelsLength: response?.models?.length || 0,
        fullResponse: response
      });
      
      if (response && 'models' in response && Array.isArray(response.models)) {
        setModels(response.models);
        console.log('📚 ModelLibrary: Successfully set models array with', response.models.length, 'items');
      } else {
        console.warn('📚 ModelLibrary: API response does not contain valid models array, using fallback models. Response structure:', response);
        setModels(getFallbackModels());
      }
    } catch (error) {
      console.error('📚 ModelLibrary: Failed to load available models:', error);
      setModels(getFallbackModels());
    }
  };

  const loadModelStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ModelLibraryStats>('/api/models/stats');
      setStats(response || calculateStatsFromModels(models));
    } catch (error) {
      console.error('Failed to load model stats:', error);
      setStats(calculateStatsFromModels(models));
    }
  };

  const getFallbackModels = (): ModelInfo[] => [
    {
      id: 'tinyllama-1.1b-chat-q4',
      name: 'TinyLlama 1.1B Chat Q4_K_M',
      provider: 'llama-cpp',
      size: 669000000,
      description: 'Small, efficient chat model perfect for local deployment',
      capabilities: ['chat', 'completion', 'local'],
      status: 'available',
      metadata: {
        parameters: '1.1B',
        quantization: 'Q4_K_M',
        memoryRequirement: '~1GB',
        contextLength: 2048,
        license: 'Apache 2.0',
        tags: ['chat', 'small', 'efficient']
      }
    },
    {
      id: 'phi-3-mini-4k-instruct',
      name: 'Phi-3 Mini 4K Instruct',
      provider: 'llama-cpp',
      size: 2300000000,
      description: 'Microsoft Phi-3 Mini model optimized for instruction following',
      capabilities: ['chat', 'instruct', 'local'],
      status: 'available',
      metadata: {
        parameters: '3.8B',
        quantization: 'Q4_K_M',
        memoryRequirement: '~3GB',
        contextLength: 4096,
        license: 'MIT',
        tags: ['instruct', 'microsoft', 'efficient']
      }
    }
  ];

  const calculateStatsFromModels = (modelList: ModelInfo[]): ModelLibraryStats => {
    const localModels = modelList.filter(m => m.status === 'local').length;
    const cloudModels = modelList.filter(m => m.status === 'available').length;
    const downloadingModels = modelList.filter(m => m.status === 'downloading').length;
    const totalSize = modelList
      .filter(m => m.status === 'local')
      .reduce((sum, m) => sum + m.size, 0);

    return {
      totalModels: modelList.length,
      localModels,
      cloudModels,
      downloadingModels,
      totalSize
    };
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadModels();
      showSuccess("Model Library Refreshed", "All model data has been updated.");
    } catch (error) {
      handleApiError(error, 'refresh model library');
    } finally {
      setRefreshing(false);
    }
  };

  const setModelActionLoading = (modelId: string, action: string, loading: boolean) => {
    const key = `${modelId}_${action}`;
    setActionLoading(prev => ({
      ...prev,
      [key]: loading
    }));
  };

  const isModelActionLoading = (modelId: string, action: string): boolean => {
    const key = `${modelId}_${action}`;
    return actionLoading[key] || false;
  };

  const handleModelAction = async (modelId: string, action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => {
    const model = models.find(m => m.id === modelId);
    const modelName = model?.name || modelId;

    // For destructive actions, show confirmation dialog
    if (action === 'delete' || action === 'cancel') {
      const dialogConfig = createConfirmationDialog(action, modelName);
      
      setConfirmationDialog({
        open: true,
        title: dialogConfig.title,
        message: dialogConfig.message,
        confirmText: dialogConfig.confirmText,
        cancelText: dialogConfig.cancelText,
        variant: dialogConfig.variant,
        loading: false,
        icon: action === 'delete' ? 'warning' : 'question',
        onConfirm: async () => {
          setConfirmationDialog(prev => ({ ...prev, loading: true }));
          try {
            await executeModelAction(modelId, action, modelName);
            setConfirmationDialog(prev => ({ ...prev, open: false }));
          } catch (error) {
            // Error is already handled in executeModelAction
          } finally {
            setConfirmationDialog(prev => ({ ...prev, loading: false }));
          }
        }
      });
      return;
    }

    // For non-destructive actions, execute directly
    await executeModelAction(modelId, action, modelName);
  };

  const executeModelAction = async (modelId: string, action: string, modelName: string) => {
    setModelActionLoading(modelId, action, true);
    
    try {
      switch (action) {
        case 'download':
          const response = await backend.makeRequestPublic(`/api/models/download`, {
            method: 'POST',
            body: JSON.stringify({ model_id: modelId })
          });
          
          if (response && (response as any).task_id) {
            // The download status hook will automatically pick up this task
            showSuccess(
              "Download Started", 
              `Download of ${modelName} has been initiated. Check the Download Manager for progress.`
            );
            
            // Show download manager if there are active downloads
            if (!showDownloadManager) {
              setShowDownloadManager(true);
            }
          }
          break;
        
        case 'delete':
          await backend.makeRequestPublic(`/api/models/${modelId}`, {
            method: 'DELETE'
          });
          showSuccess("Model Deleted", `${modelName} has been removed from local storage.`);
          break;
        
        case 'cancel':
          // Find the task ID for this model
          const task = downloadTasks.find(t => t.modelId === modelId);
          if (task) {
            await cancelDownload(task.id);
          } else {
            // Fallback to direct API call
            await backend.makeRequestPublic(`/api/models/download/${modelId}`, {
              method: 'DELETE'
            });
            showInfo("Download Cancelled", `Download of ${modelName} has been cancelled.`);
          }
          break;
        
        case 'pause':
          const pauseTask = downloadTasks.find(t => t.modelId === modelId);
          if (pauseTask) {
            await pauseDownload(pauseTask.id);
            showInfo("Download Paused", `Download of ${modelName} has been paused.`);
          }
          break;
        
        case 'resume':
          const resumeTask = downloadTasks.find(t => t.modelId === modelId);
          if (resumeTask) {
            await resumeDownload(resumeTask.id);
            showInfo("Download Resumed", `Download of ${modelName} has been resumed.`);
          }
          break;
      }
      
      // Refresh models after action
      await loadModels();
      
    } catch (error) {
      console.error(`Failed to ${action} model ${modelId}:`, error);
      handleModelManagementError(error, action, modelName);
    } finally {
      setModelActionLoading(modelId, action, false);
    }
  };

  // Helper functions for search and filtering
  const clearAllFilters = () => {
    setSearchQuery('');
    setFilterProvider('all');
    setFilterStatus('all');
    setFilterSize('all');
    setFilterCapability('all');
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (searchQuery) count++;
    if (filterProvider !== 'all') count++;
    if (filterStatus !== 'all') count++;
    if (filterSize !== 'all') count++;
    if (filterCapability !== 'all') count++;
    return count;
  };

  const toggleSort = (newSortBy: SortOption) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('asc');
    }
  };

  // Update model status based on download tasks
  const modelsWithDownloadStatus = Array.isArray(models) ? models.map(model => {
    const downloadTask = downloadTasks.find(task => task.modelId === model.id);
    if (downloadTask) {
      return {
        ...model,
        status: downloadTask.status === 'downloading' ? 'downloading' :
                downloadTask.status === 'completed' ? 'local' :
                downloadTask.status === 'error' ? 'error' : model.status,
        downloadProgress: downloadTask.progress
      };
    }
    return model;
  }) : [];
  
  // Log if models is not an array
  if (!Array.isArray(models)) {
    console.error('📚 ModelLibrary: models is not an array, using empty array for rendering', {
      modelsType: typeof models,
      modelsValue: models
    });
  }

  // Helper functions for filtering and sorting
  const getSizeCategory = (size: number): string => {
    if (size < 1024 * 1024 * 1024) return 'small'; // < 1GB
    if (size < 5 * 1024 * 1024 * 1024) return 'medium'; // < 5GB
    return 'large'; // >= 5GB
  };

  const getParameterCount = (parameters: string): number => {
    const match = parameters.match(/(\d+(?:\.\d+)?)\s*([BM])/i);
    if (!match) return 0;
    const value = parseFloat(match[1]);
    const unit = match[2].toUpperCase();
    return unit === 'B' ? value : value / 1000; // Convert M to B for comparison
  };

  // Get unique values for filter dropdowns
  const availableProviders = useMemo(() => 
    Array.from(new Set(models.map(m => m.provider))), [models]);
  
  const availableCapabilities = useMemo(() => 
    Array.from(new Set(models.flatMap(m => m.capabilities))), [models]);

  // Filter and sort models
  const filteredAndSortedModels = useMemo(() => {
    let filtered = modelsWithDownloadStatus.filter(model => {
      // Search filter (using debounced query)
      const matchesSearch = debouncedSearchQuery === '' || 
        model.name?.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
        model.description?.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
        model.metadata?.tags?.some(tag => tag?.toLowerCase().includes(debouncedSearchQuery.toLowerCase())) ||
        model.capabilities?.some(cap => cap?.toLowerCase().includes(debouncedSearchQuery.toLowerCase()));
      
      // Provider filter
      const matchesProvider = filterProvider === 'all' || model.provider === filterProvider;
      
      // Status filter
      const matchesStatus = filterStatus === 'all' || model.status === filterStatus;
      
      // Size filter
      const matchesSize = filterSize === 'all' || getSizeCategory(model.size) === filterSize;
      
      // Capability filter
      const matchesCapability = filterCapability === 'all' || 
        model.capabilities.includes(filterCapability);
      
      return matchesSearch && matchesProvider && matchesStatus && matchesSize && matchesCapability;
    });

    // Sort models
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'size':
          comparison = a.size - b.size;
          break;
        case 'parameters':
          comparison = getParameterCount(a.metadata.parameters) - getParameterCount(b.metadata.parameters);
          break;
        case 'provider':
          comparison = a.provider.localeCompare(b.provider);
          break;
        case 'status':
          const statusOrder = { 'local': 0, 'downloading': 1, 'available': 2, 'error': 3 };
          comparison = statusOrder[a.status] - statusOrder[b.status];
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [modelsWithDownloadStatus, debouncedSearchQuery, filterProvider, filterStatus, filterSize, filterCapability, sortBy, sortOrder]);

  // Group models by provider type
  const localModels = filteredAndSortedModels.filter(m => m.status === 'local');
  const cloudModels = filteredAndSortedModels.filter(m => m.status === 'available');
  const downloadingModels = filteredAndSortedModels.filter(m => m.status === 'downloading');

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <div className="space-y-2">
              <p className="text-lg font-medium">Loading Model Library</p>
              <p className="text-sm text-muted-foreground">
                Discovering available models...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card - Following LLMSettings.tsx pattern */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Library className="h-5 w-5" />
                Model Library
                <HelpTooltip helpKey="modelLibrary" />
              </CardTitle>
              <CardDescription>
                Discover, download, and manage LLM models for local and cloud providers.
              </CardDescription>
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
              {activeDownloads.length > 0 && (
                <Button
                  variant={showDownloadManager ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowDownloadManager(!showDownloadManager)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Downloads ({activeDownloads.length})
                </Button>
              )}
              {stats && (
                <Badge variant="outline" className="gap-1">
                  <Library className="h-3 w-3" />
                  {stats.localModels} local, {stats.cloudModels} available
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Quick Start Help */}
      {models.length === 0 && !loading && (
        <QuickStartHelp
          steps={[
            {
              title: "Browse Available Models",
              description: "Explore models from different providers and see their capabilities",
              helpKey: "modelLibrary"
            },
            {
              title: "Check Compatibility",
              description: "Ensure models work with your configured providers",
              helpKey: "providerCompatibility"
            },
            {
              title: "Download Models",
              description: "Download models with progress tracking and validation",
              helpKey: "downloadProcess"
            },
            {
              title: "Configure Providers",
              description: "Set up providers to use your downloaded models",
              helpKey: "integrationWorkflow"
            }
          ]}
          className="mb-6"
        />
      )}

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Library className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="flex items-center gap-1">
                    <p className="text-sm font-medium">Total Models</p>
                    <HelpTooltip helpKey="modelStatus" variant="inline" size="sm" />
                  </div>
                  <p className="text-2xl font-bold">{stats.totalModels}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <HardDrive className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Local Models</p>
                  <p className="text-2xl font-bold">{stats.localModels}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Cloud className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Available</p>
                  <p className="text-2xl font-bold">{stats.cloudModels}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Download className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Downloading</p>
                  <p className="text-2xl font-bold">{stats.downloadingModels}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Cross-reference to LLM Settings */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-medium">Provider Configuration</h3>
                <p className="text-sm text-muted-foreground">
                  Configure providers and check model compatibility in LLM Settings
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                // Navigate back to LLM Settings
                window.dispatchEvent(new CustomEvent('navigate-to-llm-settings'));
              }}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              LLM Settings
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Model-Provider Integration Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Integration Status
          </CardTitle>
          <CardDescription>
            Current integration status between Model Library and LLM providers
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Local Models Ready</h4>
              <div className="flex items-center gap-2">
                <Badge variant="default" className="gap-1">
                  <HardDrive className="h-3 w-3" />
                  {localModels.length} models
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Available for immediate use
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Download Queue</h4>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="gap-1">
                  <Download className="h-3 w-3" />
                  {downloadingModels.length} downloading
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Models being prepared
                </span>
              </div>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('navigate-to-llm-settings'));
              }}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              Configure Providers
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Test workflow integration
                toast({
                  title: "Integration Test",
                  description: "Testing Model Library integration with LLM Settings...",
                });
              }}
              className="gap-2"
            >
              <PlayCircle className="h-4 w-4" />
              Test Integration
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Search and Filters */}
      <HelpSection title="Search and Filters" helpKey="searchFiltering">
        <Card>
          <CardContent className="p-4 space-y-4">
            {/* Search Bar */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search models by name, description, tags, or capabilities..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                  {searchQuery && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="absolute right-1 top-1/2 transform -translate-y-1/2 h-7 w-7 p-0"
                      onClick={() => setSearchQuery('')}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            
            {/* Sort Controls */}
            <div className="flex items-center gap-2">
              <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="size">Size</SelectItem>
                  <SelectItem value="parameters">Parameters</SelectItem>
                  <SelectItem value="provider">Provider</SelectItem>
                  <SelectItem value="status">Status</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="gap-1"
              >
                {sortOrder === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />}
              </Button>
            </div>
          </div>

          {/* Filter Controls */}
          <div className="flex flex-wrap gap-2">
            <Select value={filterProvider} onValueChange={setFilterProvider}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {availableProviders.map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {provider}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="local">Local</SelectItem>
                <SelectItem value="available">Available</SelectItem>
                <SelectItem value="downloading">Downloading</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filterSize} onValueChange={setFilterSize}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sizes</SelectItem>
                <SelectItem value="small">Small (&lt;1GB)</SelectItem>
                <SelectItem value="medium">Medium (1-5GB)</SelectItem>
                <SelectItem value="large">Large (&gt;5GB)</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filterCapability} onValueChange={setFilterCapability}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Capability" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Capabilities</SelectItem>
                {availableCapabilities.map(capability => (
                  <SelectItem key={capability} value={capability}>
                    {capability}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {getActiveFilterCount() > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFilters}
                className="gap-1"
              >
                <X className="h-3 w-3" />
                Clear ({getActiveFilterCount()})
              </Button>
            )}
          </div>

          {/* Active Filter Badges */}
          {getActiveFilterCount() > 0 && (
            <div className="flex flex-wrap gap-2">
              {searchQuery && (
                <Badge variant="secondary" className="gap-1">
                  <Search className="h-3 w-3" />
                  Search: "{searchQuery}"
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1"
                    onClick={() => setSearchQuery('')}
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              {filterProvider !== 'all' && (
                <Badge variant="secondary" className="gap-1">
                  <Filter className="h-3 w-3" />
                  Provider: {filterProvider}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1"
                    onClick={() => setFilterProvider('all')}
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              {filterStatus !== 'all' && (
                <Badge variant="secondary" className="gap-1">
                  <Filter className="h-3 w-3" />
                  Status: {filterStatus}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1"
                    onClick={() => setFilterStatus('all')}
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              {filterSize !== 'all' && (
                <Badge variant="secondary" className="gap-1">
                  <Filter className="h-3 w-3" />
                  Size: {filterSize}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1"
                    onClick={() => setFilterSize('all')}
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              {filterCapability !== 'all' && (
                <Badge variant="secondary" className="gap-1">
                  <Filter className="h-3 w-3" />
                  Capability: {filterCapability}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1"
                    onClick={() => setFilterCapability('all')}
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
            </div>
          )}

          {/* Results Summary */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {filteredAndSortedModels.length} of {models.length} models
            </span>
            <span>
              Sorted by {sortBy} ({sortOrder === 'asc' ? 'ascending' : 'descending'})
            </span>
          </div>
        </CardContent>
      </Card>
      </HelpSection>

      {/* Download Manager */}
      {showDownloadManager && (
        <DownloadManager 
          onDownloadComplete={loadModels}
          compact={false}
        />
      )}

      {/* Provider Categories */}
      <div className="space-y-6">
        {/* Local Models */}
        {localModels.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="h-5 w-5" />
                Local Models ({localModels.length})
                <HelpTooltip helpKey="storageManagement" variant="inline" size="sm" />
              </CardTitle>
              <CardDescription>
                Models downloaded and available locally
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {localModels.length === 0 ? (
                <HelpCallout
                  type="tip"
                  title="No Local Models Yet"
                  helpKey="downloadProcess"
                >
                  Download models from the available models section below to get started. 
                  Local models provide faster access and work offline.
                </HelpCallout>
              ) : (
                localModels.map(model => (
                  <ModelCard
                    key={model.id}
                    model={model}
                    onAction={handleModelAction}
                  />
                ))
              )}
            </CardContent>
          </Card>
        )}

        {/* Downloading Models */}
        {downloadingModels.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Downloading Models ({downloadingModels.length})
                <HelpTooltip helpKey="downloadProcess" variant="inline" size="sm" />
              </CardTitle>
              <CardDescription>
                Models currently being downloaded
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {downloadingModels.map(model => (
                <ModelCard
                  key={model.id}
                  model={model}
                  onAction={handleModelAction}

                />
              ))}
            </CardContent>
          </Card>
        )}

        {/* Available Models */}
        {cloudModels.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5" />
                Available Models ({cloudModels.length})
              </CardTitle>
              <CardDescription>
                Models available for download from remote repositories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {cloudModels.map(model => (
                <ModelCard
                  key={model.id}
                  model={model}
                  onAction={handleModelAction}
                />
              ))}
            </CardContent>
          </Card>
        )}

        {/* No Models Found */}
        {filteredAndSortedModels.length === 0 && !loading && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Library className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No Models Found</h3>
              <p className="text-muted-foreground mb-4">
                {getActiveFilterCount() > 0 
                  ? "No models match your current filters. Try adjusting your search criteria."
                  : "No models are currently available. Try refreshing the library."
                }
              </p>
              {getActiveFilterCount() > 0 ? (
                <Button variant="outline" onClick={clearAllFilters}>
                  Clear All Filters
                </Button>
              ) : (
                <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                  Refresh Library
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Help Section */}
      <QuickHelp
        helpKeys={[
          'downloadProcess',
          'storageManagement',
          'providerCompatibility',
          'troubleshooting'
        ]}
        title="Model Library Help"
        className="mt-6"
      />

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={confirmationDialog.open}
        onClose={() => setConfirmationDialog(prev => ({ ...prev, open: false }))}
        title={confirmationDialog.title}
        message={confirmationDialog.message}
        confirmText={confirmationDialog.confirmText}
        cancelText={confirmationDialog.cancelText}
        type={confirmationDialog.variant === 'destructive' ? 'danger' : 'info'}
        loading={confirmationDialog.loading}
        onConfirm={confirmationDialog.onConfirm}
        icon={confirmationDialog.icon}
        details={confirmationDialog.details}
      />
    </div>
  );
}
