"use client";

import React, { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Search, 
  Filter, 
  SortAsc, 
  SortDesc, 
  Grid, 
  List,
  Download,
  Star,
  Calendar,
  HardDrive,
  Tag,
  User,
  Package
} from 'lucide-react';
import { cn } from '@/lib/utils';
import ModelCard from './ModelCard';
import ModelFilters from './ModelFilters';

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
  description?: string;
  capabilities?: string[];
  metadata?: ModelMetadata;
}

interface FileInfo {
  path: string;
  size: number;
  sha256?: string;
}

interface CompatibilityInfo {
  cpu_features: string[];
  gpu_required: boolean;
  min_ram_gb: number;
  min_vram_gb: number;
}

interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}

interface ModelFiltersType {
  search: string;
  library: string;
  status: string;
  owner: string;
  tags: string[];
}

interface ModelBrowserProps {
  models: ModelInfo[];
  onAction: (modelId: string, action: string) => Promise<void>;
  filters: ModelFiltersType;
  onFiltersChange: (filters: ModelFiltersType) => void;
}

type SortOption = 'name' | 'downloads' | 'likes' | 'size' | 'modified';
type SortDirection = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

/**
 * Model browser component with search, filtering, and sorting capabilities
 * Provides rich interface for discovering and managing available models
 */
