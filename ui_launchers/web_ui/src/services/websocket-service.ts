/**
 * WebSocket Service
 * 
 * Real-time updates with connection management and automatic reconnection.
 * Based on requirements: 12.2, 12.3
 */
import { useAppStore } from '@/store/app-store';
import { queryClient, invalidateQueries } from '@/lib/query-client';
// WebSocket message types
export interface WebSocketMessage {
  type: string;
  channel: string;
  data: any;
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
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';
// WebSocket service class
export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
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
    // Listen for online/offline events
    window.addEventListener('online', () => {
      const { setOnline, setConnectionQuality } = useAppStore.getState();
      setOnline(true);
      setConnectionQuality('good');
      if (this.connectionState === 'disconnected') {
        this.connect();
      }
    });
    window.addEventListener('offline', () => {
      const { setOnline, setConnectionQuality } = useAppStore.getState();
      setOnline(false);
      setConnectionQuality('offline');
    });
    // Listen for visibility changes to manage connection
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.connectionState === 'disconnected') {
        this.connect();
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
          const { setConnectionQuality, addNotification } = useAppStore.getState();
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
        this.ws.onclose = (event) => {
          this.stopHeartbeat();
          if (!this.isManualClose) {
            this.setConnectionState('disconnected');
            this.scheduleReconnect();
          }
        };
        this.ws.onerror = (error) => {
          this.setConnectionState('error');
          const { setConnectionQuality, addNotification } = useAppStore.getState();
          setConnectionQuality('poor');
          reject(error);
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
      this.ws.close();
      this.ws = null;
    }
    this.setConnectionState('disconnected');
  }
  // Send message through WebSocket
  public send(type: string, data: any, channel = 'default'): boolean {
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
    } catch (error) {
      return false;
    }
  }
  // Subscribe to WebSocket events
  public subscribe(eventType: WebSocketEventType, callback: (data: any) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
    // Return unsubscribe function
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
      // Handle system messages
      if (message.type === 'pong') {
        // Heartbeat response
        return;
      }
      // Emit to listeners
      const listeners = this.listeners.get(message.type as WebSocketEventType);
      if (listeners) {
        listeners.forEach(callback => {
          try {
            callback(message.data);
          } catch (error) {
          }
        });
      }
      // Handle specific message types
      this.handleSpecificMessage(message);
    } catch (error) {
    }
  }
  // Handle specific message types
  private handleSpecificMessage(message: WebSocketMessage): void {
    const { addNotification } = useAppStore.getState();
    switch (message.type) {
      case 'notification':
        addNotification({
          type: message.data.type || 'info',
          title: message.data.title,
          message: message.data.message,
        });
        break;
      case 'system.health':
        // Invalidate system health queries
        invalidateQueries.system();
        break;
      case 'chat.message':
        // Invalidate chat queries
        invalidateQueries.chat();
        break;
      case 'memory.update':
        // Invalidate memory queries
        invalidateQueries.memory();
        break;
      case 'plugin.status':
        // Invalidate plugin queries
        invalidateQueries.plugins();
        break;
      case 'provider.status':
        // Invalidate provider queries
        invalidateQueries.providers();
        break;
      default:
        // Handle unknown message types
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
  // Schedule reconnection
  private scheduleReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    this.setConnectionState('reconnecting');
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    this.reconnectTimeout = setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect().catch(() => {
        // Reconnection failed, will be handled by onclose
      });
    }, delay);
  }
  // Start heartbeat
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, 30000); // Send ping every 30 seconds
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
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  // Get authentication token
  private getAuthToken(): string | null {
    // This would typically get the token from your auth system
    return localStorage.getItem('auth-token');
  }
}
// Create singleton instance
export const websocketService = new WebSocketService();
// React hook for using WebSocket
export function useWebSocket() {
  const connectionState = websocketService.getConnectionState();
  const isConnected = websocketService.isConnected();
  return {
    connect: () => websocketService.connect(),
    disconnect: () => websocketService.disconnect(),
    send: (type: string, data: any, channel?: string) => websocketService.send(type, data, channel),
    subscribe: (eventType: WebSocketEventType, callback: (data: any) => void) => 
      websocketService.subscribe(eventType, callback),
    connectionState,
    isConnected,
  };
}
// React hook for subscribing to WebSocket events
export function useWebSocketSubscription(
  eventType: WebSocketEventType,
  callback: (data: any) => void,
  deps: React.DependencyList = []
) {
  React.useEffect(() => {
    const unsubscribe = websocketService.subscribe(eventType, callback);
    return unsubscribe;
  }, deps);
}
