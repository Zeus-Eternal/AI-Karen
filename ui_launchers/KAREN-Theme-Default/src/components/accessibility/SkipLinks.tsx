"use client";

import * as React from 'react';
import { cn } from '../../lib/utils';

interface SkipLink {
  href: string;
  label: string;
}

interface SkipLinksProps {
  links?: SkipLink[];
  className?: string;
}

const defaultLinks: SkipLink[] = [
  { href: '#main-content', label: 'Skip to main content' },
  { href: '#navigation', label: 'Skip to navigation' },
  { href: '#search', label: 'Skip to search' },
];

export function SkipLinks({ links = defaultLinks, className }: SkipLinksProps) {
  return (
    <div className={cn('skip-links', className)}>
      {links.map((link, index) => (
        <a
          key={index}
          href={link.href}
          className={cn(
            // Base styles
            'absolute left-4 top-4 z-[9999]',
            'px-4 py-2 text-sm font-medium',
            'bg-primary text-primary-foreground',
            'border border-primary-foreground/20',
            'rounded-md shadow-lg',
            'transition-all duration-200',
            // Hidden by default
            '-translate-y-full opacity-0',
            // Visible on focus
            'focus:translate-y-0 focus:opacity-100',
            // Focus styles
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            // High contrast mode
            'high-contrast:bg-black high-contrast:text-white high-contrast:border-white'
          )}
          onFocus={(e) => {
            // Ensure the target element exists and is focusable
            const target = document.querySelector(link.href);
            if (target && !target.hasAttribute('tabindex')) {
              (target as HTMLElement).setAttribute('tabindex', '-1');
            }
          }}
        >
          {link.label}
        </a>
      ))}
    </div>
  );
}

export default SkipLinks;