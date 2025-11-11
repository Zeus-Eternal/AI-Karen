/**
 * Enhanced WebSocket Service (Production-Grade)
 * - SSR-safe (guards for window/document)
 * - Exponential backoff + jitter, max delay cap
 * - Heartbeat (ping/pong) with latency + missed-pong handling
 * - Priority queue with TTL and backpressure (bufferedAmount) awareness
 * - Duplicate message suppression window
 * - Subscriptions with filter + once; clean teardown
 * - Connection metrics + quality mapping
 * - Visibility + online/offline aware
 * - Optional auth bootstrap, store hooks, and query invalidation
 *
 * Requirements: 12.2, 12.3
 */

import * as React from 'react';
import { useAppStore } from '@/store/app-store';
import { invalidateQueries } from '@/lib/query-client';

export type WebSocketPayload = Record<string, unknown>;

type NotificationType = 'info' | 'error' | 'success' | 'warning';

const isNotificationType = (value: unknown): value is NotificationType =>
  value === 'info' || value === 'error' || value === 'success' || value === 'warning';

const normalizeNotificationPayload = (payload: WebSocketPayload | undefined) => {
  const data = payload ?? {};
  return {
    type: isNotificationType(data.type) ? data.type : 'info',
    title: typeof data.title === 'string' ? data.title : 'Notification',
    message: typeof data.message === 'string' ? data.message : '',
  };
};

export interface WebSocketMessage {
  type: WebSocketEventType | string;
  channel: string;
  data: WebSocketPayload;
  timestamp: string; // ISO
  id: string;
  priority?: 'low' | 'normal' | 'high' | 'critical';
  ttl?: number;  // ms
  retry?: boolean;
}

export type WebSocketEventType =
  | 'chat.message'
  | 'chat.typing'
  | 'chat.status'
  | 'system.health'
  | 'system.metrics'
  | 'system.alert'
  | 'memory.update'
  | 'memory.search'
  | 'plugin.status'
  | 'plugin.install'
  | 'plugin.error'
  | 'provider.status'
  | 'provider.model'
  | 'user.activity'
  | 'user.presence'
  | 'notification'
  | 'workflow.status'
  | 'agent.status'
  | 'performance.metrics'
  | 'auth'
  | 'connection.info'
  | 'ping'
  | 'pong';

export type ConnectionState =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'reconnecting'
  | 'suspended';

export interface ConnectionMetrics {
  latency: number;
  messagesSent: number;
  messagesReceived: number;
  reconnectCount: number;
  lastConnected: Date | null;
  uptime: number;
  errorCount: number;
  backpressure: number; // ws.bufferedAmount
}

export interface QueuedMessage {
  message: WebSocketMessage;
  enqueuedAt: number;
  attempts: number;
  maxAttempts: number;
}

export interface Subscription {
  id: string;
  eventType: string; // allow wildcards if needed
  callback: (data: WebSocketPayload, raw: WebSocketMessage) => void;
  filter?: (data: WebSocketPayload, raw: WebSocketMessage) => boolean;
  once?: boolean;
}

export type Timer = ReturnType<typeof setTimeout>;
export type Interval = ReturnType<typeof setInterval>;

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

