import { describe, it, expect } from 'vitest';
import {  BundleAnalyzer, DEFAULT_BUNDLE_BUDGETS, BUNDLE_BUDGETS, createBundleAnalyzer } from '../bundle-analyzer';

describe('BundleAnalyzer', () => {
  const mockStats = {
    totalSize: 200 * 1024, // 200KB
    gzippedSize: 60 * 1024, // 60KB
    chunks: [
      {
        name: 'main',
        size: 80 * 1024, // 80KB
        files: ['main.js'],
        modules: ['src/app.tsx', 'src/components/ui.tsx'],
      },
      {
        name: 'vendor',
        size: 120 * 1024, // 120KB - exceeds default chunk budget
        files: ['vendor.js'],
        modules: ['node_modules/react', 'node_modules/lodash'],
      },
    ],
    assets: [
      {
        name: 'main.js',
        size: 80 * 1024,
        type: 'js' as const,
        gzippedSize: 25 * 1024,
      },
      {
        name: 'vendor.js',
        size: 120 * 1024, // Exceeds default asset budget
        type: 'js' as const,
        gzippedSize: 35 * 1024,
      },
    ],
    modules: [
      {
        name: 'src/app.tsx',
        size: 15 * 1024,
        chunks: ['main'],
        reasons: ['entry point'],
      },
      {
        name: 'node_modules/lodash',
        size: 70 * 1024, // Large module
        chunks: ['vendor'],
        reasons: ['imported by src/utils.ts'],
      },
    ],
  };

  describe('analyzeBundleStats', () => {
    it('should analyze bundle stats without violations', () => {
      const smallStats = {
        ...mockStats,
        totalSize: 100 * 1024, // 100KB - within budget
        chunks: [
          {
            name: 'main',
            size: 50 * 1024, // 50KB - within budget
            files: ['main.js'],
            modules: ['src/app.tsx'],
          },
        ],
        assets: [
          {
            name: 'main.js',
            size: 30 * 1024, // 30KB - within budget
            type: 'js' as const,
          },
        ],
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(smallStats);

      expect(result.violations).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
      expect(result.score).toBeGreaterThan(90);

    it('should detect bundle size violations', () => {
      const largeStats = {
        ...mockStats,
        totalSize: 300 * 1024, // 300KB - exceeds 250KB budget
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(largeStats);

      expect(result.violations).toHaveLength(1);
      expect(result.violations[0].type).toBe('bundle-size');
      expect(result.violations[0].severity).toBe('error');
      expect(result.violations[0].actual).toBe(300 * 1024);
      expect(result.violations[0].budget).toBe(250 * 1024);

    it('should detect chunk size violations', () => {
      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(mockStats);

      const chunkViolations = result.violations.filter(v => v.type === 'chunk-size');
      expect(chunkViolations).toHaveLength(1);
      expect(chunkViolations[0].target).toBe('vendor');
      expect(chunkViolations[0].actual).toBe(120 * 1024);

    it('should detect asset size violations', () => {
      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(mockStats);

      const assetViolations = result.violations.filter(v => v.type === 'asset-size');
      expect(assetViolations).toHaveLength(1);
      expect(assetViolations[0].target).toBe('vendor.js');
      expect(assetViolations[0].actual).toBe(120 * 1024);

    it('should generate warnings for approaching budget limits', () => {
      const warningStats = {
        ...mockStats,
        totalSize: 220 * 1024, // 88% of 250KB budget - should trigger warning
        chunks: [
          {
            name: 'main',
            size: 85 * 1024, // 85% of 100KB budget - should trigger warning
            files: ['main.js'],
            modules: ['src/app.tsx'],
          },
        ],
        assets: [
          {
            name: 'main.js',
            size: 42 * 1024, // 84% of 50KB budget - should trigger warning
            type: 'js' as const,
          },
        ],
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(warningStats);

      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.every(w => w.severity === 'warning')).toBe(true);

    it('should provide recommendations', () => {
      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(mockStats);

      expect(result.recommendations).toBeInstanceOf(Array);
      expect(result.recommendations.length).toBeGreaterThan(0);
      expect(result.recommendations.some(r => r.includes('code splitting'))).toBe(true);

    it('should calculate performance score', () => {
      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(mockStats);

      expect(result.score).toBeGreaterThanOrEqual(0);
      expect(result.score).toBeLessThanOrEqual(100);
      
      // Should have lower score due to violations
      expect(result.score).toBeLessThan(80);


  describe('custom budgets', () => {
    it('should use mobile budgets', () => {
      const mobileAnalyzer = createBundleAnalyzer('mobile');
      const result = mobileAnalyzer.analyzeBundleStats(mockStats);

      // 200KB should exceed mobile budget of 150KB
      const bundleViolations = result.violations.filter(v => v.type === 'bundle-size');
      expect(bundleViolations).toHaveLength(1);
      expect(bundleViolations[0].budget).toBe(BUNDLE_BUDGETS.mobile.maxBundleSize);

    it('should use desktop budgets', () => {
      const desktopAnalyzer = createBundleAnalyzer('desktop');
      const result = desktopAnalyzer.analyzeBundleStats(mockStats);

      // 200KB should be within desktop budget of 300KB
      const bundleViolations = result.violations.filter(v => v.type === 'bundle-size');
      expect(bundleViolations).toHaveLength(0);

    it('should use enterprise budgets', () => {
      const enterpriseAnalyzer = createBundleAnalyzer('enterprise');
      const result = enterpriseAnalyzer.analyzeBundleStats(mockStats);

      // 200KB should be well within enterprise budget of 500KB
      const bundleViolations = result.violations.filter(v => v.type === 'bundle-size');
      expect(bundleViolations).toHaveLength(0);


  describe('edge cases', () => {
    it('should handle empty stats', () => {
      const emptyStats = {
        totalSize: 0,
        gzippedSize: 0,
        chunks: [],
        assets: [],
        modules: [],
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(emptyStats);

      expect(result.violations).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
      expect(result.score).toBe(100);

    it('should handle very large bundles', () => {
      const hugeStats = {
        ...mockStats,
        totalSize: 1000 * 1024, // 1MB
        chunks: [
          {
            name: 'huge-chunk',
            size: 500 * 1024, // 500KB
            files: ['huge.js'],
            modules: ['huge-module'],
          },
        ],
        assets: [
          {
            name: 'huge.js',
            size: 500 * 1024,
            type: 'js' as const,
          },
        ],
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(hugeStats);

      expect(result.violations.length).toBeGreaterThan(0);
      expect(result.score).toBeLessThan(50);

    it('should provide good gzip ratio bonus', () => {
      const goodGzipStats = {
        ...mockStats,
        totalSize: 100 * 1024,
        gzippedSize: 25 * 1024, // 25% ratio - very good
        chunks: [
          {
            name: 'main',
            size: 50 * 1024,
            files: ['main.js'],
            modules: ['src/app.tsx'],
          },
        ],
        assets: [
          {
            name: 'main.js',
            size: 30 * 1024,
            type: 'js' as const,
          },
        ],
      };

      const analyzer = new BundleAnalyzer();
      const result = analyzer.analyzeBundleStats(goodGzipStats);

      expect(result.score).toBeGreaterThan(95);


