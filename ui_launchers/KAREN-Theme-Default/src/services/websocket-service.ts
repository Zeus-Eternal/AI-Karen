/**
 * WebSocket Service
 *
 * Real-time updates with connection management and automatic reconnection.
 * Based on requirements: 12.2, 12.3
 */

import * as React from 'react';
import { useAppStore } from '@/store/app-store';
import { invalidateQueries } from '@/lib/query-client';

type NotificationType = 'info' | 'success' | 'warning' | 'error';
const isNotificationType = (value: unknown): value is NotificationType =>
  value === 'info' || value === 'success' || value === 'warning' || value === 'error';

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  channel: string;
  data: unknown;
  timestamp: string;
  id?: string;
}

// WebSocket event types
export type WebSocketEventType =
  | 'chat.message'
  | 'chat.typing'
  | 'system.health'
  | 'system.metrics'
  | 'memory.update'
  | 'plugin.status'
  | 'provider.status'
  | 'user.activity'
  | 'notification';

// Connection states
export type ConnectionState =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'reconnecting';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;

  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private readonly maxReconnectDelay = 30000;

  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  private listeners: Map<WebSocketEventType, Set<(data: unknown) => void>> = new Map();

  private connectionState: ConnectionState = 'disconnected';
  private isManualClose = false;

  constructor(url?: string) {
    this.url = url || this.getWebSocketUrl();
    this.setupConnectionStateHandlers();
  }

  // Get WebSocket URL based on current location
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  }

  // Setup connection state handlers
  private setupConnectionStateHandlers(): void {
    // Online
    window.addEventListener('online', () => {
      const { setOnline, setConnectionQuality } = useAppStore.getState();
      setOnline(true);
      setConnectionQuality('good');
      if (this.connectionState === 'disconnected') {
        this.connect().catch(() => void 0);
      }
    });

    // Offline
    window.addEventListener('offline', () => {
      const { setOnline, setConnectionQuality } = useAppStore.getState();
      setOnline(false);
      setConnectionQuality('offline');
      this.setConnectionState('disconnected');
      this.stopHeartbeat();
      if (this.ws) {
        try {
          this.ws.close();
        } catch (error) {
          // Ignore close errors
          void error;
        }
        this.ws = null;
      }
    });

    // Page visibility
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.connectionState === 'disconnected') {
        this.connect().catch(() => void 0);
      }
    });
  }

  // Connect to WebSocket
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isManualClose = false;
      this.setConnectionState('connecting');

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.setConnectionState('connected');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startHeartbeat();

          const { setConnectionQuality } = useAppStore.getState();
          setConnectionQuality('good');

          // Send authentication if user is logged in
          const { user } = useAppStore.getState();
          if (user) {
            this.send('auth', { token: this.getAuthToken() });
          }

          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = () => {
          this.stopHeartbeat();
          if (!this.isManualClose) {
            this.setConnectionState('disconnected');
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = () => {
          this.setConnectionState('error');
          const { setConnectionQuality } = useAppStore.getState();
          setConnectionQuality('poor');
          reject(new Error('WebSocket connection error'));
        };
      } catch (error) {
        this.setConnectionState('error');
        reject(error);
      }
    });
  }

  // Disconnect from WebSocket
  public disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      try {
        this.ws.close();
      } catch (error) {
        // Ignore close errors
        void error;
      }
      this.ws = null;
    }

    this.setConnectionState('disconnected');
  }

  // Send message through WebSocket
  public send(type: string, data: unknown, channel = 'default'): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    const message: WebSocketMessage = {
      type,
      channel,
      data,
      timestamp: new Date().toISOString(),
      id: this.generateMessageId(),
    };
    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch {
      return false;
    }
  }

  // Subscribe to WebSocket events
  public subscribe(eventType: WebSocketEventType, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
    // Return unsubscribe
    return () => {
      const listeners = this.listeners.get(eventType);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  // Get current connection state
  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  // Check if connected
  public isConnected(): boolean {
    return this.connectionState === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  // Handle incoming messages
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Heartbeat response
      if (message.type === 'pong') return;

      // Emit to listeners
      const listeners = this.listeners.get(message.type as WebSocketEventType);
      if (listeners) {
        listeners.forEach((cb) => {
          try {
            cb(message.data);
          } catch (error) {
            // swallow listener errors
            void error;
          }
        });
      }

      // Side effects for specific message types
      this.handleSpecificMessage(message);
    } catch {
      // ignore malformed messages
      return;
    }
  }

  // Handle specific message types -> invalidate queries, notify, etc.
  private handleSpecificMessage(message: WebSocketMessage): void {
    const { addNotification } = useAppStore.getState();

    switch (message.type as WebSocketEventType) {
      case 'notification': {
        // message.data: { type?: 'info'|'success'|'warning'|'error', title: string, message: string }
        const payload = (message.data as Record<string, unknown>) || {};
        const normalizedType = isNotificationType(payload.type) ? payload.type : 'info';
        const title = typeof payload.title === 'string' ? payload.title : 'Notification';
        const text = typeof payload.message === 'string' ? payload.message : '';
        addNotification?.({
          type: normalizedType,
          title,
          message: text,
        });
        break;
      }
      case 'system.health':
        invalidateQueries.system?.();
        break;
      case 'chat.message':
        invalidateQueries.chat?.();
        break;
      case 'memory.update':
        invalidateQueries.memory?.();
        break;
      case 'plugin.status':
        invalidateQueries.plugins?.();
        break;
      case 'provider.status':
        invalidateQueries.providers?.();
        break;
      case 'chat.typing':
      case 'system.metrics':
      case 'user.activity':
      default:
        // no-op or add handling as needed
        break;
    }
  }

  // Set connection state and update store
  private setConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    const { setConnectionQuality } = useAppStore.getState();
    switch (state) {
      case 'connected':
        setConnectionQuality('good');
        break;
      case 'connecting':
      case 'reconnecting':
        setConnectionQuality('poor');
        break;
      case 'disconnected':
      case 'error':
        setConnectionQuality('offline');
        break;
    }
  }

  // Schedule reconnection with backoff
  private scheduleReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.setConnectionState('reconnecting');
    this.reconnectAttempts++;

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    this.reconnectTimeout = setTimeout(() => {
      // eslint-disable-next-line no-console
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );
      this.connect().catch(() => {
        // failure handled via onclose -> will schedule next backoff attempt
      });
    }, delay);
  }

  // Start heartbeat
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, 30000); // 30s ping
  }

  // Stop heartbeat
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Generate unique message ID
  private generateMessageId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  }

  // Get authentication token
  private getAuthToken(): string | null {
    return localStorage.getItem('karen_access_token');
  }
}

export let websocketService: WebSocketService | null = null;

const getWebSocketService = (): WebSocketService | null => {
  if (typeof window === 'undefined') return null;
  if (!websocketService) {
    websocketService = new WebSocketService();
  }
  return websocketService;
};

// React hook for using WebSocket
export function useWebSocket() {
  const service = getWebSocketService();
  const connectionState = service?.getConnectionState() ?? 'disconnected';
  const isConnected = service?.isConnected() ?? false;

  return {
    connect: () => service?.connect(),
    disconnect: () => service?.disconnect(),
    send: (type: string, data: unknown, channel?: string) => service?.send(type, data, channel),
    subscribe: (eventType: WebSocketEventType, callback: (data: unknown) => void) =>
      service?.subscribe(eventType, callback),
    connectionState,
    isConnected,
  };
}

// React hook for subscribing to WebSocket events
export function useWebSocketSubscription(
  eventType: WebSocketEventType,
  callback: (data: unknown) => void,
  deps: React.DependencyList = []
) {
  React.useEffect(() => {
    const service = getWebSocketService();
    if (!service) return undefined;
    const unsubscribe = service.subscribe(eventType, callback);
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

export { getWebSocketService };
