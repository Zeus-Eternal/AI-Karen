import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ObservabilityManager, { 
  getObservabilityManager, 
  initializeObservability,
  setUser,
  trackChatMessage,
  trackFeature,
  startFunnel,
  completeFunnelStep,
  captureError,
  measurePerformance,
  getHealthStatus,
  flushObservability
} from '../observability';

// Mock all the services
vi.mock('../telemetry', () => ({
  getTelemetryService: vi.fn(() => ({
    track: vi.fn(),
    setUserId: vi.fn(),
    setCorrelationId: vi.fn(),
    flush: vi.fn(),
    destroy: vi.fn(),
    getStats: vi.fn(() => ({
      queueSize: 5,
      correlationId: 'test-correlation',
    })),
  })),
}));

vi.mock('../performanceMonitoring', () => ({
  getPerformanceMonitor: vi.fn(() => ({
    mark: vi.fn(),
    measure: vi.fn(() => 1000),
    markFirstToken: vi.fn(),
    markStreamComplete: vi.fn(),
    getMetrics: vi.fn(() => ({
      memoryUsage: 50 * 1024 * 1024, // 50MB
      firstToken: 500,
      streamComplete: 2000,
    })),
    destroy: vi.fn(),
  })),
}));

vi.mock('../errorTracking', () => ({
  getErrorTracker: vi.fn(() => ({
    captureError: vi.fn(() => 'error-id-123'),
    addBreadcrumb: vi.fn(),
    setUser: vi.fn(),
    getStats: vi.fn(() => ({
      storedReportCount: 5,
      breadcrumbCount: 10,
    })),
    destroy: vi.fn(),
  })),
}));

vi.mock('../userAnalytics', () => ({
  getUserAnalytics: vi.fn(() => ({
    trackEvent: vi.fn(),
    trackMessageSend: vi.fn(),
    trackMessageStreamStart: vi.fn(),
    trackMessageStreamComplete: vi.fn(),
    trackMessageStreamAbort: vi.fn(),
    trackFeatureUsage: vi.fn(),
    startFunnel: vi.fn(),
    completeFunnelStep: vi.fn(),
    flush: vi.fn(),
    destroy: vi.fn(),
    getStats: vi.fn(() => ({
      eventCount: 15,
      sessionId: 'session-123',
      engagementScore: 75,
    })),
  })),
}));

import { getTelemetryService } from '../telemetry';
import { getPerformanceMonitor } from '../performanceMonitoring';
import { getErrorTracker } from '../errorTracking';
import { getUserAnalytics } from '../userAnalytics';

