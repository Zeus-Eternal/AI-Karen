"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Lightbulb,
  TrendingUp,
  ArrowRight,
  HelpCircle,
  Zap,
  Brain,
} from "lucide-react";

import type {
  EnhancedChatMessage,
  ConversationContext,
  ContextSuggestion,
} from "@/types/enhanced-chat";

interface ContextSuggestionsProps {
  messages: EnhancedChatMessage[];
  conversationContext: ConversationContext;
  onSuggestionSelect: (suggestion: ContextSuggestion) => void;
  className?: string;
  maxSuggestions?: number;
}

export const ContextSuggestions: React.FC<ContextSuggestionsProps> = ({
  messages,
  conversationContext,
  onSuggestionSelect,
  className = "",
  maxSuggestions = 6,
}) => {
  const [suggestions, setSuggestions] = useState<ContextSuggestion[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Derived, context-aware suggestions
  const generatedSuggestions = useMemo<ContextSuggestion[]>(() => {
    if (!messages || messages.length === 0 || !conversationContext) return [];

    const lastMessage = messages[messages.length - 1];
    const currentTopic = conversationContext.currentThread?.topic ?? "";
    const userPatterns = conversationContext.userPatterns ?? [];

    const out: ContextSuggestion[] = [];

    // Follow-ups based on assistant output
    if (lastMessage && lastMessage.role === "assistant") {
      const hasCodeHint =
        (typeof lastMessage.content === "string" &&
          lastMessage.content.toLowerCase().includes("code")) ||
        lastMessage.type === "code";

      if (hasCodeHint) {
        out.push({
          id: "follow-up-code-1",
          type: "follow_up",
          text: "Can you explain this code in more detail?",
          confidence: 0.85,
          reasoning: "Assistant provided code; user may want deeper explanation",
        });
        out.push({
          id: "follow-up-code-2",
          type: "follow_up",
          text: "How can I modify this code for my use case?",
          confidence: 0.8,
          reasoning: "Common next step after code examples",
        });
      }

      const hasErrorHint =
        typeof lastMessage.content === "string" &&
        (lastMessage.content.toLowerCase().includes("error") ||
          lastMessage.content.toLowerCase().includes("problem"));

      if (hasErrorHint) {
        out.push({
          id: "follow-up-error-1",
          type: "follow_up",
          text: "What are some alternative approaches?",
          confidence: 0.75,
          reasoning: "Offer alternatives when issues are mentioned",
        });
      }
    }

    // Clarifications for complex threads
    if (conversationContext.currentThread?.metadata?.complexity === "complex") {
      out.push({
        id: "clarification-1",
        type: "clarification",
        text: "Can you break this down into simpler steps?",
        confidence: 0.7,
        reasoning: "Complex topic benefits from simplification",
      });
      out.push({
        id: "clarification-2",
        type: "clarification",
        text: "What are the key points I should focus on?",
        confidence: 0.68,
        reasoning: "Helps user focus on the essentials",
      });
    }

    // Topic expansion
    if (currentTopic) {
      out.push({
        id: "related-topic-1",
        type: "related_topic",
        text: `Tell me more about ${currentTopic}`,
        confidence: 0.65,
        reasoning: "Explore current topic deeper",
      });
    }

    // Pattern-based actions
    userPatterns.forEach((pattern, index) => {
      if (pattern?.type === "preference" && (pattern.confidence ?? 0) > 0.7) {
        out.push({
          id: `pattern-${index}`,
          type: "action",
          text: `Would you like help with ${pattern.pattern}?`,
          confidence: (pattern.confidence ?? 0) * 0.8,
          reasoning: `Based on preference pattern: ${pattern.pattern}`,
        });
      }
    });

    // Memory-based nudges
    const memories = conversationContext.memoryContext?.relevantMemories ?? [];
    if (memories.length > 0) {
      const top = memories[0];
      out.push({
        id: "memory-1",
        type: "related_topic",
        text: "This reminds me of something we discussed before…",
        confidence: Math.min(0.99, (top.relevance ?? 0.7) * 0.9),
        reasoning: "Leverage top relevant prior memory",
      });
    }

    // Action suggestions based on last user message
    const lastUserMessage = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMessage && typeof lastUserMessage.content === "string") {
      const c = lastUserMessage.content.toLowerCase();

      if (c.includes("how") || c.includes("tutorial")) {
        out.push({
          id: "action-tutorial",
          type: "action",
          text: "Would you like a step-by-step tutorial?",
          confidence: 0.75,
          reasoning: "User asked for guidance",
        });
      }

      if (c.includes("example") || c.includes("show me")) {
        out.push({
          id: "action-example",
          type: "action",
          text: "Can you show me a practical example?",
          confidence: 0.8,
          reasoning: "User requested examples",
        });
      }

      if (c.includes("best") || c.includes("recommend")) {
        out.push({
          id: "action-recommend",
          type: "action",
          text: "What are the best practices for this?",
          confidence: 0.72,
          reasoning: "User seeking recommendations",
        });
      }
    }

    return out.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)).slice(0, maxSuggestions);
  }, [messages, conversationContext, maxSuggestions]);

  useEffect(() => {
    let isActive = true;

    void Promise.resolve().then(() => {
      if (isActive) {
        setIsGenerating(true);
      }
    });

    const timer = setTimeout(() => {
      if (!isActive) {
        return;
      }
      setSuggestions(generatedSuggestions);
      setIsGenerating(false);
    }, 300);

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, [generatedSuggestions]);

  const getSuggestionIcon = (type: ContextSuggestion["type"]) => {
    switch (type) {
      case "follow_up":
        return ArrowRight;
      case "clarification":
        return HelpCircle;
      case "related_topic":
        return Brain;
      case "action":
        return Zap;
      default:
        return Lightbulb;
    }
  };

  const getSuggestionBadgeVariant = (confidence: number | undefined) => {
    const c = confidence ?? 0;
    if (c >= 0.8) return "default" as const;
    if (c >= 0.6) return "secondary" as const;
    return "outline" as const;
  };

  if (suggestions.length === 0 && !isGenerating) {
    return null;
  }

  return (
    <Card className={className}>
      <CardContent className="p-4 sm:p-4 md:p-6">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="h-4 w-4 text-primary" />
          <h3 className="font-medium text-sm md:text-base lg:text-lg">Smart Suggestions</h3>
          {isGenerating && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              Generating…
            </div>
          )}
        </div>

        {isGenerating ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <ScrollArea className="max-h-48">
            <div className="space-y-2">
              {suggestions.map((s) => {
                const Icon = getSuggestionIcon(s.type);
                return (
                  <Button
                    key={s.id}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start h-auto p-3 text-left hover:bg-muted/50 sm:p-4 md:p-6"
                    onClick={() => onSuggestionSelect(s)}
                    aria-label={`Suggestion: ${s.text}`}
                  >
                    <div className="flex items-start gap-3 w-full">
                      <Icon className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-left md:text-base lg:text-lg">
                          {s.text}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            variant={getSuggestionBadgeVariant(s.confidence)}
                            className="text-xs sm:text-sm md:text-base"
                          >
                            {s.type.replace("_", " ")}
                          </Badge>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
                            <TrendingUp className="h-3 w-3" />
                            {Math.round((s.confidence ?? 0) * 100)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </Button>
                );
              })}
            </div>
          </ScrollArea>
        )}

        {suggestions.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Context-aware prompts generated from recent messages, topic, memory relevance, and learned user patterns.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ContextSuggestions;
