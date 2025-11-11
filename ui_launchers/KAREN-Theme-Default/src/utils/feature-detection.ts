/**
 * Feature Detection and Graceful Degradation System
 * Provides comprehensive feature detection for modern web APIs and CSS features,
 * enabling graceful degradation and progressive enhancement.
 */

import * as React from 'react';

export interface FeatureSupport {
  // CSS Features
  cssCustomProperties: boolean;
  cssGrid: boolean;
  cssFlexbox: boolean;
  cssContainerQueries: boolean;
  cssLogicalProperties: boolean;
  cssClamp: boolean;
  cssBackdropFilter: boolean;
  cssScrollBehavior: boolean;
  cssAspectRatio: boolean;
  cssGap: boolean;

  // JavaScript APIs
  intersectionObserver: boolean;
  resizeObserver: boolean;
  mutationObserver: boolean;
  webAnimations: boolean;
  requestIdleCallback: boolean;
  requestAnimationFrame: boolean;

  // Browser Features
  webGL: boolean;
  webGL2: boolean;
  webWorkers: boolean;
  serviceWorkers: boolean;
  localStorage: boolean;
  sessionStorage: boolean;
  indexedDB: boolean;

  // Media Features
  webP: boolean;
  avif: boolean;
  webM: boolean;

  // Input Features
  touchEvents: boolean;
  pointerEvents: boolean;
  deviceMotion: boolean;
  vibration: boolean;

  // Network Features
  onlineStatus: boolean;
  connectionAPI: boolean;

  // Performance Features
  performanceObserver: boolean;
  performanceTiming: boolean;

  // Accessibility Features
  reducedMotion: boolean;
  highContrast: boolean;
  forcedColors: boolean;
}

export type Callback = (features: FeatureSupport) => void;

type MediaQueryListWithLegacy = MediaQueryList & {
  addListener?: (listener: (this: MediaQueryList, ev: MediaQueryListEvent) => void) => void;
};

