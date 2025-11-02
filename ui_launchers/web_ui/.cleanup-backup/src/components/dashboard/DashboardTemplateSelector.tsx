'use client';

import React, { useState } from 'react';
import { 
  Layout, 
  Star, 
  Users, 
  Settings, 
  Download,
  Eye,
  Plus,
  Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import type { DashboardTemplate } from '@/store/dashboard-store';

interface DashboardTemplateSelectorProps {
  templates: DashboardTemplate[];
  userRoles?: string[];
  onApplyTemplate: (templateId: string) => void;
  onPreviewTemplate?: (template: DashboardTemplate) => void;
  className?: string;
}

export const DashboardTemplateSelector: React.FC<DashboardTemplateSelectorProps> = ({
  templates,
  userRoles = [],
  onApplyTemplate,
  onPreviewTemplate,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [previewTemplate, setPreviewTemplate] = useState<DashboardTemplate | null>(null);

  // Filter templates based on user roles and search
  const filteredTemplates = templates.filter(template => {
    // Role-based filtering
    if (template.category === 'role-based' && template.roles) {
      const hasRequiredRole = template.roles.some(role => userRoles.includes(role));
      if (!hasRequiredRole) return false;
    }

    // Category filtering
    if (selectedCategory !== 'all' && template.category !== selectedCategory) {
      return false;
    }

    // Search filtering
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        template.name.toLowerCase().includes(query) ||
        template.description.toLowerCase().includes(query) ||
        template.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    return true;
  });

  // Group templates by category
  const groupedTemplates = filteredTemplates.reduce((acc, template) => {
    const category = template.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(template);
    return acc;
  }, {} as Record<string, DashboardTemplate[]>);

  const handleApplyTemplate = (templateId: string) => {
    onApplyTemplate(templateId);
    setIsOpen(false);
  };

  const handlePreviewTemplate = (template: DashboardTemplate) => {
    setPreviewTemplate(template);
    onPreviewTemplate?.(template);
  };

  const getCategoryIcon = (category: DashboardTemplate['category']) => {
    switch (category) {
      case 'system':
        return <Settings className="h-4 w-4" />;
      case 'role-based':
        return <Users className="h-4 w-4" />;
      case 'user':
        return <Star className="h-4 w-4" />;
      default:
        return <Layout className="h-4 w-4" />;
    }
  };

  const getCategoryLabel = (category: DashboardTemplate['category']) => {
    switch (category) {
      case 'system':
        return 'System Templates';
      case 'role-based':
        return 'Role-Based Templates';
      case 'user':
        return 'User Templates';
      default:
        return 'Templates';
    }
  };

  const getCategoryBadgeVariant = (category: DashboardTemplate['category']) => {
    switch (category) {
      case 'system':
        return 'default';
      case 'role-based':
        return 'secondary';
      case 'user':
        return 'outline';
      default:
        return 'outline';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className={className}>
          <Layout className="h-4 w-4 mr-2" />
          Templates
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Dashboard Templates</DialogTitle>
        </DialogHeader>
        
        <div className="flex flex-col h-full">
          {/* Search and Filter Controls */}
          <div className="flex gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="system">System</SelectItem>
                <SelectItem value="role-based">Role-Based</SelectItem>
                <SelectItem value="user">User Created</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Templates Grid */}
          <div className="flex-1 overflow-y-auto">
            {Object.keys(groupedTemplates).length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Layout className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No templates found</h3>
                <p className="text-sm">
                  {searchQuery 
                    ? 'Try adjusting your search criteria'
                    : 'No templates available for your current filters'
                  }
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
                  <div key={category}>
                    <div className="flex items-center gap-2 mb-3">
                      {getCategoryIcon(category as DashboardTemplate['category'])}
                      <h3 className="text-lg font-semibold">
                        {getCategoryLabel(category as DashboardTemplate['category'])}
                      </h3>
                      <Badge variant="secondary" className="text-xs">
                        {categoryTemplates.length}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {categoryTemplates.map(template => (
                        <Card 
                          key={template.id} 
                          className="cursor-pointer hover:shadow-md transition-shadow"
                        >
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <CardTitle className="text-base flex items-center gap-2">
                                  {template.name}
                                  {template.isDefault && (
                                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                  )}
                                </CardTitle>
                                <CardDescription className="text-xs mt-1">
                                  {template.description}
                                </CardDescription>
                              </div>
                              <Badge 
                                variant={getCategoryBadgeVariant(template.category)}
                                className="text-xs"
                              >
                                {template.category}
                              </Badge>
                            </div>
                          </CardHeader>
                          
                          <CardContent className="pt-0">
                            {/* Template Tags */}
                            {template.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-3">
                                {template.tags.slice(0, 3).map(tag => (
                                  <Badge key={tag} variant="outline" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                                {template.tags.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{template.tags.length - 3}
                                  </Badge>
                                )}
                              </div>
                            )}
                            
                            {/* Template Stats */}
                            <div className="text-xs text-muted-foreground mb-3">
                              {template.config.widgets.length} widgets • {template.config.layout} layout
                            </div>
                            
                            {/* Template Actions */}
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => handleApplyTemplate(template.id)}
                                className="flex-1"
                              >
                                <Plus className="h-3 w-3 mr-1" />
                                Use Template
                              </Button>
                              
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handlePreviewTemplate(template)}
                              >
                                <Eye className="h-3 w-3" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </DialogContent>

      {/* Template Preview Dialog */}
      {previewTemplate && (
        <Dialog 
          open={!!previewTemplate} 
          onOpenChange={() => setPreviewTemplate(null)}
        >
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {previewTemplate.name}
                {previewTemplate.isDefault && (
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                )}
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {previewTemplate.description}
              </p>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Category:</span> {previewTemplate.category}
                </div>
                <div>
                  <span className="font-medium">Layout:</span> {previewTemplate.config.layout}
                </div>
                <div>
                  <span className="font-medium">Widgets:</span> {previewTemplate.config.widgets.length}
                </div>
                <div>
                  <span className="font-medium">Refresh:</span> {previewTemplate.config.refreshInterval / 1000}s
                </div>
              </div>
              
              {previewTemplate.tags.length > 0 && (
                <div>
                  <span className="font-medium text-sm">Tags:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {previewTemplate.tags.map(tag => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {previewTemplate.config.widgets.length > 0 && (
                <div>
                  <span className="font-medium text-sm">Widgets:</span>
                  <div className="mt-2 space-y-2">
                    {previewTemplate.config.widgets.map(widget => (
                      <div key={widget.id} className="flex items-center justify-between p-2 bg-muted rounded">
                        <div>
                          <span className="text-sm font-medium">{widget.title}</span>
                          <span className="text-xs text-muted-foreground ml-2">
                            ({widget.type})
                          </span>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {widget.size}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setPreviewTemplate(null)}
                >
                  Close
                </Button>
                <Button
                  onClick={() => {
                    handleApplyTemplate(previewTemplate.id);
                    setPreviewTemplate(null);
                  }}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Use This Template
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Dialog>
  );
};

export default DashboardTemplateSelector;