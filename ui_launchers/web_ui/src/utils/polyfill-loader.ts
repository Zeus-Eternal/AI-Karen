'use client';
/**
 * Polyfill Loader System (production-grade)
 *
 * - SSR-safe: never touches window/document on server
 * - Idempotent: dedupes concurrent loads with a promise map
 * - CSP-friendly: optional nonce & integrity for added scripts
 * - Privacy/Perf: uses targeted, version-pinned polyfills (no polyfill.io shotgun)
 * - Integrates with featureDetection; falls back to internal probes if not ready
 * - Critical polyfills (Promise/Object.assign/fetch) auto-load on init (browser only)
 */

import React from 'react';
import { featureDetection } from './feature-detection';

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

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

type KnownPolyfill =
  | 'intersectionObserver'
  | 'resizeObserver'
  | 'requestIdleCallback'
  | 'webAnimations'
  | 'customElements'
  | 'fetch'
  | 'promise'
  | 'objectAssign'
  | 'arrayIncludes'
  | 'stringIncludes'
  | 'cssCustomProperties';

export interface ScriptLoadOptions {
  nonce?: string;
  integrity?: string; // optional SRI
  crossOrigin?: 'anonymous' | 'use-credentials';
}

class PolyfillLoaderService {
  private loadedPolyfills = new Set<string>();
  private loadingPromises = new Map<string, Promise<void>>();
  private scriptPresence = new Set<string>(); // track script URLs inserted
  private defaultScriptOptions: ScriptLoadOptions = {};

  constructor({ autoLoadCritical = true, scriptOptions }: { autoLoadCritical?: boolean; scriptOptions?: ScriptLoadOptions } = {}) {
    if (scriptOptions) this.defaultScriptOptions = { ...scriptOptions };
    if (isBrowser && autoLoadCritical) {
      // fire and forget; don’t block app
      this.loadCriticalPolyfills().catch(() => void 0);
    }
  }

  // --- Public controls -------------------------------------------------------

  setDefaultScriptOptions(opts: ScriptLoadOptions) {
    this.defaultScriptOptions = { ...opts };
  }

  public isPolyfillLoaded(name: KnownPolyfill): boolean {
    return this.loadedPolyfills.has(name);
  }

  public getLoadedPolyfills(): string[] {
    return Array.from(this.loadedPolyfills);
  }

  public async loadPolyfills(config: Partial<PolyfillConfig>, scriptOptions?: ScriptLoadOptions): Promise<PolyfillLoadResult> {
    const result: PolyfillLoadResult = { loaded: [], failed: [], skipped: [] };
    if (!isBrowser) return { ...result, skipped: Object.keys(config) };

    const needed = this.determineNeededPolyfills(config);

    const loads = needed.map(async (polyfill) => {
      try {
        await this.loadPolyfill(polyfill as KnownPolyfill, scriptOptions);
        result.loaded.push(polyfill);
      } catch {
        result.failed.push(polyfill);
      }
    });

    await Promise.allSettled(loads);

    // mark skipped (requested but not needed or already loaded)
    Object.keys(config).forEach((k) => {
      const key = k as KnownPolyfill;
      if ((config as any)[key] && !needed.includes(key) && this.isSatisfied(key)) {
        result.skipped.push(key);
      }
    });

    return result;
  }

  public async loadPolyfillsForFeatures(features: KnownPolyfill[], scriptOptions?: ScriptLoadOptions): Promise<PolyfillLoadResult> {
    const cfg: Partial<PolyfillConfig> = {};
    features.forEach((f) => ((cfg as any)[f] = true));
    return this.loadPolyfills(cfg, scriptOptions);
  }

  public async ensurePolyfillsLoaded(polyfills: KnownPolyfill[], scriptOptions?: ScriptLoadOptions): Promise<void> {
    if (!isBrowser) return;
    await Promise.all(polyfills.map((p) => this.loadPolyfill(p, scriptOptions)));
  }

  // --- Internal core ---------------------------------------------------------

  private async loadCriticalPolyfills(): Promise<void> {
    await this.loadPolyfills(
      {
        promise: true,
        objectAssign: true,
        fetch: true,
      },
      this.defaultScriptOptions
    );
  }

