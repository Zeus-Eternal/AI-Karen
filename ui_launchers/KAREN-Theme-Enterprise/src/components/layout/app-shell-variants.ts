import { cva, type VariantProps } from "class-variance-authority";

export const appShellVariants = cva(
  [
    "min-h-screen",
    "bg-[var(--color-neutral-50)] dark:bg-[var(--color-neutral-950)]",
    "transition-colors [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
  ],
  {
    variants: {
      layout: {
        default: "flex",
        grid: "grid grid-cols-[auto_1fr] grid-rows-[auto_1fr]",
      },
    },
    defaultVariants: {
      layout: "default",
    },
  }
);

export const appShellSidebarVariants = cva(
  [
    "flex flex-col",
    "bg-[var(--color-neutral-100)] dark:bg-[var(--color-neutral-900)]",
    "border-r border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]",
    "transition-all [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
    "z-50",
    "focus:outline-none",
  ],
  {
    variants: {
      state: {
        open: "translate-x-0",
        closed: "-translate-x-full lg:translate-x-0",
        collapsed: "w-16",
        expanded: "w-64",
      },
      position: {
        fixed: "fixed top-0 left-0 h-full",
        relative: "relative",
      },
    },
    defaultVariants: {
      state: "open",
      position: "relative",
    },
  }
);

export const appShellHeaderVariants = cva([
  "sticky top-0 z-30",
  "flex items-center",
  "min-h-[var(--header-height)]",
  "px-[var(--space-lg)]",
  "bg-[var(--glass-background-strong)]",
  "border-b border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]",
  "backdrop-blur-[var(--backdrop-blur-lg)]",
  "transition-colors [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
]);

export const appShellMainVariants = cva([
  "flex-1 min-h-0",
  "p-[var(--space-lg)]",
  "bg-[var(--color-neutral-50)] dark:bg-[var(--color-neutral-950)]",
  "transition-colors [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
]);

export type AppShellMainVariants = VariantProps<typeof appShellMainVariants>;

export const appShellFooterVariants = cva([
  "flex items-center justify-between",
  "px-[var(--space-lg)] py-[var(--space-md)]",
  "bg-[var(--color-neutral-100)] dark:bg-[var(--color-neutral-900)]",
  "border-t border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]",
  "text-[var(--text-sm)] text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]",
]);
