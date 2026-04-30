'use client';

import React from 'react';
import type { Citation } from '@/lib/types';

interface CitationBadgeProps {
  citations?: Citation[];
  onClick?: () => void;
}

const getCitationCountLabel = (count: number): string => {
  return `${count} source${count === 1 ? '' : 's'}`;
};

export default function CitationBadge({
  citations,
  onClick,
}: CitationBadgeProps) {
  const citationCount = Array.isArray(citations) ? citations.length : 0;

  if (citationCount === 0) {
    return null;
  }

  const label = getCitationCountLabel(citationCount);
  const isInteractive = typeof onClick === 'function';

  /*
   * CitationBadge is display UI only. It should reflect the citations supplied
   * by the backend/message metadata and must not invent or resolve sources here.
   */
  return (
    <button
      type="button"
      onClick={isInteractive ? onClick : undefined}
      disabled={!isInteractive}
      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
        isInteractive
          ? 'bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:cursor-default dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800'
          : 'cursor-default bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
      }`}
      title={label}
      aria-label={isInteractive ? `Show ${label}` : label}
    >
      <svg
        className="h-3 w-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
        />
      </svg>

      <span>{label}</span>
    </button>
  );
}