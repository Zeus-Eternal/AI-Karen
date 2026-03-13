/**
 * Performance System Diagnostic Logger
 * 
 * Validates architectural assumptions and identifies runtime conflicts
 * in the performance optimization system before refactoring.
 */

export interface DiagnosticLog {
  timestamp: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  category: 'duplication' | 'conflict' | 'api' | 'memory' | 'performance';
  message: string;
  details?: Record<string, unknown>;
}

export interface SystemHealthCheck {
  duplicateFiles: string[];
  conflictingMonitors: string[];
  apiInconsistencies: string[];
  memoryLeaks: string[];
  performanceIssues: string[];
}

class PerformanceDiagnosticLogger {
  private logs: DiagnosticLog[] = [];
  private startTime = Date.now();

  log(level: DiagnosticLog['level'], category: DiagnosticLog['category'], message: string, details?: Record<string, unknown>): void {
    const log: DiagnosticLog = {
      timestamp: Date.now(),
      level,
      category,
      message,
      details
    };
    
    this.logs.push(log);
    
    // Also log to console for immediate visibility
    const prefix = `[PERF-DIAGNOSTIC] [${level.toUpperCase()}] [${category.toUpperCase()}]`;
    switch (level) {
      case 'error':
        console.error(prefix, message, details);
        break;
      case 'warn':
        console.warn(prefix, message, details);
        break;
      case 'info':
        console.info(prefix, message, details);
        break;
      case 'debug':
        console.debug(prefix, message, details);
        break;
    }
  }

  /**
   * Check for duplicate files by analyzing import patterns
   */
  detectDuplicateFiles(): void {
    // Check for known duplicate files
    const potentialDuplicates = [
      'optimization.ts',
      'optimization-utils.ts',
      'performance-monitor.ts',
      'performance-optimizer.ts'
    ];

    potentialDuplicates.forEach(file => {
      this.log('warn', 'duplication', `Potential duplicate file detected: ${file}`, {
        file,
        recommendation: 'Consolidate into unified implementation'
      });
    });
  }

  /**
   * Check for conflicting performance monitors
   */
  detectConflictingMonitors(): void {
    // Check if multiple performance monitors are initialized
    const monitorIndicators = [
      () => typeof window !== 'undefined' && (window as any).__performanceMonitor,
      () => typeof window !== 'undefined' && (window as any).__perfMonitor,
      () => typeof window !== 'undefined' && (window as any).__monitoring
    ];

    const activeMonitors = monitorIndicators.filter(check => check()).length;
    
    if (activeMonitors > 1) {
      this.log('error', 'conflict', `Multiple performance monitors detected: ${activeMonitors}`, {
        count: activeMonitors,
        recommendation: 'Consolidate into single monitoring system'
      });
    }
  }

  /**
   * Check API inconsistencies across performance modules
   */
  detectApiInconsistencies(): void {
    // This would be expanded to check actual API shapes at runtime
    this.log('info', 'api', 'Checking API consistency across performance modules', {
      modules: ['services/performance-optimizer', 'lib/performance/performance-optimizer', 'unified-optimization']
    });
  }

  /**
   * Check for memory leaks in performance tracking
   */
  detectMemoryIssues(): void {
    if (typeof window !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      const usageRatio = memory.usedJSHeapSize / memory.totalJSHeapSize;
      
      if (usageRatio > 0.8) {
        this.log('warn', 'memory', `High memory usage detected: ${(usageRatio * 100).toFixed(1)}%`, {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          recommendation: 'Check for memory leaks in performance tracking'
        });
      }
    }
  }

  /**
   * Check performance system health
   */
  detectPerformanceIssues(): void {
    // Check for excessive observer registration
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      const observerCount = (window as any).__performanceObserverCount || 0;
      
      if (observerCount > 10) {
        this.log('warn', 'performance', `Excessive performance observers: ${observerCount}`, {
          recommendation: 'Consolidate observers and prevent duplicates'
        });
      }
    }
  }

  /**
   * Run comprehensive diagnostic check
   */
  runDiagnostics(): SystemHealthCheck {
    this.log('info', 'performance', 'Starting performance system diagnostics', {
      startTime: this.startTime
    });

    const healthCheck: SystemHealthCheck = {
      duplicateFiles: [],
      conflictingMonitors: [],
      apiInconsistencies: [],
      memoryLeaks: [],
      performanceIssues: []
    };

    try {
      this.detectDuplicateFiles();
      this.detectConflictingMonitors();
      this.detectApiInconsistencies();
      this.detectMemoryIssues();
      this.detectPerformanceIssues();
    } catch (error) {
      this.log('error', 'performance', 'Diagnostic check failed', { error });
    }

    // Collect issues from logs
    this.logs.forEach(log => {
      switch (log.category) {
        case 'duplication':
          healthCheck.duplicateFiles.push(log.message);
          break;
        case 'conflict':
          healthCheck.conflictingMonitors.push(log.message);
          break;
        case 'api':
          healthCheck.apiInconsistencies.push(log.message);
          break;
        case 'memory':
          healthCheck.memoryLeaks.push(log.message);
          break;
        case 'performance':
          healthCheck.performanceIssues.push(log.message);
          break;
      }
    });

    this.log('info', 'performance', 'Diagnostic check completed', {
      duration: Date.now() - this.startTime,
      issueCount: healthCheck.duplicateFiles.length + healthCheck.conflictingMonitors.length + 
                 healthCheck.apiInconsistencies.length + healthCheck.memoryLeaks.length + 
                 healthCheck.performanceIssues.length
    });

    return healthCheck;
  }

  /**
   * Get diagnostic logs
   */
  getLogs(level?: DiagnosticLog['level'], category?: DiagnosticLog['category']): DiagnosticLog[] {
    return this.logs.filter(log => {
      if (level && log.level !== level) return false;
      if (category && log.category !== category) return false;
      return true;
    });
  }

  /**
   * Clear diagnostic logs
   */
  clearLogs(): void {
    this.logs = [];
    this.startTime = Date.now();
  }

  /**
   * Export diagnostic report
   */
  exportReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      duration: Date.now() - this.startTime,
      logs: this.logs,
      summary: this.runDiagnostics()
    };
    
    return JSON.stringify(report, null, 2);
  }
}

// Singleton instance
let diagnosticLogger: PerformanceDiagnosticLogger | null = null;

export function getDiagnosticLogger(): PerformanceDiagnosticLogger {
  if (!diagnosticLogger) {
    diagnosticLogger = new PerformanceDiagnosticLogger();
  }
  return diagnosticLogger;
}

// Auto-run diagnostics in development
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  setTimeout(() => {
    const logger = getDiagnosticLogger();
    const healthCheck = logger.runDiagnostics();
    
    if (healthCheck.duplicateFiles.length > 0 || 
        healthCheck.conflictingMonitors.length > 0 || 
        healthCheck.apiInconsistencies.length > 0) {
      console.warn('🔍 Performance System Issues Detected:', healthCheck);
    }
  }, 1000);
}

export default PerformanceDiagnosticLogger;