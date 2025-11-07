"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { formatDistanceToNow } from "date-fns";

// UI (shadcn)
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Icons (lucide)
import {
  MessageSquare,
  Search as SearchIcon,
  Filter as FilterIcon,
  MoreHorizontal,
  Share2,
  Download,
  Archive,
  Trash2,
  Users,
  Clock,
  TrendingUp,
  BarChart3,
} from "lucide-react";

// Error boundary (local)
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

// Toast
import { useToast } from "@/hooks/use-toast";

/* ----------------------------------------------------------------------------
 * Types
 * --------------------------------------------------------------------------*/

export type Sentiment = "positive" | "neutral" | "negative";
export type Complexity = "simple" | "medium" | "complex";

export interface ThreadMetadata {
  sentiment: Sentiment;
  complexity: Complexity;
  tags: string[];
  messageCount: number;
  averageResponseTime: number; // ms
  summary?: string;
}

export interface ConversationThread {
  id: string;
  title: string;
  topic: string;
  status: "active" | "archived";
  createdAt: Date;
  updatedAt: Date;
  participants: string[];
  metadata: ThreadMetadata;
}

export interface ConversationAnalytics {
  totalConversations: number;
  totalMessages: number;
  averageLength: number;
  topTopics: Array<{ topic: string; count: number }>;
  sentimentDistribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  complexityDistribution: {
    simple: number;
    medium: number;
    complex: number;
  };
  activityByDay: Array<{ date: string; count: number }>;
}

interface ConversationManagerProps {
  conversations: ConversationThread[];
  analytics?: ConversationAnalytics;
  onConversationSelect: (conversationId: string) => void;
  onConversationUpdate: (
    conversationId: string,
    updates: Partial<ConversationThread>
  ) => void;
  onConversationDelete: (conversationId: string) => void;
  onConversationArchive: (conversationId: string) => void;
  onConversationExport: (conversationIds: string[]) => void;
  onConversationShare: (conversationId: string) => void;
  className?: string;
}

/* ----------------------------------------------------------------------------
 * Component
 * --------------------------------------------------------------------------*/

