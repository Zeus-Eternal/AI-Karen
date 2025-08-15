import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useStableDeps,
  useStableCallback,
  useStableMemo,
  useDebouncedCallback,
  useThrottledCallback,
  useExpensiveComputation,
  usePerformanceMeasure
} from '../memoization';

describe('Memoization Utilities', () => {
  beforeEach(() => {
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('useStableDeps', () => {
    it('should return same reference for identical primitive arrays', () => {
      const { result, rerender } = renderHook(
        ({ deps }) => useStableDeps(deps),
        { initialProps: { deps: [1, 2, 3] as const } }
      );

      const firstResult = result.current;

      rerender({ deps: [1, 2, 3] as const });
      expect(result.current).toBe(firstResult);
    });

    it('should return new reference for different arrays', () => {
      const { result, rerender } = renderHook(
        ({ deps }) => useStableDeps(deps),
        { initialProps: { deps: [1, 2, 3] as const } }
      );

      const firstResult = result.current;

      rerender({ deps: [1, 2, 4] as const });
      expect(result.current).not.toBe(firstResult);
    });

    it('should handle object dependencies', () => {
      const { result, rerender } = renderHook(
        ({ deps }) => useStableDeps(deps),
        { initialProps: { deps: [{ a: 1, b: 2 }] as const } }
      );

      const firstResult = result.current;

      rerender({ deps: [{ a: 1, b: 2 }] as const });
      expect(result.current).toBe(firstResult);

      rerender({ deps: [{ a: 1, b: 3 }] as const });
      expect(result.current).not.toBe(firstResult);
    });
  });

  describe('useStableCallback', () => {
    it('should return same callback reference for stable deps', () => {
      const mockFn = vi.fn();
      const { result, rerender } = renderHook(
        ({ value }) => useStableCallback(() => mockFn(value), [value]),
        { initialProps: { value: 'test' } }
      );

      const firstCallback = result.current;

      rerender({ value: 'test' });
      expect(result.current).toBe(firstCallback);
    });

    it('should return new callback reference for changed deps', () => {
      const mockFn = vi.fn();
      const { result, rerender } = renderHook(
        ({ value }) => useStableCallback(() => mockFn(value), [value]),
        { initialProps: { value: 'test' } }
      );

      const firstCallback = result.current;

      rerender({ value: 'changed' });
      expect(result.current).not.toBe(firstCallback);
    });
  });

  describe('useStableMemo', () => {
    it('should return same value for stable deps', () => {
      const expensiveComputation = vi.fn(() => ({ computed: true }));
      const { result, rerender } = renderHook(
        ({ value }) => useStableMemo(() => expensiveComputation(value), [value]),
        { initialProps: { value: 'test' } }
      );

      const firstResult = result.current;
      expect(expensiveComputation).toHaveBeenCalledTimes(1);

      rerender({ value: 'test' });
      expect(result.current).toBe(firstResult);
      expect(expensiveComputation).toHaveBeenCalledTimes(1);
    });

    it('should recompute for changed deps', () => {
      const expensiveComputation = vi.fn(() => ({ computed: true }));
      const { result, rerender } = renderHook(
        ({ value }) => useStableMemo(() => expensiveComputation(value), [value]),
        { initialProps: { value: 'test' } }
      );

      const firstResult = result.current;

      rerender({ value: 'changed' });
      expect(result.current).not.toBe(firstResult);
      expect(expensiveComputation).toHaveBeenCalledTimes(2);
    });
  });

  describe('useDebouncedCallback', () => {
    it('should debounce callback execution', () => {
      const mockFn = vi.fn();
      const { result } = renderHook(() =>
        useDebouncedCallback(mockFn, 100, [])
      );

      // Call multiple times quickly
      result.current('arg1');
      result.current('arg2');
      result.current('arg3');

      expect(mockFn).not.toHaveBeenCalled();

      // Fast forward time
      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg3');
    });

    it('should cancel previous timeout on new calls', () => {
      const mockFn = vi.fn();
      const { result } = renderHook(() =>
        useDebouncedCallback(mockFn, 100, [])
      );

      result.current('arg1');
      
      act(() => {
        vi.advanceTimersByTime(50);
      });

      result.current('arg2');

      act(() => {
        vi.advanceTimersByTime(50);
      });

      expect(mockFn).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(50);
      });

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg2');
    });
  });

  describe('useThrottledCallback', () => {
    it('should throttle callback execution', () => {
      const mockFn = vi.fn();
      const { result } = renderHook(() =>
        useThrottledCallback(mockFn, 100, [])
      );

      // First call should execute immediately
      result.current('arg1');
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg1');

      // Subsequent calls within throttle period should be delayed
      result.current('arg2');
      result.current('arg3');
      expect(mockFn).toHaveBeenCalledTimes(1);

      // Fast forward time
      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(mockFn).toHaveBeenCalledTimes(2);
      expect(mockFn).toHaveBeenLastCalledWith('arg3');
    });
  });

  describe('useExpensiveComputation', () => {
    it('should cache computation results', () => {
      const expensiveComputation = vi.fn((a: number, b: number) => a + b);
      const { result, rerender } = renderHook(
        ({ args }) => useExpensiveComputation(expensiveComputation, args),
        { initialProps: { args: [1, 2] as const } }
      );

      expect(result.current).toBe(3);
      expect(expensiveComputation).toHaveBeenCalledTimes(1);

      // Same args should use cache
      rerender({ args: [1, 2] as const });
      expect(result.current).toBe(3);
      expect(expensiveComputation).toHaveBeenCalledTimes(1);

      // Different args should recompute
      rerender({ args: [2, 3] as const });
      expect(result.current).toBe(5);
      expect(expensiveComputation).toHaveBeenCalledTimes(2);
    });

    it('should implement LRU cache', () => {
      const expensiveComputation = vi.fn((a: number) => a * 2);
      const { rerender } = renderHook(
        ({ args }) => useExpensiveComputation(expensiveComputation, args, 2),
        { initialProps: { args: [1] as const } }
      );

      // Fill cache
      rerender({ args: [1] as const });
      rerender({ args: [2] as const });
      expect(expensiveComputation).toHaveBeenCalledTimes(2);

      // Add third item (should evict first)
      rerender({ args: [3] as const });
      expect(expensiveComputation).toHaveBeenCalledTimes(3);

      // Access first item again (should recompute)
      rerender({ args: [1] as const });
      expect(expensiveComputation).toHaveBeenCalledTimes(4);
    });
  });

  describe('usePerformanceMeasure', () => {
    beforeEach(() => {
      // Mock performance API
      global.performance = {
        now: vi.fn(() => Date.now()),
        mark: vi.fn(),
        measure: vi.fn(),
      } as any;
    });

    it('should measure performance when enabled', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      const { result } = renderHook(() =>
        usePerformanceMeasure('test-operation', true)
      );

      expect(performance.mark).toHaveBeenCalledWith('test-operation-start');

      const endMeasure = result.current;
      endMeasure();

      expect(performance.mark).toHaveBeenCalledWith('test-operation-end');
      expect(performance.measure).toHaveBeenCalledWith(
        'test-operation',
        'test-operation-start',
        'test-operation-end'
      );
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should not measure when disabled', () => {
      const { result } = renderHook(() =>
        usePerformanceMeasure('test-operation', false)
      );

      const endMeasure = result.current;
      endMeasure();

      expect(performance.mark).not.toHaveBeenCalled();
      expect(performance.measure).not.toHaveBeenCalled();
    });
  });
});