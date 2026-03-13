/**
 * ResponsiveContainer Component
 * 
 * Modern responsive container system with container query support,
 * breakpoint system, and responsive utilities for layout.
 * 
 * Based on requirements: 1.4, 8.3
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

import type { CSSCustomPropertyStyles } from './css-custom-properties';
import { assignResponsiveProperties } from './responsive-style-helpers';
import {
  type ContainerBreakpoints,
  type ContainerSize,
  type ResponsiveContainerProps,
  type ResponsiveValue,
} from './responsive-container.types';
import { responsiveContainerVariants } from './responsive-container.variants';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

/**
 * Container query breakpoints
 */
// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Process responsive value
 */
function processResponsiveValue<T>(
  value: T | ResponsiveValue<T>,
  processor?: (val: T) => string
): Record<`--${string}`, string> | string {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    const responsiveValue = value as ResponsiveValue<T>;
    const result: Record<`--${string}`, string> = {};

    const entries = Object.entries(responsiveValue) as Array<
      [keyof ResponsiveValue<T>, T | undefined]
    >;

    entries.forEach(([breakpoint, val]) => {
      if (val !== undefined) {
        const processedValue = processor ? processor(val) : String(val);
        if (breakpoint === 'base') {
          result['--container-base'] = processedValue;
        } else {
          result[`--container-${String(breakpoint)}`] = processedValue;
        }
      }
    });

    return result;
  }

  return processor ? processor(value as T) : String(value);
}

/**
 * Style-related properties for responsive container
 */
export interface ContainerStyleProps {
  padding?: string | ResponsiveValue<string>;
  margin?: string | ResponsiveValue<string>;
  minHeight?: string;
  maxHeight?: string;
  minWidth?: string;
  maxWidth?: string;
  background?: string;
  borderRadius?: string;
  shadow?: string;
  containerQueries?: boolean;
  containerName?: string;
  breakpoints?: ContainerBreakpoints;
}

/**
 * Generate container styles
 */
function generateContainerStyles(props: ContainerStyleProps): CSSCustomPropertyStyles {
  const styles: CSSCustomPropertyStyles = {};
  
  // Process padding
  if (props.padding) {
    const paddingValue = processResponsiveValue(props.padding);
    if (typeof paddingValue === 'string') {
      styles.padding = paddingValue;
    } else {
      assignResponsiveProperties(styles, paddingValue);
    }
  }
  
  // Process margin
  if (props.margin) {
    const marginValue = processResponsiveValue(props.margin);
    if (typeof marginValue === 'string') {
      styles.margin = marginValue;
    } else {
      assignResponsiveProperties(styles, marginValue);
    }
  }
  
  // Process dimensions
  if (props.minHeight) {
    styles.minHeight = props.minHeight;
  }
  
  if (props.maxHeight) {
    styles.maxHeight = props.maxHeight;
  }
  
  // Process visual properties
  if (props.background) {
    styles.backgroundColor = props.background;
  }
  
  if (props.borderRadius) {
    styles.borderRadius = props.borderRadius;
  }
  
  if (props.shadow) {
    styles.boxShadow = props.shadow;
  }
  
  // Container queries
  if (props.containerQueries) {
    styles.containerType = 'inline-size';
    if (props.containerName) {
      styles.containerName = props.containerName;
    }
  }
  
  // Custom breakpoints
  if (props.breakpoints) {
    const breakpointKeys = Object.keys(props.breakpoints) as Array<
      keyof ContainerBreakpoints
    >;

    breakpointKeys.forEach(breakpoint => {
      const value = props.breakpoints?.[breakpoint];
      if (value) {
        styles[`--breakpoint-${String(breakpoint)}` as `--${string}`] = value;
      }
    });
  }

  return styles;
}

/**
 * Get responsive size classes
 */
