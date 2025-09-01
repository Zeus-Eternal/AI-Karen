"use client";

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { X, Filter, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModelFiltersType {
  search: string;
  library: string;
  status: string;
  owner: string;
  tags: string[];
}

interface FilterOptions {
  libraries: string[];
  owners: string[];
  allTags: string[];
  statuses: string[];
}

interface ModelFiltersProps {
  filters: ModelFiltersType;
  onFiltersChange: (filters: ModelFiltersType) => void;
  filterOptions: FilterOptions;
  className?: string;
}

/**
 * Advanced model filters component
 * Provides comprehensive filtering options for model browsing
 */
export default function ModelFilters({
  filters,
  onFiltersChange,
  filterOptions,
  className
}: ModelFiltersProps) {
  const updateFilter = (key: keyof ModelFiltersType, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  const toggleTag = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag];
    
    updateFilter('tags', newTags);
  };

  const clearAllFilters = () => {
    onFiltersChange({
      search: '',
      library: '',
      status: '',
      owner: '',
      tags: []
    });
  };

  const hasActiveFilters = () => {
    return filters.library || 
           filters.status || 
           filters.owner || 
           (filters.tags && filters.tags.length > 0);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.library) count++;
    if (filters.status) count++;
    if (filters.owner) count++;
    if (filters.tags && filters.tags.length > 0) count += filters.tags.length;
    return count;
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Filter Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">Filters</span>
          {hasActiveFilters() && (
            <Badge variant="secondary" className="text-xs">
              {getActiveFilterCount()} active
            </Badge>
          )}
        </div>
        {hasActiveFilters() && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="gap-1 text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3 w-3" />
            Clear All
          </Button>
        )}
      </div>

      {/* Filter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Library Filter */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Library</Label>
          <Select
            value={filters.library}
            onValueChange={(value) => updateFilter('library', value === 'all' ? '' : value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All libraries" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All libraries</SelectItem>
              {filterOptions.libraries.map(library => (
                <SelectItem key={library} value={library}>
                  {library}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Status Filter */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Status</Label>
          <Select
            value={filters.status}
            onValueChange={(value) => updateFilter('status', value === 'all' ? '' : value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {filterOptions.statuses.map(status => (
                <SelectItem key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Owner Filter */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Owner</Label>
          <Select
            value={filters.owner}
            onValueChange={(value) => updateFilter('owner', value === 'all' ? '' : value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All owners" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All owners</SelectItem>
              {filterOptions.owners.slice(0, 20).map(owner => (
                <SelectItem key={owner} value={owner}>
                  {owner}
                </SelectItem>
              ))}
              {filterOptions.owners.length > 20 && (
                <SelectItem value="" disabled>
                  ... and {filterOptions.owners.length - 20} more
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Quick Filters */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Quick Filters</Label>
          <div className="flex flex-wrap gap-1">
            <Button
              variant={filters.status === 'local' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', filters.status === 'local' ? '' : 'local')}
              className="text-xs"
            >
              Local Only
            </Button>
            <Button
              variant={filters.status === 'available' ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateFilter('status', filters.status === 'available' ? '' : 'available')}
              className="text-xs"
            >
              Available
            </Button>
          </div>
        </div>
      </div>

      {/* Tags Filter */}
      {filterOptions.allTags.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm font-medium">
            Tags
            {filters.tags && filters.tags.length > 0 && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({filters.tags.length} selected)
              </span>
            )}
          </Label>
          <div className="flex flex-wrap gap-1 max-h-32 overflow-y-auto">
            {filterOptions.allTags.slice(0, 50).map(tag => {
              const isSelected = filters.tags?.includes(tag) || false;
              return (
                <Button
                  key={tag}
                  variant={isSelected ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => toggleTag(tag)}
                  className={cn(
                    "text-xs h-6 px-2",
                    isSelected && "bg-primary text-primary-foreground"
                  )}
                >
                  {tag}
                  {isSelected && (
                    <X className="h-2 w-2 ml-1" />
                  )}
                </Button>
              );
            })}
            {filterOptions.allTags.length > 50 && (
              <span className="text-xs text-muted-foreground px-2 py-1">
                ... and {filterOptions.allTags.length - 50} more tags
              </span>
            )}
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {hasActiveFilters() && (
        <>
          <Separator />
          <div className="space-y-2">
            <Label className="text-sm font-medium">Active Filters</Label>
            <div className="flex flex-wrap gap-1">
              {filters.library && (
                <Badge variant="secondary" className="gap-1">
                  Library: {filters.library}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => updateFilter('library', '')}
                    className="h-3 w-3 p-0 hover:bg-transparent"
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              
              {filters.status && (
                <Badge variant="secondary" className="gap-1">
                  Status: {filters.status}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => updateFilter('status', '')}
                    className="h-3 w-3 p-0 hover:bg-transparent"
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              
              {filters.owner && (
                <Badge variant="secondary" className="gap-1">
                  Owner: {filters.owner}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => updateFilter('owner', '')}
                    className="h-3 w-3 p-0 hover:bg-transparent"
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              )}
              
              {filters.tags?.map(tag => (
                <Badge key={tag} variant="secondary" className="gap-1">
                  Tag: {tag}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleTag(tag)}
                    className="h-3 w-3 p-0 hover:bg-transparent"
                  >
                    <X className="h-2 w-2" />
                  </Button>
                </Badge>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}