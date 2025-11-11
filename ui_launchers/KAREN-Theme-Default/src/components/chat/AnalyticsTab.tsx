"use client";

import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import { BarChart3, MessageSquare, Clock, Target, Activity, Brain, TrendingUp, Code } from 'lucide-react';

import type { ChatMessage } from '@/components/ChatInterface';

interface AnalyticsTabProps {
  analytics: unknown;
  messages: ChatMessage[];
}

const AnalyticsTab: React.FC<AnalyticsTabProps> = ({ analytics, messages }) => (
  <div className="flex-1 p-4 sm:p-4 md:p-6">
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 " />
        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Real-time</Badge>
      </h3>
      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
        View conversation statistics, performance metrics, and insights.
      </div>
    </div>

    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="h-4 w-4 text-blue-500 " />
            <span className="text-sm font-medium md:text-base lg:text-lg">Messages</span>
          </div>
          <div className="text-2xl font-bold">{analytics.totalMessages}</div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
            {analytics.userMessages} sent, {analytics.assistantMessages} received
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-green-500 " />
            <span className="text-sm font-medium md:text-base lg:text-lg">Response Time</span>
          </div>
          <div className="text-2xl font-bold">{analytics.averageResponseTime}ms</div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">Average latency</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-purple-500 " />
            <span className="text-sm font-medium md:text-base lg:text-lg">Confidence</span>
          </div>
          <div className="text-2xl font-bold">{analytics.averageConfidence}%</div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">AI confidence</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-4 w-4 text-orange-500 " />
            <span className="text-sm font-medium md:text-base lg:text-lg">Session</span>
          </div>
          <div className="text-2xl font-bold">{Math.floor(analytics.sessionDuration / 60)}m</div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">{analytics.sessionDuration % 60}s active</div>
        </CardContent>
      </Card>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
            <Brain className="h-4 w-4 " />
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm md:text-base lg:text-lg">Total Tokens</span>
            <Badge variant="outline">{analytics.totalTokens.toLocaleString()}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm md:text-base lg:text-lg">Estimated Cost</span>
            <Badge variant="outline">${analytics.totalCost.toFixed(4)}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm md:text-base lg:text-lg">Error Rate</span>
            <Badge variant={analytics.errorRate > 10 ? 'destructive' : 'secondary'}>
              {analytics.errorRate}%
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
            <TrendingUp className="h-4 w-4 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {analytics.topTopics.length > 0 ? (
              analytics.topTopics.map((topic: string, index: number) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary " />
                  <span className="text-sm capitalize md:text-base lg:text-lg">{topic}</span>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">No topics identified yet</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>

    {analytics.codeLanguages.length > 0 && (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
            <Code className="h-4 w-4 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {analytics.codeLanguages.map((lang: string, index: number) => (
              <Badge key={index} variant="secondary" className="text-xs sm:text-sm md:text-base">
                {lang}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    )}

    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
          <Activity className="h-4 w-4 " />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {messages.slice(-5).map((message) => (
            <div key={message.id} className="flex items-start gap-3 p-2 rounded-lg bg-muted/50 sm:p-4 md:p-6">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                message.role === 'user' ? 'bg-blue-500' : 'bg-green-500'
              }`} />
              <div className="flex-1 min-w-0 ">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium capitalize md:text-base lg:text-lg">{message.role}</span>
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {message.type}
                  </Badge>
                  {message.metadata?.confidence && (
                    <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {Math.round(message.metadata.confidence * 100)}%
                    </Badge>
                  )}
                </div>
                <div className="text-sm text-muted-foreground line-clamp-2 md:text-base lg:text-lg">
                  {message.content}
                </div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2 sm:text-sm md:text-base">
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
