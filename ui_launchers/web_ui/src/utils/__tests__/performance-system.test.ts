import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { performanceMonitor } from '../performance-monitor';
import { bundleAnalyzer } from '../bundle-analyzer';
import { animationPerformance } from '../animation-performance';

// Mock Performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByType: vi.fn(() => []),
  getEntriesByName: vi.fn(() => []),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
  observer: null as PerformanceObserver | null,
};

Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true,

// Mock PerformanceObserver
global.PerformanceObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => []),
}));

// Mock Web Vitals
vi.mock('web-vitals', () => ({
  getCLS: vi.fn((callback) => callback({ name: 'CLS', value: 0.1 })),
  getFID: vi.fn((callback) => callback({ name: 'FID', value: 50 })),
  getFCP: vi.fn((callback) => callback({ name: 'FCP', value: 1200 })),
  getLCP: vi.fn((callback) => callback({ name: 'LCP', value: 2000 })),
  getTTFB: vi.fn((callback) => callback({ name: 'TTFB', value: 300 })),
}));

describe('Performance System', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  afterEach(() => {
    vi.restoreAllMocks();

  describe('Performance Monitor', () => {
    it('should initialize performance monitoring', () => {
      performanceMonitor.init();
      
      expect(PerformanceObserver).toHaveBeenCalled();

    it('should track Core Web Vitals', async () => {
      const vitalsCallback = vi.fn();
      
      performanceMonitor.onVitals(vitalsCallback);
      performanceMonitor.init();
      
      // Wait for vitals to be collected
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(vitalsCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          CLS: expect.any(Number),
          FID: expect.any(Number),
          FCP: expect.any(Number),
          LCP: expect.any(Number),
          TTFB: expect.any(Number),
        })
      );

    it('should measure custom performance metrics', () => {
      performanceMonitor.startMeasure('component-render');
      performanceMonitor.endMeasure('component-render');
      
      expect(mockPerformance.mark).toHaveBeenCalledWith('component-render-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('component-render-end');
      expect(mockPerformance.measure).toHaveBeenCalledWith(
        'component-render',
        'component-render-start',
        'component-render-end'
      );

    it('should track navigation timing', () => {
      // Mock navigation timing
      Object.defineProperty(performance, 'navigation', {
        value: {
          type: 1, // TYPE_RELOAD
        },
        writable: true,

      Object.defineProperty(performance, 'timing', {
        value: {
          navigationStart: 1000,
          domContentLoadedEventEnd: 2000,
          loadEventEnd: 3000,
        },
        writable: true,

      const timing = performanceMonitor.getNavigationTiming();
      
      expect(timing).toEqual({
        domContentLoaded: 1000,
        loadComplete: 2000,
        navigationType: 'reload',


    it('should track resource loading performance', () => {
      const mockResources = [
        {
          name: 'https://example.com/script.js',
          entryType: 'resource',
          startTime: 100,
          responseEnd: 300,
          transferSize: 50000,
        },
        {
          name: 'https://example.com/style.css',
          entryType: 'resource',
          startTime: 150,
          responseEnd: 250,
          transferSize: 20000,
        },
      ];

      mockPerformance.getEntriesByType.mockReturnValue(mockResources);

      const resources = performanceMonitor.getResourceTiming();
      
      expect(resources).toHaveLength(2);
      expect(resources[0]).toEqual({
        name: 'https://example.com/script.js',
        duration: 200,
        size: 50000,


    it('should detect performance issues', () => {
      const issues = performanceMonitor.detectIssues({
        CLS: 0.3, // Poor
        FID: 200, // Poor
        FCP: 4000, // Poor
        LCP: 5000, // Poor
        TTFB: 1000, // Poor

      expect(issues).toContain('High Cumulative Layout Shift');
      expect(issues).toContain('Slow First Input Delay');
      expect(issues).toContain('Slow First Contentful Paint');
      expect(issues).toContain('Slow Largest Contentful Paint');
      expect(issues).toContain('Slow Time to First Byte');

    it('should generate performance report', () => {
      const mockVitals = {
        CLS: 0.1,
        FID: 50,
        FCP: 1200,
        LCP: 2000,
        TTFB: 300,
      };

      const report = performanceMonitor.generateReport(mockVitals);
      
      expect(report).toEqual({
        vitals: mockVitals,
        grade: 'Good',
        issues: [],
        recommendations: expect.any(Array),
        timestamp: expect.any(Number),


    it('should handle performance budget alerts', () => {
      const alertCallback = vi.fn();
      
      performanceMonitor.setBudget({
        LCP: 2500,
        FID: 100,
        CLS: 0.1,

      performanceMonitor.onBudgetExceeded(alertCallback);
      
      // Simulate budget exceeded
      performanceMonitor.checkBudget({
        LCP: 3000, // Exceeds budget
        FID: 50,
        CLS: 0.05,

      expect(alertCallback).toHaveBeenCalledWith({
        metric: 'LCP',
        value: 3000,
        budget: 2500,
        exceeded: 500,



  describe('Bundle Analyzer', () => {
    it('should analyze bundle composition', () => {
      const mockStats = {
        chunks: [
          {
            id: 'main',
            size: 100000,
            modules: [
              { name: 'react', size: 40000 },
              { name: 'lodash', size: 30000 },
              { name: './src/app.js', size: 30000 },
            ],
          },
        ],
      };

      const analysis = bundleAnalyzer.analyze(mockStats);
      
      expect(analysis).toEqual({
        totalSize: 100000,
        chunks: expect.any(Array),
        largestModules: expect.any(Array),
        duplicates: expect.any(Array),
        recommendations: expect.any(Array),


    it('should detect duplicate modules', () => {
      const mockStats = {
        chunks: [
          {
            id: 'main',
            modules: [
              { name: 'lodash', size: 30000 },
              { name: 'node_modules/lodash/index.js', size: 30000 },
            ],
          },
          {
            id: 'vendor',
            modules: [
              { name: 'lodash', size: 30000 },
            ],
          },
        ],
      };

      const duplicates = bundleAnalyzer.findDuplicates(mockStats);
      
      expect(duplicates).toContainEqual({
        module: 'lodash',
        occurrences: 3,
        totalSize: 90000,


    it('should suggest optimizations', () => {
      const analysis = {
        totalSize: 500000, // Large bundle
        largestModules: [
          { name: 'lodash', size: 100000 },
          { name: 'moment', size: 80000 },
        ],
        duplicates: [
          { module: 'react', occurrences: 2 },
        ],
      };

      const recommendations = bundleAnalyzer.getRecommendations(analysis);
      
      expect(recommendations).toContain('Consider code splitting for large bundle');
      expect(recommendations).toContain('Replace lodash with tree-shakable alternatives');
      expect(recommendations).toContain('Deduplicate react module');

    it('should track bundle size over time', () => {
      bundleAnalyzer.recordSize('main', 100000);
      bundleAnalyzer.recordSize('vendor', 200000);
      
      const history = bundleAnalyzer.getSizeHistory();
      
      expect(history).toEqual({
        main: [{ size: 100000, timestamp: expect.any(Number) }],
        vendor: [{ size: 200000, timestamp: expect.any(Number) }],


    it('should detect size regressions', () => {
      bundleAnalyzer.recordSize('main', 100000);
      bundleAnalyzer.recordSize('main', 150000); // 50% increase
      
      const regressions = bundleAnalyzer.detectRegressions();
      
      expect(regressions).toContainEqual({
        chunk: 'main',
        previousSize: 100000,
        currentSize: 150000,
        increase: 50000,
        percentIncrease: 50,



  describe('Animation Performance', () => {
    it('should monitor frame rate', () => {
      const frameCallback = vi.fn();
      
      animationPerformance.startMonitoring(frameCallback);
      
      // Simulate animation frames
      const mockFrames = [
        { timestamp: 0 },
        { timestamp: 16.67 }, // 60fps
        { timestamp: 33.33 },
        { timestamp: 50 },
      ];

      mockFrames.forEach(frame => {
        animationPerformance.recordFrame(frame.timestamp);

      const fps = animationPerformance.getCurrentFPS();
      expect(fps).toBeCloseTo(60, 1);

    it('should detect frame drops', () => {
      const dropCallback = vi.fn();
      
      animationPerformance.onFrameDrop(dropCallback);
      
      // Simulate frame drop (>16.67ms between frames)
      animationPerformance.recordFrame(0);
      animationPerformance.recordFrame(50); // 50ms gap = frame drop
      
      expect(dropCallback).toHaveBeenCalledWith({
        expectedTime: 16.67,
        actualTime: 50,
        droppedFrames: 2,


    it('should measure animation smoothness', () => {
      const frames = [0, 16.67, 33.33, 50, 66.67, 83.33, 100];
      
      frames.forEach(timestamp => {
        animationPerformance.recordFrame(timestamp);

      const smoothness = animationPerformance.getSmoothness();
      
      expect(smoothness).toEqual({
        averageFPS: expect.any(Number),
        frameDrops: expect.any(Number),
        jankScore: expect.any(Number),
        smoothnessScore: expect.any(Number),


    it('should optimize animation performance', () => {
      const element = document.createElement('div');
      
      animationPerformance.optimizeElement(element);
      
      expect(element.style.willChange).toBe('transform, opacity');
      expect(element.style.transform).toBe('translateZ(0)');

    it('should provide performance recommendations', () => {
      const metrics = {
        averageFPS: 30, // Low FPS
        frameDrops: 10,
        jankScore: 0.8, // High jank
      };

      const recommendations = animationPerformance.getRecommendations(metrics);
      
      expect(recommendations).toContain('Use transform and opacity for animations');
      expect(recommendations).toContain('Reduce animation complexity');
      expect(recommendations).toContain('Consider using will-change property');

    it('should handle reduced motion preferences', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        value: vi.fn().mockReturnValue({
          matches: true, // prefers-reduced-motion: reduce
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
        }),

      const shouldAnimate = animationPerformance.shouldAnimate();
      
      expect(shouldAnimate).toBe(false);


  describe('Performance Integration', () => {
    it('should coordinate all performance systems', () => {
      const performanceData = {
        vitals: { LCP: 2000, FID: 50, CLS: 0.1 },
        bundle: { totalSize: 300000 },
        animation: { averageFPS: 55 },
      };

      const overallScore = performanceMonitor.calculateOverallScore(performanceData);
      
      expect(overallScore).toEqual({
        score: expect.any(Number),
        grade: expect.any(String),
        breakdown: {
          vitals: expect.any(Number),
          bundle: expect.any(Number),
          animation: expect.any(Number),
        },


    it('should generate comprehensive performance report', () => {
      const report = performanceMonitor.generateComprehensiveReport();
      
      expect(report).toEqual({
        timestamp: expect.any(Number),
        vitals: expect.any(Object),
        bundle: expect.any(Object),
        animation: expect.any(Object),
        issues: expect.any(Array),
        recommendations: expect.any(Array),
        score: expect.any(Number),


    it('should handle performance monitoring lifecycle', () => {
      performanceMonitor.start();
      
      expect(performanceMonitor.isMonitoring()).toBe(true);
      
      performanceMonitor.stop();
      
      expect(performanceMonitor.isMonitoring()).toBe(false);


  describe('Error Handling', () => {
    it('should handle missing Performance API gracefully', () => {
      const originalPerformance = global.performance;
      // @ts-expect-error - Testing missing API
      global.performance = undefined;
      
      expect(() => {
        performanceMonitor.init();
      }).not.toThrow();
      
      global.performance = originalPerformance;

    it('should handle PerformanceObserver errors', () => {
      const mockObserver = {
        observe: vi.fn().mockImplementation(() => {
          throw new Error('Observer error');
        }),
        disconnect: vi.fn(),
      };
      
      global.PerformanceObserver = vi.fn().mockReturnValue(mockObserver);
      
      expect(() => {
        performanceMonitor.init();
      }).not.toThrow();

    it('should provide fallback metrics when APIs are unavailable', () => {
      const originalPerformance = global.performance;
      // @ts-expect-error - Testing fallback
      global.performance = { now: () => Date.now() };
      
      const timing = performanceMonitor.getNavigationTiming();
      
      expect(timing).toEqual({
        domContentLoaded: 0,
        loadComplete: 0,
        navigationType: 'unknown',

      global.performance = originalPerformance;


