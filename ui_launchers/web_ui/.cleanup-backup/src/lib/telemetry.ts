'use client';

import { safeWarn, safeInfo } from './safe-console';

interface TelemetryEvent {
  event: string;
  payload: Record<string, any>;
  correlationId?: string;
  timestamp: string;
  sessionId: string;
  userId?: string;
  userAgent: string;
  url: string;
}

interface TelemetryConfig {
  enabled: boolean;
  endpoint?: string;
  batchSize: number;
  flushInterval: number;
  maxRetries: number;
  debug: boolean;
  sampling: number; // 0-1, percentage of events to capture
}

class TelemetryService {
  private config: TelemetryConfig;
  private eventQueue: TelemetryEvent[] = [];
  private correlationId: string = '';
  private sessionId: string = '';
  private flushTimer: NodeJS.Timeout | null = null;
  private retryCount: number = 0;

  constructor(config: Partial<TelemetryConfig> = {}) {
    this.config = {
      enabled: true,
      batchSize: 10,
      flushInterval: 5000, // 5 seconds
      maxRetries: 3,
      debug: process.env.NODE_ENV === 'development',
      sampling: 1.0, // Capture all events by default
      ...config
    };

    this.sessionId = this.generateId();
    this.correlationId = this.generateId();

    // Start flush timer
    this.startFlushTimer();

    // Flush on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.flush();
      });

      // Flush on visibility change (tab switch, minimize)
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          this.flush();
        }
      });
    }
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  private shouldSample(): boolean {
    return Math.random() <= this.config.sampling;
  }

  public track(event: string, payload: Record<string, any> = {}, correlationId?: string): void {
    if (!this.config.enabled || !this.shouldSample()) {
      return;
    }

    const telemetryEvent: TelemetryEvent = {
      event,
      payload: {
        ...payload,
        // Add performance timing if available
        ...(typeof performance !== 'undefined' && {
          performanceNow: performance.now(),
          timeOrigin: performance.timeOrigin
        })
      },
      correlationId: correlationId || this.correlationId,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      userId: this.getUserId(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };

    this.eventQueue.push(telemetryEvent);

    if (this.config.debug) {
      safeInfo('📊 Telemetry Event:', telemetryEvent);
    }

    // Flush if queue is full
    if (this.eventQueue.length >= this.config.batchSize) {
      this.flush();
    }
  }

  public startSpan(name: string): Span {
    const spanId = this.generateId();
    const startTime = performance.now();

    this.track('span_start', {
      spanId,
      spanName: name,
      startTime
    });

    return {
      id: spanId,
      name,
      startTime,
      end: () => {
        const endTime = performance.now();
        const duration = endTime - startTime;

        this.track('span_end', {
          spanId,
          spanName: name,
          startTime,
          endTime,
          duration
        });

        return duration;
      },
      addTag: (key: string, value: any) => {
        this.track('span_tag', {
          spanId,
          spanName: name,
          tagKey: key,
          tagValue: value
        });
      }
    };
  }

  public setCorrelationId(id: string): void {
    this.correlationId = id;
    this.track('correlation_id_set', { correlationId: id });
  }

  public setUserId(userId: string): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('telemetry_user_id', userId);
    }
    this.track('user_id_set', { userId });
  }

  private getUserId(): string | undefined {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('telemetry_user_id') || undefined;
    }
    return undefined;
  }

  public async flush(): Promise<void> {
    if (this.eventQueue.length === 0) {
      return;
    }

    const events = [...this.eventQueue];
    this.eventQueue = [];

    if (this.config.debug) {
      safeInfo(`📊 Flushing ${events.length} telemetry events`);
    }

    // Store locally as fallback
    this.storeLocally(events);

    // Send to endpoint if configured
    if (this.config.endpoint) {
      try {
        await this.sendToEndpoint(events);
        this.retryCount = 0;
      } catch (error) {
        safeWarn('Failed to send telemetry events:', error);
        
        // Retry logic
        if (this.retryCount < this.config.maxRetries) {
          this.retryCount++;
          // Re-queue events for retry
          this.eventQueue.unshift(...events);
          
          // Exponential backoff
          setTimeout(() => {
            this.flush();
          }, Math.pow(2, this.retryCount) * 1000);
        }
      }
    }
  }

  private storeLocally(events: TelemetryEvent[]): void {
    if (typeof localStorage === 'undefined') return;

    try {
      const existing = JSON.parse(localStorage.getItem('telemetry_events') || '[]');
      const combined = [...existing, ...events];
      
      // Keep only last 1000 events to prevent storage bloat
      const trimmed = combined.slice(-1000);
      
      localStorage.setItem('telemetry_events', JSON.stringify(trimmed));
    } catch (error) {
      safeWarn('Failed to store telemetry events locally:', error);
    }
  }

  private async sendToEndpoint(events: TelemetryEvent[]): Promise<void> {
    if (!this.config.endpoint) return;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        events,
        metadata: {
          version: '1.0',
          source: 'web-ui',
          timestamp: new Date().toISOString()
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  public getStoredEvents(): TelemetryEvent[] {
    if (typeof localStorage === 'undefined') return [];

    try {
      return JSON.parse(localStorage.getItem('telemetry_events') || '[]');
    } catch {
      return [];
    }
  }

  public clearStoredEvents(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('telemetry_events');
    }
  }

  public getStats(): {
    queueSize: number;
    sessionId: string;
    correlationId: string;
    storedEvents: number;
    config: TelemetryConfig;
  } {
    return {
      queueSize: this.eventQueue.length,
      sessionId: this.sessionId,
      correlationId: this.correlationId,
      storedEvents: this.getStoredEvents().length,
      config: this.config
    };
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    this.flush();
  }
}

export interface Span {
  id: string;
  name: string;
  startTime: number;
  end: () => number;
  addTag: (key: string, value: any) => void;
}

// Singleton instance
let telemetryInstance: TelemetryService | null = null;

export const getTelemetryService = (config?: Partial<TelemetryConfig>): TelemetryService => {
  if (!telemetryInstance) {
    telemetryInstance = new TelemetryService(config);
  }
  return telemetryInstance;
};

// Convenience functions
export const track = (event: string, payload?: Record<string, any>, correlationId?: string): void => {
  getTelemetryService().track(event, payload, correlationId);
};

export const startSpan = (name: string): Span => {
  return getTelemetryService().startSpan(name);
};

export const setCorrelationId = (id: string): void => {
  getTelemetryService().setCorrelationId(id);
};

export const setUserId = (userId: string): void => {
  getTelemetryService().setUserId(userId);
};

export const flushTelemetry = (): Promise<void> => {
  return getTelemetryService().flush();
};

export default TelemetryService;