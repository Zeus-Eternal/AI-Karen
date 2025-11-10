/**
 * Audit Logger Service (Production-Grade)
 *
 * Features
 * - SSR-safe (guards for window, navigator)
 * - Config bootstrap with sane defaults
 * - Sensitive field masking + payload size enforcement
 * - Priority batch queue with max size + drop counter
 * - Periodic flush + immediate flush for critical/security events
 * - Exponential backoff with jitter on network failures
 * - beforeunload flush using navigator.sendBeacon (chunked) + fetch keepalive fallback
 * - Keepalive POSTs for background tabs
 * - Utilities: request/session/context enrichment
 * - Convenience log helpers (auth, authz, data, system, ui, security)
 *
 * Assumes existing types: AuditEvent, AuditEventType, AuditSeverity, AuditOutcome, AuditConfig, AuditFilter, AuditSearchResult
 */

import {
  AuditEvent,
  AuditEventType,
  AuditSeverity,
  AuditOutcome,
  AuditConfig,
  AuditFilter,
  AuditSearchResult,
} from '@/types/audit';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { useAppStore } from '@/store/app-store';

export type Timer = ReturnType<typeof setInterval>;

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

const KB = 1024;
const MB = 1024 * KB;

class AuditLoggerService {
  private config: AuditConfig | null = null;
  private eventQueue: AuditEvent[] = [];
  private flushTimer: Timer | null = null;
  private isInitialized = false;
  private flushing = false;
  private backoffAttempts = 0;
  private droppedEvents = 0;

  // Payload/queue controls
  private readonly MAX_QUEUE = 5000;                 // hard cap
  private readonly SOFT_QUEUE_ALERT = 2000;          // warn store/console
  private readonly MAX_EVENT_BYTES = 12 * KB;        // per-event cap after masking/trim
  private readonly MAX_PAYLOAD_BYTES = 450 * KB;     // fetch/keepalive payload target
  private readonly MAX_BEACON_BYTES = 55 * KB;       // conservative per-beacon payload target

  // Network and endpoints
  private readonly EVENTS_ENDPOINT = '/api/audit/events';
  private readonly CONFIG_ENDPOINT = '/api/audit/config';
  private readonly SEARCH_ENDPOINT = '/api/audit/search';
  private readonly EXPORT_ENDPOINT = '/api/audit/export';
  private readonly STATS_ENDPOINT = '/api/audit/statistics';

