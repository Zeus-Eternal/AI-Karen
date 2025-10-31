/**
 * Enhanced WebSocket Service Tests
 * 
 * Unit tests for the enhanced WebSocket service with connection management.
 * Based on requirements: 12.2, 12.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EnhancedWebSocketService } from '../enhanced-websocket-service';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  protocols?: string[];
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string, protocols?: string[]) {
    this.url = url;
    this.protocols = protocols;
    
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Mock successful send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason, wasClean: true }));
    }
  }

  // Helper method to simulate receiving a message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  // Helper method to simulate error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

global.WebSocket = MockWebSocket as any;

// Mock useAppStore
const mockAppStore = {
  setOnline: vi.fn(),
  setConnectionQuality: vi.fn(),
  addNotification: vi.fn(),
  getState: () => ({
    user: { id: '1', name: 'Test User' },
  }),
};

vi.mock('@/store/app-store', () => ({
  useAppStore: {
    getState: () => mockAppStore,
  },
}));

// Mock query client
vi.mock('@/lib/query-client', () => ({
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  invalidateQueries: {
    system: vi.fn(),
    chat: vi.fn(),
    memory: vi.fn(),
    plugins: vi.fn(),
    providers: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('EnhancedWebSocketService', () => {
  let wsService: EnhancedWebSocketService;

  beforeEach(() => {
    wsService = new EnhancedWebSocketService('ws://localhost:8000/ws');
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('test-token');
  });

  afterEach(() => {
    wsService.disconnect();
    vi.clearAllTimers();
  });

  describe('Connection Management', () => {
    it('should initialize with disconnected state', () => {
      expect(wsService.getConnectionState()).toBe('disconnected');
      expect(wsService.isConnected()).toBe(false);
    });

    it('should connect successfully', async () => {
      const connectPromise = wsService.connect();
      
      // Wait for connection to open
      await new Promise(resolve => setTimeout(resolve, 20));
      
      await connectPromise;
      
      expect(wsService.getConnectionState()).toBe('connected');
      expect(wsService.isConnected()).toBe(true);
    });

    it('should disconnect cleanly', async () => {
      await wsService.connect();
      expect(wsService.isConnected()).toBe(true);
      
      wsService.disconnect();
      
      expect(wsService.getConnectionState()).toBe('disconnected');
      expect(wsService.isConnected()).toBe(false);
    });

    it('should not connect if already connected', async () => {
      await wsService.connect();
      const firstConnectionState = wsService.getConnectionState();
      
      await wsService.connect(); // Second connect call
      
      expect(wsService.getConnectionState()).toBe(firstConnectionState);
    });
  });

  describe('Message Sending', () => {
    beforeEach(async () => {
      await wsService.connect();
    });

    it('should send message when connected', () => {
      const result = wsService.send('test', { message: 'hello' });
      
      expect(result).toBe(true);
    });

    it('should queue message when not connected', () => {
      wsService.disconnect();
      
      const result = wsService.send('test', { message: 'hello' });
      
      expect(result).toBe(false);
      expect(wsService.getMessageQueueSize()).toBe(1);
    });

    it('should send message with priority', () => {
      const result = wsService.send('test', { message: 'urgent' }, 'default', {
        priority: 'high',
      });
      
      expect(result).toBe(true);
    });

    it('should respect TTL for messages', () => {
      wsService.disconnect();
      
      // Send message with very short TTL
      wsService.send('test', { message: 'expired' }, 'default', {
        ttl: 1, // 1ms TTL
      });
      
      expect(wsService.getMessageQueueSize()).toBe(1);
      
      // Wait for TTL to expire and process queue
      setTimeout(() => {
        // Message should be expired and removed from queue
        expect(wsService.getMessageQueueSize()).toBe(0);
      }, 10);
    });
  });

  describe('Message Subscriptions', () => {
    beforeEach(async () => {
      await wsService.connect();
    });

    it('should subscribe to events', () => {
      const callback = vi.fn();
      const unsubscribe = wsService.subscribe('chat.message', callback);
      
      expect(wsService.getSubscriptionCount()).toBe(1);
      expect(typeof unsubscribe).toBe('function');
    });

    it('should unsubscribe from events', () => {
      const callback = vi.fn();
      const unsubscribe = wsService.subscribe('chat.message', callback);
      
      expect(wsService.getSubscriptionCount()).toBe(1);
      
      unsubscribe();
      
      expect(wsService.getSubscriptionCount()).toBe(0);
    });

    it('should call subscription callback when message received', () => {
      const callback = vi.fn();
      wsService.subscribe('chat.message', callback);
      
      // Simulate receiving a message
      const mockWs = (wsService as any).ws as MockWebSocket;
      mockWs.simulateMessage({
        type: 'chat.message',
        channel: 'default',
        data: { text: 'Hello' },
        timestamp: new Date().toISOString(),
        id: 'msg-1',
      });
      
      expect(callback).toHaveBeenCalledWith({ text: 'Hello' });
    });

    it('should filter messages based on filter function', () => {
      const callback = vi.fn();
      wsService.subscribe('chat.message', callback, {
        filter: (data) => data.important === true,
      });
      
      const mockWs = (wsService as any).ws as MockWebSocket;
      
      // Send message that should be filtered out
      mockWs.simulateMessage({
        type: 'chat.message',
        channel: 'default',
        data: { text: 'Not important', important: false },
        timestamp: new Date().toISOString(),
        id: 'msg-1',
      });
      
      expect(callback).not.toHaveBeenCalled();
      
      // Send message that should pass filter
      mockWs.simulateMessage({
        type: 'chat.message',
        channel: 'default',
        data: { text: 'Important', important: true },
        timestamp: new Date().toISOString(),
        id: 'msg-2',
      });
      
      expect(callback).toHaveBeenCalledWith({ text: 'Important', important: true });
    });

    it('should handle one-time subscriptions', () => {
      const callback = vi.fn();
      wsService.subscribe('chat.message', callback, { once: true });
      
      expect(wsService.getSubscriptionCount()).toBe(1);
      
      const mockWs = (wsService as any).ws as MockWebSocket;
      mockWs.simulateMessage({
        type: 'chat.message',
        channel: 'default',
        data: { text: 'Hello' },
        timestamp: new Date().toISOString(),
        id: 'msg-1',
      });
      
      expect(callback).toHaveBeenCalledOnce();
      expect(wsService.getSubscriptionCount()).toBe(0); // Should be auto-unsubscribed
    });
  });

  describe('Connection Metrics', () => {
    it('should track connection metrics', async () => {
      const initialMetrics = wsService.getConnectionMetrics();
      expect(initialMetrics.messagesSent).toBe(0);
      expect(initialMetrics.messagesReceived).toBe(0);
      expect(initialMetrics.reconnectCount).toBe(0);
      
      await wsService.connect();
      
      // Send a message
      wsService.send('test', { message: 'hello' });
      
      // Simulate receiving a message
      const mockWs = (wsService as any).ws as MockWebSocket;
      mockWs.simulateMessage({
        type: 'test',
        channel: 'default',
        data: { message: 'response' },
        timestamp: new Date().toISOString(),
        id: 'msg-1',
      });
      
      const metrics = wsService.getConnectionMetrics();
      expect(metrics.messagesSent).toBe(1);
      expect(metrics.messagesReceived).toBe(1);
      expect(metrics.lastConnected).toBeInstanceOf(Date);
    });

    it('should track latency with ping/pong', async () => {
      await wsService.connect();
      
      // Simulate ping/pong
      const mockWs = (wsService as any).ws as MockWebSocket;
      
      // Start heartbeat manually for testing
      (wsService as any).lastPingTime = Date.now();
      
      // Simulate pong response after 50ms
      setTimeout(() => {
        mockWs.simulateMessage({
          type: 'pong',
          channel: 'system',
          data: {},
          timestamp: new Date().toISOString(),
          id: 'pong-1',
        });
      }, 50);
      
      // Wait for pong
      await new Promise(resolve => setTimeout(resolve, 60));
      
      const metrics = wsService.getConnectionMetrics();
      expect(metrics.latency).toBeGreaterThan(0);
      expect(metrics.latency).toBeLessThan(100);
    });
  });

  describe('Error Handling', () => {
    it('should handle connection errors', async () => {
      const connectPromise = wsService.connect();
      
      // Simulate connection error
      setTimeout(() => {
        const mockWs = (wsService as any).ws as MockWebSocket;
        mockWs.simulateError();
      }, 5);
      
      await expect(connectPromise).rejects.toThrow();
      expect(wsService.getConnectionState()).toBe('error');
    });

    it('should handle message parsing errors', async () => {
      await wsService.connect();
      
      const callback = vi.fn();
      wsService.subscribe('test', callback);
      
      // Simulate invalid JSON message
      const mockWs = (wsService as any).ws as MockWebSocket;
      if (mockWs.onmessage) {
        mockWs.onmessage(new MessageEvent('message', { data: 'invalid json' }));
      }
      
      // Callback should not be called for invalid messages
      expect(callback).not.toHaveBeenCalled();
    });

    it('should handle subscription callback errors', async () => {
      await wsService.connect();
      
      const errorCallback = vi.fn(() => {
        throw new Error('Callback error');
      });
      const normalCallback = vi.fn();
      
      wsService.subscribe('test', errorCallback);
      wsService.subscribe('test', normalCallback);
      
      const mockWs = (wsService as any).ws as MockWebSocket;
      mockWs.simulateMessage({
        type: 'test',
        channel: 'default',
        data: { message: 'test' },
        timestamp: new Date().toISOString(),
        id: 'msg-1',
      });
      
      // Both callbacks should be called, error in one shouldn't affect the other
      expect(errorCallback).toHaveBeenCalled();
      expect(normalCallback).toHaveBeenCalled();
    });
  });

  describe('Reconnection Logic', () => {
    it('should attempt reconnection on connection loss', async () => {
      vi.useFakeTimers();
      
      await wsService.connect();
      expect(wsService.isConnected()).toBe(true);
      
      // Simulate connection loss
      const mockWs = (wsService as any).ws as MockWebSocket;
      mockWs.close(1006, 'Connection lost');
      
      expect(wsService.getConnectionState()).toBe('disconnected');
      
      // Fast forward time to trigger reconnection
      vi.advanceTimersByTime(2000);
      
      // Should attempt to reconnect
      expect(wsService.getConnectionState()).toBe('reconnecting');
      
      vi.useRealTimers();
    });

    it('should respect maximum reconnection attempts', async () => {
      vi.useFakeTimers();
      
      // Create service with low max attempts for testing
      const testService = new EnhancedWebSocketService('ws://localhost:8000/ws');
      (testService as any).maxReconnectAttempts = 2;
      
      await testService.connect();
      
      // Simulate multiple connection failures
      for (let i = 0; i < 3; i++) {
        const mockWs = (testService as any).ws as MockWebSocket;
        mockWs.close(1006, 'Connection lost');
        vi.advanceTimersByTime(5000);
      }
      
      // Should stop trying after max attempts
      expect((testService as any).reconnectAttempts).toBe(2);
      
      testService.disconnect();
      vi.useRealTimers();
    });
  });

  describe('Message Queue Processing', () => {
    it('should process queued messages when reconnected', async () => {
      // Start disconnected
      wsService.disconnect();
      
      // Queue some messages
      wsService.send('test1', { message: 'first' });
      wsService.send('test2', { message: 'second' });
      
      expect(wsService.getMessageQueueSize()).toBe(2);
      
      // Connect and wait for queue processing
      await wsService.connect();
      
      // Wait for queue to be processed
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(wsService.getMessageQueueSize()).toBe(0);
    });

    it('should prioritize messages in queue', async () => {
      wsService.disconnect();
      
      // Add messages with different priorities
      wsService.send('low', { message: 'low' }, 'default', { priority: 'low' });
      wsService.send('high', { message: 'high' }, 'default', { priority: 'high' });
      wsService.send('normal', { message: 'normal' }, 'default', { priority: 'normal' });
      wsService.send('critical', { message: 'critical' }, 'default', { priority: 'critical' });
      
      expect(wsService.getMessageQueueSize()).toBe(4);
      
      // Messages should be ordered by priority in the queue
      const queue = (wsService as any).messageQueue;
      expect(queue[0].message.type).toBe('critical');
      expect(queue[1].message.type).toBe('high');
      expect(queue[2].message.type).toBe('normal');
      expect(queue[3].message.type).toBe('low');
    });
  });

  describe('Duplicate Message Handling', () => {
    it('should ignore duplicate messages', async () => {
      await wsService.connect();
      
      const callback = vi.fn();
      wsService.subscribe('test', callback);
      
      const messageData = {
        type: 'test',
        channel: 'default',
        data: { message: 'duplicate test' },
        timestamp: new Date().toISOString(),
        id: 'msg-duplicate',
      };
      
      const mockWs = (wsService as any).ws as MockWebSocket;
      
      // Send same message twice
      mockWs.simulateMessage(messageData);
      mockWs.simulateMessage(messageData);
      
      // Callback should only be called once
      expect(callback).toHaveBeenCalledTimes(1);
    });
  });

  describe('Cleanup', () => {
    it('should clear all subscriptions', async () => {
      await wsService.connect();
      
      wsService.subscribe('test1', vi.fn());
      wsService.subscribe('test2', vi.fn());
      
      expect(wsService.getSubscriptionCount()).toBe(2);
      
      wsService.clearSubscriptions();
      
      expect(wsService.getSubscriptionCount()).toBe(0);
    });

    it('should clean up on disconnect', async () => {
      await wsService.connect();
      
      wsService.send('test', { message: 'queued' });
      wsService.subscribe('test', vi.fn());
      
      wsService.disconnect();
      
      expect(wsService.getMessageQueueSize()).toBe(0);
      expect(wsService.isConnected()).toBe(false);
    });
  });
});