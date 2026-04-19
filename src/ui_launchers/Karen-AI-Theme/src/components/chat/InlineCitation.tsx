"use client";

import React, { useState } from 'react';
import type { Citation } from '@/lib/types';

interface InlineCitationProps {
  index: number;
  citation: Citation;
}

export default function InlineCitation({ index, citation }: InlineCitationProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span
      className="inline-block relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        className="inline-flex items-center justify-center w-5 h-5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-mono hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
        title={`Source ${index + 1}`}
      >
        {index + 1}
      </button>

      {showTooltip && (
        <div className="absolute left-full ml-2 top-0 z-50 w-72 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="flex flex-col gap-2">
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline truncate"
              title={citation.title}
            >
              {citation.title}
            </a>
            {citation.snippet && (
              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">
                {typeof citation.snippet === 'string' ? citation.snippet : String(citation.snippet)}
              </p>
            )}
            {citation.metadata && typeof citation.metadata.domain === 'string' && (
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {String(citation.metadata.domain)}
              </p>
            )}
          </div>
        </div>
      )}
    </span>
  );
}
