"use client";

import * as React from 'react';
export interface SearchHighlightProps {
  text: string;
  searchQuery: string;
  className?: string;
}

/**
 * @file SearchHighlight.tsx
 * @description Component for highlighting search terms in text.
 * Used to highlight matching terms in model names, descriptions, and tags.
 */
export default function SearchHighlight({ text, searchQuery, className = '' }: SearchHighlightProps) {
  if (!searchQuery || !text) {
    return <span className={className}>{text}</span>;
  }

  // Create a regex to find all instances of the search query (case insensitive)
  const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        // Check if this part matches the search query
        const isMatch = regex.test(part);
        regex.lastIndex = 0; // Reset regex for next test
        
        return isMatch ? (
          <mark
            key={index}
            className="bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-100 px-0.5 rounded"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        );
      })}
    </span>
  );
}