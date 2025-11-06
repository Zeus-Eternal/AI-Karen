// Frontend UI Diagnostics and Performance Monitoring (production-grade)
// Validates rendering performance, accessibility, compatibility, and security

export type Category = 'performance' | 'accessibility' | 'compatibility' | 'security';
export type Level = 'critical' | 'warning' | 'info';

export interface DiagnosticResult {
  category: Category;
  level: Level;
  message: string;
  details?: Record<string, unknown>;
  suggestion?: string;
}

export interface ContrastIssue {
  node: Element;
  fg: string;
  bg: string;
  ratio: number;
}

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

class UIDiagnostics {
  private static instance: UIDiagnostics;
  private results: DiagnosticResult[] = [];
  private performanceMetrics: Map<string, number> = new Map();

  static getInstance(): UIDiagnostics {
    if (!UIDiagnostics.instance) {
      UIDiagnostics.instance = new UIDiagnostics();
    }
    return UIDiagnostics.instance;
  }

  // ---------------- Performance ----------------

  measureRenderTime(componentName: string, startTime: number): number {
    if (!isBrowser || typeof performance === 'undefined') return 0;
    const endTime = performance.now();
    const duration = endTime - startTime;
    this.performanceMetrics.set(componentName, duration);

    if (duration > 100) {
      this.addResult({
        category: 'performance',
        level: 'warning',
        message: `Slow render detected for ${componentName}`,
        details: { duration: Number(duration.toFixed(2)), component: componentName, thresholdMs: 100 },
        suggestion: 'Consider memoization (React.memo/useMemo/useCallback) or list virtualization.',
      });
    }

    return duration;
  }

  measureMessageRendering(messageCount: number, threshold = 50): void {
    if (messageCount > threshold) {
      this.addResult({
        category: 'performance',
        level: 'critical',
        message: 'Large message count may impact performance',
        details: { messageCount, threshold },
        suggestion: 'Implement virtualization with react-window/react-virtualized and windowed rendering.',
      });
    }
  }

  checkMemoryUsage(): void {
    if (!isBrowser || !(performance as any)?.memory) return;
    const mem = (performance as any).memory;
    const usedMB = mem.usedJSHeapSize / 1048576;
    const totalMB = mem.totalJSHeapSize / 1048576;

    if (usedMB > 100) {
      this.addResult({
        category: 'performance',
        level: 'warning',
        message: 'High memory usage detected',
        details: { usedMB: Number(usedMB.toFixed(2)), totalMB: Number(totalMB.toFixed(2)) },
        suggestion: 'Check for memory leaks; verify effect cleanup and remove unbounded caches.',
      });
    }
  }

  // ---------------- Accessibility ----------------

  checkAccessibility(root: HTMLElement | null): void {
    if (!isBrowser || !root) return;
    const issues: string[] = [];

    // Landmarks: header/main/nav/footer/aside OR role equivalents
    const hasLandmark =
      root.querySelector('main, header, nav, footer, aside, [role="main"], [role="navigation"], [role="contentinfo"]') !== null;
    if (!hasLandmark) issues.push('Missing ARIA landmarks (main/header/nav/footer/aside).');

    // Focusable elements should be visible and not clipped from tab order
    const focusables = root.querySelectorAll<HTMLElement>(
      'button, input, textarea, select, a[href], [tabindex]:not([tabindex="-1"])'
    );
    let hiddenFocusables = 0;
    focusables.forEach((el) => {
      const style = window.getComputedStyle(el);
      if (style.visibility === 'hidden' || style.display === 'none') hiddenFocusables++;
    });
    if (hiddenFocusables > 0) {
      issues.push(`Found ${hiddenFocusables} focusable element(s) not keyboard accessible (hidden/none).`);
    }

    // Images need alt text
    const imgs = root.querySelectorAll('img');
    const missingAlt = Array.from(imgs).filter((img) => !img.hasAttribute('alt') || img.getAttribute('alt') === '').length;
    if (missingAlt > 0) {
      issues.push(`Found ${missingAlt} image(s) missing descriptive alt text.`);
    }

    // Labels associated with inputs
    const inputs = root.querySelectorAll('input, textarea, select');
    const unlabeled = Array.from(inputs).filter((el) => {
      const id = el.getAttribute('id');
      if (!id) return true;
      return !root.querySelector(`label[for="${id}"]`) && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby');
    }).length;
    if (unlabeled > 0) {
      issues.push(`Found ${unlabeled} form control(s) without accessible label.`);
    }

    // Contrast quick check (approx WCAG). We’ll sample text nodes.
    const contrastProblems: ContrastIssue[] = [];
    const textNodes = root.querySelectorAll<HTMLElement>('p, span, div, li, h1, h2, h3, h4, h5, h6, label, small');
    textNodes.forEach((el) => {
      const style = window.getComputedStyle(el);
      const fg = style.color;
      const bg = this.getEffectiveBackgroundColor(el);
      if (!fg || !bg) return;

      const ratio = this.contrastRatio(fg, bg);
      const fontSizePx = parseFloat(style.fontSize || '16');
      const fontWeight = parseInt(style.fontWeight || '400', 10);
      const isBold = fontWeight >= 700;
      // WCAG AA minimum: 4.5:1 normal text, 3:1 for large text (>=18pt ~ 24px, or >=14pt ~ 18.66px + bold)
      const isLarge = fontSizePx >= 24 || (isBold && fontSizePx >= 18.66);
      const needed = isLarge ? 3 : 4.5;

      if (ratio < needed) {
        contrastProblems.push({ node: el, fg, bg, ratio: Number(ratio.toFixed(2)) as any });
      }
    });

    if (contrastProblems.length > 0) {
      issues.push(`Detected ${contrastProblems.length} potential low-contrast text element(s).`);
    }

    if (issues.length > 0) {
      this.addResult({
        category: 'accessibility',
        level: 'warning',
        message: 'Accessibility issues detected',
        details: { issues, contrastExamples: contrastProblems.slice(0, 5) },
        suggestion:
          'Add landmarks, ensure labels for inputs, provide alt text, and meet WCAG contrast. Test with a screen reader.',
      });
    }
  }

