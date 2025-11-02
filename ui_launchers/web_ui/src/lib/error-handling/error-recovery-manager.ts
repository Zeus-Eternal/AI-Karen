/**
 * Error Recovery Manager
 * 
 * Provides intelligent error recovery strategies with automatic retry logic,
 * fallback mechanisms, and adaptive recovery based on error patterns.
 */

import { ErrorInfo } from 'react';

export interface RecoveryConfig {
  maxAttempts: number;
  retryDelay: number;
  exponentialBackoff: boolean;
  section: string;
  enableSmartRecovery?: boolean;
  fallbackStrategies?: FallbackStrategy[];
}

export interface RecoveryStrategy {
  type: 'retry' | 'fallback' | 'reload' | 'redirect' | 'cache' | 'degraded';
  delay: number;
  confidence: number;
  description: string;
  actions: RecoveryAction[];
}

export interface RecoveryAction {
  type: 'clear_cache' | 'reset_state' | 'reload_component' | 'fallback_ui' | 'notify_user';
  params?: Record<string, any>;
}

export interface FallbackStrategy {
  errorPattern: RegExp;
  strategy: RecoveryStrategy;
  priority: number;
}

export class ErrorRecoveryManager {
  private config: RecoveryConfig;
  private recoveryHistory: Map<string, RecoveryAttempt[]> = new Map();
  private errorPatterns: Map<string, ErrorPattern> = new Map();

  constructor(config: RecoveryConfig) {
    this.config = {
      enableSmartRecovery: true,
      fallbackStrategies: [],
      ...config
    };

    this.initializeErrorPatterns();
  }