describe('ObservabilityManager', () => {
  let observabilityManager: ObservabilityManager;
  let mockTelemetry: any;
  let mockPerformance: any;
  let mockErrorTracker: any;
  let mockAnalytics: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockTelemetry = {
      track: vi.fn(),
      setUserId: vi.fn(),
      setCorrelationId: vi.fn(),
      flush: vi.fn(),
      destroy: vi.fn(),
      getStats: vi.fn(() => ({
        queueSize: 5,
        correlationId: 'test-correlation',
      })),
    };
    
    mockPerformance = {
      mark: vi.fn(),
      measure: vi.fn(() => 1000),
      markFirstToken: vi.fn(),
      markStreamComplete: vi.fn(),
      getMetrics: vi.fn(() => ({
        memoryUsage: 50 * 1024 * 1024,
        firstToken: 500,
        streamComplete: 2000,
      })),
      destroy: vi.fn(),
    };
    
    mockErrorTracker = {
      captureError: vi.fn(() => 'error-id-123'),
      addBreadcrumb: vi.fn(),
      setUser: vi.fn(),
      getStats: vi.fn(() => ({
        storedReportCount: 5,
        breadcrumbCount: 10,
      })),
      destroy: vi.fn(),
    };
    
    mockAnalytics = {
      trackEvent: vi.fn(),
      trackMessageSend: vi.fn(),
      trackMessageStreamStart: vi.fn(),
      trackMessageStreamComplete: vi.fn(),
      trackMessageStreamAbort: vi.fn(),
      trackFeatureUsage: vi.fn(),
      startFunnel: vi.fn(),
      completeFunnelStep: vi.fn(),
      flush: vi.fn(),
      destroy: vi.fn(),
      getStats: vi.fn(() => ({
        eventCount: 15,
        sessionId: 'session-123',
        engagementScore: 75,
      })),
    };
    
    (getTelemetryService as any).mockReturnValue(mockTelemetry);
    (getPerformanceMonitor as any).mockReturnValue(mockPerformance);
    (getErrorTracker as any).mockReturnValue(mockErrorTracker);
    (getUserAnalytics as any).mockReturnValue(mockAnalytics);
    
    observabilityManager = new ObservabilityManager();
  });

  afterEach(() => {
    observabilityManager.destroy();
  });

  describe('Initialization', () => {
    it('should initialize all services', () => {
      expect(getTelemetryService).toHaveBeenCalled();
      expect(getPerformanceMonitor).toHaveBeenCalled();
      expect(getErrorTracker).toHaveBeenCalled();
      expect(getUserAnalytics).toHaveBeenCalled();
    });

    it('should initialize with custom config', () => {
      const config = {
        telemetry: { enabled: true, debug: true },
        errorTracking: { enabled: true, maxBreadcrumbs: 100 },
        analytics: { enabled: true, trackPageViews: false },
      };
      
      const manager = new ObservabilityManager(config);
      
      expect(getTelemetryService).toHaveBeenCalledWith(config.telemetry);
      expect(getErrorTracker).toHaveBeenCalledWith(config.errorTracking);
      expect(getUserAnalytics).toHaveBeenCalledWith(config.analytics);
      
      manager.destroy();
    });
  });

  describe('User Management', () => {
    it('should set user across all services', () => {
      const userId = 'user-123';
      const userData = { name: 'Test User', role: 'admin' };
      
      observabilityManager.setUser(userId, userData);
      
      expect(mockTelemetry.setUserId).toHaveBeenCalledWith(userId);
      expect(mockErrorTracker.setUser).toHaveBeenCalledWith(userId, userData);
      expect(mockAnalytics.trackEvent).toHaveBeenCalledWith('custom', {
        type: 'user_identified',
        userId,
        userData,
      });
    });
  });

  describe('Correlation ID Management', () => {
    it('should set correlation ID across services', () => {
      const correlationId = 'corr-123';
      
      observabilityManager.setCorrelationId(correlationId);
      
      expect(mockTelemetry.setCorrelationId).toHaveBeenCalledWith(correlationId);
      expect(mockErrorTracker.addBreadcrumb).toHaveBeenCalledWith({
        category: 'custom',
        message: `Correlation ID set: ${correlationId}`,
        level: 'debug',
        data: { correlationId },
      });
    });
  });

  describe('Chat Interaction Tracking', () => {
    it('should track message send', () => {
      const data = { messageId: 'msg-123', messageLength: 50 };
      
      observabilityManager.trackChatInteraction('send', data);
      
      expect(mockPerformance.mark).toHaveBeenCalledWith('message_send_start', { messageId: 'msg-123' });
      expect(mockAnalytics.trackMessageSend).toHaveBeenCalledWith(data);
      expect(mockErrorTracker.addBreadcrumb).toHaveBeenCalledWith({
        category: 'custom',
        message: 'Chat send: msg-123',
        level: 'info',
        data,
      });
    });

    it('should track stream start', () => {
      const data = { messageId: 'msg-123', provider: 'openai' };
      
      observabilityManager.trackChatInteraction('stream_start', data);
      
      expect(mockPerformance.markFirstToken).toHaveBeenCalled();
      expect(mockAnalytics.trackMessageStreamStart).toHaveBeenCalledWith(data);
    });

    it('should track stream complete', () => {
      const data = { messageId: 'msg-123', tokenCount: 150, duration: 2000 };
      
      observabilityManager.trackChatInteraction('stream_complete', data);
      
      expect(mockPerformance.markStreamComplete).toHaveBeenCalled();
      expect(mockPerformance.measure).toHaveBeenCalledWith('message_total_time', 'message_send_start');
      expect(mockAnalytics.trackMessageStreamComplete).toHaveBeenCalledWith(data);
    });

    it('should track stream abort', () => {
      const data = { messageId: 'msg-123', reason: 'user_cancelled' };
      
      observabilityManager.trackChatInteraction('stream_abort', data);
      
      expect(mockAnalytics.trackMessageStreamAbort).toHaveBeenCalledWith(data);
    });
  });

  describe('Feature Usage Tracking', () => {
    it('should track feature usage across services', () => {
      const featureName = 'voice_input';
      const featureData = { duration: 5000, language: 'en-US' };
      
      observabilityManager.trackFeatureUsage(featureName, featureData);
      
      expect(mockAnalytics.trackFeatureUsage).toHaveBeenCalledWith(featureName, featureData);
      expect(mockTelemetry.track).toHaveBeenCalledWith('feature_usage', {
        featureName,
        ...featureData,
      });
      expect(mockErrorTracker.addBreadcrumb).toHaveBeenCalledWith({
        category: 'custom',
        message: `Feature used: ${featureName}`,
        level: 'info',
        data: featureData,
      });
    });
  });

  describe('Conversion Funnel Tracking', () => {
    it('should start conversion funnel', () => {
      const funnelName = 'onboarding';
      const steps = ['signup', 'verify', 'complete'];
      const metadata = { source: 'homepage' };
      
      observabilityManager.startConversionFunnel(funnelName, steps, metadata);
      
      expect(mockAnalytics.startFunnel).toHaveBeenCalledWith(funnelName, steps, metadata);
      expect(mockTelemetry.track).toHaveBeenCalledWith('funnel_started', {
        funnelName,
        steps,
        metadata,
      }, expect.any(String));
      expect(mockErrorTracker.addBreadcrumb).toHaveBeenCalledWith({
        category: 'custom',
        message: `Funnel started: ${funnelName}`,
        level: 'info',
        data: { steps, metadata },
      });
    });

    it('should complete funnel step', () => {
      const funnelName = 'onboarding';
      const stepName = 'signup';
      const stepData = { method: 'email' };
      
      observabilityManager.completeFunnelStep(funnelName, stepName, stepData);
      
      expect(mockAnalytics.completeFunnelStep).toHaveBeenCalledWith(funnelName, stepName, stepData);
      expect(mockPerformance.mark).toHaveBeenCalledWith(`funnel_${funnelName}_${stepName}`, stepData);
    });

    it('should not mark performance for non-key steps', () => {
      const funnelName = 'onboarding';
      const stepName = 'random_step';
      const stepData = { method: 'email' };
      
      observabilityManager.completeFunnelStep(funnelName, stepName, stepData);
      
      expect(mockAnalytics.completeFunnelStep).toHaveBeenCalledWith(funnelName, stepName, stepData);
      expect(mockPerformance.mark).not.toHaveBeenCalledWith(`funnel_${funnelName}_${stepName}`, stepData);
    });
  });

  describe('Error Capture', () => {
    it('should capture error with enhanced context', () => {
      const error = new Error('Test error');
      const context = { componentName: 'TestComponent' };
      
      const errorId = observabilityManager.captureError(error, context);
      
      expect(errorId).toBe('error-id-123');
      expect(mockErrorTracker.captureError).toHaveBeenCalledWith(error, {
        ...context,
        performanceMetrics: {
          memoryUsage: 50 * 1024 * 1024,
          firstToken: 500,
          streamComplete: 2000,
        },
        analyticsStats: {
          eventCount: 15,
          sessionId: 'session-123',
          engagementScore: 75,
        },
      });
    });
  });

  describe('Performance Measurement', () => {
    it('should measure successful operation', async () => {
      const operationName = 'test_operation';
      const operation = vi.fn().mockResolvedValue('success');
      
      const result = await observabilityManager.measurePerformance(operationName, operation);
      
      expect(result).toBe('success');
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${operationName}_start`);
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${operationName}_end`);
      expect(mockPerformance.measure).toHaveBeenCalledWith(`${operationName}_duration`, `${operationName}_start`, `${operationName}_end`);
      expect(mockTelemetry.track).toHaveBeenCalledWith('operation_complete', {
        operationName,
        duration: 1000,
        success: true,
      });
    });

    it('should measure failed operation', async () => {
      const operationName = 'test_operation';
      const error = new Error('Operation failed');
      const operation = vi.fn().mockRejectedValue(error);
      
      await expect(observabilityManager.measurePerformance(operationName, operation)).rejects.toThrow('Operation failed');
      
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${operationName}_start`);
      expect(mockPerformance.mark).toHaveBeenCalledWith(`${operationName}_end`);
      expect(mockTelemetry.track).toHaveBeenCalledWith('operation_complete', {
        operationName,
        duration: 1000,
        success: false,
        error: 'Operation failed',
      });
      expect(mockErrorTracker.captureError).toHaveBeenCalledWith(error, {
        operationName,
        duration: 1000,
        componentName: 'PerformanceMeasurement',
        performanceMetrics: expect.any(Object),
        analyticsStats: expect.any(Object),
      });
    });

    it('should handle synchronous operations', async () => {
      const operationName = 'sync_operation';
      const operation = vi.fn().mockReturnValue('sync_result');
      
      const result = await observabilityManager.measurePerformance(operationName, operation);
      
      expect(result).toBe('sync_result');
      expect(mockTelemetry.track).toHaveBeenCalledWith('operation_complete', {
        operationName,
        duration: 1000,
        success: true,
      });
    });
  });

  describe('Health Status', () => {
    it('should return healthy status', () => {
      const health = observabilityManager.getHealthStatus();
      
      expect(health).toEqual({
        telemetry: { queueSize: 5, correlationId: 'test-correlation' },
        performance: {
          memoryUsage: 50 * 1024 * 1024,
          firstToken: 500,
          streamComplete: 2000,
        },
        errorTracking: { storedReportCount: 5, breadcrumbCount: 10 },
        analytics: { eventCount: 15, sessionId: 'session-123', engagementScore: 75 },
        overall: 'healthy',
      });
    });

    it('should return degraded status for high error count', () => {
      mockErrorTracker.getStats.mockReturnValue({ storedReportCount: 15, breadcrumbCount: 10 });
      
      const health = observabilityManager.getHealthStatus();
      
      expect(health.overall).toBe('degraded');
    });

    it('should return degraded status for high memory usage', () => {
      mockPerformance.getMetrics.mockReturnValue({
        memoryUsage: 150 * 1024 * 1024, // 150MB
        firstToken: 500,
        streamComplete: 2000,
      });
      
      const health = observabilityManager.getHealthStatus();
      
      expect(health.overall).toBe('degraded');
    });

    it('should return unhealthy status for large telemetry queue', () => {
      mockTelemetry.getStats.mockReturnValue({ queueSize: 150, correlationId: 'test-correlation' });
      
      const health = observabilityManager.getHealthStatus();
      
      expect(health.overall).toBe('unhealthy');
    });
  });

  describe('Flush and Cleanup', () => {
    it('should flush all services', async () => {
      await observabilityManager.flush();
      
      expect(mockTelemetry.flush).toHaveBeenCalled();
      expect(mockAnalytics.flush).toHaveBeenCalled();
    });

    it('should destroy all services', () => {
      observabilityManager.destroy();
      
      expect(mockTelemetry.destroy).toHaveBeenCalled();
      expect(mockPerformance.destroy).toHaveBeenCalled();
      expect(mockErrorTracker.destroy).toHaveBeenCalled();
      expect(mockAnalytics.destroy).toHaveBeenCalled();
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getObservabilityManager', () => {
      const instance1 = getObservabilityManager();
      const instance2 = getObservabilityManager();
      
      expect(instance1).toBe(instance2);
    });

    it('should use convenience functions', async () => {
      const manager = getObservabilityManager();
      const setUserSpy = vi.spyOn(manager, 'setUser');
      const trackChatInteractionSpy = vi.spyOn(manager, 'trackChatInteraction');
      const trackFeatureUsageSpy = vi.spyOn(manager, 'trackFeatureUsage');
      const startConversionFunnelSpy = vi.spyOn(manager, 'startConversionFunnel');
      const completeFunnelStepSpy = vi.spyOn(manager, 'completeFunnelStep');
      const captureErrorSpy = vi.spyOn(manager, 'captureError');
      const measurePerformanceSpy = vi.spyOn(manager, 'measurePerformance');
      const getHealthStatusSpy = vi.spyOn(manager, 'getHealthStatus');
      const flushSpy = vi.spyOn(manager, 'flush');
      
      // Test convenience functions
      initializeObservability();
      setUser('user-123');
      trackChatMessage('send', { messageId: 'msg-1' });
      trackFeature('test_feature');
      startFunnel('test', ['step1']);
      completeFunnelStep('test', 'step1');
      captureError(new Error('test'));
      await measurePerformance('test_op', () => 'result');
      getHealthStatus();
      await flushObservability();
      
      expect(setUserSpy).toHaveBeenCalledWith('user-123');
      expect(trackChatInteractionSpy).toHaveBeenCalledWith('send', { messageId: 'msg-1' });
      expect(trackFeatureUsageSpy).toHaveBeenCalledWith('test_feature');
      expect(startConversionFunnelSpy).toHaveBeenCalledWith('test', ['step1']);
      expect(completeFunnelStepSpy).toHaveBeenCalledWith('test', 'step1');
      expect(captureErrorSpy).toHaveBeenCalledWith(expect.any(Error));
      expect(measurePerformanceSpy).toHaveBeenCalledWith('test_op', expect.any(Function));
      expect(getHealthStatusSpy).toHaveBeenCalled();
      expect(flushSpy).toHaveBeenCalled();
      
      setUserSpy.mockRestore();
      trackChatInteractionSpy.mockRestore();
      trackFeatureUsageSpy.mockRestore();
      startConversionFunnelSpy.mockRestore();
      completeFunnelStepSpy.mockRestore();
      captureErrorSpy.mockRestore();
      measurePerformanceSpy.mockRestore();
      getHealthStatusSpy.mockRestore();
      flushSpy.mockRestore();
    });
  });
});