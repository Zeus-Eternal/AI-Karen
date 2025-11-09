/**
 * GridContainer Component
 * 
 * Modern CSS Grid wrapper component with TypeScript interfaces,
 * dynamic columns and rows, responsive behavior, and container query support.
 * 
 * Based on requirements: 1.4, 3.2
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

/**
 * Grid template areas type for named grid areas
 */
export type GridAreas = string | string[];

/**
 * Responsive breakpoint values
 */
export interface ResponsiveValue<T> {
  base?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}

/**
 * Grid container props interface
 */
export interface GridContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Number of columns or CSS grid-template-columns value */
  columns?: string | number | ResponsiveValue<string | number>;
  
  /** Number of rows or CSS grid-template-rows value */
  rows?: string | number | ResponsiveValue<string | number>;
  
  /** Gap between grid items */
  gap?: string | ResponsiveValue<string>;
  
  /** Column gap specifically */
  columnGap?: string | ResponsiveValue<string>;
  
  /** Row gap specifically */
  rowGap?: string | ResponsiveValue<string>;
  
  /** Named grid areas */
  areas?: GridAreas | ResponsiveValue<GridAreas>;
  
  /** Auto-fit columns with minimum width */
  autoFit?: string;
  
  /** Auto-fill columns with minimum width */
  autoFill?: string;
  
  /** Grid auto-flow direction */
  autoFlow?: 'row' | 'column' | 'row dense' | 'column dense';
  
  /** Justify items alignment */
  justifyItems?: 'start' | 'end' | 'center' | 'stretch';
  
  /** Align items alignment */
  alignItems?: 'start' | 'end' | 'center' | 'stretch' | 'baseline';
  
  /** Justify content alignment */
  justifyContent?: 'start' | 'end' | 'center' | 'stretch' | 'space-around' | 'space-between' | 'space-evenly';
  
  /** Align content alignment */
  alignContent?: 'start' | 'end' | 'center' | 'stretch' | 'space-around' | 'space-between' | 'space-evenly';
  
  /** Enable responsive behavior */
  responsive?: boolean;
  
  /** Enable container queries */
  containerQueries?: boolean;
  
  /** Container name for container queries */
  containerName?: string;
  
  /** Minimum height */
  minHeight?: string;
  
  /** Maximum height */
  maxHeight?: string;
  
  /** Children elements */
  children: React.ReactNode;
}

// ============================================================================
// COMPONENT VARIANTS
// ============================================================================

/**
 * Grid container variants using CVA
 */
const gridContainerVariants = cva(
  'grid',
  {
    variants: {
      responsive: {
        true: 'responsive-grid',
        false: '',
      },
      containerQueries: {
        true: 'container-grid',
        false: '',
      },
      autoFlow: {
        row: 'grid-flow-row',
        column: 'grid-flow-col',
        'row dense': 'grid-flow-row-dense',
        'column dense': 'grid-flow-col-dense',
      },
      justifyItems: {
        start: 'justify-items-start',
        end: 'justify-items-end',
        center: 'justify-items-center',
        stretch: 'justify-items-stretch',
      },
      alignItems: {
        start: 'items-start',
        end: 'items-end',
        center: 'items-center',
        stretch: 'items-stretch',
        baseline: 'items-baseline',
      },
      justifyContent: {
        start: 'justify-start',
        end: 'justify-end',
        center: 'justify-center',
        stretch: 'justify-stretch',
        'space-around': 'justify-around',
        'space-between': 'justify-between',
        'space-evenly': 'justify-evenly',
      },
      alignContent: {
        start: 'content-start',
        end: 'content-end',
        center: 'content-center',
        stretch: 'content-stretch',
        'space-around': 'content-around',
        'space-between': 'content-between',
        'space-evenly': 'content-evenly',
      },
    },
    defaultVariants: {
      responsive: false,
      containerQueries: false,
      justifyItems: 'stretch',
      alignItems: 'stretch',
    },
  }
);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Convert number to CSS grid template value
 */
function numberToGridTemplate(value: number): string {
  return `repeat(${value}, 1fr)`;
}

/**
 * Process grid template value
 */
