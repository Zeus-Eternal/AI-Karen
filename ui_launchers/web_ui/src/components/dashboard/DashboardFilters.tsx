import React, { useState } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { useEffect } from 'react';
import { Filter, X, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import type { DashboardFilter } from '@/types/dashboard';
'use client';









  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';




interface DashboardFiltersProps {
  filters: DashboardFilter[];
  onFiltersChange: (filters: DashboardFilter[]) => void;
  availableFilterTypes?: FilterTypeConfig[];
  className?: string;
}

interface FilterTypeConfig {
  type: DashboardFilter['type'];
  label: string;
  description: string;
  valueType: 'text' | 'select' | 'multiselect' | 'number' | 'date';
  options?: Array<{ value: string; label: string }>;
}

const defaultFilterTypes: FilterTypeConfig[] = [
  {
    type: 'category',
    label: 'Category',
    description: 'Filter by data category',
    valueType: 'select',
    options: [
      { value: 'system', label: 'System' },
      { value: 'performance', label: 'Performance' },
      { value: 'security', label: 'Security' },
      { value: 'user', label: 'User Activity' },
    ]
  },
  {
    type: 'status',
    label: 'Status',
    description: 'Filter by status',
    valueType: 'select',
    options: [
      { value: 'healthy', label: 'Healthy' },
      { value: 'warning', label: 'Warning' },
      { value: 'critical', label: 'Critical' },
      { value: 'unknown', label: 'Unknown' },
    ]
  },
  {
    type: 'custom',
    label: 'Custom Filter',
    description: 'Create a custom filter',
    valueType: 'text'
  }
];

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  filters,
  onFiltersChange,
  availableFilterTypes = defaultFilterTypes,
  className
}) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newFilter, setNewFilter] = useState<Partial<DashboardFilter>>({
    type: 'category',
    enabled: true
  });

  const handleAddFilter = () => {
    if (!newFilter.name || !newFilter.type) return;

    const filter: DashboardFilter = {
      id: `filter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: newFilter.name,
      type: newFilter.type,
      value: newFilter.value || '',
      enabled: newFilter.enabled ?? true
    };

    onFiltersChange([...filters, filter]);
    setNewFilter({ type: 'category', enabled: true });
    setIsAddDialogOpen(false);
  };

  const handleUpdateFilter = (id: string, updates: Partial<DashboardFilter>) => {
    onFiltersChange(
      filters.map(filter =>
        filter.id === id ? { ...filter, ...updates } : filter
      )
    );
  };

  const handleRemoveFilter = (id: string) => {
    onFiltersChange(filters.filter(filter => filter.id !== id));
  };

  const handleToggleFilter = (id: string) => {
    handleUpdateFilter(id, { 
      enabled: !filters.find(f => f.id === id)?.enabled 
    });
  };

  const getFilterTypeConfig = (type: DashboardFilter['type']) => {
    return availableFilterTypes.find(config => config.type === type);
  };

  const renderFilterValue = (filter: DashboardFilter) => {
    const config = getFilterTypeConfig(filter.type);
    
    if (config?.valueType === 'select' && config.options) {
      const option = config.options.find(opt => opt.value === filter.value);
      return option?.label || filter.value;
    }
    
    return filter.value?.toString() || '';
  };

  const renderFilterInput = (
    value: any,
    onChange: (value: any) => void,
    config: FilterTypeConfig
  ) => {
    switch (config.valueType) {
      case 'select':

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

        return (
    <ErrorBoundary fallback={<div>Something went wrong in DashboardFilters</div>}>
      <select value={value?.toString()} onValueChange={onChange} aria-label="Select option">
            <selectTrigger aria-label="Select option">
              <selectValue placeholder="Select value..." />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              {config.options?.map(option => (
                <selectItem key={option.value} value={option.value} aria-label="Select option">
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) = aria-label="Input"> onChange(parseFloat(e.target.value) || 0)}
            placeholder="Enter number..."
          />
        );
      
      case 'date':
        return (
          <input
            type="date"
            value={value || ''}
            onChange={(e) = aria-label="Input"> onChange(e.target.value)}
          />
        );
      
      default:
        return (
          <input
            value={value || ''}
            onChange={(e) = aria-label="Input"> onChange(e.target.value)}
            placeholder="Enter value..."
          />
        );
    }
  };

  const activeFilters = filters.filter(f => f.enabled);
  const inactiveFilters = filters.filter(f => !f.enabled);

  return (
    <div className={cn('space-y-3', className)}>
      {/* Filter Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
          <span className="text-sm font-medium md:text-base lg:text-lg">Filters</span>
          {activeFilters.length > 0 && (
            <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
              {activeFilters.length} active
            </Badge>
          )}
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <button variant="outline" size="sm" aria-label="Button">
              <Plus className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
              Add Filter
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Add Filter</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="filter-name">Filter Name</Label>
                <input
                  id="filter-name"
                  value={newFilter.name || ''}
                  onChange={(e) = aria-label="Input"> setNewFilter({ ...newFilter, name: e.target.value })}
                  placeholder="Enter filter name..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="filter-type">Filter Type</Label>
                <select
                  value={newFilter.type}
                  onValueChange={(type: DashboardFilter['type']) = aria-label="Select option"> 
                    setNewFilter({ ...newFilter, type, value: '' })
                  }
                >
                  <selectTrigger aria-label="Select option">
                    <selectValue />
                  </SelectTrigger>
                  <selectContent aria-label="Select option">
                    {availableFilterTypes.map(config => (
                      <selectItem key={config.type} value={config.type} aria-label="Select option">
                        <div>
                          <div className="font-medium">{config.label}</div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            {config.description}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {newFilter.type && (
                <div className="space-y-2">
                  <Label htmlFor="filter-value">Filter Value</Label>
                  {renderFilterInput(
                    newFilter.value,
                    (value) => setNewFilter({ ...newFilter, value }),
                    getFilterTypeConfig(newFilter.type)!
                  )}
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Switch
                  id="filter-enabled"
                  checked={newFilter.enabled}
                  onCheckedChange={(enabled) => setNewFilter({ ...newFilter, enabled })}
                />
                <Label htmlFor="filter-enabled">Enable filter</Label>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  variant="outline"
                  onClick={() = aria-label="Button"> setIsAddDialogOpen(false)}
                >
                  Cancel
                </Button>
                <button
                  onClick={handleAddFilter}
                  disabled={!newFilter.name || !newFilter.type}
                 aria-label="Button">
                  Add Filter
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Filters */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {activeFilters.map(filter => (
            <Badge
              key={filter.id}
              variant="default"
              className="flex items-center gap-1 px-2 py-1"
            >
              <span className="text-xs sm:text-sm md:text-base">
                {filter.name}: {renderFilterValue(filter)}
              </span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-transparent sm:w-auto md:w-full"
                   aria-label="Button">
                    <Search className="h-3 w-3 sm:w-auto md:w-full" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => handleToggleFilter(filter.id)}
                  >
                    Disable Filter
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => handleRemoveFilter(filter.id)}
                    className="text-destructive"
                  >
                    Remove Filter
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </Badge>
          ))}
        </div>
      )}

      {/* Inactive Filters */}
      {inactiveFilters.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Inactive Filters</div>
          <div className="flex flex-wrap gap-2">
            {inactiveFilters.map(filter => (
              <Badge
                key={filter.id}
                variant="outline"
                className="flex items-center gap-1 px-2 py-1 opacity-60"
              >
                <span className="text-xs sm:text-sm md:text-base">
                  {filter.name}: {renderFilterValue(filter)}
                </span>
                <button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0 hover:bg-transparent sm:w-auto md:w-full"
                  onClick={() = aria-label="Button"> handleToggleFilter(filter.id)}
                >
                  <Plus className="h-3 w-3 sm:w-auto md:w-full" />
                </Button>
                <button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0 hover:bg-transparent sm:w-auto md:w-full"
                  onClick={() = aria-label="Button"> handleRemoveFilter(filter.id)}
                >
                  <X className="h-3 w-3 sm:w-auto md:w-full" />
                </Button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* No Filters State */}
      {filters.length === 0 && (
        <div className="text-center py-4 text-sm text-muted-foreground md:text-base lg:text-lg">
          No filters applied. Add filters to refine your dashboard data.
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
};

export default DashboardFilters;