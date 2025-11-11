/**
 * Focus Indicators Component
 * Provides accessible focus indicators with proper contrast ratios
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useFocusVisible } from '@/hooks/use-focus-management';

export interface FocusIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether to show focus indicator only on keyboard navigation */
  keyboardOnly?: boolean;
  /** Focus indicator style variant */
  variant?: 'default' | 'outline' | 'ring' | 'underline' | 'glow';
  /** Size of the focus indicator */
  size?: 'sm' | 'md' | 'lg';
  /** Color theme for the focus indicator */
  color?: 'primary' | 'secondary' | 'accent' | 'destructive';
  /** Whether the focus indicator is currently visible */
  visible?: boolean;
  /** Custom offset from the element */
  offset?: number;
  /** Children to wrap with focus indicator */
  children: React.ReactNode;
}

/**
 * FocusIndicator - Wraps children with accessible focus indicators
 */
export const FocusIndicator = React.forwardRef<HTMLDivElement, FocusIndicatorProps>(
  ({
    keyboardOnly = true,
    variant = 'default',
    size = 'md',
    color = 'primary',
    visible,
    offset = 2,
    className,
    children,
    ...props
  }, ref) => {
    const { isFocusVisible } = useFocusVisible();
    const [isFocused, setIsFocused] = React.useState(false);

    const shouldShowIndicator = visible !== undefined 
      ? visible 
      : keyboardOnly 
        ? isFocused && isFocusVisible 
        : isFocused;

    const handleFocus = React.useCallback(() => {
      setIsFocused(true);
    }, []);

    const handleBlur = React.useCallback(() => {
      setIsFocused(false);
    }, []);

    const indicatorClasses = cn(
      'focus-indicator',
      'absolute inset-0 pointer-events-none transition-all duration-200',
      {
        // Variants
        'ring-2 ring-offset-2 rounded': variant === 'default',
        'border-2 rounded': variant === 'outline',
        'ring-4 ring-offset-1 rounded': variant === 'ring',
        'border-b-2': variant === 'underline',
        'shadow-lg ring-2 ring-offset-2 rounded': variant === 'glow',
        
        // Sizes
        'ring-offset-1': size === 'sm' && (variant === 'default' || variant === 'ring'),
        'ring-offset-2': size === 'md' && (variant === 'default' || variant === 'ring'),
        'ring-offset-4': size === 'lg' && (variant === 'default' || variant === 'ring'),
        
        // Colors - Primary
        'ring-primary border-primary': color === 'primary',
        'shadow-primary/50': color === 'primary' && variant === 'glow',
        
        // Colors - Secondary
        'ring-secondary border-secondary': color === 'secondary',
        'shadow-secondary/50': color === 'secondary' && variant === 'glow',
        
        // Colors - Accent
        'ring-accent border-accent': color === 'accent',
        'shadow-accent/50': color === 'accent' && variant === 'glow',
        
        // Colors - Destructive
        'ring-destructive border-destructive': color === 'destructive',
        'shadow-destructive/50': color === 'destructive' && variant === 'glow',
        
        // Visibility
        'opacity-100': shouldShowIndicator,
        'opacity-0': !shouldShowIndicator,
      }
    );

    return (
      <div
        ref={ref}
        className={cn('focus-indicator-wrapper relative', className)}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...props}
      >
        {children}
        <div 
          className={indicatorClasses}
          style={{
            top: -offset,
            left: -offset,
            right: -offset,
            bottom: -offset,
          }}
          aria-hidden="true"
        />
      </div>
    );
  }
);

FocusIndicator.displayName = 'FocusIndicator';

/**
 * FocusRing - Simple focus ring component
 */
export interface FocusRingProps {
  /** Whether the focus ring is visible */
  visible: boolean;
  /** Size of the focus ring */
  size?: 'sm' | 'md' | 'lg';
  /** Color of the focus ring */
  color?: 'primary' | 'secondary' | 'accent' | 'destructive';
  /** Custom className */
  className?: string;
}

export const FocusRing: React.FC<FocusRingProps> = ({
  visible,
  size = 'md',
  color = 'primary',
  className,
}) => {
  return (
    <div
      className={cn(
        'absolute inset-0 pointer-events-none transition-opacity duration-200 rounded',
        'ring-offset-background',
        {
          // Sizes
          'ring-1 ring-offset-1': size === 'sm',
          'ring-2 ring-offset-2': size === 'md',
          'ring-4 ring-offset-4': size === 'lg',
          
          // Colors
          'ring-primary': color === 'primary',
          'ring-secondary': color === 'secondary',
          'ring-accent': color === 'accent',
          'ring-destructive': color === 'destructive',
          
          // Visibility
          'opacity-100': visible,
          'opacity-0': !visible,
        },
        className
      )}
      aria-hidden="true"
    />
  );
};


/**
 * FocusableArea - Creates a focusable area with proper indicators
 */
export interface FocusableAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether the area is focusable */
  focusable?: boolean;
  /** Focus indicator props */
  indicatorProps?: Partial<FocusIndicatorProps>;
  /** Callback when area receives focus */
  onFocus?: () => void;
  /** Callback when area loses focus */
  onBlur?: () => void;
}

export const FocusableArea = React.forwardRef<HTMLDivElement, FocusableAreaProps>(
  ({
    focusable = true,
    indicatorProps,
    onFocus,
    onBlur,
    className,
    children,
    tabIndex,
    ...props
  }, ref) => {
    const [isFocused, setIsFocused] = React.useState(false);

    const handleFocus = React.useCallback(() => {
      setIsFocused(true);
      onFocus?.();
    }, [onFocus]);

    const handleBlur = React.useCallback(() => {
      setIsFocused(false);
      onBlur?.();
    }, [onBlur]);

    return (
      <FocusIndicator
        visible={isFocused}
        {...indicatorProps}
      >
        <div
          ref={ref}
          className={cn(
            'focusable-area',
            focusable && 'focus:outline-none',
            className
          )}
          tabIndex={focusable ? (tabIndex ?? 0) : undefined}
          onFocus={handleFocus}
          onBlur={handleBlur}
          {...props}
        >
          {children}
        </div>
      </FocusIndicator>
    );
  }
);

FocusableArea.displayName = 'FocusableArea';

export default FocusIndicator;