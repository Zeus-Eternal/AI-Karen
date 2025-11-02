/**
 * Performance Optimizer Tests
 * Tests for automatic performance optimization functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { PerformanceOptimizer } from '../performance-optimizer';

// Mock DOM APIs
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),

global.IntersectionObserver = mockIntersectionObserver;

// Mock PerformanceObserver
class MockPerformanceObserver {
  private callback: (list: any) => void;
  
  constructor(callback: (list: any) => void) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
}

// Mock fetch
global.fetch = vi.fn();

// Mock canvas for WebP detection
const mockCanvas = {
  width: 1,
  height: 1,
  toDataURL: vi.fn(() => 'data:image/webp;base64,test'),
};

global.document = {
  createElement: vi.fn((tag) => {
    if (tag === 'canvas') return mockCanvas;
    if (tag === 'link') return { rel: '', href: '', setAttribute: vi.fn() };
    return { setAttribute: vi.fn(), appendChild: vi.fn() };
  }),
  head: { appendChild: vi.fn() },
  querySelectorAll: vi.fn(() => []),
  addEventListener: vi.fn(),
} as any;

// Mock navigator
global.navigator = {
  serviceWorker: {
    register: vi.fn(() => Promise.resolve({
      addEventListener: vi.fn(),
    })),
  },
} as any;

// Mock window
global.window = {
  location: { pathname: '/dashboard' },
} as any;

// Mock performance
global.performance = {
  memory: {
    usedJSHeapSize: 50000000,
    totalJSHeapSize: 100000000,
  },
} as any;

global.PerformanceObserver = MockPerformanceObserver as any;

describe('PerformanceOptimizer', () => {
  let optimizer: PerformanceOptimizer;

  beforeEach(() => {
    vi.clearAllMocks();
    optimizer = new PerformanceOptimizer();

  afterEach(() => {
    optimizer.destroy();

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      expect(optimizer).toBeDefined();

    it('should initialize with custom configuration', () => {
      const customConfig = {
        bundleSplitting: { enabled: false },
        imageOptimization: { webpConversion: false },
      };
      
      const customOptimizer = new PerformanceOptimizer(customConfig);
      expect(customOptimizer).toBeDefined();
      customOptimizer.destroy();


  describe('Bundle Optimization', () => {
    it('should generate bundle size recommendations', () => {
      // Mock large bundle size
      optimizer['metrics'].bundleSize.after = 600 * 1024; // 600KB
      
      const recommendations = optimizer.generateRecommendations();
      const bundleRec = recommendations.find(r => r.type === 'bundle');
      
      expect(bundleRec).toBeDefined();
      expect(bundleRec?.title).toContain('Large bundle size');

    it('should identify large components for splitting', () => {
      const recommendations = optimizer.generateRecommendations();
      const componentRecs = recommendations.filter(r => r.id.includes('component-split'));
      
      expect(componentRecs.length).toBeGreaterThan(0);


  describe('Image Optimization', () => {
    it('should detect WebP support', () => {
      const supportsWebP = optimizer['checkWebPSupport']();
      expect(supportsWebP).toBe(true);

    it('should set up lazy loading observer', () => {
      optimizer['setupLazyLoading']();
      expect(mockIntersectionObserver).toHaveBeenCalled();

    it('should generate lazy loading recommendations', () => {
      // Mock images without lazy loading
      const mockImages = [
        { loading: null, setAttribute: vi.fn() },
        { loading: null, setAttribute: vi.fn() },
      ];
      
      global.document.querySelectorAll = vi.fn((selector) => {
        if (selector === 'img') return mockImages;
        if (selector === 'img:not([loading])') return mockImages;
        return [];

      const recommendations = optimizer.generateRecommendations();
      const lazyLoadingRec = recommendations.find(r => r.id === 'lazy-loading-images');
      
      expect(lazyLoadingRec).toBeDefined();
      expect(lazyLoadingRec?.title).toContain('images without lazy loading');

    it('should check if image exists', async () => {
      (global.fetch as Mock).mockResolvedValue({ ok: true });
      
      const exists = await optimizer['checkImageExists']('test.webp');
      expect(exists).toBe(true);
      expect(fetch).toHaveBeenCalledWith('test.webp', { method: 'HEAD' });


  describe('Cache Optimization', () => {
    it('should set up service worker caching', async () => {
      await optimizer['setupServiceWorkerCaching']();
      expect(navigator.serviceWorker.register).toHaveBeenCalledWith('/sw.js');

    it('should generate cache recommendations', () => {
      // Mock low cache hit rate
      optimizer['metrics'].cachePerformance.hitRate = 30;
      optimizer['metrics'].cachePerformance.missRate = 70;
      
      const recommendations = optimizer.generateRecommendations();
      const cacheRec = recommendations.find(r => r.id === 'low-cache-hit-rate');
      
      expect(cacheRec).toBeDefined();
      expect(cacheRec?.title).toContain('Low cache hit rate');

    it('should implement preloading strategies', () => {
      optimizer['implementPreloadingStrategies']();
      // Should not throw errors

    it('should preload critical resources', () => {
      const mockLink = { rel: '', href: '', setAttribute: vi.fn() };
      global.document.createElement = vi.fn(() => mockLink);
      
      optimizer['preloadCriticalResources']();
      expect(document.createElement).toHaveBeenCalledWith('link');


  describe('Memory Management', () => {
    it('should detect memory leaks', () => {
      // Mock high memory usage
      global.performance.memory.usedJSHeapSize = 95000000;
      global.performance.memory.totalJSHeapSize = 100000000;
      
      optimizer['detectMemoryLeaks']();
      
      const recommendations = optimizer.generateRecommendations();
      const memoryRec = recommendations.find(r => r.id === 'memory-leak-detected');
      
      expect(memoryRec).toBeDefined();
      expect(memoryRec?.priority).toBe('critical');

    it('should generate memory usage recommendations', () => {
      // Mock high memory usage
      global.performance.memory.usedJSHeapSize = 85000000;
      global.performance.memory.totalJSHeapSize = 100000000;
      
      const recommendations = optimizer.generateRecommendations();
      const memoryRec = recommendations.find(r => r.id === 'high-memory-usage');
      
      expect(memoryRec).toBeDefined();
      expect(memoryRec?.type).toBe('memory');

    it('should monitor garbage collection', () => {
      optimizer['monitorGarbageCollection']();
      // Should set up monitoring without errors


  describe('Recommendations', () => {
    it('should generate initial recommendations', () => {
      const recommendations = optimizer.generateRecommendations();
      expect(recommendations.length).toBeGreaterThan(0);

    it('should sort recommendations by priority', () => {
      const recommendations = optimizer.generateRecommendations();
      
      // Check that critical/high priority items come first
      const priorities = recommendations.map(r => r.priority);
      const criticalIndex = priorities.indexOf('critical');
      const lowIndex = priorities.indexOf('low');
      
      if (criticalIndex !== -1 && lowIndex !== -1) {
        expect(criticalIndex).toBeLessThan(lowIndex);
      }

    it('should include estimated performance gains', () => {
      const recommendations = optimizer.generateRecommendations();
      
      recommendations.forEach(rec => {
        expect(rec.estimatedGain).toBeGreaterThan(0);
        expect(rec.estimatedGain).toBeLessThanOrEqual(100);


    it('should provide implementation guidance', () => {
      const recommendations = optimizer.generateRecommendations();
      
      recommendations.forEach(rec => {
        expect(rec.implementation).toBeTruthy();
        expect(rec.impact).toBeTruthy();
        expect(rec.description).toBeTruthy();



  describe('Optimization Application', () => {
    it('should apply optimizations', async () => {
      const applyOptimizationSpy = vi.spyOn(optimizer as any, 'applyOptimization');
      applyOptimizationSpy.mockResolvedValue(undefined);
      
      await optimizer.applyOptimizations();
      
      // Should attempt to apply high priority optimizations
      expect(applyOptimizationSpy).toHaveBeenCalled();

    it('should apply image optimizations', async () => {
      const mockImages = [
        { setAttribute: vi.fn(), hasAttribute: vi.fn(() => false) },
        { setAttribute: vi.fn(), hasAttribute: vi.fn(() => false) },
      ];
      
      global.document.querySelectorAll = vi.fn(() => mockImages);
      
      const recommendation = {
        id: 'lazy-loading-images',
        type: 'image' as const,
        priority: 'medium' as const,
        title: 'Add lazy loading',
        description: 'Test',
        impact: 'Test',
        implementation: 'Test',
        estimatedGain: 20,
      };
      
      await optimizer['applyImageOptimization'](recommendation);
      
      mockImages.forEach(img => {
        expect(img.setAttribute).toHaveBeenCalledWith('loading', 'lazy');


    it('should apply cache optimizations', async () => {
      const setupServiceWorkerSpy = vi.spyOn(optimizer as any, 'setupServiceWorkerCaching');
      setupServiceWorkerSpy.mockResolvedValue(undefined);
      
      const recommendation = {
        id: 'enable-service-worker',
        type: 'cache' as const,
        priority: 'high' as const,
        title: 'Enable Service Worker',
        description: 'Test',
        impact: 'Test',
        implementation: 'Test',
        estimatedGain: 40,
      };
      
      await optimizer['applyCacheOptimization'](recommendation);
      expect(setupServiceWorkerSpy).toHaveBeenCalled();


  describe('Metrics', () => {
    it('should provide optimization metrics', () => {
      const metrics = optimizer.getMetrics();
      
      expect(metrics).toHaveProperty('bundleSize');
      expect(metrics).toHaveProperty('imageOptimization');
      expect(metrics).toHaveProperty('cachePerformance');
      expect(metrics).toHaveProperty('memoryUsage');

    it('should track bundle size changes', () => {
      const metrics = optimizer.getMetrics();
      expect(metrics.bundleSize).toHaveProperty('before');
      expect(metrics.bundleSize).toHaveProperty('after');
      expect(metrics.bundleSize).toHaveProperty('reduction');

    it('should track image optimization metrics', () => {
      const metrics = optimizer.getMetrics();
      expect(metrics.imageOptimization).toHaveProperty('imagesOptimized');
      expect(metrics.imageOptimization).toHaveProperty('sizeReduction');
      expect(metrics.imageOptimization).toHaveProperty('webpConversions');


  describe('Configuration', () => {
    it('should update configuration', () => {
      const newConfig = {
        bundleSplitting: { enabled: false },
      };
      
      optimizer.updateConfig(newConfig);
      // Should not throw errors and should reinitialize

    it('should handle partial configuration updates', () => {
      const partialConfig = {
        imageOptimization: {
          webpConversion: false,
        },
      };
      
      expect(() => {
        optimizer.updateConfig(partialConfig);
      }).not.toThrow();


  describe('Resource Analysis', () => {
    it('should analyze resource performance', () => {
      const slowResource = {
        name: 'slow-script.js',
        duration: 1500,
        transferSize: 100000,
        decodedBodySize: 100000,
      } as PerformanceResourceTiming;
      
      optimizer['analyzeResourcePerformance'](slowResource);
      
      const recommendations = optimizer.generateRecommendations();
      const resourceRec = recommendations.find(r => r.id.includes('slow-resource'));
      
      expect(resourceRec).toBeDefined();

    it('should analyze garbage collection patterns', () => {
      const gcEntry = {
        name: 'gc',
        duration: 60,
        startTime: Date.now(),
        entryType: 'measure',
      } as PerformanceEntry;
      
      optimizer['analyzeGCPattern'](gcEntry);
      
      const recommendations = optimizer.generateRecommendations();
      const gcRec = recommendations.find(r => r.id === 'gc-pressure');
      
      expect(gcRec).toBeDefined();


  describe('Route Prediction', () => {
    it('should predict next page based on current route', () => {
      const nextPage = optimizer['predictNextPage']('/dashboard');
      expect(nextPage).toBe('/analytics');

    it('should return null for unknown routes', () => {
      const nextPage = optimizer['predictNextPage']('/unknown');
      expect(nextPage).toBeNull();


  describe('Memory Leak Detection', () => {
    it('should create memory leak detector', () => {
      const detector = optimizer['memoryLeakDetector'];
      expect(detector).toBeDefined();

    it('should start and stop memory monitoring', () => {
      const detector = optimizer['memoryLeakDetector'];
      
      detector.start();
      expect(detector['monitoring']).toBe(true);
      
      detector.stop();
      expect(detector['monitoring']).toBe(false);

    it('should detect memory growth trends', () => {
      const detector = optimizer['memoryLeakDetector'];
      
      // Simulate consistent memory growth
      detector['memorySnapshots'] = [100, 110, 120, 130, 140];
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      detector['analyzeMemoryTrend']();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Potential memory leak detected')
      );
      
      consoleSpy.mockRestore();


  describe('Error Handling', () => {
    it('should handle missing performance.memory gracefully', () => {
      const originalMemory = global.performance.memory;
      delete (global.performance as any).memory;
      
      expect(() => {
        optimizer['detectMemoryLeaks']();
      }).not.toThrow();
      
      global.performance.memory = originalMemory;

    it('should handle service worker registration failure', async () => {
      const originalServiceWorker = global.navigator.serviceWorker;
      global.navigator.serviceWorker.register = vi.fn(() => Promise.reject(new Error('Failed')));
      
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      await optimizer['setupServiceWorkerCaching']();
      
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
      
      global.navigator.serviceWorker = originalServiceWorker;

    it('should handle fetch errors when checking image existence', async () => {
      (global.fetch as Mock).mockRejectedValue(new Error('Network error'));
      
      const exists = await optimizer['checkImageExists']('test.webp');
      expect(exists).toBe(false);


  describe('Cleanup', () => {
    it('should cleanup observers on destroy', () => {
      const disconnectSpy = vi.fn();
      optimizer['observers'] = [{ disconnect: disconnectSpy } as any];
      
      optimizer.destroy();
      
      expect(disconnectSpy).toHaveBeenCalled();
      expect(optimizer['observers']).toHaveLength(0);

    it('should stop memory leak detector on destroy', () => {
      const stopSpy = vi.spyOn(optimizer['memoryLeakDetector'], 'stop');
      
      optimizer.destroy();
      
      expect(stopSpy).toHaveBeenCalled();


