/**
 * AppShell Component
 *
 * Main application shell with responsive sidebar, header, and main content areas.
 * Enhanced with improved accessibility, keyboard navigation, responsive behavior, and modern aesthetics.
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
import { ErrorBoundary } from "@/components/ui/error-boundary";
import {
  appShellVariants,
  appShellSidebarVariants,
  appShellHeaderVariants,
  appShellMainVariants,
  appShellFooterVariants,
} from "./app-shell-variants";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Menu, X } from "lucide-react";

type AppShellSidebarVariantProps = VariantProps<typeof appShellSidebarVariants>;

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

// eslint-disable-next-line react-refresh/only-export-components
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
  showMobileMenuToggle?: boolean;
  sidebarOverlay?: boolean;
  _sidebarWidth?: number;
  _collapsedSidebarWidth?: number;
  sidebarClassName?: string;
  headerClassName?: string;
  mainClassName?: string;
  footerClassName?: string;
}

// -------------------- AppShell --------------------

export const AppShell = React.forwardRef<HTMLDivElement, AppShellProps>(
  React.memo((
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
      showMobileMenuToggle = true,
      sidebarOverlay = true,
      _sidebarWidth = 256,
      _collapsedSidebarWidth = 64,
      sidebarClassName,
      headerClassName,
      mainClassName,
      footerClassName,
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

    const contextValue = React.useMemo(() => ({
      sidebarOpen,
      setSidebarOpen,
      sidebarCollapsed,
      setSidebarCollapsed,
      isMobile,
      isTablet,
      toggleSidebar,
      closeSidebar,
      openSidebar,
    }), [
      sidebarOpen,
      setSidebarOpen,
      sidebarCollapsed,
      setSidebarCollapsed,
      isMobile,
      isTablet,
      toggleSidebar,
      closeSidebar,
      openSidebar
    ]);

    // Memoize the skip link
    const skipLink = React.useMemo(
      () => (
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
        >
          Skip to main content
        </a>
      ),
      []
    );

    // Memoize the mobile overlay
    const mobileOverlay = React.useMemo(
      () => (
        isMobile && sidebarOpen && sidebarOverlay && (
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
            aria-label="Close sidebar"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setSidebarOpen(false);
              }
            }}
          />
        )
      ),
      [isMobile, sidebarOpen, sidebarOverlay, setSidebarOpen]
    );

    // Mobile menu toggle button
    const mobileMenuToggle = React.useMemo(
      () => (
        isMobile && showMobileMenuToggle && (
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 md:hidden"
            onClick={toggleSidebar}
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        )
      ),
      [isMobile, showMobileMenuToggle, sidebarOpen, toggleSidebar]
    );

    return (
      <AppShellContext.Provider value={contextValue}>
        <ErrorBoundary>
          <div
            ref={ref}
            className={cn(appShellVariants({ layout }), "bg-background/95 backdrop-blur-sm", className)}
            {...props}
          >
            {/* Skip to main content link for accessibility */}
            {skipLink}

            {/* Sidebar */}
            {sidebar && (
              <ErrorBoundary>
                <AppShellSidebar className={sidebarClassName}>{sidebar}</AppShellSidebar>
              </ErrorBoundary>
            )}

            {/* Main */}
            <div className="flex flex-1 min-w-0 flex-col">
              {header && (
                <ErrorBoundary>
                  <AppShellHeader className={headerClassName}>
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center">
                        {mobileMenuToggle}
                        {header}
                      </div>
                      {!isMobile && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={toggleSidebar}
                          className="h-8 w-8 hidden lg:flex"
                          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                          aria-expanded={!sidebarCollapsed}
                        >
                          {sidebarCollapsed ? (
                            <ChevronRight className="h-4 w-4" />
                          ) : (
                            <ChevronLeft className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                    </div>
                  </AppShellHeader>
                </ErrorBoundary>
              )}

              <ErrorBoundary>
                <AppShellMain
                  id="main-content"
                  tabIndex={-1}
                  aria-label="Main content"
                  role="main"
                  className={mainClassName}
                >
                  {children}
                </AppShellMain>
              </ErrorBoundary>

              {footer && (
                <ErrorBoundary>
                  <AppShellFooter className={footerClassName}>{footer}</AppShellFooter>
                </ErrorBoundary>
              )}
            </div>

            {/* Mobile overlay */}
            {mobileOverlay}
          </div>
        </ErrorBoundary>
      </AppShellContext.Provider>
    );
  })
);

AppShell.displayName = "AppShell";

export interface AppShellSidebarProps
  extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  width?: number;
  collapsedWidth?: number;
}

export const AppShellSidebar = React.forwardRef<
  HTMLDivElement,
  AppShellSidebarProps
>(({ className, children, width = 256, collapsedWidth = 64, ...props }, ref) => {
  const { sidebarOpen, sidebarCollapsed, isMobile } = useAppShell();

  const state: AppShellSidebarVariantProps["state"] = sidebarOpen
    ? sidebarCollapsed
      ? "collapsed"
      : "expanded"
    : "closed";
  const position: AppShellSidebarVariantProps["position"] = isMobile
    ? "fixed"
    : "relative";

  const sidebarStyle = React.useMemo(() => {
    if (isMobile) return {};
    
    if (sidebarCollapsed) {
      return { width: `${collapsedWidth}px` };
    }
    
    return { width: `${width}px` };
  }, [isMobile, sidebarCollapsed, width, collapsedWidth]);

  return (
        <aside
          ref={ref}
          role="navigation"
          tabIndex={-1}
          className={cn(
            // Base width when visible; ensure width is defined for expanded/collapsed
            "will-change-transform bg-card/90 backdrop-blur-sm shadow-sm",
            appShellSidebarVariants({ state, position }),
            className
          )}
          style={sidebarStyle}
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
        role="banner"
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
        role="contentinfo"
        {...props}
      >
        {children}
      </footer>
    );
  }
);

AppShellFooter.displayName = "AppShellFooter";
