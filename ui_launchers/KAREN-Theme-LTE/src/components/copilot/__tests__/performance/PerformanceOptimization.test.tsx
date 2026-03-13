import { describe, test, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest';
import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { MemoryCache, MemoryMonitor, DataOptimizer } from '../../utils/memory-optimization';
import { PerformanceMonitor, PerformanceUtils } from '../../utils/performance-monitoring';
import { VirtualizedMessageList } from '../../components/chat/VirtualizedMessageList';
import { PerformanceDashboard } from '../../components/performance/PerformanceDashboard';

// Mock performance API
Object.defineProperty(window, 'performance', {
  writable: true,
  value: {
    memory: {
      usedJSHeapSize: 10000000,
      totalJSHeapSize: 50000000,
      jsHeapSizeLimit: 100000000
    },
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByName: vi.fn(),
    clearMarks: vi.fn(),
    clearMeasures: vi.fn()
  }
});

// Mock IntersectionObserver
globalThis.IntersectionObserver = vi.fn().mockImplementation(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
  takeRecords: vi.fn(() => []),
  root: null,
  rootMargin: '',
  thresholds: []
})) as any;

// Mock requestAnimationFrame
globalThis.requestAnimationFrame = vi.fn((callback: FrameRequestCallback) => {
  return setTimeout(callback, 0) as unknown as number;
});
globalThis.cancelAnimationFrame = vi.fn();

// Mock timers
vi.useFakeTimers();

