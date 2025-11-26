/**
 * Button UI Component
 *
 * Reusable button component with various styles, sizes, and modern aesthetics.
 * Enhanced with loading states, icons, and accessibility features.
 */

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { buttonVariants } from './button-variants';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  iconOnly?: boolean;
  ripple?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant,
    size,
    asChild = false,
    loading = false,
    loadingText = "Loading...",
    leftIcon,
    rightIcon,
    iconOnly = false,
    ripple = true,
    disabled,
    children,
    onClick,
    ...props
  }, ref) => {
    const [ripples, setRipples] = React.useState<Array<{ id: number; x: number; y: number; size: number }>>([]);
    const rippleIdRef = React.useRef(0);
    
    const isDisabled = disabled || loading;
    
    const handleClick = React.useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
      if (ripple && !isDisabled) {
        const button = event.currentTarget;
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        const newRipple = {
          id: rippleIdRef.current++,
          x,
          y,
          size,
        };
        
        setRipples(prev => [...prev, newRipple]);
        
        setTimeout(() => {
          setRipples(prev => prev.filter(r => r.id !== newRipple.id));
        }, 600);
      }
      
      if (onClick) {
        onClick(event);
      }
    }, [ripple, isDisabled, onClick]);
    
    const Comp = asChild ? Slot : 'button';
    
    return (
      <Comp
        className={cn(
          buttonVariants({ variant, size, className }),
          "relative overflow-hidden",
          iconOnly && "aspect-square",
          loading && "cursor-wait"
        )}
        ref={ref}
        disabled={isDisabled}
        onClick={handleClick}
        {...props}
      >
        {/* Ripple effects */}
        {ripples.map(ripple => (
          <span
            key={ripple.id}
            className="absolute rounded-full bg-white/20 animate-ripple"
            style={{
              top: ripple.y,
              left: ripple.x,
              width: ripple.size,
              height: ripple.size,
            }}
          />
        ))}
        
        {/* Left icon or loading spinner */}
        {(leftIcon || loading) && (
          <span className="inline-flex">
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              leftIcon
            )}
          </span>
        )}
        
        {/* Button content */}
        {loading ? (
          <span className="ml-2">{loadingText}</span>
        ) : (
          <span className={cn(leftIcon && "ml-2", rightIcon && "mr-2")}>
            {children}
          </span>
        )}
        
        {/* Right icon */}
        {rightIcon && !loading && (
          <span className="inline-flex">
            {rightIcon}
          </span>
        )}
        
        {/* Visually hidden text for icon-only buttons */}
        {iconOnly && children && (
          <span className="sr-only">{children}</span>
        )}
      </Comp>
    );
  }
);
Button.displayName = 'Button';
