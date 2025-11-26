"use client";

import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { type VariantProps } from "class-variance-authority";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle, Loader } from "lucide-react";

import { cn } from "../../lib/utils";
import { toastVariants } from "./toast-variants";

/** Provider */
export const ToastProvider = ToastPrimitives.Provider;

/** Viewport */
export const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Viewport
    ref={ref}
    className={cn(
      "fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px] gap-2",
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitives.Viewport.displayName;

/** Root */
export const Toast = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> &
    VariantProps<typeof toastVariants> & {
      icon?: React.ReactNode;
      loading?: boolean;
    }
>(({ className, variant, icon, loading = false, ...props }, ref) => {
  // Default icons based on variant
  const renderIcon = React.useMemo(() => {
    if (icon) return icon;
    if (loading) return <Loader className="h-5 w-5 animate-spin" />;
    
    switch (variant) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'destructive':
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
      case 'loading':
        return <Loader className="h-5 w-5 animate-spin" />;
      default:
        return null;
    }
  }, [icon, loading, variant]);

  return (
    <ToastPrimitives.Root
      ref={ref}
      className={cn(toastVariants({ variant }), className)}
      {...props}
    >
      {renderIcon && (
        <div className="flex-shrink-0">
          {renderIcon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <ToastPrimitives.Title className="text-sm font-semibold" />
        <ToastPrimitives.Description className="text-sm opacity-90" />
      </div>
      <ToastPrimitives.Close />
    </ToastPrimitives.Root>
  );
});
Toast.displayName = ToastPrimitives.Root.displayName;

/** Action */
export const ToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Action
    ref={ref}
    className={cn(
      "inline-flex h-8 shrink-0 items-center justify-center rounded-md border bg-transparent px-3 text-sm font-medium ring-offset-background transition-colors hover:bg-secondary focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 group-[.destructive]:border-muted/40 group-[.destructive]:hover:border-destructive/30 group-[.destructive]:hover:bg-destructive group-[.destructive]:hover:text-destructive-foreground group-[.destructive]:focus:ring-destructive",
      className
    )}
    {...props}
  />
));
ToastAction.displayName = ToastPrimitives.Action.displayName;

/** Close */
export const ToastClose = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Close
    ref={ref}
    className={cn(
      "absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100 group-[.destructive]:text-red-300 group-[.destructive]:hover:text-red-50 group-[.destructive]:focus:ring-red-400 group-[.destructive]:focus:ring-offset-red-600",
      className
    )}
    {...props}
  >
    <X className="h-4 w-4 " />
  </ToastPrimitives.Close>
));
ToastClose.displayName = ToastPrimitives.Close.displayName;

/** Title */
export const ToastTitle = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Title
    ref={ref}
    className={cn("text-sm font-semibold", className)}
    {...props}
  />
));
ToastTitle.displayName = ToastPrimitives.Title.displayName;

/** Description */
export const ToastDescription = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Description
    ref={ref}
    className={cn("text-sm opacity-90", className)}
    {...props}
  />
));
ToastDescription.displayName = ToastPrimitives.Description.displayName;

/** Enhanced toast with built-in icon and action */
export const EnhancedToast = React.forwardRef<
  React.ElementRef<typeof Toast>,
  React.ComponentPropsWithoutRef<typeof Toast> & {
    title?: string;
    description?: string;
    action?: React.ReactNode;
    icon?: React.ReactNode;
    loading?: boolean;
  }
>(({ title, description, action, icon, loading, ...props }, ref) => (
  <Toast ref={ref} icon={icon} loading={loading} {...props}>
    {title && <ToastTitle>{title}</ToastTitle>}
    {description && <ToastDescription>{description}</ToastDescription>}
    {action && (
      <ToastAction altText={typeof action === 'string' ? action : 'Action'}>
        {action}
      </ToastAction>
    )}
  </Toast>
));

EnhancedToast.displayName = "EnhancedToast";

/** Types */
export type ToastProps = React.ComponentPropsWithoutRef<typeof Toast>;
export type ToastActionElement = React.ReactElement<typeof ToastAction>;
