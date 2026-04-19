"use client";

import React from 'react';
import type { Citation } from '@/lib/types';

interface CitationBadgeProps {
  citations?: Citation[];
  onClick?: () => void;
}

export default function CitationBadge({ citations, onClick }: CitationBadgeProps) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
      title={`${citations.length} source${citations.length !== 1 ? 's' : ''}`}
    >
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
      <span>{citations.length} source{citations.length !== 1 ? 's' : ''}</span>
    </button>
  );
}
