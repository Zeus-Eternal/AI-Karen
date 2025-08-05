'use client';

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, BarChart3, Grid3X3, Settings, Maximize2, Minimize2 } from 'lucide-react';
import ChatInterface from './ChatInterface';
import { ConversationGrid, ConversationRow } from './ConversationGrid';
import { ChatAnalyticsChart, ChatAnalyticsData } from './ChatAnalyticsChart';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface EnhancedChatInterfaceProps {
  className?: string;
  defaultTab?: 'chat' | 'conversations' | 'analytics';
  showTabs?: boolean;
}

export const EnhancedChatInterface: React.FC<EnhancedChatInterfaceProps> = ({
  className = '',
  defaultTab = 'chat',
  showTabs = true
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChatHook } = useHooks();
  const { toast } = useToast();
  
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [analyticsData, setAnalyticsData] = useState<ChatAnalyticsData[]>([]);
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState('24h');
  const [isLoading, setIsLoading] = useState(false);

  // Register chat hooks on mount
  useEffect(() => {
    const hookIds: string[] = [];

    // Register pre-message hook for analytics tracking
    hookIds.push(registerChatHook('preMessage', async (params) => {
      console.log('Pre-message hook triggered:', params);
      // Track message initiation
      return { success: true, timestamp: new Date() };
    }));

    // Register post-message hook for conversation updates
    hookIds.push(registerChatHook('postMessage', async (params) => {
      console.log('Post-message hook triggered:', params);
      // Update conversation list and analytics
      await refreshConversations();
      return { success: true, conversationUpdated: true };
    }));

    // Register AI suggestion hook
    hookIds.push(registerChatHook('aiSuggestion', async (params) => {
      console.log('AI suggestion hook triggered:', params);
      // Handle AI suggestions
      return { success: true, suggestions: params.suggestions };
    }));

    return () => {
      // Cleanup hooks on unmount
      hookIds.forEach(id => {
        // Note: unregisterHook would be called here in a real implementation
      });
    };
  }, [registerChatHook]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, [user]);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadConversations(),
        loadAnalyticsData()
      ]);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      toast({
        variant: 'destructive',
        title: 'Loading Error',
        description: 'Failed to load chat data. Please refresh the page.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversations = async () => {
    // Generate sample conversation data
    const sampleConversations: ConversationRow[] = [
      {
        id: '1',
        title: 'Project Planning Discussion',
        lastMessage: 'Let me help you create a comprehensive project timeline...',
        timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
        messageCount: 15,
        participants: [user?.email || 'You', 'Karen AI'],
        tags: ['planning', 'project', 'timeline'],
        sentiment: 'positive',
        aiInsights: ['Project scope analysis', 'Timeline optimization']
      },
      {
        id: '2',
        title: 'Code Review Session',
        lastMessage: 'I found several optimization opportunities in your React components...',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
        messageCount: 8,
        participants: [user?.email || 'You', 'Karen AI'],
        tags: ['code', 'review', 'react', 'optimization'],
        sentiment: 'neutral',
        aiInsights: ['Performance improvements', 'Best practices']
      },
      {
        id: '3',
        title: 'API Integration Help',
        lastMessage: 'The authentication flow looks correct. Try checking the CORS settings...',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
        messageCount: 23,
        participants: [user?.email || 'You', 'Karen AI'],
        tags: ['api', 'integration', 'cors', 'authentication'],
        sentiment: 'positive',
        aiInsights: ['API troubleshooting', 'Security recommendations']
      }
    ];

    setConversations(sampleConversations);
  };

  const loadAnalyticsData = async () => {
    // Generate sample analytics data
    const now = new Date();
    const sampleData: ChatAnalyticsData[] = [];
    
    for (let i = 23; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000); // Hourly data for 24h
      sampleData.push({
        timestamp,
        messageCount: Math.floor(Math.random() * 20) + 5,
        responseTime: Math.random() * 1500 + 300,
        userSatisfaction: Math.random() * 1.5 + 3.5, // 3.5-5 scale
        aiInsights: Math.floor(Math.random() * 5) + 1,
        tokenUsage: Math.floor(Math.random() * 800) + 200,
        llmProvider: ['ollama', 'openai'][Math.floor(Math.random() * 2)]
      });
    }

    setAnalyticsData(sampleData);
  };

  const refreshConversations = async () => {
    await loadConversations();
    toast({
      title: 'Conversations Updated',
      description: 'Conversation list has been refreshed.'
    });
  };

  const handleConversationSelect = async (conversation: ConversationRow) => {
    // Trigger hooks for conversation selection
    await triggerHooks('chat_conversationSelected', {
      conversationId: conversation.id,
      conversation
    }, { userId: user?.user_id });

    // Switch to chat tab and load conversation
    setActiveTab('chat');
    toast({
      title: 'Conversation Loaded',
      description: `Switched to "${conversation.title}"`
    });
  };

  const handleAnalyticsTimeframeChange = (timeframe: string) => {
    setAnalyticsTimeframe(timeframe);
    // Reload analytics data for new timeframe
    loadAnalyticsData();
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!showTabs) {
    return (
      <div className={`${className} ${isFullscreen ? 'fixed inset-0 z-50 bg-background' : ''}`}>
        <ChatInterface />
      </div>
    );
  }

  return (
    <div className={`${className} ${isFullscreen ? 'fixed inset-0 z-50 bg-background' : ''}`}>
      <Card className="w-full h-full">
        <CardContent className="p-0 h-full">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <TabsList className="grid w-full max-w-md grid-cols-3">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </TabsTrigger>
                <TabsTrigger value="conversations" className="flex items-center gap-2">
                  <Grid3X3 className="h-4 w-4" />
                  History
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {conversations.length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </TabsTrigger>
              </TabsList>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleFullscreen}
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex-1 min-h-0">
              <TabsContent value="chat" className="h-full m-0 p-0">
                <ChatInterface />
              </TabsContent>

              <TabsContent value="conversations" className="h-full m-0 p-4">
                <ConversationGrid
                  conversations={conversations}
                  onConversationSelect={handleConversationSelect}
                  onRefresh={refreshConversations}
                  className="h-full"
                />
              </TabsContent>

              <TabsContent value="analytics" className="h-full m-0 p-4">
                <div className="space-y-6 h-full">
                  <ChatAnalyticsChart
                    data={analyticsData}
                    timeframe={analyticsTimeframe as any}
                    onTimeframeChange={handleAnalyticsTimeframeChange}
                  />
                  
                  {/* Additional analytics components could go here */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardContent className="p-4">
                        <h3 className="text-lg font-semibold mb-2">LLM Provider Usage</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span>Ollama</span>
                            <Badge variant="default">65%</Badge>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>OpenAI</span>
                            <Badge variant="secondary">35%</Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <h3 className="text-lg font-semibold mb-2">Top Topics</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span>Code Review</span>
                            <Badge variant="default">12</Badge>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>API Integration</span>
                            <Badge variant="secondary">8</Badge>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Project Planning</span>
                            <Badge variant="secondary">6</Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};