"use client";

import React from 'react';
import { cn } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
  className?: string;
}

interface LayoutGridProps extends LayoutProps {
  columns?: 'auto' | '1' | '2' | '3' | '4' | 'auto-fit' | 'auto-fill';
  gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  responsive?: boolean;
}

// Main Layout Container
export const Layout: React.FC<LayoutProps> = ({ children, className }) => (
  <div className={cn("container-fluid", className)}>
    {children}
  </div>
);

// Grid Layout Component
export const LayoutGrid: React.FC<LayoutGridProps> = ({ 
  children, 
  className, 
  columns = 'auto-fit',
  gap = 'md',
  responsive = true 
}) => {
  const gridClasses = cn(
    "grid",
    {
      // Grid columns
      "grid-cols-1": columns === '1',
      "grid-cols-2": columns === '2',
      "grid-cols-3": columns === '3',
      "grid-cols-4": columns === '4',
      "grid-cols-[auto_1fr]": columns === 'auto',
      "grid-cols-[repeat(auto-fit,minmax(300px,1fr))]": columns === 'auto-fit',
      "grid-cols-[repeat(auto-fill,minmax(300px,1fr))]": columns === 'auto-fill',
      
      // Gap sizes
      "gap-0": gap === 'none',
      "gap-2": gap === 'sm',
      "gap-4": gap === 'md',
      "gap-6": gap === 'lg',
      "gap-8": gap === 'xl',
      
      // Responsive behavior
      "md:grid-cols-2 lg:grid-cols-3": responsive && columns === 'auto-fit',
    },
    className
  );

  return (
    <div className={gridClasses}>
      {children}
    </div>
  );
};

// Flex Layout Component
export const LayoutFlex: React.FC<LayoutProps & {
  direction?: 'row' | 'col';
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around';
  wrap?: boolean;
  gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}> = ({ 
  children, 
  className,
  direction = 'row',
  align = 'start',
  justify = 'start',
  wrap = false,
  gap = 'md'
}) => {
  const flexClasses = cn(
    "flex",
    {
      // Direction
      "flex-row": direction === 'row',
      "flex-col": direction === 'col',
      
      // Align items
      "items-start": align === 'start',
      "items-center": align === 'center',
      "items-end": align === 'end',
      "items-stretch": align === 'stretch',
      
      // Justify content
      "justify-start": justify === 'start',
      "justify-center": justify === 'center',
      "justify-end": justify === 'end',
      "justify-between": justify === 'between',
      "justify-around": justify === 'around',
      
      // Wrap
      "flex-wrap": wrap,
      
      // Gap
      "gap-0": gap === 'none',
      "gap-2": gap === 'sm',
      "gap-4": gap === 'md',
      "gap-6": gap === 'lg',
      "gap-8": gap === 'xl',
    },
    className
  );

  return (
    <div className={flexClasses}>
      {children}
    </div>
  );
};

// Section Component with modern styling
export const LayoutSection: React.FC<LayoutProps & {
  variant?: 'default' | 'card' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}> = ({ 
  children, 
  className,
  variant = 'default',
  padding = 'md'
}) => {
  const sectionClasses = cn(
    {
      // Variants
      "": variant === 'default',
      "modern-card": variant === 'card',
      "glass": variant === 'glass',
      
      // Padding
      "p-0": padding === 'none',
      "p-2": padding === 'sm',
      "p-4": padding === 'md',
      "p-6": padding === 'lg',
      "p-8": padding === 'xl',
    },
    className
  );

  return (
    <section className={sectionClasses}>
      {children}
    </section>
  );
};

// Page Header Component
export const LayoutHeader: React.FC<{
  children?: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}> = ({ 
  children, 
  className,
  title,
  description,
  actions
}) => (
  <header className={cn("modern-card-header space-y-4", className)}>
    <div className="flex-between">
      <div className="space-y-1">
        {title && <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>}
        {description && <p className="text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
    {children}
  </header>
);

// Responsive Container with max-width constraints
export const LayoutContainer: React.FC<LayoutProps & {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  centered?: boolean;
}> = ({ 
  children, 
  className,
  size = 'lg',
  centered = true
}) => {
  const containerClasses = cn(
    "w-full px-4 sm:px-6 lg:px-8",
    {
      "max-w-2xl": size === 'sm',
      "max-w-4xl": size === 'md',
      "max-w-6xl": size === 'lg',
      "max-w-7xl": size === 'xl',
      "max-w-none": size === 'full',
      "mx-auto": centered,
    },
    className
  );

  return (
    <div className={containerClasses}>
      {children}
    </div>
  );
};
