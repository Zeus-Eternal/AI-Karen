/**
 * ResponsiveContainer Component
 * 
 * Modern responsive container system with container query support,
 * breakpoint system, and responsive utilities for layout.
 * 
 * Based on requirements: 1.4, 8.3
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

/**
 * Container query breakpoints
 */
export interface ContainerBreakpoints {
  xs?: string;
  sm?: string;
  md?: string;
  lg?: string;
  xl?: string;
  '2xl'?: string;
}

/**
 * Responsive value type
 */
export interface ResponsiveValue<T> {
  base?: T;
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}

/**
 * Container size variants
 */
export type ContainerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full' | 'screen';

/**
 * Responsive container props
 */
export interface ResponsiveContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Container size variant */
  size?: ContainerSize | ResponsiveValue<ContainerSize>;
  
  /** Enable container queries */
  containerQueries?: boolean;
  
  /** Container name for container queries */
  containerName?: string;
  
  /** Custom container breakpoints */
  breakpoints?: ContainerBreakpoints;
  
  /** Padding */
  padding?: string | ResponsiveValue<string>;
  
  /** Margin */
  margin?: string | ResponsiveValue<string>;
  
  /** Center the container */
  center?: boolean;
  
  /** Fluid container (no max-width) */
  fluid?: boolean;
  
  /** Enable responsive behavior */
  responsive?: boolean;
  
  /** Minimum height */
  minHeight?: string;
  
  /** Maximum height */
  maxHeight?: string;
  
  /** Background color */
  background?: string;
  
  /** Border radius */
  borderRadius?: string;
  
  /** Box shadow */
  shadow?: string;
  
  /** Children */
  children: React.ReactNode;
}

// ============================================================================
// DEFAULT BREAKPOINTS
// ============================================================================

/**
 * Default container breakpoints
 */
export const defaultContainerBreakpoints: ContainerBreakpoints = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

/**
 * Container size mappings
 */
export const containerSizes: Record<ContainerSize, string> = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
  full: '100%',
  screen: '100vw',
};

// ============================================================================
// COMPONENT VARIANTS
// ============================================================================

/**
 * Responsive container variants
 */
const responsiveContainerVariants = cva(
  'w-full',
  {
    variants: {
      size: {
        xs: 'max-w-xs',
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        '2xl': 'max-w-2xl',
        full: 'max-w-full',
        screen: 'max-w-screen',
      },
      center: {
        true: 'mx-auto',
        false: '',
      },
      fluid: {
        true: 'max-w-none',
        false: '',
      },
      containerQueries: {
        true: 'container-responsive',
        false: '',
      },
      responsive: {
        true: 'responsive-container',
        false: '',
      },
    },
    defaultVariants: {
      size: 'full',
      center: false,
      fluid: false,
      containerQueries: false,
      responsive: false,
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
          result['--container-base'] = processedValue;
        } else {
          result[`--container-${breakpoint}`] = processedValue;
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
function generateContainerStyles(props: ContainerStyleProps): React.CSSProperties {
  const styles: React.CSSProperties = {};
  
  // Process padding
  if (props.padding) {
    const paddingValue = processResponsiveValue(props.padding);
    if (typeof paddingValue === 'string') {
      styles.padding = paddingValue;
    } else {
      Object.entries(paddingValue).forEach(([key, value]) => {
        (styles as any)[key] = value;
      });
    }
  }
  
  // Process margin
  if (props.margin) {
    const marginValue = processResponsiveValue(props.margin);
    if (typeof marginValue === 'string') {
      styles.margin = marginValue;
    } else {
      Object.entries(marginValue).forEach(([key, value]) => {
        (styles as any)[key] = value;
      });
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
    Object.entries(props.breakpoints).forEach(([breakpoint, value]) => {
      (styles as any)[`--breakpoint-${breakpoint}`] = value;
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
  
  Object.entries(size).forEach(([breakpoint, value]) => {
    if (value && breakpoint !== 'base') {
      const sizeClasses = {
        xs: 'max-w-xs',
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        '2xl': 'max-w-2xl',
        full: 'max-w-full',
        screen: 'max-w-screen',
      } as const;
      
      const sizeClass = sizeClasses[value as keyof typeof sizeClasses];
      if (sizeClass) {
        classes.push(`${breakpoint}:${sizeClass}`);
      }
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
// COMPONENT VARIANTS
// ============================================================================

export type ResponsiveContainerVariants = VariantProps<typeof responsiveContainerVariants>;

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

// ============================================================================
// CONTAINER QUERY UTILITIES
// ============================================================================

/**
 * Container query hook for JavaScript-based container queries
 */
export function useContainerQuery(containerName: string, query: string): boolean {
  const [matches, setMatches] = React.useState(false);
  
  React.useEffect(() => {
    if (!window.CSS || !window.CSS.supports || !window.CSS.supports('container-type', 'inline-size')) {
      return;
    }
    
    const mediaQuery = window.matchMedia(`@container ${containerName} ${query}`);
    
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };
    
    setMatches(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [containerName, query]);
  
  return matches;
}

/**
 * Container size detection hook
 */
export function useContainerSize(ref: React.RefObject<HTMLElement>): {
  width: number;
  height: number;
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
} {
  const [dimensions, setDimensions] = React.useState<{
    width: number;
    height: number;
    size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  }>({
    width: 0,
    height: 0,
    size: 'xs',
  });

  React.useEffect(() => {
    if (!ref.current) return;
    
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        
        let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'xs';
        
        if (width >= 1536) size = '2xl';
        else if (width >= 1280) size = 'xl';
        else if (width >= 1024) size = 'lg';
        else if (width >= 768) size = 'md';
        else if (width >= 640) size = 'sm';
        
        setDimensions({ width, height, size });
      }
    });

    resizeObserver.observe(ref.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, [ref]);
  
  return dimensions;
}