export const ConversationManager: React.FC<ConversationManagerProps> = ({
  conversations,
  analytics,
  onConversationSelect,
  onConversationUpdate,
  onConversationDelete,
  onConversationArchive,
  onConversationExport,
  onConversationShare,
  className = "",
}) => {
  const { toast } = useToast();

  // State
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "archived">(
    "all"
  );
  const [topicFilter, setTopicFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"updated" | "created" | "messages" | "title">(
    "updated"
  );
  const [selectedConversations, setSelectedConversations] = useState<Set<string>>(
    new Set()
  );

  // Topics for filtering
  const availableTopics = useMemo(() => {
    const topics = new Set<string>();
    conversations.forEach((conv) => {
      conv.metadata?.tags?.forEach((t) => topics.add(t));
      if (conv.topic) topics.add(conv.topic);
    });
    return Array.from(topics).sort((a, b) => a.localeCompare(b));
  }, [conversations]);

  // Filter + sort
  const filteredAndSortedConversations = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();

    let filtered = conversations.filter((conv) => {
      const matchesSearch =
        q === "" ||
        conv.title.toLowerCase().includes(q) ||
        (conv.topic && conv.topic.toLowerCase().includes(q)) ||
        (conv.metadata?.tags || []).some((t) => t.toLowerCase().includes(q));

      const matchesStatus = statusFilter === "all" || conv.status === statusFilter;

      const matchesTopic =
        topicFilter === "all" ||
        conv.topic === topicFilter ||
        (conv.metadata?.tags || []).includes(topicFilter);

      return matchesSearch && matchesStatus && matchesTopic;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "created":
          return b.createdAt.getTime() - a.createdAt.getTime();
        case "messages":
          return (b.metadata?.messageCount || 0) - (a.metadata?.messageCount || 0);
        case "title":
          return a.title.localeCompare(b.title);
        case "updated":
        default:
          return b.updatedAt.getTime() - a.updatedAt.getTime();
      }
    });

    return filtered;
  }, [conversations, searchQuery, statusFilter, topicFilter, sortBy]);

  // Selection
  const toggleConversationSelection = useCallback((conversationId: string) => {
    setSelectedConversations((prev) => {
      const next = new Set(prev);
      if (next.has(conversationId)) next.delete(conversationId);
      else next.add(conversationId);
      return next;
    });
  }, []);

  const clearSelection = useCallback(() => setSelectedConversations(new Set()), []);

  // Bulk ops
  const handleBulkExport = useCallback(() => {
    if (selectedConversations.size === 0) {
      toast({
        variant: "destructive",
        title: "No selection",
        description: "Select at least one conversation to export.",
      });
      return;
    }
    onConversationExport(Array.from(selectedConversations));
    clearSelection();
  }, [clearSelection, onConversationExport, selectedConversations, toast]);

  const handleBulkArchive = useCallback(() => {
    if (selectedConversations.size === 0) return;
    selectedConversations.forEach((id) => onConversationArchive(id));
    const count = selectedConversations.size;
    clearSelection();
    toast({
      title: "Archived",
      description: `${count} conversation${count > 1 ? "s" : ""} archived`,
    });
  }, [clearSelection, onConversationArchive, selectedConversations, toast]);

  // Helpers: chip colors
  const getSentimentColor = (sentiment: Sentiment) => {
    switch (sentiment) {
      case "positive":
        return "text-green-600 bg-green-50";
      case "negative":
        return "text-red-600 bg-red-50";
      case "neutral":
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getComplexityColor = (complexity: Complexity) => {
    switch (complexity) {
      case "simple":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "complex":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Accessibility: clear selection on ESC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") clearSelection();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clearSelection]);

  // Render: a single conversation
  const ConversationItem: React.FC<{ conversation: ConversationThread }> = ({
    conversation,
  }) => {
    const isSelected = selectedConversations.has(conversation.id);

    return (
      <Card
        key={conversation.id}
        className={`cursor-pointer transition-all hover:shadow-sm ${
          isSelected ? "ring-2 ring-primary" : ""
        }`}
        role="button"
        aria-label={`Open conversation ${conversation.title}`}
        onClick={() => onConversationSelect(conversation.id)}
      >
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-start gap-3">
            {/* Checkbox */}
            <input
              type="checkbox"
              aria-label="Select conversation"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                toggleConversationSelection(conversation.id);
              }}
              className="mt-1 h-4 w-4"
            />

            {/* Body */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-2 gap-2">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium truncate md:text-base lg:text-lg">
                    {conversation.title}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base truncate">
                    {conversation.topic}
                  </p>
                </div>

                {/* Row actions */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" aria-label="Conversation actions">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onConversationShare(conversation.id)}>
                      <Share2 className="h-4 w-4 mr-2" /> Share
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onConversationExport([conversation.id])}>
                      <Download className="h-4 w-4 mr-2" /> Export
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => onConversationArchive(conversation.id)}>
                      <Archive className="h-4 w-4 mr-2" />
                      {conversation.status === "archived" ? "Unarchive" : "Archive"}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onConversationDelete(conversation.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Meta chips */}
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge className={`text-xs ${getComplexityColor(conversation.metadata.complexity)}`}>
                  {conversation.metadata.complexity}
                </Badge>
                <div className={`px-2 py-1 rounded text-xs ${getSentimentColor(conversation.metadata.sentiment)}`}>
                  {conversation.metadata.sentiment}
                </div>
                <Badge variant="outline" className="text-xs">
                  {conversation.metadata.messageCount} messages
                </Badge>
              </div>

              {/* Tags */}
              {conversation.metadata.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {conversation.metadata.tags.slice(0, 3).map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {conversation.metadata.tags.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{conversation.metadata.tags.length - 3}
                    </Badge>
                  )}
                </div>
              )}

              {/* Summary */}
              {conversation.metadata.summary && (
                <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                  {conversation.metadata.summary}
                </p>
              )}

              {/* Stats */}
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDistanceToNow(conversation.updatedAt, { addSuffix: true })}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {conversation.participants.length}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  <span>{Math.round(conversation.metadata.averageResponseTime)}ms</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Analytics panel
  const AnalyticsPanel: React.FC = () => {
    if (!analytics) return null;
    const topMax = analytics.topTopics[0]?.count || 1;

    return (
      <div className="space-y-6">
        {/* Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.totalConversations}
              </div>
              <div className="text-sm text-muted-foreground">Conversations</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.totalMessages}
              </div>
              <div className="text-sm text-muted-foreground">Messages</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">
                {Math.round(analytics.averageLength)}
              </div>
              <div className="text-sm text-muted-foreground">Avg. Length</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.topTopics.length}
              </div>
              <div className="text-sm text-muted-foreground">Top Topics</div>
            </CardContent>
          </Card>
        </div>

        {/* Top topics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base">Top Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.topTopics.slice(0, 5).map((t) => (
                <div key={t.topic} className="flex items-center justify-between gap-4">
                  <span className="text-sm md:text-base truncate">{t.topic}</span>
                  <div className="flex items-center gap-2 w-40">
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${(t.count / topMax) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-6 text-right">
                      {t.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Sentiment */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base">Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Positive</span>
                <span className="text-sm font-medium">
                  {Math.round(analytics.sentimentDistribution.positive)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Neutral</span>
                <span className="text-sm font-medium">
                  {Math.round(analytics.sentimentDistribution.neutral)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-red-600">Negative</span>
                <span className="text-sm font-medium">
                  {Math.round(analytics.sentimentDistribution.negative)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // Error Fallback Component
  const ErrorFallback = () => <div className="p-4 text-sm">Something went wrong in ConversationManager</div>;

  return (
    <ErrorBoundary fallback={ErrorFallback}>
      <Card className={`h-full flex flex-col ${className}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" /> Conversations
            </CardTitle>

            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {filteredAndSortedConversations.length} of {conversations.length}
              </Badge>

              {selectedConversations.size > 0 && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      Actions ({selectedConversations.size})
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={handleBulkExport}>
                      <Download className="h-4 w-4 mr-2" /> Export Selected
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleBulkArchive}>
                      <Archive className="h-4 w-4 mr-2" /> Archive Selected
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>

          {/* Filters */}
          <div className="space-y-3 mt-3">
            <div className="relative">
              <SearchIcon className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-9"
                aria-label="Search conversations"
              />
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <FilterIcon className="h-4 w-4 text-muted-foreground" />

              {/* Status */}
              <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
                <SelectTrigger className="w-40 h-8 text-xs" aria-label="Status filter">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>

              {/* Topic */}
              <Select value={topicFilter} onValueChange={(v) => setTopicFilter(v)}>
                <SelectTrigger className="w-48 h-8 text-xs" aria-label="Topic filter">
                  <SelectValue placeholder="Topic" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Topics</SelectItem>
                  {availableTopics.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Sort */}
              <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                <SelectTrigger className="w-48 h-8 text-xs" aria-label="Sort by">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="updated">Last Updated</SelectItem>
                  <SelectItem value="created">Created</SelectItem>
                  <SelectItem value="messages">Message Count</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
          <Tabs defaultValue="conversations" className="h-full flex flex-col">
            <TabsList className="mx-4">
              <TabsTrigger value="conversations">
                Conversations ({filteredAndSortedConversations.length})
              </TabsTrigger>
              {analytics && (
                <TabsTrigger value="analytics">
                  <BarChart3 className="h-4 w-4 mr-2" /> Analytics
                </TabsTrigger>
              )}
            </TabsList>

            <div className="flex-1 mt-4">
              <TabsContent value="conversations" className="h-full m-0">
                <ScrollArea className="h-full px-4">
                  <div className="space-y-3 pb-4">
                    {filteredAndSortedConversations.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm md:text-base">
                          {searchQuery || statusFilter !== "all" || topicFilter !== "all"
                            ? "No conversations match your filters"
                            : "No conversations yet"}
                        </p>
                      </div>
                    ) : (
                      filteredAndSortedConversations.map((c) => (
                        <ConversationItem key={c.id} conversation={c} />
                      ))
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              {analytics && (
                <TabsContent value="analytics" className="h-full m-0">
                  <ScrollArea className="h-full px-4">
                    <div className="pb-4">
                      <AnalyticsPanel />
                    </div>
                  </ScrollArea>
                </TabsContent>
              )}
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </ErrorBoundary>
  );
};

export default ConversationManager;
