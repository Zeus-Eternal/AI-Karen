"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "./button";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Panel header props interface
 */
export interface PanelHeaderProps extends React.HTMLAttributes<HTMLElement> {
  /** Header title */
  title?: string;
  /** Header description */
  description?: string;
  /** Header icon */
  icon?: React.ReactNode;
  /** Action buttons or elements */
  actions?: React.ReactNode;
  /** Close button callback */
  onClose?: () => void;
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Header variant */
  variant?: "default" | "compact" | "prominent";
  /** Whether header is sticky */
  sticky?: boolean;
}

// ============================================================================
// STYLE MAPPINGS
// ============================================================================

/**
 * Header variant class mappings with responsive behavior
 */
const HEADER_VARIANT_CLASSES = {
  default: "px-3 py-2.5 sm:px-4 sm:py-3 md:px-6",
  compact: "px-2.5 py-2 sm:px-3 sm:py-2 md:px-4",
  prominent: "px-3 py-3 sm:px-4 sm:py-4 md:px-6 md:py-5",
} as const;

// ============================================================================
// COMPONENT
// ============================================================================

/**
 * Reusable Panel Header Component
 * 
 * Provides consistent header structure with 12-column grid system,
 * proper semantic HTML, and flexible content arrangement.
 */
export const PanelHeader = forwardRef<HTMLElement, PanelHeaderProps>(
  function PanelHeader(
    {
      title,
      description,
      icon,
      actions,
      onClose,
      showCloseButton = true,
      variant = "default",
      sticky = false,
      className,
      children,
      ...props
    },
    ref
  ) {
    const variantClass = HEADER_VARIANT_CLASSES[variant];

    return (
      <header
        ref={ref}
        className={cn(
          "flex-shrink-0 border-b border-border/50",
          "bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/80",
          sticky && "sticky top-0 z-10",
          // Consistent spacing using design tokens
          variantClass,
          // Proper alignment
          "flex items-start",
          className
        )}
        {...props}
      >
        <div className="grid grid-cols-12 gap-2 sm:gap-4 items-center w-full">
          {/* Icon - spans 1 column if present with responsive alignment */}
          {icon && (
            <div className="col-span-1 flex items-center justify-center">
              <div className={cn(
                "text-muted-foreground flex items-center justify-center",
                // Responsive icon sizing
                variant === "compact" ? "h-3.5 w-3.5 sm:h-4 sm:w-4" : "h-4 w-4 sm:h-5 sm:w-5"
              )}>
                {icon}
              </div>
            </div>
          )}

          {/* Title and description - responsive column spanning */}
          <div className={cn(
            "min-w-0 flex flex-col justify-center",
            // Responsive column calculation
            icon && (actions || (showCloseButton && onClose)) ? "col-span-8 sm:col-span-9" : 
            icon ? "col-span-10 sm:col-span-11" : 
            (actions || (showCloseButton && onClose)) ? "col-span-9 sm:col-span-10" : 
            "col-span-12"
          )}>
            {title && (
              <h2 className={cn(
                "font-semibold tracking-tight truncate",
                "leading-tight", // Consistent line height
                // Responsive text sizing
                variant === "compact" ? "text-sm sm:text-base" : 
                variant === "prominent" ? "text-lg sm:text-xl" : 
                "text-base sm:text-lg"
              )}>
                {title}
              </h2>
            )}
            {description && (
              <p className={cn(
                "text-muted-foreground line-clamp-2",
                "leading-relaxed", // Consistent line height
                // Responsive text sizing and spacing
                variant === "compact" ? "text-xs mt-0.5" : "text-xs sm:text-sm mt-0.5 sm:mt-1"
              )}>
                {description}
              </p>
            )}
            {children && (
              <div className={cn(
                variant === "compact" ? "mt-1" : "mt-1 sm:mt-2"
              )}>
                {children}
              </div>
            )}
          </div>

          {/* Actions and close button - responsive alignment and sizing */}
          {(actions || (showCloseButton && onClose)) && (
            <div className={cn(
              "flex items-center justify-end",
              // Responsive gap and column spanning
              "gap-1 sm:gap-2",
              icon ? "col-span-3 sm:col-span-2" : "col-span-3 sm:col-span-2"
            )}>
              {actions && (
                <div className="flex items-center gap-1 sm:gap-2">
                  {actions}
                </div>
              )}
              {showCloseButton && onClose && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className={cn(
                    "shrink-0",
                    "focus-visible:ring-2 focus-visible:ring-primary/20",
                    "transition-all duration-200",
                    // Touch-optimized sizing
                    "min-h-[44px] min-w-[44px] sm:min-h-[32px] sm:min-w-[32px]",
                    // Responsive button sizing
                    variant === "compact" ? "h-8 w-8 sm:h-7 sm:w-7" : "h-9 w-9 sm:h-8 sm:w-8",
                    // Enhanced touch feedback
                    "active:scale-95 sm:active:scale-100"
                  )}
                  aria-label="Close panel"
                >
                  <X className={cn(
                    // Responsive icon sizing
                    variant === "compact" ? "h-4 w-4 sm:h-3.5 sm:w-3.5" : "h-4 w-4"
                  )} />
                </Button>
              )}
            </div>
          )}
        </div>
      </header>
    );
  }
);

PanelHeader.displayName = "PanelHeader";