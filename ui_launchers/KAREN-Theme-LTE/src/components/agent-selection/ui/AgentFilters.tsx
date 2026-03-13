"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  type AgentFilters,
  type AgentSortOptions,
  AgentStatus,
  AgentType,
  AgentCapability,
} from '../types';
import { cn } from '@/lib/utils';

// Button variant helper function
const getButtonVariant = (variant: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link") => {
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    link: "text-primary underline-offset-4 hover:underline",
  };
  return variants[variant];
};

// Icon components
const Filter = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
  </svg>
);

const SortAsc = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
  </svg>
);

const SortDesc = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l3-3m-3 3l-3-3" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const Star = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
  </svg>
);

const Zap = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const Clock = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

interface AgentFiltersProps {
  filters: AgentFilters;
  onFiltersChange: (filters: AgentFilters) => void;
  onClear: () => void;
  capabilities: AgentCapability[];
  specializations: string[];
  developers: string[];
  className?: string;
}

export function AgentFilters({
  filters,
  onFiltersChange,
  onClear,
  capabilities,
  specializations,
  developers,
  className,
}: AgentFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [ratingRange, setRatingRange] = useState({
    min: filters.rating?.min || 1,
    max: filters.rating?.max || 5,
  });
  const [responseTimeRange, setResponseTimeRange] = useState({
    min: 0,
    max: filters.performance?.maxResponseTime || 10000,
  });
  const [successRateRange, setSuccessRateRange] = useState({
    min: filters.performance?.minSuccessRate || 0,
    max: 100,
  });

  // Status options
  const statusOptions: { value: AgentStatus; label: string; color: string }[] = [
    { value: 'available', label: 'Available', color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' },
    { value: 'busy', label: 'Busy', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' },
    { value: 'maintenance', label: 'Maintenance', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300' },
    { value: 'offline', label: 'Offline', color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300' },
    { value: 'error', label: 'Error', color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300' },
  ];

  // Type options
  const typeOptions: { value: AgentType; label: string }[] = [
    { value: 'general', label: 'General' },
    { value: 'specialized', label: 'Specialized' },
    { value: 'custom', label: 'Custom' },
    { value: 'system', label: 'System' },
  ];

  // Pricing options
  const pricingOptions: { value: 'free' | 'paid'; label: string }[] = [
    { value: 'free', label: 'Free' },
    { value: 'paid', label: 'Paid' },
  ];

  // Sort field options
  const sortFieldOptions: { value: AgentSortOptions['field']; label: string }[] = [
    { value: 'name', label: 'Name' },
    { value: 'rating', label: 'Rating' },
    { value: 'performance', label: 'Performance' },
    { value: 'createdAt', label: 'Created Date' },
    { value: 'lastUsed', label: 'Last Used' },
    { value: 'popularity', label: 'Popularity' },
  ];

  const handleStatusChange = (status: AgentStatus) => {
    const currentStatuses = filters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status];
    
    onFiltersChange({ ...filters, status: newStatuses });
  };

  const handleTypeChange = (type: AgentType) => {
    const currentTypes = filters.type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    onFiltersChange({ ...filters, type: newTypes });
  };

  const handleCapabilityChange = (capability: AgentCapability) => {
    const currentCapabilities = filters.capabilities || [];
    const newCapabilities = currentCapabilities.includes(capability)
      ? currentCapabilities.filter(c => c !== capability)
      : [...currentCapabilities, capability];
    
    onFiltersChange({ ...filters, capabilities: newCapabilities });
  };

  const handleSpecializationChange = (specialization: string) => {
    const currentSpecializations = filters.specializations || [];
    const newSpecializations = currentSpecializations.includes(specialization)
      ? currentSpecializations.filter(s => s !== specialization)
      : [...currentSpecializations, specialization];
    
    onFiltersChange({ ...filters, specializations: newSpecializations });
  };

  const handleDeveloperChange = (developer: string) => {
    const currentDevelopers = filters.developer || [];
    const newDevelopers = currentDevelopers.includes(developer)
      ? currentDevelopers.filter(d => d !== developer)
      : [...currentDevelopers, developer];
    
    onFiltersChange({ ...filters, developer: newDevelopers });
  };

  const handlePricingChange = (pricing: 'free' | 'paid') => {
    const currentPricing = filters.pricing || [];
    const newPricing = currentPricing.includes(pricing)
      ? currentPricing.filter(p => p !== pricing)
      : [...currentPricing, pricing];
    
    onFiltersChange({ ...filters, pricing: newPricing });
  };

  const handleRatingRangeChange = () => {
    onFiltersChange({
      ...filters,
      rating: {
        min: ratingRange.min,
        max: ratingRange.max,
      },
    });
  };

  const handlePerformanceRangeChange = () => {
    onFiltersChange({
      ...filters,
      performance: {
        minSuccessRate: successRateRange.min,
        maxResponseTime: responseTimeRange.max,
      },
    });
  };

  const hasActiveFilters = () => {
    return (
      (filters.status && filters.status.length > 0) ||
      (filters.type && filters.type.length > 0) ||
      (filters.capabilities && filters.capabilities.length > 0) ||
      (filters.specializations && filters.specializations.length > 0) ||
      (filters.developer && filters.developer.length > 0) ||
      (filters.pricing && filters.pricing.length > 0) ||
      filters.rating ||
      filters.performance ||
      filters.search ||
      !filters.includeDeprecated ||
      !filters.includeBeta
    );
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
            {hasActiveFilters() && (
              <span className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
                Active
              </span>
            )}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                getButtonVariant("outline")
              )}
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
            
            {hasActiveFilters() && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                  getButtonVariant("outline")
                )}
                onClick={onClear}
              >
                <X className="h-4 w-4 mr-1" />
                Clear All
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <Input
              placeholder="Search agents by name, description, capabilities..."
              value={filters.search || ''}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              className="max-w-md"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Status</label>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.status?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handleStatusChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Type</label>
            <div className="flex flex-wrap gap-2">
              {typeOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.type?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handleTypeChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Capabilities Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Capabilities</label>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {capabilities.map((capability) => (
                <button
                  key={capability}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.capabilities?.includes(capability) ? 'default' : 'outline')
                  )}
                  onClick={() => handleCapabilityChange(capability)}
                >
                  {capability.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </button>
              ))}
            </div>
          </div>

          {/* Specializations Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Specializations</label>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {specializations.map((specialization) => (
                <button
                  key={specialization}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.specializations?.includes(specialization) ? 'default' : 'outline')
                  )}
                  onClick={() => handleSpecializationChange(specialization)}
                >
                  {specialization}
                </button>
              ))}
            </div>
          </div>

          {/* Developer Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Developer</label>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {developers.map((developer) => (
                <button
                  key={developer}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.developer?.includes(developer) ? 'default' : 'outline')
                  )}
                  onClick={() => handleDeveloperChange(developer)}
                >
                  {developer}
                </button>
              ))}
            </div>
          </div>

          {/* Pricing Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Pricing</label>
            <div className="flex flex-wrap gap-2">
              {pricingOptions.map((option) => (
                <button
                  key={option.value}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant(filters.pricing?.includes(option.value) ? 'default' : 'outline')
                  )}
                  onClick={() => handlePricingChange(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Rating Range Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">
              <Star className="inline h-4 w-4 mr-1" />
              Rating Range
            </label>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-sm">Min:</label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="0.5"
                  value={ratingRange.min}
                  onChange={(e) => setRatingRange({ ...ratingRange, min: parseFloat(e.target.value) })}
                  className="w-24"
                />
                <span className="text-sm w-8">{ratingRange.min}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm">Max:</label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="0.5"
                  value={ratingRange.max}
                  onChange={(e) => setRatingRange({ ...ratingRange, max: parseFloat(e.target.value) })}
                  className="w-24"
                />
                <span className="text-sm w-8">{ratingRange.max}</span>
              </div>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                  getButtonVariant("outline")
                )}
                onClick={handleRatingRangeChange}
              >
                Apply
              </button>
            </div>
          </div>

          {/* Performance Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">
              <Zap className="inline h-4 w-4 mr-1" />
              Performance Requirements
            </label>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm">Max Response Time:</label>
                  <input
                    type="range"
                    min="100"
                    max="10000"
                    step="100"
                    value={responseTimeRange.max}
                    onChange={(e) => setResponseTimeRange({ ...responseTimeRange, max: parseInt(e.target.value) })}
                    className="w-24"
                  />
                  <span className="text-sm w-16">{responseTimeRange.max}ms</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm">Min Success Rate:</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={successRateRange.min}
                    onChange={(e) => setSuccessRateRange({ ...successRateRange, min: parseInt(e.target.value) })}
                    className="w-24"
                  />
                  <span className="text-sm w-12">{successRateRange.min}%</span>
                </div>
              </div>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                  getButtonVariant("outline")
                )}
                onClick={handlePerformanceRangeChange}
              >
                Apply Performance Filters
              </button>
            </div>
          </div>

          {/* Additional Options */}
          <div>
            <label className="block text-sm font-medium mb-2">Additional Options</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.includeDeprecated || false}
                  onChange={(e) => onFiltersChange({ ...filters, includeDeprecated: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">Include deprecated agents</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.includeBeta !== false}
                  onChange={(e) => onFiltersChange({ ...filters, includeBeta: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">Include beta agents</span>
              </label>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Sort options component
interface AgentSortOptionsProps {
  sortOptions: AgentSortOptions;
  onSortChange: (sort: AgentSortOptions) => void;
  className?: string;
}

export function AgentSortOptions({
  sortOptions,
  onSortChange,
  className,
}: AgentSortOptionsProps) {
  const sortFieldOptions: { value: AgentSortOptions['field']; label: string }[] = [
    { value: 'name', label: 'Name' },
    { value: 'rating', label: 'Rating' },
    { value: 'performance', label: 'Performance' },
    { value: 'createdAt', label: 'Created Date' },
    { value: 'lastUsed', label: 'Last Used' },
    { value: 'popularity', label: 'Popularity' },
  ];

  const handleFieldChange = (field: AgentSortOptions['field']) => {
    onSortChange({ ...sortOptions, field });
  };

  const handleDirectionToggle = () => {
    onSortChange({
      ...sortOptions,
      direction: sortOptions.direction === 'asc' ? 'desc' : 'asc',
    });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
            getButtonVariant("outline")
          )}>
            Sort by: {sortFieldOptions.find(o => o.value === sortOptions.field)?.label}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          {sortFieldOptions.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onClick={() => handleFieldChange(option.value)}
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-1",
          getButtonVariant("outline")
        )}
        onClick={handleDirectionToggle}
      >
        {sortOptions.direction === 'asc' ? (
          <SortAsc className="h-4 w-4" />
        ) : (
          <SortDesc className="h-4 w-4" />
        )}
        {sortOptions.direction === 'asc' ? 'Ascending' : 'Descending'}
      </button>
    </div>
  );
}

// Quick filter buttons
interface QuickFiltersProps {
  onFiltersChange: (filters: AgentFilters) => void;
  className?: string;
}

export function QuickFilters({ onFiltersChange, className }: QuickFiltersProps) {
  const quickFilters = [
    {
      name: 'Available Agents',
      filters: { status: ['available'] },
      icon: <Zap className="h-4 w-4" />,
    },
    {
      name: 'Top Rated',
      filters: { 
        rating: { min: 4, max: 5 },
        includeBeta: false,
        includeDeprecated: false,
      },
      icon: <Star className="h-4 w-4" />,
    },
    {
      name: 'Recently Used',
      filters: { 
        sortOptions: { field: 'lastUsed', direction: 'desc' } as AgentSortOptions,
      },
      icon: <Clock className="h-4 w-4" />,
    },
    {
      name: 'Free Agents',
      filters: { 
        pricing: ['free'],
        includeBeta: false,
        includeDeprecated: false,
      },
      icon: (
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      ),
    },
  ];

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {quickFilters.map((filter) => (
        <button
          key={filter.name}
          className={cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
            getButtonVariant("outline")
          )}
          onClick={() => onFiltersChange(filter.filters as AgentFilters)}
        >
          {filter.icon}
          {filter.name}
        </button>
      ))}
    </div>
  );
}