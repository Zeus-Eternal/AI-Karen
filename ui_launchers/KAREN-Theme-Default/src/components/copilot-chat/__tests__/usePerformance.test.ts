import { renderHook, act } from '@testing-library/react';
import { 
  usePerformance, 
  useDebounce, 
  useThrottle, 
  useVirtualScroll, 
  useMemoize, 
  useRenderTime, 
  useShouldUpdate, 
  useApiCall 
} from '../hooks/usePerformance';

// Mock the performance module
jest.mock('../utils/performance', () => ({
  PerformanceMonitor: {
    startMeasure: jest.fn(() => jest.fn())
  }
}));

describe('Performance Hooks', () => {
  describe('usePerformance', () => {
    it('should track component performance', () => {
      const { result } = renderHook(() => usePerformance('TestComponent'));
      
      expect(result.current.renderCount).toBeDefined();
      expect(result.current.mountTime).toBeDefined();
    });
  });
  
  describe('useDebounce', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });
    
    afterEach(() => {
      jest.useRealTimers();
    });
    
    it('should debounce value changes', () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        { initialProps: { value: 'initial', delay: 100 } }
      );
      
      expect(result.current).toBe('initial');
      
      // Update value
      rerender({ value: 'updated', delay: 100 });
      
      // Value should not change immediately
      expect(result.current).toBe('initial');
      
      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(100);
      });
      
      // Value should change after delay
      expect(result.current).toBe('updated');
    });
  });
  
  describe('useThrottle', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });
    
    afterEach(() => {
      jest.useRealTimers();
    });
    
    it('should throttle function calls', () => {
      const mockFn = jest.fn();
      const { result } = renderHook(() => useThrottle(mockFn, 100));
      
      // Call the throttled function multiple times
      act(() => {
        result.current();
        result.current();
        result.current();
      });
      
      // Function should be called immediately
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(100);
      });
      
      // Call again
      act(() => {
        result.current();
      });
      
      // Function should be called again
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('useVirtualScroll', () => {
    const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }));
    
    it('should calculate visible items', () => {
      const { result } = renderHook(() => 
        useVirtualScroll(items, 50, 400)
      );
      
      expect(result.current.visibleItems).toBeDefined();
      expect(result.current.totalHeight).toBe(5000); // 100 items * 50px
      expect(result.current.getItemOffset).toBeDefined();
      expect(typeof result.current.getItemOffset).toBe('function');
    });
    
    it('should update visible items on scroll', () => {
      const { result } = renderHook(() => 
        useVirtualScroll(items, 50, 400)
      );
      
      const initialVisibleItems = result.current.visibleItems;
      
      // Simulate scroll
      const scrollEvent = {
        currentTarget: {
          scrollTop: 250
        }
      } as React.UIEvent<HTMLDivElement>;
      
      act(() => {
        result.current.handleScroll(scrollEvent);
      });
      
      const scrolledVisibleItems = result.current.visibleItems;
      
      // Visible items should change after scroll
      expect(scrolledVisibleItems).not.toEqual(initialVisibleItems);
    });
  });
  
  describe('useMemoize', () => {
    it('should memoize function results', () => {
      const mockFn: jest.MockedFunction<(...args: unknown[]) => number> = jest.fn((...args: unknown[]) => {
        const [x] = args as [number];
        return x * 2;
      });
      const { result } = renderHook(() => useMemoize(mockFn, [mockFn]) as (x: number) => number);
      
      // Call the memoized function with same argument
      const result1 = result.current(5);
      const result2 = result.current(5);
      
      // Results should be the same
      expect(result1).toBe(10);
      expect(result2).toBe(10);
      
      // Function should be called only once
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
    
    it('should call function for different arguments', () => {
      const mockFn: jest.MockedFunction<(...args: unknown[]) => number> = jest.fn((...args: unknown[]) => {
        const [x] = args as [number];
        return x * 2;
      });
      const { result } = renderHook(() => useMemoize(mockFn, [mockFn]) as (x: number) => number);
      
      // Call the memoized function with different arguments
      result.current(5);
      result.current(10);
      
      // Function should be called twice
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('useRenderTime', () => {
    it('should measure render time', () => {
      const { result } = renderHook(() => useRenderTime('TestComponent'));
      
      expect(result.current.getAverageRenderTime).toBeDefined();
      expect(result.current.getMaxRenderTime).toBeDefined();
      expect(result.current.renderCount).toBeDefined();
      
      expect(typeof result.current.getAverageRenderTime).toBe('function');
      expect(typeof result.current.getMaxRenderTime).toBe('function');
    });
  });
  
  describe('useShouldUpdate', () => {
    it('should return true when props change', () => {
      const { result, rerender } = renderHook(
        ({ props }) => useShouldUpdate(props),
        { initialProps: { props: { a: 1, b: 2 } } }
      );
      
      expect(result.current).toBe(false);
      
      // Update props
      rerender({ props: { a: 2, b: 2 } });
      
      expect(result.current).toBe(true);
    });
    
    it('should return false when props do not change', () => {
      const { result, rerender } = renderHook(
        ({ props }) => useShouldUpdate(props),
        { initialProps: { props: { a: 1, b: 2 } } }
      );
      
      expect(result.current).toBe(false);
      
      // Update props with same values
      rerender({ props: { a: 1, b: 2 } });
      
      expect(result.current).toBe(false);
    });
    
    it('should check only specified dependencies', () => {
      const { result, rerender } = renderHook(
        ({ props }) => useShouldUpdate(props, ['a']),
        { initialProps: { props: { a: 1, b: 2 } } }
      );
      
      expect(result.current).toBe(false);
      
      // Update only dependency 'b'
      rerender({ props: { a: 1, b: 3 } });
      
      expect(result.current).toBe(false);
      
      // Update dependency 'a'
      rerender({ props: { a: 2, b: 3 } });
      
      expect(result.current).toBe(true);
    });
  });
  
  describe('useApiCall', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });
    
    afterEach(() => {
      jest.useRealTimers();
    });
    
    it('should execute API call', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'test' });
      const { result } = renderHook(() => useApiCall(mockApiCall));
      
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      
      // Execute API call
      await act(async () => {
        await result.current.execute('param1', 'param2');
      });
      
      expect(mockApiCall).toHaveBeenCalledWith('param1', 'param2');
      expect(result.current.data).toEqual({ data: 'test' });
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
    
    it('should handle API errors', async () => {
      const mockApiCall = jest.fn().mockRejectedValue(new Error('API Error'));
      const { result } = renderHook(() => useApiCall(mockApiCall));
      
      // Execute API call
      await act(async () => {
        await expect(result.current.execute('param1')).rejects.toThrow('API Error');
      });
      
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('API Error');
    });
    
    it('should debounce API calls', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'test' });
      const { result } = renderHook(() => useApiCall(mockApiCall, { debounceMs: 100 }));
      
      // Execute API call multiple times
      act(() => {
        result.current.execute('param1');
        result.current.execute('param2');
        result.current.execute('param3');
      });
      
      // Function should not be called yet
      expect(mockApiCall).not.toHaveBeenCalled();
      
      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(100);
      });
      
      // Wait for promises to resolve
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });
      
      // Function should be called once with the last parameters
      expect(mockApiCall).toHaveBeenCalledTimes(1);
      expect(mockApiCall).toHaveBeenCalledWith('param3');
    });
    
    it('should cache API results', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'test' });
      const { result } = renderHook(() => useApiCall(mockApiCall, { cacheKey: 'test-api' }));
      
      // Execute API call
      await act(async () => {
        await result.current.execute('param1');
      });
      
      expect(mockApiCall).toHaveBeenCalledTimes(1);
      expect(result.current.data).toEqual({ data: 'test' });
      
      // Execute API call again with same parameters
      await act(async () => {
        await result.current.execute('param1');
      });
      
      // Function should not be called again due to caching
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });
    
    it('should clear cache', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'test' });
      const { result } = renderHook(() => useApiCall(mockApiCall, { cacheKey: 'test-api' }));
      
      // Execute API call
      await act(async () => {
        await result.current.execute('param1');
      });
      
      expect(mockApiCall).toHaveBeenCalledTimes(1);
      
      // Clear cache
      act(() => {
        result.current.clearCache();
      });
      
      // Execute API call again
      await act(async () => {
        await result.current.execute('param1');
      });
      
      // Function should be called again after cache clear
      expect(mockApiCall).toHaveBeenCalledTimes(2);
    });
  });
});