  private determineNeededPolyfills(config: Partial<PolyfillConfig>): KnownPolyfill[] {
    const need: KnownPolyfill[] = [];
    const f = this.safeGetFeatures();

    const want = (k: keyof PolyfillConfig) => Boolean((config as any)[k]);

    if (want('intersectionObserver') && !this.hasIntersectionObserver(f)) need.push('intersectionObserver');
    if (want('resizeObserver') && !this.hasResizeObserver(f)) need.push('resizeObserver');
    if (want('requestIdleCallback') && !this.hasRequestIdleCallback(f)) need.push('requestIdleCallback');
    if (want('webAnimations') && !this.hasWebAnimations(f)) need.push('webAnimations');
    if (want('customElements') && !this.hasCustomElements()) need.push('customElements');
    if (want('fetch') && !this.hasFetch()) need.push('fetch');
    if (want('promise') && !this.hasPromise()) need.push('promise');
    if (want('objectAssign') && !this.hasObjectAssign()) need.push('objectAssign');
    if (want('arrayIncludes') && !this.hasArrayIncludes()) need.push('arrayIncludes');
    if (want('stringIncludes') && !this.hasStringIncludes()) need.push('stringIncludes');
    if (want('cssCustomProperties') && !this.hasCSSVars(f)) need.push('cssCustomProperties');

    return need.filter((n) => !this.loadedPolyfills.has(n));
  }

  private async loadPolyfill(name: KnownPolyfill, scriptOptions?: ScriptLoadOptions): Promise<void> {
    if (!isBrowser) return;

    if (this.loadedPolyfills.has(name) || this.isSatisfiedByEnv(name)) {
      this.loadedPolyfills.add(name);
      return;
    }

    if (this.loadingPromises.has(name)) {
      return this.loadingPromises.get(name)!;
    }

    const p = this.loadPolyfillImpl(name, scriptOptions)
      .then(() => {
        // post-check to ensure environment is now satisfied
        if (!this.isSatisfiedByEnv(name)) {
          throw new Error(`Polyfill "${name}" did not attach expected globals`);
        }
        this.loadedPolyfills.add(name);
      })
      .finally(() => {
        this.loadingPromises.delete(name);
      });

    this.loadingPromises.set(name, p);
    return p;
  }

