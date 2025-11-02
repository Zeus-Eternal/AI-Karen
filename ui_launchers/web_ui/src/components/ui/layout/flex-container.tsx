/**
 * FlexContainer Component
 * 
 * Enhanced Flexbox wrapper component with TypeScript interfaces,
 * gap support, responsive behavior, and modern flex features.
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
 * Flex container props interface
 */
export interface FlexContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Flex direction */
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse' | ResponsiveValue<'row' | 'column' | 'row-reverse' | 'column-reverse'>;
  
  /** Align items along cross axis */
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline' | ResponsiveValue<'start' | 'center' | 'end' | 'stretch' | 'baseline'>;
  
  /** Justify content along main axis */
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly' | ResponsiveValue<'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'>;
  
  /** Flex wrap behavior */
  wrap?: boolean | 'reverse' | ResponsiveValue<boolean | 'reverse'>;
  
  /** Gap between flex items */
  gap?: string | ResponsiveValue<string>;
  
  /** Row gap specifically */
  rowGap?: string | ResponsiveValue<string>;
  
  /** Column gap specifically */
  columnGap?: string | ResponsiveValue<string>;
  
  /** Flex grow for the container */
  grow?: boolean | number;
  
  /** Flex shrink for the container */
  shrink?: boolean | number;
  
  /** Flex basis for the container */
  basis?: string | number;
  
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
  
  /** Minimum width */
  minWidth?: string;
  
  /** Maximum width */
  maxWidth?: string;
  
  /** Children elements */
  children: React.ReactNode;
}

// ============================================================================
// COMPONENT VARIANTS
// ============================================================================

/**
 * Flex container variants using CVA
 */
const flexContainerVariants = cva(
  'flex',
  {
    variants: {
      direction: {
        row: 'flex-row',
        column: 'flex-col',
        'row-reverse': 'flex-row-reverse',
        'column-reverse': 'flex-col-reverse',
      },
      align: {
        start: 'items-start',
        center: 'items-center',
        end: 'items-end',
        stretch: 'items-stretch',
        baseline: 'items-baseline',
      },
      justify: {
        start: 'justify-start',
        center: 'justify-center',
        end: 'justify-end',
        between: 'justify-between',
        around: 'justify-around',
        evenly: 'justify-evenly',
      },
      wrap: {
        true: 'flex-wrap',
        false: 'flex-nowrap',
        reverse: 'flex-wrap-reverse',
      },
      responsive: {
        true: 'responsive-flex',
        false: '',
      },
      containerQueries: {
        true: 'container-flex',
        false: '',
      },
      grow: {
        true: 'flex-grow',
        false: 'flex-grow-0',
      },
      shrink: {
        true: 'flex-shrink',
        false: 'flex-shrink-0',
      },
    },
    defaultVariants: {
      direction: 'row',
      align: 'stretch',
      justify: 'start',
      wrap: false,
      responsive: false,
      containerQueries: false,
      grow: false,
      shrink: true,
    },
  }
);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

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
          result['--flex-base'] = processedValue;
        } else {
          result[`--flex-${breakpoint}`] = processedValue;
        }
      }

    return result;
  }
  
  return processor ? processor(value as T) : String(value);
}

/**
 * Style-related properties for flex container
 */
interface FlexStyleProps {
  gap?: string | ResponsiveValue<string>;
  rowGap?: string | ResponsiveValue<string>;
  columnGap?: string | ResponsiveValue<string>;
  grow?: boolean | number;
  shrink?: boolean | number;
  basis?: string | number;
  minHeight?: string;
  maxHeight?: string;
  minWidth?: string;
  maxWidth?: string;
  containerQueries?: boolean;
  containerName?: string;
}

/**
 * Generate CSS custom properties for responsive flex
 */
