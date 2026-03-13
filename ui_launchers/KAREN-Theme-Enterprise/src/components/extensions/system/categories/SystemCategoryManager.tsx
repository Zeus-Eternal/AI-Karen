import React, { useState, useEffect, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import SystemCategoryCard from './SystemCategoryCard';
import { SystemCategory, SystemCategoryFilter } from './types';
import { Search, Plus, Settings } from 'lucide-react';

interface SystemCategoryManagerProps {
  categories?: SystemCategory[];
  onCategoryToggle?: (categoryId: string) => void;
  onCategoryEdit?: (categoryId: string) => void;
  onCategoryCreate?: () => void;
  loading?: boolean;
  className?: string;
}

export default function SystemCategoryManager({
  categories = [],
  onCategoryToggle,
  onCategoryEdit,
  onCategoryCreate,
  loading = false,
  className = ''
}: SystemCategoryManagerProps) {
  const [filter, setFilter] = useState<SystemCategoryFilter>({
    search: '',
    isActive: undefined,
    sortBy: 'name',
    sortOrder: 'asc'
  });

  const filteredCategories = useMemo(() => {
    let filtered = [...categories];

    // Apply search filter
    if (filter.search) {
      filtered = filtered.filter(category =>
        category.name.toLowerCase().includes(filter.search!.toLowerCase()) ||
        category.description.toLowerCase().includes(filter.search!.toLowerCase())
      );
    }

    // Apply active filter
    if (filter.isActive !== undefined) {
      filtered = filtered.filter(category => category.isActive === filter.isActive);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (filter.sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'extensionCount':
          aValue = a.extensionCount;
          bValue = b.extensionCount;
          break;
        case 'lastUpdated':
          aValue = a.lastUpdated.getTime();
          bValue = b.lastUpdated.getTime();
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }

      if (filter.sortOrder === 'desc') {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    });

    return filtered;
  }, [categories, filter]);

  const stats = useMemo(() => {
    const total = categories.length;
    const active = categories.filter(c => c.isActive).length;
    const totalExtensions = categories.reduce((sum, c) => sum + c.extensionCount, 0);
    
    return { total, active, inactive: total - active, totalExtensions };
  }, [categories]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">System Categories</h2>
          <p className="text-muted-foreground">
            Manage system extension categories and their configurations
          </p>
        </div>
        {onCategoryCreate && (
          <Button onClick={onCategoryCreate}>
            <Plus className="h-4 w-4 mr-2" />
            New Category
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total Categories</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Badge variant="default" className="h-5 w-5 rounded-full p-0" />
              <div>
                <p className="text-sm font-medium">Active</p>
                <p className="text-2xl font-bold">{stats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="h-5 w-5 rounded-full p-0" />
              <div>
                <p className="text-sm font-medium">Inactive</p>
                <p className="text-2xl font-bold">{stats.inactive}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total Extensions</p>
                <p className="text-2xl font-bold">{stats.totalExtensions}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search categories..."
                  value={filter.search}
                  onChange={(e) => setFilter(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select
              value={filter.isActive === undefined ? 'all' : filter.isActive.toString()}
              onValueChange={(value) => 
                setFilter(prev => ({ 
                  ...prev, 
                  isActive: value === 'all' ? undefined : value === 'true' 
                }))
              }
            >
              <SelectTrigger className="w-full md:w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>
            
            <Select
              value={filter.sortBy}
              onValueChange={(value) => 
                setFilter(prev => ({ 
                  ...prev, 
                  sortBy: value as SystemCategoryFilter['sortBy']
                }))
              }
            >
              <SelectTrigger className="w-full md:w-40">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="extensionCount">Extensions</SelectItem>
                <SelectItem value="lastUpdated">Last Updated</SelectItem>
              </SelectContent>
            </Select>
            
            <Select
              value={filter.sortOrder}
              onValueChange={(value) => 
                setFilter(prev => ({ 
                  ...prev, 
                  sortOrder: value as 'asc' | 'desc'
                }))
              }
            >
              <SelectTrigger className="w-full md:w-32">
                <SelectValue placeholder="Order" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="asc">Ascending</SelectItem>
                <SelectItem value="desc">Descending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Categories Grid */}
      {filteredCategories.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No categories found</h3>
            <p className="text-muted-foreground">
              {filter.search || filter.isActive !== undefined 
                ? 'Try adjusting your filters to see more results.'
                : 'Get started by creating your first system category.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCategories.map((category) => (
            <SystemCategoryCard
              key={category.id}
              category={category}
              onToggle={onCategoryToggle}
              onEdit={onCategoryEdit}
            />
          ))}
        </div>
      )}
    </div>
  );
}