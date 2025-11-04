/**
 * Correlation ID tracking for request tracing
 */

import { v4 as uuidv4 } from 'uuid';

class CorrelationTracker {
  private static instance: CorrelationTracker;
  private correlationMap = new Map<string, string>();
  private requestStack: string[] = [];

  static getInstance(): CorrelationTracker {
    if (!CorrelationTracker.instance) {
      CorrelationTracker.instance = new CorrelationTracker();
    }
    return CorrelationTracker.instance;
  }

  /**
   * Generate a new correlation ID
   */
  generateCorrelationId(): string {
    return `corr_${uuidv4()}`;
  }

  /**
   * Set correlation ID for current request context
   */
  setCorrelationId(correlationId: string): void {
    this.requestStack.push(correlationId);
    if (typeof window !== 'undefined') {
      // Store in session storage for browser context
      sessionStorage.setItem('currentCorrelationId', correlationId);
    }
  }

  /**
   * Get current correlation ID
   */
  getCurrentCorrelationId(): string {
    if (this.requestStack.length > 0) {
      return this.requestStack[this.requestStack.length - 1];
    }
    
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('currentCorrelationId');
      if (stored) return stored;
    }
    
    // Generate new one if none exists
    const newId = this.generateCorrelationId();
    this.setCorrelationId(newId);
    return newId;
  }

  /**
   * Clear correlation ID from current context
   */
  clearCorrelationId(): void {
    this.requestStack.pop();
    if (this.requestStack.length === 0 && typeof window !== 'undefined') {
      sessionStorage.removeItem('currentCorrelationId');
    }
  }

  /**
   * Associate a request ID with a correlation ID
   */
  associateRequest(requestId: string, correlationId?: string): void {
    const corrId = correlationId || this.getCurrentCorrelationId();
    this.correlationMap.set(requestId, corrId);
  }

  /**
   * Get correlation ID for a specific request
   */
  getCorrelationForRequest(requestId: string): string | undefined {
    return this.correlationMap.get(requestId);
  }

  /**
   * Clean up old associations
   */
  cleanup(): void {
    // Keep only recent associations (last 1000)
    if (this.correlationMap.size > 1000) {
      const entries = Array.from(this.correlationMap.entries());
      const toKeep = entries.slice(-500);
      this.correlationMap.clear();
      toKeep.forEach(([key, value]) => {
        this.correlationMap.set(key, value);
      });

    }
  }

  /**
   * Create a new correlation context for async operations
   */
  withCorrelation<T>(correlationId: string, fn: () => T): T {
    this.setCorrelationId(correlationId);
    try {
      return fn();
    } finally {
      this.clearCorrelationId();
    }
  }

  /**
   * Create correlation context for async operations
   */
  async withCorrelationAsync<T>(correlationId: string, fn: () => Promise<T>): Promise<T> {
    this.setCorrelationId(correlationId);
    try {
      return await fn();
    } finally {
      this.clearCorrelationId();
    }
  }
}

export const correlationTracker = CorrelationTracker.getInstance();

/**
 * Decorator for adding correlation tracking to methods
 */
export function withCorrelation(target: any, propertyName: string, descriptor: PropertyDescriptor) {
  const method = descriptor.value;
  
  descriptor.value = function (...args: any[]) {
    const correlationId = correlationTracker.generateCorrelationId();
    return correlationTracker.withCorrelation(correlationId, () => {
      return method.apply(this, args);
    });
  };
}

/**
 * Decorator for adding correlation tracking to async methods
 */
export function withCorrelationAsync(target: any, propertyName: string, descriptor: PropertyDescriptor) {
  const method = descriptor.value;
  
  descriptor.value = async function (...args: any[]) {
    const correlationId = correlationTracker.generateCorrelationId();
    return await correlationTracker.withCorrelationAsync(correlationId, () => {
      return method.apply(this, args);
    });
  };
}
