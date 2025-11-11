'use client';

import React from 'react';

import type { SkipLink } from './skip-links';

export interface SkipLinksApi {
  skipLinks: SkipLink[];
  addSkipLink: (link: SkipLink) => void;
  removeSkipLink: (id: string) => void;
  clearSkipLinks: () => void;
}

export const useSkipLinks = (): SkipLinksApi => {
  const [skipLinks, setSkipLinks] = React.useState<SkipLink[]>([]);

  const addSkipLink = React.useCallback((link: SkipLink) => {
    setSkipLinks((prev) => {
      const exists = prev.some((existing) => existing.id === link.id);
      if (exists) {
        return prev.map((existing) =>
          existing.id === link.id ? link : existing
        );
      }
      return [...prev, link];
    });
  }, []);

  const removeSkipLink = React.useCallback((id: string) => {
    setSkipLinks((prev) => prev.filter((link) => link.id !== id));
  }, []);

  const clearSkipLinks = React.useCallback(() => {
    setSkipLinks([]);
  }, []);

  return {
    skipLinks,
    addSkipLink,
    removeSkipLink,
    clearSkipLinks,
  };
};

export const DEFAULT_SKIP_LINKS: SkipLink[] = [
  {
    id: 'skip-to-main',
    target: 'main-content',
    label: 'Skip to main content',
    description: 'Jump to the main content area of the page',
  },
  {
    id: 'skip-to-nav',
    target: 'main-navigation',
    label: 'Skip to navigation',
    description: 'Jump to the main navigation menu',
  },
  {
    id: 'skip-to-search',
    target: 'search',
    label: 'Skip to search',
    description: 'Jump to the search functionality',
  },
  {
    id: 'skip-to-footer',
    target: 'footer',
    label: 'Skip to footer',
    description: 'Jump to the page footer',
  },
];
