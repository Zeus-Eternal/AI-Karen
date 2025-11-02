/**
 * Enhanced WebSocket Service
 * 
 * Advanced real-time updates with robust connection management, automatic reconnection,
 * and message queuing.
 * Based on requirements: 12.2, 12.3
 */
import { useAppStore } from '@/store/app-store';
import { queryClient, invalidateQueries } from '@/lib/query-client';
// Enhanced WebSocket message types
export interface WebSocketMessage {
  type: string;
  channel: string;
  data: any;
  timestamp: string;
  id: string;
  priority?: 'low' | 'normal' | 'high' | 'critical';
  ttl?: number; // Time to live in milliseconds
  retry?: boolean;
}
// WebSocket event types
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
  | 'performance.metrics';
// Connection states
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting' | 'suspended';
// Connection quality metrics
export interface ConnectionMetrics {
  latency: number;
  messagesSent: number;
  messagesReceived: number;
  reconnectCount: number;
  lastConnected: Date | null;
  uptime: number;
  errorCount: number;
}
// Message queue item
interface QueuedMessage {
  message: WebSocketMessage;
  timestamp: Date;
  attempts: number;
  maxAttempts: number;
}
// Subscription
interface Subscription {
  id: string;
  eventType: WebSocketEventType;
  callback: (data: any) => void;
  filter?: (data: any) => boolean;
  once?: boolean;
}
// Enhanced WebSocket service class
export class EnhancedWebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private protocols?: string[];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private subscriptions: Map<string, Subscription> = new Map();
  private messageQueue: QueuedMessage[] = [];
  private connectionState: ConnectionState = 'disconnected';
  private isManualClose = false;
  private connectionMetrics: ConnectionMetrics = {
    latency: 0,
    messagesSent: 0,
    messagesReceived: 0,
    reconnectCount: 0,
    lastConnected: null,
    uptime: 0,
    errorCount: 0,
  };
  private lastPingTime = 0;
  private connectionStartTime = 0;
  private messageBuffer: Map<string, WebSocketMessage> = new Map();
  private duplicateMessageWindow = 5000; // 5 seconds
  constructor(url?: string, protocols?: string[]) {
    this.url = url || this.getWebSocketUrl();
    this.protocols = protocols;
    this.setupConnectionStateHandlers();
    this.setupMessageQueueProcessor();
  }
  // Get WebSocket URL based on current location
  private getWebSocketUrl(): string {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/ws`;
    }
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  }
  // Setup connection state handlers
  private setupConnectionStateHandlers(): void {
    // Listen for online/offline events
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        const { setOnline, setConnectionQuality } = useAppStore.getState();
        setOnline(true);
        setConnectionQuality('good');
        if (this.connectionState === 'disconnected' || this.connectionState === 'suspended') {
          this.connect();
        }

      window.addEventListener('offline', () => {
        const { setOnline, setConnectionQuality } = useAppStore.getState();
        setOnline(false);
        setConnectionQuality('offline');
        this.setConnectionState('suspended');

      // Listen for visibility changes to manage connection
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          if (this.connectionState === 'disconnected' || this.connectionState === 'suspended') {
            this.connect();
          }
        } else {
          // Optionally suspend connection when tab is hidden to save resources
          // this.setConnectionState('suspended');
        }

      // Listen for page unload to clean up
      window.addEventListener('beforeunload', () => {
        this.disconnect();

    }
  }
  // Setup message queue processor
  private setupMessageQueueProcessor(): void {
    // Process message queue every 1 second
    setInterval(() => {
      this.processMessageQueue();
    }, 1000);
    // Clean up old messages from buffer
    setInterval(() => {
      const now = Date.now();
      for (const [id, message] of this.messageBuffer.entries()) {
        const messageTime = new Date(message.timestamp).getTime();
        if (now - messageTime > this.duplicateMessageWindow) {
          this.messageBuffer.delete(id);
        }
      }
    }, this.duplicateMessageWindow);
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
      this.connectionStartTime = Date.now();
      // Set connection timeout
      this.connectionTimeout = setTimeout(() => {
        if (this.connectionState === 'connecting') {
          this.setConnectionState('error');
          reject(new Error('Connection timeout'));
        }
      }, 10000); // 10 second timeout
      try {
        this.ws = new WebSocket(this.url, this.protocols);
        this.ws.onopen = () => {
          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
          }
          this.setConnectionState('connected');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.connectionMetrics.lastConnected = new Date();
          this.connectionMetrics.reconnectCount = Math.max(0, this.connectionMetrics.reconnectCount);
          this.startHeartbeat();
          this.processMessageQueue();
          const { setConnectionQuality, addNotification } = useAppStore.getState();
          setConnectionQuality('good');
          // Send authentication if user is logged in
          const { user } = useAppStore.getState();
          if (user) {
            this.send('auth', { 
              token: this.getAuthToken(),
              userId: user.id,
              timestamp: new Date().toISOString(),

          }
          // Send connection info
          this.send('connection.info', {
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            reconnectCount: this.connectionMetrics.reconnectCount,

          resolve();
        };
        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };
        this.ws.onclose = (event) => {
          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
          }
          this.stopHeartbeat();
          if (!this.isManualClose) {
            this.setConnectionState('disconnected');
            this.connectionMetrics.errorCount++;
            // Log close reason
            this.scheduleReconnect();
          }
        };
        this.ws.onerror = (error) => {
          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
          }
          this.setConnectionState('error');
          this.connectionMetrics.errorCount++;
          const { setConnectionQuality, addNotification } = useAppStore.getState();
          setConnectionQuality('poor');
          reject(error);
        };
      } catch (error) {
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout);
          this.connectionTimeout = null;
        }
        this.setConnectionState('error');
        this.connectionMetrics.errorCount++;
        reject(error);
      }

  }
  // Disconnect from WebSocket
  public disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.setConnectionState('disconnected');
    this.messageQueue = []; // Clear message queue
  }
  // Send message through WebSocket
  public send(
    type: string, 
    data: any, 
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
      id: this.generateMessageId(),
      priority: options.priority || 'normal',
      ttl: options.ttl,
      retry: options.retry !== false, // Default to true
    };
    // If not connected, queue the message
    if (!this.isConnected()) {
      this.queueMessage(message);
      return false;
    }
    return this.sendMessage(message);
  }
  // Send message immediately
  private sendMessage(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.queueMessage(message);
      return false;
    }
    try {
      this.ws.send(JSON.stringify(message));
      this.connectionMetrics.messagesSent++;
      return true;
    } catch (error) {
      this.queueMessage(message);
      return false;
    }
  }
  // Queue message for later sending
  private queueMessage(message: WebSocketMessage): void {
    // Check TTL
    if (message.ttl) {
      const messageTime = new Date(message.timestamp).getTime();
      if (Date.now() - messageTime > message.ttl) {
        return; // Message expired
      }
    }
    // Add to queue with priority sorting
    const queuedMessage: QueuedMessage = {
      message,
      timestamp: new Date(),
      attempts: 0,
      maxAttempts: message.retry ? 3 : 1,
    };
    // Insert based on priority
    const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 };
    const messagePriority = priorityOrder[message.priority || 'normal'];
    let insertIndex = this.messageQueue.length;
    for (let i = 0; i < this.messageQueue.length; i++) {
      const queuePriority = priorityOrder[this.messageQueue[i].message.priority || 'normal'];
      if (messagePriority < queuePriority) {
        insertIndex = i;
        break;
      }
    }
    this.messageQueue.splice(insertIndex, 0, queuedMessage);
    // Limit queue size
    if (this.messageQueue.length > 100) {
      this.messageQueue = this.messageQueue.slice(0, 100);
    }
  }
  // Process message queue
  private processMessageQueue(): void {
    if (!this.isConnected() || this.messageQueue.length === 0) {
      return;
    }
    const now = Date.now();
    const messagesToProcess = [...this.messageQueue];
    this.messageQueue = [];
    for (const queuedMessage of messagesToProcess) {
      // Check TTL
      if (queuedMessage.message.ttl) {
        const messageTime = new Date(queuedMessage.message.timestamp).getTime();
        if (now - messageTime > queuedMessage.message.ttl) {
          continue; // Skip expired message
        }
      }
      // Try to send message
      if (this.sendMessage(queuedMessage.message)) {
        // Message sent successfully
        continue;
      } else {
        // Failed to send, check attempts
        queuedMessage.attempts++;
        if (queuedMessage.attempts < queuedMessage.maxAttempts) {
          this.messageQueue.push(queuedMessage);
        }
      }
    }
  }
  // Subscribe to WebSocket events
  public subscribe(
    eventType: WebSocketEventType, 
    callback: (data: any) => void,
    options: {
      filter?: (data: any) => boolean;
      once?: boolean;
    } = {}
  ): () => void {
    const subscription: Subscription = {
      id: this.generateSubscriptionId(),
      eventType,
      callback,
      filter: options.filter,
      once: options.once,
    };
    this.subscriptions.set(subscription.id, subscription);
    // Return unsubscribe function
    return () => {
      this.subscriptions.delete(subscription.id);
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
  // Get connection metrics
  public getConnectionMetrics(): ConnectionMetrics {
    const metrics = { ...this.connectionMetrics };
    if (this.connectionStartTime && this.connectionState === 'connected') {
      metrics.uptime = Date.now() - this.connectionStartTime;
    }
    return metrics;
  }
  // Handle incoming messages
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.connectionMetrics.messagesReceived++;
      // Check for duplicate messages
      if (this.messageBuffer.has(message.id)) {
        return; // Duplicate message, ignore
      }
      this.messageBuffer.set(message.id, message);
      // Handle system messages
      if (message.type === 'pong') {
        this.handlePong();
        return;
      }
      // Emit to subscribers
      const matchingSubscriptions = Array.from(this.subscriptions.values())
        .filter(sub => sub.eventType === message.type);
      for (const subscription of matchingSubscriptions) {
        try {
          // Apply filter if present
          if (subscription.filter && !subscription.filter(message.data)) {
            continue;
          }
          subscription.callback(message.data);
          // Remove one-time subscriptions
          if (subscription.once) {
            this.subscriptions.delete(subscription.id);
          }
        } catch (error) {
        }
      }
      // Handle specific message types
      this.handleSpecificMessage(message);
    } catch (error) {
    }
  }
  // Handle pong response
  private handlePong(): void {
    if (this.lastPingTime) {
      this.connectionMetrics.latency = Date.now() - this.lastPingTime;
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

        break;
      case 'system.health':
        invalidateQueries.system();
        break;
      case 'system.alert':
        addNotification({
          type: 'warning',
          title: 'System Alert',
          message: message.data.message,

        invalidateQueries.system();
        break;
      case 'chat.message':
        invalidateQueries.chat();
        break;
      case 'memory.update':
        invalidateQueries.memory();
        break;
      case 'plugin.status':
        invalidateQueries.plugins();
        break;
      case 'plugin.error':
        addNotification({
          type: 'error',
          title: 'Plugin Error',
          message: message.data.message,

        invalidateQueries.plugins();
        break;
      case 'provider.status':
        invalidateQueries.providers();
        break;
      case 'user.presence':
        // Handle user presence updates
        break;
      case 'performance.metrics':
        // Handle performance metrics updates
        break;
      default:
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
      case 'suspended':
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
    this.connectionMetrics.reconnectCount++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 
      this.maxReconnectDelay
    );
    this.reconnectTimeout = setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect().catch(() => {
        // Reconnection failed, will be handled by onclose

    }, delay);
  }
  // Start heartbeat
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now();
        this.send('ping', { timestamp: this.lastPingTime });
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
  // Generate unique subscription ID
  private generateSubscriptionId(): string {
    return `sub-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  // Get authentication token
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth-token');
    }
    return null;
  }
  // Clear all subscriptions
  public clearSubscriptions(): void {
    this.subscriptions.clear();
  }
  // Get subscription count
  public getSubscriptionCount(): number {
    return this.subscriptions.size;
  }
  // Get message queue size
  public getMessageQueueSize(): number {
    return this.messageQueue.length;
  }
}
// Create singleton instance
export const enhancedWebSocketService = new EnhancedWebSocketService();
// React hook for using enhanced WebSocket
export function useEnhancedWebSocket() {
  const connectionState = enhancedWebSocketService.getConnectionState();
  const isConnected = enhancedWebSocketService.isConnected();
  const metrics = enhancedWebSocketService.getConnectionMetrics();
  return {
    connect: () => enhancedWebSocketService.connect(),
    disconnect: () => enhancedWebSocketService.disconnect(),
    send: (type: string, data: any, channel?: string, options?: any) => 
      enhancedWebSocketService.send(type, data, channel, options),
    subscribe: (eventType: WebSocketEventType, callback: (data: any) => void, options?: any) => 
      enhancedWebSocketService.subscribe(eventType, callback, options),
    connectionState,
    isConnected,
    metrics,
    queueSize: enhancedWebSocketService.getMessageQueueSize(),
    subscriptionCount: enhancedWebSocketService.getSubscriptionCount(),
  };
}
// React hook for subscribing to WebSocket events with enhanced features
export function useEnhancedWebSocketSubscription(
  eventType: WebSocketEventType,
  callback: (data: any) => void,
  options: {
    filter?: (data: any) => boolean;
    once?: boolean;
    deps?: React.DependencyList;
  } = {}
) {
  const { deps = [], ...subscriptionOptions } = options;
  React.useEffect(() => {
    const unsubscribe = enhancedWebSocketService.subscribe(eventType, callback, subscriptionOptions);
    return unsubscribe;
  }, deps);
}
