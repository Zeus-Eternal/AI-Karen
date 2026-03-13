"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import {
  MemoryFilters as MemoryFiltersType,
  MemoryFiltersComponentProps,
  MemoryType,
  MemoryStatus,
  MemoryPriority,
  MemorySource
} from '../types';

// Quick filter presets
const quickFilterPresets = [
  {
    name: 'Active Memories',
    filters: { status: ['active' as MemoryStatus] },
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    name: 'Archived',
    filters: { status: ['archived' as MemoryStatus] },
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
      </svg>
    ),
  },
  {
    name: 'High Priority',
    filters: { priority: ['critical' as MemoryPriority, 'high' as MemoryPriority] },
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
  },
  {
    name: 'Recent',
    filters: {
      dateRange: {
        start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        end: new Date()
      }
    },
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    name: 'Expired',
    filters: { isExpired: true },
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
  },
];

export function MemoryFilters({
  filters,
  onFiltersChange,
  onClear,
  folders = [],
  collections = [],
  tags = [],
  categories = [],
  className
}: MemoryFiltersComponentProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState(filters.search || '');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleTypeFilterChange = (type: MemoryType) => {
    const currentTypes = filters.type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    onFiltersChange({ ...filters, type: newTypes });
  };

  const handleStatusFilterChange = (status: MemoryStatus) => {
    const currentStatuses = filters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status];
    
    onFiltersChange({ ...filters, status: newStatuses });
  };

  const handlePriorityFilterChange = (priority: MemoryPriority) => {
    const currentPriorities = filters.priority || [];
    const newPriorities = currentPriorities.includes(priority)
      ? currentPriorities.filter(p => p !== priority)
      : [...currentPriorities, priority];
    
    onFiltersChange({ ...filters, priority: newPriorities });
  };

  const handleSourceFilterChange = (source: MemorySource) => {
    const currentSources = filters.source || [];
    const newSources = currentSources.includes(source)
      ? currentSources.filter(s => s !== source)
      : [...currentSources, source];
    
    onFiltersChange({ ...filters, source: newSources });
  };

  const handleCategoryFilterChange = (category: string) => {
    const currentCategories = filters.category || [];
    const newCategories = currentCategories.includes(category)
      ? currentCategories.filter(c => c !== category)
      : [...currentCategories, category];
    
    onFiltersChange({ ...filters, category: newCategories });
  };

  const handleTagFilterChange = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag];
    
    onFiltersChange({ ...filters, tags: newTags });
  };

  const handleFolderFilterChange = (folder: string) => {
    const currentFolders = filters.folder || [];
    const newFolders = currentFolders.includes(folder)
      ? currentFolders.filter(f => f !== folder)
      : [...currentFolders, folder];
    
    onFiltersChange({ ...filters, folder: newFolders });
  };

  const handleCollectionFilterChange = (collection: string) => {
    const currentCollections = filters.collection || [];
    const newCollections = currentCollections.includes(collection)
      ? currentCollections.filter(c => c !== collection)
      : [...currentCollections, collection];
    
    onFiltersChange({ ...filters, collection: newCollections });
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    onFiltersChange({ ...filters, search: value });
  };

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) return;
    
    const currentRange = filters.dateRange || { start: new Date(), end: new Date() };
    const newRange = {
      ...currentRange,
      [field]: date
    };
    
    onFiltersChange({ ...filters, dateRange: newRange });
  };

  const handleConfidenceChange = (field: 'min' | 'max', value: string) => {
    const confidence = parseFloat(value);
    if (isNaN(confidence)) return;
    
    onFiltersChange({ 
      ...filters, 
      [field === 'min' ? 'minConfidence' : 'maxConfidence']: confidence 
    });
  };

  const handleImportanceChange = (field: 'min' | 'max', value: string) => {
    const importance = parseFloat(value);
    if (isNaN(importance)) return;
    
    onFiltersChange({ 
      ...filters, 
      [field === 'min' ? 'minImportance' : 'maxImportance']: importance 
    });
  };

  const applyQuickFilter = (presetFilters: Partial<MemoryFiltersType>) => {
    onFiltersChange({ ...filters, ...presetFilters });
  };

  const hasActiveFilters = !!(
    (filters.type && filters.type.length > 0) ||
    (filters.status && filters.status.length > 0) ||
    (filters.priority && filters.priority.length > 0) ||
    (filters.source && filters.source.length > 0) ||
    (filters.category && filters.category.length > 0) ||
    (filters.tags && filters.tags.length > 0) ||
    (filters.folder && filters.folder.length > 0) ||
    (filters.collection && filters.collection.length > 0) ||
    filters.dateRange ||
    filters.search ||
    filters.minConfidence !== undefined ||
    filters.maxConfidence !== undefined ||
    filters.minImportance !== undefined ||
    filters.maxImportance !== undefined
  );

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Memory Filters</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 01-.707.293V4z" />
              </svg>
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={onClear}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Clear
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Quick Filters */}
        <div>
          <h3 className="font-medium mb-3">Quick Filters</h3>
          <div className="flex flex-wrap gap-2">
            {quickFilterPresets.map((preset, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => applyQuickFilter(preset.filters)}
                className="flex items-center gap-2"
              >
                {preset.icon}
                {preset.name}
              </Button>
            ))}
          </div>
        </div>

        {/* Search */}
        <div>
          <h3 className="font-medium mb-3">Search</h3>
          <div className="space-y-3">
            <Input
              placeholder="Search memories..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full"
            />
          </div>
        </div>

        {isExpanded && (
          <>
            {/* Type Filters */}
            <div>
              <h3 className="font-medium mb-3">Type</h3>
              <div className="flex flex-wrap gap-2">
                {(['conversation', 'case', 'unified', 'fact', 'preference', 'context'] as MemoryType[]).map(type => (
                  <Badge
                    key={type}
                    variant={filters.type?.includes(type) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => handleTypeFilterChange(type)}
                  >
                    {type}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Status Filters */}
            <div>
              <h3 className="font-medium mb-3">Status</h3>
              <div className="flex flex-wrap gap-2">
                {(['active', 'archived', 'deleted', 'processing'] as MemoryStatus[]).map(status => (
                  <Badge
                    key={status}
                    variant={filters.status?.includes(status) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => handleStatusFilterChange(status)}
                  >
                    {status}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Priority Filters */}
            <div>
              <h3 className="font-medium mb-3">Priority</h3>
              <div className="flex flex-wrap gap-2">
                {(['low', 'medium', 'high', 'critical'] as MemoryPriority[]).map(priority => (
                  <Badge
                    key={priority}
                    variant={filters.priority?.includes(priority) ? "default" : "secondary"}
                    className="cursor-pointer"
                    onClick={() => handlePriorityFilterChange(priority)}
                  >
                    {priority}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Source Filters */}
            <div>
              <h3 className="font-medium mb-3">Source</h3>
              <div className="flex flex-wrap gap-2">
                {(['user-input', 'conversation', 'document', 'api', 'system', 'import'] as MemorySource[]).map(source => (
                  <Badge
                    key={source}
                    variant={filters.source?.includes(source) ? "default" : "secondary"}
                    className="cursor-pointer"
                    onClick={() => handleSourceFilterChange(source)}
                  >
                    {source}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Category Filters */}
            {categories.length > 0 && (
              <div>
                <h3 className="font-medium mb-3">Categories</h3>
                <div className="flex flex-wrap gap-2">
                  {categories.map(category => (
                    <Badge
                      key={category}
                      variant={filters.category?.includes(category) ? "default" : "secondary"}
                      className="cursor-pointer"
                      onClick={() => handleCategoryFilterChange(category)}
                    >
                      {category}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Tag Filters */}
            {tags.length > 0 && (
              <div>
                <h3 className="font-medium mb-3">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {tags.slice(0, 10).map(tag => (
                    <Badge
                      key={tag}
                      variant={filters.tags?.includes(tag) ? "default" : "secondary"}
                      className="cursor-pointer"
                      onClick={() => handleTagFilterChange(tag)}
                    >
                      {tag}
                    </Badge>
                  ))}
                  {tags.length > 10 && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Badge variant="secondary" className="cursor-pointer">
                          +{tags.length - 10} more
                        </Badge>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        {tags.slice(10).map(tag => (
                          <DropdownMenuItem
                            key={tag}
                            onClick={() => handleTagFilterChange(tag)}
                          >
                            {tag}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
            )}

            {/* Folder Filters */}
            {folders.length > 0 && (
              <div>
                <h3 className="font-medium mb-3">Folders</h3>
                <div className="flex flex-wrap gap-2">
                  {folders.map(folder => (
                    <Badge
                      key={folder}
                      variant={filters.folder?.includes(folder) ? "default" : "secondary"}
                      className="cursor-pointer"
                      onClick={() => handleFolderFilterChange(folder)}
                    >
                      <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                      {folder}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Collection Filters */}
            {collections.length > 0 && (
              <div>
                <h3 className="font-medium mb-3">Collections</h3>
                <div className="flex flex-wrap gap-2">
                  {collections.map(collection => (
                    <Badge
                      key={collection}
                      variant={filters.collection?.includes(collection) ? "default" : "secondary"}
                      className="cursor-pointer"
                      onClick={() => handleCollectionFilterChange(collection)}
                    >
                      <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      {collection}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Date Range */}
            <div>
              <h3 className="font-medium mb-3">Date Range</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">From</label>
                  <Input
                    type="date"
                    value={filters.dateRange?.start ? filters.dateRange.start.toISOString().split('T')[0] : ''}
                    onChange={(e) => handleDateRangeChange('start', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">To</label>
                  <Input
                    type="date"
                    value={filters.dateRange?.end ? filters.dateRange.end.toISOString().split('T')[0] : ''}
                    onChange={(e) => handleDateRangeChange('end', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Confidence Range */}
            <div>
              <h3 className="font-medium mb-3">Confidence Range</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Min</label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    placeholder="0.0"
                    value={filters.minConfidence?.toString() || ''}
                    onChange={(e) => handleConfidenceChange('min', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max</label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    placeholder="1.0"
                    value={filters.maxConfidence?.toString() || ''}
                    onChange={(e) => handleConfidenceChange('max', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Importance Range */}
            <div>
              <h3 className="font-medium mb-3">Importance Range</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Min</label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    placeholder="0.0"
                    value={filters.minImportance?.toString() || ''}
                    onChange={(e) => handleImportanceChange('min', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max</label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    placeholder="1.0"
                    value={filters.maxImportance?.toString() || ''}
                    onChange={(e) => handleImportanceChange('max', e.target.value)}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default MemoryFilters;