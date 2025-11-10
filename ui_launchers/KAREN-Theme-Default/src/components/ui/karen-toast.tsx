"use client";

import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { ChevronDown, ChevronUp, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AlertAction, KarenAlert } from "@/types/karen-alerts";

const karenToastVariants = cva(
  "group pointer-events-auto relative flex w-full items-start justify-between space-x-4 overflow-hidden rounded-lg border p-4 pr-8 shadow-lg backdrop-blur-sm transition-all duration-300 ease-in-out hover:shadow-xl hover:scale-[1.02] focus-within:ring-2 focus-within:ring-offset-2 data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full motion-reduce:transition-none motion-reduce:hover:scale-100",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground focus-within:ring-ring",
        destructive:
          "destructive border-destructive bg-destructive text-destructive-foreground focus-within:ring-destructive",
        "karen-success":
          "border-green-200 bg-green-50/90 text-green-900 shadow-green-100/50 hover:bg-green-100/90 hover:border-green-300 focus-within:ring-green-500 dark:border-green-800 dark:bg-green-950/90 dark:text-green-100 dark:shadow-green-900/20 dark:hover:bg-green-900/90 dark:hover:border-green-700",
        "karen-info":
          "border-blue-200 bg-blue-50/90 text-blue-900 shadow-blue-100/50 hover:bg-blue-100/90 hover:border-blue-300 focus-within:ring-blue-500 dark:border-blue-800 dark:bg-blue-950/90 dark:text-blue-100 dark:shadow-blue-900/20 dark:hover:bg-blue-900/90 dark:hover:border-blue-700",
        "karen-warning":
          "border-amber-200 bg-amber-50/90 text-amber-900 shadow-amber-100/50 hover:bg-amber-100/90 hover:border-amber-300 focus-within:ring-amber-500 dark:border-amber-800 dark:bg-amber-950/90 dark:text-amber-100 dark:shadow-amber-900/20 dark:hover:bg-amber-900/90 dark:hover:border-amber-700",
        "karen-error":
          "border-red-200 bg-red-50/90 text-red-900 shadow-red-100/50 hover:bg-red-100/90 hover:border-red-300 focus-within:ring-red-500 dark:border-red-800 dark:bg-red-950/90 dark:text-red-100 dark:shadow-red-900/20 dark:hover:bg-red-900/90 dark:hover:border-red-700",
        "karen-system":
          "border-purple-200 bg-purple-50/90 text-purple-900 shadow-purple-100/50 hover:bg-purple-100/90 hover:border-purple-300 focus-within:ring-purple-500 dark:border-purple-800 dark:bg-purple-950/90 dark:text-purple-100 dark:shadow-purple-900/20 dark:hover:bg-purple-900/90 dark:hover:border-purple-700",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

/**
 * Enhanced progress indicator for timed alerts with smooth animations
 */
const KarenToastProgress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    duration?: number;
    variant?: VariantProps<typeof karenToastVariants>["variant"];
    enableAnimations?: boolean;
  }
>(({ className, duration = 5000, variant = "default", enableAnimations = true, ...props }, ref) => {
  const [progress, setProgress] = React.useState(100);

  React.useEffect(() => {
    if (duration <= 0 || !enableAnimations) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (duration / 100));
        return newProgress <= 0 ? 0 : newProgress;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [duration, enableAnimations]);

  const getProgressColor = () => {
    switch (variant) {
      case "karen-success":
        return "bg-gradient-to-r from-green-400 to-green-600 shadow-sm shadow-green-200 dark:shadow-green-900/20";
      case "karen-info":
        return "bg-gradient-to-r from-blue-400 to-blue-600 shadow-sm shadow-blue-200 dark:shadow-blue-900/20";
      case "karen-warning":
        return "bg-gradient-to-r from-amber-400 to-amber-600 shadow-sm shadow-amber-200 dark:shadow-amber-900/20";
      case "karen-error":
        return "bg-gradient-to-r from-red-400 to-red-600 shadow-sm shadow-red-200 dark:shadow-red-900/20";
      case "karen-system":
        return "bg-gradient-to-r from-purple-400 to-purple-600 shadow-sm shadow-purple-200 dark:shadow-purple-900/20";
      default:
        return "bg-gradient-to-r from-primary/80 to-primary shadow-sm";
    }
  };

  return (
    <div
      className={cn(
        "h-full transition-all duration-100 ease-linear motion-reduce:transition-none",
        getProgressColor()
      )}
      style={{ 
        width: `${progress}%`,
        '--duration': `${duration}ms`
      } as React.CSSProperties}
    />
  );
});
      
KarenToastProgress.displayName = "KarenToastProgress";

type KarenToastRootProps = React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> &
  VariantProps<typeof karenToastVariants> & {
    alert?: KarenAlert;
    showProgress?: boolean;
    onActionClick?: (action: AlertAction) => void;
  };

