"use client";
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  HardDrive, 
  Cloud, 
  Download, 
  Settings, 
  AlertCircle, 
  Info,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  Package,
  Database
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getKarenBackend } from '@/lib/karen-backend';
import ModelBrowser from './ModelBrowser';
import ModelGrid from './ModelGrid';
import ModelFilters from './ModelFilters';
import OperationProgress from './OperationProgress';
import ModelDownloadDialog from './ModelDownloadDialog';
import ModelMigrationWizard from './ModelMigrationWizard';
interface ModelInfo {
  id: string;
  name: string;
  owner: string;
  repository: string;
  library: string;
  files: FileInfo[];
  total_size: number;
  last_modified: string;
  downloads: number;
  likes: number;
  tags: string[];
  license?: string;
  compatibility: CompatibilityInfo;
  status: 'available' | 'downloading' | 'local' | 'error';
  downloadProgress?: number;
  installed_at?: string;
  install_path?: string;
  pinned?: boolean;
  last_accessed?: string;
  description?: string;
  capabilities: string[];
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
}
interface FileInfo {
  path: string;
  size: number;
  sha256?: string;
}
interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}
interface CompatibilityInfo {
  cpu_features: string[];
  gpu_required: boolean;
  min_ram_gb: number;
  min_vram_gb: number;
}
interface ModelFilters {
  search: string;
  library: string;
  status: string;
  owner: string;
  tags: string[];
}
interface ModelStats {
  total_models: number;
  local_models: number;
  total_size: number;
  available_space: number;
  downloading_count: number;
}
/**
 * Main model management page component providing comprehensive model management interface
 * Following existing page component patterns and integrating with navigation
 */
