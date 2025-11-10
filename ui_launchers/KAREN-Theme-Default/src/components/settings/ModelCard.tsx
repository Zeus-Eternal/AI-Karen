"use client";

import * as React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Cpu, Zap, DollarSign, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description?: string;
  category?: string;
  capabilities?: string[];
  pricing?: {
    input?: number;
    output?: number;
  };
  performance?: {
    speed?: 'fast' | 'medium' | 'slow';
    quality?: 'high' | 'medium' | 'low';
  };
  status?: 'active' | 'beta' | 'deprecated' | 'available' | 'downloading' | 'local' | 'error';
}

export interface ModelCardProps {
  model: ModelInfo;
  selected?: boolean;
  onSelect?: (modelId: string) => void;
  onViewDetails?: (modelId: string) => void;
  footerContent?: React.ReactNode;
  className?: string;
}

export default function ModelCard({
  model,
  selected = false,
  onSelect,
  onViewDetails,
  footerContent,
  className,
}: ModelCardProps) {
  const getSpeedColor = (speed?: string) => {
    switch (speed) {
      case 'fast': return 'text-green-600 dark:text-green-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'slow': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusVariant = (status?: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'beta': return 'secondary';
      case 'deprecated': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <Card
      className={cn(
        'relative transition-all hover:shadow-md',
        selected && 'ring-2 ring-blue-500 border-blue-500',
        className
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{model.name}</CardTitle>
            <CardDescription className="text-sm mt-1">
              {model.provider}
            </CardDescription>
          </div>
          {selected && (
            <CheckCircle2 className="h-5 w-5 text-blue-500" />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {model.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {model.description}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          {model.category && (
            <Badge variant="outline">{model.category}</Badge>
          )}
          {model.status && (
            <Badge variant={getStatusVariant(model.status)}>
              {model.status}
            </Badge>
          )}
        </div>

        {model.capabilities && model.capabilities.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
              Capabilities:
            </p>
            <div className="flex flex-wrap gap-1">
              {model.capabilities.map((capability, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 text-sm">
          {model.performance?.speed && (
            <div className="flex items-center gap-1">
              <Zap className={cn('h-4 w-4', getSpeedColor(model.performance.speed))} />
              <span className="capitalize">{model.performance.speed}</span>
            </div>
          )}
          {model.performance?.quality && (
            <div className="flex items-center gap-1">
              <Cpu className="h-4 w-4" />
              <span className="capitalize">{model.performance.quality}</span>
            </div>
          )}
        </div>

        {model.pricing && (
          <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <DollarSign className="h-3 w-3" />
            <span>
              In: ${model.pricing.input?.toFixed(4) || '0'} / Out: ${model.pricing.output?.toFixed(4) || '0'}
            </span>
          </div>
        )}
      </CardContent>

      {(onSelect || onViewDetails || footerContent) && (
        <CardFooter className="gap-2 flex-wrap">
          {footerContent}
        {onSelect && (
          <Button
            variant={selected ? 'default' : 'outline'}
            size="sm"
            onClick={() => onSelect(model.id)}
            className="flex-1"
          >
            {selected ? 'Selected' : 'Select'}
          </Button>
        )}
        {onViewDetails && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewDetails(model.id)}
          >
            Details
          </Button>
        )}
        </CardFooter>
      )}
    </Card>
  );
}

export { ModelCard };
