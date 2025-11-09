/**
 * Model Browser - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Search, Download } from 'lucide-react';

export interface Model { id: string; name: string; provider: string; size: string; status: 'available' | 'local'; }
export interface ModelBrowserProps { onModelSelect?: (id: string) => void; className?: string; }

export default function ModelBrowser({ onModelSelect, className = '' }: ModelBrowserProps) {
  const [search, setSearch] = useState('');
  const models: Model[] = [
    { id: '1', name: 'GPT-4 Turbo', provider: 'OpenAI', size: '1.7T', status: 'available' },
    { id: '2', name: 'Claude 3 Opus', provider: 'Anthropic', size: '1.2T', status: 'local' },
    { id: '3', name: 'Llama 3 70B', provider: 'Meta', size: '70B', status: 'available' }
  ];
  
  const filtered = models.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle>Model Browser</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search models..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <div className="space-y-2">
          {filtered.map(m => (
            <div key={m.id} className="flex items-center justify-between p-3 border rounded hover:bg-muted/50 cursor-pointer" onClick={() => onModelSelect?.(m.id)}>
              <div>
                <div className="font-medium">{m.name}</div>
                <div className="text-sm text-muted-foreground">{m.provider} • {m.size}</div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={m.status === 'local' ? 'default' : 'secondary'}>{m.status}</Badge>
                {m.status === 'available' && <Button size="sm" variant="ghost"><Download className="h-4 w-4" /></Button>}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export { ModelBrowser };
