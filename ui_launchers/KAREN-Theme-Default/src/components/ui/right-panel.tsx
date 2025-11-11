"use client";

import React from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { PanelHeader } from "./panel-header";
import { PanelContent } from "./panel-content";
import { useReducedMotion, useAnimationVariants } from "@/hooks/use-reduced-motion";
import { useResponsivePanel, usePanelBackdrop } from "@/hooks/use-responsive-panel";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Right panel view configuration
 */
export interface RightPanelView {
  id: string;
  title: string;
  description?: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

/**
 * Right panel props interface
 */
type MotionAsideProps = React.ComponentPropsWithoutRef<typeof motion.aside>;

export interface RightPanelProps
  extends Omit<MotionAsideProps, "onDrag" | "onDragStart" | "onDragEnd" | "draggable" | "onAnimationStart" | "onAnimationEnd" | "onAnimationIteration"> {
  /** Current active view ID */
  activeView?: string;
  /** Available views */
  views: RightPanelView[];
  /** Callback when view changes */
  onViewChange?: (viewId: string) => void;
  /** Callback when panel is closed */
  onClose?: () => void;
  /** Whether the panel is open */
  isOpen?: boolean;
  /** Panel width variant */
  width?: "sm" | "md" | "lg" | "xl" | "full";
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Whether to show navigation tabs */
  showNavigation?: boolean;
  /** Custom header content */
  headerContent?: React.ReactNode;
  /** Custom footer content */
  footerContent?: React.ReactNode;
  /** Whether to enable reduced motion (auto-detected if not provided) */
  reducedMotion?: boolean;
  /** Whether panel should be collapsible on mobile */
  collapsibleOnMobile?: boolean;
  /** Whether panel should overlay content on mobile */
  overlayOnMobile?: boolean;
  /** Touch gesture support for mobile */
  touchGestures?: boolean;
}

/**
 * Right panel header props
 */
export interface RightPanelHeaderProps extends React.HTMLAttributes<HTMLElement> {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  onClose?: () => void;
  showCloseButton?: boolean;
}

/**
 * Right panel content props
 */
export interface RightPanelContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Content padding variant */
  padding?: "none" | "sm" | "md" | "lg";
  /** Whether content should scroll */
  scrollable?: boolean;
}

/**
 * Right panel navigation props
 */
export interface RightPanelNavigationProps extends React.HTMLAttributes<HTMLElement> {
  views: RightPanelView[];
  activeView?: string;
  onViewChange?: (viewId: string) => void;
}

// ============================================================================
// ANIMATION VARIANTS
// ============================================================================

/**
 * Enhanced panel slide animation variants with spring physics
 */
const panelVariants: Variants = {
  closed: {
    x: "100%",
    opacity: 0,
    scale: 0.95,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
      mass: 0.8,
    },
  },
  open: {
    x: 0,
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
      mass: 0.8,
      staggerChildren: 0.1,
    },
  },
};

/**
 * Enhanced content transition variants with coordinated animations
 */
const contentVariants: Variants = {
  initial: {
    opacity: 0,
    x: 20,
    y: 10,
    scale: 0.98,
  },
  animate: {
    opacity: 1,
    x: 0,
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
      mass: 0.5,
    },
  },
  exit: {
    opacity: 0,
    x: -20,
    y: -10,
    scale: 0.98,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
      mass: 0.5,
      duration: 0.2,
    },
  },
};

/**
 * Navigation transition variants
 */
