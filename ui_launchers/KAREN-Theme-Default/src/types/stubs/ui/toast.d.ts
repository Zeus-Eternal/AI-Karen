declare module '@/components/ui/toast' {
  import type { ReactNode } from 'react';

  export interface ToastProps {
    id?: string;
    title?: ReactNode;
    description?: ReactNode;
    action?: ToastActionElement;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    duration?: number;
    variant?: 'default' | 'destructive' | string;
    className?: string;
  }

  export type ToastActionElement = ReactNode;

  export interface ToastViewportProps {
    className?: string;
  }

  export const Toast: (props: ToastProps) => ReactNode;
  export const ToastAction: (props: { altText: string; children?: ReactNode }) => ReactNode;
  export const ToastClose: (props: { children?: ReactNode }) => ReactNode;
  export const ToastViewport: (props: ToastViewportProps) => ReactNode;
  export const ToastProvider: (props: { children?: ReactNode }) => ReactNode;
  export const ToastTitle: (props: { className?: string; children?: ReactNode }) => ReactNode;
  export const ToastDescription: (props: { className?: string; children?: ReactNode }) => ReactNode;
  export const Toaster: (props?: { children?: ReactNode }) => ReactNode;
}