function processGridTemplate(value: string | number): string {
  if (typeof value === 'number') {
    return numberToGridTemplate(value);
  }
  return value;
}

/**
 * Process responsive value
 */
function processResponsiveValue<T>(
  value: T | ResponsiveValue<T>,
  processor?: (val: T) => string
): Record<string, string> | string {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    const responsiveValue = value as ResponsiveValue<T>;
    const result: Record<string, string> = {};
    
    Object.entries(responsiveValue).forEach(([breakpoint, val]) => {
      if (val !== undefined) {
        const processedValue = processor ? processor(val) : String(val);
        if (breakpoint === 'base') {
          result['--grid-base'] = processedValue;
        } else {
          result[`--grid-${breakpoint}`] = processedValue;
        }
      }
    });

    return result;
  }
  
  return processor ? processor(value as T) : String(value);
}

/**
 * Process grid areas
 */
function processGridAreas(areas: GridAreas): string {
  if (Array.isArray(areas)) {
    return areas.map(area => `"${area}"`).join(' ');
  }
  return `"${areas}"`;
}

/**
 * Style-related properties for grid container
 */
export interface GridStyleProps {
  columns?: string | number | ResponsiveValue<string | number>;
  rows?: string | number | ResponsiveValue<string | number>;
  gap?: string | ResponsiveValue<string>;
  columnGap?: string | ResponsiveValue<string>;
  rowGap?: string | ResponsiveValue<string>;
  areas?: GridAreas | ResponsiveValue<GridAreas>;
  autoFit?: string;
  autoFill?: string;
  minHeight?: string;
  maxHeight?: string;
  containerQueries?: boolean;
  containerName?: string;
}

/**
 * Generate CSS custom properties for responsive grid
 */
