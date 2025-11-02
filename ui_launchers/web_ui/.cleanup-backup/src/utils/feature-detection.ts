/**
 * Feature Detection and Graceful Degradation System
 * 
 * Provides comprehensive feature detection for modern web APIs and CSS features,
 * enabling graceful degradation and progressive enhancement.
 */

import React from 'react';

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

class FeatureDetectionService {
  private _features: FeatureSupport | null = null;
  private _callbacks: Array<(features: FeatureSupport) => void> = [];

  constructor() {
    if (typeof window !== 'undefined') {
      this.detectFeatures();
    }
  }

  private detectFeatures(): void {
    this._features = {
      // CSS Features
      cssCustomProperties: this.detectCSSCustomProperties(),
      cssGrid: this.detectCSSGrid(),
      cssFlexbox: this.detectCSSFlexbox(),
      cssContainerQueries: this.detectCSSContainerQueries(),
      cssLogicalProperties: this.detectCSSLogicalProperties(),
      cssClamp: this.detectCSSClamp(),
      cssBackdropFilter: this.detectCSSBackdropFilter(),
      cssScrollBehavior: this.detectCSSScrollBehavior(),
      cssAspectRatio: this.detectCSSAspectRatio(),
      cssGap: this.detectCSSGap(),
      
      // JavaScript APIs
      intersectionObserver: this.detectIntersectionObserver(),
      resizeObserver: this.detectResizeObserver(),
      mutationObserver: this.detectMutationObserver(),
      webAnimations: this.detectWebAnimations(),
      requestIdleCallback: this.detectRequestIdleCallback(),
      requestAnimationFrame: this.detectRequestAnimationFrame(),
      
      // Browser Features
      webGL: this.detectWebGL(),
      webGL2: this.detectWebGL2(),
      webWorkers: this.detectWebWorkers(),
      serviceWorkers: this.detectServiceWorkers(),
      localStorage: this.detectLocalStorage(),
      sessionStorage: this.detectSessionStorage(),
      indexedDB: this.detectIndexedDB(),
      
      // Media Features
      webP: false, // Will be detected asynchronously
      avif: false, // Will be detected asynchronously
      webM: this.detectWebM(),
      
      // Input Features
      touchEvents: this.detectTouchEvents(),
      pointerEvents: this.detectPointerEvents(),
      deviceMotion: this.detectDeviceMotion(),
      vibration: this.detectVibration(),
      
      // Network Features
      onlineStatus: this.detectOnlineStatus(),
      connectionAPI: this.detectConnectionAPI(),
      
      // Performance Features
      performanceObserver: this.detectPerformanceObserver(),
      performanceTiming: this.detectPerformanceTiming(),
      
      // Accessibility Features
      reducedMotion: this.detectReducedMotion(),
      highContrast: this.detectHighContrast(),
      forcedColors: this.detectForcedColors(),
    };

    // Detect image formats asynchronously
    this.detectImageFormats();

    // Notify callbacks
    this._callbacks.forEach(callback => callback(this._features!));
  }

  // CSS Feature Detection
  private detectCSSCustomProperties(): boolean {
    return CSS.supports('color', 'var(--test)');
  }

  private detectCSSGrid(): boolean {
    return CSS.supports('display', 'grid');
  }

  private detectCSSFlexbox(): boolean {
    return CSS.supports('display', 'flex');
  }

  private detectCSSContainerQueries(): boolean {
    return CSS.supports('container-type', 'inline-size');
  }

  private detectCSSLogicalProperties(): boolean {
    return CSS.supports('margin-inline-start', '1px');
  }

  private detectCSSClamp(): boolean {
    return CSS.supports('width', 'clamp(1px, 50%, 100px)');
  }

  private detectCSSBackdropFilter(): boolean {
    return CSS.supports('backdrop-filter', 'blur(10px)');
  }

  private detectCSSScrollBehavior(): boolean {
    return CSS.supports('scroll-behavior', 'smooth');
  }

  private detectCSSAspectRatio(): boolean {
    return CSS.supports('aspect-ratio', '16/9');
  }

  private detectCSSGap(): boolean {
    return CSS.supports('gap', '1rem');
  }

  // JavaScript API Detection
  private detectIntersectionObserver(): boolean {
    return 'IntersectionObserver' in window;
  }

  private detectResizeObserver(): boolean {
    return 'ResizeObserver' in window;
  }

  private detectMutationObserver(): boolean {
    return 'MutationObserver' in window;
  }

  private detectWebAnimations(): boolean {
    return 'animate' in document.createElement('div');
  }

  private detectRequestIdleCallback(): boolean {
    return 'requestIdleCallback' in window;
  }

  private detectRequestAnimationFrame(): boolean {
    return 'requestAnimationFrame' in window;
  }

