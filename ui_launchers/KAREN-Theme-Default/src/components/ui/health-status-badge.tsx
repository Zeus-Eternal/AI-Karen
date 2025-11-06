"use client";

import React from 'react';
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';

export type HealthStatus = 'healthy' | 'degraded' | 'error' | 'unknown';

export function HealthStatusBadge() {
  const [status, setStatus] = useState<HealthStatus>('unknown');
  const [tooltip, setTooltip] = useState<string>("");

  useEffect(() => {
    let mounted = true;

    const fetchHealth = async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 4000);
        const res = await fetch('/api/health', { cache: 'no-store', signal: controller.signal });
        clearTimeout(timeout);
        const data = await res.json().catch(() => ({}));
        const s = (data?.status as HealthStatus) || 'unknown';
        if (mounted) {
          setStatus(['healthy', 'degraded', 'error'].includes(s) ? s : 'unknown');
          setTooltip(
            `providers: ${data?.total_providers ?? 0}, models: ${data?.models_available ?? 0}`
          );
        }
      } catch {
        if (mounted) {
          setStatus('degraded');
          setTooltip('backend unreachable');
        }
      }
    };

    fetchHealth();
    const id = setInterval(fetchHealth, 15000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  const colorClasses: Record<HealthStatus, string> = {
    healthy: 'bg-emerald-500 text-emerald-50 border-emerald-600',
    degraded: 'bg-amber-500 text-amber-50 border-amber-600',
    error: 'bg-red-500 text-red-50 border-red-600',
    unknown: 'bg-slate-500 text-slate-50 border-slate-600',
  };

  const dotColor: Record<HealthStatus, string> = {
    healthy: 'bg-emerald-300',
    degraded: 'bg-amber-300',
    error: 'bg-red-300',
    unknown: 'bg-slate-300',
  };

  return (
    <div className="pointer-events-none select-none fixed top-2 right-2 z-40">
      <Badge
        variant="outline"
        className={`pointer-events-auto select-auto border px-2 py-1 text-xs font-medium shadow-sm ${colorClasses[status]}`}
        title={tooltip}
      >
        <span className={`mr-1 inline-block h-2 w-2 rounded-full ${dotColor[status]}`} />
        {status}
      </Badge>
    </div>
  );
}