  // Periodic flush controls
  private readonly DEFAULT_BATCH_SIZE = 25;
  private readonly DEFAULT_FLUSH_MS = 5000;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      const response = await enhancedApiClient.get<AuditConfig>(this.CONFIG_ENDPOINT);
      this.config = response.data ?? this.getDefaultConfig();
    } catch (error) {
      console.error('[audit] Failed to load remote config, using defaults:', error);
      this.config = this.getDefaultConfig();
    }

    // Always mark initialized so logging works even if remote config fails
    this.isInitialized = true;

    // Start timers only if enabled
    if (this.config?.enabled && isBrowser) {
      this.startPeriodicFlush();
      this.setupBeforeUnloadHandler();
    }
  }

  // ---------------- Public logging API ----------------

  async logEvent(eventType: AuditEventType, action: string, options: Partial<AuditEvent> = {}): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }
    if (!this.config?.enabled) return;

    const event = this.createAuditEvent(eventType, action, options);
    const sanitized = this.sanitizeEvent(event);

    if (!sanitized) return; // dropped if oversized beyond salvage

    // Queue with backpressure limits
    if (this.eventQueue.length >= this.MAX_QUEUE) {
      this.droppedEvents++;
      // keep last N by shifting oldest
      this.eventQueue.shift();
    }
    this.eventQueue.push(sanitized);

    // warn UI if queue is growing too large
    if (this.eventQueue.length === this.SOFT_QUEUE_ALERT) {
      try {
        useAppStore.getState().addNotification?.({
          type: 'warning',
          title: 'Audit Backlog Growing',
          message: `Audit queue size ${this.eventQueue.length}. Check network or server health.`,
        });
      } catch {}
    }

    // Immediate flush for critical/security
    const sev = sanitized.severity || 'low';
    if (sev === 'critical' || String(eventType).startsWith('security:') || this.shouldImmediateFlush()) {
      await this.flush();
    } else if (this.eventQueue.length >= (this.config?.performance?.batchSize || this.DEFAULT_BATCH_SIZE)) {
      await this.flush();
    }
  }

  async logAuth(
    eventType: Extract<
      AuditEventType,
      'auth:login' | 'auth:logout' | 'auth:failed_login' | 'auth:password_change' | 'auth:session_expired'
    >,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    await this.logEvent(eventType, `User ${eventType.split(':')[1]}`, {
      outcome,
      severity: outcome === 'failure' ? ('high' as AuditSeverity) : ('low' as AuditSeverity),
      details,
      riskScore: outcome === 'failure' ? 7 : 1,
    });
  }

  async logAuthz(
    eventType: Extract<
      AuditEventType,
      | 'authz:permission_granted'
      | 'authz:permission_denied'
      | 'authz:role_assigned'
      | 'authz:role_removed'
      | 'authz:evil_mode_enabled'
      | 'authz:evil_mode_disabled'
    >,
    resource: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType.includes('evil_mode')
      ? 'critical'
      : eventType.includes('denied')
      ? 'medium'
      : 'low';
    await this.logEvent(eventType, `Authorization ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      resourceName: resource,
      details,
      riskScore: severity === 'critical' ? 9 : severity === 'medium' ? 5 : 2,
    });
  }

  async logDataAccess(
    eventType: Extract<AuditEventType, 'data:read' | 'data:create' | 'data:update' | 'data:delete' | 'data:export' | 'data:import'>,
    resourceType: string,
    resourceId: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity =
      eventType === 'data:delete' ? 'high' : eventType === 'data:export' ? 'medium' : 'low';
    await this.logEvent(eventType, `Data ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      resourceType,
      resourceId,
      details,
      riskScore: severity === 'high' ? 6 : severity === 'medium' ? 4 : 1,
    });
  }

  async logSystem(
    eventType: Extract<
      AuditEventType,
      'system:config_change' | 'system:service_start' | 'system:service_stop' | 'system:error' | 'system:warning'
    >,
    component: string,
    outcome: AuditOutcome,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType === 'system:error' ? 'high' : eventType === 'system:warning' ? 'medium' : 'low';
    await this.logEvent(eventType, `System ${eventType.split(':')[1]}`, {
      outcome,
      severity,
      component,
      details,
      riskScore: severity === 'high' ? 7 : severity === 'medium' ? 4 : 1,
    });
  }

  async logUI(
    eventType: Extract<AuditEventType, 'ui:page_view' | 'ui:action_performed' | 'ui:feature_used' | 'ui:error_encountered'>,
    action: string,
    details: Record<string, any> = {}
  ): Promise<void> {
    const severity: AuditSeverity = eventType === 'ui:error_encountered' ? 'medium' : 'low';
    await this.logEvent(eventType, action, {
      outcome: 'success',
      severity,
      details,
      riskScore: 1,
    });
  }

  async logSecurity(
    eventType: Extract<
      AuditEventType,
      'security:threat_detected' | 'security:vulnerability_found' | 'security:policy_violation' | 'security:suspicious_activity'
    >,
    description: string,
    severity: AuditSeverity = 'high',
    details: Record<string, any> = {}
  ): Promise<void> {
    await this.logEvent(eventType, description, {
      outcome: 'unknown',
      severity,
      details,
      riskScore: severity === 'critical' ? 10 : severity === 'high' ? 8 : 6,
      threatLevel: severity,
    });
  }

  // ---------------- Queries / Export / Stats ----------------

  async searchEvents(filter: AuditFilter): Promise<AuditSearchResult> {
    const response = await enhancedApiClient.post<AuditSearchResult>(this.SEARCH_ENDPOINT, filter);
    return response.data;
  }

  async exportEvents(filter: AuditFilter, format: 'json' | 'csv' | 'xlsx' = 'json'): Promise<Blob> {
    const response = await enhancedApiClient.post<Blob>(this.EXPORT_ENDPOINT, { ...filter, format });
    const payload = response.data;
    if (payload instanceof Blob) {
      return payload;
    }
    return new Blob([payload as BlobPart]);
  }

  async getStatistics(timeframe: { start: Date; end: Date }): Promise<{
    totalEvents: number;
    eventsByType: Record<AuditEventType, number>;
    eventsBySeverity: Record<AuditSeverity, number>;
    eventsByOutcome: Record<AuditOutcome, number>;
    topUsers: Array<{ userId: string; username: string; eventCount: number }>;
    riskTrends: Array<{ date: string; averageRiskScore: number }>;
  }> {
    const response = await enhancedApiClient.post(this.STATS_ENDPOINT, timeframe);
    return response.data as {
      totalEvents: number;
      eventsByType: Record<AuditEventType, number>;
      eventsBySeverity: Record<AuditSeverity, number>;
      eventsByOutcome: Record<AuditOutcome, number>;
      topUsers: Array<{ userId: string; username: string; eventCount: number }>;
      riskTrends: Array<{ date: string; averageRiskScore: number }>;
    };
  }

  // ---------------- Flush mechanics ----------------

  private shouldImmediateFlush(): boolean {
    // When asyncProcessing off, flush synchronously
    if (!this.config?.performance?.asyncProcessing) return true;
    // If queue too big, push
    if (this.eventQueue.length > this.DEFAULT_BATCH_SIZE * 3) return true;
    return false;
  }

  private async flush(): Promise<void> {
    if (this.flushing || this.eventQueue.length === 0 || !this.config?.enabled) return;

    this.flushing = true;

    try {
      // Split queue into payloads under size limit and by batch size
      const batchSize = this.config?.performance?.batchSize || this.DEFAULT_BATCH_SIZE;
      let start = 0;

      while (start < this.eventQueue.length) {
        const { payload, count } = this.buildPayload(this.eventQueue.slice(start, start + batchSize), this.MAX_PAYLOAD_BYTES);
        if (count === 0) break;

        // remove from queue optimistically
        const sending = this.eventQueue.splice(start, count);

        try {
          await enhancedApiClient.post(this.EVENTS_ENDPOINT, payload, { keepalive: true });
          // reset backoff on success
          this.backoffAttempts = 0;
        } catch (err) {
          // re-queue on failure (cap)
          this.backoffAttempts++;
          const jitter = Math.floor(Math.random() * 400);
          const delay = Math.min(30_000, Math.pow(2, this.backoffAttempts) * 500) + jitter;
          console.error('[audit] Flush failed; re-queueing & backing off', { delay, err });

          // Put back at the front, capped to MAX_QUEUE
          this.eventQueue = [...sending, ...this.eventQueue].slice(-this.MAX_QUEUE);

          await this.sleep(delay);
          // break to avoid tight loop
          break;
        }
      }
    } finally {
      this.flushing = false;
    }
  }

  private buildPayload(events: AuditEvent[], maxBytes: number): { payload: { events: AuditEvent[] }; count: number } {
    const chosen: AuditEvent[] = [];
    let size = 0;
    for (const ev of events) {
      const json = JSON.stringify(ev);
      const bytes = this.byteLen(json);
      if (bytes > this.MAX_EVENT_BYTES) {
        // oversize even after sanitize — drop
        this.droppedEvents++;
        continue;
      }
      if (size + bytes > maxBytes) break;
      chosen.push(ev);
      size += bytes;
    }
    return { payload: { events: chosen }, count: chosen.length };
    }

  private startPeriodicFlush(): void {
    const interval = this.config?.performance?.flushInterval || this.DEFAULT_FLUSH_MS;
    this.stopPeriodicFlush();
    this.flushTimer = setInterval(() => {
      // background flush using keepalive
      this.flush().catch((e) => console.error('[audit] Periodic flush failed:', e));
    }, interval);
  }

  private stopPeriodicFlush(): void {
    if (this.flushTimer) clearInterval(this.flushTimer);
    this.flushTimer = null;
  }

  private setupBeforeUnloadHandler(): void {
    if (!isBrowser) return;

    window.addEventListener('beforeunload', () => {
      if (!this.config?.enabled || this.eventQueue.length === 0) return;

      const all = [...this.eventQueue];
      this.eventQueue = [];

      // Chunk into beacon sized payloads
      const chunks: AuditEvent[][] = [];
      let current: AuditEvent[] = [];
      let currentBytes = 0;

      for (const ev of all) {
        const s = JSON.stringify(ev);
        const b = this.byteLen(s);
        if (b > this.MAX_EVENT_BYTES) {
          this.droppedEvents++;
          continue;
        }
        if (currentBytes + b > this.MAX_BEACON_BYTES) {
          if (current.length) chunks.push(current);
          current = [ev];
          currentBytes = b;
        } else {
          current.push(ev);
          currentBytes += b;
        }
      }
      if (current.length) chunks.push(current);

      for (const chunk of chunks) {
        const body = JSON.stringify({ events: chunk });
        // Prefer sendBeacon for unload; fallback to fetch keepalive
        if (navigator.sendBeacon) {
          const ok = navigator.sendBeacon(this.EVENTS_ENDPOINT, body);
          if (!ok) {
            // keepalive fetch fallback (fire-and-forget)
            try {
              fetch(this.EVENTS_ENDPOINT, {
                method: 'POST',
                body,
                headers: { 'Content-Type': 'application/json' },
                keepalive: true,
                credentials: 'include',
              }).catch(() => {});
            } catch {}
          }
        } else {
          try {
            fetch(this.EVENTS_ENDPOINT, {
              method: 'POST',
              body,
              headers: { 'Content-Type': 'application/json' },
              keepalive: true,
              credentials: 'include',
            }).catch(() => {});
          } catch {}
        }
      }
    });
  }

  // ---------------- Event creation / sanitation ----------------

  private createAuditEvent(eventType: AuditEventType, action: string, options: Partial<AuditEvent>): AuditEvent {
    const store = safeGetStore();
    const user = store?.user;

    const base: AuditEvent = {
      id: this.generateEventId(),
      timestamp: new Date(),
      eventType,
      action,
      description: options.description || action,
      severity: options.severity || 'low',
      outcome: options.outcome || 'success',

      // User context
      userId: user?.id,
      username: user?.username,
      sessionId: this.getSessionId(),

      // Request context
      ipAddress: this.getClientIP(),
      userAgent: isBrowser ? navigator.userAgent : 'server',
      requestId: this.getRequestId(),
      url: isBrowser ? window.location.href : undefined,
      referrer: isBrowser ? document.referrer || undefined : undefined,
      locale: isBrowser ? navigator.language : undefined,
      timezone: Intl?.DateTimeFormat?.().resolvedOptions?.().timeZone,

      // Technical context
      component: 'web-ui',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'development',

      // Defaults
      details: {},
      tags: [],
      customFields: {},

      ...options,
    };

    // Ensure details/tags are at least defined (avoid undefined)
    base.details = base.details || {};
    base.tags = base.tags || [];
    base.customFields = base.customFields || {};

    return base;
  }

  private sanitizeEvent(event: AuditEvent): AuditEvent | null {
    // mask sensitive fields deeply in details/customFields
    const sensitive = this.config?.captureSettings?.sensitiveFields || ['password', 'token', 'secret', 'key'];
    const masked = this.maskObject({ ...event }, new Set(sensitive));

    // enforce per-event byte size by trimming large fields
    let json = JSON.stringify(masked);
    let bytes = this.byteLen(json);

    if (bytes <= this.MAX_EVENT_BYTES) return masked;

    // try trimming details/customFields/description progressively
    const shrink = (obj: any, keys: string[]) => {
      for (const k of keys) {
        if (!obj[k]) continue;
        if (typeof obj[k] === 'string') {
          obj[k] = this.truncateString(obj[k], Math.max(0, obj[k].length - 256));
        } else if (typeof obj[k] === 'object') {
          obj[k] = this.trimObject(obj[k], 0.5); // drop half of keys heuristically
        }
      }
    };

    const candidate = { ...masked };
    shrink(candidate, ['details', 'customFields', 'description']);

    json = JSON.stringify(candidate);
    bytes = this.byteLen(json);

    if (bytes <= this.MAX_EVENT_BYTES) return candidate;

    // Final attempt: keep minimal shape
    const minimal: AuditEvent = {
      id: masked.id,
      timestamp: masked.timestamp,
      eventType: masked.eventType,
      action: masked.action,
      description: this.truncateString(masked.description || masked.action, 128),
      severity: masked.severity,
      outcome: masked.outcome,
      userId: masked.userId,
      username: masked.username,
      sessionId: masked.sessionId,
      requestId: masked.requestId,
      component: masked.component,
      version: masked.version,
      environment: masked.environment,
      details: {},
      tags: [],
      customFields: {},
      ipAddress: masked.ipAddress,
      userAgent: masked.userAgent,
      url: masked.url,
      referrer: masked.referrer,
      locale: masked.locale,
      timezone: masked.timezone,
      resourceId: masked.resourceId,
      resourceType: masked.resourceType,
      resourceName: (masked as any).resourceName,
      riskScore: masked.riskScore,
      threatLevel: (masked as any).threatLevel,
    };

    json = JSON.stringify(minimal);
    bytes = this.byteLen(json);

    if (bytes <= this.MAX_EVENT_BYTES) return minimal;

    // Give up: drop event
    this.droppedEvents++;
    return null;
  }

  private maskObject(obj: any, sensitive: Set<string>): any {
    if (!obj || typeof obj !== 'object') return obj;

    const mask = (val: any) => (typeof val === 'string' ? '***' : val && typeof val === 'object' ? '[REDACTED]' : '***');

    const recurse = (value: any): any => {
      if (!value || typeof value !== 'object') return value;
      if (Array.isArray(value)) return value.map(recurse);
      const out: any = {};
      for (const [k, v] of Object.entries(value)) {
        if (sensitive.has(k.toLowerCase())) {
          out[k] = mask(v);
        } else {
          out[k] = recurse(v);
        }
      }
      return out;
    };

    // mask details/customFields only, preserve top-level structure
    const out = { ...obj };
    if (out.details) out.details = recurse(out.details);
    if (out.customFields) out.customFields = recurse(out.customFields);
    return out;
  }

  private trimObject(o: any, keepRatio = 0.5): any {
    if (!o || typeof o !== 'object' || Array.isArray(o)) return o;
    const keys = Object.keys(o);
    const keep = Math.max(1, Math.floor(keys.length * keepRatio));
    const out: any = {};
    for (let i = 0; i < keep; i++) out[keys[i]] = o[keys[i]];
    return out;
  }

  private truncateString(s: string, dropChars: number): string {
    if (!s) return s;
    if (dropChars <= 0) return s;
    const target = Math.max(0, s.length - dropChars);
    return s.slice(0, target) + '…';
  }

  // ---------------- Utils ----------------

  private byteLen(str: string): number {
    // UTF-8 byte length
    if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(str).length;
    // fallback rough estimate
    return unescape(encodeURIComponent(str)).length;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((res) => setTimeout(res, ms));
  }

  private generateEventId(): string {
    return `audit_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  }

  private getSessionId(): string {
    if (!isBrowser) return 'server';
    try {
      return sessionStorage.getItem('sessionId') || 'unknown';
    } catch {
      return 'unknown';
    }
  }

  private getClientIP(): string {
    // Usually injected server-side; kept as placeholder
    return 'unknown';
  }

  private getRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
  }

  // ---------------- Admin / lifecycle ----------------

  updateConfig(next: Partial<AuditConfig>): void {
    this.config = { ...(this.config || this.getDefaultConfig()), ...next } as AuditConfig;
    if (!this.config.enabled) {
      this.stopPeriodicFlush();
      return;
    }
    if (isBrowser) {
      this.startPeriodicFlush();
    }
  }

  destroy(): void {
    this.stopPeriodicFlush();
    // Attempt final flush best-effort
    const pending = [...this.eventQueue];
    this.eventQueue = [];
    if (pending.length && isBrowser) {
      try {
        const { payload } = this.buildPayload(pending, this.MAX_PAYLOAD_BYTES);
        const body = JSON.stringify(payload);
        if (navigator.sendBeacon) {
          navigator.sendBeacon(this.EVENTS_ENDPOINT, body);
        } else {
          fetch(this.EVENTS_ENDPOINT, {
            method: 'POST',
            body,
            headers: { 'Content-Type': 'application/json' },
            keepalive: true,
            credentials: 'include',
          }).catch(() => {});
        }
      } catch {}
    }
  }

  // ---------------- Defaults ----------------

  private getDefaultConfig(): AuditConfig {
    return {
      enabled: true,
      captureSettings: {
        includeRequestBodies: false,
        includeResponseBodies: false,
        maskSensitiveData: true,
        sensitiveFields: ['password', 'token', 'secret', 'key', 'authorization', 'apiKey'],
        maxEventSize: this.MAX_EVENT_BYTES, // bytes
      },
      storage: {
        provider: 'database',
        retentionPeriod: 365,
        compressionEnabled: true,
        encryptionEnabled: true,
      },
      performance: {
        batchSize: this.DEFAULT_BATCH_SIZE,
        flushInterval: this.DEFAULT_FLUSH_MS,
        maxQueueSize: this.MAX_QUEUE,
        asyncProcessing: true,
      },
      alerting: {
        enabled: true,
        rules: [],
      },
      compliance: {
        enabled: true,
        frameworks: ['gdpr_compliance'],
        automaticReporting: false,
        reportSchedule: '0 0 * * 0',
      },
      anomalyDetection: {
        enabled: true,
        sensitivity: 'medium',
        algorithms: [],
        thresholds: {
          loginFrequency: 10,
          failedLoginAttempts: 5,
          unusualHours: 3,
          dataAccessVolume: 100,
          privilegeEscalation: 1,
        },
        notifications: {
          enabled: true,
          channels: ['email'],
          severity: 'high',
        },
      },
    } as AuditConfig;
  }
}

// ---- helpers ----
function safeGetStore(): any {
  try {
    return useAppStore.getState();
  } catch {
    return null;
  }
}

// Singleton instance
export const auditLogger = new AuditLoggerService();

// Auto-initialize in browser (not during tests)
if (isBrowser && process.env.NODE_ENV !== 'test') {
  auditLogger.initialize().catch((e) => console.error('[audit] init error:', e));
}
