"use client";

import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { ChevronDown, ChevronUp, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AlertAction, KarenAlert } from "@/types/karen-alerts";

const karenToastVariants = cva(
  "group pointer-events-auto relative flex w-full items-start justify-between gap-4 overflow-hidden rounded-lg border p-4 pr-8 shadow-lg backdrop-blur-sm transition-all duration-300 ease-in-out hover:scale-[1.02] hover:shadow-xl focus-within:ring-2 focus-within:ring-offset-2 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full motion-reduce:transition-none motion-reduce:hover:scale-100",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground focus-within:ring-ring",
        destructive:
          "border-destructive bg-destructive text-destructive-foreground focus-within:ring-destructive",
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

export type KarenToastVariant = NonNullable<VariantProps<typeof karenToastVariants>["variant"]>;

const VARIANT_DURATIONS: Partial<Record<KarenToastVariant, number>> = {
  default: 5000,
  destructive: 7000,
  "karen-success": 4000,
  "karen-info": 5000,
  "karen-warning": 6000,
  "karen-error": 7000,
  "karen-system": 7000,
};

const resolveDuration = (
  alert: KarenAlert | undefined,
  variant: KarenToastVariant,
  explicit?: number
): number => {
  if (typeof explicit === "number") {
    return explicit;
  }

  if (alert?.duration) {
    return alert.duration;
  }

  return VARIANT_DURATIONS[variant] ?? VARIANT_DURATIONS.default ?? 5000;
};

const actionButtonVariant = (
  variant: AlertAction["variant"] | undefined
): React.ComponentProps<typeof Button>["variant"] => {
  switch (variant) {
    case "destructive":
      return "destructive";
    case "outline":
      return "outline";
    default:
      return "secondary";
  }
};

export interface KarenToastProgressProps
  extends React.HTMLAttributes<HTMLDivElement> {
  duration?: number;
  variant?: KarenToastVariant;
  enableAnimations?: boolean;
}

const KarenToastProgress = React.forwardRef<HTMLDivElement, KarenToastProgressProps>(
  (
    {
      className,
      duration = VARIANT_DURATIONS.default ?? 5000,
      variant = "default",
      enableAnimations = true,
      ...props
    },
    ref
  ) => {
    const [progress, setProgress] = React.useState(100);

    React.useEffect(() => {
      if (!enableAnimations || duration <= 0) {
        setProgress(0);
        return;
      }

      let frameId: number;
      const start = performance.now();

      const step = (timestamp: number) => {
        const elapsed = timestamp - start;
        const next = Math.max(0, 100 - (elapsed / duration) * 100);
        setProgress(next);

        if (next > 0) {
          frameId = requestAnimationFrame(step);
        }
      };

      frameId = requestAnimationFrame(step);

      return () => cancelAnimationFrame(frameId);
    }, [duration, enableAnimations]);

    const variantStyles: Record<KarenToastVariant, string> = {
      default: "bg-gradient-to-r from-primary/70 to-primary",
      destructive: "bg-gradient-to-r from-red-500 to-red-600",
      "karen-success": "bg-gradient-to-r from-green-400 to-green-600",
      "karen-info": "bg-gradient-to-r from-blue-400 to-blue-600",
      "karen-warning": "bg-gradient-to-r from-amber-400 to-amber-600",
      "karen-error": "bg-gradient-to-r from-red-500 to-red-700",
      "karen-system": "bg-gradient-to-r from-purple-500 to-purple-700",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "h-1 w-full overflow-hidden rounded-full bg-current/10",
          className
        )}
        role="presentation"
        {...props}
      >
        <div
          className={cn(
            "h-full w-full origin-left rounded-full transition-[width] duration-100 ease-linear motion-reduce:transition-none",
            variantStyles[variant] ?? variantStyles.default
          )}
          style={{ width: `${progress}%` }}
        />
      </div>
    );
  }
);
KarenToastProgress.displayName = "KarenToastProgress";

export interface KarenToastProps
  extends React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> {
  variant?: KarenToastVariant;
  alert?: KarenAlert;
  showProgress?: boolean;
  onActionClick?: (action: AlertAction) => void;
  enableAnimations?: boolean;
}