export default function ModelBrowser({ 
  models, 
  onAction, 
  filters, 
  onFiltersChange 
}: ModelBrowserProps) {
  const [sortBy, setSortBy] = useState<SortOption>('downloads');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  // Extract unique values for filter options
  const filterOptions = useMemo(() => {
    const libraries = [...new Set(models.map(m => m.library))].sort();
    const owners = [...new Set(models.map(m => m.owner))].sort();
    const allTags = [...new Set(models.flatMap(m => m.tags || []))].sort();
    const statuses = [...new Set(models.map(m => m.status))].sort();
    
    return { libraries, owners, allTags, statuses };
  }, [models]);

  // Filter and sort models
  const filteredAndSortedModels = useMemo(() => {
    let filtered = models;

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(searchLower) ||
        model.owner.toLowerCase().includes(searchLower) ||
        model.description?.toLowerCase().includes(searchLower) ||
        model.tags?.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // Apply library filter
    if (filters.library) {
      filtered = filtered.filter(model => model.library === filters.library);
    }

    // Apply status filter
    if (filters.status) {
      filtered = filtered.filter(model => model.status === filters.status);
    }

    // Apply owner filter
    if (filters.owner) {
      filtered = filtered.filter(model => model.owner === filters.owner);
    }

    // Apply tags filter
    if (filters.tags.length > 0) {
      filtered = filtered.filter(model => 
        filters.tags.some(tag => model.tags?.includes(tag))
      );
    }

    // Sort models
    const sorted = [...filtered].sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'downloads':
          aValue = a.downloads || 0;
          bValue = b.downloads || 0;
          break;
        case 'likes':
          aValue = a.likes || 0;
          bValue = b.likes || 0;
          break;
        case 'size':
          aValue = a.total_size || 0;
          bValue = b.total_size || 0;
          break;
        case 'modified':
          aValue = new Date(a.last_modified || 0).getTime();
          bValue = new Date(b.last_modified || 0).getTime();
          break;
        default:
          return 0;
      }

      if (typeof aValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return sortDirection === 'asc' 
          ? aValue - bValue
          : bValue - aValue;
      }
    });

    return sorted;
  }, [models, filters, sortBy, sortDirection]);

  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value });
  };

  const handleBulkAction = async (action: string) => {
    const selectedArray = Array.from(selectedModels);
    if (selectedArray.length === 0) return;

    try {
      await Promise.all(
        selectedArray.map(modelId => onAction(modelId, action))
      );
      setSelectedModels(new Set());
    } catch (error) {
      console.error(`Bulk ${action} failed:`, error);
    }
  };

  const toggleModelSelection = (modelId: string) => {
    const newSelection = new Set(selectedModels);
    if (newSelection.has(modelId)) {
      newSelection.delete(modelId);
    } else {
      newSelection.add(modelId);
    }
    setSelectedModels(newSelection);
  };

  const selectAllVisible = () => {
    const visibleIds = new Set(filteredAndSortedModels.map(m => m.id));
    setSelectedModels(visibleIds);
  };

  const clearSelection = () => {
    setSelectedModels(new Set());
  };

  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <div className="space-y-4">
      {/* Search and Controls Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search models by name, owner, description, or tags..."
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(showFilters && "bg-secondary")}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          
          <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="downloads">
                <div className="flex items-center gap-2">
                  <Download className="h-3 w-3" />
                  Downloads
                </div>
              </SelectItem>
              <SelectItem value="likes">
                <div className="flex items-center gap-2">
                  <Star className="h-3 w-3" />
                  Likes
                </div>
              </SelectItem>
              <SelectItem value="name">
                <div className="flex items-center gap-2">
                  <Package className="h-3 w-3" />
                  Name
                </div>
              </SelectItem>
              <SelectItem value="size">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-3 w-3" />
                  Size
                </div>
              </SelectItem>
              <SelectItem value="modified">
                <div className="flex items-center gap-2">
                  <Calendar className="h-3 w-3" />
                  Modified
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
          >
            {sortDirection === 'asc' ? (
              <SortAsc className="h-4 w-4" />
            ) : (
              <SortDesc className="h-4 w-4" />
            )}
          </Button>
          
          <Separator orientation="vertical" className="h-6" />
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? (
              <List className="h-4 w-4" />
            ) : (
              <Grid className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Advanced Filters Panel */}
      {showFilters && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Advanced Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <ModelFilters
              filters={filters}
              onFiltersChange={onFiltersChange}
              filterOptions={filterOptions}
            />
          </CardContent>
        </Card>
      )}

      {/* Bulk Actions Bar */}
      {selectedModels.size > 0 && (
        <Card className="bg-secondary/50">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">
                  {selectedModels.size} model{selectedModels.size !== 1 ? 's' : ''} selected
                </span>
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={selectAllVisible}>
                    Select All Visible ({filteredAndSortedModels.length})
                  </Button>
                  <Button variant="outline" size="sm" onClick={clearSelection}>
                    Clear Selection
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  size="sm" 
                  onClick={() => handleBulkAction('download')}
                  disabled={!Array.from(selectedModels).some(id => 
                    models.find(m => m.id === id)?.status === 'available'
                  )}
                >
                  <Download className="h-3 w-3 mr-1" />
                  Download Selected
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Showing {filteredAndSortedModels.length} of {models.length} models
        </span>
        {filters.search && (
          <span>
            Search results for "{filters.search}"
          </span>
        )}
      </div>

      {/* Models Display */}
      {filteredAndSortedModels.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No models found</h3>
            <p className="text-muted-foreground mb-4">
              {filters.search || filters.library || filters.status || filters.owner || filters.tags.length > 0
                ? "Try adjusting your search criteria or filters"
                : "No models are currently available"
              }
            </p>
            {(filters.search || filters.library || filters.status || filters.owner || filters.tags.length > 0) && (
              <Button 
                variant="outline" 
                onClick={() => onFiltersChange({
                  search: '',
                  library: '',
                  status: '',
                  owner: '',
                  tags: []
                })}
              >
                Clear All Filters
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className={cn(
          viewMode === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            : "space-y-4"
        )}>
          {filteredAndSortedModels.map((model) => (
            <div key={model.id} className="relative">
              {/* Selection Checkbox */}
              <div className="absolute top-2 left-2 z-10">
                <Checkbox
                  checked={selectedModels.has(model.id)}
                  onCheckedChange={() => toggleModelSelection(model.id)}
                  className="bg-background border-2"
                />
              </div>
              
              <ModelCard
                model={{
                  ...model,
                  capabilities: model.capabilities || [],
                  metadata: model.metadata || {
                    parameters: 'Unknown',
                    quantization: 'Unknown',
                    memoryRequirement: 'Unknown',
                    contextLength: 0,
                    license: model.license || 'Unknown',
                    tags: model.tags || []
                  }
                }}
                onAction={onAction}
                searchQuery={filters.search}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}