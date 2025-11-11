"use client";

import * as React from "react";

import { useToast, type ToasterToast } from "@/hooks/use-toast";
import {
  ToastProvider,
  Toast,
  ToastViewport,
  ToastTitle,
  ToastDescription,
  ToastClose,
  type ToastProps as UiToastProps,
} from "@/components/ui/toast";
import { cn } from "@/lib/utils";

type ToastPosition = "top-left" | "top-right" | "bottom-left" | "bottom-right";

const viewportPositionClasses: Record<ToastPosition, string> = {
  "top-left": "top-0 left-0 sm:left-0 sm:top-0",
  "top-right": "top-0 right-0 sm:right-0 sm:top-0",
  "bottom-left": "bottom-0 left-0 sm:left-0 sm:bottom-0",
  "bottom-right": "bottom-0 right-0 sm:right-0 sm:bottom-0",
};

const stackAlignmentClasses: Record<ToastPosition, string> = {
  "top-left": "items-start sm:items-start",
  "top-right": "items-end sm:items-end",
  "bottom-left": "items-start sm:items-start",
  "bottom-right": "items-end sm:items-end",
};

const stackJustifyClasses: Record<ToastPosition, string> = {
  "top-left": "sm:mt-0 sm:mb-4",
  "top-right": "sm:mt-0 sm:mb-4",
  "bottom-left": "sm:mt-4",
  "bottom-right": "sm:mt-4",
};

export interface AppToasterProps {
  /**
   * Controls where toast notifications originate from on screen.
   * Defaults to the bottom-right corner to match the design system.
   */
  position?: ToastPosition;
  /**
   * When true, success/info toasts receive richer gradient styling while
   * destructive variants keep their critical palette.
   */
  richColors?: boolean;
}

function buildToastClassName(
  variant: ToastProps["variant"],
  className: string | undefined,
  richColors?: boolean,
) {
  if (!richColors || (variant ?? "default") === "destructive") {
    return className;
  }

  return cn(
    "bg-gradient-to-r from-karen-primary/90 to-karen-secondary/90 text-white",
    "border-transparent shadow-xl",
    className,
  );
}

export function Toaster({ position = "bottom-right", richColors = false }: AppToasterProps) {
  const { toasts } = useToast();

  return (
    <ToastProvider>
      <div
        role="status"
        aria-live="polite"
        aria-relevant="additions text"
        className={cn(
          "pointer-events-none fixed inset-0 z-[100] flex px-4 py-6 sm:p-6",
          stackAlignmentClasses[position],
        )}
      >
        <ToastViewport
          className={cn(
            "pointer-events-none",
            viewportPositionClasses[position],
          )}
        />

        <div
          className={cn(
            "flex w-full flex-col gap-2 sm:w-auto",
            stackJustifyClasses[position],
          )}
        >
          {toasts.map((toast) => {
            const { id, title, description, action, ...props } = toast as ToasterToast;
            const toastProps = props as UiToastProps;
            const { className, variant, ...rest } = toastProps;

            return (
              <Toast
                key={id}
                variant={variant}
                className={buildToastClassName(variant, className, richColors)}
                {...rest}
              >
                <div className="grid gap-1">
                  {title ? <ToastTitle>{title}</ToastTitle> : null}
                  {description ? <ToastDescription>{description}</ToastDescription> : null}
                </div>
                {action}
                <ToastClose />
              </Toast>
            );
          })}
        </div>
      </div>
    </ToastProvider>
  );
}
