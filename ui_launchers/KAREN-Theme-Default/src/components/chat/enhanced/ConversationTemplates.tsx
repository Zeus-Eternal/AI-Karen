// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/ConversationTemplates.tsx
"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

import {
  Code,
  HelpCircle,
  Lightbulb,
  BookOpen,
  Search as SearchIcon,
  Zap,
  MessageSquare,
  MoreHorizontal,
  Play,
  Edit,
  Copy,
  Trash2,
  Star,
  Plus,
  LayoutTemplate, // safer than "Template"
} from "lucide-react";

/* ----------------------------- Types ------------------------------ */

interface ConversationTemplate {
  id: string;
  name: string;
  description: string;
  category: "coding" | "learning" | "problem-solving" | "creative" | "analysis" | "general";
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
  category: "coding" | "learning" | "problem-solving" | "creative" | "analysis" | "general";
  shortcut?: string; // e.g., "Ctrl+E"
  isBuiltIn: boolean;
}

interface ConversationTemplatesProps {
  templates?: ConversationTemplate[];
  quickActions?: QuickAction[];
  onTemplateSelect: (template: ConversationTemplate) => void;
  onQuickActionSelect: (action: QuickAction) => void;
  onTemplateCreate?: (template: Omit<ConversationTemplate, "id" | "createdAt" | "updatedAt">) => void;
  onTemplateUpdate?: (templateId: string, updates: Partial<ConversationTemplate>) => void;
  onTemplateDelete?: (templateId: string) => void;
  className?: string;
}

/* ------------------------ Defaults (Built-ins) --------------------- */

const defaultTemplates: ConversationTemplate[] = [
  {
    id: "code-review",
    name: "Code Review",
    description: "Get comprehensive code review and suggestions",
    category: "coding",
    prompts: [
      { id: "1", text: "Please review this code for best practices and potential improvements:", order: 1 },
      { id: "2", text: "Are there any security concerns I should be aware of?", order: 2, isOptional: true },
      { id: "3", text: "How can I optimize this code for better performance?", order: 3, isOptional: true },
    ],
    tags: ["code", "review", "best-practices"],
    isBuiltIn: true,
    usageCount: 45,
    rating: 4.8,
    createdAt: new Date(),
    updatedAt: new Date(),
  },
  {
    id: "learning-session",
    name: "Learning Session",
    description: "Structured learning conversation with explanations and examples",
    category: "learning",
    prompts: [
      { id: "1", text: "I want to learn about [TOPIC]. Can you explain it step by step?", order: 1 },
      { id: "2", text: "Can you provide practical examples?", order: 2 },
      { id: "3", text: "What are some common mistakes to avoid?", order: 3, isOptional: true },
    ],
    tags: ["learning", "education", "examples"],
    isBuiltIn: true,
    usageCount: 32,
    rating: 4.6,
    createdAt: new Date(),
    updatedAt: new Date(),
  },
  {
    id: "problem-solving",
    name: "Problem Solving",
    description: "Systematic approach to solving complex problems",
    category: "problem-solving",
    prompts: [
      { id: "1", text: "I have a problem: [DESCRIBE PROBLEM]. Can you help me break it down?", order: 1 },
      { id: "2", text: "What are the possible solutions and their trade-offs?", order: 2 },
      { id: "3", text: "What would be the best approach given my constraints?", order: 3 },
    ],
    tags: ["problem-solving", "analysis", "solutions"],
    isBuiltIn: true,
    usageCount: 28,
    rating: 4.7,
    createdAt: new Date(),
    updatedAt: new Date(),
  },
];

