"use client";
/**
 * Progressive Enhancement System (production-grade)
 *
 * - SSR-safe: no window/document access during module init
 * - Feature-flagged: gracefully downgrades by detected capabilities & perf
 * - Observable: emits updates when perf/feature data becomes ready
 * - Deterministic: singleton service with pure getters for UI hooks
 * - Configurable: runtime updateConfig with shallow-merge semantics
 */

import React from "react";
import { featureDetection, FeatureSupport } from "./feature-detection";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface EnhancementLevel {
  basic: boolean;
  enhanced: boolean;
  advanced: boolean;
}

export interface ProgressiveEnhancementConfig {
  enableAnimations: boolean;
  enableAdvancedCSS: boolean;
  enableModernJS: boolean;
  fallbackStrategy: "graceful" | "polyfill" | "disable";
  performanceThreshold: number; // 0..1 lower = more permissive
}

export interface CSSEnhancements {
  useGrid: boolean;
  useFlexbox: boolean;
  useCustomProperties: boolean;
  useContainerQueries: boolean;
  useLogicalProperties: boolean;
  useClamp: boolean;
  useBackdropFilter: boolean;
}

export interface AnimationEnhancements {
  useTransitions: boolean;
  useTransforms: boolean;
  useWebAnimations: boolean;
  useReducedMotion: boolean;
  animationDuration: number;
  animationEasing: string;
}

export interface JSEnhancements {
  useIntersectionObserver: boolean;
  useResizeObserver: boolean;
  useWebWorkers: boolean;
  useServiceWorkers: boolean;
  useModernAPIs: boolean;
  polyfillsNeeded: string[];
}

export interface ImageEnhancements {
  format: "avif" | "webp" | "jpg";
  useLazyLoading: boolean;
  useResponsiveImages: boolean;
  useImageOptimization: boolean;
}

export interface LayoutEnhancements {
  useModernLayout: boolean;
  useContainerQueries: boolean;
  useLogicalProperties: boolean;
  gridSupport: "full" | "fallback" | "none";
  flexboxSupport: "full" | "fallback" | "none";
}

export interface PerformanceEnhancements {
  useLazyLoading: boolean;
  useCodeSplitting: boolean;
  usePreloading: boolean;
  useCaching: boolean;
  bundleStrategy: "modern" | "legacy" | "universal";
}

export interface AccessibilityEnhancements {
  useReducedMotion: boolean;
  useHighContrast: boolean;
  useForcedColors: boolean;
  enhancedFocus: boolean;
  screenReaderOptimizations: boolean;
}

export interface EnhancementSnapshot {
  css: CSSEnhancements;
  animation: AnimationEnhancements;
  js: JSEnhancements;
  image: ImageEnhancements;
  layout: LayoutEnhancements;
  performance: PerformanceEnhancements;
  accessibility: AccessibilityEnhancements;
}

// ---------------------------------------------------------------------------
// Tiny Observable helper (no external deps)
// ---------------------------------------------------------------------------
class Emitter<T = void> {
  private listeners = new Set<(payload: T) => void>();
  on(fn: (payload: T) => void) {
    this.listeners.add(fn);
    return () => this.off(fn);
  }
  off(fn: (payload: T) => void) {
    this.listeners.delete(fn);
  }
  emit(payload: T) {
    this.listeners.forEach((fn) => fn(payload));
  }
}

// SSR guards
const isBrowser = typeof window !== "undefined" && typeof document !== "undefined";

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------
class ProgressiveEnhancementService {
  private config: ProgressiveEnhancementConfig;
  private enhancementLevel: EnhancementLevel;
  private performanceScore = 1.0; // optimistic default
  private updated = new Emitter<void>();
  private measured = false;

  constructor(config: Partial<ProgressiveEnhancementConfig> = {}) {
    this.config = {
      enableAnimations: true,
      enableAdvancedCSS: true,
      enableModernJS: true,
      fallbackStrategy: "graceful",
      performanceThreshold: 0.7,
      ...config,
    };

    this.enhancementLevel = this.calculateEnhancementLevel();

    // Defer performance measurement to browser idle time to avoid blocking
    if (isBrowser) {
      // wait for features to be ready first (polyfills etc.)
      featureDetection.onFeaturesReady(() => {
        this.measurePerformance().finally(() => {
          this.enhancementLevel = this.calculateEnhancementLevel();
          this.updated.emit();
        });
      });
    }
  }

  // Observable subscription
  onUpdated(cb: () => void) {
    return this.updated.on(cb);
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
    return !!(features.cssFlexbox && features.localStorage && features.requestAnimationFrame);
  }

  private supportsEnhancedFeatures(features: FeatureSupport): boolean {
    return (
      this.supportsBasicFeatures(features) &&
      !!(features.cssGrid && features.cssCustomProperties && features.intersectionObserver)
    );
  }

  private supportsAdvancedFeatures(features: FeatureSupport): boolean {
    return (
      this.supportsEnhancedFeatures(features) &&
      !!(features.cssContainerQueries && features.webAnimations && features.resizeObserver)
    );
  }

