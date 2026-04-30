'use client';

import React from 'react';

type ToolActivityStatus = 'idle' | 'in_progress' | 'completed' | 'failed';

interface ToolActivityBadgeProps {
  toolName: string;
  status?: ToolActivityStatus;
  executionTime?: number;
}

const DEFAULT_TOOL_NAME = 'Tool';

const STATUS_LABELS: Record<Exclude<ToolActivityStatus, 'idle'>, string> = {
  in_progress: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

const STATUS_CLASSES: Record<Exclude<ToolActivityStatus, 'idle'>, string> = {
  in_progress:
    'border-blue-500/40 bg-blue-500/10 text-blue-700 dark:text-blue-300',
  completed:
    'border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  failed:
    'border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300',
};

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const formatToolName = (toolName: unknown): string => {
  return cleanString(toolName) || DEFAULT_TOOL_NAME;
};

const formatExecutionTime = (executionTime: unknown): string => {
  if (typeof executionTime !== 'number' || !Number.isFinite(executionTime)) {
    return '';
  }

  if (executionTime < 1000) {
    return `${Math.max(0, Math.round(executionTime))}ms`;
  }

  return `${(executionTime / 1000).toFixed(2)}s`;
};

export function ToolActivityBadge({
  toolName,
  status = 'idle',
  executionTime,
}: ToolActivityBadgeProps) {
  if (status === 'idle') {
    return null;
  }

  const safeToolName = formatToolName(toolName);
  const executionTimeLabel = formatExecutionTime(executionTime);
  const statusLabel = STATUS_LABELS[status];

  /*
   * ToolActivityBadge is observability UI only.
   * Tool execution state must come from backend events or message metadata,
   * never from UI-side inference.
   */
  return (
    <div
      role="status"
      aria-live={status === 'in_progress' ? 'polite' : 'off'}
      className={`inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs font-medium shadow-sm ${STATUS_CLASSES[status]}`}
      title={`${safeToolName}: ${statusLabel}${
        executionTimeLabel ? ` in ${executionTimeLabel}` : ''
      }`}
    >
      <span className="max-w-[180px] truncate">{safeToolName}</span>

      <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wide opacity-80">
        {status === 'in_progress' && (
          <span aria-hidden="true" className="animate-pulse">
            ⏳
          </span>
        )}

        {status === 'completed' && (
          <span aria-hidden="true">
            ✓
          </span>
        )}

        {status === 'failed' && (
          <span aria-hidden="true">
            ✕
          </span>
        )}

        <span>{statusLabel}</span>
      </span>

      {status === 'completed' && executionTimeLabel && (
        <span className="text-[10px] opacity-70">{executionTimeLabel}</span>
      )}
    </div>
  );
}