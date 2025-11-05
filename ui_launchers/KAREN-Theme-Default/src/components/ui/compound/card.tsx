"use client"

import * as React from "react";
import { cn } from "@/lib/utils";
// Base types for compound components
interface BaseCardProps extends React.HTMLAttributes<HTMLDivElement> {}

interface CardRootProps extends BaseCardProps {
  interactive?: boolean
  variant?: "default" | "elevated" | "outlined" | "glass"
}

interface CardActionsProps extends BaseCardProps {
  justify?: "start" | "center" | "end" | "between"
}

// Card Root Component
const CardRoot = React.forwardRef<HTMLDivElement, CardRootProps>(
  ({ className, interactive = false, variant = "default", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border bg-card text-card-foreground smooth-transition",
        {
          "modern-card": variant === "default",
          "modern-card-elevated": variant === "elevated", 
          "modern-card-outlined": variant === "outlined",
          "modern-card-glass": variant === "glass",
          "cursor-pointer hover:shadow-md": interactive,
        },
        className
      )}
      {...props}
    />
  )
)
CardRoot.displayName = "CardRoot"

// Card Header Component
const CardHeader = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("modern-card-header space-y-1.5 p-6", className)}
      {...props}
    />
  )
)
CardHeader.displayName = "CardHeader"

// Card Title Component
const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
)
CardTitle.displayName = "CardTitle"

// Card Description Component
const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
)
CardDescription.displayName = "CardDescription"

// Card Content Component
const CardContent = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("modern-card-content p-6 pt-0", className)}
      {...props}
    />
  )
)
CardContent.displayName = "CardContent"

// Card Footer Component
const CardFooter = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("modern-card-footer flex items-center p-6 pt-0", className)}
      {...props}
    />
  )
)
CardFooter.displayName = "CardFooter"

// Card Actions Component
const CardActions = React.forwardRef<HTMLDivElement, CardActionsProps>(
  ({ className, justify = "end", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-center gap-2 p-6 pt-0",
        {
          "justify-start": justify === "start",
          "justify-center": justify === "center", 
          "justify-end": justify === "end",
          "justify-between": justify === "between",
        },
        className
      )}
      {...props}
    />
  )
)
CardActions.displayName = "CardActions"

// Compound Card Component
const Card = {
  Root: CardRoot,
  Header: CardHeader,
  Title: CardTitle,
  Description: CardDescription,
  Content: CardContent,
  Footer: CardFooter,
  Actions: CardActions,
}

export {
  Card,
  CardRoot,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardActions,
}

export type {
  CardRootProps,
  CardActionsProps,
}