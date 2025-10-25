import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useReducedMotion, useAnimationDuration, useAnimationVariants } from '../use-reduced-motion';

// Mock matchMedia
const mockMatchMedia = vi.fn();

describe('useReducedMotion', () => {
  beforeEach(() => {
    // Reset the mock before each test
    mockMatchMedia.mockReset();
    
    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: mockMatchMedia,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns false when prefers-reduced-motion is not set', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result } = renderHook(() => useReducedMotion());
    
    expect(result.current).toBe(false);
    expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
  });

  it('returns true when prefers-reduced-motion is set', () => {
    const mockMediaQuery = {
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result } = renderHook(() => useReducedMotion());
    
    expect(result.current).toBe(true);
  });

  it('adds and removes event listener for media query changes', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { unmount } = renderHook(() => useReducedMotion());
    
    expect(mockMediaQuery.addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
    
    unmount();
    
    expect(mockMediaQuery.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('updates when media query changes', async () => {
    let changeHandler: (event: MediaQueryListEvent) => void;
    
    const mockMediaQuery = {
      matches: false,
      addEventListener: vi.fn((event, handler) => {
        changeHandler = handler;
      }),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result, rerender } = renderHook(() => useReducedMotion());
    
    expect(result.current).toBe(false);
    
    // Simulate media query change
    changeHandler({ matches: true } as MediaQueryListEvent);
    
    // Trigger a re-render to get the updated value
    rerender();
    
    expect(result.current).toBe(true);
  });
});

describe('useAnimationDuration', () => {
  beforeEach(() => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
  });

  it('returns normal duration when reduced motion is false', () => {
    const { result } = renderHook(() => useAnimationDuration(0.3, 0.01));
    
    expect(result.current).toBe(0.3);
  });

  it('returns reduced duration when reduced motion is true', () => {
    const mockMediaQuery = {
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result } = renderHook(() => useAnimationDuration(0.3, 0.01));
    
    expect(result.current).toBe(0.01);
  });

  it('uses default reduced duration when not provided', () => {
    const mockMediaQuery = {
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result } = renderHook(() => useAnimationDuration(0.3));
    
    expect(result.current).toBe(0.01);
  });
});

describe('useAnimationVariants', () => {
  const normalVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
  };
  
  const reducedVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
  };

  beforeEach(() => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
  });

  it('returns normal variants when reduced motion is false', () => {
    const { result } = renderHook(() => 
      useAnimationVariants(normalVariants, reducedVariants)
    );
    
    expect(result.current).toBe(normalVariants);
  });

  it('returns reduced variants when reduced motion is true', () => {
    const mockMediaQuery = {
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    
    mockMatchMedia.mockReturnValue(mockMediaQuery);
    
    const { result } = renderHook(() => 
      useAnimationVariants(normalVariants, reducedVariants)
    );
    
    expect(result.current).toBe(reducedVariants);
  });
});