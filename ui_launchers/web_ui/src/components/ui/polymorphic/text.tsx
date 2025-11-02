"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

// Text component variants and sizes
type TextVariant = "default" | "muted" | "accent" | "destructive" | "success" | "warning"
type TextSize = "xs" | "sm" | "base" | "lg" | "xl" | "2xl" | "3xl" | "4xl"
type TextWeight = "normal" | "medium" | "semibold" | "bold"
type TextAlign = "left" | "center" | "right" | "justify"

interface TextProps {
  variant?: TextVariant
  size?: TextSize
  weight?: TextWeight
  align?: TextAlign
  truncate?: boolean
  italic?: boolean
  underline?: boolean
  children: React.ReactNode
}

// Polymorphic Text Component
const Text = React.forwardRef<
  HTMLSpanElement,
  TextProps & React.HTMLAttributes<HTMLSpanElement> & { as?: React.ElementType }
>(
  (
    {
      as,
      className,
      variant = "default",
      size = "base",
      weight = "normal",
      align = "left",
      truncate = false,
      italic = false,
      underline = false,
      children,
      ...props
    },
    ref
  ) => {
    const Component = as || "span"

    return (
      <Component
        ref={ref}
        className={cn(
          // Base styles
          "transition-colors duration-200",
          
          // Variant styles
          {
            "text-foreground": variant === "default",
            "text-muted-foreground": variant === "muted",
            "text-accent-foreground": variant === "accent",
            "text-destructive": variant === "destructive",
            "text-green-600 dark:text-green-400": variant === "success",
            "text-yellow-600 dark:text-yellow-400": variant === "warning",
          },
          
          // Size styles
          {
            "text-xs": size === "xs",
            "text-sm": size === "sm",
            "text-base": size === "base",
            "text-lg": size === "lg",
            "text-xl": size === "xl",
            "text-2xl": size === "2xl",
            "text-3xl": size === "3xl",
            "text-4xl": size === "4xl",
          },
          
          // Weight styles
          {
            "font-normal": weight === "normal",
            "font-medium": weight === "medium",
            "font-semibold": weight === "semibold",
            "font-bold": weight === "bold",
          },
          
          // Alignment styles
          {
            "text-left": align === "left",
            "text-center": align === "center",
            "text-right": align === "right",
            "text-justify": align === "justify",
          },
          
          // Additional styles
          {
            "truncate": truncate,
            "italic": italic,
            "underline": underline,
          },
          
          className
        )}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

Text.displayName = "Text"

// Predefined text components for common use cases
const Heading = React.forwardRef<
  any,
  TextProps & React.HTMLAttributes<HTMLHeadingElement> & { as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" }
>(({ as = "h1", size = "2xl", weight = "bold", ...props }, ref) => (
  <Text as={as} ref={ref} size={size} weight={weight} {...props} />
))
Heading.displayName = "Heading"

const Paragraph = React.forwardRef<
  HTMLParagraphElement,
  TextProps & React.HTMLAttributes<HTMLParagraphElement> & { as?: "p" }
>(({ as = "p", size = "base", ...props }, ref) => (
  <Text as={as} ref={ref} size={size} {...props} />
))
Paragraph.displayName = "Paragraph"

const Label = React.forwardRef<
  HTMLLabelElement,
  TextProps & React.HTMLAttributes<HTMLLabelElement> & { as?: "label" }
>(({ as = "label", size = "sm", weight = "medium", ...props }, ref) => (
  <Text as={as} ref={ref} size={size} weight={weight} {...props} />
))
Label.displayName = "Label"

const Caption = React.forwardRef<
  HTMLSpanElement,
  TextProps & React.HTMLAttributes<HTMLSpanElement> & { as?: "span" }
>(({ as = "span", size = "xs", variant = "muted", ...props }, ref) => (
  <Text as={as} ref={ref} size={size} variant={variant} {...props} />
))
Caption.displayName = "Caption"

const Code = React.forwardRef<
  HTMLElement,
  TextProps & React.HTMLAttributes<HTMLElement> & { as?: "code" }
>(({ as = "code", className, ...props }, ref) => (
  <Text
    as={as}
    ref={ref}
    className={cn(
      "relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold",
      className
    )}
    {...props}
  />
))
Code.displayName = "Code"

export {
  Text,
  Heading,
  Paragraph,
  Label,
  Caption,
  Code,
}

export type {
  TextProps,
  TextVariant,
  TextSize,
  TextWeight,
  TextAlign,
}