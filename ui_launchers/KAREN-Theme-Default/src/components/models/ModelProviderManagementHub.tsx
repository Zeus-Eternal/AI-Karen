/**
 * Model Provider Management Hub - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Server, CheckCircle2, XCircle } from 'lucide-react';

export interface Provider { id: string; name: string; enabled: boolean; models_count: number; status: 'active' | 'inactive'; }
export interface ModelProviderManagementHubProps { className?: string; }

export default function ModelProviderManagementHub({ className = '' }: ModelProviderManagementHubProps) {
  const [providers, setProviders] = useState<Provider[]>([
    { id: '1', name: 'OpenAI', enabled: true, models_count: 12, status: 'active' },
    { id: '2', name: 'Anthropic', enabled: true, models_count: 5, status: 'active' },
    { id: '3', name: 'Meta', enabled: false, models_count: 8, status: 'inactive' }
  ]);
  
  const toggle = (id: string) => {
    setProviders(providers.map(p => p.id === id ? { ...p, enabled: !p.enabled, status: !p.enabled ? 'active' : 'inactive' } : p));
  };
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" />Provider Management</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {providers.map(p => (
          <div key={p.id} className="flex items-center justify-between p-3 border rounded">
            <div className="flex items-center gap-3">
              {p.status === 'active' ? <CheckCircle2 className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-gray-400" />}
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-sm text-muted-foreground">{p.models_count} models</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={p.status === 'active' ? 'default' : 'secondary'}>{p.status}</Badge>
              <Switch checked={p.enabled} onCheckedChange={() => toggle(p.id)} />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export { ModelProviderManagementHub };
