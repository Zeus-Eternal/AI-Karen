'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Brain,
  Sparkles,
  Settings,
  MoreHorizontal,
  PanelRightOpen,
  PanelRightClose
} from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import {
  EnhancedChatMessage,
  ConversationContext,
  ConversationThread,
  ContextSuggestion,
  ConversationExport,
  ConversationShare,
  EnhancedChatInterfaceProps
} from '@/types/enhanced-chat';
import ContextPanel from './ContextPanel';
import ContextSuggestions from './ContextSuggestions';
import ConversationThreading from './ConversationThreading';
import ConversationExportShare from './ConversationExportShare';

export const EnhancedChatInterface: React.FC<EnhancedChatInterfaceProps> = ({
  conversationId,
  initialMessages = [],
  enableContextPanel = true,
  enableSuggestions = true,
  enableThreading = true,
  enableMemoryIntegration = true,
  enableFileUpload = false,
  enableImageAnalysis = false,
  enableVoiceInput = false,
  enableReasoning = true,
  enableExport = true,
  enableSharing = true,
  onMessageSent,
  onMessageReceived,
  onContextChange,
  onExport,
  onShare,
  className = '',
  height = '600px',
  theme = 'auto'
}) => {
  const { toast } = useToast();
  
  // State management
  const [messages, setMessages] = useState<EnhancedChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showContextPanel, setShowContextPanel] = useState(enableContextPanel);
  const [activeThreadId, setActiveThreadId] = useState<string>(conversationId || 'default');
  
  // Mock conversation context - in real implementation, this would come from API/store
  const [conversationContext, setConversationContext] = useState<ConversationContext>({
    currentThread: {
      id: activeThreadId,
      title: 'Current Conversation',
      topic: 'General Discussion',
      messages: messages,
      participants: ['user', 'assistant'],
      createdAt: new Date(),
      updatedAt: new Date(),
      status: 'active',
      metadata: {
        messageCount: messages.length,
        averageResponseTime: 1200,
        topicDrift: 0.2,
        sentiment: 'neutral',
        complexity: 'medium',
        tags: ['general', 'ai-assistance'],
        summary: 'Ongoing conversation with AI assistant'
      }
    },
    relatedThreads: [
      {
        id: 'thread-1',
        title: 'Previous Discussion',
        topic: 'Technical Help',
        messages: [],
        participants: ['user', 'assistant'],
        createdAt: new Date(Date.now() - 86400000),
        updatedAt: new Date(Date.now() - 3600000),
        status: 'archived',
        metadata: {
          messageCount: 15,
          averageResponseTime: 800,
          topicDrift: 0.1,
          sentiment: 'positive',
          complexity: 'complex',
          tags: ['technical', 'problem-solving'],
          summary: 'Resolved technical issue with detailed explanation'
        }
      }
    ],
    userPatterns: [
      {
        type: 'preference',
        pattern: 'detailed explanations',
        confidence: 0.85,
        frequency: 12,
        lastSeen: new Date()
      },
      {
        type: 'behavior',
        pattern: 'asks follow-up questions',
        confidence: 0.92,
        frequency: 8,
        lastSeen: new Date()
      }
    ],
    sessionContext: {
      sessionId: 'session-123',
      startTime: new Date(),
      duration: 1800000, // 30 minutes
      messageCount: messages.length,
      topics: ['ai', 'assistance', 'conversation'],
      mood: 'engaged',
      focus: ['learning', 'problem-solving']
    },
    memoryContext: {
      recentMemories: [
        {
          id: 'mem-1',
          type: 'episodic',
          content: 'User prefers step-by-step explanations',
          relevance: 0.9,
          timestamp: new Date(),
          source: 'conversation-analysis'
        }
      ],
      relevantMemories: [
        {
          id: 'mem-2',
          type: 'semantic',
          content: 'User has experience with React development',
          relevance: 0.75,
          timestamp: new Date(Date.now() - 86400000),
          source: 'previous-conversation'
        }
      ],
      memoryStats: {
        totalMemories: 45,
        relevantCount: 8,
        averageRelevance: 0.72
      }
    }
  });

  // Update conversation context when messages change
  useEffect(() => {
    setConversationContext(prev => ({
      ...prev,
      currentThread: {
        ...prev.currentThread,
        messages: messages,
        updatedAt: new Date(),
        metadata: {
          ...prev.currentThread.metadata,
          messageCount: messages.length
        }
      }
    }));
    
    onContextChange?.(conversationContext);
  }, [messages, onContextChange]);

  // Handle message submission
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: EnhancedChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      type: 'text',
      status: 'sent',
      context: {
        conversationId: activeThreadId,
        topics: ['user-query'],
        intent: 'question'
      },
      metadata: {
        suggestions: []
      }
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    onMessageSent?.(userMessage);

    try {
      // Simulate AI response - in real implementation, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const assistantMessage: EnhancedChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: `I understand you're asking about "${userMessage.content}". Let me help you with that. This is a simulated response that demonstrates the enhanced chat interface with context awareness and reasoning capabilities.`,
        timestamp: new Date(),
        type: 'text',
        status: 'completed',
        confidence: 0.87,
        context: {
          conversationId: activeThreadId,
          topics: ['ai-response', 'assistance'],
          intent: 'helpful-response',
          memoryReferences: conversationContext.memoryContext.relevantMemories.slice(0, 2)
        },
        reasoning: {
          steps: [
            {
              id: 'step-1',
              description: 'Analyzed user query for intent and context',
              type: 'analysis',
              confidence: 0.9,
              evidence: ['User message content', 'Conversation history'],
              timestamp: new Date()
            },
            {
              id: 'step-2',
              description: 'Retrieved relevant information from memory',
              type: 'retrieval',
              confidence: 0.85,
              evidence: ['User preferences', 'Previous conversations'],
              timestamp: new Date()
            },
            {
              id: 'step-3',
              description: 'Synthesized response based on context',
              type: 'synthesis',
              confidence: 0.87,
              evidence: ['Context analysis', 'Memory retrieval'],
              timestamp: new Date()
            }
          ],
          confidence: 0.87,
          sources: [
            {
              id: 'source-1',
              type: 'memory',
              title: 'User Preferences',
              reliability: 0.9,
              relevance: 0.85,
              snippet: 'User prefers detailed explanations'
            }
          ],
          methodology: 'Context-aware response generation with memory integration'
        },
        metadata: {
          model: 'enhanced-ai-v1',
          provider: 'kari-ai',
          tokens: 150,
          cost: 0.002,
          latency: 1200,
          suggestions: [
            {
              id: 'sug-1',
              type: 'follow_up',
              text: 'Would you like me to explain this in more detail?',
              confidence: 0.8,
              reasoning: 'User typically asks for detailed explanations'
            },
            {
              id: 'sug-2',
              type: 'related_topic',
              text: 'Are you interested in related topics?',
              confidence: 0.7,
              reasoning: 'Based on conversation context'
            }
          ]
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
      onMessageReceived?.(assistantMessage);
      
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Message Failed',
        description: 'Failed to send message. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, activeThreadId, conversationContext, onMessageSent, onMessageReceived, toast]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: ContextSuggestion) => {
    setInputValue(suggestion.text);
  }, []);

  // Handle thread operations
  const handleThreadSelect = useCallback((threadId: string) => {
    setActiveThreadId(threadId);
    // In real implementation, load thread messages
    toast({
      title: 'Thread Selected',
      description: `Switched to conversation thread: ${threadId}`
    });
  }, [toast]);

  const handleThreadCreate = useCallback((topic: string) => {
    const newThreadId = `thread-${Date.now()}`;
    setActiveThreadId(newThreadId);
    setMessages([]);
    toast({
      title: 'New Conversation',
      description: `Started new conversation about: ${topic}`
    });
  }, [toast]);

  const handleThreadUpdate = useCallback((threadId: string, updates: Partial<ConversationThread>) => {
    toast({
      title: 'Thread Updated',
      description: 'Conversation thread has been updated'
    });
  }, [toast]);

  const handleThreadDelete = useCallback((threadId: string) => {
    toast({
      title: 'Thread Deleted',
      description: 'Conversation thread has been deleted'
    });
  }, [toast]);

  const handleThreadArchive = useCallback((threadId: string) => {
    toast({
      title: 'Thread Archived',
      description: 'Conversation thread has been archived'
    });
  }, [toast]);

  // Handle export and share
  const handleExport = useCallback(async (config: ConversationExport) => {
    if (onExport) {
      await onExport(config);
    } else {
      // Default export behavior
      const exportData = {
        thread: conversationContext.currentThread,
        messages: messages,
        config: config,
        exportedAt: new Date()
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${activeThreadId}.${config.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [conversationContext, messages, activeThreadId, onExport]);

  const handleShare = useCallback(async (config: ConversationShare): Promise<string> => {
    if (onShare) {
      onShare(config);
      // Generate a mock URL since onShare doesn't return one
      const shareId = `share-${Date.now()}`;
      return `https://app.kari-ai.com/shared/${shareId}`;
    } else {
      // Mock share URL generation
      const shareId = `share-${Date.now()}`;
      return `https://app.kari-ai.com/shared/${shareId}`;
    }
  }, [onShare]);

  // Render message bubble
  const renderMessage = (message: EnhancedChatMessage) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={message.id} className={`flex gap-3 mb-4 ${isUser ? 'justify-end' : ''}`}>
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary" />
          </div>
        )}
        
        <div className={`flex-1 max-w-[80%] ${isUser ? 'flex justify-end' : ''}`}>
          <div className={`p-3 rounded-lg ${
            isUser 
              ? 'bg-primary text-primary-foreground ml-auto' 
              : 'bg-muted border'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            
            {/* Message metadata */}
            <div className="flex items-center gap-2 mt-2 text-xs opacity-70">
              <span>{format(message.timestamp, 'HH:mm')}</span>
              
              {message.confidence && (
                <Badge variant="secondary" className="text-xs">
                  {Math.round(message.confidence * 100)}% confident
                </Badge>
              )}
              
              {message.metadata?.model && (
                <Badge variant="outline" className="text-xs">
                  {message.metadata.model}
                </Badge>
              )}
            </div>
          </div>
        </div>
        
        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <User className="h-4 w-4" />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full ${className}`} style={{ height }}>
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Main Chat Area */}
        <ResizablePanel defaultSize={showContextPanel ? 70 : 100} minSize={50}>
          <Card className="h-full flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Enhanced Chat
                  <Badge variant="secondary" className="text-xs">
                    <Brain className="h-3 w-3 mr-1" />
                    Context-Aware
                  </Badge>
                </CardTitle>
                
                <div className="flex items-center gap-2">
                  {enableExport && enableSharing && (
                    <ConversationExportShare
                      thread={conversationContext.currentThread}
                      onExport={handleExport}
                      onShare={handleShare}
                    />
                  )}
                  
                  {enableContextPanel && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowContextPanel(!showContextPanel)}
                    >
                      {showContextPanel ? (
                        <PanelRightClose className="h-4 w-4" />
                      ) : (
                        <PanelRightOpen className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0">
              {/* Messages Area */}
              <ScrollArea className="flex-1 px-4">
                <div className="py-4">
                  {messages.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <div className="flex items-center justify-center gap-2 mb-4">
                        <Bot className="h-12 w-12 opacity-50" />
                        <Sparkles className="h-8 w-8 text-primary" />
                      </div>
                      <p className="text-lg font-medium mb-2">Enhanced AI Chat</p>
                      <p className="text-sm">
                        Start a conversation with context-aware AI assistance
                      </p>
                    </div>
                  ) : (
                    messages.map(renderMessage)
                  )}
                  
                  {isLoading && (
                    <div className="flex gap-3 mb-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="inline-block p-3 rounded-lg bg-muted border">
                          <div className="flex items-center gap-2">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                            <span className="text-sm text-muted-foreground">AI is thinking...</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Suggestions */}
              {enableSuggestions && messages.length > 0 && (
                <div className="px-4 pb-2">
                  <ContextSuggestions
                    messages={messages}
                    conversationContext={conversationContext}
                    onSuggestionSelect={handleSuggestionSelect}
                    maxSuggestions={3}
                  />
                </div>
              )}

              {/* Input Area */}
              <div className="p-4 border-t">
                <div className="flex gap-2">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    size="sm"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </ResizablePanel>

        {/* Context Panel */}
        {showContextPanel && enableContextPanel && (
          <>
            <ResizableHandle />
            <ResizablePanel defaultSize={30} minSize={25} maxSize={50}>
              <div className="h-full flex flex-col gap-4 p-4">
                {/* Threading */}
                {enableThreading && (
                  <div className="flex-1">
                    <ConversationThreading
                      threads={[conversationContext.currentThread, ...conversationContext.relatedThreads]}
                      activeThreadId={activeThreadId}
                      onThreadSelect={handleThreadSelect}
                      onThreadCreate={handleThreadCreate}
                      onThreadUpdate={handleThreadUpdate}
                      onThreadDelete={handleThreadDelete}
                      onThreadArchive={handleThreadArchive}
                    />
                  </div>
                )}
                
                <Separator />
                
                {/* Context Panel */}
                <div className="flex-1">
                  <ContextPanel
                    conversation={conversationContext}
                    onThreadSelect={handleThreadSelect}
                    onMemorySelect={(memoryId) => {
                      toast({
                        title: 'Memory Selected',
                        description: `Viewing memory: ${memoryId}`
                      });
                    }}
                    onSuggestionSelect={handleSuggestionSelect}
                  />
                </div>
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>
    </div>
  );
};

export default EnhancedChatInterface;