export default function ModelManagementPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [stats, setStats] = useState<ModelStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('browse');
  const [filters, setFilters] = useState<ModelFilters>({
    search: '',
    library: '',
    status: '',
    owner: '',
    tags: []
  });
  const [browserFilters, setBrowserFilters] = useState<{
    category: string;
    provider: string;
    status: string;
    modality: string;
  }>({
    category: 'all',
    provider: 'all',
    status: 'all',
    modality: 'all'
  });
  const [operations, setOperations] = useState<Record<string, any>>({});
  const [showDownloadDialog, setShowDownloadDialog] = useState(false);
  const [showMigrationWizard, setShowMigrationWizard] = useState(false);
  const [selectedModelForDownload, setSelectedModelForDownload] = useState<ModelInfo | null>(null);
  const backend = getKarenBackend();
  const { toast } = useToast();
  // Load models and stats on component mount
  useEffect(() => {
    loadModels();
    loadStats();
  }, []);
  // Sync browser filters with main filters
  useEffect(() => {
    setBrowserFilters(prev => ({
      ...prev,
      provider: filters.library || 'all',
      status: filters.status || 'all'
    }));
  }, [filters.library, filters.status]);
  // Sync main filters with browser filters
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      library: browserFilters.provider === 'all' ? '' : browserFilters.provider,
      status: browserFilters.status === 'all' ? '' : browserFilters.status
    }));
  }, [browserFilters.provider, browserFilters.status]);
  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);
      // Load local models
      const localResponse = await backend.makeRequestPublic<ModelInfo[]>('/api/models/list/local');
      const localModels = localResponse || [];
      // Load available models (sample from HuggingFace)
      const availableResponse = await backend.makeRequestPublic<ModelInfo[]>('/api/models/list/huggingface');
      const availableModels = availableResponse || [];
      // Combine and deduplicate models
      const allModels = [...localModels, ...availableModels];
      const uniqueModels = allModels.reduce((acc, model) => {
        const existing = acc.find(m => m.id === model.id);
        if (!existing) {
          acc.push(model);
        } else if (model.status === 'local') {
          // Prefer local status over available
          acc[acc.indexOf(existing)] = model;
        }
        return acc;
      }, [] as ModelInfo[]);
      setModels(uniqueModels);
    } catch (err: any) {
      setError(err.message || 'Failed to load models');
      toast({
        title: 'Error loading models',
        description: err.message || 'Failed to load models',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };
  const loadStats = async () => {
    try {
      const response = await backend.makeRequestPublic<ModelStats>('/api/models/stats');
      setStats(response);
    } catch (err) {
    }
  };
  const handleModelAction = async (modelId: string, action: string) => {
    try {
      // Handle special actions that need dialogs
      if (action === 'download' && modelId !== '*') {
        const model = models.find(m => m.id === modelId);
        if (model) {
          setSelectedModelForDownload(model);
          setShowDownloadDialog(true);
          return;
        }
      }
      if (action === 'migrate') {
        setShowMigrationWizard(true);
        return;
      }
      setOperations(prev => ({ ...prev, [modelId]: { action, status: 'running' } }));
      let response: any;
      switch (action) {
        case 'download':
          response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/download', {
            method: 'POST',
            body: JSON.stringify({ model_id: modelId })
          });
          break;
        case 'delete':
          response = await backend.makeRequestPublic<{job_id?: string}>(`/api/models/${modelId}`, {
            method: 'DELETE'
          });
          break;
        case 'cancel':
          response = await backend.makeRequestPublic<{job_id?: string}>(`/api/models/operations/${modelId}/cancel`, {
            method: 'POST'
          });
          break;
        case 'pause':
          response = await backend.makeRequestPublic<{job_id?: string}>(`/api/models/operations/${modelId}/pause`, {
            method: 'POST'
          });
          break;
        case 'resume':
          response = await backend.makeRequestPublic<{job_id?: string}>(`/api/models/operations/${modelId}/resume`, {
            method: 'POST'
          });
          break;
        case 'gc':
          response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/gc', {
            method: 'POST'
          });
          break;
        case 'ensure':
          response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/ensure', {
            method: 'POST'
          });
          break;
        case 'validate':
          response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/validate', {
            method: 'POST'
          });
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }
      if (response?.job_id) {
        setOperations(prev => ({ 
          ...prev, 
          [modelId]: { 
            action, 
            status: 'running', 
            job_id: response.job_id 
          } 
        }));
      } else {
        setOperations(prev => ({ ...prev, [modelId]: { action, status: 'completed' } }));
        // Reload models to reflect changes
        await loadModels();
        await loadStats();
      }
      toast({
        title: `Model ${action} initiated`,
        description: `${action} operation started for ${modelId}`
      });
    } catch (err: any) {
      setOperations(prev => ({ ...prev, [modelId]: { action, status: 'error', error: err.message } }));
      toast({
        title: `Failed to ${action} model`,
        description: err.message || `Failed to ${action} model`,
        variant: 'destructive'
      });
    }
  };
  const handleDownloadWithOptions = async (modelId: string, options: any) => {
    try {
      const response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/download', {
        method: 'POST',
        body: JSON.stringify({ 
          model_id: modelId,
          ...options
        })
      });
      if (response?.job_id) {
        setOperations(prev => ({ 
          ...prev, 
          [modelId]: { 
            action: 'download', 
            status: 'running', 
            job_id: response.job_id 
          } 
        }));
      }
      await loadModels();
      await loadStats();
    } catch (err: any) {
      throw err;
    }
  };
  const handleMigration = async (options: any) => {
    try {
      const response = await backend.makeRequestPublic<{job_id?: string}>('/api/models/migrate', {
        method: 'POST',
        body: JSON.stringify(options)
      });
      if (response?.job_id) {
        setOperations(prev => ({ 
          ...prev, 
          'migration': { 
            action: 'migrate', 
            status: 'running', 
            job_id: response.job_id 
          } 
        }));
      }
      await loadModels();
      await loadStats();
    } catch (err: any) {
      throw err;
    }
  };
  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };
  if (loading) {
    return (
      <div className="container mx-auto p-6 sm:p-4 md:p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin sm:w-auto md:w-full" />
            <span>Loading models...</span>
          </div>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="container mx-auto p-6 sm:p-4 md:p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
          <AlertDescription>
            {error}
            <button 
              variant="outline" 
              size="sm" 
              className="ml-2"
              onClick={loadModels}
             aria-label="Button">
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }
  return (
    <div className="container mx-auto p-6 space-y-6 sm:p-4 md:p-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Package className="h-8 w-8 sm:w-auto md:w-full" />
            Model Management
          </h1>
          <p className="text-muted-foreground">
            Browse, download, and manage AI models for your applications
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button variant="outline" onClick={loadModels} aria-label="Button">
            <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
            Refresh
          </Button>
          <button variant="outline" aria-label="Button">
            <Settings className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
            Settings
          </Button>
        </div>
      </div>
      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Total Models</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_models}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {stats.local_models} local, {stats.total_models - stats.local_models} available
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Storage Used</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatSize(stats.total_size)}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {formatSize(stats.available_space)} available
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Downloads</CardTitle>
              <Download className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.downloading_count}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {stats.downloading_count > 0 ? 'In progress' : 'None active'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Local Models</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.local_models}</div>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                Ready to use
              </p>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="browse" className="flex items-center gap-2">
            <Search className="h-4 w-4 sm:w-auto md:w-full" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="local" className="flex items-center gap-2">
            <HardDrive className="h-4 w-4 sm:w-auto md:w-full" />
            Local Models
          </TabsTrigger>
          <TabsTrigger value="downloads" className="flex items-center gap-2">
            <Download className="h-4 w-4 sm:w-auto md:w-full" />
            Downloads
          </TabsTrigger>
          <TabsTrigger value="management" className="flex items-center gap-2">
            <Settings className="h-4 w-4 sm:w-auto md:w-full" />
            Management
          </TabsTrigger>
        </TabsList>
        <TabsContent value="browse" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5 sm:w-auto md:w-full" />
                Browse Available Models
              </CardTitle>
              <CardDescription>
                Discover and download models from HuggingFace and other repositories
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ModelBrowser
                models={models.filter(m => m.status === 'available' || m.status === 'downloading').map(model => ({
                  ...model,
                  display_name: model.name,
                  provider: model.library || 'unknown',
                  type: 'text',
                  category: model.tags?.[0] || 'general',
                  size: model.total_size || 0,
                  description: model.description || '',
                  modalities: [{
                    type: 'text',
                    input_supported: true,
                    output_supported: true,
                    formats: ['text']
                  }],
                  download_progress: model.downloadProgress,
                  metadata: {
                    ...model.metadata,
                    memory_requirement: model.metadata.memoryRequirement,
                    context_length: model.metadata.contextLength
                  }
                }))}
                onAction={handleModelAction}
                filters={browserFilters}
                onFiltersChange={setBrowserFilters}
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="local" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="h-5 w-5 sm:w-auto md:w-full" />
                Local Models
              </CardTitle>
              <CardDescription>
                Manage models installed on your system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ModelGrid
                models={models.filter(m => m.status === 'local')}
                onAction={handleModelAction}
                searchQuery={filters.search}
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="downloads" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5 sm:w-auto md:w-full" />
                Download Progress
              </CardTitle>
              <CardDescription>
                Monitor active and completed downloads
              </CardDescription>
            </CardHeader>
            <CardContent>
              <OperationProgress
                operations={operations}
                onAction={handleModelAction}
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="management" className="space-y-4">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 sm:w-auto md:w-full" />
                  Model Management Tools
                </CardTitle>
                <CardDescription>
                  Advanced model management and maintenance operations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button 
                    variant="outline" 
                    className="h-auto p-4 flex flex-col items-start gap-2 sm:p-4 md:p-6"
                    onClick={() = aria-label="Button"> handleModelAction('*', 'gc')}
                  >
                    <div className="flex items-center gap-2">
                      <Trash2 className="h-4 w-4 sm:w-auto md:w-full" />
                      <span className="font-medium">Garbage Collection</span>
                    </div>
                    <span className="text-sm text-muted-foreground text-left md:text-base lg:text-lg">
                      Remove unused models to free up disk space
                    </span>
                  </Button>
                  <button 
                    variant="outline" 
                    className="h-auto p-4 flex flex-col items-start gap-2 sm:p-4 md:p-6"
                    onClick={() = aria-label="Button"> handleModelAction('*', 'migrate')}
                  >
                    <div className="flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                      <span className="font-medium">Migrate Layout</span>
                    </div>
                    <span className="text-sm text-muted-foreground text-left md:text-base lg:text-lg">
                      Normalize model directory structure
                    </span>
                  </Button>
                  <button 
                    variant="outline" 
                    className="h-auto p-4 flex flex-col items-start gap-2 sm:p-4 md:p-6"
                    onClick={() = aria-label="Button"> handleModelAction('*', 'ensure')}
                  >
                    <div className="flex items-center gap-2">
                      <Download className="h-4 w-4 sm:w-auto md:w-full" />
                      <span className="font-medium">Ensure Essential</span>
                    </div>
                    <span className="text-sm text-muted-foreground text-left md:text-base lg:text-lg">
                      Install essential models for basic functionality
                    </span>
                  </Button>
                  <button 
                    variant="outline" 
                    className="h-auto p-4 flex flex-col items-start gap-2 sm:p-4 md:p-6"
                    onClick={() = aria-label="Button"> handleModelAction('*', 'validate')}
                  >
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4 sm:w-auto md:w-full" />
                      <span className="font-medium">Validate Registry</span>
                    </div>
                    <span className="text-sm text-muted-foreground text-left md:text-base lg:text-lg">
                      Check model registry integrity and file checksums
                    </span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      {/* Download Dialog */}
      <ModelDownloadDialog
        model={selectedModelForDownload}
        open={showDownloadDialog}
        onOpenChange={setShowDownloadDialog}
        onDownload={handleDownloadWithOptions}
      />
      {/* Migration Wizard */}
      <ModelMigrationWizard
        open={showMigrationWizard}
        onOpenChange={setShowMigrationWizard}
        onMigrate={handleMigration}
      />
    </div>
  );
}
