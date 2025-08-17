'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { webUIConfig } from '@/lib/config';

interface MetaBarProps {
  confidence?: number;
  annotations?: number;
  latencyMs?: number;
  model?: string;
  persona?: string;
  mood?: string;
  intent?: string;
  reasoning?: string;
  sources?: string[];
}

export const MetaBar: React.FC<MetaBarProps> = ({
  confidence,
  annotations,
  latencyMs,
  model,
  persona,
  mood,
  intent,
  reasoning,
  sources,
}) => {
  const items: React.ReactNode[] = [];

  if (model && webUIConfig.showModelBadge) {
    items.push(
      <Badge key="model" variant="secondary" className="text-xs">
        Model: {model}
      </Badge>,
    );
  }

  if (typeof latencyMs === 'number' && webUIConfig.showLatencyBadge) {
    items.push(
      <Badge key="latency" variant="secondary" className="text-xs">
        Latency: {latencyMs}ms
      </Badge>,
    );
  }

  if (typeof confidence === 'number' && webUIConfig.showConfidenceBadge) {
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

  if (persona) {
    items.push(
      <Badge key="persona" variant="outline" className="text-xs">
        Persona: {persona}
      </Badge>,
    );
  }

  if (mood) {
    items.push(
      <Badge key="mood" variant="outline" className="text-xs">
        Mood: {mood}
      </Badge>,
    );
  }

  if (intent) {
    items.push(
      <Badge key="intent" variant="outline" className="text-xs">
        Intent: {intent}
      </Badge>,
    );
  }

  if (reasoning) {
    items.push(
      <Badge key="reasoning" variant="outline" className="text-xs" title={reasoning}>
        Reasoning: {reasoning.length > 30 ? reasoning.substring(0, 30) + '...' : reasoning}
      </Badge>,
    );
  }

  if (sources && sources.length > 0) {
    items.push(
      <Badge key="sources" variant="outline" className="text-xs">
        Sources: {sources.length}
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
