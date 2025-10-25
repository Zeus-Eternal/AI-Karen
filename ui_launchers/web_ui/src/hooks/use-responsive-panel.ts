/**
 * Responsive Panel Hook
 * 
 * Custom hook for managing responsive panel behavior including mobile detection,
 * touch gesture support, and collapsible behavior.
 * 
 * Based on requirements: 2.4, 8.1, 8.3
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useMediaQuery } from './use-media-query';

export interface ResponsivePanelOptions {
  /** Breakpoint for mobile behavior (default: 768px) */
  mobileBreakpoint?: number;
  /** Whether panel should be collapsible on mobile */
  collapsibleOnMobile?: boolean;
  /** Whether panel should overlay content on mobile */
  overlayOnMobile?: boolean;
  /** Enable touch gesture support */
  touchGestures?: boolean;
  /** Swipe threshold for closing panel (default: 100px) */
  swipeThreshold?: number;
  /** Callback when panel is closed via gesture */
  onGestureClose?: () => void;
}

export interface ResponsivePanelState {
  /** Whether the current viewport is mobile */
  isMobile: boolean;
  /** Whether the current viewport is tablet */
  isTablet: boolean;
  /** Whether the current viewport is desktop */
  isDesktop: boolean;
  /** Current viewport width */
  viewportWidth: number;
  /** Current viewport height */
  viewportHeight: number;
  /** Whether the device supports touch */
  supportsTouch: boolean;
  /** Current device orientation */
  orientation: 'portrait' | 'landscape';
  /** Whether panel should be in overlay mode */
  shouldOverlay: boolean;
  /** Whether panel should be collapsible */
  shouldCollapse: boolean;
}

export interface ResponsivePanelActions {
  /** Handle touch start event */
  handleTouchStart: (event: TouchEvent) => void;
  /** Handle touch move event */
  handleTouchMove: (event: TouchEvent) => void;
  /** Handle touch end event */
  handleTouchEnd: (event: TouchEvent) => void;
  /** Handle keyboard navigation */
  handleKeyDown: (event: KeyboardEvent) => void;
  /** Get responsive classes for panel */
  getResponsiveClasses: () => string;
  /** Get touch gesture props */
  getTouchProps: () => Record<string, any>;
}

export interface UseResponsivePanelReturn extends ResponsivePanelState, ResponsivePanelActions {}

/**
 * Hook for managing responsive panel behavior
 */
