"use client";

import * as React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Cpu, Zap, DollarSign, Info, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ModelInfo } from './ModelCard';

export interface ModelDetailsDialogProps {
  model: ModelInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect?: (modelId: string) => void;
  className?: string;
}

export default function ModelDetailsDialog({
  model,
  open,
  onOpenChange,
  onSelect,
  className,
}: ModelDetailsDialogProps) {
  if (!model) return null;

  const handleSelect = () => {
    if (onSelect) {
      onSelect(model.id);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('max-w-2xl', className)}>
        <DialogHeader>
          <DialogTitle className="text-2xl">{model.name}</DialogTitle>
          <DialogDescription className="text-base">
            {model.provider}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6">
            {/* Description */}
            {model.description && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Description
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {model.description}
                </p>
              </div>
            )}

            <Separator />

            {/* Status and Category */}
            <div className="flex flex-wrap gap-3">
              {model.category && (
                <div>
                  <p className="text-xs font-medium mb-1">Category</p>
                  <Badge variant="outline">{model.category}</Badge>
                </div>
              )}
              {model.status && (
                <div>
                  <p className="text-xs font-medium mb-1">Status</p>
                  <Badge
                    variant={
                      model.status === 'active'
                        ? 'default'
                        : model.status === 'beta'
                        ? 'secondary'
                        : 'destructive'
                    }
                  >
                    {model.status}
                  </Badge>
                </div>
              )}
            </div>

            {/* Capabilities */}
            {model.capabilities && model.capabilities.length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Capabilities
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {model.capabilities.map((capability, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 text-sm"
                      >
                        <CheckCircle className="h-3 w-3 text-green-500" />
                        <span>{capability}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Performance */}
            {model.performance && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-semibold mb-3">Performance</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {model.performance.speed && (
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-yellow-500" />
                        <div>
                          <p className="text-xs text-gray-500">Speed</p>
                          <p className="text-sm font-medium capitalize">
                            {model.performance.speed}
                          </p>
                        </div>
                      </div>
                    )}
                    {model.performance.quality && (
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-blue-500" />
                        <div>
                          <p className="text-xs text-gray-500">Quality</p>
                          <p className="text-sm font-medium capitalize">
                            {model.performance.quality}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Pricing */}
            {model.pricing && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Pricing
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500">Input Tokens</p>
                      <p className="text-sm font-medium">
                        ${model.pricing.input?.toFixed(4) || '0.0000'} per 1K
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Output Tokens</p>
                      <p className="text-sm font-medium">
                        ${model.pricing.output?.toFixed(4) || '0.0000'} per 1K
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Model ID */}
            <Separator />
            <div>
              <p className="text-xs text-gray-500">Model ID</p>
              <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                {model.id}
              </code>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {onSelect && (
            <Button onClick={handleSelect}>
              Select Model
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export { ModelDetailsDialog };