  private async measurePerformance(): Promise<void> {
    if (!isBrowser) {
      this.performanceScore = 0.8; // SSR default
      this.measured = true;
      return;
    }

    try {
      // If Performance API missing, fallback conservatively
      if (!featureDetection.hasFeature("performanceTiming")) {
        this.performanceScore = 0.6;
        this.measured = true;
        return;
      }

      // Prefer Navigation Timing L2 where available
      const nav = performance.getEntriesByType("navigation")[0] as
        | PerformanceNavigationTiming
        | undefined;

      // Paint metrics
      const paint = performance.getEntriesByType("paint");

      let score = 0.85; // start optimistic and adjust

      if (nav) {
        const loadTime = Math.max(1, nav.loadEventEnd - nav.loadEventStart);
        const dcl = Math.max(1, nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart);
        const avg = (loadTime + dcl) / 2;
        // Map avg ms to 0.1..1.0 with 2000ms as target
        score = Math.max(0.1, Math.min(1.0, 2000 / avg));
      }

      const fcp = paint.find((e) => (e as PerformanceEntry).name === "first-contentful-paint");
      if (fcp && (fcp as PerformanceEntry).startTime > 2000) {
        score *= 0.85; // penalize slow FCP
      }

      // Respect reduced motion by lowering animation budget slightly
      const features = featureDetection.getFeatures();
      if (features.reducedMotion) {
        score = Math.min(score, 0.75);
      }

      this.performanceScore = Number(score.toFixed(3));
      this.measured = true;
    } catch {
      this.performanceScore = 0.7;
      this.measured = true;
    }
  }

  // ------------------------------ Getters ----------------------------------
  public getCSSEnhancements(): CSSEnhancements {
    const features = featureDetection.getFeatures();
    const shouldEnhance = this.config.enableAdvancedCSS && this.performanceScore >= this.config.performanceThreshold;
    return {
      useGrid: !!(features.cssGrid && (this.enhancementLevel.enhanced || shouldEnhance)),
      useFlexbox: !!features.cssFlexbox,
      useCustomProperties: !!(features.cssCustomProperties && (this.enhancementLevel.enhanced || shouldEnhance)),
      useContainerQueries: !!(features.cssContainerQueries && this.enhancementLevel.advanced && shouldEnhance),
      useLogicalProperties: !!(features.cssLogicalProperties && this.enhancementLevel.enhanced && shouldEnhance),
      useClamp: !!(features.cssClamp && this.enhancementLevel.enhanced && shouldEnhance),
      useBackdropFilter: !!(features.cssBackdropFilter && this.enhancementLevel.advanced && shouldEnhance),
    };
  }

  public getAnimationEnhancements(): AnimationEnhancements {
    const features = featureDetection.getFeatures();
    const shouldAnimate =
      this.config.enableAnimations && !features.reducedMotion && this.performanceScore >= this.config.performanceThreshold;
    return {
      useTransitions: !!shouldAnimate,
      useTransforms: !!shouldAnimate,
      useWebAnimations: !!(features.webAnimations && this.enhancementLevel.advanced && shouldAnimate),
      useReducedMotion: !!features.reducedMotion,
      animationDuration: features.reducedMotion ? 0 : this.performanceScore < 0.5 ? 150 : 250,
      animationEasing: this.enhancementLevel.enhanced ? "cubic-bezier(0.4, 0, 0.2, 1)" : "ease-in-out",
    };
  }

  public getJSEnhancements(): JSEnhancements {
    const features = featureDetection.getFeatures();
    const shouldEnhance = this.config.enableModernJS && this.performanceScore >= this.config.performanceThreshold;
    const polyfillsNeeded: string[] = [];

    if (this.config.fallbackStrategy === "polyfill") {
      if (!features.intersectionObserver) polyfillsNeeded.push("intersection-observer");
      if (!features.resizeObserver) polyfillsNeeded.push("resize-observer");
      if (!features.requestIdleCallback) polyfillsNeeded.push("request-idle-callback");
    }

    return {
      useIntersectionObserver: !!(features.intersectionObserver || this.config.fallbackStrategy === "polyfill"),
      useResizeObserver: !!(features.resizeObserver || this.config.fallbackStrategy === "polyfill"),
      useWebWorkers: !!(features.webWorkers && this.enhancementLevel.enhanced && shouldEnhance),
      useServiceWorkers: !!(features.serviceWorkers && this.enhancementLevel.advanced && shouldEnhance),
      useModernAPIs: !!(this.enhancementLevel.enhanced && shouldEnhance),
      polyfillsNeeded,
    };
  }

  public getImageEnhancements(): ImageEnhancements {
    const features = featureDetection.getFeatures();
    return {
      format: featureDetection.getImageFormat(),
      useLazyLoading: !!(features.intersectionObserver && this.enhancementLevel.enhanced),
      useResponsiveImages: !!this.enhancementLevel.enhanced,
      useImageOptimization: this.performanceScore < 0.7,
    };
  }

