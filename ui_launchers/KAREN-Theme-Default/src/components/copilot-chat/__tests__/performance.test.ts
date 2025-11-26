import { 
  debounce, 
  throttle, 
  memoize, 
  VirtualListUtils, 
  PerformanceMonitor, 
  ImageOptimizer, 
  CodeHighlighter, 
  ComponentOptimizer 
} from '../utils/performance';

describe('Performance Utilities', () => {
  describe('debounce', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });
    
    afterEach(() => {
      jest.useRealTimers();
    });
    
    it('should debounce function calls', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);
      
      // Call the debounced function multiple times
      debouncedFn();
      debouncedFn();
      debouncedFn();
      
      // Function should not be called yet
      expect(mockFn).not.toHaveBeenCalled();
      
      // Fast-forward time
      jest.advanceTimersByTime(100);
      
      // Function should be called once
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
    
    it('should reset timer on subsequent calls', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);
      
      // Call the debounced function
      debouncedFn();
      
      // Fast-forward time partially
      jest.advanceTimersByTime(50);
      
      // Call again
      debouncedFn();
      
      // Fast-forward time
      jest.advanceTimersByTime(50);
      
      // Function should not be called yet
      expect(mockFn).not.toHaveBeenCalled();
      
      // Fast-forward time
      jest.advanceTimersByTime(50);
      
      // Function should be called once
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('throttle', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });
    
    afterEach(() => {
      jest.useRealTimers();
    });
    
    it('should throttle function calls', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);
      
      // Call the throttled function multiple times
      throttledFn();
      throttledFn();
      throttledFn();
      
      // Function should be called immediately
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // Fast-forward time
      jest.advanceTimersByTime(100);
      
      // Call again
      throttledFn();
      
      // Function should be called again
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
    
    it('should ignore calls within throttle period', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);
      
      // Call the throttled function
      throttledFn();
      
      // Function should be called immediately
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // Call again within throttle period
      throttledFn();
      
      // Function should not be called again
      expect(mockFn).toHaveBeenCalledTimes(1);
      
      // Fast-forward time
      jest.advanceTimersByTime(100);
      
      // Call again after throttle period
      throttledFn();
      
      // Function should be called again
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('memoize', () => {
    it('should cache function results', () => {
      const mockFn: jest.MockedFunction<(...args: unknown[]) => number> = jest.fn((...args: unknown[]) => {
        const [x] = args as [number];
        return x * 2;
      });
      const memoizedFn = memoize(mockFn) as (x: number) => number;
      
      // Call the memoized function with same argument
      const result1 = memoizedFn(5);
      const result2 = memoizedFn(5);
      
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
      const memoizedFn = memoize(mockFn) as (x: number) => number;
      
      // Call the memoized function with different arguments
      const result1 = memoizedFn(5);
      const result2 = memoizedFn(10);
      
      // Results should be different
      expect(result1).toBe(10);
      expect(result2).toBe(20);
      
      // Function should be called twice
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
    
    it('should use custom key generator', () => {
      const mockFn: jest.MockedFunction<(...args: unknown[]) => string> = jest.fn((...args: unknown[]) => {
        const [x, y] = args as [number, string];
        return `${x}-${y}`;
      });
      const keyGenerator = (x: unknown, y: unknown) => `${String(y)}-${String(x)}`;
      const memoizedFn = memoize(mockFn, keyGenerator) as (x: number, y: string) => string;
      
      // Call the memoized function with same arguments in different order
      const result1 = memoizedFn(5, 'test');
      const result2 = memoizedFn(10, 'test');
      const result3 = memoizedFn(5, 'other');
      
      // Results should be correct
      expect(result1).toBe('5-test');
      expect(result2).toBe('10-test');
      expect(result3).toBe('5-other');
      
      // Function should be called three times
      expect(mockFn).toHaveBeenCalledTimes(3);
    });
  });
  
  describe('VirtualListUtils', () => {
    describe('calculateVisibleItems', () => {
      it('should calculate visible items correctly', () => {
        const result = VirtualListUtils.calculateVisibleItems(100, 50, 400, 0);
        
        expect(result.startIndex).toBe(0);
        expect(result.endIndex).toBe(10);
      });
      
      it('should calculate visible items with scroll offset', () => {
        const result = VirtualListUtils.calculateVisibleItems(100, 50, 400, 250);
        
        expect(result.startIndex).toBe(3);
        expect(result.endIndex).toBe(13);
      });
      
      it('should handle edge cases', () => {
        // Empty list
        const emptyResult = VirtualListUtils.calculateVisibleItems(0, 50, 400, 0);
        expect(emptyResult.startIndex).toBe(0);
        expect(emptyResult.endIndex).toBe(-1);
        
        // Scroll beyond list
        const beyondResult = VirtualListUtils.calculateVisibleItems(10, 50, 400, 1000);
        expect(beyondResult.startIndex).toBe(18);
        expect(beyondResult.endIndex).toBe(9);
      });
    });
    
    describe('calculateItemOffset', () => {
      it('should calculate item offset correctly', () => {
        const offset = VirtualListUtils.calculateItemOffset(5, 50);
        expect(offset).toBe(250);
      });
    });
    
    describe('calculateTotalHeight', () => {
      it('should calculate total height correctly', () => {
        const height = VirtualListUtils.calculateTotalHeight(100, 50);
        expect(height).toBe(5000);
      });
    });
  });
  
  describe('PerformanceMonitor', () => {
    beforeEach(() => {
      PerformanceMonitor.clearMetrics();
    });
    
    describe('startMeasure', () => {
      it('should return a function to end measurement', () => {
        const endMeasure = PerformanceMonitor.startMeasure('test');
        expect(typeof endMeasure).toBe('function');
      });
    });
    
    describe('getAverageMetric', () => {
      it('should return null for non-existent metric', () => {
        const average = PerformanceMonitor.getAverageMetric('non-existent');
        expect(average).toBeNull();
      });
      
      it('should calculate average correctly', () => {
        const endMeasure1 = PerformanceMonitor.startMeasure('test');
        endMeasure1();
        
        const endMeasure2 = PerformanceMonitor.startMeasure('test');
        endMeasure2();
        
        const average = PerformanceMonitor.getAverageMetric('test');
        expect(average).toBeGreaterThan(0);
      });
    });
    
    describe('getAllMetrics', () => {
      it('should return all metrics', () => {
        const endMeasure1 = PerformanceMonitor.startMeasure('test1');
        endMeasure1();
        
        const endMeasure2 = PerformanceMonitor.startMeasure('test2');
        endMeasure2();
        
        const metrics = PerformanceMonitor.getAllMetrics();
        
        expect(metrics).toHaveProperty('test1');
        expect(metrics).toHaveProperty('test2');
        expect(metrics.test1).toHaveProperty('average');
        expect(metrics.test1).toHaveProperty('count');
        expect(metrics.test1.count).toBe(1);
      });
    });
    
    describe('clearMetrics', () => {
      it('should clear all metrics', () => {
        const endMeasure = PerformanceMonitor.startMeasure('test');
        endMeasure();
        
        PerformanceMonitor.clearMetrics();
        
        const average = PerformanceMonitor.getAverageMetric('test');
        expect(average).toBeNull();
      });
    });
  });
  
  describe('ImageOptimizer', () => {
    describe('getOptimizedImageUrl', () => {
      it('should add optimization parameters to URL', () => {
        const url = 'https://example.com/image.jpg';
        const optimizedUrl = ImageOptimizer.getOptimizedImageUrl(url, 400, 300, 80);
        
        expect(optimizedUrl).toContain('width=400');
        expect(optimizedUrl).toContain('height=300');
        expect(optimizedUrl).toContain('quality=80');
      });
      
      it('should handle URLs with existing parameters', () => {
        const url = 'https://example.com/image.jpg?param=value';
        const optimizedUrl = ImageOptimizer.getOptimizedImageUrl(url, 400, 300, 80);
        
        expect(optimizedUrl).toContain('param=value');
        expect(optimizedUrl).toContain('width=400');
        expect(optimizedUrl).toContain('height=300');
        expect(optimizedUrl).toContain('quality=80');
      });
      
      it('should handle already optimized URLs', () => {
        const url = 'https://example.com/image.jpg?width=400&height=300';
        const optimizedUrl = ImageOptimizer.getOptimizedImageUrl(url, 400, 300, 80);
        
        expect(optimizedUrl).toBe(url);
      });
    });
    
    describe('generateSrcset', () => {
      it('should generate srcset with multiple widths', () => {
        const url = 'https://example.com/image.jpg';
        const srcset = ImageOptimizer.generateSrcset(url, [200, 400, 800]);
        
        expect(srcset).toContain('width=200 200w');
        expect(srcset).toContain('width=400 400w');
        expect(srcset).toContain('width=800 800w');
      });
    });
    
    describe('generateSizes', () => {
      it('should generate sizes attribute', () => {
        const breakpoints = [
          { maxWidth: 600, size: '100vw' },
          { maxWidth: 1200, size: '50vw' }
        ];
        
        const sizes = ImageOptimizer.generateSizes(breakpoints);
        
        expect(sizes).toContain('(max-width: 600px) 100vw');
        expect(sizes).toContain('(max-width: 1200px) 50vw');
      });
    });
  });
  
  describe('CodeHighlighter', () => {
    beforeEach(() => {
      CodeHighlighter.clearCache();
    });
    
    describe('highlightCode', () => {
      it('should cache highlighted code', async () => {
        const mockHighlightFn = jest.fn().mockResolvedValue('<highlighted>code</highlighted>');
        
        const result1 = await CodeHighlighter.highlightCode('console.log("Hello");', 'javascript', mockHighlightFn);
        const result2 = await CodeHighlighter.highlightCode('console.log("Hello");', 'javascript', mockHighlightFn);
        
        // Results should be the same
        expect(result1).toBe('<highlighted>code</highlighted>');
        expect(result2).toBe('<highlighted>code</highlighted>');
        
        // Function should be called only once
        expect(mockHighlightFn).toHaveBeenCalledTimes(1);
      });
      
      it('should call highlight function for different code', async () => {
        const mockHighlightFn = jest.fn().mockResolvedValue('<highlighted>code</highlighted>');
        
        await CodeHighlighter.highlightCode('console.log("Hello");', 'javascript', mockHighlightFn);
        await CodeHighlighter.highlightCode('console.log("World");', 'javascript', mockHighlightFn);
        
        // Function should be called twice
        expect(mockHighlightFn).toHaveBeenCalledTimes(2);
      });
    });
    
    describe('clearCache', () => {
      it('should clear cache', async () => {
        const mockHighlightFn = jest.fn().mockResolvedValue('<highlighted>code</highlighted>');
        
        await CodeHighlighter.highlightCode('console.log("Hello");', 'javascript', mockHighlightFn);
        
        // Cache should have one item
        expect(CodeHighlighter.getCacheSize()).toBe(1);
        
        CodeHighlighter.clearCache();
        
        // Cache should be empty
        expect(CodeHighlighter.getCacheSize()).toBe(0);
      });
    });
  });
  
  describe('ComponentOptimizer', () => {
    describe('shouldComponentUpdate', () => {
      it('should return true when props change', () => {
        const prevProps = { a: 1, b: 2 };
        const nextProps = { a: 2, b: 2 };
        
        const shouldUpdate = ComponentOptimizer.shouldComponentUpdate(
          prevProps,
          nextProps,
          ['a']
        );
        
        expect(shouldUpdate).toBe(true);
      });
      
      it('should return false when props do not change', () => {
        const prevProps = { a: 1, b: 2 };
        const nextProps = { a: 1, b: 2 };
        
        const shouldUpdate = ComponentOptimizer.shouldComponentUpdate(
          prevProps,
          nextProps,
          ['a']
        );
        
        expect(shouldUpdate).toBe(false);
      });
      
      it('should check only specified dependencies', () => {
        const prevProps = { a: 1, b: 2 };
        const nextProps = { a: 1, b: 3 };
        
        const shouldUpdate = ComponentOptimizer.shouldComponentUpdate(
          prevProps,
          nextProps,
          ['a']
        );
        
        expect(shouldUpdate).toBe(false);
      });
    });
    
    describe('deepEqual', () => {
      it('should return true for equal objects', () => {
        const obj1 = { a: 1, b: { c: 2 } };
        const obj2 = { a: 1, b: { c: 2 } };
        
        const isEqual = ComponentOptimizer.deepEqual(obj1, obj2);
        expect(isEqual).toBe(true);
      });
      
      it('should return false for different objects', () => {
        const obj1 = { a: 1, b: { c: 2 } };
        const obj2 = { a: 1, b: { c: 3 } };
        
        const isEqual = ComponentOptimizer.deepEqual(obj1, obj2);
        expect(isEqual).toBe(false);
      });
      
      it('should handle different types', () => {
        const isEqual1 = ComponentOptimizer.deepEqual(1, '1');
        expect(isEqual1).toBe(false);
        
        const isEqual2 = ComponentOptimizer.deepEqual(null, undefined);
        expect(isEqual2).toBe(false);
      });
    });
  });
});
