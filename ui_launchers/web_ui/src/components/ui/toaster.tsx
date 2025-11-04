"use client";

import * as React from "react";
import { useToast } from "@/hooks/use-toast";
import {
  ToastProvider,
  Toast,
  ToastViewport,
  ToastTitle,
  ToastDescription,
  ToastClose,
} from "@/components/ui/toast";

/**
 * Drop-in Toaster wired to your useToast() store.
 * - Accessible (aria-live polite)
 * - Spreads per-toast props (variant, duration, etc.)
 * - Renders optional action node
 */
export function Toaster() {
  const { toasts } = useToast();

  return (
    <ToastProvider>
      <div
        role="status"
        aria-live="polite"
        aria-relevant="additions text"
        className="pointer-events-none fixed inset-0 z-[100] flex items-end px-4 py-6 sm:items-start sm:p-6"
      >
        {/* We still render ToastViewport to position toasts correctly */}
        <ToastViewport />

        {/* Render individual toasts */}
        <div className="flex w-full flex-col gap-2 sm:mt-4 sm:w-auto">
          {toasts.map(({ id, title, description, action, ...props }) => (
            <Toast key={id} {...props}>
              <div className="grid gap-1">
                {title ? <ToastTitle>{title}</ToastTitle> : null}
                {description ? (
                  <ToastDescription>{description}</ToastDescription>
                ) : null}
              </div>
              {action ? action : null}
              <ToastClose />
            </Toast>
          ))}
        </div>
      </div>
    </ToastProvider>
  );
}
