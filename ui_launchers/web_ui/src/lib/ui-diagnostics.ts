// Frontend UI Diagnostics and Performance Monitoring
// Validates rendering performance, accessibility, and cross-browser compatibility

interface DiagnosticResult {
  category: 'performance' | 'accessibility' | 'compatibility' | 'security';
  level: 'critical' | 'warning' | 'info';
  message: string;
  details?: any;
  suggestion?: string;
}

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

  // Performance diagnostics
  measureRenderTime(componentName: string, startTime: number): number {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    this.performanceMetrics.set(componentName, duration);
    
    if (duration > 100) {
      this.addResult({
        category: 'performance',
        level: 'warning',
        message: `Slow render detected for ${componentName}`,
        details: { duration: duration.toFixed(2), component: componentName },
        suggestion: 'Consider implementing virtualization or memoization'

    }
    
    return duration;
  }

  measureMessageRendering(messageCount: number): void {
    if (messageCount > 50) {
      this.addResult({
        category: 'performance',
        level: 'critical',
        message: 'Large message count may impact performance',
        details: { messageCount, threshold: 50 },
        suggestion: 'Implement message virtualization using react-window'

    }
  }

  // Accessibility diagnostics
  checkAccessibility(element: HTMLElement | null): void {
    if (!element) return;

    const issues: string[] = [];

    // Check for ARIA landmarks
    const landmarks = element.querySelectorAll('[role]');
    if (landmarks.length === 0) {
      issues.push('Missing ARIA landmark roles');
    }

    // Check for keyboard navigation
    const focusableElements = element.querySelectorAll(
      'button, input, textarea, select, a[href], [tabindex]:not([tabindex="-1"])'
    );
    let keyboardAccessible = true;
    focusableElements.forEach((el, index) => {
      const style = window.getComputedStyle(el);
      if (style.visibility === 'hidden' || style.display === 'none') {
        keyboardAccessible = false;
      }

    if (!keyboardAccessible) {
      issues.push('Some focusable elements may not be keyboard accessible');
    }

    // Check color contrast (basic check)
    const textElements = element.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
    textElements.forEach((el) => {
      const style = window.getComputedStyle(el);
      const fontSize = parseFloat(style.fontSize);
      const fontWeight = parseInt(style.fontWeight) || 400;
      // Basic contrast check - would need more sophisticated implementation for actual WCAG
      if (style.color === style.backgroundColor) {
        issues.push('Potential color contrast issue detected');
      }

    if (issues.length > 0) {
      this.addResult({
        category: 'accessibility',
        level: 'warning',
        message: 'Accessibility issues detected',
        details: { issues },
        suggestion: 'Implement proper ARIA landmarks and test with screen readers'

    }
  }

  // Cross-browser compatibility
  checkBrowserCompatibility(): void {
    const issues: string[] = [];

    // Check for modern CSS features
    if (!CSS.supports('display', 'grid')) {
      issues.push('CSS Grid not supported');
    }

    if (!CSS.supports('color', 'var(--test)')) {
      issues.push('CSS Custom Properties not supported');
    }

    // Check for modern JavaScript features using safe feature detection
    try {
      // Test optional chaining by checking if the syntax is supported
      const testObj = {};
      const testResult = (testObj as any)?.property;
      // If we get here, optional chaining is supported
    } catch {
      issues.push('Optional chaining not supported');
    }

    try {
      // Test nullish coalescing by checking if the operator is supported
      const nullValue: any = null;
      const test = nullValue ?? "default";
      // If we get here, nullish coalescing is supported
    } catch {
      issues.push('Nullish coalescing not supported');
    }

    // Check for Intersection Observer (for virtualization)
    if (!('IntersectionObserver' in window)) {
      issues.push('Intersection Observer not supported - virtualization may not work');
    }

    if (issues.length > 0) {
      this.addResult({
        category: 'compatibility',
        level: 'warning',
        message: 'Browser compatibility issues detected',
        details: { issues, userAgent: navigator.userAgent },
        suggestion: 'Consider polyfills or alternative implementations for unsupported features'

    }
  }

  // Security checks
  checkSecurity(element: HTMLElement | null): void {
    if (!element) return;

    const issues: string[] = [];

    // Check for potential XSS vulnerabilities
    const scriptElements = element.querySelectorAll('script');
    if (scriptElements.length > 0) {
      issues.push('Inline scripts detected - potential XSS risk');
    }

    // Check for unsafe innerHTML usage
    const elementsWithInnerHTML = Array.from(element.querySelectorAll('*')).filter(el => 
      el.innerHTML && el.innerHTML.includes('script') || el.innerHTML.includes('javascript:')
    );
    
    if (elementsWithInnerHTML.length > 0) {
      issues.push('Potential unsafe innerHTML usage detected');
    }

    if (issues.length > 0) {
      this.addResult({
        category: 'security',
        level: 'warning',
        message: 'Potential security issues detected',
        details: { issues },
        suggestion: 'Use DOMPurify for HTML sanitization and avoid inline scripts'

    }
  }

  // Memory usage monitoring
  checkMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const usedMB = memory.usedJSHeapSize / 1048576;
      const totalMB = memory.totalJSHeapSize / 1048576;
      
      if (usedMB > 100) {
        this.addResult({
          category: 'performance',
          level: 'warning',
          message: 'High memory usage detected',
          details: { usedMB: usedMB.toFixed(2), totalMB: totalMB.toFixed(2) },
          suggestion: 'Check for memory leaks and optimize component lifecycle'

      }
    }
  }

  // Component-specific diagnostics
  checkChatInterface(element: HTMLElement | null, messageCount: number): void {
    this.measureMessageRendering(messageCount);
    this.checkAccessibility(element);
    this.checkSecurity(element);
    
    // Check for virtualization
    const messageContainers = element?.querySelectorAll('[class*="message"], [class*="bubble"]');
    if (messageContainers && messageContainers.length > 50) {
      this.addResult({
        category: 'performance',
        level: 'critical',
        message: 'Chat interface missing message virtualization',
        details: { visibleMessages: messageContainers.length },
        suggestion: 'Implement react-window for virtualized message list'

    }
  }

  private addResult(result: DiagnosticResult): void {
    this.results.push(result);
    this.logResult(result);
  }

  private logResult(result: DiagnosticResult): void {
    const emoji = result.level === 'critical' ? '🚨' : result.level === 'warning' ? '⚠️' : 'ℹ️';
    console.group(`${emoji} UI Diagnostic: ${result.category.toUpperCase()} - ${result.level.toUpperCase()}`);
    console.log(`Message: ${result.message}`);
    if (result.details) {
      console.log('Details:', result.details);
    }
    if (result.suggestion) {
      console.log(`Suggestion: ${result.suggestion}`);
    }
    console.groupEnd();
  }

  getResults(): DiagnosticResult[] {
    return this.results;
  }

  clearResults(): void {
    this.results = [];
  }

  generateReport(): string {
    const critical = this.results.filter(r => r.level === 'critical');
    const warnings = this.results.filter(r => r.level === 'warning');
    const info = this.results.filter(r => r.level === 'info');

    return `
====================

Critical Issues: ${critical.length}
Warnings: ${warnings.length}
Info: ${info.length}

${critical.length > 0 ? 'CRITICAL ISSUES:\n' + critical.map(r => `• ${r.message}`).join('\n') + '\n' : ''}
${warnings.length > 0 ? 'WARNINGS:\n' + warnings.map(r => `• ${r.message}`).join('\n') + '\n' : ''}

Performance Metrics:
${Array.from(this.performanceMetrics.entries()).map(([component, time]) => 
  `• ${component}: ${time.toFixed(2)}ms`).join('\n')}
    `.trim();
  }
}

// React hook for component diagnostics
export const useUIDiagnostics = (componentName: string) => {
  const diagnostics = UIDiagnostics.getInstance();
  const startTime = performance.now();

  return {
    measureRender: () => diagnostics.measureRenderTime(componentName, startTime),
    checkComponent: (element: HTMLElement | null, additionalData?: any) => {
      diagnostics.checkAccessibility(element);
      diagnostics.checkSecurity(element);
      
      if (componentName.includes('Chat')) {
        diagnostics.checkChatInterface(element, additionalData?.messageCount || 0);
      }
    },
    getResults: () => diagnostics.getResults()
  };
};

// Export singleton instance
export default UIDiagnostics.getInstance();