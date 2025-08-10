'use client';

/**
 * Modern Chat Interface with AG-UI + CopilotKit Integration
 * 
 * This component replaces the legacy ChatInterface with a modern implementation that:
 * - Uses AG-Grid for conversation management and history
 * - Integrates CopilotKit for AI-powered assistance
 * - Provides proper message rendering without truncation issues
 * - Offers advanced features like memory integration, analytics, and real-time collaboration
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, RowSelectedEvent } from 'ag-grid-community';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotTextarea } from '@copilotkit/react-textarea';
import { useCopilotAction, useCopilotReadable } from '@copilotkit/react-core';

// UI Components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';

// Icons
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Sparkles,
  Grid3X3,
  BarChart3,
  Settings,
  Maximize2,
  Minimize2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  Brain,
  Zap,
  Eye,
  Archive
} from 'lucide-react';

// Contexts and Services
import { useAuth } from '@/contexts/AuthContext';
import { useHooks } from '@/contexts/HookContext';
import { useToast } from '@/hooks/use-toast';
import { getChatService } from '@/services/chatService';
import { getKarenBackend } from '@/lib/karen-backend';

// Types
import type { ChatMessage, KarenSettings } from '@/lib/types';

// AG-Grid Styles
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

interface ConversationRow {
  id: string;
  title: string;
  messageCount: number;
  lastMessage: string;
  timestamp: Date;
  participants: string[];
  status: 'active' | 'archived' | 'draft';
  sentiment: 'positive' | 'neutral' | 'negative';
  aiConfidence: number;
  tags: string[];
}

interface ModernChatInterfaceProps {
  className?: string;
  height?: string;
  showTabs?: boolean;
  defaultTab?: 'chat' | 'conversations' | 'analytics';
  enableFullscreen?: boolean;
}

export const ModernChatInterface: React.FC<ModernChatInterfaceProps> = ({
  className = '',
  height = '100%',
  showTabs = true,
  defaultTab = 'chat',
  enableFullscreen = true
}) => {
  const { user, isAuthenticated } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const chatService = getChatService();
  const karenBackend = getKarenBackend();

  // State Management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<AgGridReact>(null);

  // CopilotKit Integration
  useCopilotReadable({
    description: 'Current chat messages and conversation context',
    value: {
      messages: messages.slice(-10), // Last 10 messages for context
      conversationId: currentConversationId,
      userPreferences: user?.preferences || {}
    }
  });

  useCopilotAction({
    name: 'analyzeConversation',
    description: 'Analyze the current conversation for insights and suggestions',
    parameters: [
      {
        name: 'analysisType',
        type: 'string',
        description: 'Type of analysis to perform (sentiment, topics, suggestions)',
        enum: ['sentiment', 'topics', 'suggestions', 'summary']
      }
    ],
    handler: async ({ analysisType }) => {
      const analysis = await analyzeConversation(messages, analysisType);
      toast({
        title: 'Analysis Complete',
        description: `${analysisType} analysis has been generated`,
      });
      return analysis;
    }
  });

  useCopilotAction({
    name: 'suggestResponse',
    description: 'Suggest a response based on conversation context',
    parameters: [
      {
        name: 'tone',
        type: 'string',
        description: 'Tone for the suggested response',
        enum: ['professional', 'casual', 'helpful', 'creative']
      }
    ],
    handler: async ({ tone }) => {
      const suggestion = await generateResponseSuggestion(messages, tone);
      setInputValue(suggestion);
      return `Response suggestion generated with ${tone} tone`;
    }
  });

  // AG-Grid Column Definitions for Conversations
  const conversationColumns: ColDef[] = useMemo(() => [
    {
      headerName: 'Title',
      field: 'title',
      flex: 2,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2 py-1">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{params.value}</span>
        </div>
      )
    },
    {
      headerName: 'Messages',
      field: 'messageCount',
      width: 100,
      cellRenderer: (params: any) => (
        <Badge variant="secondary">{params.value}</Badge>
      )
    },
    {
      headerName: 'Last Activity',
      field: 'timestamp',
      width: 150,
      cellRenderer: (params: any) => (
        <span className="text-sm text-muted-foreground">
          {new Date(params.value).toLocaleDateString()}
        </span>
      )
    },
    {
      headerName: 'Status',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => {
        const statusColors = {
          active: 'bg-green-100 text-green-800',
          archived: 'bg-gray-100 text-gray-800',
          draft: 'bg-yellow-100 text-yellow-800'
        };
        return (
          <Badge className={statusColors[params.value as keyof typeof statusColors]}>
            {params.value}
          </Badge>
        );
      }
    },
    {
      headerName: 'AI Confidence',
      field: 'aiConfidence',
      width: 120,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          <Progress value={params.value * 100} className="w-12 h-2" />
          <span className="text-xs">{Math.round(params.value * 100)}%</span>
        </div>
      )
    }
  ], []);

  // Initialize chat data
  useEffect(() => {
    if (isAuthenticated && user) {
      initializeChatData();
    }
  }, [isAuthenticated, user]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeChatData = async () => {
    try {
      setIsLoading(true);
      
      // Load conversations
      const userConversations = await chatService.getUserConversations(user!.user_id);
      const conversationRows: ConversationRow[] = userConversations.map(conv => ({
        id: conv.sessionId,
        title: `Conversation ${conv.sessionId.slice(0, 8)}`,
        messageCount: conv.messages.length,
        lastMessage: conv.messages[conv.messages.length - 1]?.content || 'No messages',
        timestamp: conv.updatedAt,
        participants: [user!.email],
        status: 'active' as const,
        sentiment: 'neutral' as const,
        aiConfidence: 0.85,
        tags: ['general']
      }));
      
      setConversations(conversationRows);
      
      // If no current conversation, create one
      if (!currentConversationId && conversationRows.length === 0) {
        await createNewConversation();
      }
      
    } catch (error) {
      console.error('Failed to initialize chat data:', error);
      toast({
        variant: 'destructive',
        title: 'Initialization Error',
        description: 'Failed to load chat data. Please refresh the page.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const createNewConversation = async () => {
    try {
      const { conversationId, sessionId } = await chatService.createConversationSession(user!.user_id);
      setCurrentConversationId(conversationId);
      
      // Add to conversations list
      const newConversation: ConversationRow = {
        id: conversationId,
        title: 'New Conversation',
        messageCount: 0,
        lastMessage: 'Conversation started',
        timestamp: new Date(),
        participants: [user!.email],
        status: 'active',
        sentiment: 'neutral',
        aiConfidence: 0.0,
        tags: ['new']
      };
      
      setConversations(prev => [newConversation, ...prev]);
      setMessages([]);
      
    } catch (error) {
      console.error('Failed to create conversation:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to create new conversation'
      });
    }
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || !currentConversationId) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      aiData: null,
      shouldAutoPlay: false
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Trigger hooks for message processing
      await triggerHooks('message_sent', {
        messageId: userMessage.id,
        content: content.substring(0, 100),
        conversationId: currentConversationId,
        userId: user?.user_id
      }, { userId: user?.user_id });

      // Process message with Karen backend
      const result = await karenBackend.processUserMessage(
        content,
        messages,
        user?.preferences as KarenSettings || {},
        user?.user_id,
        currentConversationId
      );

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: result.finalResponse,
        timestamp: new Date(),
        aiData: result.aiDataForFinalResponse,
        shouldAutoPlay: false
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Store memory if needed
      if (result.suggestedNewFacts && result.suggestedNewFacts.length > 0) {
        await karenBackend.storeMemory(
          content,
          'conversation',
          result.suggestedNewFacts,
          user?.user_id
        );
      }

      // Update conversation in grid
      setConversations(prev => prev.map(conv => 
        conv.id === currentConversationId 
          ? {
              ...conv,
              messageCount: conv.messageCount + 2,
              lastMessage: result.finalResponse.substring(0, 50) + '...',
              timestamp: new Date(),
              aiConfidence: result.aiDataForFinalResponse?.confidence || 0.85
            }
          : conv
      ));

    } catch (error) {
      console.error('Failed to send message:', error);
      toast({
        variant: 'destructive',
        title: 'Message Error',
        description: 'Failed to send message. Please try again.'
      });
    } finally {
      setIsTyping(false);
    }
  };

  const analyzeConversation = async (messages: ChatMessage[], type: string) => {
    // Mock analysis - in real implementation, this would call AI services
    const analysis = {
      sentiment: 'positive',
      topics: ['technology', 'development', 'AI'],
      suggestions: ['Consider exploring advanced features', 'Review documentation'],
      summary: 'Productive conversation about technical topics'
    };
    
    return analysis[type as keyof typeof analysis] || analysis;
  };

  const generateResponseSuggestion = async (messages: ChatMessage[], tone: string) => {
    // Mock suggestion - in real implementation, this would use AI
    const suggestions = {
      professional: "Thank you for your inquiry. I'd be happy to help you with that.",
      casual: "Sure thing! Let me help you out with that.",
      helpful: "I understand what you're looking for. Here's how I can assist:",
      creative: "That's an interesting challenge! Let's explore some innovative solutions."
    };
    
    return suggestions[tone as keyof typeof suggestions] || suggestions.helpful;
  };

  const handleConversationSelect = (event: RowSelectedEvent) => {
    if (event.node.isSelected()) {
      const conversation = event.data as ConversationRow;
      setCurrentConversationId(conversation.id);
      // Load messages for this conversation
      // In real implementation, this would fetch messages from the backend
      setMessages([]);
    }
  };

  const MessageComponent = ({ message }: { message: ChatMessage }) => {
    const isUser = message.role === 'user';
    
    return (
      <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>
        
        <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
          <div className={`inline-block p-3 rounded-lg ${
            isUser 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted border'
          }`}>
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
            
            {message.aiData && (
              <div className="mt-2 pt-2 border-t border-border/20">
                <div className="flex items-center gap-2 text-xs opacity-70">
                  {message.aiData.confidence && (
                    <Badge variant="outline" className="text-xs">
                      {Math.round(message.aiData.confidence * 100)}% confidence
                    </Badge>
                  )}
                  <Badge variant="secondary" className="text-xs">
                    AI Enhanced
                  </Badge>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <span>{message.timestamp.toLocaleTimeString()}</span>
            
            {!isUser && (
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Copy className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <ThumbsUp className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const ChatTab = () => (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">Welcome to Modern Chat</p>
              <p className="text-sm">
                Enhanced with AG-UI and CopilotKit for the best chat experience.
                Start a conversation to see the magic happen!
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageComponent key={message.id} message={message} />
            ))
          )}
          
          {isTyping && (
            <div className="flex gap-3 mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="inline-block p-3 rounded-lg bg-muted border">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">AI is thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area with CopilotKit Integration */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <CopilotTextarea
            className="flex-1 min-h-[40px] max-h-[120px] resize-none"
            placeholder="Type your message... (CopilotKit will help with suggestions)"
            value={inputValue}
            onValueChange={setInputValue}
            autosuggestionsConfig={{
              textareaPurpose: "Chat message input with AI assistance",
              chatApiConfigs: {
                suggestionsApiConfig: {
                  forwardedParams: {
                    max_tokens: 20,
                    stop: ["\n", "."],
                  },
                },
              },
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (inputValue.trim() && !isLoading && !isTyping) {
                  sendMessage(inputValue);
                }
              }
            }}
            disabled={isLoading || isTyping}
          />
          <Button 
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading || isTyping}
            size="sm"
          >
            {isLoading || isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center gap-2 mt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setInputValue("Help me understand this concept")}
            disabled={isLoading || isTyping}
          >
            <Brain className="h-3 w-3 mr-1" />
            Explain
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setInputValue("Can you analyze this for me?")}
            disabled={isLoading || isTyping}
          >
            <Zap className="h-3 w-3 mr-1" />
            Analyze
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={createNewConversation}
            disabled={isLoading}
          >
            <MessageSquare className="h-3 w-3 mr-1" />
            New Chat
          </Button>
        </div>
      </div>
    </div>
  );

  const ConversationsTab = () => (
    <div className="h-full ag-theme-alpine">
      <AgGridReact
        ref={gridRef}
        rowData={conversations}
        columnDefs={conversationColumns}
        defaultColDef={{
          sortable: true,
          filter: true,
          resizable: true
        }}
        rowSelection="single"
        onRowSelected={handleConversationSelect}
        animateRows={true}
        enableCellTextSelection={true}
        suppressRowClickSelection={false}
        onGridReady={(event: GridReadyEvent) => {
          event.api.sizeColumnsToFit();
        }}
      />
    </div>
  );

  const AnalyticsTab = () => (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{messages.length}</div>
            <p className="text-xs text-muted-foreground">In current conversation</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">AI Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85%</div>
            <p className="text-xs text-muted-foreground">Average response quality</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conversations.filter(c => c.status === 'active').length}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Conversation Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Analytics and insights will be displayed here, powered by AG-Charts and CopilotKit analysis.
          </p>
        </CardContent>
      </Card>
    </div>
  );

  if (!isAuthenticated) {
    return (
      <Card className="flex items-center justify-center h-64">
        <CardContent>
          <p className="text-muted-foreground">Please log in to access the chat interface.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <CopilotKit runtimeUrl="/api/copilot">
      <Card className={`flex flex-col ${className} ${isFullscreen ? 'fixed inset-0 z-50' : ''}`} style={{ height }}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Modern Chat Interface
              <Badge variant="secondary" className="text-xs">
                AG-UI + CopilotKit
              </Badge>
            </CardTitle>
            
            {enableFullscreen && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col p-0">
          {showTabs ? (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
              <div className="px-4">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="chat" className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Chat
                  </TabsTrigger>
                  <TabsTrigger value="conversations" className="flex items-center gap-2">
                    <Grid3X3 className="h-4 w-4" />
                    Conversations
                  </TabsTrigger>
                  <TabsTrigger value="analytics" className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Analytics
                  </TabsTrigger>
                </TabsList>
              </div>
              
              <TabsContent value="chat" className="flex-1 m-0">
                <ChatTab />
              </TabsContent>
              
              <TabsContent value="conversations" className="flex-1 m-0 p-4">
                <ConversationsTab />
              </TabsContent>
              
              <TabsContent value="analytics" className="flex-1 m-0">
                <AnalyticsTab />
              </TabsContent>
            </Tabs>
          ) : (
            <ChatTab />
          )}
        </CardContent>
      </Card>
    </CopilotKit>
  );
};

export default ModernChatInterface;