"use client";
import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Search,
  Filter,
  Grid,
  List,
  RefreshCw,
  Download,
  HardDrive,
  Cloud,
  AlertCircle,
  CheckCircle,
  Loader2,
  Settings,
  BarChart3,
  Eye,
  Cpu,
  Brain,
  Zap
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { useToast } from '@/hooks/use-toast';
import ModelCard from '../settings/ModelCard';
import ModelDetailsDialog from '../settings/ModelDetailsDialog';
import ModelPerformanceComparison from './ModelPerformanceComparison';
import ModelStatusMonitor from './ModelStatusMonitor';
import ModelConfigurationPanel from './ModelConfigurationPanel';
interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  type: string;
  category: string;
  size: number;
  description: string;
  capabilities: string[];
  modalities: Array<{
    type: string;
    input_supported: boolean;
    output_supported: boolean;
    formats: string[];
  }>;
  status: 'available' | 'downloading' | 'local' | 'error';
  download_progress?: number;
  metadata: {
    parameters?: string;
    quantization?: string;
    memory_requirement?: string;
    context_length?: number;
    license?: string;
    tags?: string[];
    specialization?: string[];
    performance_metrics?: {
      inference_speed?: string;
      memory_efficiency?: string;
      quality_score?: string;
    };
  };
  local_path?: string;
  download_url?: string;
  checksum?: string;
  disk_usage?: number;
  last_used?: number;
  download_date?: number;
}
interface ModelFilters {
  category: string;
  provider: string;
  status: string;
  modality: string;
}
interface ModelBrowserProps {
  className?: string;
  models?: ModelInfo[];
  onAction?: (modelId: string, action: string) => Promise<void>;
  filters?: ModelFilters;
  onFiltersChange?: React.Dispatch<React.SetStateAction<ModelFilters>>;
}
// Transform ModelInfo from snake_case to camelCase for compatibility with ModelCard
const transformModelForCard = (model: ModelInfo) => ({
  ...model,
  metadata: {
    parameters: model.metadata.parameters || '',
    quantization: model.metadata.quantization || '',
    memoryRequirement: model.metadata.memory_requirement || '',
    contextLength: model.metadata.context_length || 0,
    license: model.metadata.license || '',
    tags: model.metadata.tags || []
  }
});
const ModelBrowser: React.FC<ModelBrowserProps> = ({ 
  className, 
  models: externalModels, 
  onAction: externalOnAction,
  filters: externalFilters,
  onFiltersChange: externalOnFiltersChange
}) => {
  const [internalModels, setInternalModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [internalFilters, setInternalFilters] = useState<ModelFilters>({
    category: 'all',
    provider: 'all',
    status: 'all',
    modality: 'all'
  });
  // Use external props when provided, otherwise use internal state
  const models = externalModels || internalModels;
  const filters = externalFilters || internalFilters;
  const onFiltersChange = externalOnFiltersChange || setInternalFilters;
  const selectedCategory = filters.category;
  const selectedProvider = filters.provider;
  const selectedStatus = filters.status;
  const selectedModality = filters.modality;
  // Filter change handlers
  const handleCategoryChange = (value: string) => {
    onFiltersChange(prev => ({ ...prev, category: value }));
  };
  const handleProviderChange = (value: string) => {
    onFiltersChange(prev => ({ ...prev, provider: value }));
  };
  const handleStatusChange = (value: string) => {
    onFiltersChange(prev => ({ ...prev, status: value }));
  };
  const handleModalityChange = (value: string) => {
    onFiltersChange(prev => ({ ...prev, modality: value }));
  };
  const handleClearFilters = () => {
    setSearchQuery('');
    onFiltersChange({
      category: 'all',
      provider: 'all',
      status: 'all',
      modality: 'all'
    });
  };
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [showPerformanceComparison, setShowPerformanceComparison] = useState(false);
  const [showStatusMonitor, setShowStatusMonitor] = useState(false);
  const [showConfigurationPanel, setShowConfigurationPanel] = useState(false);
  const { toast } = useToast();
  const backend = getKarenBackend();
  // Load models from the discovery service (only when using internal state)
  const loadModels = async () => {
    if (externalModels) return; // Don't load if using external models
    try {
      setLoading(true);
      setError(null);
      // Use the model discovery service endpoint
      const response = await backend.makeRequestPublic<{
        models: ModelInfo[];
        total_count: number;
        categories: Record<string, number>;
        providers: Record<string, number>;
        modalities: Record<string, number>;
      }>('/api/models/discovery/all');
      if (response?.models) {
        setInternalModels(response.models);
      } else {
        // Fallback to model library if discovery service is not available
        const libraryResponse = await backend.makeRequestPublic<{
          models: ModelInfo[];
          total_count: number;
        }>('/api/models/library');
        if (libraryResponse?.models) {
          setInternalModels(libraryResponse.models);
        }
      }
    } catch (err) {
      setError('Failed to load models. Please try again.');
      toast({
        title: "Error Loading Models",
        description: "Could not load model information. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadModels();
  }, []);
  // Filter and search models
  const filteredModels = useMemo(() => {
    return models.filter(model => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const searchableText = [
          model.name,
          model.display_name,
          model.description,
          model.provider,
          model.type,
          model.category,
          ...(model.capabilities || []),
          ...(model.metadata?.tags || []),
          ...(model.metadata?.specialization || [])
        ].join(' ').toLowerCase();
        if (!searchableText.includes(query)) {
          return false;
        }
      }
      // Category filter
      if (selectedCategory !== 'all' && model.category !== selectedCategory) {
        return false;
      }
      // Provider filter
      if (selectedProvider !== 'all' && model.provider !== selectedProvider) {
        return false;
      }
      // Status filter
      if (selectedStatus !== 'all' && model.status !== selectedStatus) {
        return false;
      }
      // Modality filter
      if (selectedModality !== 'all') {
        const hasModality = model.modalities?.some(mod => 
          mod.type.toLowerCase() === selectedModality.toLowerCase()
        );
        if (!hasModality) {
          return false;
        }
      }
      return true;
    });
  }, [models, searchQuery, selectedCategory, selectedProvider, selectedStatus, selectedModality]);
  // Get unique values for filters
  const categories = useMemo(() => {
    const cats = new Set(models.map(m => m.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [models]);
  const providers = useMemo(() => {
    const provs = new Set(models.map(m => m.provider).filter(Boolean));
    return Array.from(provs).sort();
  }, [models]);
  const modalities = useMemo(() => {
    const mods = new Set<string>();
    models.forEach(model => {
      model.modalities?.forEach(mod => {
        mods.add(mod.type);
      });
    });
    return Array.from(mods).sort();
  }, [models]);
  // Handle model actions
  const handleModelAction = async (modelId: string, action: 'download' | 'delete' | 'cancel' | 'pause' | 'resume') => {
    // Use external action handler if provided
    if (externalOnAction) {
      return externalOnAction(modelId, action);
    }
    try {
      let endpoint = '';
      let method = 'POST';
      switch (action) {
        case 'download':
          endpoint = '/api/models/download';
          break;
        case 'delete':
          endpoint = `/api/models/local/${modelId}`;
          method = 'DELETE';
          break;
        case 'cancel':
        case 'pause':
        case 'resume':
          // These would need to be implemented based on the download task system
          endpoint = `/api/models/download/${modelId}/${action}`;
          break;
      }
      if (action === 'download') {
        await backend.makeRequestPublic(endpoint, {
          method,
          body: JSON.stringify({ model_id: modelId })
        });
      } else {
        await backend.makeRequestPublic(endpoint, { method });
      }
      // Refresh models after action
      await loadModels();
      toast({
        title: "Action Completed",
        description: `Model ${action} completed successfully.`,
      });
    } catch (error) {
      toast({
        title: "Action Failed",
        description: `Failed to ${action} model. Please try again.`,
        variant: "destructive",
      });
    }
  };
  // Wrapper for ModelDetailsDialog actions
  const handleDetailsDialogAction = async (modelId: string, action: 'delete' | 'validate' | 'refresh') => {
    switch (action) {
      case 'delete':
        return handleModelAction(modelId, 'delete');
      case 'validate':
        // For now, treat validate as a refresh action
        await loadModels();
        break;
      case 'refresh':
        await loadModels();
        break;
    }
  };
  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'llama-cpp':
      case 'local':
        return <HardDrive className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'transformers':
      case 'huggingface':
        return <Brain className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'openai':
        return <Zap className="h-4 w-4 sm:w-auto md:w-full" />;
      default:
        return <Cpu className="h-4 w-4 sm:w-auto md:w-full" />;
    }
  };
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'local':
        return 'default';
      case 'downloading':
        return 'secondary';
      case 'available':
        return 'outline';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 sm:p-4 md:p-6">
        <Loader2 className="h-8 w-8 animate-spin sm:w-auto md:w-full" />
        <span className="ml-2">Loading models...</span>
      </div>
    );
  }
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
        <AlertDescription>
          {error}
          <button
            variant="outline"
            size="sm"
            onClick={loadModels}
            className="ml-2"
           aria-label="Button">
            <RefreshCw className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Browser</h2>
          <p className="text-muted-foreground">
            Discover, manage, and organize your AI models
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowPerformanceComparison(true)}
          >
            <BarChart3 className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            Compare
          </Button>
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowStatusMonitor(true)}
          >
            <Eye className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            Monitor
          </Button>
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowConfigurationPanel(true)}
          >
            <Settings className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            Configure
          </Button>
          <button
            variant="outline"
            size="sm"
            onClick={loadModels}
           aria-label="Button">
            <RefreshCw className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            Refresh
          </Button>
        </div>
      </div>
      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters & Search</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            <input
              placeholder="Search models by name, description, capabilities..."
              value={searchQuery}
              onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          {/* Filter Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <select value={selectedCategory} onValueChange={handleCategoryChange} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Category" />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Categories</SelectItem>
                {categories.map(category => (
                  <selectItem key={category} value={category} aria-label="Select option">
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <select value={selectedProvider} onValueChange={handleProviderChange} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Provider" />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Providers</SelectItem>
                {providers.map(provider => (
                  <selectItem key={provider} value={provider} aria-label="Select option">
                    <div className="flex items-center gap-2">
                      {getProviderIcon(provider)}
                      {provider}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <select value={selectedStatus} onValueChange={handleStatusChange} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Status" />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Status</SelectItem>
                <selectItem value="local" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />
                    Local
                  </div>
                </SelectItem>
                <selectItem value="available" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-blue-500 sm:w-auto md:w-full" />
                    Available
                  </div>
                </SelectItem>
                <selectItem value="downloading" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <Download className="h-4 w-4 text-orange-500 sm:w-auto md:w-full" />
                    Downloading
                  </div>
                </SelectItem>
                <selectItem value="error" aria-label="Select option">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />
                    Error
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <select value={selectedModality} onValueChange={handleModalityChange} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Modality" />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Modalities</SelectItem>
                {modalities.map(modality => (
                  <selectItem key={modality} value={modality} aria-label="Select option">
                    {modality}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              <button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() = aria-label="Button"> setViewMode('grid')}
              >
                <Grid className="h-4 w-4 sm:w-auto md:w-full" />
              </Button>
              <button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() = aria-label="Button"> setViewMode('list')}
              >
                <List className="h-4 w-4 sm:w-auto md:w-full" />
              </Button>
            </div>
            <div className="text-sm text-muted-foreground flex items-center md:text-base lg:text-lg">
              {filteredModels.length} of {models.length} models
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Models Display */}
      {filteredModels.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">No models found matching your criteria.</p>
            <button
              variant="outline"
              onClick={handleClearFilters}
              className="mt-2"
             aria-label="Button">
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className={
          viewMode === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            : "space-y-4"
        }>
          {filteredModels.map(model => (
            <ModelCard
              key={model.id}
              model={transformModelForCard(model)}
              onAction={handleModelAction}
              searchQuery={searchQuery}
            />
          ))}
        </div>
      )}
      {/* Model Details Dialog */}
      <ModelDetailsDialog
        model={selectedModel ? transformModelForCard(selectedModel) : null}
        open={showDetailsDialog}
        onOpenChange={setShowDetailsDialog}
        onAction={handleDetailsDialogAction}
      />
      {/* Performance Comparison Dialog */}
      <ModelPerformanceComparison
        models={filteredModels}
        open={showPerformanceComparison}
        onOpenChange={setShowPerformanceComparison}
      />
      {/* Status Monitor Dialog */}
      <ModelStatusMonitor
        models={filteredModels}
        open={showStatusMonitor}
        onOpenChange={setShowStatusMonitor}
      />
      {/* Configuration Panel Dialog */}
      <ModelConfigurationPanel
        open={showConfigurationPanel}
        onOpenChange={setShowConfigurationPanel}
      />
    </div>
  );
};
export default ModelBrowser;
