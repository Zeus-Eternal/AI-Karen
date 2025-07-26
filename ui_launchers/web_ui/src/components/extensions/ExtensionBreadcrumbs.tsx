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
    dispatch({ type: 'RESET_BREADCRUMBS' });
    breadcrumbs.slice(0, index).forEach((item) => {
      dispatch({ type: 'PUSH_BREADCRUMB', item });
    });
  };

  return (
    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
      {breadcrumbs.map((crumb, idx) => (
        <React.Fragment key={crumb.id}>
          <button
            className="hover:underline"
            onClick={() => handleClick(idx)}
            type="button"
          >
            {crumb.label}
          </button>
          {idx < breadcrumbs.length - 1 && <Separator orientation="vertical" className="h-4" />}
        </React.Fragment>
      ))}
    </div>
  );
}