export class EnhancedWebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private protocols?: string[];

  // reconnection/backoff
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 10;
  private readonly baseReconnectDelay = 1000; // 1s
  private readonly maxReconnectDelay = 30000; // 30s
  private reconnectTimeout: Timer | null = null;
  private connectionTimeout: Timer | null = null;
  private readonly connectTimeoutMs = 10000;

  // heartbeat
  private heartbeatInterval: Interval | null = null;
  private readonly heartbeatMs = 30000;
  private lastPingTs = 0;
  private missedPongs = 0;
  private readonly maxMissedPongs = 2;

  // state
  private connectionState: ConnectionState = 'disconnected';
  private isManualClose = false;
  private connectionStartTime = 0;

  // metrics
  private connectionMetrics: ConnectionMetrics = {
    latency: 0,
    messagesSent: 0,
    messagesReceived: 0,
    reconnectCount: 0,
    lastConnected: null,
    uptime: 0,
    errorCount: 0,
    backpressure: 0,
  };

  // subscriptions & queue
  private subscriptions: Map<string, Subscription> = new Map();
  private messageQueue: QueuedMessage[] = [];
  private readonly maxQueue = 250;
  private readonly backpressureThreshold = 1_000_000; // bytes; tune per app

  // de-dup
  private messageBuffer: Map<string, number> = new Map();
  private readonly duplicateWindowMs = 5000;
  private dedupCleanupInterval: Interval | null = null;

  // intervals
  private queueProcessorInterval: Interval | null = null;

  constructor(url?: string, protocols?: string[]) {
    this.url = url || this.getWebSocketUrl();
    this.protocols = protocols;
    if (isBrowser) {
      this.bindConnectionStateHandlers();
      this.startMaintenanceLoops();
    }
  }

  // ---------- URLs / Bootstrapping ----------

  private getWebSocketUrl(): string {
    if (isBrowser) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/ws`;
    }
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  }

  // ---------- Lifecycle & Connection ----------

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!isBrowser) {
        reject(new Error('WebSocket unavailable on server'));
        return;
      }
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isManualClose = false;
      this.setConnectionState(this.reconnectAttempts ? 'reconnecting' : 'connecting');
      this.connectionStartTime = Date.now();

      // connection timeout
      this.clearConnectionTimeout();
      this.connectionTimeout = setTimeout(() => {
        if (this.connectionState === 'connecting' || this.connectionState === 'reconnecting') {
          this.setConnectionState('error');
          this.safeStoreSetQuality('poor');
          reject(new Error('WebSocket connection timeout'));
          this.safeClose('Connection timeout');
        }
      }, this.connectTimeoutMs);

      try {
        this.ws = new WebSocket(this.url, this.protocols);

        this.ws.onopen = () => {
          this.clearConnectionTimeout();
          this.setConnectionState('connected');
          this.reconnectAttempts = 0;
          this.connectionMetrics.lastConnected = new Date();
          this.startHeartbeat();
          this.safeStoreSetQuality('good');
          this.processMessageQueue();
          this.sendAuthIfAvailable();
          this.send('connection.info', {
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            reconnectCount: this.connectionMetrics.reconnectCount,
          });
          resolve();
        };

        this.ws.onmessage = (event) => this.handleMessage(event);

        this.ws.onclose = () => {
          this.clearConnectionTimeout();
          this.stopHeartbeat();
          this.connectionMetrics.errorCount++;
          this.connectionMetrics.backpressure = 0;
          if (!this.isManualClose) {
            this.setConnectionState('disconnected');
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (err) => {
          this.clearConnectionTimeout();
          this.connectionMetrics.errorCount++;
          this.safeStoreSetQuality('poor');
          // Don't reject if we're in reconnecting loop; resolve/reject only for explicit connect() call
          reject(err);
        };
      } catch (error) {
        this.clearConnectionTimeout();
        this.setConnectionState('error');
        this.connectionMetrics.errorCount++;
        reject(error);
      }
    });
  }

  public disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    this.clearReconnectTimeout();
    this.clearConnectionTimeout();
    this.safeClose('Manual disconnect');
    this.setConnectionState('disconnected');
    this.messageQueue = [];
  }

  private safeClose(reason: string) {
    try {
      if (this.ws) this.ws.close(1000, reason);
    } catch (error) {
      console.warn('Error closing WebSocket', error);
    }
    this.ws = null;
  }

  private scheduleReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.setConnectionState('error');
      this.safeStoreSetQuality('offline');
      return;
    }
    this.reconnectAttempts++;
    this.connectionMetrics.reconnectCount++;
    const exp = Math.min(this.maxReconnectDelay, this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1));
    const jitter = Math.floor(Math.random() * 400); // up to 400ms jitter
    const delay = exp + jitter;

    this.setConnectionState('reconnecting');
    this.clearReconnectTimeout();
    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(() => {
        // will be handled via onclose/onerror, next attempt scheduled there
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.missedPongs = 0;
    this.heartbeatInterval = setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      this.lastPingTs = Date.now();
      this.send('ping', { ts: this.lastPingTs }, 'system', { retry: false, priority: 'low' });
      // if pong not received by next tick, count as missed
      if (this.missedPongs > this.maxMissedPongs) {
        // force reconnect to recover a zombie connection
        this.safeClose('Missed pong threshold');
      }
      this.missedPongs++;
    }, this.heartbeatMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    this.heartbeatInterval = null;
    this.missedPongs = 0;
  }

  private clearReconnectTimeout() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this.reconnectTimeout = null;
  }

  private clearConnectionTimeout() {
    if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
    this.connectionTimeout = null;
  }

  // ---------- Messaging ----------

  public send(
    type: string,
    data: WebSocketPayload,
    channel = 'default',
    options: {
      priority?: 'low' | 'normal' | 'high' | 'critical';
      ttl?: number;
      retry?: boolean;
    } = {}
  ): boolean {
    const message: WebSocketMessage = {
      type,
      channel,
      data,
      timestamp: new Date().toISOString(),
      id: this.generateId('msg'),
      priority: options.priority ?? 'normal',
      ttl: options.ttl,
      retry: options.retry !== false,
    };

    if (!this.isConnected()) {
      this.queueMessage(message);
      return false;
    }
    return this.sendMessage(message);
  }

  private sendMessage(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.queueMessage(message);
      return false;
    }

    // backpressure: if bufferedAmount is high, requeue
    this.connectionMetrics.backpressure = this.ws.bufferedAmount;
    if (this.ws.bufferedAmount > this.backpressureThreshold) {
      this.queueMessage(message);
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      this.connectionMetrics.messagesSent++;
      return true;
    } catch (error) {
      console.warn('WebSocket send failed, requeueing', error);
      this.queueMessage(message);
      return false;
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    // TTL check at enqueue time
    if (message.ttl) {
      const createdAt = new Date(message.timestamp).getTime();
      if (Date.now() - createdAt > message.ttl) return;
    }

    const item: QueuedMessage = {
      message,
      enqueuedAt: Date.now(),
      attempts: 0,
      maxAttempts: message.retry ? 3 : 1,
    };

    const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 } as const;
    const p = priorityOrder[message.priority ?? 'normal'];

    // Insert by priority
    let idx = this.messageQueue.length;
    for (let i = 0; i < this.messageQueue.length; i++) {
      const q = priorityOrder[this.messageQueue[i].message.priority ?? 'normal'];
      if (p < q) {
        idx = i;
        break;
      }
    }
    this.messageQueue.splice(idx, 0, item);

    // Cap queue
    if (this.messageQueue.length > this.maxQueue) {
      this.messageQueue.length = this.maxQueue;
    }
  }

  private processMessageQueue(): void {
    if (!this.isConnected() || this.messageQueue.length === 0) return;

    const now = Date.now();
    const pending: QueuedMessage[] = [];
    for (const qm of this.messageQueue) {
      // TTL re-check
      if (qm.message.ttl) {
        const createdAt = new Date(qm.message.timestamp).getTime();
        if (now - createdAt > qm.message.ttl) continue;
      }
      if (this.sendMessage(qm.message)) {
        // sent
      } else {
        qm.attempts++;
        if (qm.attempts < qm.maxAttempts) pending.push(qm);
      }
    }
    this.messageQueue = pending;
  }

  private startMaintenanceLoops(): void {
    // queue processor
    if (!this.queueProcessorInterval) {
      this.queueProcessorInterval = setInterval(() => this.processMessageQueue(), 1000);
    }
    // dedup cleanup
    if (!this.dedupCleanupInterval) {
      this.dedupCleanupInterval = setInterval(() => {
        const now = Date.now();
        for (const [id, ts] of this.messageBuffer.entries()) {
          if (now - ts > this.duplicateWindowMs) this.messageBuffer.delete(id);
        }
      }, this.duplicateWindowMs);
    }
  }

  // ---------- Subscriptions ----------

  public subscribe(
    eventType: WebSocketEventType | string,
    callback: (data: WebSocketPayload, raw: WebSocketMessage) => void,
    options: { filter?: (data: WebSocketPayload, raw: WebSocketMessage) => boolean; once?: boolean } = {}
  ): () => void {
    const sub: Subscription = {
      id: this.generateId('sub'),
      eventType,
      callback,
      filter: options.filter,
      once: options.once,
    };
    this.subscriptions.set(sub.id, sub);
    return () => {
      this.subscriptions.delete(sub.id);
    };
  }

  public clearSubscriptions(): void {
    this.subscriptions.clear();
  }

  public getSubscriptionCount(): number {
    return this.subscriptions.size;
  }

  // ---------- Incoming messages ----------

  private handleMessage(event: MessageEvent): void {
    try {
      const msg: WebSocketMessage = JSON.parse(event.data);

      // duplicate suppression
      if (this.messageBuffer.has(msg.id)) return;
      this.messageBuffer.set(msg.id, Date.now());

      this.connectionMetrics.messagesReceived++;

      // pong handling
      if (msg.type === 'pong') {
        this.handlePong();
        return;
      }

      // emit to subscribers
      for (const sub of this.subscriptions.values()) {
        if (sub.eventType === msg.type || sub.eventType === '*') {
          if (sub.filter && !sub.filter(msg.data, msg)) continue;
          try {
            sub.callback(msg.data, msg);
          } catch (error) {
            console.error('Subscriber callback failed', { subscriptionId: sub.id, error });
          }
          if (sub.once) this.subscriptions.delete(sub.id);
        }
      }

      // app-specific handlers (optional)
      this.handleSpecificMessage(msg);
    } catch (error) {
      console.warn('Malformed websocket message', error, event.data);
    }
  }

  private handlePong(): void {
    if (this.lastPingTs) {
      this.connectionMetrics.latency = Date.now() - this.lastPingTs;
    }
    this.missedPongs = 0;
  }

  private handleSpecificMessage(message: WebSocketMessage): void {
    // Decoupled invalidation/notifications via app store
    const store = useAppStore?.getState?.();
    const notificationPayload = normalizeNotificationPayload(message.data);

    switch (message.type) {
      case 'notification':
        store?.addNotification?.({
          ...notificationPayload,
        });
        break;
      case 'system.health':
      case 'system.metrics':
        invalidateQueries?.system?.();
        break;
      case 'system.alert':
        store?.addNotification?.({
          ...notificationPayload,
          type: 'warning',
          title: 'System Alert',
        });
        invalidateQueries?.system?.();
        break;
      case 'plugin.status':
      case 'plugin.install':
      case 'plugin.error':
        if (message.type === 'plugin.error') {
          store?.addNotification?.({
            ...notificationPayload,
            type: 'error',
            title: 'Plugin Error',
          });
        }
        invalidateQueries?.plugins?.();
        break;
      case 'provider.status':
      case 'provider.model':
        invalidateQueries?.providers?.();
        break;
      case 'chat.message':
      case 'chat.status':
      case 'chat.typing':
        invalidateQueries?.chat?.();
        break;
      case 'memory.update':
      case 'memory.search':
        invalidateQueries?.memory?.();
        break;
      case 'performance.metrics':
        // hook for your live perf dashboard
        break;
      default:
        break;
    }
  }

  // ---------- State / Metrics ----------

  private setConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    const quality =
      state === 'connected' ? 'good' : state === 'connecting' || state === 'reconnecting' ? 'poor' : 'offline';
    this.safeStoreSetQuality(quality);
  }

  private safeStoreSetQuality(quality: 'good' | 'poor' | 'offline') {
    try {
      useAppStore.getState().setConnectionQuality?.(quality);
    } catch (error) {
      console.warn('Failed to update connection quality', error);
    }
  }

  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  public isConnected(): boolean {
    return this.connectionState === 'connected' && !!this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  public getConnectionMetrics(): ConnectionMetrics {
    const m = { ...this.connectionMetrics };
    if (this.connectionStartTime && this.connectionState === 'connected') {
      m.uptime = Date.now() - this.connectionStartTime;
    }
    return m;
  }

  public getMessageQueueSize(): number {
    return this.messageQueue.length;
  }

  // ---------- Environment Hooks ----------

  private bindConnectionStateHandlers(): void {
    // online/offline
    window.addEventListener('online', () => {
      try {
        useAppStore.getState().setOnline?.(true);
        this.safeStoreSetQuality('good');
      } catch (error) {
        console.warn('Failed to update online status', error);
      }
      if (this.connectionState === 'disconnected' || this.connectionState === 'suspended') {
        this.connect().catch(() => {});
      }
    });

    window.addEventListener('offline', () => {
      try {
        useAppStore.getState().setOnline?.(false);
        this.safeStoreSetQuality('offline');
      } catch (error) {
        console.warn('Failed to update offline status', error);
      }
      this.setConnectionState('suspended');
    });

    // visibility (optional suspend)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        if (this.connectionState === 'disconnected' || this.connectionState === 'suspended') {
          this.connect().catch(() => {});
        }
      }
    });

    // unload cleanup
    window.addEventListener('beforeunload', () => {
      this.disconnect();
    });
  }

  private sendAuthIfAvailable(): void {
    try {
      const store = useAppStore.getState?.();
      const user = store?.user;
      const token = this.getAuthToken();
      if (user && token) {
        this.send('auth', { token, userId: user.id, timestamp: new Date().toISOString() }, 'system', {
          retry: true,
          priority: 'high',
        });
      }
    } catch (error) {
      console.warn('Failed to send auth payload', error);
    }
  }

  private getAuthToken(): string | null {
    if (!isBrowser) return null;
    try {
      return localStorage.getItem('auth-token');
    } catch (error) {
      console.warn('Unable to read auth token', error);
      return null;
    }
  }

  // ---------- Utils ----------

  private generateId(prefix: string): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }

  public destroy(): void {
    this.disconnect();
    if (this.queueProcessorInterval) clearInterval(this.queueProcessorInterval);
    if (this.dedupCleanupInterval) clearInterval(this.dedupCleanupInterval);
    this.queueProcessorInterval = null;
    this.dedupCleanupInterval = null;
    this.clearSubscriptions();
    this.messageQueue = [];
    this.messageBuffer.clear();
  }
}

// Singleton
export const enhancedWebSocketService = new EnhancedWebSocketService();

// ---------- React Hooks ----------

export function useEnhancedWebSocket() {
  const [, force] = React.useReducer((x) => x + 1, 0);

  React.useEffect(() => {
    let mounted = true;
    // poll minimal state to trigger re-render (avoid heavy listeners)
    const interval = setInterval(() => {
      if (mounted) force();
    }, 500);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    connect: () => enhancedWebSocketService.connect(),
    disconnect: () => enhancedWebSocketService.disconnect(),
    send: (
      type: string,
      data: WebSocketPayload,
      channel?: string,
      options?: { priority?: 'low' | 'normal' | 'high' | 'critical'; ttl?: number; retry?: boolean }
    ) => enhancedWebSocketService.send(type, data, channel, options),
    subscribe: (
      eventType: WebSocketEventType | string,
      callback: (data: WebSocketPayload, raw: WebSocketMessage) => void,
      options?: { filter?: (data: WebSocketPayload, raw: WebSocketMessage) => boolean; once?: boolean }
    ) => enhancedWebSocketService.subscribe(eventType, callback, options),
    connectionState: enhancedWebSocketService.getConnectionState(),
    isConnected: enhancedWebSocketService.isConnected(),
    metrics: enhancedWebSocketService.getConnectionMetrics(),
    queueSize: enhancedWebSocketService.getMessageQueueSize(),
    subscriptionCount: enhancedWebSocketService.getSubscriptionCount(),
  };
}

export function useEnhancedWebSocketSubscription(
  eventType: WebSocketEventType | string,
  callback: (data: WebSocketPayload, raw: WebSocketMessage) => void,
  options: {
    filter?: (data: WebSocketPayload, raw: WebSocketMessage) => boolean;
    once?: boolean;
    deps?: React.DependencyList;
  } = {}
) {
  const { deps = [], filter, once } = options;
  React.useEffect(() => {
    const unsubscribe = enhancedWebSocketService.subscribe(eventType, callback, { filter, once });
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
