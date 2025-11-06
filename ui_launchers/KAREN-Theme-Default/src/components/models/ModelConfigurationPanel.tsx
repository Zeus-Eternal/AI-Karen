/**
 * Model Configuration Panel - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Settings, Save } from 'lucide-react';

export interface ModelConfig { temperature: number; max_tokens: number; top_p: number; stream: boolean; }
export interface ModelConfigurationPanelProps { onSave?: (config: ModelConfig) => void; className?: string; }

export default function ModelConfigurationPanel({ onSave, className = '' }: ModelConfigurationPanelProps) {
  const [config, setConfig] = useState<ModelConfig>({ temperature: 0.7, max_tokens: 2000, top_p: 0.9, stream: true });
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle className="flex items-center gap-2"><Settings className="h-5 w-5" />Configuration</CardTitle></CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between"><Label>Temperature</Label><span className="text-sm text-muted-foreground">{config.temperature}</span></div>
          <Slider value={[config.temperature]} onValueChange={([v]) => setConfig({ ...config, temperature: v })} max={2} step={0.1} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between"><Label>Max Tokens</Label><span className="text-sm text-muted-foreground">{config.max_tokens}</span></div>
          <Slider value={[config.max_tokens]} onValueChange={([v]) => setConfig({ ...config, max_tokens: v })} max={4096} step={100} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between"><Label>Top P</Label><span className="text-sm text-muted-foreground">{config.top_p}</span></div>
          <Slider value={[config.top_p]} onValueChange={([v]) => setConfig({ ...config, top_p: v })} max={1} step={0.05} />
        </div>
        <div className="flex items-center justify-between">
          <Label>Enable Streaming</Label>
          <Switch checked={config.stream} onCheckedChange={(v) => setConfig({ ...config, stream: v })} />
        </div>
        <Button onClick={() => onSave?.(config)} className="w-full"><Save className="h-4 w-4 mr-2" />Save Configuration</Button>
      </CardContent>
    </Card>
  );
}

export { ModelConfigurationPanel };