  public getLayoutEnhancements(): LayoutEnhancements {
    const features = featureDetection.getFeatures();
    const css = this.getCSSEnhancements();
    return {
      useModernLayout: !!this.enhancementLevel.enhanced,
      useContainerQueries: !!css.useContainerQueries,
      useLogicalProperties: !!css.useLogicalProperties,
      gridSupport: features.cssGrid ? "full" : this.config.fallbackStrategy === "graceful" ? "fallback" : "none",
      flexboxSupport: features.cssFlexbox ? "full" : this.config.fallbackStrategy === "graceful" ? "fallback" : "none",
    };
  }

  public getPerformanceEnhancements(): PerformanceEnhancements {
    const features = featureDetection.getFeatures();
    return {
      useLazyLoading: !!this.enhancementLevel.enhanced,
      useCodeSplitting: !!(this.enhancementLevel.enhanced && this.performanceScore >= 0.6),
      usePreloading: !!(this.enhancementLevel.advanced && this.performanceScore >= 0.8),
      useCaching: !!(features.serviceWorkers && this.enhancementLevel.advanced),
      bundleStrategy: this.enhancementLevel.advanced ? "modern" : this.enhancementLevel.enhanced ? "universal" : "legacy",
    };
  }

  public getAccessibilityEnhancements(): AccessibilityEnhancements {
    const features = featureDetection.getFeatures();
    return {
      useReducedMotion: !!features.reducedMotion,
      useHighContrast: !!features.highContrast,
      useForcedColors: !!features.forcedColors,
      enhancedFocus: !!this.enhancementLevel.enhanced,
      screenReaderOptimizations: !!this.enhancementLevel.enhanced,
    };
  }

  // ------------------------------ Utils ------------------------------------
  public getEnhancementLevel(): EnhancementLevel {
    return { ...this.enhancementLevel };
  }

  public getPerformanceScore(): number {
    return this.performanceScore;
  }

  public hasMeasured(): boolean {
    return this.measured;
  }

  public shouldUseFeature(feature: keyof FeatureSupport, level: keyof EnhancementLevel = "enhanced"): boolean {
    return featureDetection.hasFeature(feature) && !!this.enhancementLevel[level];
  }

  public generateCSS(): string {
    const animations = this.getAnimationEnhancements();
    const layout = this.getLayoutEnhancements();

    let css = "";

    // Fallbacks for older browsers
    if (layout.flexboxSupport === "fallback") {
      css += `
        .flex-fallback { display: table; width: 100%; }
        .flex-fallback > * { display: table-cell; vertical-align: top; }
      `;
    }
    if (layout.gridSupport === "fallback") {
      css += `
        .grid-fallback { display: block; }
        .grid-fallback > * { float: left; width: 50%; }
        .grid-fallback::after { content: ""; display: table; clear: both; }
      `;
    }

    // Reduced motion guardrails
    if (animations.useReducedMotion) {
      css += `
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
        }
      `;
    }

    return css;
  }

  public updateConfig(newConfig: Partial<ProgressiveEnhancementConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.enhancementLevel = this.calculateEnhancementLevel();
    this.updated.emit();
  }
}

// Singleton instance
export const progressiveEnhancement = new ProgressiveEnhancementService();

// ---------------------------------------------------------------------------
// React hook
// ---------------------------------------------------------------------------
export function useProgressiveEnhancement() {
  const getSnapshot = React.useCallback<() => EnhancementSnapshot>(() => ({
    css: progressiveEnhancement.getCSSEnhancements(),
    animation: progressiveEnhancement.getAnimationEnhancements(),
    js: progressiveEnhancement.getJSEnhancements(),
    image: progressiveEnhancement.getImageEnhancements(),
    layout: progressiveEnhancement.getLayoutEnhancements(),
    performance: progressiveEnhancement.getPerformanceEnhancements(),
    accessibility: progressiveEnhancement.getAccessibilityEnhancements(),
  }), []);

  const [state, setState] = React.useState<EnhancementSnapshot>(getSnapshot);
  const [level, setLevel] = React.useState<EnhancementLevel>(progressiveEnhancement.getEnhancementLevel());
  const [score, setScore] = React.useState<number>(progressiveEnhancement.getPerformanceScore());

  React.useEffect(() => {
    // Update immediately when feature-detection finishes and service emits
    const off = progressiveEnhancement.onUpdated(() => {
      setState(getSnapshot());
      setLevel(progressiveEnhancement.getEnhancementLevel());
      setScore(progressiveEnhancement.getPerformanceScore());
    });

    // Also update when feature-detection subsystem signals readiness directly
    const unsubFD = featureDetection.onFeaturesReady(() => {
      setState(getSnapshot());
      setLevel(progressiveEnhancement.getEnhancementLevel());
      setScore(progressiveEnhancement.getPerformanceScore());
    });

    return () => {
      off();
      unsubFD();
    };
  }, [getSnapshot]);

  return {
    ...state,
    enhancementLevel: level,
    performanceScore: score,
    shouldUseFeature: progressiveEnhancement.shouldUseFeature.bind(progressiveEnhancement),
    hasMeasured: progressiveEnhancement.hasMeasured(),
    generateCSS: progressiveEnhancement.generateCSS.bind(progressiveEnhancement),
    updateConfig: progressiveEnhancement.updateConfig.bind(progressiveEnhancement),
  };
}

export default progressiveEnhancement;