  private initializeErrorPatterns() {
    // Network-related errors
    this.errorPatterns.set('network', {
      patterns: [
        /network.*error/i,
        /fetch.*failed/i,
        /connection.*refused/i,
        /timeout/i,
        /cors/i
      ],
      strategy: {
        type: 'retry',
        delay: 2000,
        confidence: 0.8,
        description: 'Network connectivity issue detected. Retrying with exponential backoff.',
        actions: [
          { type: 'clear_cache' },
          { type: 'notify_user', params: { message: 'Checking network connection...' } }
        ]
      }

    // Chunk loading errors (common in SPAs)
    this.errorPatterns.set('chunk_loading', {
      patterns: [
        /loading.*chunk.*failed/i,
        /chunkloaderror/i,
        /loading.*css.*chunk.*failed/i
      ],
      strategy: {
        type: 'reload',
        delay: 1000,
        confidence: 0.9,
        description: 'Application update detected. Reloading to get latest version.',
        actions: [
          { type: 'clear_cache' },
          { type: 'notify_user', params: { message: 'Updating application...' } }
        ]
      }

    // Authentication errors
    this.errorPatterns.set('auth', {
      patterns: [
        /unauthorized/i,
        /authentication.*failed/i,
        /token.*expired/i,
        /401/i,
        /403/i
      ],
      strategy: {
        type: 'redirect',
        delay: 500,
        confidence: 0.95,
        description: 'Authentication issue detected. Redirecting to login.',
        actions: [
          { type: 'clear_cache', params: { type: 'auth' } },
          { type: 'notify_user', params: { message: 'Please log in again.' } }
        ]
      }

    // Memory/Performance errors
    this.errorPatterns.set('memory', {
      patterns: [
        /out.*of.*memory/i,
        /maximum.*call.*stack/i,
        /too.*much.*recursion/i
      ],
      strategy: {
        type: 'degraded',
        delay: 1000,
        confidence: 0.7,
        description: 'Performance issue detected. Switching to lightweight mode.',
        actions: [
          { type: 'clear_cache' },
          { type: 'reset_state' },
          { type: 'fallback_ui', params: { mode: 'minimal' } }
        ]
      }

    // Component rendering errors
    this.errorPatterns.set('render', {
      patterns: [
        /cannot.*read.*property/i,
        /undefined.*is.*not.*a.*function/i,
        /cannot.*access.*before.*initialization/i,
        /hook.*called.*outside/i
      ],
      strategy: {
        type: 'fallback',
        delay: 500,
        confidence: 0.6,
        description: 'Component error detected. Using fallback rendering.',
        actions: [
          { type: 'reset_state' },
          { type: 'fallback_ui', params: { mode: 'degraded' } }
        ]
      }

  }

  public async getRecoveryStrategy(
    error: Error,
    errorInfo: ErrorInfo,
    attemptCount: number
  ): Promise<RecoveryStrategy> {
    const errorKey = this.generateErrorKey(error, errorInfo);
    
    // Record this recovery attempt
    this.recordRecoveryAttempt(errorKey, error, attemptCount);

    // Check for custom fallback strategies first
    const customStrategy = this.findCustomStrategy(error);
    if (customStrategy) {
      return customStrategy;
    }

    // Use pattern-based recovery
    const patternStrategy = this.findPatternStrategy(error);
    if (patternStrategy) {
      return this.adaptStrategyForAttempt(patternStrategy, attemptCount);
    }

    // Use smart recovery if enabled
    if (this.config.enableSmartRecovery) {
      const smartStrategy = await this.generateSmartStrategy(error, errorInfo, attemptCount);
      if (smartStrategy) {
        return smartStrategy;
      }
    }

    // Default fallback strategy
    return this.getDefaultStrategy(attemptCount);
  }

  private generateErrorKey(error: Error, errorInfo: ErrorInfo): string {
    const message = error.message.toLowerCase();
    const stack = error.stack?.split('\n')[0] || '';
    const component = errorInfo.componentStack.split('\n')[1] || '';
    
    return `${message}-${stack}-${component}`.replace(/[^a-z0-9-]/g, '');
  }

  private recordRecoveryAttempt(errorKey: string, error: Error, attemptCount: number) {
    if (!this.recoveryHistory.has(errorKey)) {
      this.recoveryHistory.set(errorKey, []);
    }

    const attempts = this.recoveryHistory.get(errorKey)!;
    attempts.push({
      timestamp: Date.now(),
      attemptCount,
      errorMessage: error.message,
      success: false // Will be updated when recovery succeeds

    // Keep only recent attempts (last 10)
    if (attempts.length > 10) {
      attempts.splice(0, attempts.length - 10);
    }
  }

  private findCustomStrategy(error: Error): RecoveryStrategy | null {
    if (!this.config.fallbackStrategies) return null;

    for (const fallback of this.config.fallbackStrategies) {
      if (fallback.errorPattern.test(error.message)) {
        return fallback.strategy;
      }
    }

    return null;
  }

  private findPatternStrategy(error: Error): RecoveryStrategy | null {
    const errorMessage = error.message.toLowerCase();
    const errorName = error.name.toLowerCase();
    const errorString = `${errorMessage} ${errorName}`;

    for (const [patternName, pattern] of this.errorPatterns.entries()) {
      for (const regex of pattern.patterns) {
        if (regex.test(errorString)) {
          return pattern.strategy;
        }
      }
    }

    return null;
  }

  private adaptStrategyForAttempt(strategy: RecoveryStrategy, attemptCount: number): RecoveryStrategy {
    const adaptedStrategy = { ...strategy };

    // Apply exponential backoff if configured
    if (this.config.exponentialBackoff) {
      adaptedStrategy.delay = strategy.delay * Math.pow(2, attemptCount - 1);
    }

    // Reduce confidence with each attempt
    adaptedStrategy.confidence = Math.max(0.1, strategy.confidence - (attemptCount * 0.1));

    // Add more aggressive actions for repeated failures
    if (attemptCount >= 2) {
      adaptedStrategy.actions = [
        ...strategy.actions,
        { type: 'clear_cache' },
        { type: 'reset_state' }
      ];
    }

    if (attemptCount >= 3) {
      adaptedStrategy.type = 'degraded';
      adaptedStrategy.actions.push(
        { type: 'fallback_ui', params: { mode: 'minimal' } }
      );
    }

    return adaptedStrategy;
  }

  private async generateSmartStrategy(
    error: Error,
    errorInfo: ErrorInfo,
    attemptCount: number
  ): Promise<RecoveryStrategy | null> {
    // Analyze error history for this type of error
    const errorKey = this.generateErrorKey(error, errorInfo);
    const history = this.recoveryHistory.get(errorKey) || [];

    if (history.length === 0) {
      return null; // No history to learn from
    }

    // Calculate success rate of different strategies
    const successfulStrategies = history.filter(attempt => attempt.success);
    
    if (successfulStrategies.length > 0) {
      // Use the most successful strategy pattern
      return {
        type: 'retry',
        delay: this.calculateOptimalDelay(history),
        confidence: successfulStrategies.length / history.length,
        description: 'Using learned recovery pattern based on historical success.',
        actions: [
          { type: 'clear_cache' },
          { type: 'reset_state' }
        ]
      };
    }

    // If no successful recoveries, try a different approach
    return {
      type: 'fallback',
      delay: 1000,
      confidence: 0.3,
      description: 'Previous recovery attempts failed. Trying alternative approach.',
      actions: [
        { type: 'fallback_ui', params: { mode: 'degraded' } },
        { type: 'notify_user', params: { message: 'Switching to safe mode...' } }
      ]
    };
  }

  private calculateOptimalDelay(history: RecoveryAttempt[]): number {
    // Calculate average delay that led to successful recoveries
    const successfulAttempts = history.filter(attempt => attempt.success);
    
    if (successfulAttempts.length === 0) {
      return this.config.retryDelay;
    }

    // For now, return the configured delay
    // In a real implementation, you might track delay times and their success rates
    return this.config.retryDelay;
  }

  private getDefaultStrategy(attemptCount: number): RecoveryStrategy {
    if (attemptCount >= this.config.maxAttempts) {
      return {
        type: 'fallback',
        delay: 0,
        confidence: 0.1,
        description: 'Maximum recovery attempts reached. Using minimal fallback.',
        actions: [
          { type: 'fallback_ui', params: { mode: 'minimal' } },
          { type: 'notify_user', params: { message: 'Unable to recover. Please refresh the page.' } }
        ]
      };
    }

    return {
      type: 'retry',
      delay: this.config.retryDelay * attemptCount,
      confidence: Math.max(0.2, 0.8 - (attemptCount * 0.2)),
      description: 'Using default retry strategy.',
      actions: [
        { type: 'clear_cache' },
        { type: 'reset_state' }
      ]
    };
  }

  public markRecoverySuccess(error: Error, errorInfo: ErrorInfo) {
    const errorKey = this.generateErrorKey(error, errorInfo);
    const attempts = this.recoveryHistory.get(errorKey);
    
    if (attempts && attempts.length > 0) {
      // Mark the most recent attempt as successful
      attempts[attempts.length - 1].success = true;
    }
  }

  public getRecoveryStats(): RecoveryStats {
    let totalAttempts = 0;
    let successfulAttempts = 0;
    const errorTypes = new Map<string, number>();

    for (const [errorKey, attempts] of this.recoveryHistory.entries()) {
      totalAttempts += attempts.length;
      successfulAttempts += attempts.filter(a => a.success).length;
      
      const errorType = errorKey.split('-')[0];
      errorTypes.set(errorType, (errorTypes.get(errorType) || 0) + attempts.length);
    }

    return {
      totalAttempts,
      successfulAttempts,
      successRate: totalAttempts > 0 ? successfulAttempts / totalAttempts : 0,
      errorTypes: Object.fromEntries(errorTypes),
      section: this.config.section
    };
  }

  public clearHistory() {
    this.recoveryHistory.clear();
  }
}

interface RecoveryAttempt {
  timestamp: number;
  attemptCount: number;
  errorMessage: string;
  success: boolean;
}

interface ErrorPattern {
  patterns: RegExp[];
  strategy: RecoveryStrategy;
}

interface RecoveryStats {
  totalAttempts: number;
  successfulAttempts: number;
  successRate: number;
  errorTypes: Record<string, number>;
  section: string;
}

export default ErrorRecoveryManager;