  // ---------------- Compatibility ----------------

  checkBrowserCompatibility(): void {
    if (!isBrowser) return;
    const issues: string[] = [];

    // CSS supports
    if (!('CSS' in window) || !CSS.supports('display', 'grid')) issues.push('CSS Grid not supported.');
    if (!('CSS' in window) || !CSS.supports('color', 'var(--test)')) issues.push('CSS Custom Properties not supported.');

    // Parser probes for syntax (optional chaining, nullish coalescing)
    if (!this.syntaxSupported('return (a?.b)')) {
      issues.push('Optional chaining (?.) not supported.');
    }
    if (!this.syntaxSupported('return (x ?? "d")')) {
      issues.push('Nullish coalescing (??) not supported.');
    }

    // IntersectionObserver
    if (!('IntersectionObserver' in window)) {
      issues.push('IntersectionObserver not supported — virtualization may require a polyfill.');
    }

    if (issues.length > 0) {
      this.addResult({
        category: 'compatibility',
        level: 'warning',
        message: 'Browser compatibility issues detected',
        details: { issues, userAgent: navigator.userAgent },
        suggestion: 'Load polyfills/ponyfills or provide degraded behavior for legacy browsers.',
      });
    }
  }

  // ---------------- Security ----------------

  checkSecurity(root: HTMLElement | null): void {
    if (!isBrowser || !root) return;
    const issues: string[] = [];

    // Inline <script> blocks increase XSS risk
    const scripts = root.querySelectorAll('script');
    if (scripts.length > 0) {
      issues.push('Inline <script> elements found — consider moving to external scripts and enforcing CSP.');
    }

    // Dangerous inline handlers (on*) and javascript: URLs
    const allEls = root.querySelectorAll<HTMLElement>('*');
    let inlineHandlers = 0;
    let jsHref = 0;

    allEls.forEach((el) => {
      for (const attr of Array.from(el.attributes)) {
        const name = attr.name.toLowerCase();
        const value = (attr.value || '').toLowerCase();
        if (name.startsWith('on')) inlineHandlers++;
        if (name === 'href' && value.startsWith('javascript:')) jsHref++;
      }
    });

    if (inlineHandlers > 0) {
      issues.push(`Found ${inlineHandlers} inline event handler(s) (on*). Prefer addEventListener and safe bindings.`);
    }
    if (jsHref > 0) {
      issues.push(`Found ${jsHref} link(s) with javascript: URLs — replace with safe handlers.`);
    }

    if (issues.length > 0) {
      this.addResult({
        category: 'security',
        level: 'warning',
        message: 'Potential client-side security issues detected',
        details: { issues },
        suggestion: 'Sanitize HTML (e.g., DOMPurify), enforce strict CSP, avoid inline handlers and javascript: URLs.',
      });
    }
  }

  // ---------------- Chat-specific composite ----------------

  checkChatInterface(root: HTMLElement | null, messageCount: number): void {
    this.measureMessageRendering(messageCount);
    this.checkAccessibility(root);
    this.checkSecurity(root);

    if (!root) return;

    const bubbles = root.querySelectorAll('[class*="message"], [class*="bubble"]');
    if (bubbles.length > 50) {
      this.addResult({
        category: 'performance',
        level: 'critical',
        message: 'Chat interface likely missing virtualization for message list',
        details: { visibleMessageNodes: bubbles.length, threshold: 50 },
        suggestion: 'Use react-window/react-virtualized and windowed rendering to keep DOM small.',
      });
    }
  }

  // ---------------- Results / Reports ----------------

  getResults(): DiagnosticResult[] {
    return [...this.results];
  }

  clearResults(): void {
    this.results = [];
  }

