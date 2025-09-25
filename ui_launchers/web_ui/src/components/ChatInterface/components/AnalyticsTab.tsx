"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ChatAnalytics, ChatMessage } from "../types";

interface AnalyticsTabProps {
  analytics: ChatAnalytics;
  messages: ChatMessage[];
}

const AnalyticsTab: React.FC<AnalyticsTabProps> = ({ analytics, messages }) => {
  return (
    <div className="flex-1 overflow-y-auto space-y-4 p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Conversation Metrics</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-muted-foreground">Total Messages</div>
            <div className="text-xl font-semibold">{analytics.totalMessages}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Avg. Response Time</div>
            <div className="text-xl font-semibold">
              {Math.round(analytics.averageResponseTime)} ms
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Tokens Used</div>
            <div className="text-xl font-semibold">{analytics.totalTokens}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Estimated Cost</div>
            <div className="text-xl font-semibold">
              ${analytics.totalCost.toFixed(4)}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Topics & Languages</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {analytics.topTopics.map((topic) => (
            <Badge key={topic} variant="secondary">
              {topic}
            </Badge>
          ))}
          {analytics.codeLanguages.map((language) => (
            <Badge key={language} variant="outline">
              {language}
            </Badge>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Messages</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {messages.slice(-5).map((message) => (
            <div key={message.id} className="space-y-1">
              <div className="text-xs uppercase text-muted-foreground">
                {message.role} • {message.type ?? "text"}
              </div>
              <div className="text-sm">
                {message.content.length > 200
                  ? `${message.content.slice(0, 197)}...`
                  : message.content}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsTab;
