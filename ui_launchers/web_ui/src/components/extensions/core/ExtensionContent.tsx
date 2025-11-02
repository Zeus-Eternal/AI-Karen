"use client";

import React from 'react';

export interface ExtensionContentProps {
  children: React.ReactNode;
  className?: string;
}

export default function ExtensionContent({ children, className }: ExtensionContentProps) {
  return <div className={className ?? 'p-2 space-y-2'}>{children}</div>;
}
