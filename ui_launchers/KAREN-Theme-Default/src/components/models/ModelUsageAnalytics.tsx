/**
 * Model Usage Analytics - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { BarChart3, TrendingUp } from 'lucide-react';

export interface UsageData { model: string; requests: number; tokens: number; percentage: number; }
export interface ModelUsageAnalyticsProps { className?: string; }

export default function ModelUsageAnalytics({ className = '' }: ModelUsageAnalyticsProps) {
  const usage: UsageData[] = [
    { model: 'GPT-4 Turbo', requests: 1250, tokens: 850000, percentage: 45 },
    { model: 'Claude 3 Opus', requests: 980, tokens: 720000, percentage: 35 },
    { model: 'Llama 3 70B', requests: 560, tokens: 420000, percentage: 20 }
  ];
  
  const total_requests = usage.reduce((s, u) => s + u.requests, 0);
  const total_tokens = usage.reduce((s, u) => s + u.tokens, 0);
  
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />Usage Analytics
        </CardTitle>
        <div className="text-sm text-muted-foreground">
          {total_requests.toLocaleString()} requests • {(total_tokens / 1000).toFixed(0)}K tokens
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {usage.map(u => (
          <div key={u.model}>
            <div className="flex justify-between mb-2">
              <span className="font-medium">{u.model}</span>
              <span className="text-sm text-muted-foreground">{u.percentage}%</span>
            </div>
            <Progress value={u.percentage} />
            <div className="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>{u.requests} requests</span>
              <span>{(u.tokens / 1000).toFixed(0)}K tokens</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export { ModelUsageAnalytics };
