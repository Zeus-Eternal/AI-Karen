/**
 * Model Card - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Server, Zap, HardDrive } from 'lucide-react';

export interface CardModel { name: string; description: string; provider: string; size: string; capabilities: string[]; }
export interface ModelCardProps { model: CardModel; onSelect?: () => void; className?: string; }

export default function ModelCard({ model, onSelect, className = '' }: ModelCardProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{model.name}</CardTitle>
        <CardDescription>{model.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-1"><Server className="h-4 w-4" />{model.provider}</div>
          <div className="flex items-center gap-1"><HardDrive className="h-4 w-4" />{model.size}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {model.capabilities.map(c => <Badge key={c} variant="secondary">{c}</Badge>)}
        </div>
        <Button onClick={onSelect} className="w-full">Select Model</Button>
      </CardContent>
    </Card>
  );
}

export { ModelCard };
