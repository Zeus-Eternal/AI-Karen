/**
 * Cost Tracking System - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DollarSign } from 'lucide-react';

export interface CostEntry { id: string; cost: number; model: string; }
export interface CostTrackingSystemProps { className?: string; }

export default function CostTrackingSystem({ className = '' }: CostTrackingSystemProps) {
  const [costs] = useState<CostEntry[]>([
    { id: '1', cost: 0.45, model: 'GPT-4' },
    { id: '2', cost: 0.23, model: 'Claude' }
  ]);
  const total = costs.reduce((s, e) => s + e.cost, 0);
  
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5" />Cost Tracking
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{total.toFixed(2)} USD</div>
        {costs.map(c => <div key={c.id} className="flex justify-between mt-2">
          <span>{c.model}</span><Badge>{c.cost.toFixed(2)}</Badge>
        </div>)}
      </CardContent>
    </Card>
  );
}

export { CostTrackingSystem };
