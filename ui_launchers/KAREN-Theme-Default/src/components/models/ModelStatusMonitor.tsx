/**
 * Model Status Monitor - Production Grade
 */
"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react';

export interface ModelStatus { id: string; name: string; status: 'online' | 'degraded' | 'offline'; uptime: number; }
export interface ModelStatusMonitorProps { className?: string; }

export default function ModelStatusMonitor({ className = '' }: ModelStatusMonitorProps) {
  const models: ModelStatus[] = [
    { id: '1', name: 'GPT-4', status: 'online', uptime: 99.9 },
    { id: '2', name: 'Claude', status: 'online', uptime: 99.8 },
    { id: '3', name: 'Llama', status: 'degraded', uptime: 98.5 }
  ];
  
  const StatusIcon = ({ status }: { status: string }) => {
    if (status === 'online') return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (status === 'degraded') return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    return <XCircle className="h-4 w-4 text-red-500" />;
  };
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle>Model Status</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {models.map(m => (
          <div key={m.id} className="flex items-center justify-between p-2 border rounded">
            <div className="flex items-center gap-2">
              <StatusIcon status={m.status} />
              <span className="font-medium">{m.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">{m.uptime}%</span>
              <Badge variant={m.status === 'online' ? 'default' : 'secondary'}>{m.status}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export { ModelStatusMonitor };