  private async loadPolyfillImpl(name: KnownPolyfill, scriptOptions?: ScriptLoadOptions): Promise<void> {
    switch (name) {
      case 'intersectionObserver':
        if (this.hasIntersectionObserver()) return;
        await this.loadScriptOnce(
          'https://cdn.jsdelivr.net/npm/intersection-observer@0.12.2/intersection-observer.js',
          scriptOptions
        );
        return;

      case 'resizeObserver':
        if (this.hasResizeObserver()) return;
        await this.loadScriptOnce(
          'https://cdn.jsdelivr.net/npm/resize-observer-polyfill@1.5.1/dist/ResizeObserver.global.js',
          scriptOptions
        );
        return;

      case 'requestIdleCallback':
        if (this.hasRequestIdleCallback()) return;
        (window as any).requestIdleCallback = (cb: IdleRequestCallback) => {
          const start = Date.now();
          return window.setTimeout(() => {
            cb({
              didTimeout: false,
              timeRemaining: () => Math.max(0, 50 - (Date.now() - start)),
            } as IdleDeadline);
          }, 1);
        };
        (window as any).cancelIdleCallback = (id: number) => clearTimeout(id);
        return;

      case 'webAnimations':
        if (this.hasWebAnimations()) return;
        await this.loadScriptOnce('https://cdn.jsdelivr.net/npm/web-animations-js@2.3.2/web-animations.min.js', scriptOptions);
        return;

      case 'customElements':
        if (this.hasCustomElements()) return;
        await this.loadScriptOnce('https://cdn.jsdelivr.net/npm/@webcomponents/custom-elements@1.6.0/custom-elements.min.js', scriptOptions);
        return;

      case 'fetch':
        if (this.hasFetch()) return;
        await this.loadScriptOnce('https://cdn.jsdelivr.net/npm/whatwg-fetch@3.6.20/dist/fetch.umd.js', scriptOptions);
        return;

      case 'promise':
        if (this.hasPromise()) return;
        await this.loadScriptOnce('https://cdn.jsdelivr.net/npm/promise-polyfill@8.3.0/dist/polyfill.min.js', scriptOptions);
        return;

      case 'objectAssign':
        if (this.hasObjectAssign()) return;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (Object as any).assign =
          (Object as any).assign ||
          function (target: any, ...sources: any[]) {
            if (target == null) throw new TypeError('Cannot convert undefined or null to object');
            const to = Object(target);
            for (const src of sources) {
              if (src != null) {
                for (const key in src) {
                  if (Object.prototype.hasOwnProperty.call(src, key)) {
                    (to as any)[key] = (src as any)[key];
                  }
                }
              }
            }
            return to;
          };
        return;

      case 'arrayIncludes':
        if (this.hasArrayIncludes()) return;
        // eslint-disable-next-line no-extend-native
        (Array.prototype as any).includes =
          (Array.prototype as any).includes ||
          function (searchElement: any, fromIndex?: number) {
            const O = Object(this);
            const len = parseInt((O as any).length, 10) || 0;
            if (len === 0) return false;
            const n = parseInt(String(fromIndex ?? 0), 10) || 0;
            let k = n >= 0 ? n : Math.max(len + n, 0);
            while (k < len) {
              if ((O as any)[k] === searchElement) return true;
              k++;
            }
            return false;
          };
        return;

      case 'stringIncludes':
        if (this.hasStringIncludes()) return;
        // eslint-disable-next-line no-extend-native
        (String.prototype as any).includes =
          (String.prototype as any).includes ||
          function (search: string, start?: number) {
            const s = String(this);
            const idx = typeof start === 'number' ? start : 0;
            if (idx + search.length > s.length) return false;
            return s.indexOf(search, idx) !== -1;
          };
        return;

      case 'cssCustomProperties':
        if (this.hasCSSVars()) return;
        await this.loadScriptOnce(
          'https://cdn.jsdelivr.net/npm/css-vars-ponyfill@2.4.9/dist/css-vars-ponyfill.min.js',
          scriptOptions
        );
        if ((window as any).cssVars) {
          (window as any).cssVars({
            onlyLegacy: true,
            preserveStatic: false,
            preserveVars: false,
            updateURLs: true,
            shadowDOM: true,
            watch: false,
          });
        }
        return;

      default:
        throw new Error(`Unknown polyfill: ${name}`);
    }
  }

  // --- Environment checks ----------------------------------------------------

  private safeGetFeatures() {
    try {
      return featureDetection.getFeatures();
    } catch {
      return null; // featureDetection may not be ready yet
    }
  }

  private hasIntersectionObserver(f?: ReturnType<typeof featureDetection.getFeatures> | null): boolean {
    if (!isBrowser) return true;
    return !!(window as any).IntersectionObserver || !!(f && f.intersectionObserver);
  }

  private hasResizeObserver(f?: ReturnType<typeof featureDetection.getFeatures> | null): boolean {
    if (!isBrowser) return true;
    return !!(window as any).ResizeObserver || !!(f && f.resizeObserver);
  }

  private hasRequestIdleCallback(f?: ReturnType<typeof featureDetection.getFeatures> | null): boolean {
    if (!isBrowser) return true;
    return 'requestIdleCallback' in window || !!(f && f.requestIdleCallback);
  }

  private hasWebAnimations(f?: ReturnType<typeof featureDetection.getFeatures> | null): boolean {
    if (!isBrowser) return true;
    return 'animate' in document.createElement('div') || !!(f && f.webAnimations);
  }

  private hasCustomElements(): boolean {
    if (!isBrowser) return true;
    return 'customElements' in window;
  }

  private hasFetch(): boolean {
    if (!isBrowser) return true;
    return 'fetch' in window;
  }

  private hasPromise(): boolean {
    if (!isBrowser) return true;
    return !!window.Promise;
  }