  generateReport(): string {
    const critical = this.results.filter((r) => r.level === 'critical');
    const warnings = this.results.filter((r) => r.level === 'warning');
    const info = this.results.filter((r) => r.level === 'info');

    const perfLines = Array.from(this.performanceMetrics.entries()).map(
      ([name, time]) => `• ${name}: ${time.toFixed(2)}ms`
    );

    return [
      '# UI Diagnostics Report',
      '',
      `**Critical:** ${critical.length}  |  **Warnings:** ${warnings.length}  |  **Info:** ${info.length}`,
      '',
      critical.length ? '## Critical\n' + critical.map((r) => `- ${r.message}`).join('\n') + '\n' : '',
      warnings.length ? '## Warnings\n' + warnings.map((r) => `- ${r.message}`).join('\n') + '\n' : '',
      info.length ? '## Info\n' + info.map((r) => `- ${r.message}`).join('\n') + '\n' : '',
      '## Performance Metrics',
      perfLines.length ? perfLines.join('\n') : 'No render metrics recorded.',
      '',
    ]
      .join('\n')
      .trim();
  }

  // ---------------- Internals ----------------

  private addResult(result: DiagnosticResult): void {
    this.results.push(result);
    this.logResult(result);
  }

  private logResult(result: DiagnosticResult): void {
    const emoji = result.level === 'critical' ? '🚨' : result.level === 'warning' ? '⚠️' : 'ℹ️';
    // Keep console minimal but structured
    // eslint-disable-next-line no-console
    console.group(`${emoji} UI Diagnostic: ${result.category.toUpperCase()} - ${result.level.toUpperCase()}`);
    console.log('Message:', result.message);
    if (result.details) console.log('Details:', result.details);
    if (result.suggestion) console.log('Suggestion:', result.suggestion);
    // eslint-disable-next-line no-console
    console.groupEnd();
  }

  private syntaxSupported(body: string): boolean {
    if (!isBrowser) return true; // SSR: assume modern toolchain
    try {
      // Use Function constructor to probe parser support
      // eslint-disable-next-line no-new-func
      new Function(body);
      return true;
    } catch {
      return false;
    }
  }

  private parseColorToRgb(cssColor: string): { r: number; g: number; b: number } | null {
    const ctx = (document as any).__colorCtx || (() => {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      const c = canvas.getContext('2d');
      (document as any).__colorCtx = c;
      return c;
    })();
    if (!ctx) return null;
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = '#000'; // reset
    try {
      ctx.fillStyle = cssColor;
      const computed = ctx.fillStyle; // normalized
      if (!computed) return null;
      // Set and read a pixel
      ctx.fillRect(0, 0, 1, 1);
      const rgba = ctx.getImageData(0, 0, 1, 1).data; // [r,g,b,a]
      return { r: rgba[0], g: rgba[1], b: rgba[2] };
    } catch {
      return null;
    }
  }

  private relativeLuminance(rgb: { r: number; g: number; b: number }): number {
    const srgb = [rgb.r, rgb.g, rgb.b].map((v) => v / 255).map((c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)));
    return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
    }

  private contrastRatio(fgCss: string, bgCss: string): number {
    const fg = this.parseColorToRgb(fgCss);
    const bg = this.parseColorToRgb(bgCss);
    if (!fg || !bg) return 21; // assume best if parsing failed
    const L1 = this.relativeLuminance(fg);
    const L2 = this.relativeLuminance(bg);
    const lighter = Math.max(L1, L2);
    const darker = Math.min(L1, L2);
    return (lighter + 0.05) / (darker + 0.05);
  }

  private getEffectiveBackgroundColor(el: Element): string {
    let node: Element | null = el as Element;
    while (node && node !== document.documentElement) {
      const bg = window.getComputedStyle(node).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
        return bg;
      }
      node = node.parentElement;
    }
    // fallback to document background
    return window.getComputedStyle(document.body || document.documentElement).backgroundColor || 'rgb(255,255,255)';
  }
}

// Singleton export
const singleton = UIDiagnostics.getInstance();
export default singleton;

// ---------------- React hook ----------------

import * as React from 'react';

export const useUIDiagnostics = (componentName: string) => {
  const diagnostics = singleton;
  const startRef = React.useRef<number>(isBrowser && typeof performance !== 'undefined' ? performance.now() : 0);
  const rootRef = React.useRef<HTMLElement | null>(null);

  // measure render duration after paint
  React.useEffect(() => {
    if (!isBrowser) return;
    const start = startRef.current || performance.now();
    // defer to next frame to approximate mount paint cost
    const id = requestAnimationFrame(() => {
      diagnostics.measureRenderTime(componentName, start);
    });
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount

  // convenience checker
  const checkComponent = React.useCallback(
    (additional?: { messageCount?: number }) => {
      const node = rootRef.current;
      diagnostics.checkAccessibility(node);
      diagnostics.checkSecurity(node);
      if (componentName.toLowerCase().includes('chat')) {
        diagnostics.checkChatInterface(node, additional?.messageCount ?? 0);
      }
    },
    [componentName]
  );

  return {
    ref: rootRef as React.MutableRefObject<HTMLElement | null>,
    measureRender: () => diagnostics.measureRenderTime(componentName, startRef.current || 0),
    checkComponent,
    checkCompatibility: () => diagnostics.checkBrowserCompatibility(),
    checkMemory: () => diagnostics.checkMemoryUsage(),
    getResults: () => diagnostics.getResults(),
    clearResults: () => diagnostics.clearResults(),
    generateReport: () => diagnostics.generateReport(),
  };
};
