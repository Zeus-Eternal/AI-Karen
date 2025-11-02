/**
 * Progressive Enhancement System
 * 
 * Provides utilities for implementing progressive enhancement patterns,
 * ensuring the application works across all browsers while providing
 * enhanced experiences for modern browsers.
 */
import React from 'react';
import { featureDetection, FeatureSupport } from './feature-detection';
export interface EnhancementLevel {
  basic: boolean;
  enhanced: boolean;
  advanced: boolean;
}
export interface ProgressiveEnhancementConfig {
  enableAnimations: boolean;
  enableAdvancedCSS: boolean;
  enableModernJS: boolean;
  fallbackStrategy: 'graceful' | 'polyfill' | 'disable';
  performanceThreshold: number;
}
class ProgressiveEnhancementService {
  private config: ProgressiveEnhancementConfig;
  private enhancementLevel: EnhancementLevel;
  private performanceScore: number = 1.0;
  constructor(config: Partial<ProgressiveEnhancementConfig> = {}) {
    this.config = {
      enableAnimations: true,
      enableAdvancedCSS: true,
      enableModernJS: true,
      fallbackStrategy: 'graceful',
      performanceThreshold: 0.7,
      ...config,
    };
    this.enhancementLevel = this.calculateEnhancementLevel();
    this.measurePerformance();
  }
  private calculateEnhancementLevel(): EnhancementLevel {
    const features = featureDetection.getFeatures();
    return {
      basic: this.supportsBasicFeatures(features),
      enhanced: this.supportsEnhancedFeatures(features),
      advanced: this.supportsAdvancedFeatures(features),
    };
  }
  private supportsBasicFeatures(features: FeatureSupport): boolean {
    return features.cssFlexbox && 
           features.localStorage && 
           features.requestAnimationFrame;
  }
  private supportsEnhancedFeatures(features: FeatureSupport): boolean {
    return this.supportsBasicFeatures(features) &&
           features.cssGrid &&
           features.cssCustomProperties &&
           features.intersectionObserver;
  }
  private supportsAdvancedFeatures(features: FeatureSupport): boolean {
    return this.supportsEnhancedFeatures(features) &&
           features.cssContainerQueries &&
           features.webAnimations &&
           features.resizeObserver;
  }
  private async measurePerformance(): Promise<void> {
    if (!featureDetection.hasFeature('performanceTiming')) {
      this.performanceScore = 0.5; // Conservative estimate
      return;
    }
    try {
      // Measure various performance metrics
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      if (navigation) {
        const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
        const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
        // Calculate performance score based on load times
        const avgLoadTime = (loadTime + domContentLoaded) / 2;
        this.performanceScore = Math.max(0.1, Math.min(1.0, 2000 / avgLoadTime));
      }
      // Factor in paint metrics
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint');
      if (fcp && fcp.startTime > 2000) {
        this.performanceScore *= 0.8; // Reduce score for slow FCP
      }
    } catch (error) {
      this.performanceScore = 0.7; // Default conservative score
    }
  }
  // CSS Enhancement Methods
  public getCSSEnhancements(): {
    useGrid: boolean;
    useFlexbox: boolean;
    useCustomProperties: boolean;
    useContainerQueries: boolean;
    useLogicalProperties: boolean;
    useClamp: boolean;
    useBackdropFilter: boolean;
  } {
    const features = featureDetection.getFeatures();
    const shouldEnhance = this.config.enableAdvancedCSS && this.performanceScore >= this.config.performanceThreshold;
    return {
      useGrid: features.cssGrid && (this.enhancementLevel.enhanced || shouldEnhance),
      useFlexbox: features.cssFlexbox, // Always use if available (basic feature)
      useCustomProperties: features.cssCustomProperties && (this.enhancementLevel.enhanced || shouldEnhance),
      useContainerQueries: features.cssContainerQueries && this.enhancementLevel.advanced && shouldEnhance,
      useLogicalProperties: features.cssLogicalProperties && this.enhancementLevel.enhanced && shouldEnhance,
      useClamp: features.cssClamp && this.enhancementLevel.enhanced && shouldEnhance,
      useBackdropFilter: features.cssBackdropFilter && this.enhancementLevel.advanced && shouldEnhance,
    };
  }
  // Animation Enhancement Methods
  public getAnimationEnhancements(): {
    useTransitions: boolean;
    useTransforms: boolean;
    useWebAnimations: boolean;
    useReducedMotion: boolean;
    animationDuration: number;
    animationEasing: string;
  } {
    const features = featureDetection.getFeatures();
    const shouldAnimate = this.config.enableAnimations && 
                         !features.reducedMotion && 
                         this.performanceScore >= this.config.performanceThreshold;
    return {
      useTransitions: shouldAnimate,
      useTransforms: shouldAnimate,
      useWebAnimations: features.webAnimations && this.enhancementLevel.advanced && shouldAnimate,
      useReducedMotion: features.reducedMotion,
      animationDuration: features.reducedMotion ? 0 : (this.performanceScore < 0.5 ? 150 : 250),
      animationEasing: this.enhancementLevel.enhanced ? 'cubic-bezier(0.4, 0, 0.2, 1)' : 'ease-in-out',
    };
  }
  // JavaScript Enhancement Methods
  public getJSEnhancements(): {
    useIntersectionObserver: boolean;
    useResizeObserver: boolean;
    useWebWorkers: boolean;
    useServiceWorkers: boolean;
    useModernAPIs: boolean;
    polyfillsNeeded: string[];
  } {
    const features = featureDetection.getFeatures();
    const shouldEnhance = this.config.enableModernJS && this.performanceScore >= this.config.performanceThreshold;
    const polyfillsNeeded: string[] = [];
    // Determine needed polyfills based on fallback strategy
    if (this.config.fallbackStrategy === 'polyfill') {
      if (!features.intersectionObserver) polyfillsNeeded.push('intersection-observer');
      if (!features.resizeObserver) polyfillsNeeded.push('resize-observer');
      if (!features.requestIdleCallback) polyfillsNeeded.push('request-idle-callback');
    }
    return {
      useIntersectionObserver: features.intersectionObserver || this.config.fallbackStrategy === 'polyfill',
      useResizeObserver: features.resizeObserver || this.config.fallbackStrategy === 'polyfill',
      useWebWorkers: features.webWorkers && this.enhancementLevel.enhanced && shouldEnhance,
      useServiceWorkers: features.serviceWorkers && this.enhancementLevel.advanced && shouldEnhance,
      useModernAPIs: this.enhancementLevel.enhanced && shouldEnhance,
      polyfillsNeeded,
    };
  }
  // Image Enhancement Methods
  public getImageEnhancements(): {
    format: 'avif' | 'webp' | 'jpg';
    useLazyLoading: boolean;
    useResponsiveImages: boolean;
    useImageOptimization: boolean;
  } {
    const features = featureDetection.getFeatures();
    return {
      format: featureDetection.getImageFormat(),
      useLazyLoading: features.intersectionObserver && this.enhancementLevel.enhanced,
      useResponsiveImages: this.enhancementLevel.enhanced,
      useImageOptimization: this.performanceScore < 0.7, // Use optimization for slower devices
    };
  }
  // Layout Enhancement Methods
  public getLayoutEnhancements(): {
    useModernLayout: boolean;
    useContainerQueries: boolean;
    useLogicalProperties: boolean;
    gridSupport: 'full' | 'fallback' | 'none';
    flexboxSupport: 'full' | 'fallback' | 'none';
  } {
    const features = featureDetection.getFeatures();
    const cssEnhancements = this.getCSSEnhancements();
    return {
      useModernLayout: this.enhancementLevel.enhanced,
      useContainerQueries: cssEnhancements.useContainerQueries,
      useLogicalProperties: cssEnhancements.useLogicalProperties,
      gridSupport: features.cssGrid ? 'full' : (this.config.fallbackStrategy === 'graceful' ? 'fallback' : 'none'),
      flexboxSupport: features.cssFlexbox ? 'full' : (this.config.fallbackStrategy === 'graceful' ? 'fallback' : 'none'),
    };
  }
  // Performance Enhancement Methods
  public getPerformanceEnhancements(): {
    useLazyLoading: boolean;
    useCodeSplitting: boolean;
    usePreloading: boolean;
    useCaching: boolean;
    bundleStrategy: 'modern' | 'legacy' | 'universal';
  } {
    return {
      useLazyLoading: this.enhancementLevel.enhanced,
      useCodeSplitting: this.enhancementLevel.enhanced && this.performanceScore >= 0.6,
      usePreloading: this.enhancementLevel.advanced && this.performanceScore >= 0.8,
      useCaching: featureDetection.hasFeature('serviceWorkers') && this.enhancementLevel.advanced,
      bundleStrategy: this.enhancementLevel.advanced ? 'modern' : (this.enhancementLevel.enhanced ? 'universal' : 'legacy'),
    };
  }
  // Accessibility Enhancement Methods
  public getAccessibilityEnhancements(): {
    useReducedMotion: boolean;
    useHighContrast: boolean;
    useForcedColors: boolean;
    enhancedFocus: boolean;
    screenReaderOptimizations: boolean;
  } {
    const features = featureDetection.getFeatures();
    return {
      useReducedMotion: features.reducedMotion,
      useHighContrast: features.highContrast,
      useForcedColors: features.forcedColors,
      enhancedFocus: this.enhancementLevel.enhanced,
      screenReaderOptimizations: this.enhancementLevel.enhanced,
    };
  }
  // Utility Methods
  public getEnhancementLevel(): EnhancementLevel {
    return { ...this.enhancementLevel };
  }
  public getPerformanceScore(): number {
    return this.performanceScore;
  }
  public shouldUseFeature(feature: keyof FeatureSupport, level: keyof EnhancementLevel = 'enhanced'): boolean {
    return featureDetection.hasFeature(feature) && this.enhancementLevel[level];
  }
  public generateCSS(): string {
    const enhancements = this.getCSSEnhancements();
    const animations = this.getAnimationEnhancements();
    const layout = this.getLayoutEnhancements();
    let css = '';
    // Add fallback styles for older browsers
    if (layout.flexboxSupport === 'fallback') {
      css += `
        .flex-fallback {
          display: table;
          width: 100%;
        }
        .flex-fallback > * {
          display: table-cell;
          vertical-align: top;
        }
      `;
    }
    if (layout.gridSupport === 'fallback') {
      css += `
        .grid-fallback {
          display: block;
        }
        .grid-fallback > * {
          float: left;
          width: 50%;
        }
        .grid-fallback::after {
          content: "";
          display: table;
          clear: both;
        }
      `;
    }
    // Add reduced motion styles
    if (animations.useReducedMotion) {
      css += `
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `;
    }
    return css;
  }
  public updateConfig(newConfig: Partial<ProgressiveEnhancementConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.enhancementLevel = this.calculateEnhancementLevel();
  }
}
// Create singleton instance
export const progressiveEnhancement = new ProgressiveEnhancementService();
// React hook for progressive enhancement
export function useProgressiveEnhancement() {
  const [enhancements, setEnhancements] = React.useState({
    css: progressiveEnhancement.getCSSEnhancements(),
    animation: progressiveEnhancement.getAnimationEnhancements(),
    js: progressiveEnhancement.getJSEnhancements(),
    image: progressiveEnhancement.getImageEnhancements(),
    layout: progressiveEnhancement.getLayoutEnhancements(),
    performance: progressiveEnhancement.getPerformanceEnhancements(),
    accessibility: progressiveEnhancement.getAccessibilityEnhancements(),
  });
  React.useEffect(() => {
    const unsubscribe = featureDetection.onFeaturesReady(() => {
      setEnhancements({
        css: progressiveEnhancement.getCSSEnhancements(),
        animation: progressiveEnhancement.getAnimationEnhancements(),
        js: progressiveEnhancement.getJSEnhancements(),
        image: progressiveEnhancement.getImageEnhancements(),
        layout: progressiveEnhancement.getLayoutEnhancements(),
        performance: progressiveEnhancement.getPerformanceEnhancements(),
        accessibility: progressiveEnhancement.getAccessibilityEnhancements(),
      });
    });
    return unsubscribe;
  }, []);
  return {
    ...enhancements,
    enhancementLevel: progressiveEnhancement.getEnhancementLevel(),
    performanceScore: progressiveEnhancement.getPerformanceScore(),
    shouldUseFeature: progressiveEnhancement.shouldUseFeature.bind(progressiveEnhancement),
  };
}
export default progressiveEnhancement;