function generateGridStyles(props: GridStyleProps): React.CSSProperties {
  const styles: React.CSSProperties = {};
  
  // Process columns
  if (props.columns) {
    const columnsValue = processResponsiveValue(
      props.columns,
      processGridTemplate
    );
    if (typeof columnsValue === 'string') {
      styles.gridTemplateColumns = columnsValue;
    } else {
      Object.entries(columnsValue).forEach(([key, value]) => {
        (styles as any)[key] = value;
      });
    }
  }
  
  // Process rows
  if (props.rows) {
    const rowsValue = processResponsiveValue(
      props.rows,
      processGridTemplate
    );
    if (typeof rowsValue === 'string') {
      styles.gridTemplateRows = rowsValue;
    } else {
      Object.entries(rowsValue).forEach(([key, value]) => {
        (styles as any)[key] = value;
      });
    }
  }
  
  // Process gap
  if (props.gap) {
    const gapValue = processResponsiveValue(props.gap);
    if (typeof gapValue === 'string') {
      styles.gap = gapValue;
    } else {
      Object.entries(gapValue).forEach(([key, value]) => {
        (styles as any)[key] = value;
      });
    }
  }
  
  // Process column gap
  if (props.columnGap) {
    const columnGapValue = processResponsiveValue(props.columnGap);
    if (typeof columnGapValue === 'string') {
      styles.columnGap = columnGapValue;
    }
  }
  
  // Process row gap
  if (props.rowGap) {
    const rowGapValue = processResponsiveValue(props.rowGap);
    if (typeof rowGapValue === 'string') {
      styles.rowGap = rowGapValue;
    }
  }
  
  // Process areas
  if (props.areas) {
    const areasValue = processResponsiveValue(
      props.areas,
      processGridAreas
    );
    if (typeof areasValue === 'string') {
      styles.gridTemplateAreas = areasValue;
    }
  }
  
  // Process auto-fit
  if (props.autoFit) {
    styles.gridTemplateColumns = `repeat(auto-fit, minmax(${props.autoFit}, 1fr))`;
  }
  
  // Process auto-fill
  if (props.autoFill) {
    styles.gridTemplateColumns = `repeat(auto-fill, minmax(${props.autoFill}, 1fr))`;
  }
  
  // Process min/max height
  if (props.minHeight) {
    styles.minHeight = props.minHeight;
  }
  
  if (props.maxHeight) {
    styles.maxHeight = props.maxHeight;
  }
  
  // Container queries
  if (props.containerQueries) {
    styles.containerType = 'inline-size';
    if (props.containerName) {
      styles.containerName = props.containerName;
    }
  }
  
  return styles;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

/**
 * GridContainer component with modern CSS Grid features
 */
export const GridContainer = React.forwardRef<HTMLDivElement, GridContainerProps>(
  (
    {
      columns,
      rows,
      gap,
      columnGap,
      rowGap,
      areas,
      autoFit,
      autoFill,
      autoFlow,
      justifyItems,
      alignItems,
      justifyContent,
      alignContent,
      responsive = false,
      containerQueries = false,
      containerName,
      minHeight,
      maxHeight,
      className,
      style,
      children,
      ...props
    },
    ref
  ) => {
    // Generate dynamic styles
    const gridStyles = generateGridStyles({
      columns,
      rows,
      gap,
      columnGap,
      rowGap,
      areas,
      autoFit,
      autoFill,
      minHeight,
      maxHeight,
      containerQueries,
      containerName,
    });

    // Combine styles
    const combinedStyles = {
      ...gridStyles,
      ...style,
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          gridContainerVariants({
            responsive,
            containerQueries,
            autoFlow,
            justifyItems,
            alignItems,
            justifyContent,
            alignContent,
          }),
          className
        )}
        style={combinedStyles}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GridContainer.displayName = 'GridContainer';

// ============================================================================
// COMPONENT VARIANTS
// ============================================================================

export type GridContainerVariants = VariantProps<typeof gridContainerVariants>;

// ============================================================================
// PRESET COMPONENTS
// ============================================================================

/**
 * Common grid layouts as preset components
 */

/**
 * Two column grid
 */
export const TwoColumnGrid = React.forwardRef<HTMLDivElement, Omit<GridContainerProps, 'columns'>>(
  (props, ref) => (
    <GridContainer
      ref={ref}
      columns={2}
      gap="var(--space-lg)"
      {...props}
    />
  )
);

TwoColumnGrid.displayName = 'TwoColumnGrid';

/**
 * Three column grid
 */
export const ThreeColumnGrid = React.forwardRef<HTMLDivElement, Omit<GridContainerProps, 'columns'>>(
  (props, ref) => (
    <GridContainer
      ref={ref}
      columns={3}
      gap="var(--space-lg)"
      {...props}
    />
  )
);

ThreeColumnGrid.displayName = 'ThreeColumnGrid';

/**
 * Auto-fit grid with minimum column width
 */
export const AutoFitGrid = React.forwardRef<HTMLDivElement, Omit<GridContainerProps, 'autoFit'> & { minColumnWidth: string }>(
  ({ minColumnWidth, ...props }, ref) => (
    <GridContainer
      ref={ref}
      autoFit={minColumnWidth}
      gap="var(--space-lg)"
      {...props}
    />
  )
);

AutoFitGrid.displayName = 'AutoFitGrid';

/**
 * Responsive card grid
 */
export const ResponsiveCardGrid = React.forwardRef<HTMLDivElement, Omit<GridContainerProps, 'columns' | 'responsive'>>(
  (props, ref) => (
    <GridContainer
      ref={ref}
      columns={{
        base: 1,
        sm: 2,
        md: 3,
        lg: 4,
      }}
      gap="var(--space-lg)"
      responsive={true}
      {...props}
    />
  )
);

ResponsiveCardGrid.displayName = 'ResponsiveCardGrid';

/**
 * Dashboard grid with named areas
 */
export const DashboardGrid = React.forwardRef<HTMLDivElement, Omit<GridContainerProps, 'areas' | 'columns' | 'rows'>>(
  (props, ref) => (
    <GridContainer
      ref={ref}
      columns="1fr 300px"
      rows="auto 1fr auto"
      areas={[
        'header header',
        'main sidebar',
        'footer footer'
      ]}
      gap="var(--space-lg)"
      minHeight="100vh"
      {...props}
    />
  )
);

DashboardGrid.displayName = 'DashboardGrid';