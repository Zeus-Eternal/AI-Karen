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
import { type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import {
  appShellVariants,
  appShellSidebarVariants,
  appShellHeaderVariants,
  appShellMainVariants,
  appShellFooterVariants,
} from "./app-shell-variants";

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
          } catch (error) {
            if (process.env.NODE_ENV !== "production") {
              console.warn("Failed to persist sidebar open state", error);
            }
          }
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
          } catch (error) {
            if (process.env.NODE_ENV !== "production") {
              console.warn("Failed to persist sidebar collapsed state", error);
            }
          }
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
      if (!enableKeyboardShortcuts || !hasWindow) return;

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
    }, [enableKeyboardShortcuts, isMobile, sidebarOpen, toggleSidebar, closeSidebar, hasWindow]);

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
        appShellSidebarVariants({ state: state as unknown, position: position as unknown }),
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