function generateFlexStyles(props: FlexStyleProps): React.CSSProperties {
  const styles: React.CSSProperties = {};
  
  // Process gap
  if (props.gap) {
    const gapValue = processResponsiveValue(props.gap);
    if (typeof gapValue === 'string') {
      styles.gap = gapValue;
    } else {
      Object.entries(gapValue).forEach(([key, value]) => {
        (styles as any)[key] = value;

    }
  }
  
  // Process row gap
  if (props.rowGap) {
    const rowGapValue = processResponsiveValue(props.rowGap);
    if (typeof rowGapValue === 'string') {
      styles.rowGap = rowGapValue;
    }
  }
  
  // Process column gap
  if (props.columnGap) {
    const columnGapValue = processResponsiveValue(props.columnGap);
    if (typeof columnGapValue === 'string') {
      styles.columnGap = columnGapValue;
    }
  }
  
  // Process flex grow
  if (typeof props.grow === 'number') {
    styles.flexGrow = props.grow;
  }
  
  // Process flex shrink
  if (typeof props.shrink === 'number') {
    styles.flexShrink = props.shrink;
  }
  
  // Process flex basis
  if (props.basis) {
    styles.flexBasis = typeof props.basis === 'number' ? `${props.basis}px` : props.basis;
  }
  
  // Process dimensions
  if (props.minHeight) {
    styles.minHeight = props.minHeight;
  }
  
  if (props.maxHeight) {
    styles.maxHeight = props.maxHeight;
  }
  
  if (props.minWidth) {
    styles.minWidth = props.minWidth;
  }
  
  if (props.maxWidth) {
    styles.maxWidth = props.maxWidth;
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

/**
 * Responsive properties for flex container
 */
interface FlexResponsiveProps {
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse' | ResponsiveValue<'row' | 'column' | 'row-reverse' | 'column-reverse'>;
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline' | ResponsiveValue<'start' | 'center' | 'end' | 'stretch' | 'baseline'>;
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly' | ResponsiveValue<'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'>;
  wrap?: boolean | 'reverse' | ResponsiveValue<boolean | 'reverse'>;
  responsive?: boolean;
}

/**
 * Get responsive variant classes
 */
function getResponsiveClasses(props: FlexResponsiveProps): string {
  const classes: string[] = [];
  
  // Handle responsive direction
  if (props.responsive && typeof props.direction === 'object') {
    Object.entries(props.direction).forEach(([breakpoint, value]) => {
      if (value && breakpoint !== 'base') {
        const directionClasses = {
          row: 'flex-row',
          column: 'flex-col',
          'row-reverse': 'flex-row-reverse',
          'column-reverse': 'flex-col-reverse',
        } as const;
        
        const directionClass = directionClasses[value as keyof typeof directionClasses];
        if (directionClass) {
          classes.push(`${breakpoint}:${directionClass}`);
        }
      }

  }
  
  // Handle responsive align
  if (props.responsive && typeof props.align === 'object') {
    Object.entries(props.align).forEach(([breakpoint, value]) => {
      if (value && breakpoint !== 'base') {
        const alignClasses = {
          start: 'items-start',
          center: 'items-center',
          end: 'items-end',
          stretch: 'items-stretch',
          baseline: 'items-baseline',
        } as const;
        
        const alignClass = alignClasses[value as keyof typeof alignClasses];
        if (alignClass) {
          classes.push(`${breakpoint}:${alignClass}`);
        }
      }

  }
  
  // Handle responsive justify
  if (props.responsive && typeof props.justify === 'object') {
    Object.entries(props.justify).forEach(([breakpoint, value]) => {
      if (value && breakpoint !== 'base') {
        const justifyClasses = {
          start: 'justify-start',
          center: 'justify-center',
          end: 'justify-end',
          between: 'justify-between',
          around: 'justify-around',
          evenly: 'justify-evenly',
        } as const;
        
        const justifyClass = justifyClasses[value as keyof typeof justifyClasses];
        if (justifyClass) {
          classes.push(`${breakpoint}:${justifyClass}`);
        }
      }

  }
  
  // Handle responsive wrap
  if (props.responsive && typeof props.wrap === 'object') {
    Object.entries(props.wrap).forEach(([breakpoint, value]) => {
      if (value !== undefined && breakpoint !== 'base') {
        const wrapClass = value === true ? 'flex-wrap' : value === 'reverse' ? 'flex-wrap-reverse' : 'flex-nowrap';
        classes.push(`${breakpoint}:${wrapClass}`);
      }

  }
  
  return classes.join(' ');
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

/**
 * FlexContainer component with enhanced Flexbox features
 */
export const FlexContainer = React.forwardRef<HTMLDivElement, FlexContainerProps>(
  (
    {
      direction = 'row',
      align = 'stretch',
      justify = 'start',
      wrap = false,
      gap,
      rowGap,
      columnGap,
      grow = false,
      shrink = true,
      basis,
      responsive = false,
      containerQueries = false,
      containerName,
      minHeight,
      maxHeight,
      minWidth,
      maxWidth,
      className,
      style,
      children,
      ...props
    },
    ref
  ) => {
    // Get base values for non-responsive props
    const baseDirection = typeof direction === 'object' ? direction.base || 'row' : direction;
    const baseAlign = typeof align === 'object' ? align.base || 'stretch' : align;
    const baseJustify = typeof justify === 'object' ? justify.base || 'start' : justify;
    const baseWrap = typeof wrap === 'object' ? wrap.base || false : wrap;
    
    // Generate dynamic styles
    const flexStyles = generateFlexStyles({
      gap,
      rowGap,
      columnGap,
      grow,
      shrink,
      basis,
      minHeight,
      maxHeight,
      minWidth,
      maxWidth,
      containerQueries,
      containerName,

    // Get responsive classes
    const responsiveClasses = responsive ? getResponsiveClasses({
      direction,
      align,
      justify,
      wrap,
      responsive,
    }) : '';
    
    // Combine styles
    const combinedStyles = {
      ...flexStyles,
      ...style,
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          flexContainerVariants({
            direction: baseDirection,
            align: baseAlign,
            justify: baseJustify,
            wrap: baseWrap,
            responsive,
            containerQueries,
            grow: typeof grow === 'boolean' ? grow : undefined,
            shrink: typeof shrink === 'boolean' ? shrink : undefined,
          }),
          responsiveClasses,
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

FlexContainer.displayName = 'FlexContainer';

// ============================================================================
// COMPONENT VARIANTS
// ============================================================================

export type FlexContainerVariants = VariantProps<typeof flexContainerVariants>;

// ============================================================================
// PRESET COMPONENTS
// ============================================================================

/**
 * Common flex layouts as preset components
 */

/**
 * Horizontal stack with gap
 */
export const HStack = React.forwardRef<HTMLDivElement, Omit<FlexContainerProps, 'direction'>>(
  ({ gap = 'var(--space-md)', ...props }, ref) => (
    <FlexContainer
      ref={ref}
      direction="row"
      gap={gap}
      {...props}
    />
  )
);

HStack.displayName = 'HStack';

/**
 * Vertical stack with gap
 */
export const VStack = React.forwardRef<HTMLDivElement, Omit<FlexContainerProps, 'direction'>>(
  ({ gap = 'var(--space-md)', ...props }, ref) => (
    <FlexContainer
      ref={ref}
      direction="column"
      gap={gap}
      {...props}
    />
  )
);

VStack.displayName = 'VStack';

/**
 * Centered flex container
 */
export const Center = React.forwardRef<HTMLDivElement, Omit<FlexContainerProps, 'align' | 'justify'>>(
  (props, ref) => (
    <FlexContainer
      ref={ref}
      align="center"
      justify="center"
      {...props}
    />
  )
);

Center.displayName = 'Center';

/**
 * Space between flex container
 */
export const SpaceBetween = React.forwardRef<HTMLDivElement, Omit<FlexContainerProps, 'justify'>>(
  (props, ref) => (
    <FlexContainer
      ref={ref}
      justify="between"
      align="center"
      {...props}
    />
  )
);

SpaceBetween.displayName = 'SpaceBetween';

/**
 * Responsive flex container that changes direction based on screen size
 */
export const ResponsiveFlex = React.forwardRef<HTMLDivElement, Omit<FlexContainerProps, 'direction' | 'responsive'>>(
  (props, ref) => (
    <FlexContainer
      ref={ref}
      direction={{
        base: 'column',
        md: 'row',
      }}
      responsive={true}
      gap="var(--space-lg)"
      {...props}
    />
  )
);

ResponsiveFlex.displayName = 'ResponsiveFlex';

/**
 * Flex item component for use within flex containers
 */
export interface FlexItemProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Flex grow */
  grow?: boolean | number;
  
  /** Flex shrink */
  shrink?: boolean | number;
  
  /** Flex basis */
  basis?: string | number;
  
  /** Align self */
  alignSelf?: 'auto' | 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  
  /** Order */
  order?: number;
  
  /** Children */
  children: React.ReactNode;
}

/**
 * Flex item variants
 */
const flexItemVariants = cva(
  '',
  {
    variants: {
      grow: {
        true: 'flex-grow',
        false: 'flex-grow-0',
      },
      shrink: {
        true: 'flex-shrink',
        false: 'flex-shrink-0',
      },
      alignSelf: {
        auto: 'self-auto',
        start: 'self-start',
        center: 'self-center',
        end: 'self-end',
        stretch: 'self-stretch',
        baseline: 'self-baseline',
      },
    },
    defaultVariants: {
      grow: false,
      shrink: true,
    },
  }
);

/**
 * FlexItem component for individual flex items
 */
export const FlexItem = React.forwardRef<HTMLDivElement, FlexItemProps>(
  (
    {
      grow = false,
      shrink = true,
      basis,
      alignSelf,
      order,
      className,
      style,
      children,
      ...props
    },
    ref
  ) => {
    const itemStyles: React.CSSProperties = {
      ...style,
    };
    
    // Process flex properties
    if (typeof grow === 'number') {
      itemStyles.flexGrow = grow;
    }
    
    if (typeof shrink === 'number') {
      itemStyles.flexShrink = shrink;
    }
    
    if (basis) {
      itemStyles.flexBasis = typeof basis === 'number' ? `${basis}px` : basis;
    }
    
    if (order !== undefined) {
      itemStyles.order = order;
    }
    
    return (
      <div
        ref={ref}
        className={cn(
          flexItemVariants({
            grow: typeof grow === 'boolean' ? grow : undefined,
            shrink: typeof shrink === 'boolean' ? shrink : undefined,
            alignSelf,
          }),
          className
        )}
        style={itemStyles}
        {...props}
      >
        {children}
      </div>
    );
  }
);

FlexItem.displayName = 'FlexItem';