function getCSS(): typeof CSS | undefined {
  return (globalThis as { CSS?: typeof CSS }).CSS;
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

// Removed unused function _supportsCSS

function safeCSSSupports(prop: string, value: string): boolean {
  try {
    const css = getCSS();
    return css ? css.supports(prop, value) : false;
  } catch {
    return false;
  }
}

// Removed unused function _safeCSSSupportsSyntax

function canUseStorage(storage: 'localStorage' | 'sessionStorage'): boolean {
  if (!isBrowser()) return false;
  try {
    const key = '__fd_test__';
    const target = window[storage];
    target.setItem(key, key);
    target.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function canUseIndexedDB(): boolean {
  if (!isBrowser()) return false;
  try {
    return 'indexedDB' in window && !!window.indexedDB;
  } catch {
    return false;
  }
}

class FeatureDetectionService {
  private _features: FeatureSupport | null = null;
  private _callbacks: Callback[] = [];
  private _readyResolve!: (v: FeatureSupport) => void;
  private _readyPromise: Promise<FeatureSupport>;
  private _listenersBound = false;

  constructor() {
    this._readyPromise = new Promise<FeatureSupport>((resolve) => {
      this._readyResolve = resolve;
    });

    if (isBrowser()) {
      // Detect immediately after current tick so DOM APIs are ready
      if (document.readyState === 'complete' || document.readyState === 'interactive') {
        this.detectFeatures();
      } else {
        document.addEventListener('DOMContentLoaded', () => this.detectFeatures(), { once: true });
      }
    }
  }

  private detectFeatures(): void {
    // Base snapshot
    this._features = {
      // CSS Features
      cssCustomProperties: safeCSSSupports('color', 'var(--test)'),
      cssGrid: safeCSSSupports('display', 'grid'),
      cssFlexbox: safeCSSSupports('display', 'flex'),
      cssContainerQueries: safeCSSSupports('container-type', 'inline-size'),
      cssLogicalProperties: safeCSSSupports('margin-inline-start', '1px'),
      cssClamp: safeCSSSupports('width', 'clamp(1px, 50%, 100px)'),
      cssBackdropFilter: safeCSSSupports('backdrop-filter', 'blur(10px)'),
      cssScrollBehavior: safeCSSSupports('scroll-behavior', 'smooth'),
      cssAspectRatio: safeCSSSupports('aspect-ratio', '16/9'),
      cssGap: safeCSSSupports('gap', '1rem'),

      // JavaScript APIs
      intersectionObserver: isBrowser() ? 'IntersectionObserver' in window : false,
      resizeObserver: isBrowser() ? 'ResizeObserver' in window : false,
      mutationObserver: isBrowser() ? 'MutationObserver' in window : false,
      webAnimations: isBrowser() ? 'animate' in document.createElement('div') : false,
      requestIdleCallback: isBrowser() ? 'requestIdleCallback' in window : false,
      requestAnimationFrame: isBrowser() ? 'requestAnimationFrame' in window : false,

      // Browser Features
      webGL: this.detectWebGL(),
      webGL2: this.detectWebGL2(),
      webWorkers: isBrowser() ? 'Worker' in window : false,
      serviceWorkers: isBrowser() ? 'serviceWorker' in navigator : false,
      localStorage: canUseStorage('localStorage'),
      sessionStorage: canUseStorage('sessionStorage'),
      indexedDB: canUseIndexedDB(),

      // Media Features
      webP: false, // async
      avif: false, // async
      webM: this.detectWebM(),

      // Input Features
      touchEvents: isBrowser() ? ('ontouchstart' in window || (navigator.maxTouchPoints || 0) > 0) : false,
      pointerEvents: isBrowser() ? 'onpointerdown' in window : false,
      deviceMotion: isBrowser() ? 'DeviceMotionEvent' in window : false,
      vibration: isBrowser() ? 'vibrate' in navigator : false,

      // Network Features
      onlineStatus: isBrowser() ? 'onLine' in navigator && navigator.onLine : false,
      connectionAPI: isBrowser()
        ? ('connection' in navigator || 'mozConnection' in navigator || 'webkitConnection' in navigator)
        : false,

      // Performance Features
      performanceObserver: isBrowser() ? 'PerformanceObserver' in window : false,
      performanceTiming: isBrowser() ? 'timing' in performance : false,

      // Accessibility Features
      reducedMotion: this.mq('(prefers-reduced-motion: reduce)'),
      highContrast: this.mq('(prefers-contrast: more)') || this.mq('(prefers-contrast: high)'),
      forcedColors: this.mq('(forced-colors: active)'),
    };

    // Bind live listeners (once)
    if (isBrowser() && !this._listenersBound) {
      this._listenersBound = true;
      // online/offline
      window.addEventListener('online', this.syncOnlineStatus);
      window.addEventListener('offline', this.syncOnlineStatus);
      // reduced motion changes
      try {
        const rm = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (typeof rm.addEventListener === 'function') {
          rm.addEventListener('change', this.syncReducedMotion);
        } else {
          const legacy = rm as MediaQueryListWithLegacy;
          if (typeof legacy.addListener === 'function') {
            legacy.addListener(this.syncReducedMotion);
          }
        }
      } catch {
        /* noop */
      }
    }

    // Async image formats then finalize
    this.detectImageFormats().finally(() => {
      // Notify
      this._callbacks.forEach(cb => this._features && cb(this._features));
      if (this._features) this._readyResolve(this._features);
    });
  }

  private mq(query: string): boolean {
    if (!isBrowser() || typeof window.matchMedia !== 'function') return false;
    try {
      return window.matchMedia(query).matches;
    } catch {
      return false;
    }
  }

  // Media Feature Detection
  private detectWebM(): boolean {
    if (!isBrowser()) return false;
    try {
      const video = document.createElement('video');
      return typeof video.canPlayType === 'function' && video.canPlayType('video/webm') !== '';
    } catch {
      return false;
    }
  }

  private detectWebGL(): boolean {
    if (!isBrowser()) return false;
    try {
      const canvas = document.createElement('canvas');
      const webgl1 = canvas.getContext('webgl') as WebGLRenderingContext | null;
      const experimental = canvas.getContext('experimental-webgl') as WebGLRenderingContext | null;
      return !!(webgl1 || experimental);
    } catch {
      return false;
    }
  }

  private detectWebGL2(): boolean {
    if (!isBrowser()) return false;
    try {
      const canvas = document.createElement('canvas');
      return !!canvas.getContext('webgl2');
    } catch {
      return false;
    }
  }

  private canUseImageFormat(src: string, timeoutMs = 4000): Promise<boolean> {
    if (!isBrowser()) return Promise.resolve(false);
    return new Promise((resolve) => {
      const img = new Image();
      let done = false;
      const cleanup = () => {
        img.onload = null;
        img.onerror = null;
      };
      const finish = (val: boolean) => {
        if (done) return;
        done = true;
        cleanup();
        resolve(val);
      };
      const timer = setTimeout(() => finish(false), timeoutMs);

      img.onload = () => {
        clearTimeout(timer);
        finish(true);
      };
      img.onerror = () => {
        clearTimeout(timer);
        finish(false);
      };
      // Setting referrerPolicy avoids some noisy console warnings in strict sites
      try {
        img.referrerPolicy = 'no-referrer';
      } catch {
        /* noop */
      }
      img.src = src;
    });
  }

  private async detectImageFormats(): Promise<void> {
    if (!this._features) return;

    // WebP
    const webp = await this.canUseImageFormat(
      // Tiny WebP
      'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA'
    );

    // AVIF (tiny)
    const avif = await this.canUseImageFormat(
      'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A='
    );

    this._features.webP = webp;
    this._features.avif = avif;
  }

  // Live sync handlers
  private syncOnlineStatus = () => {
    if (!this._features) return;
    this._features.onlineStatus = navigator.onLine;
    this._callbacks.forEach(cb => cb({ ...this._features! }));
  };

  private syncReducedMotion = () => {
    if (!this._features) return;
    this._features.reducedMotion = this.mq('(prefers-reduced-motion: reduce)');
    this._callbacks.forEach(cb => cb({ ...this._features! }));
  };

  // Public API
  public getFeatures(): FeatureSupport {
    if (!this._features) {
      // Return a conservative baseline in SSR or very early hydration
      return {
        cssCustomProperties: false,
        cssGrid: false,
        cssFlexbox: true, // extremely common baseline
        cssContainerQueries: false,
        cssLogicalProperties: false,
        cssClamp: false,
        cssBackdropFilter: false,
        cssScrollBehavior: false,
        cssAspectRatio: false,
        cssGap: true,

        intersectionObserver: false,
        resizeObserver: false,
        mutationObserver: false,
        webAnimations: false,
        requestIdleCallback: false,
        requestAnimationFrame: false,

        webGL: false,
        webGL2: false,
        webWorkers: false,
        serviceWorkers: false,
        localStorage: false,
        sessionStorage: false,
        indexedDB: false,

        webP: false,
        avif: false,
        webM: false,

        touchEvents: false,
        pointerEvents: false,
        deviceMotion: false,
        vibration: false,

        onlineStatus: false,
        connectionAPI: false,

        performanceObserver: false,
        performanceTiming: false,

        reducedMotion: false,
        highContrast: false,
        forcedColors: false,
      };
    }
    return { ...this._features };
  }

  public whenReady(): Promise<FeatureSupport> {
    return this._readyPromise;
  }

  public hasFeature(feature: keyof FeatureSupport): boolean {
    return !!this.getFeatures()[feature];
  }

  public onFeaturesReady(callback: Callback): () => void {
    if (this._features) {
      callback(this.getFeatures());
    } else {
      this._callbacks.push(callback);
    }
    return () => {
      const idx = this._callbacks.indexOf(callback);
      if (idx >= 0) this._callbacks.splice(idx, 1);
    };
  }

  public supportsModernCSS(): boolean {
    const f = this.getFeatures();
    return f.cssCustomProperties && f.cssGrid && f.cssFlexbox;
  }

  public supportsModernJS(): boolean {
    const f = this.getFeatures();
    return f.intersectionObserver && f.requestAnimationFrame && f.localStorage;
  }

  public supportsAdvancedFeatures(): boolean {
    const f = this.getFeatures();
    return f.cssContainerQueries && f.cssBackdropFilter && f.webAnimations;
  }

  public getImageFormat(): 'avif' | 'webp' | 'jpg' {
    const f = this.getFeatures();
    if (f.avif) return 'avif';
    if (f.webP) return 'webp';
    return 'jpg';
  }

  public shouldUsePolyfills(): boolean {
    return !(this.supportsModernJS() && this.supportsModernCSS());
  }
}

// Singleton
export const featureDetection = new FeatureDetectionService();

// React hook for feature detection
export function useFeatureDetection() {
  const [features, setFeatures] = React.useState<FeatureSupport | null>(null);

  React.useEffect(() => {
    const unsub = featureDetection.onFeaturesReady(setFeatures);
    // If already ready, ensure immediate snapshot
    if (!features && featureDetection['getFeatures']) {
      try {
        const snapshot = featureDetection.getFeatures();
        // If the snapshot is not the conservative SSR baseline, accept it:
        if (isBrowser()) setFeatures(snapshot);
      } catch {
        // ignore; will receive async callback
      }
    }
    return unsub;
  }, [features]);

  return {
    features,
    whenReady: () => featureDetection.whenReady(),
    hasFeature: (feature: keyof FeatureSupport) => featureDetection.hasFeature(feature),
    supportsModernCSS: () => featureDetection.supportsModernCSS(),
    supportsModernJS: () => featureDetection.supportsModernJS(),
    supportsAdvancedFeatures: () => featureDetection.supportsAdvancedFeatures(),
    getImageFormat: () => featureDetection.getImageFormat(),
    shouldUsePolyfills: () => featureDetection.shouldUsePolyfills(),
  };
}

export default featureDetection;