describe('Performance Optimization', () => {
  describe('MemoryCache', () => {
    let cache: MemoryCache<string>;

    beforeEach(() => {
      cache = new MemoryCache({ maxSize: 3, ttl: 1000 });
    });

    afterEach(() => {
      cache.destroy();
      vi.clearAllTimers();
    });

    test('should store and retrieve values', () => {
      cache.set('key1', 'value1');
      expect(cache.get('key1')).toBe('value1');
    });

    test('should evict oldest entries when cache is full', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      cache.set('key3', 'value3');
      
      // Cache is now full
      expect(cache.size()).toBe(3);
      
      // Adding another entry should evict the oldest
      cache.set('key4', 'value4');
      expect(cache.size()).toBe(3);
      expect(cache.get('key1')).toBeUndefined();
      expect(cache.get('key4')).toBe('value4');
    });

    test('should expire entries after TTL', () => {
      cache.set('key1', 'value1', 100); // 100ms TTL
      
      // Should be available immediately
      expect(cache.get('key1')).toBe('value1');
      
      // Advance time beyond TTL
      act(() => {
        vi.advanceTimersByTime(150);
      });
      
      // Should be expired now
      expect(cache.get('key1')).toBeUndefined();
    });

    test('should clear all entries', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      
      expect(cache.size()).toBe(2);
      
      cache.clear();
      
      expect(cache.size()).toBe(0);
      expect(cache.get('key1')).toBeUndefined();
      expect(cache.get('key2')).toBeUndefined();
    });
  });

  describe('MemoryMonitor', () => {
    let monitor: MemoryMonitor;

    beforeEach(() => {
      monitor = new MemoryMonitor({
        warningThreshold: 70,
        criticalThreshold: 90
      });
    });

    afterEach(() => {
      monitor.clearWarningHistory();
    });

    test('should get current memory usage', () => {
      const usage = monitor.getMemoryUsage();
      
      expect(usage).toEqual({
        used: 10000000,
        total: 50000000,
        percentage: 10,
        limit: 100000000
      });
    });

    test('should detect warning memory usage', () => {
      // Mock high memory usage
      Object.defineProperty(window.performance, 'memory', {
        value: {
          usedJSHeapSize: 80000000, // 80% of limit
          totalJSHeapSize: 90000000,
          jsHeapSizeLimit: 100000000
        },
        writable: true
      });

      const { isWarning, isCritical, usage } = monitor.checkMemoryUsage();
      
      expect(isWarning).toBe(true);
      expect(isCritical).toBe(false);
      expect(usage?.percentage).toBe(80);
    });

    test('should detect critical memory usage', () => {
      // Mock critical memory usage
      Object.defineProperty(window.performance, 'memory', {
        value: {
          usedJSHeapSize: 95000000, // 95% of limit
          totalJSHeapSize: 98000000,
          jsHeapSizeLimit: 100000000
        },
        writable: true
      });

      const { isWarning, isCritical, usage } = monitor.checkMemoryUsage();
      
      expect(isWarning).toBe(true);
      expect(isCritical).toBe(true);
      expect(usage?.percentage).toBe(95);
    });

    test('should track warning history', () => {
      // Mock high memory usage
      Object.defineProperty(window.performance, 'memory', {
        value: {
          usedJSHeapSize: 80000000,
          totalJSHeapSize: 90000000,
          jsHeapSizeLimit: 100000000
        },
        writable: true
      });

      monitor.checkMemoryUsage();
      
      const history = monitor.getWarningHistory();
      
      expect(history.length).toBe(1);
      expect(history[0]?.percentage).toBe(80);
    });
  });

  describe('DataOptimizer', () => {
    test('should chunk arrays correctly', () => {
      const array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      const chunks = DataOptimizer.chunkArray(array, 3);
      
      expect(chunks).toEqual([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10]
      ]);
    });

    test('should paginate data correctly', () => {
      const array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      const result = DataOptimizer.paginate(array, 3, 2);
      
      expect(result).toEqual({
        data: [4, 5, 6],
        totalPages: 4,
        totalItems: 10
      });
    });

    test('should debounce function calls', () => {
      vi.useFakeTimers();
      
      const mockFn = vi.fn();
      const debouncedFn = DataOptimizer.debounce(mockFn, 100);
      
      // Call multiple times quickly
      debouncedFn();
      debouncedFn();
      debouncedFn();
      
      // Should not be called yet
      expect(mockFn).not.toHaveBeenCalled();
      
      // Advance timer
      act(() => {
        vi.advanceTimersByTime(150);
      });
      
      // Should be called once
      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    test('should throttle function calls', () => {
      vi.useFakeTimers();
      
      const mockFn = vi.fn().mockReturnValue('result');
      const throttledFn = DataOptimizer.throttle(mockFn, 100);
      
      // Call multiple times
      const result1 = throttledFn();
      const result2 = throttledFn();
      const result3 = throttledFn();
      
      // Should be called only once
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // All calls should return the same result
      expect(result1).toBe('result');
      expect(result2).toBe('result');
      expect(result3).toBe('result');
      
      // Advance timer
      act(() => {
        vi.advanceTimersByTime(150);
      });
      
      // Call again after throttle period
      const result4 = throttledFn();
      
      // Should be called again
      expect(mockFn).toHaveBeenCalledTimes(2);
    });

    test('should memoize function results', () => {
      const mockFn = vi.fn((x: number) => x * 2);
      const memoizedFn = DataOptimizer.memoize(mockFn);
      
      // Call with same argument multiple times
      const result1 = memoizedFn(5);
      const result2 = memoizedFn(5);
      const result3 = memoizedFn(5);
      
      // Should be called only once
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // All calls should return the same result
      expect(result1).toBe(10);
      expect(result2).toBe(10);
      expect(result3).toBe(10);
      
      // Call with different argument
      const result4 = memoizedFn(10);
      
      // Should be called again
      expect(mockFn).toHaveBeenCalledTimes(2);
      expect(result4).toBe(20);
    });
  });

  describe('PerformanceMonitor', () => {
    let monitor: PerformanceMonitor;

    beforeEach(() => {
      monitor = new PerformanceMonitor();
      vi.clearAllMocks();
    });

    afterEach(() => {
      monitor.destroy();
    });

    test('should measure performance', () => {
      // Mock performance.measure to return a duration
      (window.performance.measure as ReturnType<typeof vi.fn>).mockReturnValue({
        duration: 50,
        startTime: 1000
      });
      
      (window.performance.getEntriesByName as ReturnType<typeof vi.fn>).mockReturnValue([{
        duration: 50,
        startTime: 1000
      }]);
      
      monitor.start('test-operation');
      const duration = monitor.end('test-operation');
      
      expect(duration).toBe(50);
      expect(window.performance.mark).toHaveBeenCalledWith('test-operation-start');
      expect(window.performance.mark).toHaveBeenCalledWith('test-operation-end');
      expect(window.performance.measure).toHaveBeenCalledWith('test-operation', 'test-operation-start', 'test-operation-end');
    });

    test('should get performance metrics', () => {
      // Add some mock entries
      monitor['entries'] = [
        { name: 'test1', duration: 10, startTime: 1000, type: 'measure' },
        { name: 'test2', duration: 20, startTime: 2000, type: 'measure' }
      ];
      
      const metrics = monitor.getMetrics();
      
      expect(metrics.renderTime).toBe(15); // Average of 10 and 20
      expect(metrics.timestamp).toBeGreaterThan(0);
    });

    test('should track memory usage when enabled', () => {
      const memoryMonitor = new PerformanceMonitor({ enableMemoryTracking: true });
      
      const metrics = memoryMonitor.getMetrics();
      
      expect(metrics.memoryUsage).toEqual({
        used: 10000000,
        total: 50000000,
        percentage: 10,
        limit: 100000000
      });
      
      memoryMonitor.destroy();
    });
  });

  describe('PerformanceUtils', () => {
    test('should measure function execution time', () => {
      const mockFn = vi.fn(() => 'result');
      const measuredFn = PerformanceUtils.measureTime('test-fn', mockFn);
      
      const result = measuredFn();
      
      expect(result).toBe('result');
      expect(mockFn).toHaveBeenCalled();
    });
  });

  describe('VirtualizedMessageList', () => {
    const mockTheme = {
      colors: {
        primary: '#007bff',
        secondary: '#6c757d',
        background: '#ffffff',
        surface: '#f8f9fa',
        text: '#212529',
        textSecondary: '#6c757d',
        border: '#dee2e6',
        error: '#dc3545',
        warning: '#ffc107',
        success: '#28a745',
        info: '#17a2b8'
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        xxl: '48px'
      },
      typography: {
        fontFamily: 'Arial, sans-serif',
        fontSize: {
          xs: '12px',
          sm: '14px',
          base: '16px',
          lg: '18px',
          xl: '20px',
          xxl: '24px'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        }
      },
      borderRadius: '4px',
      shadows: {
        sm: '0 1px 2px rgba(0,0,0,0.1)',
        md: '0 4px 6px rgba(0,0,0,0.1)',
        lg: '0 10px 15px rgba(0,0,0,0.1)'
      }
    };

    const mockMessages = Array.from({ length: 100 }, (_, i) => {
      const role = i % 2 === 0 ? 'user' : 'assistant';
      return {
        id: `msg-${i}`,
        role,
        content: `Message ${i + 1}`,
        timestamp: new Date()
      };
    }) as any;

    test('should render virtualized message list', () => {
      render(
        <VirtualizedMessageList
          messages={mockMessages}
          theme={mockTheme}
          pageSize={10}
        />
      );
      
      // Should render only a subset of messages (virtualized)
      const messageElements = screen.getAllByText(/Message \d+/);
      expect(messageElements.length).toBeLessThan(mockMessages.length);
    });

    test('should call onLoadMore when scrolling to bottom', () => {
      const mockOnLoadMore = vi.fn();
      
      render(
        <VirtualizedMessageList
          messages={mockMessages}
          theme={mockTheme}
          pageSize={10}
          onLoadMore={mockOnLoadMore}
        />
      );
      
      // Simulate scroll to bottom
      const container = screen.getByRole('article').closest('div');
      if (container) {
        act(() => {
          Object.defineProperty(container, 'scrollTop', {
            value: container.scrollHeight - container.clientHeight,
            writable: true
          });
          fireEvent.scroll(container);
        });
      }
      
      // Should call onLoadMore
      expect(mockOnLoadMore).toHaveBeenCalled();
    });
  });

  describe('PerformanceDashboard', () => {
    const mockTheme = {
      colors: {
        primary: '#007bff',
        secondary: '#6c757d',
        background: '#ffffff',
        surface: '#f8f9fa',
        text: '#212529',
        textSecondary: '#6c757d',
        border: '#dee2e6',
        error: '#dc3545',
        warning: '#ffc107',
        success: '#28a745',
        info: '#17a2b8'
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        xxl: '48px'
      },
      typography: {
        fontFamily: 'Arial, sans-serif',
        fontSize: {
          xs: '12px',
          sm: '14px',
          base: '16px',
          lg: '18px',
          xl: '20px',
          xxl: '24px'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        }
      },
      borderRadius: '4px',
      shadows: {
        sm: '0 1px 2px rgba(0,0,0,0.1)',
        md: '0 4px 6px rgba(0,0,0,0.1)',
        lg: '0 10px 15px rgba(0,0,0,0.1)'
      }
    };

    test('should render performance dashboard', () => {
      render(<PerformanceDashboard theme={mockTheme} />);
      
      expect(screen.getByText('Performance Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Avg. Render Time')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    });

    test('should toggle expanded state', () => {
      render(<PerformanceDashboard theme={mockTheme} />);
      
      // Should be expanded by default
      expect(screen.getByText('Avg. Render Time')).toBeInTheDocument();
      
      // Click collapse button
      const collapseButton = screen.getByLabelText('Collapse dashboard');
      fireEvent.click(collapseButton);
      
      // Should be collapsed
      expect(screen.queryByText('Avg. Render Time')).not.toBeInTheDocument();
      
      // Click expand button
      const expandButton = screen.getByLabelText('Expand dashboard');
      fireEvent.click(expandButton);
      
      // Should be expanded again
      expect(screen.getByText('Avg. Render Time')).toBeInTheDocument();
    });

    test('should call onClose when close button is clicked', () => {
      const mockOnClose = vi.fn();
      
      render(<PerformanceDashboard theme={mockTheme} onClose={mockOnClose} />);
      
      const closeButton = screen.getByLabelText('Close dashboard');
      fireEvent.click(closeButton);
      
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});