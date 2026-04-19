"use client";

import React, { useState } from 'react';
import type { Citation } from '@/lib/types';

interface SourceListProps {
  citations?: Citation[];
}

export default function SourceList({ citations }: SourceListProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
      >
        <svg
          className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
        <span>Sources ({citations.length})</span>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {citations.map((citation, index) => (
            <div
              key={citation.id}
              className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-medium flex items-center justify-center">
                  {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline truncate block"
                    title={citation.title}
                  >
                    {citation.title}
                  </a>
                  {citation.snippet && (
                    <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                      {typeof citation.snippet === 'string' ? citation.snippet : String(citation.snippet)}
                    </p>
                  )}
                  {citation.metadata && typeof citation.metadata.domain === 'string' && (
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                      {String(citation.metadata.domain)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
