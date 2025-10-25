"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import type { PolymorphicComponentPropWithRef, PolymorphicRef } from "../compound/types"

// Container component variants and sizes
type ContainerVariant = "default" | "fluid" | "constrained" | "centered" | "padded"
type ContainerSize = "xs" | "sm" | "md" | "lg" | "xl" | "2xl" | "full"
type ContainerDisplay = "block" | "flex" | "grid" | "inline" | "inline-flex" | "inline-grid"

interface ContainerProps {
  variant?: ContainerVariant
  size?: ContainerSize
  display?: ContainerDisplay
  responsive?: boolean
  children: React.ReactNode
}

// Polymorphic Container Component
const Container = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement> & { as?: React.ElementType }
>(
  (
    {
      as,
      className,
      variant = "default",
      size = "full",
      display = "block",
      responsive = true,
      children,
      ...props
    },
    ref
  ) => {
    const Component = as || "div"

    return (
      <Component
        ref={ref}
        className={cn(
          // Base styles
          "transition-all duration-200",
          
          // Display styles
          {
            "block": display === "block",
            "flex": display === "flex",
            "grid": display === "grid",
            "inline": display === "inline",
            "inline-flex": display === "inline-flex",
            "inline-grid": display === "inline-grid",
          },
          
          // Variant styles
          {
            // Default container with max-width and centering
            "mx-auto": variant === "default" || variant === "constrained" || variant === "centered",
            "w-full": variant === "default" || variant === "fluid" || variant === "constrained",
            "px-4 sm:px-6 lg:px-8": variant === "padded" || variant === "default",
            "flex items-center justify-center": variant === "centered",
          },
          
          // Size styles (max-width constraints)
          responsive && {
            "max-w-xs": size === "xs",
            "max-w-sm": size === "sm",
            "max-w-md": size === "md",
            "max-w-lg": size === "lg",
            "max-w-xl": size === "xl",
            "max-w-2xl": size === "2xl",
            "max-w-none": size === "full",
          },
          
          // Non-responsive size styles
          !responsive && {
            "w-80": size === "xs",
            "w-96": size === "sm",
            "w-[32rem]": size === "md",
            "w-[40rem]": size === "lg",
            "w-[48rem]": size === "xl",
            "w-[56rem]": size === "2xl",
            "w-full": size === "full",
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

Container.displayName = "Container"

// Predefined container components for common use cases
const FlexContainer = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement> & {
    direction?: "row" | "column" | "row-reverse" | "column-reverse"
    align?: "start" | "center" | "end" | "stretch" | "baseline"
    justify?: "start" | "center" | "end" | "between" | "around" | "evenly"
    wrap?: boolean
    gap?: "none" | "xs" | "sm" | "md" | "lg" | "xl"
  }
>(({ 
  display = "flex",
  direction = "row",
  align = "start",
  justify = "start",
  wrap = false,
  gap = "none",
  className,
  ...props 
}, ref) => (
  <Container
    ref={ref}
    display={display}
    className={cn(
      // Flex direction
      {
        "flex-row": direction === "row",
        "flex-col": direction === "column",
        "flex-row-reverse": direction === "row-reverse",
        "flex-col-reverse": direction === "column-reverse",
      },
      
      // Align items
      {
        "items-start": align === "start",
        "items-center": align === "center",
        "items-end": align === "end",
        "items-stretch": align === "stretch",
        "items-baseline": align === "baseline",
      },
      
      // Justify content
      {
        "justify-start": justify === "start",
        "justify-center": justify === "center",
        "justify-end": justify === "end",
        "justify-between": justify === "between",
        "justify-around": justify === "around",
        "justify-evenly": justify === "evenly",
      },
      
      // Flex wrap
      {
        "flex-wrap": wrap,
      },
      
      // Gap
      {
        "gap-1": gap === "xs",
        "gap-2": gap === "sm",
        "gap-4": gap === "md",
        "gap-6": gap === "lg",
        "gap-8": gap === "xl",
      },
      
      className
    )}
    {...props}
  />
))
FlexContainer.displayName = "FlexContainer"

const GridContainer = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement> & {
    columns?: number | string
    rows?: number | string
    gap?: "none" | "xs" | "sm" | "md" | "lg" | "xl"
    autoFit?: boolean
    minItemWidth?: string
  }
>(({ 
  display = "grid",
  columns = "auto",
  rows = "auto",
  gap = "md",
  autoFit = false,
  minItemWidth = "250px",
  className,
  style,
  ...props 
}, ref) => (
  <Container
    ref={ref}
    display={display}
    className={cn(
      // Gap
      {
        "gap-1": gap === "xs",
        "gap-2": gap === "sm",
        "gap-4": gap === "md",
        "gap-6": gap === "lg",
        "gap-8": gap === "xl",
      },
      
      className
    )}
    style={{
      gridTemplateColumns: autoFit 
        ? `repeat(auto-fit, minmax(${minItemWidth}, 1fr))`
        : typeof columns === "number" 
          ? `repeat(${columns}, 1fr)`
          : columns,
      gridTemplateRows: typeof rows === "number" 
        ? `repeat(${rows}, 1fr)`
        : rows,
      ...style,
    }}
    {...props}
  />
))
GridContainer.displayName = "GridContainer"

const CenteredContainer = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement>
>(({ variant = "centered", ...props }, ref) => (
  <Container ref={ref} variant={variant} {...props} />
))
CenteredContainer.displayName = "CenteredContainer"

const ConstrainedContainer = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement>
>(({ variant = "constrained", ...props }, ref) => (
  <Container ref={ref} variant={variant} {...props} />
))
ConstrainedContainer.displayName = "ConstrainedContainer"

const FluidContainer = React.forwardRef<
  HTMLDivElement,
  ContainerProps & React.HTMLAttributes<HTMLDivElement>
>(({ variant = "fluid", size = "full", ...props }, ref) => (
  <Container ref={ref} variant={variant} size={size} {...props} />
))
FluidContainer.displayName = "FluidContainer"

export {
  Container,
  FlexContainer,
  GridContainer,
  CenteredContainer,
  ConstrainedContainer,
  FluidContainer,
}

export type {
  ContainerProps,
  ContainerVariant,
  ContainerSize,
  ContainerDisplay,
}