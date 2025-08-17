"use client";

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import {
  Database,
  Search,
  Filter,
  Download,
  Upload,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  HardDrive,
  Cloud,
  Globe,
  Zap,
  Eye,
  Settings,
  Shield,
  Lock,
  Info,
  Star,
  Calendar,
  FileText,
  Tag,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

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
  huggingface_id?: string;
  is_local?: boolean;
  download_status?: 'available' | 'downloading' | 'downloaded' | 'error';
  download_progress?: number;
}

interface ModelFilters {
  provider?: string;
  format?: string;
  size_range?: [number, number];
  capabilities?: string[];
  local_only?: boolean;
  remote_only?: boolean;
  search_query?: string;
  sort_by?: 'name' | 'size' | 'downloads' | 'likes' | 'updated' | 'created';
  sort_order?: 'asc' | 'desc';
  family?: string;
  license?: string;
  runtime?: string;
}

interface HuggingFaceSearchResult {
  models: ModelInfo[];
  total: number;
  page: number;
  per_page: number;
}

interface ModelBrowserProps {
  providers: Array<{
    name: string;
    provider_type: string;
    capabilities: string[];
  }>;
  onModelSelect?: (model: ModelInfo) => void;
  selectedModels?: string[];
  allowMultiSelect?: boolean;
  showDownloadActions?: boolean;
}

const HUGGINGFACE_SEARCH_ENDPOINT = '/api/huggingface/search';
const MODEL_DOWNLOAD_ENDPOINT = '/api/models/download';

