/**
 * Enhanced Model Selector Component
 * 
 * Provides intelligent model selection with priority-based logic:
 * 1. Last selected model
 * 2. Default model  
 * 3. First available model
 */
import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Loader2, CheckCircle, AlertCircle, Star, Settings, RefreshCw, MessageSquare, Image, Layers, Search, Filter, Activity, Zap, ChevronDown, ChevronRight } from 'lucide-react';
import { useModelSelection } from '@/hooks/useModelSelection';
import { modelSelectionService } from '@/lib/model-selection-service';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';
interface EnhancedModelSelectorProps {
  filterByCapability?: string;
  filterByType?: 'text' | 'image' | 'embedding' | 'multimodal';
  preferLocal?: boolean;
  showStats?: boolean;
  showActions?: boolean;
  showScanning?: boolean;
  showFilters?: boolean;
  showHealthIndicators?: boolean;
  onModelChange?: (model: Model | null) => void;
  className?: string;
}
interface ScanStatus {
  isScanning: boolean;
  lastScan?: string;
  scanProgress?: number;
  directoriesScanned?: string[];
  totalModelsFound?: number;
}
interface ModelFilter {
  type?: 'text' | 'image' | 'embedding' | 'multimodal' | 'all';
  capability?: string;
  status?: 'local' | 'available' | 'all';
  health?: 'healthy' | 'unhealthy' | 'all';
  search?: string;
}
interface ModelCardProps {
  model: Model;
  isSelected: boolean;
  onSelect: () => void;
  onSetDefault: () => void;
  showActions: boolean;
  showHealthIndicators: boolean;
}
interface ModelTypeSectionProps {
  title: string;
  icon: React.ReactNode;
  models: Model[];
  selectedModel?: string | null;
  onModelSelect: (modelId: string) => void;
  onSetDefault: () => void;
  showActions: boolean;
  showHealthIndicators: boolean;
  defaultOpen?: boolean;
}
const ModelTypeSection: React.FC<ModelTypeSectionProps> = ({
  title,
  icon,
  models,
  selectedModel,
  onModelSelect,
  onSetDefault,
  showActions,
  showHealthIndicators,
  defaultOpen = true
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  if (models.length === 0) return null;
  const healthyCount = models.filter(m => !m.health || m.health.is_healthy).length;
  const localCount = models.filter(m => m.status === 'local').length;
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <button variant="ghost" className="w-full justify-between p-4 h-auto sm:p-4 md:p-6" aria-label="Button">
          <div className="flex items-center gap-3">
            {icon}
            <div className="text-left">
              <h3 className="font-medium">{title}</h3>
              <div className="flex items-center gap-4 text-sm text-gray-500 md:text-base lg:text-lg">
                <span>{models.length} models</span>
                <span>{localCount} local</span>
                {showHealthIndicators && (
                  <span>{healthyCount} healthy</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{models.length}</Badge>
            {isOpen ? <ChevronDown className="w-4 h-4 sm:w-auto md:w-full" /> : <ChevronRight className="w-4 h-4 sm:w-auto md:w-full" />}
          </div>
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="px-4 pb-4">
        <div className="grid gap-3 mt-2">
          {models.map((model) => (
            <ModelCard 
              key={model.id} 
              model={model} 
              isSelected={selectedModel === model.id}
              onSelect={() => onModelSelect(model.id)}
              onSetDefault={onSetDefault}
              showActions={showActions}
              showHealthIndicators={showHealthIndicators}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};
const ModelCard: React.FC<ModelCardProps> = ({ 
  model, 
  isSelected, 
  onSelect, 
  onSetDefault, 
  showActions,
  showHealthIndicators 
}) => {
  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'text':
        return <MessageSquare className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'image':
        return <Image className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'embedding':
        return <Layers className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'multimodal':
        return <Zap className="w-4 h-4 sm:w-auto md:w-full" />;
      default:
        return <Settings className="w-4 h-4 sm:w-auto md:w-full" />;
    }
  };
  const getTypeBadge = (model: Model) => {
    const type = model.type || 'unknown';
    const colors = {
      text: 'bg-blue-100 text-blue-800',
      image: 'bg-purple-100 text-purple-800',
      embedding: 'bg-green-100 text-green-800',
      multimodal: 'bg-orange-100 text-orange-800',
      unknown: 'bg-gray-100 text-gray-800'
    };
    return (
      <Badge variant="outline" className={colors[type as keyof typeof colors] || colors.unknown}>
        <span className="flex items-center gap-1">
          {getTypeIcon(type)}
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </span>
      </Badge>
    );
  };
  const getStatusBadge = (model: Model) => {
    switch (model.status) {
      case 'local':
        return <Badge variant="default" className="bg-green-100 text-green-800">Local</Badge>;
      case 'available':
        return <Badge variant="outline">Available</Badge>;
      case 'downloading':
        return <Badge variant="default" className="bg-yellow-100 text-yellow-800">Downloading</Badge>;
      default:
        return <Badge variant="secondary">{model.status}</Badge>;
    }
  };
  const getHealthBadge = (model: Model) => {
    if (!showHealthIndicators || !model.health) return null;
    const isHealthy = model.health.is_healthy;
    return (
      <Badge 
        variant={isHealthy ? "default" : "destructive"} 
        className={isHealthy ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
      >
        <span className="flex items-center gap-1">
          {isHealthy ? <CheckCircle className="w-3 h-3 sm:w-auto md:w-full" /> : <AlertCircle className="w-3 h-3 sm:w-auto md:w-full" />}
          {isHealthy ? 'Healthy' : 'Issues'}
        </span>
      </Badge>
    );
  };
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };
  const getModelMetadata = (model: Model) => {
    const metadata = [];
    if (model.size) {
      metadata.push(`Size: ${formatFileSize(model.size)}`);
    }
    if (model.subtype) {
      metadata.push(`Format: ${model.subtype}`);
    }
    if (model.provider) {
      metadata.push(`Provider: ${model.provider}`);
    }
    // Add type-specific metadata
    if (model.metadata) {
      if (model.type === 'text' || model.type === 'multimodal') {
        if (model.metadata.parameter_count) {
          metadata.push(`Parameters: ${model.metadata.parameter_count}`);
        }
        if (model.metadata.context_length) {
          metadata.push(`Context: ${model.metadata.context_length}`);
        }
        if (model.metadata.quantization) {
          metadata.push(`Quantization: ${model.metadata.quantization}`);
        }
      }
      if (model.type === 'image') {
        if (model.metadata.resolution) {
          const res = Array.isArray(model.metadata.resolution) 
            ? model.metadata.resolution.join('x') 
            : model.metadata.resolution;
          metadata.push(`Resolution: ${res}`);
        }
        if (model.metadata.base_model) {
          metadata.push(`Base: ${model.metadata.base_model}`);
        }
      }
    }
    return metadata;
  };
  return (
    <div 
      className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {getTypeIcon(model.type)}
            <h3 className="font-medium text-lg">{model.name}</h3>
            {isSelected && <CheckCircle className="w-4 h-4 text-blue-600 sm:w-auto md:w-full" />}
          </div>
          <p className="text-sm text-gray-600 mb-2 md:text-base lg:text-lg">{model.description}</p>
        </div>
        {showActions && (
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={(e) = aria-label="Button"> {
                e.stopPropagation();
                onSelect();
              }}
              variant={isSelected ? "default" : "outline"}
              size="sm"
            >
              {isSelected ? 'Selected' : 'Select'}
            </Button>
            {isSelected && (
              <button
                onClick={(e) = aria-label="Button"> {
                  e.stopPropagation();
                  onSetDefault();
                }}
                variant="outline"
                size="sm"
              >
                <Star className="w-4 h-4 mr-1 sm:w-auto md:w-full" />
                Set Default
              </Button>
            )}
          </div>
        )}
      </div>
      {/* Badges */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        {getTypeBadge(model)}
        {getStatusBadge(model)}
        {getHealthBadge(model)}
        {/* Capabilities */}
        {model.capabilities?.slice(0, 3).map((capability) => (
          <Badge key={capability} variant="secondary" className="text-xs sm:text-sm md:text-base">
            {capability}
          </Badge>
        ))}
        {model.capabilities && model.capabilities.length > 3 && (
          <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
            +{model.capabilities.length - 3} more
          </Badge>
        )}
      </div>
      {/* Metadata */}
      <div className="text-xs text-gray-500 space-y-1 sm:text-sm md:text-base">
        {getModelMetadata(model).map((item, index) => (
          <div key={index}>{item}</div>
        ))}
        {/* Health Issues */}
        {showHealthIndicators && model.health && !model.health.is_healthy && model.health.issues.length > 0 && (
          <div className="mt-2 p-2 bg-red-50 rounded text-red-700 sm:p-4 md:p-6">
            <div className="font-medium text-xs mb-1 sm:text-sm md:text-base">Health Issues:</div>
            {model.health.issues.slice(0, 2).map((issue, index) => (
              <div key={index} className="text-xs sm:text-sm md:text-base">• {issue}</div>
            ))}
            {model.health.issues.length > 2 && (
              <div className="text-xs sm:text-sm md:text-base">• +{model.health.issues.length - 2} more issues</div>
            )}
          </div>
        )}
        {/* Performance Metrics */}
        {model.health?.performance_metrics && Object.keys(model.health.performance_metrics).length > 0 && (
          <div className="mt-2 p-2 bg-gray-50 rounded sm:p-4 md:p-6">
            <div className="font-medium text-xs mb-1 sm:text-sm md:text-base">Performance:</div>
            <div className="grid grid-cols-2 gap-1 text-xs sm:text-sm md:text-base">
              {Object.entries(model.health.performance_metrics).slice(0, 4).map(([key, value]) => (
                <div key={key}>
                  {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Last used/scanned */}
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
          {model.last_used && (
            <span>Last used: {new Date(model.last_used).toLocaleDateString()}</span>
          )}
          {model.last_scanned && (
            <span>Scanned: {new Date(model.last_scanned).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </div>
  );
};
export default function EnhancedModelSelector({
  filterByCapability,
  filterByType,
  preferLocal = true,
  showStats = true,
  showActions = true,
  showScanning = true,
  showFilters = true,
  showHealthIndicators = true,
  onModelChange,
  className = ''
}: EnhancedModelSelectorProps) {
  const { toast } = useToast();
  const [stats, setStats] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [scanStatus, setScanStatus] = useState<ScanStatus>({ isScanning: false });
  const [modelFilter, setModelFilter] = useState<ModelFilter>({
    type: filterByType || 'all',
    capability: filterByCapability,
    status: 'all',
    health: 'all',
    search: ''
  });
  const {
    models,
    selectedModel,
    selectedModelInfo,
    setSelectedModel,
    loading,
    error,
    refresh,
    selectionReason,
    isModelReady,
    setAsDefault
  } = useModelSelection({
    autoSelect: true,
    preferLocal,
    filterByCapability: modelFilter.capability,
    onModelSelected: (model, reason) => {
      onModelChange?.(model);
      if (model) {
        toast({
          title: 'Model Selected',
          description: `${model.name} selected (${reason.replace('_', ' ')})`,
        });
      }
    }
  });
  // Filter models based on current filter settings
  const filteredModels = useMemo(() => {
    let filtered = [...models];
    // Filter by search term
    if (modelFilter.search?.trim()) {
      const searchTerm = modelFilter.search.toLowerCase();
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(searchTerm) ||
        model.description.toLowerCase().includes(searchTerm) ||
        model.provider.toLowerCase().includes(searchTerm) ||
        model.capabilities?.some(cap => cap.toLowerCase().includes(searchTerm))
      );
    }
    // Filter by type
    if (modelFilter.type && modelFilter.type !== 'all') {
      filtered = filtered.filter(model => {
        if (model.type === modelFilter.type) return true;
        // Support multimodal models that can handle the requested type
        if (model.type === 'multimodal' && modelFilter.type && modelFilter.type !== 'multimodal') {
          return model.capabilities?.includes(`${modelFilter.type}-generation`) || 
                 model.capabilities?.includes(modelFilter.type);
        }
        return false;
      });
    }
    // Filter by status
    if (modelFilter.status && modelFilter.status !== 'all') {
      filtered = filtered.filter(model => model.status === modelFilter.status);
    }
    // Filter by health
    if (modelFilter.health && modelFilter.health !== 'all') {
      filtered = filtered.filter(model => {
        const isHealthy = !model.health || model.health.is_healthy;
        return modelFilter.health === 'healthy' ? isHealthy : !isHealthy;
      });
    }
    return filtered;
  }, [models, modelFilter]);
  // Categorize models by type
  const categorizedModels = useMemo(() => {
    const categories = {
      text: filteredModels.filter(m => m.type === 'text' || (!m.type && m.capabilities?.includes('text-generation'))),
      image: filteredModels.filter(m => m.type === 'image' || m.capabilities?.includes('image-generation')),
      embedding: filteredModels.filter(m => m.type === 'embedding' || m.capabilities?.includes('embedding')),
      multimodal: filteredModels.filter(m => m.type === 'multimodal'),
      other: filteredModels.filter(m => !['text', 'image', 'embedding', 'multimodal'].includes(m.type || ''))
    };
    return categories;
  }, [filteredModels]);
  // Load selection statistics with enhanced categorization
  const loadStats = async () => {
    setLoadingStats(true);
    try {
      const [selectionStats, categorySummary, registry] = await Promise.all([
        modelSelectionService.getSelectionStats(),
        modelSelectionService.getModelCategorySummary(),
        modelSelectionService.getModelRegistry()
      ]);
      setStats({
        ...selectionStats,
        categories: categorySummary,
        scanMetadata: registry.scanMetadata
      });
    } catch (error) {
    } finally {
      setLoadingStats(false);
    }
  };
  // Trigger dynamic model scanning
  const triggerScan = async (forceRefresh = false) => {
    setScanStatus({ isScanning: true, scanProgress: 0 });
    try {
      // Start scanning with progress updates
      const startTime = Date.now();
      // Scan all directories
      const directories = ['models/llama-cpp', 'models/transformers', 'models/stable-diffusion', 'models/flux'];
      let scannedCount = 0;
      for (const directory of directories) {
        setScanStatus(prev => ({
          ...prev,
          scanProgress: (scannedCount / directories.length) * 100,
          directoriesScanned: directories.slice(0, scannedCount + 1)
        }));
        // Simulate scanning progress (in real implementation, this would be actual API calls)
        await new Promise(resolve => setTimeout(resolve, 200));
        scannedCount++;
      }
      // Refresh models with dynamic scanning
      await refresh();
      await loadStats();
      const scanDuration = Date.now() - startTime;
      setScanStatus({
        isScanning: false,
        lastScan: new Date().toISOString(),
        scanProgress: 100,
        directoriesScanned: directories,
        totalModelsFound: models.length
      });
      toast({
        title: 'Scan Complete',
        description: `Found ${models.length} models in ${scanDuration}ms`,
      });
    } catch (error) {
      setScanStatus({ isScanning: false });
      toast({
        title: 'Scan Failed',
        description: 'Failed to scan model directories',
        variant: 'destructive'
      });
    }
  };
  useEffect(() => {
    if (showStats) {
      loadStats();
    }
    // Set up real-time directory watching if scanning is enabled
    if (showScanning) {
      const unsubscribe = modelSelectionService.addChangeListener((event) => {
        // Refresh models when directory changes are detected
        refresh();
        loadStats();
        toast({
          title: 'Models Updated',
          description: `Changes detected in ${event.directory}`,
        });
      });
      return unsubscribe;
    }
  }, [showStats, showScanning, refresh]);
  const handleSetAsDefault = async () => {
    try {
      await setAsDefault();
      toast({
        title: 'Default Model Set',
        description: `${selectedModelInfo?.name} is now your default model`,
      });
      loadStats(); // Refresh stats
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to set default model',
        variant: 'destructive'
      });
    }
  };
  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
  };
  const handleRefresh = async () => {
    try {
      await triggerScan(true);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to refresh models',
        variant: 'destructive'
      });
    }
  };
  const handleFilterChange = (key: keyof ModelFilter, value: any) => {
    setModelFilter(prev => ({ ...prev, [key]: value }));
  };
  const clearFilters = () => {
    setModelFilter({
      type: 'all',
      capability: undefined,
      status: 'all',
      health: 'all',
      search: ''
    });
  };
  const getSelectionReasonBadge = (reason: string | null) => {
    switch (reason) {
      case 'last_selected':
        return <Badge variant="default" className="bg-blue-100 text-blue-800">Last Used</Badge>;
      case 'default':
        return <Badge variant="default" className="bg-green-100 text-green-800">Default</Badge>;
      case 'first_available':
        return <Badge variant="secondary">Auto-Selected</Badge>;
      case 'user_selected':
        return <Badge variant="default" className="bg-purple-100 text-purple-800">User Choice</Badge>;
      default:
        return null;
    }
  };
  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'text':
        return <MessageSquare className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'image':
        return <Image className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'embedding':
        return <Layers className="w-4 h-4 sm:w-auto md:w-full" />;
      case 'multimodal':
        return <Zap className="w-4 h-4 sm:w-auto md:w-full" />;
      default:
        return <Settings className="w-4 h-4 sm:w-auto md:w-full" />;
    }
  };
  const getTypeBadge = (model: Model) => {
    const type = model.type || 'unknown';
    const colors = {
      text: 'bg-blue-100 text-blue-800',
      image: 'bg-purple-100 text-purple-800',
      embedding: 'bg-green-100 text-green-800',
      multimodal: 'bg-orange-100 text-orange-800',
      unknown: 'bg-gray-100 text-gray-800'
    };
    return (
      <Badge variant="outline" className={colors[type as keyof typeof colors] || colors.unknown}>
        <span className="flex items-center gap-1">
          {getTypeIcon(type)}
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </span>
      </Badge>
    );
  };
  const getHealthBadge = (model: Model) => {
    if (!showHealthIndicators || !model.health) return null;
    const isHealthy = model.health.is_healthy;
    return (
      <Badge 
        variant={isHealthy ? "default" : "destructive"} 
        className={isHealthy ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
      >
        <span className="flex items-center gap-1">
          {isHealthy ? <CheckCircle className="w-3 h-3 sm:w-auto md:w-full" /> : <AlertCircle className="w-3 h-3 sm:w-auto md:w-full" />}
          {isHealthy ? 'Healthy' : 'Issues'}
        </span>
      </Badge>
    );
  };
  const getStatusBadge = (model: Model) => {
    switch (model.status) {
      case 'local':
        return <Badge variant="default" className="bg-green-100 text-green-800">Local</Badge>;
      case 'available':
        return <Badge variant="outline">Available</Badge>;
      case 'downloading':
        return <Badge variant="default" className="bg-yellow-100 text-yellow-800">Downloading</Badge>;
      default:
        return <Badge variant="secondary">{model.status}</Badge>;
    }
  };
  const ScanStatusIndicator = () => {
    if (!showScanning) return null;
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600 md:text-base lg:text-lg">
        {scanStatus.isScanning ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin sm:w-auto md:w-full" />
            <span>Scanning... {Math.round(scanStatus.scanProgress || 0)}%</span>
          </>
        ) : scanStatus.lastScan ? (
          <>
            <Activity className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
            <span>Last scan: {new Date(scanStatus.lastScan).toLocaleTimeString()}</span>
            {scanStatus.totalModelsFound && (
              <Badge variant="outline" className="ml-2">
                {scanStatus.totalModelsFound} models
              </Badge>
            )}
          </>
        ) : (
          <>
            <AlertCircle className="w-4 h-4 text-yellow-600 sm:w-auto md:w-full" />
            <span>No recent scan</span>
          </>
        )}
      </div>
    );
  };
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-6 sm:p-4 md:p-6">
          <Loader2 className="h-6 w-6 animate-spin mr-2 sm:w-auto md:w-full" />
          <span>Loading models...</span>
        </CardContent>
      </Card>
    );
  }
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6 sm:p-4 md:p-6">
          <div className="flex items-center text-red-600">
            <AlertCircle className="h-5 w-5 mr-2 sm:w-auto md:w-full" />
            <span>Error: {error}</span>
          </div>
          <button onClick={handleRefresh} className="mt-4" variant="outline" aria-label="Button">
            <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Enhanced Model Library</span>
            <div className="flex items-center gap-2">
              <ScanStatusIndicator />
              {showActions && (
                <button 
                  onClick={handleRefresh} 
                  variant="outline" 
                  size="sm"
                  disabled={scanStatus.isScanning}
                 aria-label="Button">
                  <RefreshCw className={`h-4 w-4 mr-2 ${scanStatus.isScanning ? 'animate-spin' : ''}`} />
                  {scanStatus.isScanning ? 'Scanning...' : 'Scan & Refresh'}
                </Button>
              )}
            </div>
          </CardTitle>
          <CardDescription>
            Dynamic model discovery with multi-modal support and real-time scanning
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          {showFilters && (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <h4 className="font-medium flex items-center gap-2">
                  <Filter className="w-4 h-4 sm:w-auto md:w-full" />
                  Filters
                </h4>
                <button onClick={clearFilters} variant="ghost" size="sm" aria-label="Button">
                  Clear All
                </Button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                  <input
                    placeholder="Search models..."
                    value={modelFilter.search || ''}
                    onChange={(e) = aria-label="Input"> handleFilterChange('search', e.target.value)}
                    className="pl-10"
                  />
                </div>
                {/* Type Filter */}
                <select value={modelFilter.type || 'all'} onValueChange={(value) = aria-label="Select option"> handleFilterChange('type', value)}>
                  <selectTrigger aria-label="Select option">
                    <selectValue placeholder="Model Type" />
                  </SelectTrigger>
                  <selectContent aria-label="Select option">
                    <selectItem value="all" aria-label="Select option">All Types</SelectItem>
                    <selectItem value="text" aria-label="Select option">
                      <span className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 sm:w-auto md:w-full" />
                        Text Generation
                      </span>
                    </SelectItem>
                    <selectItem value="image" aria-label="Select option">
                      <span className="flex items-center gap-2">
                        <Image className="w-4 h-4 sm:w-auto md:w-full" />
                        Image Generation
                      </span>
                    </SelectItem>
                    <selectItem value="embedding" aria-label="Select option">
                      <span className="flex items-center gap-2">
                        <Layers className="w-4 h-4 sm:w-auto md:w-full" />
                        Embedding
                      </span>
                    </SelectItem>
                    <selectItem value="multimodal" aria-label="Select option">
                      <span className="flex items-center gap-2">
                        <Zap className="w-4 h-4 sm:w-auto md:w-full" />
                        Multi-modal
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
                {/* Status Filter */}
                <select value={modelFilter.status || 'all'} onValueChange={(value) = aria-label="Select option"> handleFilterChange('status', value)}>
                  <selectTrigger aria-label="Select option">
                    <selectValue placeholder="Status" />
                  </SelectTrigger>
                  <selectContent aria-label="Select option">
                    <selectItem value="all" aria-label="Select option">All Status</SelectItem>
                    <selectItem value="local" aria-label="Select option">Local Only</SelectItem>
                    <selectItem value="available" aria-label="Select option">Available</SelectItem>
                  </SelectContent>
                </Select>
                {/* Health Filter */}
                {showHealthIndicators && (
                  <select value={modelFilter.health || 'all'} onValueChange={(value) = aria-label="Select option"> handleFilterChange('health', value)}>
                    <selectTrigger aria-label="Select option">
                      <selectValue placeholder="Health" />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="all" aria-label="Select option">All Models</SelectItem>
                      <selectItem value="healthy" aria-label="Select option">Healthy Only</SelectItem>
                      <selectItem value="unhealthy" aria-label="Select option">With Issues</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              </div>
              {/* Active Filters Summary */}
              <div className="flex items-center gap-2 flex-wrap">
                {Object.entries(modelFilter).map(([key, value]) => {
                  if (!value || value === 'all' || (key === 'search' && !value.trim())) return null;
                  return (
                    <Badge key={key} variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {key}: {value}
                    </Badge>
                  );
                })}
                {filteredModels.length !== models.length && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {filteredModels.length} of {models.length} models
                  </Badge>
                )}
              </div>
            </div>
          )}
          {/* Current Selection */}
          {selectedModelInfo && (
            <div className="p-4 bg-gray-50 rounded-lg sm:p-4 md:p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium">{selectedModelInfo.name}</h4>
                <div className="flex items-center space-x-2">
                  {getSelectionReasonBadge(selectionReason)}
                  {getTypeBadge(selectedModelInfo)}
                  {getStatusBadge(selectedModelInfo)}
                  {getHealthBadge(selectedModelInfo)}
                  {isModelReady && <CheckCircle className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />}
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2 md:text-base lg:text-lg">{selectedModelInfo.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-500 sm:text-sm md:text-base">
                  <span>Provider: {selectedModelInfo.provider || 'Unknown'}</span>
                  {selectedModelInfo.subtype && (
                    <span>Format: {selectedModelInfo.subtype}</span>
                  )}
                  {selectedModelInfo.size && (
                    <span>Size: {(selectedModelInfo.size / 1e9).toFixed(1)}GB</span>
                  )}
                </div>
                {showActions && selectedModel && (
                  <button onClick={handleSetAsDefault} variant="outline" size="sm" aria-label="Button">
                    <Star className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                    Set as Default
                  </Button>
                )}
              </div>
            </div>
          )}
          {/* Model Selector */}
          <div>
            <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Select Model</label>
            <select value={selectedModel || ''} onValueChange={setSelectedModel} aria-label="Select option">
              <selectTrigger aria-label="Select option">
                <selectValue placeholder="Choose a model..." />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                {filteredModels.map((model) => (
                  <selectItem key={model.id} value={model.id} aria-label="Select option">
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-2">
                        {getTypeIcon(model.type)}
                        <span>{model.name}</span>
                      </div>
                      <div className="flex items-center space-x-1 ml-2">
                        {getStatusBadge(model)}
                        {showHealthIndicators && model.health && !model.health.is_healthy && (
                          <AlertCircle className="w-3 h-3 text-red-500 sm:w-auto md:w-full" />
                        )}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {filteredModels.length === 0 && (
            <div className="text-center py-4 text-gray-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 sm:w-auto md:w-full" />
              <p>No models match current filters</p>
              <div className="text-sm mt-2 space-y-1 md:text-base lg:text-lg">
                {models.length === 0 ? (
                  <p>Try scanning for models or check your model directories</p>
                ) : (
                  <p>Try adjusting your filters or clearing them</p>
                )}
                {showActions && (
                  <button onClick={clearFilters} variant="outline" size="sm" className="mt-2" aria-label="Button">
                    Clear Filters
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Categorized Model Sections */}
      {filteredModels.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Available Models ({filteredModels.length})</span>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {categorizedModels.text.length} Text
                </Badge>
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {categorizedModels.image.length} Image
                </Badge>
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {categorizedModels.embedding.length} Embedding
                </Badge>
                {categorizedModels.multimodal.length > 0 && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {categorizedModels.multimodal.length} Multi-modal
                  </Badge>
                )}
                {categorizedModels.other.length > 0 && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {categorizedModels.other.length} Other
                  </Badge>
                )}
              </div>
            </CardTitle>
            <CardDescription>
              Models organized by type with collapsible sections
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* Text Generation Models */}
            <ModelTypeSection
              title="Text Generation Models"
              icon={<MessageSquare className="w-5 h-5 text-blue-600 sm:w-auto md:w-full" />}
              models={categorizedModels.text}
              selectedModel={selectedModel}
              onModelSelect={handleModelSelect}
              onSetDefault={handleSetAsDefault}
              showActions={showActions}
              showHealthIndicators={showHealthIndicators}
              defaultOpen={modelFilter.type === 'text' || modelFilter.type === 'all'}
            />
            {/* Image Generation Models */}
            <ModelTypeSection
              title="Image Generation Models"
              icon={<Image className="w-5 h-5 text-purple-600 sm:w-auto md:w-full" />}
              models={categorizedModels.image}
              selectedModel={selectedModel}
              onModelSelect={handleModelSelect}
              onSetDefault={handleSetAsDefault}
              showActions={showActions}
              showHealthIndicators={showHealthIndicators}
              defaultOpen={modelFilter.type === 'image'}
            />
            {/* Embedding Models */}
            <ModelTypeSection
              title="Embedding Models"
              icon={<Layers className="w-5 h-5 text-green-600 sm:w-auto md:w-full" />}
              models={categorizedModels.embedding}
              selectedModel={selectedModel}
              onModelSelect={handleModelSelect}
              onSetDefault={handleSetAsDefault}
              showActions={showActions}
              showHealthIndicators={showHealthIndicators}
              defaultOpen={modelFilter.type === 'embedding'}
            />
            {/* Multi-modal Models */}
            <ModelTypeSection
              title="Multi-modal Models"
              icon={<Zap className="w-5 h-5 text-orange-600 sm:w-auto md:w-full" />}
              models={categorizedModels.multimodal}
              selectedModel={selectedModel}
              onModelSelect={handleModelSelect}
              onSetDefault={handleSetAsDefault}
              showActions={showActions}
              showHealthIndicators={showHealthIndicators}
              defaultOpen={modelFilter.type === 'multimodal'}
            />
            {/* Other Models */}
            {categorizedModels.other.length > 0 && (
              <ModelTypeSection
                title="Other Models"
                icon={<Settings className="w-5 h-5 text-gray-600 sm:w-auto md:w-full" />}
                models={categorizedModels.other}
                selectedModel={selectedModel}
                onModelSelect={handleModelSelect}
                onSetDefault={handleSetAsDefault}
                showActions={showActions}
                showHealthIndicators={showHealthIndicators}
                defaultOpen={false}
              />
            )}
            {/* Quick Actions */}
            {showActions && (
              <div className="pt-4 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium md:text-base lg:text-lg">Quick Actions</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() = aria-label="Button"> handleFilterChange('type', 'all')}
                      variant="outline"
                      size="sm"
                    >
                      Show All Types
                    </Button>
                    <button
                      onClick={() = aria-label="Button"> handleFilterChange('status', 'local')}
                      variant="outline"
                      size="sm"
                    >
                      Local Only
                    </Button>
                    {showHealthIndicators && (
                      <button
                        onClick={() = aria-label="Button"> handleFilterChange('health', 'healthy')}
                        variant="outline"
                        size="sm"
                      >
                        Healthy Only
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      {/* Enhanced Statistics */}
      {showStats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2 sm:w-auto md:w-full" />
              Model Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingStats ? (
              <div className="flex items-center">
                <Loader2 className="h-4 w-4 animate-spin mr-2 sm:w-auto md:w-full" />
                <span>Loading statistics...</span>
              </div>
            ) : stats ? (
              <div className="space-y-6">
                {/* Overall Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{stats.totalModels || models.length}</div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">Total Models</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{stats.readyModels || models.filter(m => m.status === 'local').length}</div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">Ready Models</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{stats.localModels || models.filter(m => m.status === 'local').length}</div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">Local Models</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{filteredModels.length}</div>
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">Filtered Models</div>
                  </div>
                </div>
                {/* Model Type Breakdown */}
                {stats.categories && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Layers className="w-4 h-4 sm:w-auto md:w-full" />
                      Model Types
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(stats.categories.types).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded sm:p-4 md:p-6">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(type)}
                            <span className="text-sm capitalize md:text-base lg:text-lg">{type}</span>
                          </div>
                          <Badge variant="outline">{String(count)}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* Health Status */}
                {showHealthIndicators && stats.categories?.health && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Activity className="w-4 h-4 sm:w-auto md:w-full" />
                      Health Status
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex items-center justify-between p-2 bg-green-50 rounded sm:p-4 md:p-6">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
                          <span className="text-sm md:text-base lg:text-lg">Healthy</span>
                        </div>
                        <Badge variant="outline" className="bg-green-100 text-green-800">
                          {stats.categories.health.healthy || 0}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-red-50 rounded sm:p-4 md:p-6">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />
                          <span className="text-sm md:text-base lg:text-lg">Issues</span>
                        </div>
                        <Badge variant="outline" className="bg-red-100 text-red-800">
                          {stats.categories.health.unhealthy || 0}
                        </Badge>
                      </div>
                    </div>
                  </div>
                )}
                {/* Scan Metadata */}
                {stats.scanMetadata && (
                  <div className="text-xs text-gray-500 pt-2 border-t sm:text-sm md:text-base">
                    <div className="flex items-center justify-between">
                      <span>Last scan: {new Date(stats.scanMetadata.last_scan).toLocaleString()}</span>
                      <span>Scan duration: {stats.scanMetadata.scan_duration_ms}ms</span>
                    </div>
                    <div className="mt-1">
                      Directories: {stats.scanMetadata.directories_scanned?.join(', ')}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">Statistics unavailable</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
