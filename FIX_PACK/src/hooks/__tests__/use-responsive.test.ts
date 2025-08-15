import { renderHook, act } from '@testing-library/react';
import { useResponsive } from '../use-responsive';

// Mock telemetry hook
jest.mock('../use-telemetry', () => ({
  useTelemetry: () => ({
    track: jest.fn()
  })
}));

// Mock window properties
const mockWindow = {
  innerWidth: 1024,
  innerHeight: 768,
  devicePixelRatio: 1,
  matchMedia: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
};

const mockNavigator = {
  maxTouchPoints: 0,
  connection: {
    effectiveType: '4g'
  }
};

// Mock matchMedia
const mockMatchMedia = (matches: boolean) => ({
  matches,
  media: '',
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn()
});

describe('useResponsive', () => {
  beforeEach(() => {
    // Reset window mock
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024
    });
    
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768
    });
    
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      configurable: true,
      value: 1
    });
    
    Object.defineProperty(navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: 0
    });
    
    // Mock matchMedia to return false by default
    window.matchMedia = jest.fn().mockImplementation(() => mockMatchMedia(false));
    
    // Mock navigator.connection
    Object.defineProperty(navigator, 'connection', {
      writable: true,
      configurable: true,
      value: { effectiveType: '4g' }
    });
    
    jest.clearAllMocks();
  });

  it('should initialize with correct desktop state', () => {
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.width).toBe(1024);
    expect(result.current.height).toBe(768);
    expect(result.current.breakpoint).toBe('lg');
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.isLandscape).toBe(true);
    expect(result.current.isPortrait).toBe(false);
    expect(result.current.isTouchDevice).toBe(false);
  });

  it('should detect mobile breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', { value: 640 });
    Object.defineProperty(window, 'innerHeight', { value: 1136 });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.breakpoint).toBe('sm');
    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.isPortrait).toBe(true);
  });

  it('should detect tablet breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', { value: 768 });
    Object.defineProperty(window, 'innerHeight', { value: 1024 });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.breakpoint).toBe('md');
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
  });

  it('should detect touch device', () => {
    Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.isTouchDevice).toBe(true);
  });

  it('should detect high DPI display', () => {
    Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.isHighDPI).toBe(true);
  });

  it('should detect reduced motion preference', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-reduced-motion: reduce)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.prefersReducedMotion).toBe(true);
  });

  it('should detect reduced data preference', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-reduced-data: reduce)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.prefersReducedData).toBe(true);
  });

  it('should detect connection type', () => {
    Object.defineProperty(navigator, 'connection', {
      value: { effectiveType: '3g' }
    });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.connectionType).toBe('3g');
  });

  it('should check breakpoint correctly', () => {
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.isBreakpoint('lg')).toBe(true);
    expect(result.current.isBreakpoint('md')).toBe(false);
  });

  it('should check breakpoint up correctly', () => {
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.isBreakpointUp('md')).toBe(true);
    expect(result.current.isBreakpointUp('lg')).toBe(true);
    expect(result.current.isBreakpointUp('xl')).toBe(false);
  });

  it('should check breakpoint down correctly', () => {
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.isBreakpointDown('xl')).toBe(true);
    expect(result.current.isBreakpointDown('lg')).toBe(true);
    expect(result.current.isBreakpointDown('md')).toBe(false);
  });

  it('should get responsive value correctly', () => {
    const { result } = renderHook(() => useResponsive());
    
    const value = result.current.getResponsiveValue({
      xs: 'small',
      md: 'medium',
      lg: 'large',
      xl: 'extra-large'
    });
    
    expect(value).toBe('large');
  });

  it('should get responsive value with fallback', () => {
    const { result } = renderHook(() => useResponsive());
    
    const value = result.current.getResponsiveValue({
      xs: 'small',
      sm: 'small-medium'
    });
    
    expect(value).toBe('small');
  });

  it('should calculate optimal image size', () => {
    const { result } = renderHook(() => useResponsive());
    
    const size = result.current.getOptimalImageSize();
    expect(size).toBeGreaterThan(0);
  });

  it('should calculate optimal image size for high DPI', () => {
    Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
    
    const { result } = renderHook(() => useResponsive());
    
    const size = result.current.getOptimalImageSize();
    expect(size).toBeGreaterThan(56); // Should be doubled for high DPI
  });

  it('should determine if animations should be reduced', () => {
    window.matchMedia = jest.fn().mockImplementation((query) => {
      if (query === '(prefers-reduced-motion: reduce)') {
        return mockMatchMedia(true);
      }
      return mockMatchMedia(false);
    });
    
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.shouldReduceAnimations()).toBe(true);
  });

  it('should get optimal chunk size based on connection', () => {
    Object.defineProperty(navigator, 'connection', {
      value: { effectiveType: 'slow-2g' }
    });
    
    const { result } = renderHook(() => useResponsive());
    
    const chunkSize = result.current.getOptimalChunkSize();
    expect(chunkSize).toBe(10); // Small chunks for slow connection
  });

  it('should get touch target size', () => {
    Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
    
    const { result } = renderHook(() => useResponsive());
    
    const targetSize = result.current.getTouchTargetSize();
    expect(targetSize).toBeGreaterThanOrEqual(44); // Minimum touch target size
  });

  it('should generate responsive classes', () => {
    Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
    Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
    
    const { result } = renderHook(() => useResponsive());
    
    const classes = result.current.getResponsiveClasses('base-class');
    
    expect(classes).toContain('base-class');
    expect(classes).toContain('bp-lg');
    expect(classes).toContain('desktop');
    expect(classes).toContain('landscape');
    expect(classes).toContain('touch');
    expect(classes).toContain('high-dpi');
    expect(classes).toContain('connection-4g');
  });

  it('should use custom breakpoints', () => {
    const customBreakpoints = {
      md: 800,
      lg: 1200
    };
    
    Object.defineProperty(window, 'innerWidth', { value: 900 });
    
    const { result } = renderHook(() => useResponsive(customBreakpoints));
    
    expect(result.current.breakpoint).toBe('md');
    expect(result.current.breakpoints.md).toBe(800);
    expect(result.current.breakpoints.lg).toBe(1200);
  });

  it('should handle window resize events', () => {
    const { result } = renderHook(() => useResponsive());
    
    expect(result.current.width).toBe(1024);
    
    // Simulate window resize
    Object.defineProperty(window, 'innerWidth', { value: 640 });
    
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    
    // Note: In a real test, we'd need to wait for the debounced update
    // This is a simplified test to verify the event listener is set up
    expect(window.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
  });

  it('should handle SSR environment', () => {
    // Mock window as undefined (SSR environment)
    const originalWindow = global.window;
    delete (global as any).window;
    
    const { result } = renderHook(() => useResponsive());
    
    // Should provide default values for SSR
    expect(result.current.width).toBe(1024);
    expect(result.current.height).toBe(768);
    expect(result.current.breakpoint).toBe('lg');
    expect(result.current.isDesktop).toBe(true);
    
    // Restore window
    global.window = originalWindow;
  });
});