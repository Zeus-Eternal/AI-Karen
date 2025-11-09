"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Cpu, Search, ChevronDown, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Model {
  id: string;
  name: string;
  provider: string;
  category?: string;
  features?: string[];
}

export interface EnhancedModelSelectorProps {
  models?: Model[];
  selectedModel?: string;
  onModelChange?: (modelId: string) => void;
  variant?: 'select' | 'popover';
  showSearch?: boolean;
  className?: string;
}

export default function EnhancedModelSelector({
  models = [],
  selectedModel,
  onModelChange,
  variant = 'select',
  showSearch = true,
  className,
}: EnhancedModelSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [open, setOpen] = useState(false);

  const filteredModels = models.filter(
    (model) =>
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedModelData = models.find((m) => m.id === selectedModel);

  const handleSelect = (modelId: string) => {
    if (onModelChange) {
      onModelChange(modelId);
    }
    setOpen(false);
  };

  if (variant === 'popover') {
    return (
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn('justify-between', className)}
          >
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              <span className="truncate">
                {selectedModelData?.name || 'Select model...'}
              </span>
            </div>
            <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[400px] p-0">
          {showSearch && (
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search models..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          )}
          <div className="max-h-[300px] overflow-auto p-1">
            {filteredModels.length === 0 ? (
              <div className="py-6 text-center text-sm text-gray-500">
                No models found
              </div>
            ) : (
              filteredModels.map((model) => (
                <button
                  key={model.id}
                  onClick={() => handleSelect(model.id)}
                  className={cn(
                    'w-full flex items-start gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
                    selectedModel === model.id && 'bg-gray-100 dark:bg-gray-800'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium truncate">{model.name}</p>
                      {selectedModel === model.id && (
                        <CheckCircle2 className="h-4 w-4 text-blue-600 shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-gray-500 truncate">
                      {model.provider}
                    </p>
                    {model.category && (
                      <Badge variant="secondary" className="mt-1 text-xs">
                        {model.category}
                      </Badge>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </PopoverContent>
      </Popover>
    );
  }

  // Default select variant
  return (
    <Select value={selectedModel} onValueChange={onModelChange}>
      <SelectTrigger className={cn('w-full', className)}>
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4" />
          <SelectValue placeholder="Select model..." />
        </div>
      </SelectTrigger>
      <SelectContent>
        {models.map((model) => (
          <SelectItem key={model.id} value={model.id}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{model.name}</div>
                <div className="text-xs text-gray-500 truncate">
                  {model.provider}
                </div>
              </div>
              {model.category && (
                <Badge variant="secondary" className="text-xs">
                  {model.category}
                </Badge>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export { EnhancedModelSelector };
