import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import UserAnalytics, { 
  getUserAnalytics, 
  trackEvent, 
  trackMessageSend, 
  trackMessageStreamStart, 
  trackMessageStreamComplete, 
  trackMessageStreamAbort, 
  trackFeatureUsage, 
  trackPageView, 
  startFunnel, 
  completeFunnelStep, 
  abandonFunnel 
} from '../userAnalytics';
import { getTelemetryService } from '../telemetry';
import { getPerformanceMonitor } from '../performanceMonitoring';

// Mock dependencies
vi.mock('../telemetry', () => ({
  getTelemetryService: vi.fn(() => ({
    track: vi.fn(),
    getStats: vi.fn(() => ({ correlationId: 'test-correlation-123' })),
  })),
}));

vi.mock('../performanceMonitoring', () => ({
  getPerformanceMonitor: vi.fn(() => ({
    getMetrics: vi.fn(() => ({
      firstToken: 500,
      streamComplete: 2000,
    })),
  })),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

// Mock fetch
const fetchMock = vi.fn();

// Mock performance
const performanceMock = {
  memory: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000,
  },
};

// Mock navigator
const navigatorMock = {
  userAgent: 'Mozilla/5.0 (Test Browser)',
  onLine: true,
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

Object.defineProperty(global, 'fetch', {
  value: fetchMock,
});

Object.defineProperty(global, 'performance', {
  value: performanceMock,
});

Object.defineProperty(global, 'navigator', {
  value: navigatorMock,
});

// Mock window and document
Object.defineProperty(window, 'location', {
  value: {
    href: 'https://example.com/test',
    pathname: '/test',
  },
  writable: true,
});

Object.defineProperty(window, 'innerWidth', {
  value: 1920,
  writable: true,
});

Object.defineProperty(window, 'innerHeight', {
  value: 1080,
  writable: true,
});

Object.defineProperty(document, 'referrer', {
  value: 'https://google.com',
  writable: true,
});

Object.defineProperty(document, 'title', {
  value: 'Test Page',
  writable: true,
});

Object.defineProperty(document, 'hidden', {
  value: false,
  writable: true,
});

Object.defineProperty(document, 'visibilityState', {
  value: 'visible',
  writable: true,
});

describe('UserAnalytics', () => {
  let userAnalytics: UserAnalytics;
  let mockTelemetryTrack: any;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
    });

    mockTelemetryTrack = vi.fn();
    (getTelemetryService as any).mockReturnValue({
      track: mockTelemetryTrack,
      getStats: vi.fn(() => ({ correlationId: 'test-correlation-123' })),
    });

    userAnalytics = new UserAnalytics({
      enabled: true,
      trackPageViews: false, // Disable for most tests
      flushInterval: 100, // Short interval for testing
      batchSize: 3,
    });
  });

  afterEach(() => {
    userAnalytics.destroy();
  });

  describe('Initialization', () => {
    it('should initialize with default config', () => {
      const analytics = new UserAnalytics();
      const stats = analytics.getStats();
      
      expect(stats.sessionId).toBeTruthy();
      expect(stats.sessionDuration).toBeGreaterThan(0);
      
      analytics.destroy();
    });

    it('should not initialize when disabled', () => {
      const analytics = new UserAnalytics({ enabled: false });
      
      analytics.trackEvent('custom', { test: 'data' });
      
      expect(mockTelemetryTrack).not.toHaveBeenCalled();
      
      analytics.destroy();
    });

    it('should track initial page view when enabled', () => {
      const analytics = new UserAnalytics({ trackPageViews: true });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'page_view',
        }),
        'test-correlation-123'
      );
      
      analytics.destroy();
    });
  });

  describe('Event Tracking', () => {
    it('should track basic events', () => {
      userAnalytics.trackEvent('custom', { testData: 'value' });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'custom',
          data: { testData: 'value' },
          performanceMetrics: expect.objectContaining({
            memoryUsage: 1000000,
            firstTokenTime: 500,
            streamCompleteTime: 2000,
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should include user ID when available', () => {
      localStorageMock.getItem.mockReturnValue('user-123');
      
      userAnalytics.trackEvent('custom', { test: 'data' });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          userId: 'user-123',
        }),
        'test-correlation-123'
      );
    });

    it('should respect sample rate', () => {
      const mathSpy = vi.spyOn(Math, 'random').mockReturnValue(0.8);
      const sampledAnalytics = new UserAnalytics({ sampleRate: 0.5 });
      
      sampledAnalytics.trackEvent('custom', { test: 'data' });
      
      expect(mockTelemetryTrack).not.toHaveBeenCalled();
      
      mathSpy.mockRestore();
      sampledAnalytics.destroy();
    });

    it('should flush when batch size is reached', () => {
      const flushSpy = vi.spyOn(userAnalytics, 'flush');
      
      userAnalytics.trackEvent('event1');
      userAnalytics.trackEvent('event2');
      expect(flushSpy).not.toHaveBeenCalled();
      
      userAnalytics.trackEvent('event3');
      expect(flushSpy).toHaveBeenCalled();
      
      flushSpy.mockRestore();
    });
  });

  describe('Chat-specific Tracking', () => {
    it('should track message send', () => {
      userAnalytics.trackMessageSend({
        messageId: 'msg-123',
        messageLength: 50,
        messageType: 'text',
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'message_send',
          data: expect.objectContaining({
            messageId: 'msg-123',
            messageLength: 50,
            messageType: 'text',
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should track message stream start', () => {
      userAnalytics.trackMessageStreamStart({
        messageId: 'msg-123',
        provider: 'openai',
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'message_stream_start',
          data: expect.objectContaining({
            messageId: 'msg-123',
            provider: 'openai',
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should track message stream complete', () => {
      userAnalytics.trackMessageStreamComplete({
        messageId: 'msg-123',
        tokenCount: 150,
        duration: 2000,
        provider: 'openai',
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'message_stream_complete',
          data: expect.objectContaining({
            messageId: 'msg-123',
            tokenCount: 150,
            duration: 2000,
            provider: 'openai',
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should track message stream abort', () => {
      userAnalytics.trackMessageStreamAbort({
        messageId: 'msg-123',
        reason: 'user_cancelled',
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'message_stream_abort',
          data: expect.objectContaining({
            messageId: 'msg-123',
            reason: 'user_cancelled',
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should track feature usage', () => {
      userAnalytics.trackFeatureUsage('voice_input', { 
        duration: 5000,
        language: 'en-US' 
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'feature_use',
          data: expect.objectContaining({
            featureName: 'voice_input',
            duration: 5000,
            language: 'en-US',
          }),
        }),
        'test-correlation-123'
      );
    });
  });

  describe('Page View Tracking', () => {
    it('should track page views', () => {
      userAnalytics.trackPageView();
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          interactionType: 'page_view',
          data: expect.objectContaining({
            url: 'https://example.com/test',
            pathname: '/test',
            referrer: 'https://google.com',
            title: 'Test Page',
          }),
        }),
        'test-correlation-123'
      );
    });

    it('should track custom page views', () => {
      userAnalytics.trackPageView('https://example.com/custom');
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'user_interaction',
        expect.objectContaining({
          data: expect.objectContaining({
            url: 'https://example.com/custom',
            pathname: '/custom',
          }),
        }),
        'test-correlation-123'
      );
    });
  });

  describe('Conversion Funnel Tracking', () => {
    it('should start funnel', () => {
      userAnalytics.startFunnel('onboarding', ['signup', 'verify', 'complete'], {
        source: 'homepage'
      });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_start',
        {
          funnelName: 'onboarding',
          steps: ['signup', 'verify', 'complete'],
          metadata: { source: 'homepage' },
        }
      );
    });

    it('should complete funnel steps', () => {
      userAnalytics.startFunnel('onboarding', ['signup', 'verify', 'complete']);
      userAnalytics.completeFunnelStep('onboarding', 'signup', { method: 'email' });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_step_complete',
        {
          funnelName: 'onboarding',
          stepName: 'signup',
          stepIndex: 0,
          isComplete: false,
          completedSteps: 1,
          totalSteps: 3,
          stepData: { method: 'email' },
        }
      );
    });

    it('should complete entire funnel', () => {
      userAnalytics.startFunnel('onboarding', ['signup', 'verify']);
      userAnalytics.completeFunnelStep('onboarding', 'signup');
      userAnalytics.completeFunnelStep('onboarding', 'verify');
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_step_complete',
        expect.objectContaining({
          stepName: 'verify',
          isComplete: true,
        })
      );
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_complete',
        expect.objectContaining({
          funnelName: 'onboarding',
          steps: 2,
        })
      );
    });

    it('should abandon funnel', () => {
      userAnalytics.startFunnel('onboarding', ['signup', 'verify', 'complete']);
      userAnalytics.completeFunnelStep('onboarding', 'signup');
      userAnalytics.abandonFunnel('onboarding', 'user_left');
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_abandon',
        {
          funnelName: 'onboarding',
          completedSteps: 1,
          totalSteps: 3,
          lastStep: 'signup',
          reason: 'user_left',
        }
      );
    });

    it('should handle invalid funnel operations', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      userAnalytics.completeFunnelStep('nonexistent', 'step');
      expect(consoleSpy).toHaveBeenCalledWith('Funnel "nonexistent" not found');
      
      userAnalytics.startFunnel('test', ['step1', 'step2']);
      userAnalytics.completeFunnelStep('test', 'invalid_step');
      expect(consoleSpy).toHaveBeenCalledWith('Step "invalid_step" not found in funnel "test"');
      
      consoleSpy.mockRestore();
    });
  });

  describe('User Journey Analysis', () => {
    it('should calculate engagement score', () => {
      // Add some events to increase engagement
      for (let i = 0; i < 10; i++) {
        userAnalytics.trackEvent('click', { element: `button-${i}` });
      }
      
      userAnalytics.trackPageView('/page1');
      userAnalytics.trackPageView('/page2');
      
      const score = userAnalytics.getEngagementScore();
      expect(score).toBeGreaterThan(0);
      expect(score).toBeLessThanOrEqual(100);
    });

    it('should calculate bounce rate', () => {
      // New session should have bounce rate of 1.0 initially
      const bounceRate = userAnalytics.getBounceRate();
      expect(bounceRate).toBe(1.0);
      
      // After page view, should still be 1.0 if short session
      userAnalytics.trackPageView('/page1');
      expect(userAnalytics.getBounceRate()).toBe(1.0);
      
      // After multiple page views, should be 0.0
      userAnalytics.trackPageView('/page2');
      expect(userAnalytics.getBounceRate()).toBe(0.0);
    });

    it('should provide comprehensive stats', () => {
      userAnalytics.trackEvent('click');
      userAnalytics.trackPageView('/test');
      userAnalytics.startFunnel('test', ['step1', 'step2']);
      
      const stats = userAnalytics.getStats();
      
      expect(stats).toEqual({
        eventCount: 2, // click + page_view
        sessionId: expect.any(String),
        sessionDuration: expect.any(Number),
        pageViews: 1,
        activeFunnels: ['test'],
        engagementScore: expect.any(Number),
        bounceRate: expect.any(Number),
      });
    });
  });

  describe('Session Management', () => {
    it('should end session properly', () => {
      userAnalytics.trackEvent('test_event');
      userAnalytics.startFunnel('test', ['step1']);
      
      userAnalytics.endSession();
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'session_end',
        expect.objectContaining({
          sessionId: expect.any(String),
          duration: expect.any(Number),
          eventCount: 1,
          pageViews: 0,
          engagementScore: expect.any(Number),
          bounceRate: expect.any(Number),
          activeFunnels: ['test'],
        })
      );
      
      // Should abandon active funnels
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'funnel_abandon',
        expect.objectContaining({
          funnelName: 'test',
          reason: 'session_end',
        })
      );
    });
  });

  describe('Event Listeners', () => {
    it('should setup event listeners', () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener');
      const windowAddEventListenerSpy = vi.spyOn(window, 'addEventListener');
      
      const analytics = new UserAnalytics({
        trackClicks: true,
        trackScrolling: true,
        trackFocus: true,
        trackResize: true,
      });
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
      expect(windowAddEventListenerSpy).toHaveBeenCalledWith('focus', expect.any(Function));
      expect(windowAddEventListenerSpy).toHaveBeenCalledWith('blur', expect.any(Function));
      expect(windowAddEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));
      
      analytics.destroy();
      addEventListenerSpy.mockRestore();
      windowAddEventListenerSpy.mockRestore();
    });
  });

  describe('Remote Endpoint', () => {
    it('should send events to endpoint', async () => {
      const endpointAnalytics = new UserAnalytics({
        endpoint: 'https://api.example.com/analytics',
        apiKey: 'test-api-key',
        batchSize: 1,
      });
      
      endpointAnalytics.trackEvent('test_event');
      await endpointAnalytics.flush();
      
      expect(fetchMock).toHaveBeenCalledWith(
        'https://api.example.com/analytics',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key',
          }),
          body: expect.stringContaining('test_event'),
        })
      );
      
      endpointAnalytics.destroy();
    });

    it('should handle endpoint errors gracefully', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const endpointAnalytics = new UserAnalytics({
        endpoint: 'https://api.example.com/analytics',
        batchSize: 1,
      });
      
      endpointAnalytics.trackEvent('test_event');
      await endpointAnalytics.flush();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to send analytics events:',
        expect.any(Error)
      );
      
      // Should re-queue events
      expect(endpointAnalytics.getStats().eventCount).toBe(1);
      
      endpointAnalytics.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Cleanup', () => {
    it('should destroy properly', () => {
      userAnalytics.trackEvent('test_event');
      userAnalytics.startFunnel('test', ['step1']);
      
      const flushSpy = vi.spyOn(userAnalytics, 'flush');
      
      userAnalytics.destroy();
      
      expect(flushSpy).toHaveBeenCalled();
      
      const stats = userAnalytics.getStats();
      expect(stats.eventCount).toBe(0);
      expect(stats.activeFunnels).toEqual([]);
      
      flushSpy.mockRestore();
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getUserAnalytics', () => {
      const instance1 = getUserAnalytics();
      const instance2 = getUserAnalytics();
      
      expect(instance1).toBe(instance2);
    });

    it('should use convenience functions', () => {
      const analytics = getUserAnalytics();
      const trackEventSpy = vi.spyOn(analytics, 'trackEvent');
      const trackMessageSendSpy = vi.spyOn(analytics, 'trackMessageSend');
      const trackMessageStreamStartSpy = vi.spyOn(analytics, 'trackMessageStreamStart');
      const trackMessageStreamCompleteSpy = vi.spyOn(analytics, 'trackMessageStreamComplete');
      const trackMessageStreamAbortSpy = vi.spyOn(analytics, 'trackMessageStreamAbort');
      const trackFeatureUsageSpy = vi.spyOn(analytics, 'trackFeatureUsage');
      const trackPageViewSpy = vi.spyOn(analytics, 'trackPageView');
      const startFunnelSpy = vi.spyOn(analytics, 'startFunnel');
      const completeFunnelStepSpy = vi.spyOn(analytics, 'completeFunnelStep');
      const abandonFunnelSpy = vi.spyOn(analytics, 'abandonFunnel');
      
      trackEvent('custom', { test: 'data' });
      trackMessageSend({ messageId: 'msg-1', messageLength: 10 });
      trackMessageStreamStart({ messageId: 'msg-1' });
      trackMessageStreamComplete({ messageId: 'msg-1' });
      trackMessageStreamAbort({ messageId: 'msg-1' });
      trackFeatureUsage('test_feature');
      trackPageView('/test');
      startFunnel('test', ['step1']);
      completeFunnelStep('test', 'step1');
      abandonFunnel('test');
      
      expect(trackEventSpy).toHaveBeenCalledWith('custom', { test: 'data' });
      expect(trackMessageSendSpy).toHaveBeenCalledWith({ messageId: 'msg-1', messageLength: 10 });
      expect(trackMessageStreamStartSpy).toHaveBeenCalledWith({ messageId: 'msg-1' });
      expect(trackMessageStreamCompleteSpy).toHaveBeenCalledWith({ messageId: 'msg-1' });
      expect(trackMessageStreamAbortSpy).toHaveBeenCalledWith({ messageId: 'msg-1' });
      expect(trackFeatureUsageSpy).toHaveBeenCalledWith('test_feature');
      expect(trackPageViewSpy).toHaveBeenCalledWith('/test');
      expect(startFunnelSpy).toHaveBeenCalledWith('test', ['step1']);
      expect(completeFunnelStepSpy).toHaveBeenCalledWith('test', 'step1');
      expect(abandonFunnelSpy).toHaveBeenCalledWith('test');
      
      trackEventSpy.mockRestore();
      trackMessageSendSpy.mockRestore();
      trackMessageStreamStartSpy.mockRestore();
      trackMessageStreamCompleteSpy.mockRestore();
      trackMessageStreamAbortSpy.mockRestore();
      trackFeatureUsageSpy.mockRestore();
      trackPageViewSpy.mockRestore();
      startFunnelSpy.mockRestore();
      completeFunnelStepSpy.mockRestore();
      abandonFunnelSpy.mockRestore();
    });
  });
});