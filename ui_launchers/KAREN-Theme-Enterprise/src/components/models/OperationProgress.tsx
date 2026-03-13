/**
 * Operation Progress - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';

export interface Operation { id: string; name: string; progress: number; status: 'pending' | 'running' | 'complete' | 'error'; message?: string; }
export interface OperationProgressProps { operations: Operation[]; className?: string; }

export default function OperationProgress({ operations, className = '' }: OperationProgressProps) {
  const StatusIcon = ({ status }: { status: string }) => {
    if (status === 'complete') return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (status === 'error') return <XCircle className="h-4 w-4 text-red-500" />;
    if (status === 'running') return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    return <div className="h-4 w-4 rounded-full border-2 border-muted" />;
  };
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle>Operations</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {operations.map(op => (
          <div key={op.id} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusIcon status={op.status} />
                <span className="font-medium">{op.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{op.progress}%</span>
                <Badge variant={op.status === 'complete' ? 'default' : op.status === 'error' ? 'destructive' : 'secondary'}>{op.status}</Badge>
              </div>
            </div>
            {op.status === 'running' && <Progress value={op.progress} />}
            {op.message && <div className="text-sm text-muted-foreground">{op.message}</div>}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export { OperationProgress };
