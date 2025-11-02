/**
 * Polyfill Loader System
 * 
 * Dynamically loads polyfills for missing browser features to ensure
 * compatibility across all supported browsers.
 */
import React from 'react';
import { featureDetection } from './feature-detection';
export interface PolyfillConfig {
  intersectionObserver: boolean;
  resizeObserver: boolean;
  requestIdleCallback: boolean;
  webAnimations: boolean;
  customElements: boolean;
  fetch: boolean;
  promise: boolean;
  objectAssign: boolean;
  arrayIncludes: boolean;
  stringIncludes: boolean;
  cssCustomProperties: boolean;
}
export interface PolyfillLoadResult {
  loaded: string[];
  failed: string[];
  skipped: string[];
}
class PolyfillLoaderService {
  private loadedPolyfills = new Set<string>();
  private loadingPromises = new Map<string, Promise<void>>();
  constructor() {
    // Auto-load critical polyfills
    this.loadCriticalPolyfills();
  }
  private async loadCriticalPolyfills(): Promise<void> {
    const criticalPolyfills: (keyof PolyfillConfig)[] = [
      'fetch',
      'promise',
      'objectAssign',
    ];
    await this.loadPolyfills(
      criticalPolyfills.reduce((config, key) => {
        config[key] = true;
        return config;
      }, {} as Partial<PolyfillConfig>)
    );
  }
  public async loadPolyfills(config: Partial<PolyfillConfig>): Promise<PolyfillLoadResult> {
    const result: PolyfillLoadResult = {
      loaded: [],
      failed: [],
      skipped: [],
    };
    const polyfillsToLoad = this.determineNeededPolyfills(config);
    await Promise.allSettled(
      polyfillsToLoad.map(async (polyfill) => {
        try {
          await this.loadPolyfill(polyfill);
          result.loaded.push(polyfill);
        } catch (error) {
          result.failed.push(polyfill);
        }
      })
    );
    // Add skipped polyfills
    Object.keys(config).forEach(key => {
      if (!polyfillsToLoad.includes(key) && config[key as keyof PolyfillConfig]) {
        result.skipped.push(key);
      }

    return result;
  }
  private determineNeededPolyfills(config: Partial<PolyfillConfig>): string[] {
    const needed: string[] = [];
    const features = featureDetection.getFeatures();
    // Check each polyfill
    if (config.intersectionObserver && !features.intersectionObserver) {
      needed.push('intersectionObserver');
    }
    if (config.resizeObserver && !features.resizeObserver) {
      needed.push('resizeObserver');
    }
    if (config.requestIdleCallback && !features.requestIdleCallback) {
      needed.push('requestIdleCallback');
    }
    if (config.webAnimations && !features.webAnimations) {
      needed.push('webAnimations');
    }
    if (config.customElements && !('customElements' in window)) {
      needed.push('customElements');
    }
    if (config.fetch && !('fetch' in window)) {
      needed.push('fetch');
    }
    if (config.promise && !window.Promise) {
      needed.push('promise');
    }
    if (config.objectAssign && !Object.assign) {
      needed.push('objectAssign');
    }
    if (config.arrayIncludes && !Array.prototype.includes) {
      needed.push('arrayIncludes');
    }
    if (config.stringIncludes && !String.prototype.includes) {
      needed.push('stringIncludes');
    }
    if (config.cssCustomProperties && !features.cssCustomProperties) {
      needed.push('cssCustomProperties');
    }
    return needed.filter(polyfill => !this.loadedPolyfills.has(polyfill));
  }
  private async loadPolyfill(name: string): Promise<void> {
    // Return existing promise if already loading
    if (this.loadingPromises.has(name)) {
      return this.loadingPromises.get(name);
    }
    // Skip if already loaded
    if (this.loadedPolyfills.has(name)) {
      return Promise.resolve();
    }
    const loadPromise = this.loadPolyfillImplementation(name);
    this.loadingPromises.set(name, loadPromise);
    try {
      await loadPromise;
      this.loadedPolyfills.add(name);
    } finally {
      this.loadingPromises.delete(name);
    }
  }
  private async loadPolyfillImplementation(name: string): Promise<void> {
    switch (name) {
      case 'intersectionObserver':
        return this.loadIntersectionObserverPolyfill();
      case 'resizeObserver':
        return this.loadResizeObserverPolyfill();
      case 'requestIdleCallback':
        return this.loadRequestIdleCallbackPolyfill();
      case 'webAnimations':
        return this.loadWebAnimationsPolyfill();
      case 'customElements':
        return this.loadCustomElementsPolyfill();
      case 'fetch':
        return this.loadFetchPolyfill();
      case 'promise':
        return this.loadPromisePolyfill();
      case 'objectAssign':
        return this.loadObjectAssignPolyfill();
      case 'arrayIncludes':
        return this.loadArrayIncludesPolyfill();
      case 'stringIncludes':
        return this.loadStringIncludesPolyfill();
      case 'cssCustomProperties':
        return this.loadCSSCustomPropertiesPolyfill();
      default:
        throw new Error(`Unknown polyfill: ${name}`);
    }
  }
  // Polyfill implementations
  private async loadIntersectionObserverPolyfill(): Promise<void> {
    if ('IntersectionObserver' in window) return;
    // Use CDN or local polyfill
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=IntersectionObserver');
  }
  private async loadResizeObserverPolyfill(): Promise<void> {
    if ('ResizeObserver' in window) return;
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=ResizeObserver');
  }
  private async loadRequestIdleCallbackPolyfill(): Promise<void> {
    if ('requestIdleCallback' in window) return;
    // Inline polyfill for requestIdleCallback
    (window as any).requestIdleCallback = (callback: IdleRequestCallback, options?: IdleRequestOptions) => {
      const start = Date.now();
      return setTimeout(() => {
        callback({
          didTimeout: false,
          timeRemaining() {
            return Math.max(0, 50 - (Date.now() - start));
          },

      }, 1);
    };
    (window as any).cancelIdleCallback = (id: number) => {
      clearTimeout(id);
    };
  }
  private async loadWebAnimationsPolyfill(): Promise<void> {
    if ('animate' in document.createElement('div')) return;
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=Element.prototype.animate');
  }
  private async loadCustomElementsPolyfill(): Promise<void> {
    if ('customElements' in window) return;
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=CustomElements');
  }
  private async loadFetchPolyfill(): Promise<void> {
    if ('fetch' in window) return;
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=fetch');
  }
  private async loadPromisePolyfill(): Promise<void> {
    if (window.Promise) return;
    await this.loadScript('https://polyfill.io/v3/polyfill.min.js?features=Promise');
  }
  private loadObjectAssignPolyfill(): Promise<void> {
    if (typeof Object.assign === 'function') return Promise.resolve();
    // Inline polyfill for Object.assign
    Object.assign = function(target: any, ...sources: any[]) {
      if (target == null) {
        throw new TypeError('Cannot convert undefined or null to object');
      }
      const to = Object(target);
      for (let index = 0; index < sources.length; index++) {
        const nextSource = sources[index];
        if (nextSource != null) {
          for (const nextKey in nextSource) {
            if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
              to[nextKey] = nextSource[nextKey];
            }
          }
        }
      }
      return to;
    };
    return Promise.resolve();
  }
  private loadArrayIncludesPolyfill(): Promise<void> {
    if (typeof Array.prototype.includes === 'function') return Promise.resolve();
    // Inline polyfill for Array.prototype.includes
    Array.prototype.includes = function(searchElement: any, fromIndex?: number) {
      const O = Object(this);
      const len = parseInt(O.length) || 0;
      if (len === 0) return false;
      const n = parseInt(String(fromIndex || 0)) || 0;
      let k = n >= 0 ? n : Math.max(len + n, 0);
      while (k < len) {
        if (O[k] === searchElement) return true;
        k++;
      }
      return false;
    };
    return Promise.resolve();
  }
  private loadStringIncludesPolyfill(): Promise<void> {
    if (typeof String.prototype.includes === 'function') return Promise.resolve();
    // Inline polyfill for String.prototype.includes
    String.prototype.includes = function(search: string, start?: number) {
      if (typeof start !== 'number') {
        start = 0;
      }
      if (start + search.length > this.length) {
        return false;
      } else {
        return this.indexOf(search, start) !== -1;
      }
    };
    return Promise.resolve();
  }
  private async loadCSSCustomPropertiesPolyfill(): Promise<void> {
    if (CSS.supports('color', 'var(--test)')) return;
    // Load CSS custom properties polyfill
    await this.loadScript('https://cdn.jsdelivr.net/npm/css-vars-ponyfill@2');
    // Initialize the polyfill
    if ((window as any).cssVars) {
      (window as any).cssVars({
        watch: true,
        preserveStatic: false,
        preserveVars: false,

    }
  }
  private loadScript(src: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // Check if script is already loaded
      const existingScript = document.querySelector(`script[src="${src}"]`);
      if (existingScript) {
        resolve();
        return;
      }
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);

  }
  // Public API
  public isPolyfillLoaded(name: string): boolean {
    return this.loadedPolyfills.has(name);
  }
  public getLoadedPolyfills(): string[] {
    return Array.from(this.loadedPolyfills);
  }
  public async loadPolyfillsForFeatures(features: string[]): Promise<PolyfillLoadResult> {
    const config: Partial<PolyfillConfig> = {};
    features.forEach(feature => {
      if (feature in config) {
        (config as any)[feature] = true;
      }

    return this.loadPolyfills(config);
  }
  public async ensurePolyfillsLoaded(polyfills: string[]): Promise<void> {
    const promises = polyfills.map(polyfill => this.loadPolyfill(polyfill));
    await Promise.all(promises);
  }
}
// Create singleton instance
export const polyfillLoader = new PolyfillLoaderService();
// React hook for polyfill loading
export function usePolyfills(config: Partial<PolyfillConfig>) {
  const [loadResult, setLoadResult] = React.useState<PolyfillLoadResult | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  React.useEffect(() => {
    let mounted = true;
    polyfillLoader.loadPolyfills(config).then(result => {
      if (mounted) {
        setLoadResult(result);
        setIsLoading(false);
      }

    return () => {
      mounted = false;
    };
  }, [JSON.stringify(config)]);
  return {
    loadResult,
    isLoading,
    isPolyfillLoaded: polyfillLoader.isPolyfillLoaded.bind(polyfillLoader),
    getLoadedPolyfills: polyfillLoader.getLoadedPolyfills.bind(polyfillLoader),
  };
}
export default polyfillLoader;
