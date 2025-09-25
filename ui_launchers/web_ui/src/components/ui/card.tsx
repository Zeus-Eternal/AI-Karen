import * as React from "react";

import { cn } from "@/lib/utils";

type BaseCardProps = React.HTMLAttributes<HTMLDivElement>;

interface CardProps extends BaseCardProps {
  interactive?: boolean;
  variant?: "default" | "elevated" | "outlined" | "glass";
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, interactive = false, variant = "default", ...props }: CardProps, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border bg-card text-card-foreground smooth-transition",
        {
          "modern-card": variant === "default",
          "modern-card-elevated": variant === "elevated",
          "modern-card-outlined": variant === "outlined",
          "modern-card-glass": variant === "glass",
          interactive,
          "cursor-pointer": interactive,
        },
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }: BaseCardProps, ref) => (
    <div
      ref={ref}
      data-testid="card-header"
      className={cn("modern-card-header space-y-1.5", className)}
      {...props}
    />
  )
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }: BaseCardProps, ref) => (
    <div
      ref={ref}
      data-testid="card-title"
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
);
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }: BaseCardProps, ref) => (
    <div
      ref={ref}
      data-testid="card-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
);
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }: BaseCardProps, ref) => (
    <div
      ref={ref}
      data-testid="card-content"
      className={cn("modern-card-content", className)}
      {...props}
    />
  )
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, BaseCardProps>(
  ({ className, ...props }: BaseCardProps, ref) => (
    <div
      ref={ref}
      className={cn("modern-card-footer flex items-center", className)}
      {...props}
    />
  )
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
