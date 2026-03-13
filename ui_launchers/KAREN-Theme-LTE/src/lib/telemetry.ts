/**
 * Telemetry Service
 * Provides telemetry and analytics capabilities
 */

export interface TelemetryEvent {
  id: string;
  type: 'user_action' | 'system_event' | 'error' | 'performance';
  category: string;
  action: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  userId?: string;
  sessionId?: string;
}

export interface TelemetryConfig {
  enabled: boolean;
  endpoint?: string;
  batchSize: number;
  flushInterval: number;
}

class TelemetryService {
  private config: TelemetryConfig;
  private events: TelemetryEvent[] = [];
  private isInitialized = false;

  constructor(config: Partial<TelemetryConfig> = {}) {
    this.config = {
      enabled: true,
      batchSize: 50,
      flushInterval: 30000, // 30 seconds
      ...config
    };

    if (this.config.enabled) {
      this.initialize();
    }
  }

  private initialize(): void {
    if (this.isInitialized) return;

    this.isInitialized = true;
    
    // Set up flush interval
    if (this.config.flushInterval > 0) {
      setInterval(() => {
        this.flush();
      }, this.config.flushInterval);
    }

    // Flush on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.flush();
      });
    }
  }

  trackEvent(event: Omit<TelemetryEvent, 'id' | 'timestamp'>): void {
    if (!this.config.enabled || !this.isInitialized) return;

    const telemetryEvent: TelemetryEvent = {
      id: this.generateId(),
      timestamp: new Date(),
      ...event
    };

    this.events.push(telemetryEvent);

    // Auto-flush if batch size reached
    if (this.events.length >= this.config.batchSize) {
      this.flush();
    }
  }

  trackUserAction(action: string, category: string = 'general', metadata?: Record<string, unknown>): void {
    this.trackEvent({
      type: 'user_action',
      category,
      action,
      metadata
    });
  }

  trackSystemEvent(event: string, category: string = 'system', metadata?: Record<string, unknown>): void {
    this.trackEvent({
      type: 'system_event',
      category,
      action: event,
      metadata
    });
  }

  trackError(error: Error | string, context?: Record<string, unknown>): void {
    const errorMessage = error instanceof Error ? error.message : error;
    const errorStack = error instanceof Error ? error.stack : undefined;

    this.trackEvent({
      type: 'error',
      category: 'error_handling',
      action: errorMessage,
      metadata: {
        ...context,
        stack: errorStack
      }
    });
  }

  trackPerformance(metric: string, value: number, unit?: string): void {
    this.trackEvent({
      type: 'performance',
      category: 'performance',
      action: metric,
      metadata: {
        value,
        unit
      }
    });
  }

  track(event: string | TelemetryEvent, properties?: Record<string, unknown>, correlationId?: string, streamId?: string): void {
    if (typeof event === 'string') {
      this.trackEvent({
        type: 'user_action',
        category: 'general',
        action: event,
        metadata: {
          ...properties,
          correlationId,
          streamId
        }
      });
    } else {
      this.trackEvent({
        ...event,
        metadata: {
          ...event.metadata,
          correlationId,
          streamId
        }
      });
    }
  }

  setUserId(userId: string): void {
    // Store user ID for subsequent events
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('telemetry_user_id', userId);
    }
  }

  setSessionId(sessionId: string): void {
    // Store session ID for subsequent events
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('telemetry_session_id', sessionId);
    }
  }

  flush(): void {
    if (this.events.length === 0 || !this.config.enabled) return;

    const eventsToSend = [...this.events];
    this.events = [];

    if (this.config.endpoint) {
      this.sendToEndpoint(eventsToSend);
    } else {
      console.log('Telemetry events:', eventsToSend);
    }
  }

  private sendToEndpoint(events: TelemetryEvent[]): void {
    if (!this.config.endpoint) return;

    fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(events)
    }).catch(error => {
      console.error('Failed to send telemetry events:', error);
      // Re-add events to queue on failure
      this.events.unshift(...events);
    });
  }

  generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  getUserId(): string | null {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('telemetry_user_id');
    }
    return null;
  }

  getSessionId(): string | null {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('telemetry_session_id');
    }
    return null;
  }

  getEvents(): TelemetryEvent[] {
    return [...this.events];
  }

  clear(): void {
    this.events = [];
  }

  enable(): void {
    this.config.enabled = true;
    if (!this.isInitialized) {
      this.initialize();
    }
  }

  disable(): void {
    this.config.enabled = false;
  }
}

// Singleton instance
let telemetryService: TelemetryService | null = null;

export const getTelemetryService = (): TelemetryService => {
  if (!telemetryService) {
    telemetryService = new TelemetryService();
  }
  return telemetryService;
};

export default TelemetryService;