export function useResponsivePanel(options: ResponsivePanelOptions = {}): UseResponsivePanelReturn {
  const {
    mobileBreakpoint = 768,
    collapsibleOnMobile = true,
    overlayOnMobile = true,
    touchGestures = true,
    swipeThreshold = 100,
    onGestureClose,
  } = options;

  // Media queries for responsive behavior
  const isMobile = useMediaQuery(`(max-width: ${mobileBreakpoint - 1}px)`);
  const isTablet = useMediaQuery(`(min-width: ${mobileBreakpoint}px) and (max-width: 1023px)`);
  const isDesktop = useMediaQuery(`(min-width: 1024px)`);

  // Viewport state
  const [viewportWidth, setViewportWidth] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(0);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [supportsTouch, setSupportsTouch] = useState(false);

  // Touch gesture state
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const touchMoveRef = useRef<{ x: number; y: number } | null>(null);

  // Update viewport dimensions
  const updateViewport = useCallback(() => {
    setViewportWidth(window.innerWidth);
    setViewportHeight(window.innerHeight);
    setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait');
  }, []);

  // Detect touch support
  const detectTouchSupport = useCallback(() => {
    setSupportsTouch(
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      // @ts-ignore
      navigator.msMaxTouchPoints > 0
    );
  }, []);

  // Initialize viewport and touch detection
  useEffect(() => {
    updateViewport();
    detectTouchSupport();

    window.addEventListener('resize', updateViewport);
    window.addEventListener('orientationchange', updateViewport);

    return () => {
      window.removeEventListener('resize', updateViewport);
      window.removeEventListener('orientationchange', updateViewport);
    };
  }, [updateViewport, detectTouchSupport]);

  // Touch gesture handlers
  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (!touchGestures || !supportsTouch) return;

    const touch = event.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
  }, [touchGestures, supportsTouch]);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!touchGestures || !supportsTouch || !touchStartRef.current) return;

    const touch = event.touches[0];
    touchMoveRef.current = {
      x: touch.clientX,
      y: touch.clientY,
    };

    // Prevent default scrolling if swiping horizontally
    const deltaX = Math.abs(touch.clientX - touchStartRef.current.x);
    const deltaY = Math.abs(touch.clientY - touchStartRef.current.y);

    if (deltaX > deltaY && deltaX > 10) {
      event.preventDefault();
    }
  }, [touchGestures, supportsTouch]);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (!touchGestures || !supportsTouch || !touchStartRef.current || !touchMoveRef.current) {
      touchStartRef.current = null;
      touchMoveRef.current = null;
      return;
    }

    const deltaX = touchMoveRef.current.x - touchStartRef.current.x;
    const deltaY = Math.abs(touchMoveRef.current.y - touchStartRef.current.y);
    const deltaTime = Date.now() - touchStartRef.current.time;

    // Check for swipe right gesture (close panel)
    if (
      deltaX > swipeThreshold &&
      deltaY < 100 && // Vertical tolerance
      deltaTime < 500 // Time limit for swipe
    ) {
      onGestureClose?.();
    }

    touchStartRef.current = null;
    touchMoveRef.current = null;
  }, [touchGestures, supportsTouch, swipeThreshold, onGestureClose]);

  // Keyboard navigation handler
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      onGestureClose?.();
    }
  }, [onGestureClose]);

  // Get responsive classes
  const getResponsiveClasses = useCallback(() => {
    const classes = ['panel-responsive'];

    if (isMobile) {
      classes.push('panel-mobile');
      if (collapsibleOnMobile) classes.push('panel-collapsible');
      if (overlayOnMobile) classes.push('panel-overlay');
    }

    if (isTablet) {
      classes.push('panel-tablet');
    }

    if (isDesktop) {
      classes.push('panel-desktop');
    }

    if (supportsTouch) {
      classes.push('panel-touch-enabled');
      if (touchGestures) classes.push('panel-touch-gestures');
    }

    if (orientation === 'landscape' && viewportHeight < 600) {
      classes.push('panel-landscape-compact');
    }

    return classes.join(' ');
  }, [
    isMobile,
    isTablet,
    isDesktop,
    supportsTouch,
    touchGestures,
    collapsibleOnMobile,
    overlayOnMobile,
    orientation,
    viewportHeight,
  ]);

  // Get touch gesture props
  const getTouchProps = useCallback(() => {
    if (!touchGestures || !supportsTouch) return {};

    return {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
      style: {
        touchAction: 'pan-y',
        WebkitTouchCallout: 'none',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      },
    };
  }, [touchGestures, supportsTouch, handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    // State
    isMobile,
    isTablet,
    isDesktop,
    viewportWidth,
    viewportHeight,
    supportsTouch,
    orientation,
    shouldOverlay: isMobile && overlayOnMobile,
    shouldCollapse: isMobile && collapsibleOnMobile,

    // Actions
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleKeyDown,
    getResponsiveClasses,
    getTouchProps,
  };
}

/**
 * Hook for managing panel backdrop behavior
 */
export function usePanelBackdrop(isOpen: boolean, onClose?: () => void) {
  const { isMobile, shouldOverlay } = useResponsivePanel();

  useEffect(() => {
    if (!isMobile || !shouldOverlay || !isOpen) return;

    const handleBackdropClick = (event: MouseEvent) => {
      const target = event.target as Element;
      if (target.classList.contains('panel-backdrop')) {
        onClose?.();
      }
    };

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose?.();
      }
    };

    document.addEventListener('click', handleBackdropClick);
    document.addEventListener('keydown', handleEscapeKey);

    return () => {
      document.removeEventListener('click', handleBackdropClick);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isMobile, shouldOverlay, isOpen, onClose]);

  return {
    showBackdrop: isMobile && shouldOverlay && isOpen,
    backdropProps: {
      className: 'panel-backdrop',
      'data-state': isOpen ? 'open' : 'closed',
      'aria-hidden': true,
    },
  };
}

/**
 * Hook for optimizing panel performance on mobile
 */
export function usePanelPerformance() {
  const { isMobile, supportsTouch } = useResponsivePanel();

  const getPerformanceProps = useCallback(() => {
    const props: Record<string, any> = {};

    if (isMobile) {
      // Optimize for mobile performance
      props.style = {
        ...props.style,
        contain: 'layout style paint',
        willChange: 'transform',
        transform: 'translateZ(0)',
      };
    }

    if (supportsTouch) {
      // Optimize touch interactions
      props.style = {
        ...props.style,
        touchAction: 'pan-y',
        WebkitTouchCallout: 'none',
      };
    }

    return props;
  }, [isMobile, supportsTouch]);

  return {
    getPerformanceProps,
  };
}