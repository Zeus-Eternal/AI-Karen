/**
 * Model Compatibility Badge - Production Grade
 */
"use client";

import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export type CompatibilityStatus = 'compatible' | 'incompatible' | 'partial';
export interface ModelCompatibilityBadgeProps { status: CompatibilityStatus; details?: string; className?: string; }

export default function ModelCompatibilityBadge({ status, details, className = '' }: ModelCompatibilityBadgeProps) {
  const config = {
    compatible: { icon: CheckCircle2, variant: 'default' as const, label: 'Compatible', color: 'text-green-500' },
    incompatible: { icon: XCircle, variant: 'destructive' as const, label: 'Incompatible', color: 'text-red-500' },
    partial: { icon: AlertCircle, variant: 'secondary' as const, label: 'Partial', color: 'text-yellow-500' }
  }[status];
  
  const Icon = config.icon;
  
  return (
    <Badge variant={config.variant} className={`flex items-center gap-1 ${className}`} title={details}>
      <Icon className={`h-3 w-3 ${config.color}`} />
      {config.label}
    </Badge>
  );
}

export { ModelCompatibilityBadge };
