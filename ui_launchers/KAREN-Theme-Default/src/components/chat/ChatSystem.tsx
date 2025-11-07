"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent } from 'ag-grid-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Grid3X3, BarChart3, Sparkles, Brain, Bot, Zap, Database } from 'lucide-react';
import { ChatBubble } from './ChatBubble';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { getChatService } from '@/services/chatService';
import { format } from 'date-fns';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { safeError } from '@/lib/safe-console';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  confidence?: number;
  aiData?: {
    keywords?: string[];
    reasoning?: string;
    sources?: string[];
  };
}

interface ConversationData {
  id: string;
  title: string;
  messageCount: number;
  lastActivity: Date;
  status: 'active' | 'archived';
  sentiment: 'positive' | 'neutral' | 'negative';
}

interface ChatSystemProps {
  className?: string;
  defaultView?: 'chat' | 'conversations' | 'analytics';
}

export const ChatSystem: React.FC<ChatSystemProps> = ({
  className = '',
  defaultView = 'chat'
}) => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const chatService = getChatService();
  
  const [activeView, setActiveView] = useState(defaultView);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<ConversationData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<AgGridReact>(null);

  // Initialize chat session
  useEffect(() => {
    const initializeChat = async () => {
      if (user && !sessionId && !conversationId) {
        try {
          const { conversationId: newConversationId, sessionId: newSessionId } = 
            await chatService.createConversationSession(user.userId);
          setSessionId(newSessionId);
          setConversationId(newConversationId);
        } catch (error) {
          safeError('Failed to initialize chat session:', error);
          toast({
            variant: 'destructive',
            title: 'Chat Initialization Failed',
            description: 'Unable to start chat session. Please refresh and try again.'
          });
        }
      }
    };

    if (isAuthenticated) {
      initializeChat();
    }
  }, [user, isAuthenticated, sessionId, conversationId, chatService, toast]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load conversations for grid view
  useEffect(() => {
    const loadConversations = async () => {
      if (user && activeView === 'conversations') {
        try {
          const userConversations = await chatService.getUserConversations(user.userId);
          const conversationData: ConversationData[] = userConversations.map(conv => ({
            id: conv.sessionId,
            title: `Conversation ${conv.sessionId.slice(0, 8)}`,
            messageCount: conv.messages.length,
            lastActivity: conv.updatedAt,
            status: 'active' as const,
            sentiment: 'neutral' as const
          }));
          setConversations(conversationData);
        } catch (error) {
          safeError('Failed to load conversations:', error);
        }
      }
    };

    loadConversations();
  }, [user, activeView, chatService]);

  // Handle message submission
  const handleSubmit = useCallback(async (message: string) => {
    if (!message.trim() || !user || !conversationId) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Add message to conversation
      await chatService.addMessageToConversation(conversationId, userMessage);

      // Process message with AI
      const result = await chatService.processUserMessage(
        message,
        messages,
        {} as any, // Preferences not available in simplified mode
        { userId: user.userId, sessionId: sessionId || undefined }
      );

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: result.finalResponse,
        timestamp: new Date(),
        confidence: result.aiDataForFinalResponse?.confidence,
        aiData: {
          keywords: result.aiDataForFinalResponse?.keywords,
          reasoning: (result.aiDataForFinalResponse as any)?.reasoning,
          sources: ['AI Karen Engine', 'Knowledge Base']
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
      await chatService.addMessageToConversation(conversationId, assistantMessage);

    } catch (error) {
      safeError('Failed to process message:', error);
      toast({
        variant: 'destructive',
        title: 'Message Failed',
        description: 'Unable to process your message. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [user, conversationId, sessionId, messages, chatService, toast]);

  // AG-Grid column definitions for conversations
  const conversationColumns: ColDef[] = [
    {
      headerName: 'Conversation',
      field: 'title',
      flex: 2,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2 py-1">
          <MessageSquare className="h-4 w-4 text-muted-foreground " />
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
      field: 'lastActivity',
      flex: 1,
      cellRenderer: (params: any) => (
        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
          {format(new Date(params.value), 'MMM dd, HH:mm')}
        </span>
      )
    },
    {
      headerName: 'Status',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => (
        <Badge variant={params.value === 'active' ? 'default' : 'secondary'}>
          {params.value}
        </Badge>
      )
    },
    {
      headerName: 'Sentiment',
      field: 'sentiment',
      width: 100,
      cellRenderer: (params: any) => {
        const colors = {
          positive: 'bg-green-100 text-green-800',
          neutral: 'bg-gray-100 text-gray-800',
          negative: 'bg-red-100 text-red-800'
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs ${colors[params.value as keyof typeof colors]}`}>
            {params.value}
          </span>
        );
      }
    }
];

return (
    <div className={`flex flex-col h-full ${className}`}>
      <Tabs value={activeView} onValueChange={(value) => setActiveView(value as 'chat' | 'conversations' | 'analytics')} className="flex-1 flex flex-col">
        <div className="border-b">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 " />
            </TabsTrigger>
            <TabsTrigger value="conversations" className="flex items-center gap-2">
              <Grid3X3 className="h-4 w-4 " />
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 " />
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <TabsContent value="chat" className="flex-1 flex flex-col m-0 p-0 sm:p-4 md:p-6">
            <CopilotKit runtimeUrl="/api/copilot">
              <Card className="flex-1 flex flex-col">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 " />
                    <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                      <Brain className="h-3 w-3 mr-1 " />
                    </Badge>
                  </CardTitle>
                </CardHeader>

                <CardContent className="flex-1 flex flex-col p-0 sm:p-4 md:p-6">
                  {/* Messages Area */}
                  <ScrollArea className="flex-1 px-4">
                    <div className="space-y-4 pb-4">
                      {messages.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <div className="flex items-center justify-center gap-2 mb-4">
                            <Bot className="h-12 w-12 opacity-50 " />
                            <Zap className="h-8 w-8 text-primary " />
                          </div>
                          <p className="text-lg font-medium mb-2">Welcome to AI Karen</p>
                          <p className="text-sm md:text-base lg:text-lg">
                            Your intelligent assistant powered by advanced AI and enhanced with CopilotKit.
                            Ask me anything or request help with your tasks!
                          </p>
                        </div>
                      ) : (
                        messages.map((message) => (
                          <ChatBubble
                            key={message.id}
                            role={message.role}
                            content={message.content}
                            meta={{ confidence: message.confidence }}
                          />
                        ))
                      )}
                      
                      {isLoading && (
                        <div className="flex gap-3 mb-4">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center ">
                            <Bot className="h-4 w-4 " />
                          </div>
                          <div className="flex-1">
                            <div className="inline-block p-3 rounded-lg bg-muted border sm:p-4 md:p-6">
                              <div className="flex items-center gap-2">
                                <div className="flex space-x-1">
                                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce "></div>
                                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce " style={{ animationDelay: '0.1s' }}></div>
                                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce " style={{ animationDelay: '0.2s' }}></div>
                                </div>
                                <span className="text-sm text-muted-foreground md:text-base lg:text-lg">AI Karen is thinking...</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      <div ref={messagesEndRef} />
                    </div>
                  </ScrollArea>

                  {/* CopilotKit Chat Integration */}
                  <div className="border-t">
                    <CopilotChat
                      instructions="You are AI Karen, an intelligent assistant. Help users with their questions and tasks. Be helpful, accurate, and engaging."
                      labels={{
                        title: "AI Karen Assistant",
                        initial: "Hello! I'm AI Karen. How can I help you today?",
                        placeholder: "Ask me anything..."
                      }}
                      onInProgress={(inProgress) => setIsLoading(inProgress)}
                      onSubmitMessage={handleSubmit}
                    />
                  </div>
                </CardContent>
              </Card>
            </CopilotKit>
          </TabsContent>

          <TabsContent value="conversations" className="flex-1 m-0 p-4 sm:p-4 md:p-6">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 " />
                  <Badge variant="outline">{conversations.length} conversations</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="h-full p-0 sm:p-4 md:p-6">
                <div className="ag-theme-alpine h-full">
                  <AgGridReact
                    ref={gridRef}
                    rowData={conversations}
                    columnDefs={conversationColumns}
                    defaultColDef={{
                      sortable: true,
                      filter: true,
                      resizable: true
                    }}
                    animateRows={true}
                    rowSelection="multiple"
                    onGridReady={(event: GridReadyEvent) => {
                      event.api.sizeColumnsToFit();
                    }}
                    className="h-full"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="flex-1 m-0 p-4 sm:p-4 md:p-6">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 " />
                  <Badge variant="secondary">Coming Soon</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50 " />
                  <p className="text-lg font-medium mb-2">Analytics Dashboard</p>
                  <p className="text-sm md:text-base lg:text-lg">
                    Detailed conversation analytics and insights will be available here.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};

export default ChatSystem;