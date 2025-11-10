/**
 * Model Metrics Dashboard - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Zap, TrendingUp } from 'lucide-react';

export interface ModelMetric { model: string; latency: number; throughput: number; }
export interface ModelMetricsDashboardProps { className?: string; }

export default function ModelMetricsDashboard({ className = '' }: ModelMetricsDashboardProps) {
  const metrics: ModelMetric[] = [
    { model: 'GPT-4', latency: 1200, throughput: 85 },
    { model: 'Claude', latency: 950, throughput: 92 }
  ];
  
  return (
    <div className={`grid gap-4 ${className}`}>
      {metrics.map(m => (
        <Card key={m.model}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />{m.model}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex gap-4">
            <div><Zap className="h-4 w-4 inline" /> {m.latency}ms</div>
            <div><TrendingUp className="h-4 w-4 inline" /> {m.throughput} t/s</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export { ModelMetricsDashboard };
