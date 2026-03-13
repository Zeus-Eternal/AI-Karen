/**
 * Integrated Model Display - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Server, BarChart3, Settings } from 'lucide-react';

export interface DisplayModel { name: string; status: string; metrics: { requests: number; latency: number; cost: number; }; config: Record<string, unknown>; }
export interface IntegratedModelDisplayProps { model: DisplayModel; onConfigure?: () => void; className?: string; }

export default function IntegratedModelDisplay({ model, onConfigure, className = '' }: IntegratedModelDisplayProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />{model.name}
          </CardTitle>
          <Badge>{model.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="metrics">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="metrics"><BarChart3 className="h-4 w-4 mr-2" />Metrics</TabsTrigger>
            <TabsTrigger value="config"><Settings className="h-4 w-4 mr-2" />Config</TabsTrigger>
          </TabsList>
          <TabsContent value="metrics" className="space-y-2">
            <div className="flex justify-between p-2 border rounded"><span>Requests:</span><span className="font-medium">{model.metrics.requests}</span></div>
            <div className="flex justify-between p-2 border rounded"><span>Latency:</span><span className="font-medium">{model.metrics.latency}ms</span></div>
            <div className="flex justify-between p-2 border rounded"><span>Cost:</span><span className="font-medium">${model.metrics.cost}</span></div>
          </TabsContent>
          <TabsContent value="config" className="space-y-2">
            {Object.entries(model.config).map(([k, v]) => (
              <div key={k} className="flex justify-between p-2 border rounded"><span>{k}:</span><span className="font-medium">{String(v)}</span></div>
            ))}
            <Button onClick={onConfigure} className="w-full mt-2">Configure</Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

export { IntegratedModelDisplay };