const KarenToast = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Root>,
  KarenToastProps
>(
  (
    {
      className,
      children,
      variant = "default",
      alert,
      showProgress = false,
      onActionClick,
      enableAnimations = true,
      duration: durationProp,
      ...props
    },
    ref
  ) => {
    const resolvedVariant = alert?.variant ?? variant;
    const resolvedDuration = resolveDuration(
      alert,
      resolvedVariant,
      typeof durationProp === "number" ? durationProp : undefined
    );

    const [isExpanded, setIsExpanded] = React.useState(false);

    const handleActionClick = React.useCallback(
      async (action: AlertAction) => {
        await action.action();
        onActionClick?.(action);
      },
      [onActionClick]
    );

    return (
      <ToastPrimitives.Root
        ref={ref}
        className={cn(karenToastVariants({ variant: resolvedVariant }), className)}
        duration={resolvedDuration}
        {...props}
      >
        <div className="flex w-full flex-col gap-3">
          <div className="flex items-start gap-3">
            {alert?.emoji ? (
              <div
                className="flex h-8 w-8 items-center justify-center text-2xl"
                role="img"
                aria-label="Alert indicator"
              >
                {alert.emoji}
              </div>
            ) : null}

            <div className="flex-1 space-y-1">
              {alert?.title ? (
                <KarenToastTitle>{alert.title}</KarenToastTitle>
              ) : null}
              {alert?.message ? (
                <KarenToastDescription>{alert.message}</KarenToastDescription>
              ) : null}
              {children}
            </div>
          </div>

          {alert?.expandableContent ? (
            <div className="space-y-2">
              <Button
                type="button"
                variant="link"
                size="sm"
                className="h-auto px-0 text-xs font-medium opacity-75 hover:opacity-100"
                onClick={() => setIsExpanded((prev) => !prev)}
                aria-expanded={isExpanded}
                aria-controls="karen-toast-expandable"
              >
                <span>{isExpanded ? "Show less" : "Show more"}</span>
                {isExpanded ? (
                  <ChevronUp className="ml-1 h-3 w-3" />
                ) : (
                  <ChevronDown className="ml-1 h-3 w-3" />
                )}
              </Button>
              {isExpanded ? (
                <div
                  id="karen-toast-expandable"
                  className="rounded-md bg-black/5 p-3 text-xs text-foreground/80 dark:bg-white/5 sm:text-sm"
                >
                  {alert.expandableContent}
                </div>
              ) : null}
            </div>
          ) : null}

          {alert?.actions?.length ? (
            <div className="flex flex-wrap gap-2 pt-2">
              {alert.actions.map((action) => (
                <Button
                  key={action.label}
                  type="button"
                  variant={actionButtonVariant(action.variant)}
                  size="sm"
                  onClick={() => void handleActionClick(action)}
                >
                  {action.icon ? <span className="mr-1">{action.icon}</span> : null}
                  {action.label}
                </Button>
              ))}
            </div>
          ) : null}
        </div>

        {showProgress && resolvedDuration > 0 ? (
          <KarenToastProgress
            duration={resolvedDuration}
            variant={resolvedVariant}
            enableAnimations={enableAnimations}
            className="mt-3"
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
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action> & {
    variant?: "default" | "destructive" | "outline";
  }
>(({ className, variant = "default", ...props }, ref) => {
  const variantStyles: Record<"default" | "destructive" | "outline", string> = {
    destructive: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    outline: "border border-current/20 bg-transparent hover:bg-current/10 focus:ring-current",
    default: "bg-current/10 hover:bg-current/20 focus:ring-current",
  };

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
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Title
    ref={ref}
    className={cn("text-sm font-semibold leading-tight", className)}
    {...props}
  />
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

export type KarenToastPropsPublic = React.ComponentPropsWithoutRef<typeof KarenToast>;
export type KarenToastActionElement = React.ReactElement<typeof KarenToastAction>;

export {
  type KarenToastVariant,
  type KarenToastPropsPublic as KarenToastProps,
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
