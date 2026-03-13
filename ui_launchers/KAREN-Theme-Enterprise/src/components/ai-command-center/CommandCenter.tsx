'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  AlertTriangle,
  TrendingUp,
  Zap,
  Brain,
  Shield,
  DollarSign,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { GlassCard } from '@/components/ui/glass-card';

export interface CommandCenterInsight {
  id: string;
  type: 'optimization' | 'warning' | 'info' | 'recommendation' | 'success' | 'error';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  actionable: boolean;
  actions?: QuickAction[];
  timestamp: Date;
  category: 'performance' | 'cost' | 'security' | 'quality' | 'system';
}

export interface QuickAction {
  id: string;
  label: string;
  variant?: 'default' | 'destructive' | 'outline' | 'secondary';
  onClick: () => Promise<void>;
}

// Mock insights data
const mockInsights: CommandCenterInsight[] = [
  {
    id: '1',
    type: 'recommendation',
    title: 'Reduce Costs by 30%',
    description: '70% of your requests use GPT-4, but 80% of those could use GPT-3.5 with similar quality',
    impact: 'high',
    actionable: true,
    category: 'cost',
    timestamp: new Date(),
    actions: [
      {
        id: 'enable-smart-routing',
        label: 'Enable Smart Routing',
        variant: 'default',
        onClick: async () => console.log('Enabling smart routing...'),
      },
    ],
  },
  {
    id: '2',
    type: 'warning',
    title: 'Memory Usage High',
    description: 'Vector store is at 85% capacity. Consider archiving old embeddings.',
    impact: 'high',
    actionable: true,
    category: 'performance',
    timestamp: new Date(),
    actions: [
      {
        id: 'archive-embeddings',
        label: 'Archive Old Data',
        variant: 'secondary',
        onClick: async () => console.log('Archiving...'),
      },
    ],
  },
  {
    id: '3',
    type: 'optimization',
    title: 'Batch Processing Available',
    description: '15 queued tasks could be batched for 40% faster processing',
    impact: 'medium',
    actionable: true,
    category: 'performance',
    timestamp: new Date(),
    actions: [
      {
        id: 'enable-batching',
        label: 'Enable Batching',
        variant: 'default',
        onClick: async () => console.log('Enabling batching...'),
      },
    ],
  },
  {
    id: '4',
    type: 'info',
    title: 'New Model Available',
    description: 'Claude 3.5 Sonnet is now available with improved performance',
    impact: 'low',
    actionable: false,
    category: 'system',
    timestamp: new Date(),
  },
  {
    id: '5',
    type: 'success',
    title: 'Optimization Complete',
    description: 'Query cache optimization reduced average latency by 45ms',
    impact: 'medium',
    actionable: false,
    category: 'performance',
    timestamp: new Date(),
  },
];

const insightIcons = {
  optimization: TrendingUp,
  warning: AlertTriangle,
  info: Brain,
  recommendation: Sparkles,
  success: CheckCircle2,
  error: XCircle,
};

const insightColors = {
  optimization: 'text-blue-600 dark:text-blue-400 bg-blue-500/10',
  warning: 'text-yellow-600 dark:text-yellow-400 bg-yellow-500/10',
  info: 'text-blue-600 dark:text-blue-400 bg-blue-500/10',
  recommendation: 'text-purple-600 dark:text-purple-400 bg-purple-500/10',
  success: 'text-green-600 dark:text-green-400 bg-green-500/10',
  error: 'text-red-600 dark:text-red-400 bg-red-500/10',
};

const impactColors = {
  high: 'bg-red-500',
  medium: 'bg-yellow-500',
  low: 'bg-green-500',
};

export interface CommandCenterProps {
  className?: string;
  insights?: CommandCenterInsight[];
  onActionClick?: (actionId: string, insightId: string) => Promise<void>;
}

export function CommandCenter({
  className,
  insights = mockInsights,
  onActionClick,
}: CommandCenterProps) {
  const [processingActions, setProcessingActions] = useState<Set<string>>(new Set());

  const handleActionClick = async (action: QuickAction, insightId: string) => {
    setProcessingActions((prev) => new Set(prev).add(action.id));
    try {
      if (onActionClick) {
        await onActionClick(action.id, insightId);
      } else {
        await action.onClick();
      }
    } finally {
      setProcessingActions((prev) => {
        const next = new Set(prev);
        next.delete(action.id);
        return next;
      });
    }
  };

  const highPriorityInsights = insights.filter((i) => i.impact === 'high');
  const actionableInsights = insights.filter((i) => i.actionable);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Command Center Header */}
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-blue-500/5 to-purple-600/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="text-lg">AI Command Center</div>
              <div className="text-sm font-normal text-muted-foreground">
                Proactive Intelligence & System Insights
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
                <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">{highPriorityInsights.length}</div>
                <div className="text-xs text-muted-foreground">High Priority</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">{actionableInsights.length}</div>
                <div className="text-xs text-muted-foreground">Actions Available</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <DollarSign className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">$247</div>
                <div className="text-xs text-muted-foreground">Potential Savings</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Clock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">2.3s</div>
                <div className="text-xs text-muted-foreground">Optimization Gain</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Proactive Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-3">
              {insights.map((insight, index) => {
                const Icon = insightIcons[insight.type];
                return (
                  <React.Fragment key={insight.id}>
                    <GlassCard
                      intensity="light"
                      padding="md"
                      className={cn(
                        'transition-all duration-200',
                        insight.actionable && 'hover:shadow-md'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {/* Icon */}
                        <div
                          className={cn(
                            'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
                            insightColors[insight.type]
                          )}
                        >
                          <Icon className="h-5 w-5" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-semibold">{insight.title}</h4>
                                <div
                                  className={cn(
                                    'h-2 w-2 rounded-full',
                                    impactColors[insight.impact]
                                  )}
                                  title={`${insight.impact} impact`}
                                />
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {insight.description}
                              </p>
                            </div>
                            <Badge variant="outline" className="shrink-0 text-xs">
                              {insight.category}
                            </Badge>
                          </div>

                          {/* Actions */}
                          {insight.actions && insight.actions.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-2">
                              {insight.actions.map((action) => (
                                <Button
                                  key={action.id}
                                  size="sm"
                                  variant={action.variant || 'default'}
                                  onClick={() => handleActionClick(action, insight.id)}
                                  disabled={processingActions.has(action.id)}
                                  className="gap-1"
                                >
                                  {action.label}
                                  <ChevronRight className="h-3 w-3" />
                                </Button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </GlassCard>
                    {index < insights.length - 1 && <Separator />}
                  </React.Fragment>
                );
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline" className="h-auto flex-col gap-2 p-4">
              <Zap className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium">Optimize Now</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col gap-2 p-4">
              <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium">Run Diagnostics</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col gap-2 p-4">
              <DollarSign className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              <span className="text-sm font-medium">Cost Analysis</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col gap-2 p-4">
              <Brain className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium">Memory Cleanup</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default CommandCenter;
