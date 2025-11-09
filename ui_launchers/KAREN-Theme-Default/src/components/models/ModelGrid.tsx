/**
 * Model Grid - Production Grade
 */
"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download, Info } from 'lucide-react';

export interface GridModel { id: string; name: string; provider: string; size: string; status: string; }
export interface ModelGridProps { models: GridModel[]; onSelect?: (id: string) => void; className?: string; }

export default function ModelGrid({ models, onSelect, className = '' }: ModelGridProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
      {models.map(m => (
        <Card key={m.id} className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => onSelect?.(m.id)}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{m.name}</CardTitle>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">{m.provider}</Badge>
              <Badge variant="outline">{m.size}</Badge>
            </div>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button size="sm" variant="outline" className="flex-1"><Info className="h-4 w-4 mr-1" />Details</Button>
            <Button size="sm" className="flex-1"><Download className="h-4 w-4 mr-1" />Install</Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export { ModelGrid };
