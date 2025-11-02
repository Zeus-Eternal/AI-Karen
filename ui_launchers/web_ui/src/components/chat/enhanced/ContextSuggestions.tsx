
"use client";
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';


import { } from 'lucide-react';

import { } from '@/types/enhanced-chat';

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
  className = '',
  maxSuggestions = 6
}) => {
  const [suggestions, setSuggestions] = useState<ContextSuggestion[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Generate context-aware suggestions based on conversation state
  const generateSuggestions = useMemo(() => {
    const lastMessage = messages[messages.length - 1];
    const recentMessages = messages.slice(-5);
    const currentTopic = conversationContext.currentThread.topic;
    const userPatterns = conversationContext.userPatterns;

    const suggestions: ContextSuggestion[] = [];

    // Follow-up suggestions based on last message
    if (lastMessage && lastMessage.role === 'assistant') {
      if (lastMessage.content.includes('code') || lastMessage.type === 'code') {
        suggestions.push({
          id: 'follow-up-code-1',
          type: 'follow_up',
          text: 'Can you explain this code in more detail?',
          confidence: 0.85,
          reasoning: 'User received code and might need explanation'

        suggestions.push({
          id: 'follow-up-code-2',
          type: 'follow_up',
          text: 'How can I modify this code for my use case?',
          confidence: 0.80,
          reasoning: 'Common follow-up for code examples'

      }

      if (lastMessage.content.includes('error') || lastMessage.content.includes('problem')) {
        suggestions.push({
          id: 'follow-up-error-1',
          type: 'follow_up',
          text: 'What are some alternative approaches?',
          confidence: 0.75,
          reasoning: 'User encountered an issue and might need alternatives'

      }
    }

    // Clarification suggestions based on conversation complexity
    if (conversationContext.currentThread.metadata.complexity === 'complex') {
      suggestions.push({
        id: 'clarification-1',
        type: 'clarification',
        text: 'Can you break this down into simpler steps?',
        confidence: 0.70,
        reasoning: 'Complex conversation might benefit from simplification'

      suggestions.push({
        id: 'clarification-2',
        type: 'clarification',
        text: 'What are the key points I should focus on?',
        confidence: 0.68,
        reasoning: 'Help user focus on important aspects'

    }

    // Topic-related suggestions
    if (currentTopic) {
      suggestions.push({
        id: 'related-topic-1',
        type: 'related_topic',
        text: `Tell me more about ${currentTopic}`,
        confidence: 0.65,
        reasoning: 'Expand on current topic of discussion'

    }

    // Pattern-based suggestions from user behavior
    userPatterns.forEach((pattern, index) => {
      if (pattern.type === 'preference' && pattern.confidence > 0.7) {
        suggestions.push({
          id: `pattern-${index}`,
          type: 'action',
          text: `Would you like help with ${pattern.pattern}?`,
          confidence: pattern.confidence * 0.8,
          reasoning: `Based on user's preference pattern: ${pattern.pattern}`

      }

    // Memory-based suggestions
    if (conversationContext.memoryContext.relevantMemories.length > 0) {
      const topMemory = conversationContext.memoryContext.relevantMemories[0];
      suggestions.push({
        id: 'memory-1',
        type: 'related_topic',
        text: 'This reminds me of something we discussed before...',
        confidence: topMemory.relevance * 0.9,
        reasoning: 'Reference to relevant past conversation'

    }

    // Action suggestions based on message content
    const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMessage) {
      const content = lastUserMessage.content.toLowerCase();
      
      if (content.includes('how') || content.includes('tutorial')) {
        suggestions.push({
          id: 'action-tutorial',
          type: 'action',
          text: 'Would you like a step-by-step tutorial?',
          confidence: 0.75,
          reasoning: 'User asking for guidance'

      }
      
      if (content.includes('example') || content.includes('show me')) {
        suggestions.push({
          id: 'action-example',
          type: 'action',
          text: 'Can you show me a practical example?',
          confidence: 0.80,
          reasoning: 'User requesting examples'

      }
      
      if (content.includes('best') || content.includes('recommend')) {
        suggestions.push({
          id: 'action-recommend',
          type: 'action',
          text: 'What are the best practices for this?',
          confidence: 0.72,
          reasoning: 'User seeking recommendations'

      }
    }

    // Sort by confidence and limit
    return suggestions
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, maxSuggestions);
  }, [messages, conversationContext, maxSuggestions]);

  useEffect(() => {
    setIsGenerating(true);
    // Simulate suggestion generation delay
    const timer = setTimeout(() => {
      setSuggestions(generateSuggestions);
      setIsGenerating(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [generateSuggestions]);

  const getSuggestionIcon = (type: ContextSuggestion['type']) => {
    switch (type) {
      case 'follow_up':
        return ArrowRight;
      case 'clarification':
        return HelpCircle;
      case 'related_topic':
        return Brain;
      case 'action':
        return Zap;
      default:
        return Lightbulb;
    }
  };

  const getSuggestionColor = (confidence: number) => {
    if (confidence >= 0.8) return 'default';
    if (confidence >= 0.6) return 'secondary';
    return 'outline';
  };

  if (suggestions.length === 0 && !isGenerating) {
    return null;
  }

  return (
    <Card className={`${className}`}>
      <CardContent className="p-4 sm:p-4 md:p-6">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="h-4 w-4 text-primary " />
          <h3 className="font-medium text-sm md:text-base lg:text-lg">Smart Suggestions</h3>
          {isGenerating && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse "></div>
              Generating...
            </div>
          )}
        </div>

        {isGenerating ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-muted rounded animate-pulse"></div>
            ))}
          </div>
        ) : (
          <ScrollArea className="max-h-48">
            <div className="space-y-2">
              {suggestions.map((suggestion) => {
                const Icon = getSuggestionIcon(suggestion.type);
                return (
                  <Button
                    key={suggestion.id}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start h-auto p-3 text-left hover:bg-muted/50 sm:p-4 md:p-6"
                    onClick={() => onSuggestionSelect(suggestion)}
                  >
                    <div className="flex items-start gap-3 w-full">
                      <Icon className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground " />
                      <div className="flex-1 min-w-0 ">
                        <p className="text-sm font-medium text-left md:text-base lg:text-lg">
                          {suggestion.text}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge 
                            variant={getSuggestionColor(suggestion.confidence)} 
                            className="text-xs sm:text-sm md:text-base"
                          >
                            {suggestion.type.replace('_', ' ')}
                          </Badge>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground sm:text-sm md:text-base">
                            <TrendingUp className="h-3 w-3 " />
                            {Math.round(suggestion.confidence * 100)}%
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
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ContextSuggestions;