const navigationVariants: Variants = {
  initial: { opacity: 0, y: -10 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      delay: 0.1,
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
  exit: { 
    opacity: 0, 
    y: -10,
    transition: {
      duration: 0.15,
    },
  },
};

/**
 * Header transition variants
 */
const headerVariants: Variants = {
  initial: { opacity: 0, y: -20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
  exit: { 
    opacity: 0, 
    y: -20,
    transition: {
      duration: 0.15,
    },
  },
};

/**
 * Reduced motion variants for accessibility
 */
const reducedMotionVariants: Variants = {
  closed: { 
    opacity: 0,
    transition: { duration: 0.01 },
  },
  open: { 
    opacity: 1,
    transition: { duration: 0.01 },
  },
  initial: { 
    opacity: 0,
    transition: { duration: 0.01 },
  },
  animate: { 
    opacity: 1,
    transition: { duration: 0.01 },
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.01 },
  },
};

// ============================================================================
// STYLE MAPPINGS
// ============================================================================

/**
 * Panel width class mappings with responsive behavior
 */
const PANEL_WIDTH_CLASSES = {
  sm: "w-80 max-w-[90vw] min-w-[20rem] sm:max-w-[85vw] md:max-w-[80vw] lg:max-w-[75vw]",
  md: "w-96 max-w-[90vw] min-w-[24rem] sm:max-w-[85vw] md:max-w-[80vw] lg:max-w-[70vw]",
  lg: "w-[28rem] max-w-[90vw] min-w-[28rem] sm:max-w-[85vw] md:max-w-[75vw] lg:max-w-[65vw]",
  xl: "w-[32rem] max-w-[90vw] min-w-[32rem] sm:max-w-[85vw] md:max-w-[70vw] lg:max-w-[60vw]",
  full: "w-full min-w-full",
} as const;



// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Right Panel Header Component (using reusable PanelHeader)
 */
export const RightPanelHeader = React.forwardRef<HTMLElement, RightPanelHeaderProps>(
  function RightPanelHeader(props, ref) {
    return <PanelHeader ref={ref} {...props} />;
  }
);

/**
 * Right Panel Navigation Component
 */
export const RightPanelNavigation = React.forwardRef<HTMLElement, RightPanelNavigationProps>(
  function RightPanelNavigation(
    { views, activeView, onViewChange, className, ...props },
    ref
  ) {
    if (views.length <= 1) return null;

    return (
      <nav
        ref={ref}
        className={cn(
          "flex-shrink-0 border-b border-border/50",
          "bg-muted/30 backdrop-blur-sm",
          // Responsive padding using design tokens
          "px-3 py-2 sm:px-4 md:px-6",
          className
        )}
        {...props}
      >
        <div className="grid grid-cols-12 gap-2 sm:gap-4">
          <div className="col-span-12">
            {/* Horizontal scrollable navigation with responsive behavior */}
            <div className="flex overflow-x-auto scrollbar-hide">
              <div className={cn(
                "flex items-center min-w-full",
                // Responsive gap
                "gap-0.5 sm:gap-1",
                // Proper vertical alignment
                "py-1"
              )}>
                {views.map((view) => (
                  <Button
                    key={view.id}
                    variant={activeView === view.id ? "default" : "ghost"}
                    size="sm"
                    onClick={() => onViewChange?.(view.id)}
                    className={cn(
                      "whitespace-nowrap shrink-0",
                      // Responsive spacing and alignment
                      "h-8 px-2 sm:px-3",
                      "flex items-center justify-center",
                      // Touch-optimized sizing on mobile
                      "min-h-[44px] sm:min-h-[32px]", // 44px is iOS recommended touch target
                      // Proper focus and hover states
                      "focus-visible:ring-2 focus-visible:ring-[var(--component-button-default-ring)] focus-visible:ring-offset-[var(--component-button-default-ring-offset,var(--color-neutral-50))]",
                      "transition-all duration-200",
                      // Enhanced touch feedback
                      "active:scale-95 sm:active:scale-100"
                    )}
                  >
                    {view.icon && (
                      <span className={cn(
                        "flex items-center justify-center",
                        // Responsive icon spacing
                        "mr-1 sm:mr-2 h-4 w-4"
                      )}>
                        {view.icon}
                      </span>
                    )}
                    <span className={cn(
                      "font-medium",
                      // Responsive text size
                      "text-xs sm:text-sm",
                      // Hide text on very small screens if needed
                      "max-xs:sr-only sm:not-sr-only"
                    )}>
                      {view.title}
                    </span>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>
    );
  }
);

/**
 * Right Panel Content Component (using reusable PanelContent)
 */
export const RightPanelContent = React.forwardRef<HTMLDivElement, RightPanelContentProps>(
  function RightPanelContent(props, ref) {
    return <PanelContent ref={ref} {...props} />;
  }
);

/**
 * Main Right Panel Component
 */
const RightPanelBase = React.forwardRef<HTMLElement, RightPanelProps>(
  function RightPanel(
    {
      activeView,
      views,
      onViewChange,
      onClose,
      isOpen = true,
      width = "lg",
      showCloseButton = true,
      showNavigation = true,
      headerContent,
      footerContent,
      reducedMotion,
      collapsibleOnMobile = true,
      overlayOnMobile = true,
      touchGestures = true,
      className,
      ...props
    },
    ref
  ) {
    // Auto-detect reduced motion preference if not explicitly provided
    const systemReducedMotion = useReducedMotion();
    const shouldReduceMotion = reducedMotion ?? systemReducedMotion;

    // Responsive panel behavior
    const responsivePanel = useResponsivePanel({
      collapsibleOnMobile,
      overlayOnMobile,
      touchGestures,
      onGestureClose: onClose,
    });

    // Panel backdrop for mobile overlay
    const { showBackdrop, backdropProps } = usePanelBackdrop(isOpen, onClose);

    // Find the current active view
    const currentView = views.find((view) => view.id === activeView) || views[0];

    // Choose animation variants based on reduced motion preference
    const panelAnimationVariants = useAnimationVariants(panelVariants, reducedMotionVariants);
    const contentAnimationVariants = useAnimationVariants(contentVariants, reducedMotionVariants);
    const headerAnimationVariants = useAnimationVariants(headerVariants, reducedMotionVariants);
    const navigationAnimationVariants = useAnimationVariants(navigationVariants, reducedMotionVariants);

    const widthClass = PANEL_WIDTH_CLASSES[width];

    // Filter out props that conflict with Framer Motion
    const filteredProps = React.useMemo<Partial<MotionAsideProps>>(() => {
      const sanitizedProps: Partial<MotionAsideProps> = { ...props };

      delete sanitizedProps.onDrag;
      delete sanitizedProps.onDragEnd;
      delete sanitizedProps.onDragStart;
      delete sanitizedProps.draggable;
      delete sanitizedProps.onAnimationStart;
      delete sanitizedProps.onAnimationEnd;
      delete sanitizedProps.onAnimationIteration;

      return sanitizedProps;
    }, [props]);

    if (!isOpen) return null;

    return (
      <>
        {/* Mobile backdrop */}
        {showBackdrop && <div {...backdropProps} />}
        
        <motion.aside
          ref={ref}
          initial="closed"
          animate="open"
          exit="closed"
          variants={panelAnimationVariants}
          className={cn(
            // Fixed positioning with proper z-index and responsive behavior
            "fixed right-0 top-0 z-50",
            // Proper viewport height handling
            "panel-viewport-height",
            // Mobile-first responsive positioning
            responsivePanel.shouldOverlay && "sm:relative sm:right-auto sm:top-auto sm:z-auto sm:panel-viewport-height-desktop-auto",
            // Background and border with consistent design tokens
            "bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/80",
            "border-l border-border/50",
            "shadow-xl",
            // Enhanced shadow on mobile for overlay effect
            responsivePanel.shouldOverlay && "shadow-2xl sm:shadow-xl",
            // Layout structure with proper overflow handling
            "flex flex-col",
            "overflow-hidden", // Prevent panel from overflowing
            // Width with responsive behavior
            widthClass,
            // Responsive classes from hook
            responsivePanel.getResponsiveClasses(),
            // Responsive visibility
            responsivePanel.shouldCollapse && "max-sm:translate-x-full max-sm:data-[state=open]:translate-x-0",
            className
          )}
          style={{
            // Ensure proper content containment
            contain: "layout style paint",
            // Mobile touch optimization
            WebkitTouchCallout: "none",
            WebkitUserSelect: "none",
            touchAction: "pan-y",
          }}
          // Add data attributes for responsive behavior
          data-state={isOpen ? "open" : "closed"}
          data-mobile-overlay={responsivePanel.shouldOverlay}
          data-collapsible={responsivePanel.shouldCollapse}
          // Touch gesture props
          {...responsivePanel.getTouchProps()}
          {...filteredProps}
        >
        {/* Header with coordinated animation */}
        <motion.div
          variants={headerAnimationVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <RightPanelHeader
            title={currentView?.title}
            description={currentView?.description}
            onClose={onClose}
            showCloseButton={showCloseButton}
          >
            {headerContent}
          </RightPanelHeader>
        </motion.div>

        {/* Navigation with staggered animation */}
        {showNavigation && (
          <motion.div
            variants={navigationAnimationVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <RightPanelNavigation
              views={views}
              activeView={activeView}
              onViewChange={onViewChange}
            />
          </motion.div>
        )}

        {/* Content with smooth transitions and proper overflow handling */}
        <RightPanelContent 
          scrollable={true}
          padding="md"
          className="flex-1 min-h-0 overflow-hidden" // Ensure proper flex behavior and overflow
        >
          <AnimatePresence mode="wait" initial={false}>
            {currentView && (
              <motion.div
                key={currentView.id}
                initial="initial"
                animate="animate"
                exit="exit"
                variants={contentAnimationVariants}
                className={cn(
                  "h-full w-full",
                  // Proper content alignment and spacing
                  "flex flex-col",
                  // Ensure content doesn't overflow
                  "overflow-hidden"
                )}
                // Add layout animation for smooth resizing
                {...(!shouldReduceMotion && { 
                  layout: true,
                  layoutId: `panel-content-${currentView.id}` 
                })}
              >
                <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide">
                  {currentView.content}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </RightPanelContent>

        {/* Footer with coordinated animation and consistent spacing */}
        {footerContent && (
          <motion.footer
            variants={headerAnimationVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={cn(
              "flex-shrink-0 border-t border-border/50",
              "bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/80",
              // Consistent padding using design tokens
              "px-4 py-3 sm:px-6",
              // Proper alignment
              "flex items-center"
            )}
          >
            <div className="grid grid-cols-12 gap-4 w-full">
              <div className="col-span-12 flex items-center justify-between">
                {footerContent}
              </div>
            </div>
          </motion.footer>
        )}
      </motion.aside>
      </>
    );
  }
);

// ============================================================================
// COMPOUND COMPONENT EXPORTS
// ============================================================================

/**
 * Compound component pattern export
 */
type RightPanelComponent = React.ForwardRefExoticComponent<
  RightPanelProps & React.RefAttributes<HTMLElement>
> & {
  Header: typeof RightPanelHeader;
  Navigation: typeof RightPanelNavigation;
  Content: typeof RightPanelContent;
};

export const RightPanel = RightPanelBase as RightPanelComponent;

RightPanel.Header = RightPanelHeader;
RightPanel.Navigation = RightPanelNavigation;
RightPanel.Content = RightPanelContent;
