
"use client";
import React, { useState } from 'react';
import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';

import { } from '@/components/ui/dialog';
import { } from '@/components/ui/select';

import { } from '@/components/ui/dropdown-menu';

import { } from 'lucide-react';


interface ConversationTemplate {
  id: string;
  name: string;
  description: string;
  category: 'coding' | 'learning' | 'problem-solving' | 'creative' | 'analysis' | 'general';
  prompts: Array<{
    id: string;
    text: string;
    order: number;
    isOptional?: boolean;
  }>;
  tags: string[];
  isBuiltIn: boolean;
  usageCount: number;
  rating: number;
  createdAt: Date;
  updatedAt: Date;
}

interface QuickAction {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  prompt: string;
  category: string;
  shortcut?: string;
  isBuiltIn: boolean;
}

interface ConversationTemplatesProps {
  templates?: ConversationTemplate[];
  quickActions?: QuickAction[];
  onTemplateSelect: (template: ConversationTemplate) => void;
  onQuickActionSelect: (action: QuickAction) => void;
  onTemplateCreate?: (template: Omit<ConversationTemplate, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onTemplateUpdate?: (templateId: string, updates: Partial<ConversationTemplate>) => void;
  onTemplateDelete?: (templateId: string) => void;
  className?: string;
}

const defaultTemplates: ConversationTemplate[] = [
  {
    id: 'code-review',
    name: 'Code Review',
    description: 'Get comprehensive code review and suggestions',
    category: 'coding',
    prompts: [
      { id: '1', text: 'Please review this code for best practices and potential improvements:', order: 1 },
      { id: '2', text: 'Are there any security concerns I should be aware of?', order: 2, isOptional: true },
      { id: '3', text: 'How can I optimize this code for better performance?', order: 3, isOptional: true }
    ],
    tags: ['code', 'review', 'best-practices'],
    isBuiltIn: true,
    usageCount: 45,
    rating: 4.8,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: 'learning-session',
    name: 'Learning Session',
    description: 'Structured learning conversation with explanations and examples',
    category: 'learning',
    prompts: [
      { id: '1', text: 'I want to learn about [TOPIC]. Can you explain it step by step?', order: 1 },
      { id: '2', text: 'Can you provide practical examples?', order: 2 },
      { id: '3', text: 'What are some common mistakes to avoid?', order: 3, isOptional: true }
    ],
    tags: ['learning', 'education', 'examples'],
    isBuiltIn: true,
    usageCount: 32,
    rating: 4.6,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    id: 'problem-solving',
    name: 'Problem Solving',
    description: 'Systematic approach to solving complex problems',
    category: 'problem-solving',
    prompts: [
      { id: '1', text: 'I have a problem: [DESCRIBE PROBLEM]. Can you help me break it down?', order: 1 },
      { id: '2', text: 'What are the possible solutions and their trade-offs?', order: 2 },
      { id: '3', text: 'What would be the best approach given my constraints?', order: 3 }
    ],
    tags: ['problem-solving', 'analysis', 'solutions'],
    isBuiltIn: true,
    usageCount: 28,
    rating: 4.7,
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

const defaultQuickActions: QuickAction[] = [
  {
    id: 'explain-code',
    name: 'Explain Code',
    description: 'Get detailed explanation of code functionality',
    icon: Code,
    prompt: 'Please explain what this code does, how it works, and any important details:',
    category: 'coding',
    shortcut: 'Ctrl+E',
    isBuiltIn: true
  },
  {
    id: 'ask-question',
    name: 'Ask Question',
    description: 'Get help with a specific question',
    icon: HelpCircle,
    prompt: 'I have a question about:',
    category: 'general',
    shortcut: 'Ctrl+Q',
    isBuiltIn: true
  },
  {
    id: 'brainstorm',
    name: 'Brainstorm Ideas',
    description: 'Generate creative ideas and solutions',
    icon: Lightbulb,
    prompt: 'Help me brainstorm ideas for:',
    category: 'creative',
    shortcut: 'Ctrl+B',
    isBuiltIn: true
  },
  {
    id: 'summarize',
    name: 'Summarize',
    description: 'Get a concise summary of content',
    icon: BookOpen,
    prompt: 'Please provide a clear summary of:',
    category: 'analysis',
    isBuiltIn: true
  }
];

export const ConversationTemplates: React.FC<ConversationTemplatesProps> = ({
  templates = defaultTemplates,
  quickActions = defaultQuickActions,
  onTemplateSelect,
  onQuickActionSelect,
  onTemplateCreate,
  onTemplateUpdate,
  onTemplateDelete,
  className = ''
}) => {
  const { toast } = useToast();
  
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ConversationTemplate | null>(null);
  
  // New template form state
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    category: 'general' as ConversationTemplate['category'],
    prompts: [{ text: '', order: 1 }],
    tags: [] as string[]

  // Filter templates
  const filteredTemplates = React.useMemo(() => {
    return templates.filter(template => {
      const matchesSearch = searchQuery === '' ||
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter;
      
      return matchesSearch && matchesCategory;

  }, [templates, searchQuery, categoryFilter]);

  // Filter quick actions
  const filteredQuickActions = React.useMemo(() => {
    return quickActions.filter(action => {
      const matchesSearch = searchQuery === '' ||
        action.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.description.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = categoryFilter === 'all' || action.category === categoryFilter;
      
      return matchesSearch && matchesCategory;

  }, [quickActions, searchQuery, categoryFilter]);

  // Handle template creation
  const handleCreateTemplate = () => {
    if (!newTemplate.name.trim()) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Template name is required'

      return;
    }

    const template: Omit<ConversationTemplate, 'id' | 'createdAt' | 'updatedAt'> = {
      ...newTemplate,
      prompts: newTemplate.prompts.map((prompt, index) => ({
        id: `prompt-${index}`,
        text: prompt.text,
        order: index + 1
      })),
      isBuiltIn: false,
      usageCount: 0,
      rating: 0
    };

    onTemplateCreate?.(template);
    setShowCreateDialog(false);
    setNewTemplate({
      name: '',
      description: '',
      category: 'general',
      prompts: [{ text: '', order: 1 }],
      tags: []

    toast({
      title: 'Template Created',
      description: 'Your conversation template has been created successfully'

  };

  // Handle template selection
  const handleTemplateSelect = (template: ConversationTemplate) => {
    onTemplateSelect(template);
    
    // Update usage count if update function is available
    if (onTemplateUpdate) {
      onTemplateUpdate(template.id, {
        usageCount: template.usageCount + 1,
        updatedAt: new Date()

    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'coding':
        return Code;
      case 'learning':
        return BookOpen;
      case 'problem-solving':
        return Zap;
      case 'creative':
        return Lightbulb;
      case 'analysis':
        return Search;
      default:
        return MessageSquare;
    }
  };

  // Get category color
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'coding':
        return 'bg-blue-100 text-blue-800';
      case 'learning':
        return 'bg-green-100 text-green-800';
      case 'problem-solving':
        return 'bg-purple-100 text-purple-800';
      case 'creative':
        return 'bg-yellow-100 text-yellow-800';
      case 'analysis':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Render template item
  const renderTemplate = (template: ConversationTemplate) => {
    const CategoryIcon = getCategoryIcon(template.category);

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
      <Card key={template.id} className="hover:shadow-sm transition-shadow">
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start gap-3 flex-1">
              <CategoryIcon className="h-5 w-5 text-muted-foreground mt-0.5 " />
              <div className="flex-1 min-w-0 ">
                <h3 className="font-medium text-sm md:text-base lg:text-lg">{template.name}</h3>
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {template.description}
                </p>
              </div>
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0 " >
                  <MoreHorizontal className="h-3 w-3 " />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleTemplateSelect(template)}>
                  <Play className="h-4 w-4 mr-2 " />
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setEditingTemplate(template)}>
                  <Edit className="h-4 w-4 mr-2 " />
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Copy className="h-4 w-4 mr-2 " />
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {!template.isBuiltIn && (
                  <DropdownMenuItem 
                    onClick={() => onTemplateDelete?.(template.id)}
                    className="text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2 " />
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <Badge className={`text-xs ${getCategoryColor(template.category)}`}>
              {template.category}
            </Badge>
            
            <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
              <Star className="h-3 w-3 fill-current text-yellow-500 " />
              <span>{template.rating.toFixed(1)}</span>
            </div>
            
            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Used {template.usageCount} times
            </span>
          </div>

          <div className="flex flex-wrap gap-1 mb-3">
            {template.tags.map(tag => (
              <Badge key={tag} variant="outline" className="text-xs sm:text-sm md:text-base">
                {tag}
              </Badge>
            ))}
          </div>

          <div className="space-y-1">
            <span className="text-xs font-medium sm:text-sm md:text-base">Prompts ({template.prompts.length}):</span>
            {template.prompts.slice(0, 2).map(prompt => (
              <p key={prompt.id} className="text-xs text-muted-foreground line-clamp-1 sm:text-sm md:text-base">
                {prompt.order}. {prompt.text}
              </p>
            ))}
            {template.prompts.length > 2 && (
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                +{template.prompts.length - 2} more prompts
              </p>
            )}
          </div>

          <Button
            onClick={() => handleTemplateSelect(template)}
            className="w-full mt-3"
            size="sm"
          >
            <Play className="h-4 w-4 mr-2 " />
          </Button>
        </CardContent>
      </Card>
    );
  };

  // Render quick action
  const renderQuickAction = (action: QuickAction) => {
    const Icon = action.icon;
    
    return (
      <Card 
        key={action.id} 
        className="hover:shadow-sm transition-shadow cursor-pointer"
        onClick={() => onQuickActionSelect(action)}
      >
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-3 mb-2">
            <Icon className="h-5 w-5 text-primary " />
            <div className="flex-1">
              <h3 className="font-medium text-sm md:text-base lg:text-lg">{action.name}</h3>
              {action.shortcut && (
                <Badge variant="outline" className="text-xs mt-1 sm:text-sm md:text-base">
                  {action.shortcut}
                </Badge>
              )}
            </div>
          </div>
          
          <p className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            {action.description}
          </p>
          
          <Badge className={`text-xs ${getCategoryColor(action.category)}`}>
            {action.category}
          </Badge>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Template className="h-5 w-5 " />
            Templates & Quick Actions
          </CardTitle>
          
          {onTemplateCreate && (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button size="sm" aria-label="Button">
                  <Plus className="h-4 w-4 mr-2 " />
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Template</DialogTitle>
                  <DialogDescription>
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Name</label>
                    <input
                      value={newTemplate.name}
                      onChange={(e) => setNewTemplate(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Template name"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Description</label>
                    <textarea
                      value={newTemplate.description}
                      onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Template description"
                      rows={2}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Category</label>
                    <select
                      value={newTemplate.category}
                      onValueChange={(value) = aria-label="Select option"> setNewTemplate(prev => ({ ...prev, category: value as any }))}
                    >
                      <selectTrigger aria-label="Select option">
                        <selectValue />
                      </SelectTrigger>
                      <selectContent aria-label="Select option">
                        <selectItem value="general" aria-label="Select option">General</SelectItem>
                        <selectItem value="coding" aria-label="Select option">Coding</SelectItem>
                        <selectItem value="learning" aria-label="Select option">Learning</SelectItem>
                        <selectItem value="problem-solving" aria-label="Select option">Problem Solving</SelectItem>
                        <selectItem value="creative" aria-label="Select option">Creative</SelectItem>
                        <selectItem value="analysis" aria-label="Select option">Analysis</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button onClick={handleCreateTemplate} className="flex-1" >
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setShowCreateDialog(false)}
                    >
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Search and Filters */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground " />
            <input
              placeholder="Search templates and actions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
          
          <select value={categoryFilter} onValueChange={setCategoryFilter} aria-label="Select option">
            <selectTrigger className="w-full h-8 text-xs sm:text-sm md:text-base" aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="all" aria-label="Select option">All Categories</SelectItem>
              <selectItem value="general" aria-label="Select option">General</SelectItem>
              <selectItem value="coding" aria-label="Select option">Coding</SelectItem>
              <selectItem value="learning" aria-label="Select option">Learning</SelectItem>
              <selectItem value="problem-solving" aria-label="Select option">Problem Solving</SelectItem>
              <selectItem value="creative" aria-label="Select option">Creative</SelectItem>
              <selectItem value="analysis" aria-label="Select option">Analysis</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
        <ScrollArea className="h-full px-4">
          <div className="space-y-6 pb-4">
            {/* Quick Actions */}
            {filteredQuickActions.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium md:text-base lg:text-lg">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredQuickActions.map(renderQuickAction)}
                </div>
              </div>
            )}

            {/* Templates */}
            {filteredTemplates.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium md:text-base lg:text-lg">Templates</h3>
                <div className="space-y-3">
                  {filteredTemplates.map(renderTemplate)}
                </div>
              </div>
            )}

            {/* Empty State */}
            {filteredTemplates.length === 0 && filteredQuickActions.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Template className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                <p className="text-sm md:text-base lg:text-lg">
                  {searchQuery || categoryFilter !== 'all'
                    ? 'No templates or actions match your search'
                    : 'No templates or actions available'}
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default ConversationTemplates;