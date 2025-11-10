/**
 * AppShell Component
 *
 * Main application shell with responsive sidebar, header, and main content areas.
 * Enhanced with improved accessibility, keyboard navigation, and responsive behavior.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// -------------------- Context --------------------

export interface AppShellContextType {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (
    collapsed: boolean | ((prev: boolean) => boolean)
  ) => void;
  isMobile: boolean;
  isTablet: boolean;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  openSidebar: () => void;
}

const AppShellContext = createContext<AppShellContextType | undefined>(
  undefined
);

export function useAppShell() {
  const context = useContext(AppShellContext);
  if (!context) throw new Error("useAppShell must be used within an AppShell");
  return context;
}

// -------------------- Variants --------------------

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

export interface AppShellProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof appShellVariants> {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  defaultSidebarOpen?: boolean;
  defaultSidebarCollapsed?: boolean;
  sidebarBreakpoint?: number; // <lg
  tabletBreakpoint?: number; // <xl
  persistSidebarState?: boolean;
  enableKeyboardShortcuts?: boolean;
}

// -------------------- AppShell --------------------

export const AppShell = React.forwardRef<HTMLDivElement, AppShellProps>(
  (
    {
      className,
      layout,
      children,
      sidebar,
      header,
      footer,
      defaultSidebarOpen = true,
      defaultSidebarCollapsed = false,
      sidebarBreakpoint = 768,
      tabletBreakpoint = 1024,
      persistSidebarState = true,
      enableKeyboardShortcuts = true,
      ...props
    },
    ref
  ) => {
    // SSR guard
    const hasWindow = typeof window !== "undefined";

    // Persisted state
    const [sidebarOpen, setSidebarOpenState] = useState<boolean>(() => {
      if (!persistSidebarState || !hasWindow) return defaultSidebarOpen;
      try {
        const stored = window.localStorage.getItem("appshell-sidebar-open");
        return stored ? JSON.parse(stored) : defaultSidebarOpen;
      } catch {
        return defaultSidebarOpen;
      }
    });

    const [sidebarCollapsed, setSidebarCollapsedState] = useState<boolean>(() => {
      if (!persistSidebarState || !hasWindow) return defaultSidebarCollapsed;
      try {
        const stored = window.localStorage.getItem("appshell-sidebar-collapsed");
        return stored ? JSON.parse(stored) : defaultSidebarCollapsed;
      } catch {
        return defaultSidebarCollapsed;
      }
    });

    const [isMobile, setIsMobile] = useState(false);
    const [isTablet, setIsTablet] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Persist helpers
    const setSidebarOpen = useCallback(
      (open: boolean | ((prev: boolean) => boolean)) => {
        const newValue = typeof open === "function" ? open(sidebarOpen) : open;
        setSidebarOpenState(newValue);
        if (persistSidebarState && hasWindow) {
          try {
            window.localStorage.setItem(
              "appshell-sidebar-open",
              JSON.stringify(newValue)
            );
          } catch {}
        }
      },
      [sidebarOpen, persistSidebarState, hasWindow]
    );

    const setSidebarCollapsed = useCallback(
      (collapsed: boolean | ((prev: boolean) => boolean)) => {
        const newValue =
          typeof collapsed === "function" ? collapsed(sidebarCollapsed) : collapsed;
        setSidebarCollapsedState(newValue);
        if (persistSidebarState && hasWindow) {
          try {
            window.localStorage.setItem(
              "appshell-sidebar-collapsed",
              JSON.stringify(newValue)
            );
          } catch {}
        }
      },
      [sidebarCollapsed, persistSidebarState, hasWindow]
    );

    // Utilities
    const toggleSidebar = useCallback(() => {
      if (isMobile) {
        setSidebarOpen((prev) => !prev);
      } else {
        setSidebarCollapsed((prev) => !prev);
      }
    }, [isMobile, setSidebarOpen, setSidebarCollapsed]);

    const closeSidebar = useCallback(() => {
      if (isMobile) setSidebarOpen(false);
    }, [isMobile, setSidebarOpen]);

    const openSidebar = useCallback(() => {
      if (isMobile) setSidebarOpen(true);
      else setSidebarCollapsed(false);
    }, [isMobile, setSidebarOpen, setSidebarCollapsed]);

    // Responsive behavior
    useEffect(() => {
      if (!hasWindow) return;

      let timeoutId: ReturnType<typeof setTimeout>;

      const handleResize = () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          const width = window.innerWidth;
          const mobile = width < sidebarBreakpoint;
          const tablet = width >= sidebarBreakpoint && width < tabletBreakpoint;

          setIsMobile(mobile);
          setIsTablet(tablet);

          // Auto-close sidebar on mobile when switching from desktop
          if (mobile && sidebarOpen) {
            setSidebarOpen(false);
          }
        }, 100);
      };

      handleResize();
      window.addEventListener("resize", handleResize);
      return () => {
        clearTimeout(timeoutId);
        window.removeEventListener("resize", handleResize);
      };
    }, [
      hasWindow,
      sidebarBreakpoint,
      tabletBreakpoint,
      sidebarOpen,
      setSidebarOpen,
    ]);

    // Keyboard navigation
    useEffect(() => {
      if (!enableKeyboardShortcuts || !mounted || !hasWindow) return;

      const handleKeyDown = (event: KeyboardEvent) => {
        const target = event.target as HTMLElement | null;
        const isTyping =
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          target?.isContentEditable;

        if (isTyping) return;

        // Ctrl/Cmd + B => toggle sidebar
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
          event.preventDefault();
          toggleSidebar();
        }

        // Escape => close on mobile
        if (event.key === "Escape" && isMobile && sidebarOpen) {
          event.preventDefault();
          closeSidebar();
        }

        // Alt + S => focus sidebar
        if (event.altKey && event.key.toLowerCase() === "s" && sidebarOpen) {
          event.preventDefault();
          const nav = document.querySelector('[role="navigation"]') as
            | HTMLElement
            | undefined;
          nav?.focus();
        }

        // Alt + M => focus main
        if (event.altKey && event.key.toLowerCase() === "m") {
          event.preventDefault();
          const main = document.querySelector("main") as HTMLElement | undefined;
          main?.focus();
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [enableKeyboardShortcuts, mounted, isMobile, sidebarOpen, toggleSidebar, closeSidebar, hasWindow]);

    useEffect(() => {
      setMounted(true);
    }, []);

    const contextValue: AppShellContextType = {
      sidebarOpen,
      setSidebarOpen,
      sidebarCollapsed,
      setSidebarCollapsed,
      isMobile,
      isTablet,
      toggleSidebar,
      closeSidebar,
      openSidebar,
    };

    return (
      <AppShellContext.Provider value={contextValue}>
        <div
          ref={ref}
          className={cn(appShellVariants({ layout }), className)}
          {...props}
        >
          {/* Sidebar */}
          {sidebar && <AppShellSidebar>{sidebar}</AppShellSidebar>}

          {/* Main */}
          <div className="flex flex-1 min-w-0 flex-col">
            {header && <AppShellHeader>{header}</AppShellHeader>}

            <AppShellMain tabIndex={-1}>{children}</AppShellMain>

            {footer && <AppShellFooter>{footer}</AppShellFooter>}
          </div>

          {/* Mobile overlay */}
          {isMobile && sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black/50 lg:hidden"
              onClick={() => setSidebarOpen(false)}
              aria-hidden="true"
            />
          )}
        </div>
      </AppShellContext.Provider>
    );
  }
);

