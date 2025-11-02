/**
 * Performance Profiler Tests
 * Tests for performance profiling and bottleneck detection functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { PerformanceProfiler } from '../performance-profiler';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByType: vi.fn(() => []),
};

// Mock PerformanceObserver
class MockPerformanceObserver {
  private callback: (list: any) => void;
  
  constructor(callback: (list: any) => void) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
}

// Mock MutationObserver
class MockMutationObserver {
  private callback: (mutations: any[]) => void;
  
  constructor(callback: (mutations: any[]) => void) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
}

global.performance = mockPerformance as any;
global.PerformanceObserver = MockPerformanceObserver as any;
global.MutationObserver = MockMutationObserver as any;
global.document = { body: {} } as any;

describe('PerformanceProfiler', () => {
  let profiler: PerformanceProfiler;

  beforeEach(() => {
    vi.clearAllMocks();
    profiler = new PerformanceProfiler();

  afterEach(() => {
    profiler.destroy();

  describe('Initialization', () => {
    it('should initialize profiler', () => {
      expect(profiler).toBeDefined();

    it('should be enabled by default', () => {
      expect(profiler['isEnabled']).toBe(true);


  describe('Profile Management', () => {
    it('should start a profile', () => {
      const id = profiler.startProfile('test-function', 'function', { test: true });
      
      expect(id).toBeTruthy();
      expect(profiler['activeProfiles'].has(id)).toBe(true);
      expect(mockPerformance.mark).toHaveBeenCalledWith('test-function-start');

    it('should end a profile', () => {
      const id = profiler.startProfile('test-function');
      const profile = profiler.endProfile(id);
      
      expect(profile).toBeDefined();
      expect(profile?.name).toBe('test-function');
      expect(profile?.duration).toBeGreaterThanOrEqual(0);
      expect(profiler['activeProfiles'].has(id)).toBe(false);
      expect(mockPerformance.mark).toHaveBeenCalledWith('test-function-end');
      expect(mockPerformance.measure).toHaveBeenCalledWith('test-function', 'test-function-start', 'test-function-end');

    it('should return null when ending non-existent profile', () => {
      const profile = profiler.endProfile('non-existent');
      expect(profile).toBeNull();

    it('should not start profile when disabled', () => {
      profiler.setEnabled(false);
      const id = profiler.startProfile('test-function');
      expect(id).toBe('');

    it('should not end profile when disabled', () => {
      const id = profiler.startProfile('test-function');
      profiler.setEnabled(false);
      const profile = profiler.endProfile(id);
      expect(profile).toBeNull();


  describe('Function Profiling', () => {
    it('should profile synchronous function', () => {
      const testFn = vi.fn(() => 'result');
      const result = profiler.profileFunction('sync-test', testFn, { sync: true });
      
      expect(result).toBe('result');
      expect(testFn).toHaveBeenCalled();
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toBe('sync-test');
      expect(profiles[0].type).toBe('function');

    it('should profile asynchronous function', async () => {
      const testFn = vi.fn(async () => 'async-result');
      const result = await profiler.profileAsync('async-test', testFn, { async: true });
      
      expect(result).toBe('async-result');
      expect(testFn).toHaveBeenCalled();
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toBe('async-test');

    it('should handle function errors gracefully', () => {
      const errorFn = vi.fn(() => { throw new Error('Test error'); });
      
      expect(() => {
        profiler.profileFunction('error-test', errorFn);
      }).toThrow('Test error');
      
      // Profile should still be recorded
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);

    it('should handle async function errors gracefully', async () => {
      const errorFn = vi.fn(async () => { throw new Error('Async error'); });
      
      await expect(
        profiler.profileAsync('async-error-test', errorFn)
      ).rejects.toThrow('Async error');
      
      // Profile should still be recorded
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);


  describe('Bottleneck Detection', () => {
    it('should detect slow operations as bottlenecks', () => {
      const id = profiler.startProfile('slow-operation');
      
      // Mock slow operation
      const profile = profiler['activeProfiles'].get(id);
      if (profile) {
        profile.startTime = performance.now() - 2000; // 2 seconds ago
      }
      
      profiler.endProfile(id);
      
      const profiles = profiler.getProfiles();
      expect(profiles[0].bottleneck).toBe(true);
      expect(profiles[0].severity).toBe('medium');
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBeGreaterThan(0);

    it('should create bottleneck for long tasks', () => {
      const longTaskEntry = {
        name: 'longtask',
        duration: 200,
        startTime: performance.now(),
        entryType: 'longtask',
      };
      
      profiler['detectLongTaskBottleneck'](longTaskEntry);
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBe(1);
      expect(bottlenecks[0].type).toBe('javascript');
      expect(bottlenecks[0].description).toContain('Long running task');

    it('should not create duplicate bottlenecks', () => {
      const bottleneckData = {
        type: 'javascript' as const,
        location: 'test-location',
        description: 'Test bottleneck',
        impact: 50,
        duration: 1000,
        suggestions: ['Test suggestion'],
      };
      
      profiler['createBottleneck'](bottleneckData);
      profiler['createBottleneck'](bottleneckData);
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBe(1);
      expect(bottlenecks[0].frequency).toBe(2);


  describe('Navigation Timing Analysis', () => {
    it('should analyze navigation timing', () => {
      const navEntry = {
        navigationStart: 0,
        responseStart: 1200, // Slow response
        domContentLoadedEventStart: 2000,
        domContentLoadedEventEnd: 2600, // Slow DOM loading
        domComplete: 3000,
        loadEventEnd: 3500,
      } as PerformanceNavigationTiming;
      
      profiler['analyzeNavigationTiming'](navEntry);
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toBe('Page Navigation');
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBeGreaterThan(0);
      expect(bottlenecks.some(b => b.type === 'network')).toBe(true);
      expect(bottlenecks.some(b => b.type === 'javascript')).toBe(true);


  describe('Resource Timing Analysis', () => {
    it('should analyze resource timing', () => {
      const resourceEntry = {
        name: 'https://example.com/large-script.js',
        startTime: 0,
        responseEnd: 2500, // Slow resource
        duration: 2500,
        transferSize: 2 * 1024 * 1024, // 2MB - large resource
        decodedBodySize: 2 * 1024 * 1024,
        domainLookupStart: 0,
        domainLookupEnd: 50,
        connectStart: 50,
        connectEnd: 100,
        requestStart: 100,
        responseStart: 1000,
      } as PerformanceResourceTiming;
      
      profiler['analyzeResourceTiming'](resourceEntry);
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toContain('large-script.js');
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBeGreaterThan(0);
      expect(bottlenecks.some(b => b.description.includes('Slow resource loading'))).toBe(true);
      expect(bottlenecks.some(b => b.description.includes('Large resource size') || b.description.includes('Slow resource loading'))).toBe(true);


  describe('Paint Timing Analysis', () => {
    it('should analyze paint timing', () => {
      const paintEntry = {
        name: 'first-contentful-paint',
        startTime: 2000, // Slow FCP
        duration: 0,
        entryType: 'paint',
      } as PerformanceEntry;
      
      profiler['analyzePaintTiming'](paintEntry);
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toBe('Paint: first-contentful-paint');
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks.length).toBe(1);
      expect(bottlenecks[0].type).toBe('render');
      expect(bottlenecks[0].description).toContain('Slow first contentful paint');


  describe('User Timing Capture', () => {
    it('should capture user timing measures', () => {
      const measureEntry = {
        name: 'custom-measure',
        startTime: 100,
        duration: 500,
        entryType: 'measure',
      } as PerformanceEntry;
      
      profiler['captureUserTiming'](measureEntry);
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(1);
      expect(profiles[0].name).toBe('custom-measure');
      expect(profiles[0].metadata.userTiming).toBe(true);

    it('should ignore user timing marks', () => {
      const markEntry = {
        name: 'custom-mark',
        startTime: 100,
        duration: 0,
        entryType: 'mark',
      } as PerformanceEntry;
      
      profiler['captureUserTiming'](markEntry);
      
      const profiles = profiler.getProfiles();
      expect(profiles.length).toBe(0);


  describe('Performance Patterns', () => {
    it('should identify frequent slow API calls pattern', () => {
      // Add multiple slow API profiles
      for (let i = 0; i < 6; i++) {
        profiler['profiles'].push({
          id: `api-${i}`,
          name: `API Call ${i}`,
          startTime: Date.now() - i * 1000,
          endTime: Date.now() - i * 1000 + 1500,
          duration: 1500,
          type: 'api',
          metadata: {},
          children: [],
          bottleneck: true,
          severity: 'medium',

      }
      
      profiler['analyzePerformancePatterns']();
      
      const suggestions = profiler.getOptimizationSuggestions();
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.some(s => s.title.includes('Frequent Slow API Calls') || s.title.includes('API'))).toBe(true);

    it('should identify excessive rendering pattern', () => {
      // Add many render profiles
      for (let i = 0; i < 25; i++) {
        profiler['profiles'].push({
          id: `render-${i}`,
          name: `Render ${i}`,
          startTime: Date.now() - i * 100,
          endTime: Date.now() - i * 100 + 50,
          duration: 50,
          type: 'render',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }
      
      profiler['analyzePerformancePatterns']();
      
      const suggestions = profiler.getOptimizationSuggestions();
      expect(suggestions.some(s => s.title.includes('Excessive Rendering'))).toBe(true);


  describe('Performance Comparison', () => {
    beforeEach(() => {
      // Add baseline profiles
      const baselineTime = Date.now() - 2 * 60 * 60 * 1000; // 2 hours ago
      for (let i = 0; i < 5; i++) {
        profiler['profiles'].push({
          id: `baseline-${i}`,
          name: 'test-function',
          startTime: baselineTime + i * 1000,
          endTime: baselineTime + i * 1000 + 1000,
          duration: 1000,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }
      
      // Add current profiles (faster)
      const currentTime = Date.now() - 30 * 60 * 1000; // 30 minutes ago
      for (let i = 0; i < 5; i++) {
        profiler['profiles'].push({
          id: `current-${i}`,
          name: 'test-function',
          startTime: currentTime + i * 1000,
          endTime: currentTime + i * 1000 + 800,
          duration: 800,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }

    it('should compare performance between time periods', () => {
      const now = Date.now();
      const oneHourAgo = now - 60 * 60 * 1000;
      const twoHoursAgo = now - 2 * 60 * 60 * 1000;
      
      const comparisons = profiler.comparePerformance(twoHoursAgo, oneHourAgo, oneHourAgo, now);
      
      expect(comparisons.length).toBe(1);
      expect(comparisons[0].name).toBe('test-function');
      expect(comparisons[0].improvement).toBeGreaterThan(0); // Should show improvement
      expect(comparisons[0].regression).toBe(false);

    it('should detect performance regression', () => {
      // Add slower current profiles
      const currentTime = Date.now() - 30 * 60 * 1000;
      for (let i = 0; i < 5; i++) {
        profiler['profiles'].push({
          id: `slow-current-${i}`,
          name: 'regression-function',
          startTime: currentTime + i * 1000,
          endTime: currentTime + i * 1000 + 1500,
          duration: 1500,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: true,
          severity: 'medium',

      }
      
      // Add faster baseline profiles
      const baselineTime = Date.now() - 2 * 60 * 60 * 1000;
      for (let i = 0; i < 5; i++) {
        profiler['profiles'].push({
          id: `fast-baseline-${i}`,
          name: 'regression-function',
          startTime: baselineTime + i * 1000,
          endTime: baselineTime + i * 1000 + 800,
          duration: 800,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }
      
      const now = Date.now();
      const oneHourAgo = now - 60 * 60 * 1000;
      const twoHoursAgo = now - 2 * 60 * 60 * 1000;
      
      const comparisons = profiler.comparePerformance(twoHoursAgo, oneHourAgo, oneHourAgo, now);
      
      const regressionComparison = comparisons.find(c => c.name === 'regression-function');
      expect(regressionComparison).toBeDefined();
      expect(regressionComparison?.regression).toBe(true);
      expect(regressionComparison?.improvement).toBeLessThan(-5);


  describe('Regression Tests', () => {
    it('should add regression test', () => {
      profiler.addRegressionTest('test-function', 1000, 20);
      
      const tests = profiler.getRegressionTests();
      expect(tests.length).toBe(1);
      expect(tests[0].name).toBe('test-function');
      expect(tests[0].baseline).toBe(1000);
      expect(tests[0].threshold).toBe(20);
      expect(tests[0].status).toBe('pass');

    it('should update regression test status', () => {
      profiler.addRegressionTest('test-function', 1000, 20);
      
      // Add profiles that exceed threshold
      for (let i = 0; i < 3; i++) {
        profiler['profiles'].push({
          id: `regression-${i}`,
          name: 'test-function',
          startTime: Date.now() - i * 1000,
          endTime: Date.now() - i * 1000 + 1300, // 30% slower than baseline
          duration: 1300,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: true,
          severity: 'medium',

      }
      
      profiler['updateRegressionTests']();
      
      const tests = profiler.getRegressionTests();
      expect(tests[0].status).toBe('fail');
      expect(tests[0].currentValue).toBeGreaterThan(1000);


  describe('Data Management', () => {
    it('should get profiles with limit', () => {
      // Add multiple profiles
      for (let i = 0; i < 10; i++) {
        profiler['profiles'].push({
          id: `profile-${i}`,
          name: `Function ${i}`,
          startTime: Date.now() - i * 1000,
          endTime: Date.now() - i * 1000 + 100,
          duration: 100,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }
      
      const allProfiles = profiler.getProfiles();
      expect(allProfiles.length).toBe(10);
      
      const limitedProfiles = profiler.getProfiles(5);
      expect(limitedProfiles.length).toBe(5);

    it('should sort bottlenecks by priority', () => {
      profiler['bottlenecks'] = [
        {
          id: '1',
          type: 'javascript',
          location: 'low',
          description: 'Low priority',
          impact: 20,
          frequency: 1,
          duration: 100,
          suggestions: [],
          priority: 'low',
          detectedAt: Date.now(),
        },
        {
          id: '2',
          type: 'javascript',
          location: 'critical',
          description: 'Critical priority',
          impact: 90,
          frequency: 1,
          duration: 1000,
          suggestions: [],
          priority: 'critical',
          detectedAt: Date.now(),
        },
        {
          id: '3',
          type: 'javascript',
          location: 'medium',
          description: 'Medium priority',
          impact: 50,
          frequency: 1,
          duration: 500,
          suggestions: [],
          priority: 'medium',
          detectedAt: Date.now(),
        },
      ];
      
      const bottlenecks = profiler.getBottlenecks();
      expect(bottlenecks[0].priority).toBe('critical');
      expect(bottlenecks[1].priority).toBe('medium');
      expect(bottlenecks[2].priority).toBe('low');

    it('should sort suggestions by impact', () => {
      profiler['suggestions'] = [
        {
          id: '1',
          type: 'code',
          title: 'Low impact',
          description: 'Low impact suggestion',
          impact: 'low',
          effort: 'low',
          implementation: 'Test',
          estimatedGain: 10,
          confidence: 50,
        },
        {
          id: '2',
          type: 'code',
          title: 'High impact',
          description: 'High impact suggestion',
          impact: 'high',
          effort: 'medium',
          implementation: 'Test',
          estimatedGain: 50,
          confidence: 80,
        },
      ];
      
      const suggestions = profiler.getOptimizationSuggestions();
      expect(suggestions[0].impact).toBe('high');
      expect(suggestions[1].impact).toBe('low');

    it('should limit profiles to prevent memory leaks', () => {
      // Add many profiles
      for (let i = 0; i < 1200; i++) {
        profiler['profiles'].push({
          id: `profile-${i}`,
          name: `Function ${i}`,
          startTime: Date.now() - i * 1000,
          endTime: Date.now() - i * 1000 + 100,
          duration: 100,
          type: 'function',
          metadata: {},
          children: [],
          bottleneck: false,
          severity: 'low',

      }
      
      // Trigger profile end which should clean up
      const id = profiler.startProfile('cleanup-test');
      profiler.endProfile(id);
      
      expect(profiler['profiles'].length).toBeLessThanOrEqual(500);

    it('should clear all data', () => {
      profiler.startProfile('test');
      profiler['bottlenecks'].push({
        id: '1',
        type: 'javascript',
        location: 'test',
        description: 'test',
        impact: 50,
        frequency: 1,
        duration: 100,
        suggestions: [],
        priority: 'medium',
        detectedAt: Date.now(),

      profiler.clear();
      
      expect(profiler.getProfiles()).toHaveLength(0);
      expect(profiler.getBottlenecks()).toHaveLength(0);
      expect(profiler['activeProfiles'].size).toBe(0);


  describe('Enable/Disable', () => {
    it('should enable and disable profiler', () => {
      expect(profiler['isEnabled']).toBe(true);
      
      profiler.setEnabled(false);
      expect(profiler['isEnabled']).toBe(false);
      
      profiler.setEnabled(true);
      expect(profiler['isEnabled']).toBe(true);


  describe('Cleanup', () => {
    it('should cleanup observers on destroy', () => {
      const disconnectSpy = vi.fn();
      profiler['observers'] = [{ disconnect: disconnectSpy } as any];
      
      profiler.destroy();
      
      expect(disconnectSpy).toHaveBeenCalled();
      expect(profiler['observers']).toHaveLength(0);


