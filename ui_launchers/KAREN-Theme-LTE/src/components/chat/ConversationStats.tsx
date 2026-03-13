/**
 * Conversation Stats Component - Display conversation analytics and insights
 */

import React, { useState, useEffect } from 'react';
import { ConversationStats as ConversationStatsType } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  BarChart3, 
  Calendar, 
  MessageSquare, 
  TrendingUp,
  Users,
  Clock,
  Eye,
  Download
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConversationStatsProps {
  userId: string;
  className?: string;
}

export const ConversationStats: React.FC<ConversationStatsProps> = ({
  userId,
  className = ''
}) => {
  const [timeRange, setTimeRange] = useState<'7' | '30' | '90'>('30');
  const [stats, setStats] = useState<ConversationStatsType | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'trends'>('overview');

  // Mock data - in real implementation, this would fetch from API
  const mockStats: ConversationStatsType = {
    totalConversations: 42,
    totalMessages: 1258,
    activeConversations: 8,
    archivedConversations: 12,
    pinnedConversations: 5,
    averageMessagesPerConversation: 30,
    mostActiveDay: '2023-12-15',
    providerUsage: {
      'OpenAI': 18,
      'Anthropic': 12,
      'Google': 8,
      'Local': 4
    },
    tagUsage: {
      'work': 15,
      'personal': 8,
      'project': 12,
      'idea': 5,
      'research': 2
    }
  };

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setStats(mockStats);
      setLoading(false);
    }, 1000);

    return () => {
      clearTimeout(timer);
    };
  }, [timeRange]);

  const handleTimeRangeChange = (range: '7' | '30' | '90') => {
    setTimeRange(range);
    // In real implementation, this would trigger a stats refresh
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      'OpenAI': 'bg-green-500',
      'Anthropic': 'bg-purple-500',
      'Google': 'bg-blue-500',
      'Local': 'bg-gray-500'
    };
    return colors[provider] || 'bg-gray-500';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    const icons = {
      up: <TrendingUp className="h-4 w-4 text-green-500" />,
      down: <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />,
      stable: <div className="h-4 w-4 text-gray-500 flex items-center justify-center">—</div>
    };
    return icons[trend] || icons.stable;
  };

  return (
    <div className={cn('conversation-stats', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Conversation Statistics</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Time Range Selector */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Time Period</h3>
            <div className="flex space-x-2">
              {['7', '30', '90'].map((range) => (
                <Button
                  key={range}
                  variant={timeRange === range ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleTimeRangeChange(range as '7' | '30' | '90')}
                >
                  {range === '7' ? '7 Days' : range === '30' ? '30 Days' : '90 Days'}
                </Button>
              ))}
            </div>
          </div>

          {/* Stats Overview */}
          <Tabs value={activeTab} onValueChange={(value: string) => setActiveTab(value as 'overview' | 'usage' | 'trends')}>
            <TabsList>
              <TabsTrigger value="overview" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>Overview</span>
              </TabsTrigger>
              <TabsTrigger value="usage" className="flex items-center space-x-2">
                <Users className="h-4 w-4" />
                <span>Usage</span>
              </TabsTrigger>
              <TabsTrigger value="trends" className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4" />
                <span>Trends</span>
              </TabsTrigger>
            </TabsList>

            {loading && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="text-muted-foreground">Loading statistics...</p>
              </div>
            )}

            {stats && (
              <>
                <TabsContent value="overview" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Total Conversations */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-primary mb-2">
                          {formatNumber(stats.totalConversations)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Total Conversations
                        </div>
                      </CardContent>
                    </Card>

                    {/* Active Conversations */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-green-600 mb-2">
                          {formatNumber(stats.activeConversations)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Active Conversations
                        </div>
                      </CardContent>
                    </Card>

                    {/* Archived Conversations */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-orange-600 mb-2">
                          {formatNumber(stats.archivedConversations)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Archived Conversations
                        </div>
                      </CardContent>
                    </Card>

                    {/* Pinned Conversations */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-blue-600 mb-2">
                          {formatNumber(stats.pinnedConversations)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Pinned Conversations
                        </div>
                      </CardContent>
                    </Card>

                    {/* Average Messages */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-purple-600 mb-2">
                          {formatNumber(stats.averageMessagesPerConversation)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Avg Messages/Conversation
                        </div>
                      </CardContent>
                    </Card>

                    {/* Most Active Day */}
                    <Card>
                      <CardContent className="text-center p-6">
                        <div className="text-4xl font-bold text-indigo-600 mb-2">
                          {stats.mostActiveDay}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Most Active Day
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="usage" className="space-y-6">
                  <h3 className="text-lg font-semibold mb-4">Provider Usage</h3>
                  <div className="space-y-4">
                    {Object.entries(stats.providerUsage).map(([provider, count]) => (
                      <div key={provider} className="flex items-center justify-between p-4 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={cn(
                            'w-12 h-12 rounded-full flex items-center justify-center text-white font-bold',
                            getProviderColor(provider)
                          )}>
                            {provider.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="text-sm font-medium">{provider}</div>
                            <div className="text-2xl font-bold">{formatNumber(count)}</div>
                          </div>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {Math.round((count / stats.totalConversations) * 100)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="trends" className="space-y-6">
                  <h3 className="text-lg font-semibold mb-4">Tag Usage</h3>
                  <div className="space-y-4">
                    {Object.entries(stats.tagUsage).map(([tag, count]) => (
                      <div key={tag} className="flex items-center justify-between p-4 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Badge variant="outline" className="text-sm">
                            {tag}
                          </Badge>
                          <div className="flex-1">
                            <div className="text-sm font-medium">{tag}</div>
                            <div className="text-2xl font-bold">{formatNumber(count)}</div>
                          </div>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {Math.round((count / stats.totalMessages) * 100)}% of messages
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </>
            )}

            {/* Export Button */}
            <div className="flex justify-center mt-6">
              <Button variant="outline" size="sm" className="flex items-center space-x-2">
                <Download className="h-4 w-4" />
                <span>Export Detailed Report</span>
              </Button>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};