AppShell.displayName = "AppShell";

// -------------------- Sidebar --------------------

export const appShellSidebarVariants = cva(
  [
    "flex flex-col",
    "bg-[var(--color-neutral-100)] dark:bg-[var(--color-neutral-900)]",
    "border-r border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]",
    "transition-all [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
    "z-50",
    "focus:outline-none", // focusable when using a11y shortcuts
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

export interface AppShellSidebarProps
  extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const AppShellSidebar = React.forwardRef<
  HTMLDivElement,
  AppShellSidebarProps
>(({ className, children, ...props }, ref) => {
  const { sidebarOpen, sidebarCollapsed, isMobile } = useAppShell();

  const state = sidebarOpen
    ? sidebarCollapsed
      ? "collapsed"
      : "expanded"
    : "closed";
  const position = isMobile ? "fixed" : "relative";

  return (
    <aside
      ref={ref}
      role="navigation"
      tabIndex={-1}
      className={cn(
        // Base width when visible; ensure width is defined for expanded/collapsed
        "will-change-transform",
        appShellSidebarVariants({ state: state as any, position: position as any }),
        className
      )}
      aria-label="Main navigation"
      {...props}
    >
      {children}
    </aside>
  );
});

AppShellSidebar.displayName = "AppShellSidebar";

// -------------------- Header --------------------

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

export interface AppShellHeaderProps
  extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
}

export const AppShellHeader = React.forwardRef<HTMLElement, AppShellHeaderProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <header
        ref={ref}
        className={cn(appShellHeaderVariants(), className)}
        {...props}
      >
        {children}
      </header>
    );
  }
);

AppShellHeader.displayName = "AppShellHeader";

// -------------------- Main --------------------

export const appShellMainVariants = cva([
  "flex-1 min-h-0",
  "p-[var(--space-lg)]",
  "bg-[var(--color-neutral-50)] dark:bg-[var(--color-neutral-950)]",
  "transition-colors [transition-duration:var(--duration-normal)] [transition-timing-function:var(--ease-standard)]",
]);

export type AppShellMainVariants = VariantProps<typeof appShellMainVariants>;

export interface AppShellMainProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
}

export const AppShellMain = React.forwardRef<HTMLElement, AppShellMainProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <main
        ref={ref}
        className={cn(appShellMainVariants(), className)}
        {...props}
      >
        {children}
      </main>
    );
  }
);

AppShellMain.displayName = "AppShellMain";

// -------------------- Footer --------------------

export const appShellFooterVariants = cva([
  "flex items-center justify-between",
  "px-[var(--space-lg)] py-[var(--space-md)]",
  "bg-[var(--color-neutral-100)] dark:bg-[var(--color-neutral-900)]",
  "border-t border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]",
  "text-[var(--text-sm)] text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]",
]);

export interface AppShellFooterProps
  extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
}

export const AppShellFooter = React.forwardRef<HTMLElement, AppShellFooterProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <footer
        ref={ref}
        className={cn(appShellFooterVariants(), className)}
        {...props}
      >
        {children}
      </footer>
    );
  }
);

AppShellFooter.displayName = "AppShellFooter";
