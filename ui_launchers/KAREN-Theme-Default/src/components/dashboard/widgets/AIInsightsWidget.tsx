"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Brain, TrendingUp, TrendingDown, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react';
import type { WidgetProps } from '@/types/dashboard';

interface AIInsight {
  id: string;
  type: 'trend' | 'anomaly' | 'recommendation' | 'success';
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'success' | 'error';
  timestamp: string;
}

const AIInsightsWidget: React.FC<WidgetProps> = ({ config, data }) => {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchInsights = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/dashboard/ai-insights');
        if (response.ok) {
          const data = await response.json();
          setInsights(data.insights || []);
        } else {
          // Fallback sample insights
          setInsights([
            {
              id: '1',
              type: 'trend',
              title: 'User Engagement Up',
              description: 'User engagement has increased by 18% this week',
              severity: 'success',
              timestamp: new Date().toISOString(),
            },
            {
              id: '2',
              type: 'recommendation',
              title: 'Optimize Response Times',
              description: 'Consider caching frequently requested data to improve response times',
              severity: 'info',
              timestamp: new Date().toISOString(),
            },
            {
              id: '3',
              type: 'anomaly',
              title: 'Unusual Activity Detected',
              description: 'Higher than normal traffic detected at 3 PM',
              severity: 'warning',
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } catch (error) {
        console.warn('AI Insights unavailable:', error);
        // Use fallback
        setInsights([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInsights();
  }, []);

  const getIcon = (type: AIInsight['type']) => {
    switch (type) {
      case 'trend':
        return TrendingUp;
      case 'anomaly':
        return AlertTriangle;
      case 'recommendation':
        return Lightbulb;
      case 'success':
        return CheckCircle;
      default:
        return Brain;
    }
  };

  const getVariant = (severity: AIInsight['severity']) => {
    switch (severity) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'default';
      case 'success':
        return 'default';
      default:
        return 'outline';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI Insights
          </CardTitle>
          <CardDescription>Loading insights...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI Insights
        </CardTitle>
        <CardDescription>
          {insights.length} insights from AI analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {insights.length === 0 ? (
          <Alert>
            <AlertDescription>No insights available at this time.</AlertDescription>
          </Alert>
        ) : (
          insights.map((insight) => {
            const Icon = getIcon(insight.type);
            return (
              <Alert key={insight.id} variant={getVariant(insight.severity)}>
                <Icon className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <strong className="text-sm">{insight.title}</strong>
                      <p className="text-sm mt-1">{insight.description}</p>
                    </div>
                    <Badge variant="outline" className="ml-2">
                      {insight.type}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>
            );
          })
        )}
      </CardContent>
    </Card>
  );
};

export default AIInsightsWidget;
