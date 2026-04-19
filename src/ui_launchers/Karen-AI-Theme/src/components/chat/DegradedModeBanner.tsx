"use client";

import React from 'react';

interface DegradedModeBannerProps {
  reason: string;
  fallbackPath?: string;
  onDismiss?: () => void;
}

export default function DegradedModeBanner({ reason, fallbackPath, onDismiss }: DegradedModeBannerProps) {
  return (
    <div className="w-full p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded-r-lg mb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <svg className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.932-3L13.932 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.932 3h13.856c1.54 0 2.502-1.667 1.932-3z"
            />
          </svg>
          <div className="flex flex-col">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              System operating in degraded mode
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
              {reason}
            </p>
            {fallbackPath && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                Fallback path: {fallbackPath}
              </p>
            )}
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 p-1 hover:bg-amber-100 dark:hover:bg-amber-800/30 rounded transition-colors"
            aria-label="Dismiss notification"
          >
            <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
