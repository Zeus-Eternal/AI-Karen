/**
 * ARIA Enhanced Button Component
 * Extends the base button with comprehensive accessibility features
 */

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";
import {
  createAriaLabel,
  createInteractiveAria,
  createLoadingAria,
  mergeAriaProps,
  type AriaProps,
} from "@/utils/aria";
import { AriaStatus } from "./aria-live-region";
import { buttonVariants, type ButtonVariantProps } from "./aria-enhanced-button-variants";

export interface AriaEnhancedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    ButtonVariantProps {
  asChild?: boolean;
  
  // ARIA enhancements
  /** Accessible label for the button */
  ariaLabel?: string;
  /** ID of element that labels this button */
  ariaLabelledBy?: string;
  /** ID of element that describes this button */
  ariaDescribedBy?: string;
  /** Whether the button is in a pressed state (for toggle buttons) */
  pressed?: boolean;
  /** Whether the button controls an expanded element */
  expanded?: boolean;
  /** Whether the button is currently selected */
  selected?: boolean;
  /** Whether the button represents the current item in a set */
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time';
  /** Whether the button has a popup */
  hasPopup?: boolean | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog';
  /** ID of element controlled by this button */
  controls?: string;
  /** Loading state */
  loading?: boolean;
  /** Loading text to announce */
  loadingText?: string;
  /** Success state */
  success?: boolean;
  /** Success message to announce */
  successMessage?: string;
  /** Error state */
  error?: boolean;
  /** Error message to announce */
  errorMessage?: string;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaEnhancedButton = React.forwardRef<HTMLButtonElement, AriaEnhancedButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false,
    ariaLabel,
    ariaLabelledBy,
    ariaDescribedBy,
    pressed,
    expanded,
    selected,
    current,
    hasPopup,
    controls,
    loading = false,
    loadingText = "Loading...",
    success = false,
    successMessage,
    error = false,
    errorMessage,
    ariaProps,
    disabled,
    children,
    ...props 
  }, ref) => {
    const Comp = asChild ? Slot : "button";
    
    // Create comprehensive ARIA attributes
    const labelProps = createAriaLabel(ariaLabel, ariaLabelledBy, ariaDescribedBy);
    const interactiveProps = createInteractiveAria(expanded, selected, pressed, current, disabled || loading);
    const loadingProps = loading ? createLoadingAria(true, loadingText) : {};
    
    // Additional ARIA attributes
    const additionalProps: Partial<AriaProps> = {};
    if (hasPopup !== undefined) additionalProps['aria-haspopup'] = hasPopup;
    if (controls) additionalProps['aria-controls'] = controls;
    
    // Merge all ARIA props
    const mergedAriaProps = mergeAriaProps(
      labelProps,
      interactiveProps,
      loadingProps,
      additionalProps,
      ariaProps
    );

    // Filter out properties that conflict with HTML button attributes
    const { 'aria-relevant': _ariaRelevant, ...finalAriaProps } = mergedAriaProps;

    // Determine button content based on state
    const buttonContent = React.useMemo(() => {
      if (loading) {
        return (
          <>
            <svg 
              className="animate-spin -ml-1 mr-2 h-4 w-4 " 
              xmlns="http://www.w3.org/2000/svg" 
              fill="none" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {loadingText}
          </>
        );
      }
      return children;
    }, [loading, loadingText, children]);

    return (
      <>
        <Comp
          className={cn(
            buttonVariants({ variant, size, className }),
            {
              'cursor-not-allowed': loading,
              'opacity-50': loading,
            }
          )}
          ref={ref}
          disabled={disabled || loading}
          {...finalAriaProps}
          {...props}
        >
          {buttonContent}
        </Comp>
        
        {/* Status announcements */}
        {loading && (
          <AriaStatus 
            message={loadingText} 
            loading={true}
          />
        )}
        {success && successMessage && (
          <AriaStatus 
            message={successMessage} 
            success={true}
          />
        )}
        {error && errorMessage && (
          <AriaStatus 
            message={errorMessage} 
            error={true}
          />
        )}
      </>
    );
  }
);

AriaEnhancedButton.displayName = "AriaEnhancedButton";

/**
 * Toggle Button - A button that maintains pressed state
 */
export interface ToggleButtonProps extends Omit<AriaEnhancedButtonProps, 'pressed'> {
  /** Whether the toggle is currently pressed */
  pressed: boolean;
  /** Callback when toggle state changes */
  onPressedChange?: (pressed: boolean) => void;
  /** Label for pressed state */
  pressedLabel?: string;
  /** Label for unpressed state */
  unpressedLabel?: string;
}

export const ToggleButton = React.forwardRef<HTMLButtonElement, ToggleButtonProps>(
  ({ 
    pressed, 
    onPressedChange, 
    pressedLabel, 
    unpressedLabel,
    ariaLabel,
    onClick,
    children,
    ...props 
  }, ref) => {
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      onPressedChange?.(!pressed);
      onClick?.(event);
    };

    const effectiveLabel = pressed 
      ? (pressedLabel || ariaLabel)
      : (unpressedLabel || ariaLabel);

    return (
      <AriaEnhancedButton
        ref={ref}
        pressed={pressed}
        ariaLabel={effectiveLabel}
        onClick={handleClick}
        {...props}
      >
        {children}
      </AriaEnhancedButton>
    );
  }
);

ToggleButton.displayName = "ToggleButton";

/**
 * Menu Button - A button that opens a menu
 */
export interface MenuButtonProps extends Omit<AriaEnhancedButtonProps, 'hasPopup' | 'expanded'> {
  /** Whether the menu is currently open */
  menuOpen: boolean;
  /** ID of the menu element */
  menuId?: string;
}

export const MenuButton = React.forwardRef<HTMLButtonElement, MenuButtonProps>(
  ({ menuOpen, menuId, ...props }, ref) => {
    return (
      <AriaEnhancedButton
        ref={ref}
        hasPopup="menu"
        expanded={menuOpen}
        controls={menuId}
        {...props}
      />
    );
  }
);

MenuButton.displayName = "MenuButton";
