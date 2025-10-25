"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"
import type { PolymorphicComponentPropWithRef, PolymorphicRef } from "../compound/types"

// Button component variants and sizes
type ButtonVariant = "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
type ButtonSize = "xs" | "sm" | "md" | "lg" | "xl"

interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  disabled?: boolean
  asChild?: boolean
  fullWidth?: boolean
  children: React.ReactNode
}

// Polymorphic Button Component
const Button = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement> & { as?: React.ElementType }
>(
  (
    {
      as,
      className,
      variant = "default",
      size = "md",
      loading = false,
      disabled = false,
      asChild = false,
      fullWidth = false,
      children,
      ...props
    },
    ref
  ) => {
    const Component = asChild ? Slot : (as || "button")
    const isDisabled = disabled || loading

    return (
      <Component
        ref={ref}
        className={cn(
          // Base styles
          "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium",
          "ring-offset-background transition-colors duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          
          // Variant styles
          {
            "bg-primary text-primary-foreground hover:bg-primary/90": variant === "default",
            "bg-destructive text-destructive-foreground hover:bg-destructive/90": variant === "destructive",
            "border border-input bg-background hover:bg-accent hover:text-accent-foreground": variant === "outline",
            "bg-secondary text-secondary-foreground hover:bg-secondary/80": variant === "secondary",
            "hover:bg-accent hover:text-accent-foreground": variant === "ghost",
            "text-primary underline-offset-4 hover:underline": variant === "link",
          },
          
          // Size styles
          {
            "h-7 px-2 text-xs": size === "xs",
            "h-8 px-3 text-sm": size === "sm",
            "h-10 px-4 py-2": size === "md",
            "h-11 px-8": size === "lg",
            "h-12 px-10 text-lg": size === "xl",
          },
          
          // Full width
          {
            "w-full": fullWidth,
          },
          
          // Loading state
          {
            "cursor-not-allowed": loading,
          },
          
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
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
        )}
        {children}
      </Component>
    )
  }
)

Button.displayName = "Button"

// Predefined button components for common use cases
const IconButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement> & { icon: React.ReactNode; "aria-label": string }
>(({ icon, children, className, size = "md", ...props }, ref) => (
  <Button
    ref={ref}
    size={size}
    className={cn(
      "aspect-square p-0",
      {
        "h-7 w-7": size === "xs",
        "h-8 w-8": size === "sm", 
        "h-10 w-10": size === "md",
        "h-11 w-11": size === "lg",
        "h-12 w-12": size === "xl",
      },
      className
    )}
    {...props}
  >
    {icon}
    {children && <span className="sr-only">{children}</span>}
  </Button>
))
IconButton.displayName = "IconButton"

const LinkButton = React.forwardRef<
  any,
  ButtonProps & { href: string; as?: React.ElementType; [key: string]: any }
>(({ as = "a", variant = "link", children, ...props }, ref) => (
  <Button as={as} ref={ref} variant={variant} {...props}>
    {children}
  </Button>
))
LinkButton.displayName = "LinkButton"

const SubmitButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ type = "submit", variant = "default", ...props }, ref) => (
  <Button ref={ref} type={type} variant={variant} {...props} />
))
SubmitButton.displayName = "SubmitButton"

const ResetButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ type = "reset", variant = "outline", ...props }, ref) => (
  <Button ref={ref} type={type} variant={variant} {...props} />
))
ResetButton.displayName = "ResetButton"

const CancelButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ variant = "ghost", ...props }, ref) => (
  <Button ref={ref} variant={variant} {...props} />
))
CancelButton.displayName = "CancelButton"

const DestructiveButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ variant = "destructive", ...props }, ref) => (
  <Button ref={ref} variant={variant} {...props} />
))
DestructiveButton.displayName = "DestructiveButton"

export {
  Button,
  IconButton,
  LinkButton,
  SubmitButton,
  ResetButton,
  CancelButton,
  DestructiveButton,
}

export type {
  ButtonProps,
  ButtonVariant,
  ButtonSize,
}