const KarenToast = React.forwardRef<React.ElementRef<typeof ToastPrimitives.Root>, KarenToastRootProps>(
  ({ className, variant, alert, showProgress = true, onActionClick, duration, ...props }, ref) => {
    const [isExpanded, setIsExpanded] = React.useState(false);

    const handleActionClick = React.useCallback(
      (action: AlertAction) => {
        action.action();
        onActionClick?.(action);
      },
      [onActionClick]
    );

    const resolvedDuration = alert?.duration ?? duration;

    return (
      <ToastPrimitives.Root
        ref={ref}
        className={cn(karenToastVariants({ variant: alert?.variant ?? variant }), className)}
        duration={resolvedDuration}
        {...props}
      >
        <div className="flex w-full flex-col space-y-2">
          <div className="flex items-start space-x-3">
            {alert?.emoji && (
              <div className="flex-shrink-0 text-lg" role="img" aria-label="Alert indicator">
                {alert.emoji}
              </div>
            )}
            
            {/* Expandable content */}
            {alert?.expandableContent && (
              <div className="mt-2">
                <button
                  type="button"
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="flex items-center space-x-1 text-xs font-medium opacity-75 hover:opacity-100 transition-opacity sm:text-sm md:text-base"
                  aria-expanded={isExpanded}
                  aria-controls="expandable-content"
                >
                  <span>{isExpanded ? "Show less" : "Show more"}</span>
                  {isExpanded ? (
                    <ChevronUp className="h-3 w-3 " />
                  ) : (
                    <ChevronDown className="h-3 w-3 " />
                  )}
                </button>
                
                {isExpanded && (
                  <div
                    id="expandable-content"
                    className="mt-2 p-2 rounded bg-black/5 dark:bg-white/5 text-xs sm:text-sm md:text-base"
                  >
                    {alert.expandableContent}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        {/* Action buttons */}
        {alert?.actions && alert.actions.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2 border-t border-current/10">
            {alert.actions.map((action, index) => (
              <button
                key={index}
                type="button"
                onClick={() => {
                  action.action();
                  onActionClick?.(action);
                }}
                className={cn(
                  "inline-flex h-7 items-center justify-center rounded-md px-3 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                  action.variant === "destructive"
                    ? "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500"
                    : action.variant === "outline"
                    ? "border border-current/20 bg-transparent hover:bg-current/10 focus:ring-current"
                    : "bg-current/10 hover:bg-current/20 focus:ring-current"
                )}
              >
                {action.icon && <span className="mr-1">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </div>
        )}
        
        {/* Progress indicator */}
      {showProgress && alert?.duration && (
        <KarenToastProgress duration={alert.duration} variant={variant} />
      )}
      
      {/* Close button */}
      <KarenToastClose />
    </ToastPrimitives.Root>
  );
});
KarenToast.displayName = "KarenToast";

const KarenToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action> & { variant?: "default" | "destructive" | "outline" }
>(({ className, variant = "default", ...props }, ref) => {
  const variantStyles = {
    destructive: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    outline: "border border-current/20 bg-transparent hover:bg-current/10 focus:ring-current",
    default: "bg-current/10 hover:bg-current/20 focus:ring-current",
  } as const;

  return (
    <ToastPrimitives.Action
      ref={ref}
      className={cn(
        "inline-flex h-7 items-center justify-center rounded-md px-3 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
});
    
KarenToastAction.displayName = "KarenToastAction";

const KarenToastClose = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Close
    ref={ref}
    className={cn(
      "absolute right-2 top-2 rounded-md p-1 text-current/50 opacity-0 transition-opacity hover:text-current focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-current/20 group-hover:opacity-100",
      className
    )}
    aria-label="Close notification"
    {...props}
  >
    <X className="h-4 w-4" />
  </ToastPrimitives.Close>
));
KarenToastClose.displayName = "KarenToastClose";

const KarenToastTitle = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title> & { emoji?: string }
>(({ className, emoji, children, ...props }, ref) => (
  <ToastPrimitives.Title ref={ref} className={cn("text-sm font-semibold leading-tight", className)} {...props}>
    {emoji && (
      <span className="mr-2" role="img" aria-label="Alert indicator">
        {emoji}
      </span>
    )}
    {children}
  </ToastPrimitives.Title>
));
KarenToastTitle.displayName = "KarenToastTitle";

const KarenToastDescription = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Description
    ref={ref}
    className={cn("text-sm opacity-90 leading-relaxed", className)}
    {...props}
  />
));
KarenToastDescription.displayName = "KarenToastDescription";

const KarenToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport> & {
    position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  }
>(({ className, position = "top-right", ...props }, ref) => {
  const positionClasses: Record<string, string> = {
    "top-left": "top-0 left-0 flex-col sm:top-4 sm:left-4",
    "top-right": "top-0 right-0 flex-col sm:top-4 sm:right-4",
    "bottom-left": "bottom-0 left-0 flex-col-reverse sm:bottom-4 sm:left-4",
    "bottom-right": "bottom-0 right-0 flex-col-reverse sm:bottom-4 sm:right-4",
  };

  return (
    <ToastPrimitives.Viewport
      ref={ref}
      className={cn(
        "fixed z-[100] flex max-h-screen w-full max-w-full gap-2 p-2 sm:max-w-[420px] sm:gap-3 sm:p-4",
        positionClasses[position],
        className
      )}
      {...props}
    />
  );
});
    
KarenToastViewport.displayName = "KarenToastViewport";

const KarenToastProvider = ToastPrimitives.Provider;

export type KarenToastProps = React.ComponentPropsWithoutRef<typeof KarenToast>;
export type KarenToastActionElement = React.ReactElement<typeof KarenToastAction>;

export {
  KarenToastProvider,
  KarenToastViewport,
  KarenToast,
  KarenToastTitle,
  KarenToastDescription,
  KarenToastClose,
  KarenToastAction,
  KarenToastProgress,
  karenToastVariants,
};
