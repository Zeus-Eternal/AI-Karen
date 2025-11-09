"use client";

import React, { ReactNode } from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface NavigationLayoutProps {
  children?: ReactNode;
  showBreadcrumbs?: boolean;
  breadcrumbs?: { label: string; href?: string }[];
  className?: string;
}

export default function NavigationLayout({
  children,
  showBreadcrumbs = false,
  breadcrumbs = [],
  className,
}: NavigationLayoutProps) {
  return (
    <div className={cn('flex flex-col w-full', className)}>
      {showBreadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-2 px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
          <Home className="h-4 w-4 text-gray-500" />
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={index}>
              <ChevronRight className="h-4 w-4 text-gray-400" />
              {crumb.href ? (
                <a
                  href={crumb.href}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {crumb.label}
                </a>
              ) : (
                <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                  {crumb.label}
                </span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}
      <div className="flex-1 w-full">{children}</div>
    </div>
  );
}

export { NavigationLayout };