  private hasObjectAssign(): boolean {
    if (!isBrowser) return true;
    return typeof Object.assign === 'function';
  }

  private hasArrayIncludes(): boolean {
    if (!isBrowser) return true;
    return typeof Array.prototype.includes === 'function';
  }

  private hasStringIncludes(): boolean {
    if (!isBrowser) return true;
    return typeof String.prototype.includes === 'function';
  }

  private hasCSSVars(f?: ReturnType<typeof featureDetection.getFeatures> | null): boolean {
    if (!isBrowser) return true;
    try {
      return (f && f.cssCustomProperties) || (window as any).CSS?.supports?.('color', 'var(--x)') || false;
    } catch {
      return false;
    }
  }

  private isSatisfiedByEnv(name: KnownPolyfill): boolean {
    const f = this.safeGetFeatures();
    switch (name) {
      case 'intersectionObserver':
        return this.hasIntersectionObserver(f);
      case 'resizeObserver':
        return this.hasResizeObserver(f);
      case 'requestIdleCallback':
        return this.hasRequestIdleCallback(f);
      case 'webAnimations':
        return this.hasWebAnimations(f);
      case 'customElements':
        return this.hasCustomElements();
      case 'fetch':
        return this.hasFetch();
      case 'promise':
        return this.hasPromise();
      case 'objectAssign':
        return this.hasObjectAssign();
      case 'arrayIncludes':
        return this.hasArrayIncludes();
      case 'stringIncludes':
        return this.hasStringIncludes();
      case 'cssCustomProperties':
        return this.hasCSSVars(f);
    }
  }

  private isSatisfied(name: string): boolean {
    return this.loadedPolyfills.has(name) || this.isSatisfiedByEnv(name as KnownPolyfill);
  }

  // --- Script loader (CSP/SRI aware, idempotent) -----------------------------

  private loadScriptOnce(src: string, opts?: ScriptLoadOptions): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      if (!isBrowser) {
        resolve();
        return;
      }
      if (this.scriptPresence.has(src)) {
        setTimeout(resolve, 0);
        return;
      }
      const existing = document.querySelector<HTMLScriptElement>(`script[src="${src}"]`);
      if (existing) {
        this.scriptPresence.add(src);
        setTimeout(resolve, 0);
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.async = true;

      const finalOpts = { ...this.defaultScriptOptions, ...(opts || {}) };
      if (finalOpts.nonce) script.setAttribute('nonce', finalOpts.nonce);
      if (finalOpts.integrity) {
        script.integrity = finalOpts.integrity;
        script.crossOrigin = finalOpts.crossOrigin || 'anonymous';
      } else if (finalOpts.crossOrigin) {
        script.crossOrigin = finalOpts.crossOrigin;
      }

      script.onload = () => {
        this.scriptPresence.add(src);
        resolve();
      };
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);
    });
  }
}

// --- Singleton ---------------------------------------------------------------
export const polyfillLoader = new PolyfillLoaderService();

// --- React hook --------------------------------------------------------------
export function usePolyfills(config: Partial<PolyfillConfig>, scriptOptions?: ScriptLoadOptions) {
  const [loadResult, setLoadResult] = React.useState<PolyfillLoadResult | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);

  React.useEffect(() => {
    if (!isBrowser) {
      setLoadResult({ loaded: [], failed: [], skipped: Object.keys(config) });
      setIsLoading(false);
      return;
    }
    let mounted = true;
    (async () => {
      try {
        const result = await polyfillLoader.loadPolyfills(config, scriptOptions);
        if (mounted) {
          setLoadResult(result);
          setIsLoading(false);
        }
      } catch {
        if (mounted) {
          setLoadResult({ loaded: [], failed: Object.keys(config), skipped: [] });
          setIsLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(config), JSON.stringify(scriptOptions || {})]);

  return {
    loadResult,
    isLoading,
    isPolyfillLoaded: (name: KnownPolyfill) => polyfillLoader.isPolyfillLoaded(name),
    getLoadedPolyfills: () => polyfillLoader.getLoadedPolyfills(),
  };
}

export default polyfillLoader;
