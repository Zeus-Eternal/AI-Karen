/**
 * Model Performance Comparison - Production Grade
 */
"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { TrendingUp } from 'lucide-react';

export interface PerformanceMetric { model: string; latency: number; throughput: number; quality: number; }
export interface ModelPerformanceComparisonProps { metrics: PerformanceMetric[]; className?: string; }

export default function ModelPerformanceComparison({ metrics, className = '' }: ModelPerformanceComparisonProps) {
  const maxLatency = Math.max(...metrics.map(m => m.latency));
  const maxThroughput = Math.max(...metrics.map(m => m.throughput));
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5" />Performance Comparison</CardTitle></CardHeader>
      <CardContent className="space-y-6">
        {metrics.map(m => (
          <div key={m.model}>
            <div className="font-medium mb-3">{m.model}</div>
            <div className="space-y-2 text-sm">
              <div>
                <div className="flex justify-between mb-1"><span>Latency</span><span>{m.latency}ms</span></div>
                <Progress value={(m.latency / maxLatency) * 100} />
              </div>
              <div>
                <div className="flex justify-between mb-1"><span>Throughput</span><span>{m.throughput} t/s</span></div>
                <Progress value={(m.throughput / maxThroughput) * 100} />
              </div>
              <div>
                <div className="flex justify-between mb-1"><span>Quality</span><span>{m.quality}/100</span></div>
                <Progress value={m.quality} />
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export { ModelPerformanceComparison };