  // Browser Feature Detection
  private detectWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
    } catch {
      return false;
    }
  }

  private detectWebGL2(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!canvas.getContext('webgl2');
    } catch {
      return false;
    }
  }

  private detectWebWorkers(): boolean {
    return 'Worker' in window;
  }

  private detectServiceWorkers(): boolean {
    return 'serviceWorker' in navigator;
  }

  private detectLocalStorage(): boolean {
    try {
      const test = '__test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private detectSessionStorage(): boolean {
    try {
      const test = '__test__';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private detectIndexedDB(): boolean {
    return 'indexedDB' in window;
  }

  // Media Feature Detection
  private detectWebM(): boolean {
    const video = document.createElement('video');
    return video.canPlayType('video/webm') !== '';
  }

  private async detectImageFormats(): Promise<void> {
    if (!this._features) return;

    // Detect WebP
    this._features.webP = await this.canUseImageFormat('data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA');
    
    // Detect AVIF
    this._features.avif = await this.canUseImageFormat('data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A=');

    // Notify callbacks about updated features
    this._callbacks.forEach(callback => callback(this._features!));
  }

  private canUseImageFormat(src: string): Promise<boolean> {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = src;
    });
  }

  // Input Feature Detection
  private detectTouchEvents(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }

  private detectPointerEvents(): boolean {
    return 'onpointerdown' in window;
  }

  private detectDeviceMotion(): boolean {
    return 'DeviceMotionEvent' in window;
  }

  private detectVibration(): boolean {
    return 'vibrate' in navigator;
  }

  // Network Feature Detection
  private detectOnlineStatus(): boolean {
    return 'onLine' in navigator;
  }

  private detectConnectionAPI(): boolean {
    return 'connection' in navigator || 'mozConnection' in navigator || 'webkitConnection' in navigator;
  }

  // Performance Feature Detection
  private detectPerformanceObserver(): boolean {
    return 'PerformanceObserver' in window;
  }

  private detectPerformanceTiming(): boolean {
    return 'performance' in window && 'timing' in performance;
  }

  // Accessibility Feature Detection
  private detectReducedMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  private detectHighContrast(): boolean {
    return window.matchMedia('(prefers-contrast: high)').matches;
  }

  private detectForcedColors(): boolean {
    return window.matchMedia('(forced-colors: active)').matches;
  }

  // Public API
  public getFeatures(): FeatureSupport {
    if (!this._features) {
      throw new Error('Feature detection not yet complete');
    }
    return { ...this._features };
  }

  public hasFeature(feature: keyof FeatureSupport): boolean {
    return this._features?.[feature] ?? false;
  }

  public onFeaturesReady(callback: (features: FeatureSupport) => void): () => void {
    if (this._features) {
      callback(this._features);
    } else {
      this._callbacks.push(callback);
    }

    // Return unsubscribe function
    return () => {
      const index = this._callbacks.indexOf(callback);
      if (index > -1) {
        this._callbacks.splice(index, 1);
      }
    };
  }

  public supportsModernCSS(): boolean {
    return this.hasFeature('cssCustomProperties') && 
           this.hasFeature('cssGrid') && 
           this.hasFeature('cssFlexbox');
  }

  public supportsModernJS(): boolean {
    return this.hasFeature('intersectionObserver') && 
           this.hasFeature('requestAnimationFrame') && 
           this.hasFeature('localStorage');
  }

  public supportsAdvancedFeatures(): boolean {
    return this.hasFeature('cssContainerQueries') && 
           this.hasFeature('cssBackdropFilter') && 
           this.hasFeature('webAnimations');
  }

  public getImageFormat(): 'avif' | 'webp' | 'jpg' {
    if (this.hasFeature('avif')) return 'avif';
    if (this.hasFeature('webP')) return 'webp';
    return 'jpg';
  }

  public shouldUsePolyfills(): boolean {
    return !this.supportsModernJS() || !this.supportsModernCSS();
  }
}

// Create singleton instance
export const featureDetection = new FeatureDetectionService();

// React hook for feature detection
export function useFeatureDetection() {
  const [features, setFeatures] = React.useState<FeatureSupport | null>(null);

  React.useEffect(() => {
    const unsubscribe = featureDetection.onFeaturesReady(setFeatures);
    return unsubscribe;
  }, []);

  return {
    features,
    hasFeature: (feature: keyof FeatureSupport) => featureDetection.hasFeature(feature),
    supportsModernCSS: () => featureDetection.supportsModernCSS(),
    supportsModernJS: () => featureDetection.supportsModernJS(),
    supportsAdvancedFeatures: () => featureDetection.supportsAdvancedFeatures(),
    getImageFormat: () => featureDetection.getImageFormat(),
    shouldUsePolyfills: () => featureDetection.shouldUsePolyfills(),
  };
}

export default featureDetection;