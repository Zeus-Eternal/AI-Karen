'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Activity,
  BarChart3,
  Brain,
  Clock,
  Code,
  MessageSquare,
  Target,
  TrendingUp,
} from 'lucide-react';

import type { ChatMessage } from './ChatInterface';

interface AnalyticsTabProps {
  analytics: any;
  messages: ChatMessage[];
}

const AnalyticsTab: React.FC<AnalyticsTabProps> = ({ analytics, messages }) => (
  <div className="flex-1 p-4">
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
        <BarChart3 className="h-5 w-5" />
        Chat Analytics
        <Badge variant="outline" className="text-xs">Real-time</Badge>
      </h3>
      <div className="text-sm text-muted-foreground">
        View conversation statistics, performance metrics, and insights.
      </div>
    </div>

    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">Messages</span>
          </div>
          <div className="text-2xl font-bold">{analytics.totalMessages}</div>
          <div className="text-xs text-muted-foreground">
            {analytics.userMessages} sent, {analytics.assistantMessages} received
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-green-500" />
            <span className="text-sm font-medium">Response Time</span>
          </div>
          <div className="text-2xl font-bold">{analytics.averageResponseTime}ms</div>
          <div className="text-xs text-muted-foreground">Average latency</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-purple-500" />
            <span className="text-sm font-medium">Confidence</span>
          </div>
          <div className="text-2xl font-bold">{analytics.averageConfidence}%</div>
          <div className="text-xs text-muted-foreground">AI confidence</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-4 w-4 text-orange-500" />
            <span className="text-sm font-medium">Session</span>
          </div>
          <div className="text-2xl font-bold">{Math.floor(analytics.sessionDuration / 60)}m</div>
          <div className="text-xs text-muted-foreground">{analytics.sessionDuration % 60}s active</div>
        </CardContent>
      </Card>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Usage Statistics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm">Total Tokens</span>
            <Badge variant="outline">{analytics.totalTokens.toLocaleString()}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm">Estimated Cost</span>
            <Badge variant="outline">${analytics.totalCost.toFixed(4)}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm">Error Rate</span>
            <Badge variant={analytics.errorRate > 10 ? 'destructive' : 'secondary'}>
              {analytics.errorRate}%
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Top Topics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {analytics.topTopics.length > 0 ? (
              analytics.topTopics.map((topic: string, index: number) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary" />
                  <span className="text-sm capitalize">{topic}</span>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted-foreground">No topics identified yet</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>

    {analytics.codeLanguages.length > 0 && (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Code className="h-4 w-4" />
            Programming Languages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {analytics.codeLanguages.map((lang: string, index: number) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {lang}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    )}

    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Recent Messages
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {messages.slice(-5).map((message) => (
            <div key={message.id} className="flex items-start gap-3 p-2 rounded-lg bg-muted/50">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                message.role === 'user' ? 'bg-blue-500' : 'bg-green-500'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium capitalize">{message.role}</span>
                  <Badge variant="outline" className="text-xs">
                    {message.type}
                  </Badge>
                  {message.metadata?.confidence && (
                    <Badge variant="secondary" className="text-xs">
                      {Math.round(message.metadata.confidence * 100)}%
                    </Badge>
                  )}
                </div>
                <div className="text-sm text-muted-foreground line-clamp-2">
                  {message.content}
                </div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                  <span>{message.timestamp.toLocaleTimeString()}</span>
                  {message.metadata?.latencyMs && (
                    <span>• {message.metadata.latencyMs}ms</span>
                  )}
                  {message.metadata?.tokens && (
                    <span>• {message.metadata.tokens} tokens</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  </div>
);

export default AnalyticsTab;
