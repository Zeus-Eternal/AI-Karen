import React from "react";
const { forwardRef } = React;
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export type AlertProps = React.ComponentPropsWithoutRef<"div"> &
  VariantProps<typeof alertVariants> & {
    ariaLabel?: string;
    ariaLive?: 'polite' | 'assertive' | 'off';
    dismissible?: boolean;
    onDismiss?: () => void;
  }

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({
    className,
    variant,
    children,
    ariaLabel,
    ariaLive,
    dismissible = false,
    onDismiss,
    ...props
  }, ref) => {
    const alertId = React.useId();
    
    return (
      <div
        ref={ref}
        id={alertId}
        role="alert"
        aria-label={ariaLabel}
        aria-live={ariaLive || (variant === 'destructive' ? 'assertive' : 'polite')}
        data-testid="alert"
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        {children}
        {dismissible && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="absolute top-4 right-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            aria-label="Dismiss alert"
            aria-controls={alertId}
          >
            <span aria-hidden="true">×</span>
          </button>
        )}
      </div>
    );
  }
)
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<
  HTMLHeadingElement,
  React.ComponentPropsWithoutRef<"h5">
>(({ className, children, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  >
    {children}
  </h5>
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<"div">
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    data-testid="alert-description"
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  >
    {children}
  </div>
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription };
