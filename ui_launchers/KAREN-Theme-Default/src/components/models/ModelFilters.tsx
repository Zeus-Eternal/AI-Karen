/**
 * Model Filters - Production Grade
 */
"use client";

import * as React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export interface FilterState { providers: string[]; statuses: string[]; sort: string; }
export interface ModelFiltersProps { filters: FilterState; onChange: (filters: FilterState) => void; className?: string; }

export default function ModelFilters({ filters, onChange, className = '' }: ModelFiltersProps) {
  const toggleProvider = (p: string) => {
    const providers = filters.providers.includes(p) ? filters.providers.filter(x => x !== p) : [...filters.providers, p];
    onChange({ ...filters, providers });
  };
  
  return (
    <Card className={className}>
      <CardContent className="pt-6 space-y-4">
        <div>
          <Label className="mb-3 block">Provider</Label>
          {['OpenAI', 'Anthropic', 'Meta'].map(p => (
            <div key={p} className="flex items-center space-x-2 mb-2">
              <Checkbox id={p} checked={filters.providers.includes(p)} onCheckedChange={() => toggleProvider(p)} />
              <label htmlFor={p} className="text-sm cursor-pointer">{p}</label>
            </div>
          ))}
        </div>
        <div>
          <Label className="mb-2 block">Sort By</Label>
          <Select value={filters.sort} onValueChange={(v) => onChange({ ...filters, sort: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="size">Size</SelectItem>
              <SelectItem value="popularity">Popularity</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}

export { ModelFilters };
