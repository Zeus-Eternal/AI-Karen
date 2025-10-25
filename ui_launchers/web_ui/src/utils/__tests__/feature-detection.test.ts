import { describe, it, expect, beforeEach, vi } from 'vitest';
import { featureDetection } from '../feature-detection';

// Mock CSS.supports
const mockCSSSupports = vi.fn();
global.CSS = {
  supports: mockCSSSupports,
} as any;

// Mock window APIs
const mockWindow = {
  IntersectionObserver: vi.fn(),
  ResizeObserver: vi.fn(),
  MutationObserver: vi.fn(),
  Worker: vi.fn(),
  matchMedia: vi.fn(),
  navigator: {
    serviceWorker: {},
    maxTouchPoints: 0,
    onLine: true,
  },
  localStorage: {
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
  sessionStorage: {
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
  performance: {
    timing: {},
  },
  requestAnimationFrame: vi.fn(),
  requestIdleCallback: vi.fn(),
} as any;

Object.assign(global, { window: mockWindow });

describe('FeatureDetectionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCSSSupports.mockReturnValue(true);
  });

  describe('CSS Feature Detection', () => {
    it('should detect CSS custom properties support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        return property === 'color' && value === 'var(--test)';
      });

      const features = featureDetection.getFeatures();
      expect(features.cssCustomProperties).toBe(true);
      expect(mockCSSSupports).toHaveBeenCalledWith('color', 'var(--test)');
    });

    it('should detect CSS Grid support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        return property === 'display' && value === 'grid';
      });

      const features = featureDetection.getFeatures();
      expect(features.cssGrid).toBe(true);
      expect(mockCSSSupports).toHaveBeenCalledWith('display', 'grid');
    });

    it('should detect CSS Flexbox support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        return property === 'display' && value === 'flex';
      });

      const features = featureDetection.getFeatures();
      expect(features.cssFlexbox).toBe(true);
      expect(mockCSSSupports).toHaveBeenCalledWith('display', 'flex');
    });

    it('should detect CSS container queries support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        return property === 'container-type' && value === 'inline-size';
      });

      const features = featureDetection.getFeatures();
      expect(features.cssContainerQueries).toBe(true);
      expect(mockCSSSupports).toHaveBeenCalledWith('container-type', 'inline-size');
    });

    it('should detect CSS clamp support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        return property === 'width' && value === 'clamp(1px, 50%, 100px)';
      });

      const features = featureDetection.getFeatures();
      expect(features.cssClamp).toBe(true);
      expect(mockCSSSupports).toHaveBeenCalledWith('width', 'clamp(1px, 50%, 100px)');
    });
  });

  describe('JavaScript API Detection', () => {
    it('should detect IntersectionObserver support', () => {
      const features = featureDetection.getFeatures();
      expect(features.intersectionObserver).toBe(true);
    });

    it('should detect ResizeObserver support', () => {
      const features = featureDetection.getFeatures();
      expect(features.resizeObserver).toBe(true);
    });

    it('should detect MutationObserver support', () => {
      const features = featureDetection.getFeatures();
      expect(features.mutationObserver).toBe(true);
    });

    it('should detect requestAnimationFrame support', () => {
      const features = featureDetection.getFeatures();
      expect(features.requestAnimationFrame).toBe(true);
    });

    it('should detect requestIdleCallback support', () => {
      const features = featureDetection.getFeatures();
      expect(features.requestIdleCallback).toBe(true);
    });
  });

  describe('Browser Feature Detection', () => {
    it('should detect Web Workers support', () => {
      const features = featureDetection.getFeatures();
      expect(features.webWorkers).toBe(true);
    });

    it('should detect Service Workers support', () => {
      const features = featureDetection.getFeatures();
      expect(features.serviceWorkers).toBe(true);
    });

    it('should detect localStorage support', () => {
      const features = featureDetection.getFeatures();
      expect(features.localStorage).toBe(true);
    });

    it('should detect sessionStorage support', () => {
      const features = featureDetection.getFeatures();
      expect(features.sessionStorage).toBe(true);
    });

    it('should handle localStorage errors gracefully', () => {
      mockWindow.localStorage.setItem.mockImplementation(() => {
        throw new Error('Storage disabled');
      });

      const features = featureDetection.getFeatures();
      expect(features.localStorage).toBe(false);
    });
  });

  describe('Media Feature Detection', () => {
    it('should detect touch events support', () => {
      mockWindow.navigator.maxTouchPoints = 1;
      const features = featureDetection.getFeatures();
      expect(features.touchEvents).toBe(true);
    });

    it('should detect online status support', () => {
      const features = featureDetection.getFeatures();
      expect(features.onlineStatus).toBe(true);
    });
  });

  describe('Accessibility Feature Detection', () => {
    it('should detect reduced motion preference', () => {
      mockWindow.matchMedia.mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
      }));

      const features = featureDetection.getFeatures();
      expect(features.reducedMotion).toBe(true);
    });

    it('should detect high contrast preference', () => {
      mockWindow.matchMedia.mockImplementation((query) => ({
        matches: query === '(prefers-contrast: high)',
      }));

      const features = featureDetection.getFeatures();
      expect(features.highContrast).toBe(true);
    });

    it('should detect forced colors mode', () => {
      mockWindow.matchMedia.mockImplementation((query) => ({
        matches: query === '(forced-colors: active)',
      }));

      const features = featureDetection.getFeatures();
      expect(features.forcedColors).toBe(true);
    });
  });

  describe('Feature Queries', () => {
    it('should check if specific feature is supported', () => {
      expect(featureDetection.hasFeature('cssGrid')).toBe(true);
      expect(featureDetection.hasFeature('cssCustomProperties')).toBe(true);
    });

    it('should check modern CSS support', () => {
      expect(featureDetection.supportsModernCSS()).toBe(true);
    });

    it('should check modern JS support', () => {
      expect(featureDetection.supportsModernJS()).toBe(true);
    });

    it('should check advanced features support', () => {
      mockCSSSupports.mockImplementation((property, value) => {
        if (property === 'container-type' && value === 'inline-size') return true;
        if (property === 'backdrop-filter' && value === 'blur(10px)') return true;
        return false;
      });

      // Mock web animations
      const mockElement = {
        animate: vi.fn(),
      };
      global.document = {
        createElement: () => mockElement,
      } as any;

      expect(featureDetection.supportsAdvancedFeatures()).toBe(true);
    });

    it('should determine optimal image format', () => {
      // This will be 'jpg' initially since image format detection is async
      expect(featureDetection.getImageFormat()).toBe('jpg');
    });

    it('should determine if polyfills are needed', () => {
      // Mock missing features
      delete mockWindow.IntersectionObserver;
      delete mockWindow.localStorage;
      
      expect(featureDetection.shouldUsePolyfills()).toBe(true);
    });
  });

  describe('Callbacks', () => {
    it('should call callbacks when features are ready', () => {
      const callback = vi.fn();
      const unsubscribe = featureDetection.onFeaturesReady(callback);

      expect(callback).toHaveBeenCalledWith(expect.objectContaining({
        cssGrid: expect.any(Boolean),
        cssFlexbox: expect.any(Boolean),
        intersectionObserver: expect.any(Boolean),
      }));

      unsubscribe();
    });

    it('should allow unsubscribing from callbacks', () => {
      const callback = vi.fn();
      const unsubscribe = featureDetection.onFeaturesReady(callback);
      
      callback.mockClear();
      unsubscribe();

      // Trigger feature detection again (this is implementation-specific)
      // The callback should not be called again
      expect(callback).not.toHaveBeenCalled();
    });
  });
});