/**
 * Enhanced Model Selector - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react';

export interface SelectorModel { id: string; name: string; provider: string; status: string; recommended: boolean; }
export interface EnhancedModelSelectorProps { models: SelectorModel[]; onSelect: (id: string) => void; showRecommendations?: boolean; className?: string; }

export default function EnhancedModelSelector({ models, onSelect, showRecommendations = true, className = '' }: EnhancedModelSelectorProps) {
  const [selected, setSelected] = useState<string>('');
  const recommended = models.filter(m => m.recommended);
  
  const handleSelect = (id: string) => {
    setSelected(id);
    onSelect(id);
  };
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle>Select Model</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {showRecommendations && recommended.length > 0 && (
          <div className="p-3 bg-purple-50 dark:bg-purple-950/20 rounded border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span className="font-medium text-sm">Recommended</span>
            </div>
            <div className="space-y-2">
              {recommended.map(m => (
                <Button key={m.id} onClick={() => handleSelect(m.id)} variant="outline" className="w-full justify-start">
                  <div className="flex items-center justify-between w-full">
                    <span>{m.name}</span>
                    <Badge>{m.provider}</Badge>
                  </div>
                </Button>
              ))}
            </div>
          </div>
        )}
        <Select value={selected} onValueChange={handleSelect}>
          <SelectTrigger><SelectValue placeholder="Choose a model..." /></SelectTrigger>
          <SelectContent>
            {models.map(m => (
              <SelectItem key={m.id} value={m.id}>
                <div className="flex items-center gap-2">
                  <span>{m.name}</span>
                  <Badge variant="secondary">{m.provider}</Badge>
                  {m.recommended && <Sparkles className="h-3 w-3 text-purple-500" />}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
    </Card>
  );
}

export { EnhancedModelSelector };