export default function ModelBrowser({
  providers = [],
  onModelSelect,
  selectedModels = [],
  allowMultiSelect = false,
  showDownloadActions = true
}: ModelBrowserProps) {
  // State
  const [localModels, setLocalModels] = useState<ModelInfo[]>([]);
  const [huggingFaceModels, setHuggingFaceModels] = useState<ModelInfo[]>([]);
  const [searchResults, setSearchResults] = useState<HuggingFaceSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  
  // Filters and search
  const [filters, setFilters] = useState<ModelFilters>({
    sort_by: 'downloads',
    sort_order: 'desc'
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, setActiveTab] = useState<'local' | 'huggingface' | 'all'>('all');
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  // Load models on mount
  useEffect(() => {
    loadLocalModels();
    searchHuggingFaceModels('', 1);
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        searchHuggingFaceModels(searchQuery, 1);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadLocalModels = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<ModelInfo[]>('/api/models/local');
      setLocalModels(response || []);
    } catch (error) {
      console.error('Failed to load local models:', error);
      setLocalModels([]);
    } finally {
      setLoading(false);
    }
  };

  const searchHuggingFaceModels = async (query: string, page: number = 1) => {
    try {
      setSearchLoading(true);
      const params = new URLSearchParams({
        query: query || '',
        page: page.toString(),
        per_page: '20',
        sort: filters.sort_by || 'downloads',
        direction: filters.sort_order || 'desc'
      });

      if (filters.format) params.append('filter', `format:${filters.format}`);
      if (filters.license) params.append('filter', `license:${filters.license}`);

      const response = await backend.makeRequestPublic<HuggingFaceSearchResult>(
        `${HUGGINGFACE_SEARCH_ENDPOINT}?${params}`
      );
      
      setSearchResults(response);
      setHuggingFaceModels(response?.models || []);
    } catch (error) {
      console.error('Failed to search Hugging Face models:', error);
      setSearchResults(null);
      setHuggingFaceModels([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const downloadModel = async (model: ModelInfo) => {
    try {
      setDownloadingModels(prev => new Set(prev).add(model.id));
      
      const response = await backend.makeRequestPublic('/api/models/download', {
        method: 'POST',
        body: JSON.stringify({
          model_id: model.huggingface_id || model.id,
          model_name: model.name,
          provider: model.provider
        })
      });

      toast({
        title: "Download Started",
        description: `Started downloading ${model.name}. Check the downloads section for progress.`,
      });

      // Refresh local models after a delay
      setTimeout(() => {
        loadLocalModels();
      }, 2000);

    } catch (error) {
      console.error('Failed to download model:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'downloadModel');
      toast({
        variant: 'destructive',
        title: info.title || "Download Failed",
        description: info.message || "Could not start model download.",
      });
    } finally {
      setDownloadingModels(prev => {
        const newSet = new Set(prev);
        newSet.delete(model.id);
        return newSet;
      });
    }
  };

  // Combined and filtered models
  const allModels = useMemo(() => {
    let combined: ModelInfo[] = [];
    
    switch (activeTab) {
      case 'local':
        combined = localModels;
        break;
      case 'huggingface':
        combined = huggingFaceModels;
        break;
      case 'all':
      default:
        combined = [...localModels, ...huggingFaceModels];
        break;
    }

    return combined;
  }, [localModels, huggingFaceModels, activeTab]);

  const filteredModels = useMemo(() => {
    let filtered = [...allModels];
    
    // Apply filters
    if (filters.provider) {
      filtered = filtered.filter(model => model.provider === filters.provider);
    }
    
    if (filters.format) {
      filtered = filtered.filter(model => model.format === filters.format);
    }
    
    if (filters.family) {
      filtered = filtered.filter(model => 
        model.family.toLowerCase().includes(filters.family!.toLowerCase())
      );
    }
    
    if (filters.capabilities?.length) {
      filtered = filtered.filter(model => 
        filters.capabilities!.every(cap => model.capabilities.includes(cap))
      );
    }
    
    if (filters.local_only) {
      filtered = filtered.filter(model => model.is_local || model.local_path);
    }
    
    if (filters.remote_only) {
      filtered = filtered.filter(model => !model.is_local && !model.local_path);
    }
    
    if (filters.size_range) {
      const [min, max] = filters.size_range;
      filtered = filtered.filter(model => {
        if (!model.size) return false;
        return model.size >= min && model.size <= max;
      });
    }
    
    if (filters.runtime) {
      filtered = filtered.filter(model => 
        model.runtime_compatibility?.includes(filters.runtime!)
      );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      const { sort_by = 'downloads', sort_order = 'desc' } = filters;
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
        case 'created':
          comparison = new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
          break;
      }
      
      return sort_order === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  }, [allModels, filters]);

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

  const getModelTypeIcon = (model: ModelInfo) => {
    if (model.is_local || model.local_path) {
      return <HardDrive className="h-4 w-4 text-green-600" />;
    }
    return <Cloud className="h-4 w-4 text-blue-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Browser</h2>
          <p className="text-muted-foreground">
            Browse local models and discover new ones from Hugging Face
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              loadLocalModels();
              searchHuggingFaceModels(searchQuery, 1);
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
        <Button
          variant={activeTab === 'all' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('all')}
        >
          <Globe className="h-4 w-4 mr-2" />
          All Models
        </Button>
        <Button
          variant={activeTab === 'local' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('local')}
        >
          <HardDrive className="h-4 w-4 mr-2" />
          Local ({localModels.length})
        </Button>
        <Button
          variant={activeTab === 'huggingface' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('huggingface')}
        >
          <Cloud className="h-4 w-4 mr-2" />
          Hugging Face
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search models by name, description, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>
            <Select
              value={filters.sort_by || 'downloads'}
              onValueChange={(value) => setFilters(prev => ({ 
                ...prev, 
                sort_by: value as ModelFilters['sort_by'] 
              }))}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Sort by Name</SelectItem>
                <SelectItem value="size">Sort by Size</SelectItem>
                <SelectItem value="downloads">Sort by Downloads</SelectItem>
                <SelectItem value="likes">Sort by Likes</SelectItem>
                <SelectItem value="updated">Sort by Updated</SelectItem>
                <SelectItem value="created">Sort by Created</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters(prev => ({ 
                ...prev, 
                sort_order: prev.sort_order === 'asc' ? 'desc' : 'asc' 
              }))}
            >
              {filters.sort_order === 'asc' ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-muted/30 rounded-lg">
              <div>
                <Label className="text-sm font-medium">Provider</Label>
                <Select
                  value={filters.provider || ''}
                  onValueChange={(value) => setFilters(prev => ({ 
                    ...prev, 
                    provider: value || undefined 
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All providers" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All providers</SelectItem>
                    {providers.map(provider => (
                      <SelectItem key={provider.name} value={provider.name}>
                        {provider.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Format</Label>
                <Select
                  value={filters.format || ''}
                  onValueChange={(value) => setFilters(prev => ({ 
                    ...prev, 
                    format: value || undefined 
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All formats" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All formats</SelectItem>
                    <SelectItem value="gguf">GGUF</SelectItem>
                    <SelectItem value="safetensors">SafeTensors</SelectItem>
                    <SelectItem value="pytorch">PyTorch</SelectItem>
                    <SelectItem value="onnx">ONNX</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Model Family</Label>
                <Input
                  placeholder="e.g., llama, mistral"
                  value={filters.family || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    family: e.target.value || undefined 
                  }))}
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="local-only"
                    checked={filters.local_only || false}
                    onCheckedChange={(checked) => setFilters(prev => ({ 
                      ...prev, 
                      local_only: checked,
                      remote_only: checked ? false : prev.remote_only
                    }))}
                  />
                  <Label htmlFor="local-only" className="text-sm">Local only</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="remote-only"
                    checked={filters.remote_only || false}
                    onCheckedChange={(checked) => setFilters(prev => ({ 
                      ...prev, 
                      remote_only: checked,
                      local_only: checked ? false : prev.local_only
                    }))}
                  />
                  <Label htmlFor="remote-only" className="text-sm">Remote only</Label>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card> 
     {/* Model Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>
                {activeTab === 'local' && 'Local Models'}
                {activeTab === 'huggingface' && 'Hugging Face Models'}
                {activeTab === 'all' && 'All Models'}
              </CardTitle>
              <CardDescription>
                {filteredModels.length > 0 ? (
                  `Showing ${filteredModels.length} model${filteredModels.length !== 1 ? 's' : ''}`
                ) : (
                  'No models found matching your criteria'
                )}
              </CardDescription>
            </div>
            {searchResults && activeTab === 'huggingface' && (
              <div className="text-sm text-muted-foreground">
                Page {searchResults.page} of {Math.ceil(searchResults.total / searchResults.per_page)}
              </div>
            )}
          </div>
        </CardHeader>
        
        <CardContent>
          {loading || searchLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">
                  {loading ? 'Loading local models...' : 'Searching models...'}
                </p>
              </div>
            </div>
          ) : filteredModels.length > 0 ? (
            <div className="space-y-4">
              {filteredModels.map((model) => (
                <Card 
                  key={model.id} 
                  className={`hover:shadow-md transition-all cursor-pointer ${
                    selectedModels.includes(model.id) ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => onModelSelect?.(model)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          {getModelTypeIcon(model)}
                          <div>
                            <h4 className="font-semibold text-lg">{model.name}</h4>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {model.provider}
                              </Badge>
                              {model.family && (
                                <Badge variant="secondary" className="text-xs">
                                  {model.family}
                                </Badge>
                              )}
                              {model.is_local || model.local_path ? (
                                <Badge variant="default" className="text-xs bg-green-100 text-green-800">
                                  <HardDrive className="h-3 w-3 mr-1" />
                                  Local
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="text-xs">
                                  <Cloud className="h-3 w-3 mr-1" />
                                  Remote
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {model.description && (
                          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                            {model.description}
                          </p>
                        )}
                        
                        {/* Model Metadata */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          {model.parameters && (
                            <div>
                              <span className="text-xs text-muted-foreground">Parameters</span>
                              <div className="font-medium text-sm">{model.parameters}</div>
                            </div>
                          )}
                          {model.size && (
                            <div>
                              <span className="text-xs text-muted-foreground">Size</span>
                              <div className="font-medium text-sm">{formatFileSize(model.size)}</div>
                            </div>
                          )}
                          {model.context_length && (
                            <div>
                              <span className="text-xs text-muted-foreground">Context</span>
                              <div className="font-medium text-sm">{model.context_length.toLocaleString()} tokens</div>
                            </div>
                          )}
                          {model.format && (
                            <div>
                              <span className="text-xs text-muted-foreground">Format</span>
                              <div className="font-medium text-sm">{model.format.toUpperCase()}</div>
                            </div>
                          )}
                        </div>
                        
                        {/* Capabilities */}
                        {model.capabilities.length > 0 && (
                          <div className="mb-4">
                            <span className="text-xs text-muted-foreground mb-2 block">Capabilities</span>
                            <div className="flex flex-wrap gap-1">
                              {model.capabilities.map((capability) => (
                                <Badge key={capability} variant="outline" className="text-xs flex items-center gap-1">
                                  {getCapabilityIcon(capability)}
                                  {capability.replace('_', ' ')}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Tags */}
                        {model.tags && model.tags.length > 0 && (
                          <div className="mb-4">
                            <span className="text-xs text-muted-foreground mb-2 block">Tags</span>
                            <div className="flex flex-wrap gap-1">
                              {model.tags.slice(0, 8).map(tag => (
                                <Badge key={tag} variant="outline" className="text-xs">
                                  <Tag className="h-3 w-3 mr-1" />
                                  {tag}
                                </Badge>
                              ))}
                              {model.tags.length > 8 && (
                                <span className="text-xs text-muted-foreground">
                                  +{model.tags.length - 8} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Runtime Compatibility */}
                        {model.runtime_compatibility && model.runtime_compatibility.length > 0 && (
                          <div className="mb-4">
                            <span className="text-xs text-muted-foreground mb-2 block">Runtime Compatibility</span>
                            <div className="flex flex-wrap gap-1">
                              {model.runtime_compatibility.map(runtime => (
                                <Badge key={runtime} variant="secondary" className="text-xs">
                                  {runtime}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Right Side - Stats and Actions */}
                      <div className="ml-6 text-right space-y-3">
                        {/* Stats */}
                        <div className="space-y-2">
                          {model.downloads && (
                            <div className="flex items-center justify-end gap-1 text-sm text-muted-foreground">
                              <Download className="h-4 w-4" />
                              {model.downloads.toLocaleString()}
                            </div>
                          )}
                          {model.likes && (
                            <div className="flex items-center justify-end gap-1 text-sm text-muted-foreground">
                              <Star className="h-4 w-4" />
                              {model.likes.toLocaleString()}
                            </div>
                          )}
                          {model.updated_at && (
                            <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground">
                              <Calendar className="h-3 w-3" />
                              {new Date(model.updated_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        
                        {/* Actions */}
                        {showDownloadActions && (
                          <div className="space-y-2">
                            {model.is_local || model.local_path ? (
                              <div className="flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                                <span className="text-sm text-green-600">Downloaded</span>
                              </div>
                            ) : (
                              <Button
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  downloadModel(model);
                                }}
                                disabled={downloadingModels.has(model.id)}
                              >
                                {downloadingModels.has(model.id) ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Downloading
                                  </>
                                ) : (
                                  <>
                                    <Download className="h-4 w-4 mr-2" />
                                    Download
                                  </>
                                )}
                              </Button>
                            )}
                            
                            {model.huggingface_id && (
                              <Button
                                variant="outline"
                                size="sm"
                                asChild
                                onClick={(e) => e.stopPropagation()}
                              >
                                <a 
                                  href={`https://huggingface.co/${model.huggingface_id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <ExternalLink className="h-4 w-4 mr-2" />
                                  View on HF
                                </a>
                              </Button>
                            )}
                          </div>
                        )}
                        
                        {/* License */}
                        {model.license && (
                          <div className="text-xs text-muted-foreground">
                            <FileText className="h-3 w-3 inline mr-1" />
                            {model.license}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Download Progress */}
                    {model.download_status === 'downloading' && model.download_progress !== undefined && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Downloading...</span>
                          <span className="text-sm font-medium">{model.download_progress}%</span>
                        </div>
                        <Progress value={model.download_progress} className="h-2" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              
              {/* Pagination for Hugging Face results */}
              {searchResults && activeTab === 'huggingface' && searchResults.total > searchResults.per_page && (
                <div className="flex justify-center gap-2 pt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => searchHuggingFaceModels(searchQuery, searchResults.page - 1)}
                    disabled={searchResults.page <= 1 || searchLoading}
                  >
                    Previous
                  </Button>
                  <span className="flex items-center px-4 text-sm text-muted-foreground">
                    Page {searchResults.page} of {Math.ceil(searchResults.total / searchResults.per_page)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => searchHuggingFaceModels(searchQuery, searchResults.page + 1)}
                    disabled={searchResults.page >= Math.ceil(searchResults.total / searchResults.per_page) || searchLoading}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No Models Found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery || Object.keys(filters).some(k => filters[k as keyof ModelFilters])
                  ? 'No models match your current filters.'
                  : activeTab === 'local' 
                    ? 'No local models found. Download some models to get started.'
                    : 'Try searching for models or adjusting your filters.'}
              </p>
              {activeTab === 'local' && (
                <Button onClick={() => setActiveTab('huggingface')}>
                  <Cloud className="h-4 w-4 mr-2" />
                  Browse Hugging Face Models
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Summary Stats */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-primary">{localModels.length}</div>
              <div className="text-xs text-muted-foreground">Local Models</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{searchResults?.total || 0}</div>
              <div className="text-xs text-muted-foreground">Available on HF</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{downloadingModels.size}</div>
              <div className="text-xs text-muted-foreground">Downloading</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{filteredModels.length}</div>
              <div className="text-xs text-muted-foreground">Filtered Results</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}