function getResponsiveSizeClasses(size: ContainerSize | ResponsiveValue<ContainerSize>, responsive: boolean): string {
  if (!responsive || typeof size === 'string') {
    return '';
  }

  const classes: string[] = [];

  const responsiveSize = size as ResponsiveValue<ContainerSize>;
  const breakpoints = Object.keys(responsiveSize) as Array<
    keyof ResponsiveValue<ContainerSize>
  >;

  const sizeClassMap: Record<ContainerSize, string> = {
    xs: 'max-w-xs',
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-full',
    screen: 'max-w-screen',
  };

  breakpoints.forEach(breakpoint => {
    const value = responsiveSize[breakpoint];
    if (!value || breakpoint === 'base') {
      return;
    }

    const sizeClass = sizeClassMap[value];
    if (sizeClass) {
      classes.push(`${String(breakpoint)}:${sizeClass}`);
    }
  });

  return classes.join(' ');
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

/**
 * ResponsiveContainer component with container query support
 */
export const ResponsiveContainer = React.forwardRef<HTMLDivElement, ResponsiveContainerProps>(
  (
    {
      size = 'full',
      containerQueries = false,
      containerName,
      breakpoints,
      padding,
      margin,
      center = false,
      fluid = false,
      responsive = false,
      minHeight,
      maxHeight,
      background,
      borderRadius,
      shadow,
      className,
      style,
      children,
      ...props
    },
    ref
  ) => {
    // Get base size for non-responsive props
    const baseSize = typeof size === 'object' ? size.base || 'full' : size;
    
    // Generate dynamic styles
    const containerStyles = generateContainerStyles({
      padding,
      margin,
      minHeight,
      maxHeight,
      background,
      borderRadius,
      shadow,
      containerQueries,
      containerName,
      breakpoints,
    });

    // Get responsive classes
    const responsiveSizeClasses = responsive ? getResponsiveSizeClasses(size, responsive) : '';
    
    // Combine styles
    const combinedStyles = {
      ...containerStyles,
      ...style,
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          responsiveContainerVariants({
            size: baseSize,
            center,
            fluid,
            containerQueries,
            responsive,
          }),
          responsiveSizeClasses,
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

ResponsiveContainer.displayName = 'ResponsiveContainer';

// ============================================================================
// PRESET COMPONENTS
// ============================================================================

/**
 * Common container layouts as preset components
 */

/**
 * Page container with standard padding and centering
 */
export const PageContainer = React.forwardRef<HTMLDivElement, Omit<ResponsiveContainerProps, 'center' | 'padding'>>(
  (props, ref) => (
    <ResponsiveContainer
      ref={ref}
      center={true}
      padding={{
        base: 'var(--space-md)',
        sm: 'var(--space-lg)',
        lg: 'var(--space-xl)',
      }}
      responsive={true}
      {...props}
    />
  )
);

PageContainer.displayName = 'PageContainer';

/**
 * Section container with responsive sizing
 */
export const SectionContainer = React.forwardRef<HTMLDivElement, Omit<ResponsiveContainerProps, 'size' | 'center'>>(
  (props, ref) => (
    <ResponsiveContainer
      ref={ref}
      size={{
        base: 'full',
        sm: 'lg',
        lg: 'xl',
        xl: '2xl',
      }}
      center={true}
      responsive={true}
      {...props}
    />
  )
);

SectionContainer.displayName = 'SectionContainer';

/**
 * Card container with container queries
 */
export const CardContainer = React.forwardRef<HTMLDivElement, Omit<ResponsiveContainerProps, 'containerQueries' | 'borderRadius' | 'shadow'>>(
  (props, ref) => (
    <ResponsiveContainer
      ref={ref}
      containerQueries={true}
      borderRadius="var(--radius-lg)"
      shadow="var(--shadow-md)"
      padding="var(--space-lg)"
      background="var(--color-neutral-50)"
      {...props}
    />
  )
);

CardContainer.displayName = 'CardContainer';

/**
 * Sidebar container with fixed width
 */
export const SidebarContainer = React.forwardRef<HTMLDivElement, Omit<ResponsiveContainerProps, 'size' | 'minHeight'>>(
  (props, ref) => (
    <ResponsiveContainer
      ref={ref}
      size={{
        base: 'full',
        md: 'sm',
      }}
      minHeight="100vh"
      responsive={true}
      {...props}
    />
  )
);

SidebarContainer.displayName = 'SidebarContainer';

/**
 * Content container with reading-optimized width
 */
export const ContentContainer = React.forwardRef<HTMLDivElement, Omit<ResponsiveContainerProps, 'size' | 'center'>>(
  (props, ref) => (
    <ResponsiveContainer
      ref={ref}
      size={{
        base: 'full',
        sm: 'md',
        lg: 'lg',
      }}
      center={true}
      responsive={true}
      {...props}
    />
  )
);

ContentContainer.displayName = 'ContentContainer';

