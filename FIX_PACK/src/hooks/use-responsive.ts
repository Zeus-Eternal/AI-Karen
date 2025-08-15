import { useState, useEffect, useCallback } from 'react';
import { useTelemetry } from './use-telemetry';

export interface BreakpointConfig {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
}

export interface ResponsiveState {
  width: number;
  height: number;
  breakpoint: keyof BreakpointConfig;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLandscape: boolean;
  isPortrait: boolean;
  isTouchDevice: boolean;
  isHighDPI: boolean;
  prefersReducedMotion: boolean;
  prefersReducedData: boolean;
  connectionType: string;
}

const DEFAULT_BREAKPOINTS: BreakpointConfig = {
  xs: 320,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
};

export const useResponsive = (customBreakpoints?: Partial<BreakpointConfig>) => {
  const { track } = useTelemetry();
  const breakpoints = { ...DEFAULT_BREAKPOINTS, ...customBreakpoints };
  
  const [state, setState] = useState<ResponsiveState>(() => {
    if (typeof window === 'undefined') {
      return {
        width: 1024,
        height: 768,
        breakpoint: 'lg' as keyof BreakpointConfig,
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        isLandscape: true,
        isPortrait: false,
        isTouchDevice: false,
        isHighDPI: false,
        prefersReducedMotion: false,
        prefersReducedData: false,
        connectionType: 'unknown'
      };
    }

    return getResponsiveState();
  });

  function getResponsiveState(): ResponsiveState {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Determine breakpoint
    let breakpoint: keyof BreakpointConfig = 'xs';
    if (width >= breakpoints['2xl']) breakpoint = '2xl';
    else if (width >= breakpoints.xl) breakpoint = 'xl';
    else if (width >= breakpoints.lg) breakpoint = 'lg';
    else if (width >= breakpoints.md) breakpoint = 'md';
    else if (width >= breakpoints.sm) breakpoint = 'sm';

    // Device type detection
    const isMobile = width < breakpoints.md;
    const isTablet = width >= breakpoints.md && width < breakpoints.lg;
    const isDesktop = width >= breakpoints.lg;
    
    // Orientation
    const isLandscape = width > height;
    const isPortrait = height > width;
    
    // Touch device detection
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // High DPI detection
    const isHighDPI = window.devicePixelRatio > 1;
    
    // Motion preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    // Data preferences
    const prefersReducedData = window.matchMedia('(prefers-reduced-data: reduce)').matches;
    
    // Connection type
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    const connectionType = connection?.effectiveType || 'unknown';

    return {
      width,
      height,
      breakpoint,
      isMobile,
      isTablet,
      isDesktop,
      isLandscape,
      isPortrait,
      isTouchDevice,
      isHighDPI,
      prefersReducedMotion,
      prefersReducedData,
      connectionType
    };
  }

  const updateState = useCallback(() => {
    const newState = getResponsiveState();
    setState(prevState => {
      // Track breakpoint changes
      if (prevState.breakpoint !== newState.breakpoint) {
        track('responsive_breakpoint_change', {
          from: prevState.breakpoint,
          to: newState.breakpoint,
          width: newState.width,
          height: newState.height
        });
      }
      
      // Track orientation changes
      if (prevState.isLandscape !== newState.isLandscape) {
        track('responsive_orientation_change', {
          orientation: newState.isLandscape ? 'landscape' : 'portrait',
          width: newState.width,
          height: newState.height
        });
      }
      
      return newState;
    });
  }, [track]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Debounce resize events
    let timeoutId: NodeJS.Timeout;
    const debouncedUpdate = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateState, 150);
    };

    window.addEventListener('resize', debouncedUpdate);
    window.addEventListener('orientationchange', debouncedUpdate);

    // Listen for media query changes
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const dataQuery = window.matchMedia('(prefers-reduced-data: reduce)');

    const handleMotionChange = () => updateState();
    const handleDataChange = () => updateState();

    motionQuery.addEventListener('change', handleMotionChange);
    dataQuery.addEventListener('change', handleDataChange);

    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', debouncedUpdate);
      window.removeEventListener('orientationchange', debouncedUpdate);
      motionQuery.removeEventListener('change', handleMotionChange);
      dataQuery.removeEventListener('change', handleDataChange);
    };
  }, [updateState]);

  // Utility functions
  const isBreakpoint = useCallback((bp: keyof BreakpointConfig) => {
    return state.breakpoint === bp;
  }, [state.breakpoint]);

  const isBreakpointUp = useCallback((bp: keyof BreakpointConfig) => {
    const bpOrder: (keyof BreakpointConfig)[] = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];
    const currentIndex = bpOrder.indexOf(state.breakpoint);
    const targetIndex = bpOrder.indexOf(bp);
    return currentIndex >= targetIndex;
  }, [state.breakpoint]);

  const isBreakpointDown = useCallback((bp: keyof BreakpointConfig) => {
    const bpOrder: (keyof BreakpointConfig)[] = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];
    const currentIndex = bpOrder.indexOf(state.breakpoint);
    const targetIndex = bpOrder.indexOf(bp);
    return currentIndex <= targetIndex;
  }, [state.breakpoint]);

  const getResponsiveValue = useCallback(<T>(values: Partial<Record<keyof BreakpointConfig, T>>): T | undefined => {
    const bpOrder: (keyof BreakpointConfig)[] = ['2xl', 'xl', 'lg', 'md', 'sm', 'xs'];
    const currentIndex = bpOrder.indexOf(state.breakpoint);
    
    // Find the first value that matches current breakpoint or smaller
    for (let i = currentIndex; i < bpOrder.length; i++) {
      const bp = bpOrder[i];
      if (values[bp] !== undefined) {
        return values[bp];
      }
    }
    
    return undefined;
  }, [state.breakpoint]);

  const getOptimalImageSize = useCallback(() => {
    const baseSize = getResponsiveValue({
      xs: 32,
      sm: 40,
      md: 48,
      lg: 56,
      xl: 64,
      '2xl': 72
    }) || 48;
    
    return state.isHighDPI ? baseSize * 2 : baseSize;
  }, [state.isHighDPI, getResponsiveValue]);

  const shouldReduceAnimations = useCallback(() => {
    return state.prefersReducedMotion || state.prefersReducedData || state.connectionType === 'slow-2g';
  }, [state.prefersReducedMotion, state.prefersReducedData, state.connectionType]);

  const getOptimalChunkSize = useCallback(() => {
    // Adjust chunk sizes based on connection and device
    if (state.prefersReducedData || state.connectionType === 'slow-2g') {
      return 10;
    } else if (state.connectionType === '2g') {
      return 25;
    } else if (state.connectionType === '3g') {
      return 50;
    } else if (state.isMobile) {
      return 75;
    } else {
      return 100;
    }
  }, [state.prefersReducedData, state.connectionType, state.isMobile]);

  const getTouchTargetSize = useCallback(() => {
    // Ensure touch targets meet accessibility guidelines
    const minSize = state.isTouchDevice ? 44 : 32;
    const comfortableSize = state.isTouchDevice ? 48 : 36;
    
    return getResponsiveValue({
      xs: minSize,
      sm: minSize,
      md: comfortableSize,
      lg: comfortableSize,
      xl: comfortableSize,
      '2xl': comfortableSize
    }) || minSize;
  }, [state.isTouchDevice, getResponsiveValue]);

  const getResponsiveClasses = useCallback((baseClasses: string = '') => {
    const classes = [baseClasses];
    
    // Add breakpoint classes
    classes.push(`bp-${state.breakpoint}`);
    
    // Add device type classes
    if (state.isMobile) classes.push('mobile');
    if (state.isTablet) classes.push('tablet');
    if (state.isDesktop) classes.push('desktop');
    
    // Add orientation classes
    if (state.isLandscape) classes.push('landscape');
    if (state.isPortrait) classes.push('portrait');
    
    // Add capability classes
    if (state.isTouchDevice) classes.push('touch');
    if (state.isHighDPI) classes.push('high-dpi');
    
    // Add preference classes
    if (state.prefersReducedMotion) classes.push('reduce-motion');
    if (state.prefersReducedData) classes.push('reduce-data');
    
    // Add connection classes
    classes.push(`connection-${state.connectionType}`);
    
    return classes.filter(Boolean).join(' ');
  }, [state]);

  return {
    // State
    ...state,
    breakpoints,
    
    // Utilities
    isBreakpoint,
    isBreakpointUp,
    isBreakpointDown,
    getResponsiveValue,
    getOptimalImageSize,
    shouldReduceAnimations,
    getOptimalChunkSize,
    getTouchTargetSize,
    getResponsiveClasses
  };
};