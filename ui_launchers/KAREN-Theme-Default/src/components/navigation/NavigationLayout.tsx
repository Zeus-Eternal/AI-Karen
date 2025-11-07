"use client";

import React, { ReactNode } from 'react';

export interface NavigationLayoutProps {
  children?: ReactNode;
  showBreadcrumbs?: boolean;
}

export default function NavigationLayout({ children, showBreadcrumbs }: NavigationLayoutProps) {
  return (
    <div>
      <h3>NavigationLayout</h3>
      <p>This component is temporarily disabled for production build.</p>
      {children}
    </div>
  );
}

export { NavigationLayout };
