"use client";

import * as React from 'react';
import { useExtensionContext } from '../../../extensions/ExtensionContext';

export interface ExtensionHeaderProps {
  /** Optional custom title. Defaults to current category */
  title?: string;
}

export default function ExtensionHeader({ title }: ExtensionHeaderProps) {
  const {
    state: { currentCategory },
  } = useExtensionContext();
  return (
    <header className="p-2 border-b sm:p-4 md:p-6">
      <h2 className="text-lg font-semibold tracking-tight">
        {title ?? currentCategory}
      </h2>
    </header>
  );
}