const defaultQuickActions: QuickAction[] = [
  {
    id: "explain-code",
    name: "Explain Code",
    description: "Get detailed explanation of code functionality",
    icon: Code,
    prompt: "Please explain what this code does, how it works, and any important details:",
    category: "coding",
    shortcut: "Ctrl+E",
    isBuiltIn: true,
  },
  {
    id: "ask-question",
    name: "Ask Question",
    description: "Get help with a specific question",
    icon: HelpCircle,
    prompt: "I have a question about:",
    category: "general",
    shortcut: "Ctrl+Q",
    isBuiltIn: true,
  },
  {
    id: "brainstorm",
    name: "Brainstorm Ideas",
    description: "Generate creative ideas and solutions",
    icon: Lightbulb,
    prompt: "Help me brainstorm ideas for:",
    category: "creative",
    shortcut: "Ctrl+B",
    isBuiltIn: true,
  },
  {
    id: "summarize",
    name: "Summarize",
    description: "Get a concise summary of content",
    icon: BookOpen,
    prompt: "Please provide a clear summary of:",
    category: "analysis",
    isBuiltIn: true,
  },
];

/* ---------------------------- Component ---------------------------- */

export const ConversationTemplates: React.FC<ConversationTemplatesProps> = ({
  templates = defaultTemplates,
  quickActions = defaultQuickActions,
  onTemplateSelect,
  onQuickActionSelect,
  onTemplateCreate,
  onTemplateUpdate,
  onTemplateDelete,
  className = "",
}) => {
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] =
    useState<ConversationTemplate["category"] | "all">("all");

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ConversationTemplate | null>(null);

  const [newTemplate, setNewTemplate] = useState<{
    name: string;
    description: string;
    category: ConversationTemplate["category"];
    prompts: { text: string; order: number; isOptional?: boolean }[];
    tags: string[];
  }>({
    name: "",
    description: "",
    category: "general",
    prompts: [{ text: "", order: 1 }],
    tags: [],
  });

  /* ---------------------- Derived, Filters, Memos ---------------------- */

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        q === "" ||
        template.name.toLowerCase().includes(q) ||
        template.description.toLowerCase().includes(q) ||
        template.tags.some((t) => t.toLowerCase().includes(q));

      const matchesCategory = categoryFilter === "all" || template.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [templates, searchQuery, categoryFilter]);

  const filteredQuickActions = useMemo(() => {
    return quickActions.filter((action) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        q === "" ||
        action.name.toLowerCase().includes(q) ||
        action.description.toLowerCase().includes(q);

      const matchesCategory = categoryFilter === "all" || action.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [quickActions, searchQuery, categoryFilter]);

  /* ------------------------- Handlers & Logic -------------------------- */

  const handleCreateTemplate = useCallback(() => {
    if (!newTemplate.name.trim()) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Template name is required.",
      });
      return;
    }

    const template: Omit<ConversationTemplate, "id" | "createdAt" | "updatedAt"> = {
      name: newTemplate.name.trim(),
      description: newTemplate.description.trim(),
      category: newTemplate.category,
      prompts: newTemplate.prompts
        .filter((p) => p.text.trim().length > 0)
        .map((p, idx) => ({
          id: `prompt-${idx + 1}`,
          text: p.text.trim(),
          order: idx + 1,
          isOptional: p.isOptional,
        })),
      tags: newTemplate.tags.map((t) => t.trim()).filter(Boolean),
      isBuiltIn: false,
      usageCount: 0,
      rating: 0,
    };

    onTemplateCreate?.(template);

    setShowCreateDialog(false);
    setNewTemplate({
      name: "",
      description: "",
      category: "general",
      prompts: [{ text: "", order: 1 }],
      tags: [],
    });

    toast({
      title: "Template Created",
      description: "Your conversation template has been created successfully.",
    });
  }, [newTemplate, onTemplateCreate, toast]);

  const handleTemplateSelect = useCallback(
    (template: ConversationTemplate) => {
      onTemplateSelect(template);
      if (onTemplateUpdate) {
        onTemplateUpdate(template.id, { usageCount: template.usageCount + 1, updatedAt: new Date() });
      }
    },
    [onTemplateSelect, onTemplateUpdate]
  );

  // Keyboard shortcuts for quick actions (Ctrl+E / Ctrl+Q / Ctrl+B)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      const matchByShortcut = (shortcut?: string) =>
        shortcut ? shortcut.toLowerCase().replace("cmd", "ctrl") === `ctrl+${key}` : false;

      if (ctrl && ["e", "q", "b"].includes(key)) {
        const action = quickActions.find((a) => matchByShortcut(a.shortcut));
        if (action) {
          e.preventDefault();
          onQuickActionSelect(action);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onQuickActionSelect, quickActions]);

  /* --------------------------- UI Helpers ----------------------------- */

  const getCategoryIcon = (category: ConversationTemplate["category"] | "all") => {
    switch (category) {
      case "coding":
        return Code;
      case "learning":
        return BookOpen;
      case "problem-solving":
        return Zap;
      case "creative":
        return Lightbulb;
      case "analysis":
        return SearchIcon;
      case "general":
      default:
        return MessageSquare;
    }
  };

  const getCategoryColor = (category: ConversationTemplate["category"] | "all") => {
    switch (category) {
      case "coding":
        return "bg-blue-100 text-blue-800";
      case "learning":
        return "bg-green-100 text-green-800";
      case "problem-solving":
        return "bg-purple-100 text-purple-800";
      case "creative":
        return "bg-yellow-100 text-yellow-800";
      case "analysis":
        return "bg-orange-100 text-orange-800";
      case "general":
      case "all":
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  /* ---------------------- Renderers: Template/Action ------------------- */

  const renderTemplate = (template: ConversationTemplate) => {
    const CategoryIcon = getCategoryIcon(template.category);

    return (
      <Card key={template.id} className="hover:shadow-sm transition-shadow">
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-start gap-3 flex-1">
              <CategoryIcon className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-sm md:text-base lg:text-lg">{template.name}</h3>
                <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                  {template.description}
                </p>
              </div>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Template actions">
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleTemplateSelect(template)}>
                  <Play className="h-4 w-4 mr-2" />
                  Use
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setEditingTemplate(template)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    // simple clone-to-create UX
                    if (onTemplateCreate) {
                      const cloned: Omit<ConversationTemplate, "id" | "createdAt" | "updatedAt"> = {
                        name: `${template.name} (Copy)`,
                        description: template.description,
                        category: template.category,
                        prompts: template.prompts.map((p, i) => ({
                          id: `prompt-${i + 1}`,
                          order: i + 1,
                          text: p.text,
                          isOptional: p.isOptional,
                        })),
                        tags: [...template.tags],
                        isBuiltIn: false,
                        usageCount: 0,
                        rating: 0,
                      };
                      onTemplateCreate(cloned);
                      toast({ title: "Template Cloned", description: "Copy created successfully." });
                    }
                  }}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {!template.isBuiltIn && (
                  <DropdownMenuItem
                    onClick={() => onTemplateDelete?.(template.id)}
                    className="text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <Badge className={`text-xs ${getCategoryColor(template.category)}`}>{template.category}</Badge>

            <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
              <Star className="h-3 w-3 fill-current text-yellow-500" />
              <span>{template.rating.toFixed(1)}</span>
            </div>

            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Used {template.usageCount} times
            </span>
          </div>

          <div className="flex flex-wrap gap-1 mb-3">
            {template.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs sm:text-sm md:text-base">
                {tag}
              </Badge>
            ))}
          </div>

          <div className="space-y-1">
            <span className="text-xs font-medium sm:text-sm md:text-base">
              Prompts ({template.prompts.length}):
            </span>
            {template.prompts.slice(0, 2).map((prompt) => (
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

          <Button onClick={() => handleTemplateSelect(template)} className="w-full mt-3" size="sm">
            <Play className="h-4 w-4 mr-2" />
            Use Template
          </Button>
        </CardContent>
      </Card>
    );
  };

  const renderQuickAction = (action: QuickAction) => {
    const Icon = action.icon;
    return (
      <Card
        key={action.id}
        role="button"
        tabIndex={0}
        className="hover:shadow-sm transition-shadow cursor-pointer"
        onClick={() => onQuickActionSelect(action)}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onQuickActionSelect(action)}
      >
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-3 mb-2">
            <Icon className="h-5 w-5 text-primary" />
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

          <Badge className={`text-xs ${getCategoryColor(action.category)}`}>{action.category}</Badge>
        </CardContent>
      </Card>
    );
  };

  /* ------------------------------- JSX -------------------------------- */

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <LayoutTemplate className="h-5 w-5" />
            Templates & Quick Actions
          </CardTitle>

          {onTemplateCreate && (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button size="sm" aria-label="Create template">
                  <Plus className="h-4 w-4 mr-2" />
                  New
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Template</DialogTitle>
                  <DialogDescription>Define a reusable chat template for your team.</DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Name</label>
                    <Input
                      value={newTemplate.name}
                      onChange={(e) => setNewTemplate((prev) => ({ ...prev, name: e.target.value }))}
                      placeholder="Template name"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium">Description</label>
                    <Textarea
                      value={newTemplate.description}
                      onChange={(e) =>
                        setNewTemplate((prev) => ({ ...prev, description: e.target.value }))
                      }
                      placeholder="Template description"
                      rows={2}
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium">Category</label>
                    <Select
                      value={newTemplate.category}
                      onValueChange={(value) =>
                        setNewTemplate((prev) => ({
                          ...prev,
                          category: value as ConversationTemplate["category"],
                        }))
                      }
                    >
                      <SelectTrigger aria-label="Select category">
                        <SelectValue placeholder="Choose a category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">General</SelectItem>
                        <SelectItem value="coding">Coding</SelectItem>
                        <SelectItem value="learning">Learning</SelectItem>
                        <SelectItem value="problem-solving">Problem Solving</SelectItem>
                        <SelectItem value="creative">Creative</SelectItem>
                        <SelectItem value="analysis">Analysis</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Prompts</label>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setNewTemplate((prev) => ({
                            ...prev,
                            prompts: [...prev.prompts, { text: "", order: prev.prompts.length + 1 }],
                          }))
                        }
                      >
                        Add Prompt
                      </Button>
                    </div>

                    <div className="space-y-2">
                      {newTemplate.prompts.map((p, idx) => (
                        <div key={idx} className="flex gap-2">
                          <Input
                            value={p.text}
                            onChange={(e) =>
                              setNewTemplate((prev) => {
                                const copy = [...prev.prompts];
                                copy[idx] = { ...copy[idx], text: e.target.value };
                                return { ...prev, prompts: copy };
                              })
                            }
                            placeholder={`Prompt ${idx + 1}`}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label="Remove prompt"
                            onClick={() =>
                              setNewTemplate((prev) => {
                                const copy = [...prev.prompts];
                                copy.splice(idx, 1);
                                return {
                                  ...prev,
                                  prompts: copy.map((pp, i) => ({ ...pp, order: i + 1 })),
                                };
                              })
                            }
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium">Tags (comma separated)</label>
                    <Input
                      value={newTemplate.tags.join(", ")}
                      onChange={(e) =>
                        setNewTemplate((prev) => ({
                          ...prev,
                          tags: e.target.value
                            .split(",")
                            .map((t) => t.trim())
                            .filter(Boolean),
                        }))
                      }
                      placeholder="e.g. code, review, security"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button className="flex-1" onClick={handleCreateTemplate}>
                      Create
                    </Button>
                    <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Search & Filters */}
        <div className="space-y-3 mt-3">
          <div className="relative">
            <SearchIcon className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates and actions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>

          <Select
            value={categoryFilter}
            onValueChange={(val) => setCategoryFilter(val as ConversationTemplate["category"] | "all")}
          >
            <SelectTrigger className="w-full h-8 text-xs sm:text-sm md:text-base" aria-label="Filter by category">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="general">General</SelectItem>
              <SelectItem value="coding">Coding</SelectItem>
              <SelectItem value="learning">Learning</SelectItem>
              <SelectItem value="problem-solving">Problem Solving</SelectItem>
              <SelectItem value="creative">Creative</SelectItem>
              <SelectItem value="analysis">Analysis</SelectItem>
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
                <div className="space-y-3">{filteredTemplates.map(renderTemplate)}</div>
              </div>
            )}

            {/* Empty State */}
            {filteredTemplates.length === 0 && filteredQuickActions.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <LayoutTemplate className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm md:text-base lg:text-lg">
                  {searchQuery || categoryFilter !== "all"
                    ? "No templates or actions match your search"
                    : "No templates or actions available"}
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
