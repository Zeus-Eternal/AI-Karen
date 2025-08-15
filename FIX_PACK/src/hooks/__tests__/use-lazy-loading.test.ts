import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useLazyComponent,
  useBatchLazyLoading,
  useIntersectionLazyLoading,
  useLoadingPriority
} from '../use-lazy-loading';

// Mock component
const MockComponent = () => null;

// Mock import function
const createMockImport = (delay = 0, shouldFail = false) => {
  return vi.fn(() => 
    new Promise((resolve, reject) => {
      setTimeout(() => {
        if (shouldFail) {
          reject(new Error('Import failed'));
        } else {
          resolve({ default: MockComponent });
        }
      }, delay);
    })
  );
};

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
});

beforeEach(() => {
  vi.clearAllMocks();
  global.IntersectionObserver = mockIntersectionObserver;
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useLazyComponent', () => {
  it('should initialize with correct default state', () => {
    const mockImport = createMockImport();
    const { result } = renderHook(() => useLazyComponent(mockImport));

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isLoaded).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.component).toBe(null);
  });

  it('should preload component when preload is true', async () => {
    const mockImport = createMockImport(100);
    renderHook(() => useLazyComponent(mockImport, true));

    expect(mockImport).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(mockImport).toHaveBeenCalledTimes(1);
    });
  });

  it('should load component manually', async () => {
    const mockImport = createMockImport(100);
    const { result } = renderHook(() => useLazyComponent(mockImport));

    expect(result.current.isLoading).toBe(false);

    act(() => {
      result.current.loadComponent();
    });

    expect(result.current.isLoading).toBe(true);

    act(() => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.component).toBe(MockComponent);
    });
  });

  it('should handle loading errors', async () => {
    const mockImport = createMockImport(100, true);
    const { result } = renderHook(() => useLazyComponent(mockImport));

    act(() => {
      result.current.loadComponent().catch(() => {});
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeInstanceOf(Error);
      expect(result.current.error?.message).toBe('Import failed');
    });
  });

  it('should return cached component on subsequent loads', async () => {
    const mockImport = createMockImport(100);
    const { result } = renderHook(() => useLazyComponent(mockImport));

    // First load
    act(() => {
      result.current.loadComponent();
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    // Second load should return cached component
    const component = await result.current.loadComponent();
    expect(component).toBe(MockComponent);
    expect(mockImport).toHaveBeenCalledTimes(1); // Should not call import again
  });
});

describe('useBatchLazyLoading', () => {
  it('should initialize with correct state for multiple components', () => {
    const mockImports = [createMockImport(), createMockImport(), createMockImport()];
    const { result } = renderHook(() => useBatchLazyLoading(mockImports));

    expect(result.current.loadingStates).toHaveLength(3);
    expect(result.current.components).toHaveLength(3);
    expect(result.current.loadingStates.every(state => !state.isLoading && !state.isLoaded)).toBe(true);
  });

  it('should load specific component by index', async () => {
    const mockImports = [createMockImport(100), createMockImport(100), createMockImport(100)];
    const { result } = renderHook(() => useBatchLazyLoading(mockImports));

    act(() => {
      result.current.loadComponent(1);
    });

    expect(result.current.loadingStates[1].isLoading).toBe(true);
    expect(result.current.loadingStates[0].isLoading).toBe(false);
    expect(result.current.loadingStates[2].isLoading).toBe(false);

    act(() => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(result.current.loadingStates[1].isLoaded).toBe(true);
      expect(result.current.components[1]).toBe(MockComponent);
    });
  });

  it('should preload all components when preloadAll is true', async () => {
    const mockImports = [createMockImport(100), createMockImport(100)];
    renderHook(() => useBatchLazyLoading(mockImports, true));

    expect(mockImports[0]).toHaveBeenCalledTimes(1);
    expect(mockImports[1]).toHaveBeenCalledTimes(1);
  });

  it('should handle invalid component index', async () => {
    const mockImports = [createMockImport()];
    const { result } = renderHook(() => useBatchLazyLoading(mockImports));

    await expect(result.current.loadComponent(-1)).rejects.toThrow('Invalid component index');
    await expect(result.current.loadComponent(1)).rejects.toThrow('Invalid component index');
  });
});

describe('useIntersectionLazyLoading', () => {
  it('should set up intersection observer', () => {
    const mockImport = createMockImport();
    const { result } = renderHook(() => useIntersectionLazyLoading(mockImport));

    // Mock element
    const mockElement = document.createElement('div');
    result.current.ref(mockElement);

    expect(mockIntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        rootMargin: '50px',
        threshold: 0.1,
      })
    );
  });

  it('should load component when element becomes visible', async () => {
    const mockImport = createMockImport(100);
    let intersectionCallback: (entries: any[]) => void;

    mockIntersectionObserver.mockImplementation((callback) => {
      intersectionCallback = callback;
      return {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };
    });

    const { result } = renderHook(() => useIntersectionLazyLoading(mockImport));

    // Mock element becoming visible
    act(() => {
      intersectionCallback([{ isIntersecting: true }]);
    });

    expect(result.current.isVisible).toBe(true);
    expect(mockImport).toHaveBeenCalledTimes(1);
  });
});

describe('useLoadingPriority', () => {
  it('should process high priority queue first', async () => {
    const { result } = renderHook(() => useLoadingPriority());
    
    const executionOrder: string[] = [];
    
    const highPriorityTask = vi.fn(() => {
      executionOrder.push('high');
      return Promise.resolve();
    });
    
    const lowPriorityTask = vi.fn(() => {
      executionOrder.push('low');
      return Promise.resolve();
    });

    act(() => {
      result.current.addLowPriority(lowPriorityTask);
      result.current.addHighPriority(highPriorityTask);
    });

    await waitFor(() => {
      expect(result.current.isProcessing).toBe(false);
    });

    expect(executionOrder).toEqual(['high', 'low']);
  });

  it('should track queue sizes', () => {
    const { result } = renderHook(() => useLoadingPriority());

    act(() => {
      result.current.addHighPriority(() => Promise.resolve());
      result.current.addHighPriority(() => Promise.resolve());
      result.current.addLowPriority(() => Promise.resolve());
    });

    expect(result.current.queueSizes.high).toBe(2);
    expect(result.current.queueSizes.low).toBe(1);
  });

  it('should handle task failures gracefully', async () => {
    const { result } = renderHook(() => useLoadingPriority());
    
    const failingTask = vi.fn(() => Promise.reject(new Error('Task failed')));
    const successTask = vi.fn(() => Promise.resolve());

    act(() => {
      result.current.addHighPriority(failingTask);
      result.current.addHighPriority(successTask);
    });

    await waitFor(() => {
      expect(result.current.isProcessing).toBe(false);
    });

    expect(failingTask).toHaveBeenCalled();
    expect(successTask).toHaveBeenCalled();
  });
});