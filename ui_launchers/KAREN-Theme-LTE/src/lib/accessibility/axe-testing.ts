/**
 * Axe-core Accessibility Testing
 * Comprehensive accessibility testing with automated and manual checks
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { auditLogger } from '@/lib/audit-logger';

// Import axe-core dynamically
let axe: {
  run: (context?: Element | string | object, options?: object) => Promise<{ violations: AxeViolation[] }>;
  default?: {
    run: (context?: Element | string | object, options?: object) => Promise<{ violations: AxeViolation[] }>;
  };
  [key: string]: unknown;
} | null = null;

// Axe violation interface
interface AxeViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor' | null;
  rule: string;
  description: string;
  tags: string[];
  target: string[];
  help: string;
  [key: string]: unknown;
}

// Accessibility test result
export interface AccessibilityTest {
  name: string;
  status: 'pass' | 'fail' | 'warning' | 'review';
  description: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  tags: string[];
  violations: AxeViolation[];
  timestamp: Date;
}

// Accessibility testing state
export interface AxeTestingState {
  isRunning: boolean;
  currentTest: AccessibilityTest | null;
  progress: number;
  results: AccessibilityTest[];
  config: AxeTestingConfig;
}

// Testing configuration
export interface AxeTestingConfig {
  includeLevel: 'A' | 'AA' | 'AAA';
  includeTags: string[];
  excludeSelectors: string[];
  reporter: 'v1' | 'v2';
  timeout: number;
}

// Hook return type
export interface UseAxeTestingReturn {
  state: AxeTestingState;
  runFullTest: () => Promise<AccessibilityTest[]>;
  runQuickTest: () => Promise<AccessibilityTest[]>;
  testComponent: (component: Element | string | object, options?: Partial<AxeTestingConfig>) => Promise<AccessibilityTest[]>;
  testPage: (url?: string) => Promise<AccessibilityTest[]>;
  getResults: () => AccessibilityTest[];
  clearResults: () => void;
  generateReport: () => string;
}

// Initialize axe-core
const initializeAxe = async (): Promise<void> => {
  if (typeof window !== 'undefined' && !axe) {
    try {
      // Dynamic import of axe-core
      const axeModule = await import('axe-core');
      axe = (axeModule.default || axeModule) as {
        run: (context?: Element | string | object, options?: object) => Promise<{ violations: AxeViolation[] }>;
        default?: { run: (context?: Element | string | object, options?: object) => Promise<{ violations: AxeViolation[] }>; };
        [key: string]: unknown;
      };
      
      if (axe && typeof axe.run === 'function') {
        console.log('Axe-core initialized successfully');
      } else {
        console.error('Axe-core loaded but run function not available');
      }
    } catch (error) {
      console.error('Failed to load axe-core:', error);
      auditLogger.log('ERROR', 'ACCESSIBILITY_ERROR', {
        error: 'Failed to load axe-core',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
      });
    }
  }
};

export function useAxeTesting(config: Partial<AxeTestingConfig> = {}): UseAxeTestingReturn {
  const defaultConfig: AxeTestingConfig = {
    includeLevel: 'AA',
    includeTags: [],
    excludeSelectors: [],
    reporter: 'v2',
    timeout: 10000,
  };
  
  const [state, setState] = useState<AxeTestingState>({
    isRunning: false,
    currentTest: null,
    progress: 0,
    results: [],
    config: { ...defaultConfig, ...config },
  });
  
  // Initialize axe-core on mount
  useEffect(() => {
    initializeAxe();
  }, []);
  
  // Run full accessibility test
  const runFullTest = useCallback(async (): Promise<AccessibilityTest[]> => {
    if (!axe) {
      setState(prev => ({ ...prev, error: 'Axe-core not loaded' }));
      throw new Error('Axe-core not loaded');
    }
    
    const startTime = Date.now();
    setState(prev => ({ ...prev, isRunning: true, progress: 0 }));
    
    try {
      const results = await axe.run({
        reporter: state.config.reporter,
        include: ['wcag2a', 'wcag21aa', 'wcag2aa'],
        exclude: state.config.excludeSelectors,
        tags: state.config.includeTags,
      });
      
      const formattedResults: AccessibilityTest[] = results.violations.map((violation: AxeViolation, index: number) => ({
        name: `Axe Test ${index + 1}`,
        status: violation.impact === 'critical' ? 'fail' : 'warning',
        description: `${violation.rule}: ${violation.description}`,
        impact: violation.impact || 'moderate',
        tags: violation.tags || [],
        violations: [violation],
        timestamp: new Date(),
      }));
      
      setState(prev => ({
        ...prev,
        isRunning: false,
        progress: 100,
        results: formattedResults,
      }));
      
      // Log results
      auditLogger.log('INFO', 'ACCESSIBILITY_TEST_COMPLETED', {
        testType: 'full',
        violationsCount: results.violations.length,
        criticalCount: results.violations.filter((v: AxeViolation) => v.impact === 'critical').length,
        testDuration: Date.now() - startTime,
      });
      
      return formattedResults;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: error instanceof Error ? error.message : 'Test failed',
      }));
      
      auditLogger.log('ERROR', 'ACCESSIBILITY_TEST_ERROR', {
        error: error instanceof Error ? error.message : 'Unknown error',
        testType: 'full',
      });
      
      return [];
    }
  }, [axe, state.config]);
  
  // Run quick accessibility test
  const runQuickTest = useCallback(async (): Promise<AccessibilityTest[]> => {
    if (!axe) {
      setState(prev => ({ ...prev, error: 'Axe-core not loaded' }));
      throw new Error('Axe-core not loaded');
    }
    
    setState(prev => ({ ...prev, isRunning: true, progress: 0 }));
    
    try {
      const results = await axe.run({
        reporter: 'v2',
        include: ['wcag2a', 'best-practice'],
        exclude: state.config.excludeSelectors,
        tags: state.config.includeTags,
      });
      
      const formattedResults: AccessibilityTest[] = results.violations.slice(0, 5).map((violation: AxeViolation, index: number) => ({
        name: `Quick Test ${index + 1}`,
        status: 'warning',
        description: `${violation.rule}: ${violation.description}`,
        impact: violation.impact || 'moderate',
        tags: violation.tags || [],
        violations: [violation],
        timestamp: new Date(),
      }));
      
      setState(prev => ({
        ...prev,
        isRunning: false,
        progress: 100,
        results: formattedResults,
      }));
      
      return formattedResults;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: error instanceof Error ? error.message : 'Quick test failed',
      }));
      
      auditLogger.log('ERROR', 'ACCESSIBILITY_TEST_ERROR', {
        error: error instanceof Error ? error.message : 'Unknown error',
        testType: 'quick',
      });
      
      return [];
    }
  }, [axe, state.config]);
  
  // Test specific component
  const testComponent = useCallback(async (component: Element | string | object, options: Partial<AxeTestingConfig> = {}): Promise<AccessibilityTest[]> => {
    if (!axe) {
      throw new Error('Axe-core not loaded');
    }
    
    setState(prev => ({ ...prev, isRunning: true, currentTest: { name: 'Component Test', status: 'warning', description: 'Testing component...', impact: 'moderate', tags: [], violations: [], timestamp: new Date() } }));
    
    try {
      const results = await axe.run(component, {
        include: ['wcag2a', 'wcag21aa', 'best-practice'],
        exclude: [...(state.config.excludeSelectors || []), ...(options.excludeSelectors || [])],
        tags: [...(state.config.includeTags || []), ...(options.includeTags || [])],
        reporter: state.config.reporter,
      });
      
      const formattedResults: AccessibilityTest[] = results.violations.map((violation: AxeViolation, index: number) => ({
        name: `Component Test - ${violation.rule}`,
        status: violation.impact === 'critical' ? 'fail' : 'warning',
        description: `${violation.rule}: ${violation.description}`,
        impact: violation.impact || 'moderate',
        tags: violation.tags || [],
        violations: [violation],
        timestamp: new Date(),
      }));
      
      setState(prev => ({
        ...prev,
        isRunning: false,
        currentTest: null,
        progress: 100,
        results: formattedResults,
      }));
      
      return formattedResults;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        currentTest: null,
        error: error instanceof Error ? error.message : 'Component test failed',
      }));
      
      auditLogger.log('ERROR', 'ACCESSIBILITY_TEST_ERROR', {
        error: error instanceof Error ? error.message : 'Unknown error',
        testType: 'component',
      });
      
      return [];
    }
  }, [axe, state.config]);
  
  // Test entire page
  const testPage = useCallback(async (url?: string): Promise<AccessibilityTest[]> => {
    if (!axe) {
      throw new Error('Axe-core not loaded');
    }
    
    setState(prev => ({ ...prev, isRunning: true, currentTest: { name: 'Page Test', status: 'warning', description: 'Testing page...', impact: 'moderate', tags: [], violations: [], timestamp: new Date() } }));
    
    try {
      const target = url ? await fetch(url).then(res => res.text()).then(html => {
        const parser = new DOMParser();
        return parser.parseFromString(html, 'text/html');
      }) : document.documentElement;
      
      const results = await axe.run(target, {
        include: ['wcag2a', 'wcag21aa', 'best-practice'],
        exclude: state.config.excludeSelectors,
        tags: state.config.includeTags,
        reporter: state.config.reporter,
      });
      
      const formattedResults: AccessibilityTest[] = results.violations.map((violation: AxeViolation, index: number) => ({
        name: `Page Test - ${violation.rule}`,
        status: violation.impact === 'critical' ? 'fail' : 'warning',
        description: `${violation.rule}: ${violation.description}`,
        impact: violation.impact || 'moderate',
        tags: violation.tags || [],
        violations: [violation],
        timestamp: new Date(),
      }));
      
      setState(prev => ({
        ...prev,
        isRunning: false,
        currentTest: null,
        progress: 100,
        results: formattedResults,
      }));
      
      return formattedResults;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        currentTest: null,
        error: error instanceof Error ? error.message : 'Page test failed',
      }));
      
      auditLogger.log('ERROR', 'ACCESSIBILITY_TEST_ERROR', {
        error: error instanceof Error ? error.message : 'Unknown error',
        testType: 'page',
      });
      
      return [];
    }
  }, [axe, state.config]);
  
  // Get test results
  const getResults = useCallback((): AccessibilityTest[] => {
    return state.results;
  }, [state.results]);
  
  // Clear results
  const clearResults = useCallback(() => {
    setState(prev => ({ ...prev, results: [] }));
  }, []);
  
  // Generate accessibility report
  const generateReport = useCallback((): string => {
    const results = state.results;
    
    if (results.length === 0) {
      return 'No accessibility violations found. Great job!';
    }
    
    const summary = {
      total: results.length,
      critical: results.filter(r => r.status === 'fail' && r.impact === 'critical').length,
      serious: results.filter(r => r.status === 'fail' && r.impact === 'serious').length,
      moderate: results.filter(r => r.status === 'fail' && r.impact === 'moderate').length,
      minor: results.filter(r => r.status === 'fail' && r.impact === 'minor').length,
      warnings: results.filter(r => r.status === 'warning').length,
      passes: results.filter(r => r.status === 'pass').length,
    };
    
    let report = `# Accessibility Test Report\n\n`;
    report += `Generated: ${new Date().toISOString()}\n`;
    report += `WCAG Level: ${state.config.includeLevel || 'AA'}\n\n`;
    
    if (summary.total > 0) {
      report += `## Summary\n\n`;
      report += `- Total violations: ${summary.total}\n`;
      report += `- Critical: ${summary.critical}\n`;
      report += `- Serious: ${summary.serious}\n`;
      report += `- Moderate: ${summary.moderate}\n`;
      report += `- Minor: ${summary.minor}\n`;
      report += `- Warnings: ${summary.warnings}\n`;
      report += `- Passes: ${summary.passes}\n\n`;
      
      report += `## Violations\n\n`;
      
      results.forEach((result, index) => {
        if (result.status === 'fail') {
          report += `### ${index + 1}. ${result.name} - ${result.impact.toUpperCase()}\n\n`;
          report += `**Rule:** ${result.violations[0]?.rule}\n\n`;
          report += `**Description:** ${result.description}\n\n`;
          report += `**Impact:** ${result.impact}\n\n`;
          
          if (result.violations.length > 0) {
            report += `**Target Elements:**\n\n`;
            result.violations.forEach((violation: AxeViolation, vIndex: number) => {
              report += `- \`${violation.target[0]}\` (selector: \`${violation.target[0]}\`)\n`;
              report += `  - ${violation.help}\n\n`;
            });
          }
        }
      });
    }
    
    report += `## Recommendations\n\n`;
    
    if (summary.critical > 0) {
      report += `1. **Critical issues must be addressed immediately** - These prevent users with disabilities from using the application.\n\n`;
    }
    
    if (summary.serious > 0) {
      report += `2. **Serious issues should be prioritized** - These significantly impact usability.\n\n`;
    }
    
    if (summary.moderate > 0) {
      report += `3. **Moderate issues should be addressed** - These impact the user experience but don't prevent usage.\n\n`;
    }
    
    if (summary.warnings > 0) {
      report += `4. **Minor issues should be reviewed** - These are cosmetic or have minimal impact.\n\n`;
    }
    
    if (summary.passes > 0) {
      report += `5. **Great job!** - The application meets accessibility standards.\n\n`;
    }
    
    return report;
  }, [state.results, state.config]);
  
  return {
    state,
    runFullTest,
    runQuickTest,
    testComponent,
    testPage,
    getResults,
    clearResults,
    generateReport,
  };
}
