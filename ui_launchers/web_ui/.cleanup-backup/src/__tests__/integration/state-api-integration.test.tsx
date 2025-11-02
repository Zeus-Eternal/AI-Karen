/**
 * State Management and API Integration Tests
 * 
 * Integration tests for state management, API client, and WebSocket service working together.
 * Based on requirements: 12.2, 12.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useAppStore } from '@/store/app-store';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { enhancedWebSocketService, useEnhancedWebSocket } from '@/services/enhanced-websocket-service';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string) {
    // Mock successful send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }
}

global.WebSocket = MockWebSocket as any;

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

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('State Management and API Integration', () => {
  beforeEach(() => {
    // Reset store state
    useAppStore.getState().resetAppState();
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('test-token');
  });

  afterEach(() => {
    enhancedWebSocketService.disconnect();
    vi.clearAllTimers();
  });

  describe('Authentication Flow Integration', () => {
    it('should handle login flow with API and state updates', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light' as const,
          density: 'comfortable' as const,
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      // Mock successful login API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: { user: mockUser, token: 'new-token' },
          status: 'success',
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Perform login
      const response = await enhancedApiClient.post('/auth/login', {
        email: 'test@example.com',
        password: 'password',
      });

      // Update store with login response
      act(() => {
        useAppStore.getState().login(response.data.user);
      });

      // Verify state updates
      const state = useAppStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
      expect(state.authError).toBeNull();
    });

    it('should handle login failure with error state', async () => {
      // Mock failed login API response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          message: 'Invalid credentials',
          status: 'error',
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Attempt login
      try {
        await enhancedApiClient.post('/auth/login', {
          email: 'test@example.com',
          password: 'wrong-password',
        });
      } catch (error: any) {
        // Update store with error
        act(() => {
          useAppStore.getState().setAuthError(error.message);
        });
      }

      // Verify error state
      const state = useAppStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.authError).toBe('Invalid credentials');
    });

    it('should handle logout with state cleanup', async () => {
      // First login
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light' as const,
          density: 'comfortable' as const,
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      act(() => {
        useAppStore.getState().login(mockUser);
      });

      expect(useAppStore.getState().isAuthenticated).toBe(true);

      // Mock logout API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Perform logout
      await enhancedApiClient.post('/auth/logout');

      act(() => {
        useAppStore.getState().logout();
      });

      // Verify state cleanup
      const state = useAppStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.notifications).toEqual([]);
      expect(state.errors).toEqual({});
    });
  });

  describe('Loading State Integration', () => {
    it('should manage loading states during API calls', async () => {
      mockFetch.mockImplementationOnce(() =>
        new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              status: 200,
              json: async () => ({ data: 'test', status: 'success' }),
              headers: new Headers({ 'content-type': 'application/json' }),
            });
          }, 100);
        })
      );

      // Start API call
      const apiPromise = enhancedApiClient.get('/test', { loadingKey: 'test-api' });

      // Check loading state is set
      expect(useAppStore.getState().loadingStates['test-api']).toBe(true);

      // Wait for API call to complete
      await apiPromise;

      // Check loading state is cleared
      expect(useAppStore.getState().loadingStates['test-api']).toBeUndefined();
    });

    it('should clear loading states on API errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      try {
        await enhancedApiClient.get('/test', { loadingKey: 'test-api' });
      } catch (error) {
        // Expected error
      }

      // Check loading state is cleared even on error
      expect(useAppStore.getState().loadingStates['test-api']).toBeUndefined();
    });
  });

  describe('WebSocket and State Integration', () => {
    it('should update state based on WebSocket messages', async () => {
      const wrapper = createWrapper();
      
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      // Connect WebSocket
      await act(async () => {
        await result.current.connect();
      });

      expect(result.current.isConnected).toBe(true);

      // Simulate notification message
      const mockWs = (enhancedWebSocketService as any).ws as MockWebSocket;
      act(() => {
        mockWs.simulateMessage({
          type: 'notification',
          channel: 'default',
          data: {
            type: 'info',
            title: 'Test Notification',
            message: 'This is a test notification',
          },
          timestamp: new Date().toISOString(),
          id: 'msg-1',
        });
      });

      // Check that notification was added to state
      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0].title).toBe('Test Notification');
    });

    it('should handle connection quality updates', async () => {
      const wrapper = createWrapper();
      
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      // Connect WebSocket
      await act(async () => {
        await result.current.connect();
      });

      // Check connection quality is good
      expect(useAppStore.getState().connectionQuality).toBe('good');

      // Simulate connection error
      const mockWs = (enhancedWebSocketService as any).ws as MockWebSocket;
      act(() => {
        if (mockWs.onerror) {
          mockWs.onerror(new Event('error'));
        }
      });

      // Check connection quality is updated
      expect(useAppStore.getState().connectionQuality).toBe('poor');
    });

    it('should send authentication on WebSocket connection', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light' as const,
          density: 'comfortable' as const,
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      // Login user first
      act(() => {
        useAppStore.getState().login(mockUser);
      });

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      // Mock WebSocket send to capture auth message
      const sendSpy = vi.spyOn(enhancedWebSocketService, 'send');

      // Connect WebSocket
      await act(async () => {
        await result.current.connect();
      });

      // Verify auth message was sent
      expect(sendSpy).toHaveBeenCalledWith('auth', {
        token: 'test-token',
        userId: '1',
        timestamp: expect.any(String),
      });
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle API errors with notifications', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          message: 'Internal server error',
          status: 'error',
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      try {
        await enhancedApiClient.get('/test');
      } catch (error) {
        // Error should be handled by interceptors
      }

      // Check that error notification was added
      const state = useAppStore.getState();
      expect(state.notifications.some(n => n.type === 'error')).toBe(true);
    });

    it('should handle network errors with connection quality updates', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      try {
        await enhancedApiClient.get('/test');
      } catch (error) {
        // Error should be handled by interceptors
      }

      // Check that connection quality was updated
      expect(useAppStore.getState().connectionQuality).toBe('offline');
    });

    it('should handle 401 errors with automatic logout', async () => {
      // Login user first
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light' as const,
          density: 'comfortable' as const,
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      act(() => {
        useAppStore.getState().login(mockUser);
      });

      expect(useAppStore.getState().isAuthenticated).toBe(true);

      // Mock 401 response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          message: 'Unauthorized',
          status: 'error',
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      try {
        await enhancedApiClient.get('/protected');
      } catch (error) {
        // Error should be handled by interceptors
      }

      // Check that user was logged out
      expect(useAppStore.getState().isAuthenticated).toBe(false);
      expect(useAppStore.getState().user).toBeNull();
    });
  });

  describe('Feature Flag Integration', () => {
    it('should manage feature flags through API and state', async () => {
      const featureFlags = {
        newDashboard: true,
        betaFeatures: false,
        advancedSettings: true,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: featureFlags,
          status: 'success',
        }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // Fetch feature flags
      const response = await enhancedApiClient.get('/features');

      // Update state with feature flags
      act(() => {
        Object.entries(response.data).forEach(([feature, enabled]) => {
          useAppStore.getState().setFeature(feature, enabled as boolean);
        });
      });

      // Verify feature flags in state
      const state = useAppStore.getState();
      expect(state.features.newDashboard).toBe(true);
      expect(state.features.betaFeatures).toBe(false);
      expect(state.features.advancedSettings).toBe(true);
    });
  });

  describe('Real-time Updates Integration', () => {
    it('should handle real-time system health updates', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      await act(async () => {
        await result.current.connect();
      });

      // Mock system health update
      const mockWs = (enhancedWebSocketService as any).ws as MockWebSocket;
      act(() => {
        mockWs.simulateMessage({
          type: 'system.health',
          channel: 'system',
          data: {
            status: 'degraded',
            services: {
              api: 'healthy',
              database: 'degraded',
              cache: 'healthy',
            },
          },
          timestamp: new Date().toISOString(),
          id: 'health-1',
        });
      });

      // Verify that system queries would be invalidated
      // (This would be tested by checking queryClient.invalidateQueries calls)
    });

    it('should handle real-time chat messages', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      await act(async () => {
        await result.current.connect();
      });

      // Subscribe to chat messages
      const messageCallback = vi.fn();
      act(() => {
        result.current.subscribe('chat.message', messageCallback);
      });

      // Simulate chat message
      const mockWs = (enhancedWebSocketService as any).ws as MockWebSocket;
      act(() => {
        mockWs.simulateMessage({
          type: 'chat.message',
          channel: 'general',
          data: {
            id: 'msg-1',
            text: 'Hello, world!',
            user: 'test-user',
            timestamp: new Date().toISOString(),
          },
          timestamp: new Date().toISOString(),
          id: 'chat-msg-1',
        });
      });

      // Verify callback was called
      expect(messageCallback).toHaveBeenCalledWith({
        id: 'msg-1',
        text: 'Hello, world!',
        user: 'test-user',
        timestamp: expect.any(String),
      });
    });
  });

  describe('Performance and Monitoring Integration', () => {
    it('should track API request metrics', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: 'test', status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await enhancedApiClient.get('/test');

      // Check request logs
      const logs = enhancedApiClient.getRequestLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].method).toBe('GET');
      expect(logs[0].status).toBe(200);
      expect(logs[0].duration).toBeGreaterThan(0);
    });

    it('should track WebSocket connection metrics', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useEnhancedWebSocket(), { wrapper });

      await act(async () => {
        await result.current.connect();
      });

      // Send a message
      act(() => {
        result.current.send('test', { message: 'hello' });
      });

      // Check metrics
      expect(result.current.metrics.messagesSent).toBe(1);
      expect(result.current.metrics.lastConnected).toBeInstanceOf(Date);
    });
  });
});