// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/ConversationThreading.tsx
"use client";

import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
  MoreHorizontal,
  Archive,
  Trash2,
  TrendingUp,
  Tag,
  Clock,
  Users,
  Brain,
  MessageSquare,
  Plus,
  Search,
  Filter,
} from "lucide-react";

import type { ConversationThread, ThreadMetadata } from "@/types/enhanced-chat";
import { formatDistanceToNow } from "date-fns";

interface ConversationThreadingProps {
  threads: ConversationThread[];
  activeThreadId?: string;
  onThreadSelect: (threadId: string) => void;
  onThreadCreate: (topic: string) => void;
  onThreadUpdate: (threadId: string, updates: Partial<ConversationThread>) => void;
  onThreadDelete: (threadId: string) => void;
  onThreadArchive: (threadId: string) => void; // toggle archive/unarchive
  className?: string;
}

export const ConversationThreading: React.FC<ConversationThreadingProps> = ({
  threads,
  activeThreadId,
  onThreadSelect,
  onThreadCreate,
  // onThreadUpdate (reserved for inline edit footer / future),
  onThreadDelete,
  onThreadArchive,
  className = "",
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "archived">("all");
  const [sortBy, setSortBy] = useState<"updated" | "created" | "messages">("updated");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newThreadTopic, setNewThreadTopic] = useState("");

  const safeLower = (v?: string) => (v ?? "").toLowerCase();
  const safeTags = (t?: string[]) => t ?? [];

  const filteredAndSortedThreads = useMemo(() => {
    const q = safeLower(searchQuery);

    let filtered = threads.filter((thread) => {
      const title = safeLower(thread.title);
      const topic = safeLower(thread.topic);
      const tags = safeTags(thread.metadata?.tags).map((t) => t.toLowerCase());

      const matchesSearch =
        q === "" ||
        title.includes(q) ||
        topic.includes(q) ||
        tags.some((tag) => tag.includes(q));

      const matchesFilter = filterStatus === "all" || thread.status === filterStatus;

      return matchesSearch && matchesFilter;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "created": {
          const aTime = new Date(a.createdAt as any).getTime();
          const bTime = new Date(b.createdAt as any).getTime();
          return bTime - aTime;
        }
        case "messages": {
          const aCount = a.metadata?.messageCount ?? 0;
          const bCount = b.metadata?.messageCount ?? 0;
          return bCount - aCount;
        }
        case "updated":
        default: {
          const aTime = new Date(a.updatedAt as any).getTime();
          const bTime = new Date(b.updatedAt as any).getTime();
          return bTime - aTime;
        }
      }
    });

    return filtered;
  }, [threads, searchQuery, filterStatus, sortBy]);

  const handleCreateThread = () => {
    const topic = newThreadTopic.trim();
    if (!topic) return;
    onThreadCreate(topic);
    setNewThreadTopic("");
    setShowCreateForm(false);
  };

  const getComplexityColor = (complexity: ThreadMetadata["complexity"]) => {
    switch (complexity) {
      case "simple":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
      case "complex":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
    }
  };

  const getSentimentColor = (sentiment: ThreadMetadata["sentiment"]) => {
    switch (sentiment) {
      case "positive":
        return "text-green-600 dark:text-green-400";
      case "negative":
        return "text-red-600 dark:text-red-400";
      case "neutral":
      default:
        return "text-muted-foreground";
    }
  };

  const renderThreadItem = (thread: ConversationThread) => {
    const isActive = thread.id === activeThreadId;

    const msgCount = thread.metadata?.messageCount ?? 0;
    const tags = safeTags(thread.metadata?.tags);
    const complexity = (thread.metadata?.complexity ?? "simple") as ThreadMetadata["complexity"];
    const sentiment = (thread.metadata?.sentiment ?? "neutral") as ThreadMetadata["sentiment"];
    const avgMs =
      Math.round((thread.metadata?.averageResponseTime ?? 0) || 0) || 0;

    return (
      <div
        key={thread.id}
        role="button"
        tabIndex={0}
        aria-pressed={isActive}
        aria-label={`Open thread: ${thread.title}`}
        className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-sm outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
          isActive ? "border-primary bg-primary/5" : "hover:bg-muted/50"
        }`}
        onClick={() => onThreadSelect(thread.id)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onThreadSelect(thread.id);
        }}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm truncate md:text-base lg:text-lg">
              {thread.title}
            </h3>
            <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
              {thread.topic}
            </p>
          </div>

          <div className="flex items-center gap-2 ml-2">
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
              {msgCount}
            </Badge>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  aria-label="Thread actions"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                onClick={(e) => e.stopPropagation()}
              >
                <DropdownMenuItem
                  onClick={() => onThreadArchive(thread.id)}
                >
                  <Archive className="h-4 w-4 mr-2" />
                  {thread.status === "archived" ? "Unarchive" : "Archive"}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => onThreadDelete(thread.id)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Thread metadata */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`px-2 py-1 rounded-full text-xs capitalize ${getComplexityColor(
              complexity
            )}`}
          >
            {complexity}
          </span>

          <div className={`flex items-center gap-1 text-xs ${getSentimentColor(sentiment)}`}>
            <TrendingUp className="h-3 w-3" />
            <span className="capitalize">{sentiment}</span>
          </div>

          {tags.length > 0 && (
            <div className="flex items-center gap-1">
              <Tag className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {tags.slice(0, 2).join(", ")}
                {tags.length > 2 && "…"}
              </span>
            </div>
          )}
        </div>

        {/* Thread summary */}
        {thread.metadata?.summary && (
          <p className="text-xs text-muted-foreground mb-2 line-clamp-2 sm:text-sm md:text-base">
            {thread.metadata.summary}
          </p>
        )}

        {/* Thread stats */}
        <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDistanceToNow(new Date(thread.updatedAt as any), { addSuffix: true })}
            </span>

            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {thread.participants?.length ?? 0}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <Brain className="h-3 w-3" />
            <span>{avgMs}ms avg</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <MessageSquare className="h-5 w-5" />
            Threads{" "}
            <span className="text-muted-foreground text-sm">
              ({threads.length})
            </span>
          </CardTitle>

          <Button
            size="sm"
            onClick={() => setShowCreateForm(true)}
            className="h-8"
            aria-label="Create new thread"
          >
            <Plus className="h-4 w-4 mr-1" />
            New
          </Button>
        </div>

        {/* Create new thread form */}
        {showCreateForm && (
          <div className="space-y-2 p-3 border rounded-lg bg-muted/50 sm:p-4 md:p-6">
            <Input
              placeholder="Enter conversation topic…"
              value={newThreadTopic}
              onChange={(e) => setNewThreadTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCreateThread();
                } else if (e.key === "Escape") {
                  setShowCreateForm(false);
                  setNewThreadTopic("");
                }
              }}
              aria-label="New thread topic"
              autoFocus
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateThread}>
                Create
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewThreadTopic("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Search and filters */}
        <div className="space-y-2 mt-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
              aria-label="Search conversations"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <label className="sr-only" htmlFor="filter-status">
              Filter status
            </label>
            <select
              id="filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="text-sm border rounded px-2 py-1 bg-background md:text-base"
              aria-label="Filter by status"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>

            <label className="sr-only" htmlFor="sort-by">
              Sort by
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-sm border rounded px-2 py-1 bg-background md:text-base"
              aria-label="Sort threads"
            >
              <option value="updated">Last Updated</option>
              <option value="created">Created</option>
              <option value="messages">Message Count</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
        <ScrollArea className="h-full px-4">
          <div className="space-y-3 pb-4">
            {filteredAndSortedThreads.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm md:text-base lg:text-lg">
                  {searchQuery || filterStatus !== "all"
                    ? "No conversations match your filters"
                    : "No conversations yet"}
                </p>
                {!searchQuery && filterStatus === "all" && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => setShowCreateForm(true)}
                  >
                    Start a thread
                  </Button>
                )}
              </div>
            ) : (
              filteredAndSortedThreads.map(renderThreadItem)
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default ConversationThreading;
