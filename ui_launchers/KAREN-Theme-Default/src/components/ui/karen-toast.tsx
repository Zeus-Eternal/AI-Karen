"use client";

import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { ChevronDown, ChevronUp, X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { AlertAction, KarenAlert } from "@/types/karen-alerts";

const karenToastVariants = cva(
  "group pointer-events-auto relative flex w-full items-start justify-between space-x-4 overflow-hidden rounded-lg border p-4 pr-8 shadow-lg backdrop-blur-sm transition-all duration-300 ease-in-out hover:scale-[1.02] hover:shadow-xl focus-within:ring-2 focus-within:ring-offset-2 data-[state=open]:animate-in data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full data-[state=closed]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[swipe=cancel]:translate-x-0 data-[swipe=end]:animate-out data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none motion-reduce:hover:scale-100 motion-reduce:transition-none",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground focus-within:ring-ring",
        destructive:
          "destructive border-destructive bg-destructive text-destructive-foreground focus-within:ring-destructive",
        "karen-success":
          "border-green-200 bg-green-50/90 text-green-900 shadow-green-100/50 hover:border-green-300 hover:bg-green-100/90 focus-within:ring-green-500 dark:border-green-800 dark:bg-green-950/90 dark:text-green-100 dark:shadow-green-900/20 dark:hover:border-green-700 dark:hover:bg-green-900/90",
        "karen-info":
          "border-blue-200 bg-blue-50/90 text-blue-900 shadow-blue-100/50 hover:border-blue-300 hover:bg-blue-100/90 focus-within:ring-blue-500 dark:border-blue-800 dark:bg-blue-950/90 dark:text-blue-100 dark:shadow-blue-900/20 dark:hover:border-blue-700 dark:hover:bg-blue-900/90",
        "karen-warning":
          "border-amber-200 bg-amber-50/90 text-amber-900 shadow-amber-100/50 hover:border-amber-300 hover:bg-amber-100/90 focus-within:ring-amber-500 dark:border-amber-800 dark:bg-amber-950/90 dark:text-amber-100 dark:shadow-amber-900/20 dark:hover:border-amber-700 dark:hover:bg-amber-900/90",
        "karen-error":
          "border-red-200 bg-red-50/90 text-red-900 shadow-red-100/50 hover:border-red-300 hover:bg-red-100/90 focus-within:ring-red-500 dark:border-red-800 dark:bg-red-950/90 dark:text-red-100 dark:shadow-red-900/20 dark:hover:border-red-700 dark:hover:bg-red-900/90",
        "karen-system":
          "border-purple-200 bg-purple-50/90 text-purple-900 shadow-purple-100/50 hover:border-purple-300 hover:bg-purple-100/90 focus-within:ring-purple-500 dark:border-purple-800 dark:bg-purple-950/90 dark:text-purple-100 dark:shadow-purple-900/20 dark:hover:border-purple-700 dark:hover:bg-purple-900/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

type ToastVariant = VariantProps<typeof karenToastVariants>["variant"];

const PROGRESS_COLOR_BY_VARIANT: Record<Exclude<ToastVariant, undefined>, string> = {
  default: "bg-gradient-to-r from-primary/80 to-primary shadow-sm",
  destructive: "bg-gradient-to-r from-red-500 to-red-700 shadow-sm shadow-red-200 dark:shadow-red-900/20",
  "karen-success": "bg-gradient-to-r from-green-400 to-green-600 shadow-sm shadow-green-200 dark:shadow-green-900/20",
  "karen-info": "bg-gradient-to-r from-blue-400 to-blue-600 shadow-sm shadow-blue-200 dark:shadow-blue-900/20",
  "karen-warning": "bg-gradient-to-r from-amber-400 to-amber-600 shadow-sm shadow-amber-200 dark:shadow-amber-900/20",
  "karen-error": "bg-gradient-to-r from-red-400 to-red-600 shadow-sm shadow-red-200 dark:shadow-red-900/20",
  "karen-system": "bg-gradient-to-r from-purple-400 to-purple-600 shadow-sm shadow-purple-200 dark:shadow-purple-900/20",
};

/**
 * Enhanced progress indicator for timed alerts with smooth animations
 */
const KarenToastProgress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    duration?: number;
    variant?: ToastVariant;
    enableAnimations?: boolean;
  }
>(({ className, duration = 5000, variant = "default", enableAnimations = true, ...props }, ref) => {
  const [progress, setProgress] = React.useState(100);

  React.useEffect(() => {
    setProgress(100);

    if (duration <= 0 || !enableAnimations) {
      return;
    }

    const interval = window.setInterval(() => {
      setProgress((prev) => {
        const nextValue = prev - 100 / (duration / 100);
        return nextValue <= 0 ? 0 : nextValue;
      });
    }, 100);

    return () => window.clearInterval(interval);
  }, [duration, enableAnimations]);

  const resolvedVariant: Exclude<ToastVariant, undefined> = variant ?? "default";
  const progressClassName = PROGRESS_COLOR_BY_VARIANT[resolvedVariant] ?? PROGRESS_COLOR_BY_VARIANT.default;

  return (
    <div
      ref={ref}
      className={cn("relative h-1 w-full overflow-hidden rounded-full bg-current/10", className)}
      {...props}
    >
      <div
        className={cn(
          "h-full origin-left transform transition-all duration-100 ease-linear motion-reduce:transition-none",
          progressClassName
        )}
        style={{ width: `${progress}%` }}
      />
    </div>
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
  ({
    className,
    variant,
    alert,
    showProgress = true,
    onActionClick,
    duration,
    children,
    ...props
  }, ref) => {
    const [isExpanded, setIsExpanded] = React.useState(false);

    const resolvedVariant: Exclude<ToastVariant, undefined> = alert?.variant ?? variant ?? "default";
    const resolvedDuration = alert?.duration ?? duration;

    const handleActionClick = React.useCallback(
      (action: AlertAction) => {
        try {
          const outcome = action.action();
          if (outcome && typeof (outcome as Promise<unknown>).finally === "function") {
            (outcome as Promise<unknown>).finally(() => onActionClick?.(action));
          } else {
            onActionClick?.(action);
          }
        } catch (error) {
          onActionClick?.(action);
          throw error;
        }
      },
      [onActionClick]
    );

    const hasCustomChildren = React.Children.count(children) > 0;

    return (
      <ToastPrimitives.Root
        ref={ref}
        className={cn(karenToastVariants({ variant: resolvedVariant }), className)}
        duration={resolvedDuration}
        {...props}
      >
        <div className="flex w-full flex-col space-y-3">
          <div className="flex items-start space-x-3">
            {alert?.emoji ? (
              <div className="flex-shrink-0 text-lg" role="img" aria-label="Alert indicator">
                {alert.emoji}
              </div>
            ) : null}

            <div className="flex-1 space-y-2">
              {hasCustomChildren ? (
                children
              ) : (
                <>
                  {alert?.title ? (
                    <p className="text-sm font-semibold leading-tight">{alert.title}</p>
                  ) : null}
                  {alert?.message ? (
                    <p className="text-sm leading-relaxed text-foreground/80">{alert.message}</p>
                  ) : null}
                </>
              )}

              {alert?.expandableContent ? (
                <div>
                  <button
                    type="button"
                    onClick={() => setIsExpanded((value) => !value)}
                    className="flex items-center space-x-1 text-xs font-medium opacity-75 transition-opacity hover:opacity-100 sm:text-sm md:text-base"
                    aria-expanded={isExpanded}
                    aria-controls="karen-toast-expandable-content"
                  >
                    <span>{isExpanded ? "Show less" : "Show more"}</span>
                    {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>

                  {isExpanded ? (
                    <div
                      id="karen-toast-expandable-content"
                      className="mt-2 rounded bg-black/5 p-2 text-xs dark:bg-white/5 sm:text-sm md:text-base"
                    >
                      {alert.expandableContent}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>

          {alert?.actions && alert.actions.length > 0 ? (
            <div className="flex flex-wrap gap-2 border-t border-current/10 pt-2">
              {alert.actions.map((action, index) => {
                const variantClassName =
                  action.variant === "destructive"
                    ? "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500"
                    : action.variant === "outline"
                    ? "border border-current/20 bg-transparent hover:bg-current/10 focus-visible:ring-current"
                    : "bg-current/10 hover:bg-current/20 focus-visible:ring-current";

                return (
                  <button
                    key={`${action.label}-${index}`}
                    type="button"
                    onClick={() => handleActionClick(action)}
                    className={cn(
                      "inline-flex h-7 items-center justify-center rounded-md px-3 text-xs font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                      variantClassName
                    )}
                  >
                    {action.icon ? <span className="mr-1">{action.icon}</span> : null}
                    {action.label}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>

        {showProgress && resolvedDuration ? (
          <KarenToastProgress
            className="mt-3"
            duration={resolvedDuration}
            enableAnimations
            variant={resolvedVariant}
          />
        ) : null}

        <KarenToastClose />
      </ToastPrimitives.Root>
    );
  }
);
KarenToast.displayName = "KarenToast";

const KarenToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action> & { variant?: "default" | "destructive" | "outline" }
>(({ className, variant = "default", ...props }, ref) => {
  const variantStyles = {
    destructive: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500",
    outline: "border border-current/20 bg-transparent hover:bg-current/10 focus-visible:ring-current",
    default: "bg-current/10 hover:bg-current/20 focus-visible:ring-current",
  } as const;

  return (
    <ToastPrimitives.Action
      ref={ref}
      className={cn(
        "inline-flex h-7 items-center justify-center rounded-md px-3 text-xs font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
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
      "absolute right-2 top-2 rounded-md p-1 text-current/50 opacity-0 transition-opacity hover:text-current focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-current/20 group-hover:opacity-100",
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
    {emoji ? (
      <span className="mr-2" role="img" aria-label="Alert indicator">
        {emoji}
      </span>
    ) : null}
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
    className={cn("text-sm leading-relaxed text-foreground/80", className)}
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
    "top-left": "top-0 left-0 flex-col sm:left-4 sm:top-4",
    "top-right": "top-0 right-0 flex-col sm:right-4 sm:top-4",
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
  type KarenToastProps,
  type KarenToastActionElement,
  karenToastVariants,
  KarenToastProvider,
  KarenToastViewport,
  KarenToast,
  KarenToastTitle,
  KarenToastDescription,
  KarenToastClose,
  KarenToastAction,
  KarenToastProgress,
};
