/**
 * Breadcrumb navigation for the Extension Manager sidebar.
 * Displays the current hierarchy path and allows quick navigation
 * back to a parent level.
 */
"use client";

import React from 'react';
import { Separator } from '@/components/ui/separator';
import { useExtensionContext } from '@/extensions';

export default function ExtensionBreadcrumbs() {
  const {
    state: { breadcrumbs },
    dispatch,
  } = useExtensionContext();

  if (breadcrumbs.length === 0) {
    return null;
  }

  const handleClick = (index: number) => {
    dispatch({ type: 'SET_LEVEL', level: index + 1 });
  };

  return (
    <div className="flex items-center space-x-2 text-sm text-muted-foreground md:text-base lg:text-lg">
      {breadcrumbs.map((crumb, idx) => (
        <React.Fragment key={crumb.id}>
          <button
            className="hover:underline"
            onClick={() => handleClick(idx)}
            type="button"
          >
            {crumb.name}
          </button>
          {idx < breadcrumbs.length - 1 && <Separator orientation="vertical" className="h-4" />}
        </React.Fragment>
      ))}
    </div>
  );
}
