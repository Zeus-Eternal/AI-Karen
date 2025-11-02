"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Panel content props interface
 */
export interface PanelContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Content padding variant */
  padding?: "none" | "xs" | "sm" | "md" | "lg" | "xl";
  /** Whether content should scroll */
  scrollable?: boolean;
  /** Content alignment */
  align?: "start" | "center" | "end";
  /** Content justification */
  justify?: "start" | "center" | "end" | "between";
  /** Whether to use full height */
  fullHeight?: boolean;
  /** Grid columns to span (1-12) */
  columns?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  /** Grid column offset */
  offset?: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;
}

// ============================================================================
// STYLE MAPPINGS
// ============================================================================

/**
 * Content padding class mappings with responsive behavior
 */
const CONTENT_PADDING_CLASSES = {
  none: "p-0",
  xs: "p-1.5 sm:p-2",
  sm: "p-2 sm:p-3",
  md: "p-3 sm:p-4 md:p-4",
  lg: "p-4 sm:p-5 md:p-6",
  xl: "p-5 sm:p-6 md:p-8",
} as const;

/**
 * Content alignment class mappings
 */
const CONTENT_ALIGN_CLASSES = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
} as const;

/**
 * Content justification class mappings
 */
const CONTENT_JUSTIFY_CLASSES = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
} as const;

/**
 * Grid column span class mappings
 */
const GRID_COLUMN_CLASSES = {
  1: "col-span-1",
  2: "col-span-2",
  3: "col-span-3",
  4: "col-span-4",
  5: "col-span-5",
  6: "col-span-6",
  7: "col-span-7",
  8: "col-span-8",
  9: "col-span-9",
  10: "col-span-10",
  11: "col-span-11",
  12: "col-span-12",
} as const;

/**
 * Grid column offset class mappings
 */
const GRID_OFFSET_CLASSES = {
  0: "",
  1: "col-start-2",
  2: "col-start-3",
  3: "col-start-4",
  4: "col-start-5",
  5: "col-start-6",
  6: "col-start-7",
  7: "col-start-8",
  8: "col-start-9",
  9: "col-start-10",
  10: "col-start-11",
  11: "col-start-12",
} as const;

// ============================================================================
// COMPONENT
// ============================================================================

/**
 * Reusable Panel Content Component
 * 
 * Provides consistent content structure with 12-column grid system,
 * proper overflow handling, and flexible layout options.
 */
export const PanelContent = forwardRef<HTMLDivElement, PanelContentProps>(
  function PanelContent(
    {
      padding = "md",
      scrollable = true,
      align = "start",
      justify = "start",
      fullHeight = true,
      columns = 12,
      offset = 0,
      className,
      children,
      ...props
    },
    ref
  ) {
    const paddingClass = CONTENT_PADDING_CLASSES[padding];
    const alignClass = CONTENT_ALIGN_CLASSES[align];
    const justifyClass = CONTENT_JUSTIFY_CLASSES[justify];
    const columnClass = GRID_COLUMN_CLASSES[columns];
    const offsetClass = GRID_OFFSET_CLASSES[offset];

    return (
      <div
        ref={ref}
        className={cn(
          "flex-1",
          fullHeight && "min-h-0",
          // Proper overflow handling with smooth scrolling
          scrollable && "overflow-y-auto overflow-x-hidden scrollbar-hide",
          scrollable && "scroll-smooth",
          paddingClass,
          className
        )}
        style={{
          // Ensure proper scrolling behavior
          scrollBehavior: 'smooth',
          // Optimize for scrolling performance
          willChange: scrollable ? 'scroll-position' : 'auto',
        }}
        {...props}
      >
        <div className={cn(
          "grid grid-cols-12",
          // Responsive gap
          "gap-2 sm:gap-3 md:gap-4",
          fullHeight && "min-h-full",
          // Proper content alignment
          alignClass,
          justifyClass,
          // Ensure content doesn't cause horizontal overflow
          "w-full max-w-full"
        )}>
          <div className={cn(
            columnClass, 
            offsetClass,
            // Prevent content from overflowing
            "min-w-0 max-w-full",
            // Responsive vertical spacing
            "space-y-2 sm:space-y-3 md:space-y-4"
          )}>
            {children}
          </div>
        </div>
      </div>
    );
  }
);

PanelContent.displayName = "PanelContent";

// ============================================================================
// SPECIALIZED CONTENT COMPONENTS
// ============================================================================

/**
 * Panel content section with semantic structure
 */
export interface PanelSectionProps extends Omit<PanelContentProps, 'children'> {
  /** Section title */
  title?: string;
  /** Section description */
  description?: string;
  /** Section content */
  children: React.ReactNode;
  /** Section header actions */
  actions?: React.ReactNode;
}

/**
 * Panel Section Component
 */
export const PanelSection = forwardRef<HTMLDivElement, PanelSectionProps>(
  function PanelSection(
    {
      title,
      description,
      actions,
      children,
      ...contentProps
    },
    ref
  ) {
    return (
      <PanelContent ref={ref} {...contentProps}>
        <section className="space-y-4">
          {(title || description || actions) && (
            <header className="space-y-2">
              {(title || actions) && (
                <div className="flex items-center justify-between">
                  {title && (
                    <h3 className="text-base font-medium tracking-tight">
                      {title}
                    </h3>
                  )}
                  {actions && (
                    <div className="flex items-center gap-2">
                      {actions}
                    </div>
                  )}
                </div>
              )}
              {description && (
                <p className="text-sm text-muted-foreground">
                  {description}
                </p>
              )}
            </header>
          )}
          <div className="space-y-4">
            {children}
          </div>
        </section>
      </PanelContent>
    );
  }
);

PanelSection.displayName = "PanelSection";

// ============================================================================
// COMPOUND COMPONENT EXPORTS
// ============================================================================

/**
 * Compound component pattern export
 */
(PanelContent as any).Section = PanelSection;