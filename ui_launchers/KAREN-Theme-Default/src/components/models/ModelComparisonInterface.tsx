/**
 * Model Comparison Interface - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { GitCompare } from 'lucide-react';

export interface ComparisonModel { id: string; name: string; latency: number; cost: number; quality: number; }
export interface ModelComparisonInterfaceProps { className?: string; }

export default function ModelComparisonInterface({ className = '' }: ModelComparisonInterfaceProps) {
  const models: ComparisonModel[] = [
    { id: '1', name: 'GPT-4', latency: 1200, cost: 0.03, quality: 95 },
    { id: '2', name: 'Claude', latency: 950, cost: 0.075, quality: 97 },
    { id: '3', name: 'Llama', latency: 600, cost: 0.001, quality: 85 }
  ];
  
  const [selected, setSelected] = useState<string[]>(['1', '2']);
  const compared = models.filter(m => selected.includes(m.id));
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle className="flex items-center gap-2"><GitCompare className="h-5 w-5" />Model Comparison</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          {['1', '2'].map((slot, i) => (
            <Select key={slot} value={selected[i]} onValueChange={(v) => setSelected(selected.map((s, j) => j === i ? v : s))}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {models.map(m => <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>)}
              </SelectContent>
            </Select>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {compared.map(m => (
            <div key={m.id} className="space-y-2 p-3 border rounded">
              <div className="font-medium">{m.name}</div>
              <div className="text-sm space-y-1">
                <div className="flex justify-between"><span>Latency:</span><Badge variant="secondary">{m.latency}ms</Badge></div>
                <div className="flex justify-between"><span>Cost:</span><Badge variant="secondary">${m.cost}</Badge></div>
                <div className="flex justify-between"><span>Quality:</span><Badge variant="secondary">{m.quality}/100</Badge></div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export { ModelComparisonInterface };
