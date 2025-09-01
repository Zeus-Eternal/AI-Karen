"use client";

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { 
  Search, 
  Grid, 
  List,
  Download,
  Trash2,
  Pin,
  PinOff,
  MoreHorizontal,
  Package,
  HardDrive,
  Star,
  User,
  Calendar,
  Clock
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import ModelCard from './ModelCard';

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
  capabilities: string[];
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
  pinned?: boolean;
  install_path?: string;
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

interface ModelGridProps {
  models: ModelInfo[];
  onAction: (modelId: string, action: string) => Promise<void>;
  searchQuery?: string;
}

type ViewMode = 'grid' | 'list';
type SortOption = 'name' | 'size' | 'lastUsed' | 'downloadDate';
type SortDirection = 'asc' | 'desc';

/**
 * Model grid component with bulk selection using existing table selection patterns
 * Provides grid/list view modes and bulk actions for model management
 */
export default function ModelGrid({ 
  models, 
  onAction, 
  searchQuery = '' 
}: ModelGridProps) {
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [sortBy, setSortBy] = useState<SortOption>('lastUsed');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [localSearchQuery, setLocalSearchQuery] = useState('');
  const [bulkActionLoading, setBulkActionLoading] = useState<string | null>(null);
  
  const { toast } = useToast();

  // Use local search if provided, otherwise use prop
  const effectiveSearchQuery = localSearchQuery || searchQuery;

  // Filter and sort models
  const filteredAndSortedModels = useMemo(() => {
    let filtered = models;

    // Apply search filter
    if (effectiveSearchQuery) {
      const searchLower = effectiveSearchQuery.toLowerCase();
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(searchLower) ||
        model.owner.toLowerCase().includes(searchLower) ||
        model.description?.toLowerCase().includes(searchLower) ||
        model.tags?.some(tag => tag.toLowerCase().includes(searchLower)) ||
        model.capabilities?.some(cap => cap.toLowerCase().includes(searchLower))
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
        case 'size':
          aValue = a.diskUsage || a.total_size || 0;
          bValue = b.diskUsage || b.total_size || 0;
          break;
        case 'lastUsed':
          aValue = a.lastUsed || 0;
          bValue = b.lastUsed || 0;
          break;
        case 'downloadDate':
          aValue = a.downloadDate || 0;
          bValue = b.downloadDate || 0;
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
  }, [models, effectiveSearchQuery, sortBy, sortDirection]);

  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatRelativeTime = (timestamp?: number): string => {
    if (!timestamp) return 'Never';
    const now = Date.now();
    const diff = now - (timestamp * 1000);
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
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

  const handleBulkAction = async (action: string) => {
    const selectedArray = Array.from(selectedModels);
    if (selectedArray.length === 0) return;

    setBulkActionLoading(action);
    
    try {
      // Execute actions in parallel for better performance
      await Promise.all(
        selectedArray.map(modelId => onAction(modelId, action))
      );
      
      toast({
        title: `Bulk ${action} completed`,
        description: `Successfully ${action}ed ${selectedArray.length} model${selectedArray.length !== 1 ? 's' : ''}`
      });
      
      setSelectedModels(new Set());
    } catch (error: any) {
      console.error(`Bulk ${action} failed:`, error);
      toast({
        title: `Bulk ${action} failed`,
        description: error.message || `Failed to ${action} selected models`,
        variant: 'destructive'
      });
    } finally {
      setBulkActionLoading(null);
    }
  };

  const handleTogglePin = async (modelId: string, currentlyPinned: boolean) => {
    try {
      await onAction(modelId, currentlyPinned ? 'unpin' : 'pin');
      toast({
        title: currentlyPinned ? 'Model unpinned' : 'Model pinned',
        description: `${models.find(m => m.id === modelId)?.name} has been ${currentlyPinned ? 'unpinned' : 'pinned'}`
      });
    } catch (error: any) {
      console.error('Failed to toggle pin:', error);
      toast({
        title: 'Failed to toggle pin',
        description: error.message || 'Failed to update pin status',
        variant: 'destructive'
      });
    }
  };

  if (models.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No Local Models</h3>
          <p className="text-muted-foreground">
            You don't have any models installed locally yet. 
            Browse available models to download some.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search local models..."
            value={localSearchQuery}
            onChange={(e) => setLocalSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="px-3 py-2 text-sm border rounded-md bg-background"
          >
            <option value="lastUsed">Last Used</option>
            <option value="downloadDate">Download Date</option>
            <option value="name">Name</option>
            <option value="size">Size</option>
          </select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
          >
            {sortDirection === 'asc' ? '↑' : '↓'}
          </Button>
          
          <Separator orientation="vertical" className="h-6" />
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? <List className="h-4 w-4" /> : <Grid className="h-4 w-4" />}
          </Button>
        </div>
      </div>

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
                  variant="outline"
                  onClick={() => handleBulkAction('pin')}
                  disabled={bulkActionLoading === 'pin'}
                  className="gap-1"
                >
                  <Pin className="h-3 w-3" />
                  Pin Selected
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkAction('unpin')}
                  disabled={bulkActionLoading === 'unpin'}
                  className="gap-1"
                >
                  <PinOff className="h-3 w-3" />
                  Unpin Selected
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  onClick={() => handleBulkAction('delete')}
                  disabled={bulkActionLoading === 'delete'}
                  className="gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  Delete Selected
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Showing {filteredAndSortedModels.length} of {models.length} local models
        </span>
        {effectiveSearchQuery && (
          <span>
            Search results for "{effectiveSearchQuery}"
          </span>
        )}
      </div>

      {/* Models Display */}
      {filteredAndSortedModels.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No models found</h3>
            <p className="text-muted-foreground mb-4">
              No models match your search criteria
            </p>
            <Button 
              variant="outline" 
              onClick={() => setLocalSearchQuery('')}
            >
              Clear Search
            </Button>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
              
              {/* Pin Toggle */}
              <div className="absolute top-2 right-2 z-10">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleTogglePin(model.id, model.pinned || false)}
                  className="h-8 w-8 p-0 bg-background/80 hover:bg-background"
                >
                  {model.pinned ? (
                    <Pin className="h-3 w-3 text-orange-500" />
                  ) : (
                    <PinOff className="h-3 w-3 text-muted-foreground" />
                  )}
                </Button>
              </div>
              
              <ModelCard
                model={model}
                onAction={onAction}
                searchQuery={effectiveSearchQuery}
              />
            </div>
          ))}
        </div>
      ) : (
        /* List View */
        <div className="space-y-2">
          {filteredAndSortedModels.map((model) => (
            <Card key={model.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="py-4">
                <div className="flex items-center gap-4">
                  {/* Selection Checkbox */}
                  <Checkbox
                    checked={selectedModels.has(model.id)}
                    onCheckedChange={() => toggleModelSelection(model.id)}
                  />
                  
                  {/* Model Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <h3 className="font-medium truncate">{model.name}</h3>
                      {model.pinned && (
                        <Badge variant="secondary" className="text-xs">
                          <Pin className="h-2 w-2 mr-1" />
                          Pinned
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {model.owner}
                      </div>
                      <div className="flex items-center gap-1">
                        <HardDrive className="h-3 w-3" />
                        {formatSize(model.diskUsage || model.total_size)}
                      </div>
                      {model.lastUsed && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatRelativeTime(model.lastUsed)}
                        </div>
                      )}
                      {model.downloadDate && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Downloaded {formatRelativeTime(model.downloadDate)}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTogglePin(model.id, model.pinned || false)}
                      className="gap-1"
                    >
                      {model.pinned ? (
                        <>
                          <PinOff className="h-3 w-3" />
                          Unpin
                        </>
                      ) : (
                        <>
                          <Pin className="h-3 w-3" />
                          Pin
                        </>
                      )}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => onAction(model.id, 'delete')}
                      className="gap-1"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}