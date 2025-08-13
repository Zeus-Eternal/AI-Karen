'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';

interface MetaBarProps {
  confidence?: number;
  annotations?: number;
  latencyMs?: number;
  model?: string;
}

export const MetaBar: React.FC<MetaBarProps> = ({
  confidence,
  annotations,
  latencyMs,
  model,
}) => {
  const items: React.ReactNode[] = [];

  if (model) {
    items.push(
      <Badge key="model" variant="secondary" className="text-xs">
        Model: {model}
      </Badge>,
    );
  }

  if (typeof latencyMs === 'number') {
    items.push(
      <Badge key="latency" variant="secondary" className="text-xs">
        Latency: {latencyMs}ms
      </Badge>,
    );
  }

  if (typeof confidence === 'number') {
    items.push(
      <Badge key="confidence" variant="secondary" className="text-xs">
        Confidence: {confidence}
      </Badge>,
    );
  }

  if (typeof annotations === 'number') {
    items.push(
      <Badge key="annotations" variant="secondary" className="text-xs">
        Annotations: {annotations}
      </Badge>,
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 border-b border-border px-4 py-2">
      {items}
    </div>
  );
};

export default MetaBar;
