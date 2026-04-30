'use client';

import React, { useId, useMemo, useState } from 'react';
import type { Citation } from '@/lib/types';

interface InlineCitationProps {
  index: number;
  citation: Citation;
}

const DEFAULT_CITATION_TITLE = 'Untitled source';

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const stringifyValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value.trim();
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (value == null) {
    return '';
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

const getSafeUrl = (value: unknown): string => {
  const rawUrl = cleanString(value);

  if (!rawUrl) {
    return '';
  }

  try {
    const parsed = new URL(rawUrl);

    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.toString();
    }
  } catch {
    return '';
  }

  return '';
};

const getCitationDomain = (citation: Citation): string => {
  const metadataDomain =
    citation.metadata && typeof citation.metadata.domain === 'string'
      ? citation.metadata.domain
      : '';

  if (metadataDomain.trim()) {
    return metadataDomain.trim();
  }

  const safeUrl = getSafeUrl(citation.url);

  if (!safeUrl) {
    return '';
  }

  try {
    return new URL(safeUrl).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
};

export default function InlineCitation({
  index,
  citation,
}: InlineCitationProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const tooltipId = useId();

  const citationNumber = Math.max(1, index + 1);

  const title = useMemo(() => {
    return cleanString(citation.title) || DEFAULT_CITATION_TITLE;
  }, [citation.title]);

  const snippet = useMemo(() => {
    return stringifyValue(citation.snippet);
  }, [citation.snippet]);

  const safeUrl = useMemo(() => {
    return getSafeUrl(citation.url);
  }, [citation.url]);

  const domain = useMemo(() => {
    return getCitationDomain(citation);
  }, [citation]);

  /*
   * InlineCitation displays citation data already attached to the message.
   * It should not resolve, fetch, enrich, or invent sources in the UI layer.
   */
  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        type="button"
        className="inline-flex h-5 w-5 items-center justify-center rounded bg-blue-100 font-mono text-xs text-blue-700 transition-colors hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
        title={`Source ${citationNumber}`}
        aria-label={`Show source ${citationNumber}`}
        aria-describedby={showTooltip ? tooltipId : undefined}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        onClick={() => {
          if (safeUrl && typeof window !== 'undefined') {
            window.open(safeUrl, '_blank', 'noopener,noreferrer');
          }
        }}
      >
        {citationNumber}
      </button>

      {showTooltip && (
        <div
          id={tooltipId}
          role="tooltip"
          className="absolute left-full top-0 z-50 ml-2 w-72 rounded-lg border border-gray-200 bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-800"
        >
          <div className="flex flex-col gap-2">
            {safeUrl ? (
              <a
                href={safeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="truncate text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                title={title}
              >
                {title}
              </a>
            ) : (
              <span
                className="truncate text-sm font-medium text-gray-700 dark:text-gray-300"
                title={title}
              >
                {title}
              </span>
            )}

            {snippet && (
              <p className="line-clamp-3 text-xs text-gray-600 dark:text-gray-400">
                {snippet}
              </p>
            )}

            {domain && (
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {domain}
              </p>
            )}
          </div>
        </div>
      )}
    </span>
  );
}