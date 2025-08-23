"use client";
import React from 'react';
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
    <header className="p-2 border-b">
      <h2 className="text-lg font-semibold tracking-tight">
        {title ?? currentCategory}
      </h2>
    </header>
  );
}
