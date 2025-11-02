'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { webUIConfig } from '@/lib/config';

interface MetaBarProps {
  confidence?: number;
  annotations?: number;
  latencyMs?: number;
  model?: string;
  tokens?: number;
  cost?: number;
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
  tokens,
  cost,
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

  if (typeof tokens === 'number' && tokens > 0) {
    items.push(
      <Badge key="tokens" variant="secondary" className="text-xs">
        Tokens: {tokens}
      </Badge>,
    );
  }

  if (typeof cost === 'number') {
    items.push(
      <Badge key="cost" variant="secondary" className="text-xs">
        Cost: ${'{'}cost.toFixed ? cost.toFixed(6) : cost{'}'}
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
    <div className="chat-meta-bar">
      <div className="container max-w-screen-xl flex flex-wrap items-center gap-2 py-2">
        {items}
      </div>
    </div>
  );
};

export default MetaBar;
