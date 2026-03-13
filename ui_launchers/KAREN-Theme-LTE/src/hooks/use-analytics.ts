/**
 * Analytics Hook
 * Provides comprehensive analytics and performance monitoring
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { auditLogger } from '@/lib/audit-logger';

// Extended PerformanceEntry interface to include missing properties
interface ExtendedPerformanceEntry extends PerformanceEntry {
  value?: number;
  hadRecentInput?: boolean;
  getTime?: () => number;
}

// Analytics event types
export interface AnalyticsEvent {
  name: string;
  category: 'user' | 'system' | 'performance' | 'error' | 'feature';
  action: string;
  value?: unknown;
  metadata?: Record<string, unknown>;
  timestamp: Date;
  sessionId?: string;
  userId?: string;
}

// Performance metrics
export interface PerformanceMetrics {
  // Core Web Vitals
  cls: number;
  fid: number;
  lcp: number;
  fcp: number;
  ttfb: number;
  inp: number;
  
  // Custom metrics
  responseTime: number;
  provider: string;
  tokensUsed: number;
  cacheHitRate: number;
  errorRate: number;
  uptime: number;
  memoryUsage: number;
  bundleSize: number;
}

// Analytics state
export interface AnalyticsState {
  events: AnalyticsEvent[];
  metrics: PerformanceMetrics;
  isEnabled: boolean;
  samplingRate: number;
  maxEvents: number;
  batchSize: number;
  flushInterval: number;
  endpoint?: string;
  apiKey?: string;
}

// Hook return type
export interface UseAnalyticsReturn {
  track: (event: Omit<AnalyticsEvent, 'timestamp'>) => void;
  trackPerformance: (metrics: Partial<PerformanceMetrics>) => void;
  trackError: (error: Error, context?: Record<string, unknown>) => void;
  trackFeature: (feature: string, action: string, value?: unknown) => void;
  setUser: (userId: string, properties?: Record<string, unknown>) => void;
  setSession: (sessionId: string, properties?: Record<string, unknown>) => void;
  flush: () => Promise<void>;
  getMetrics: () => PerformanceMetrics;
  getEvents: (category?: AnalyticsEvent['category'], limit?: number) => AnalyticsEvent[];
  enable: () => void;
  disable: () => void;
}

export function useAnalytics(options: Partial<AnalyticsState> = {}): UseAnalyticsReturn {
  const [state, setState] = useState<AnalyticsState>({
    events: [],
    metrics: {
      cls: 0,
      fid: 0,
      lcp: 0,
      fcp: 0,
      ttfb: 0,
      inp: 0,
      responseTime: 0,
      provider: '',
      tokensUsed: 0,
      cacheHitRate: 0,
      errorRate: 0,
      uptime: 0,
      memoryUsage: 0,
      bundleSize: 0,
    },
    isEnabled: true,
    samplingRate: 0.1, // 10% sampling
    maxEvents: 1000,
    batchSize: 10,
    flushInterval: 30000, // 30 seconds
    endpoint: options.endpoint || '/api/analytics',
    apiKey: options.apiKey,
  });
  
  const performanceObserverRef = useRef<PerformanceObserver | null>(null);
  const visibilityChangeRef = useRef<boolean>(false);
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const eventQueueRef = useRef<AnalyticsEvent[]>([]);

  // Flush events to server
  const flushEvents = useCallback(async () => {
    if (!state.isEnabled || eventQueueRef.current.length === 0) return;

    const eventsToSend = eventQueueRef.current.slice(0, state.batchSize);
    eventQueueRef.current = eventQueueRef.current.slice(state.batchSize);

    try {
      const response = await fetch(state.endpoint || '/api/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.apiKey || ''}`,
        },
        body: JSON.stringify({
          events: eventsToSend,
          metrics: state.metrics,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
          referrer: document.referrer,
        }),
      });

      if (response.ok) {
        // Clear sent events from queue
        eventQueueRef.current = [];
      } else {
        console.error('Failed to send analytics events:', response.statusText);
      }
    } catch (error) {
      console.error('Analytics flush error:', error);
    }
  }, [state.isEnabled, state.endpoint, state.apiKey, state.batchSize, state.metrics]);
  
  // Initialize performance observer
  useEffect(() => {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries() as ExtendedPerformanceEntry[]) {
          if (entry.entryType === 'largest-contentful-paint') {
            setState(prev => ({
              ...prev,
              metrics: {
                ...prev.metrics,
                lcp: entry.startTime,
              },
            }));
          } else if (entry.entryType === 'first-contentful-paint') {
            setState(prev => ({
              ...prev,
              metrics: {
                ...prev.metrics,
                fcp: entry.startTime,
              },
            }));
          } else if (entry.entryType === 'first-input-delay') {
            setState(prev => ({
              ...prev,
              metrics: {
                ...prev.metrics,
                fid: entry.startTime,
              },
            }));
          } else if (entry.entryType === 'layout-shift') {
            setState(prev => ({
              ...prev,
              metrics: {
                ...prev.metrics,
                cls: entry.value || 0,
              },
            }));
          }
        }
      });
      
      observer.observe({
        type: 'largest-contentful-paint',
        buffered: true,
      });
      
      observer.observe({
        type: 'first-contentful-paint',
        buffered: true,
      });
      
      observer.observe({
        type: 'first-input-delay',
        buffered: true,
      });
      
      observer.observe({
        type: 'layout-shift',
        buffered: true,
      });
      
      performanceObserverRef.current = observer;
    }
  }, [flushEvents]);
  
  // Track page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        visibilityChangeRef.current = true;
        // Page became hidden, flush events
        flushEvents();
      } else {
        visibilityChangeRef.current = false;
        // Page became visible
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [flushEvents]);
  
  // Track page unload
  useEffect(() => {
    const handleUnload = () => {
      flushEvents();
    };
    
    window.addEventListener('beforeunload', handleUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleUnload);
    };
  }, [flushEvents]);
  
  // Track Core Web Vitals
  useEffect(() => {
    const measureWebVitals = () => {
      // LCP (Largest Contentful Paint)
      new Promise(resolve => {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries() as ExtendedPerformanceEntry[]) {
            if (entry.entryType === 'largest-contentful-paint') {
              resolve(entry.startTime);
              return;
            }
          }
        }).observe({
          type: 'largest-contentful-paint',
          buffered: true,
        });
      }).then((lcp) => {
        if (lcp) {
          setState(prev => ({
            ...prev,
            metrics: {
              ...prev.metrics,
              lcp: typeof lcp === 'number' ? lcp : (lcp as ExtendedPerformanceEntry).getTime?.() || 0,
            },
          }));
        }
      });
      
      // FID (First Input Delay)
      new Promise(resolve => {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries() as ExtendedPerformanceEntry[]) {
            if (entry.entryType === 'first-input-delay') {
              resolve(entry.startTime);
              return;
            }
          }
        }).observe({
          type: 'first-input-delay',
          buffered: true,
        });
      }).then((fid) => {
        if (fid) {
          setState(prev => ({
            ...prev,
            metrics: {
              ...prev.metrics,
              fid: typeof fid === 'number' ? fid : (fid as ExtendedPerformanceEntry).getTime?.() || 0,
            },
          }));
        }
      });
      
      // CLS (Cumulative Layout Shift)
      let clsValue = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries() as ExtendedPerformanceEntry[]) {
          if (entry.entryType === 'layout-shift') {
            if (!entry.hadRecentInput) {
              clsValue += entry.value || 0;
            }
          }
        }
      }).observe({
        type: 'layout-shift',
        buffered: true,
      });
      
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          metrics: {
            ...prev.metrics,
            cls: clsValue,
          },
        }));
      }, 1000);
    };
    
    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      (window as Window & { requestIdleCallback?: (callback: (deadline: IdleDeadline) => void, options?: { timeout?: number }) => void }).requestIdleCallback(
        (deadline: IdleDeadline) => {
          measureWebVitals();
          deadline.timeRemaining();
        },
        { timeout: 5000 }
      );
    }
  }, []);
  
  // Auto-flush timer
  useEffect(() => {
    if (flushTimeoutRef.current) {
      clearTimeout(flushTimeoutRef.current);
    }
    
    flushTimeoutRef.current = setTimeout(() => {
      flushEvents();
    }, state.flushInterval);
    
    return () => {
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current);
        flushTimeoutRef.current = null;
      }
    };
  }, [state.flushInterval, flushEvents]);
  
  // Track event
  const track = useCallback((event: Omit<AnalyticsEvent, 'timestamp'>) => {
    if (!state.isEnabled) return;
    
    const fullEvent: AnalyticsEvent = {
      ...event,
      timestamp: new Date(),
    };
    
    // Apply sampling
    if (Math.random() > state.samplingRate) {
      eventQueueRef.current.push(fullEvent);
      
      // Auto-flush if queue is full
      if (eventQueueRef.current.length >= state.maxEvents) {
        flushEvents();
      }
    }
    
    // Log to audit logger for security events
    if (event.category === 'error') {
      auditLogger.log('ERROR', event.name, {
        action: event.action,
        value: event.value,
        ...event.metadata,
      });
    }
  }, [state.isEnabled, state.samplingRate, state.maxEvents, flushEvents]);
  
  // Track performance metrics
  const trackPerformance = useCallback((metrics: Partial<PerformanceMetrics>) => {
    if (!state.isEnabled) return;
    
    setState(prev => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        ...metrics,
      },
    }));
    
    // Log performance metrics to audit logger
    auditLogger.log('INFO', 'PERFORMANCE_METRICS', {
      responseTime: metrics.responseTime,
      provider: metrics.provider,
      tokensUsed: metrics.tokensUsed,
      cacheHitRate: metrics.cacheHitRate,
      errorRate: metrics.errorRate,
    });
  }, [state.isEnabled]);
  
  // Track error
  const trackError = useCallback((error: Error, context?: Record<string, unknown>) => {
    if (!state.isEnabled) return;
    
    const errorEvent: AnalyticsEvent = {
      name: error.name,
      category: 'error',
      action: 'occurred',
      value: error.message,
      metadata: {
        stack: error.stack,
        context,
        userAgent: navigator.userAgent,
        url: window.location.href,
      },
      timestamp: new Date(),
    };
    
    eventQueueRef.current.push(errorEvent);
    
    // Log error to audit logger
    auditLogger.log('ERROR', 'ERROR_OCCURRED', {
      error: error.message,
      stack: error.stack,
      context,
    });
    
    // Auto-flush for errors
    if (eventQueueRef.current.length >= state.maxEvents) {
      flushEvents();
    }
  }, [state.isEnabled, state.maxEvents, flushEvents]);
  
  // Track feature usage
  const trackFeature = useCallback((feature: string, action: string, value?: unknown) => {
    if (!state.isEnabled) return;
    
    const featureEvent: AnalyticsEvent = {
      name: feature,
      category: 'feature',
      action,
      value,
      timestamp: new Date(),
    };
    
    eventQueueRef.current.push(featureEvent);
    
    auditLogger.log('INFO', 'FEATURE_USED', {
      feature,
      action,
      value,
    });
  }, [state.isEnabled]);
  
  // Set user
  const setUser = useCallback((userId: string, properties?: Record<string, unknown>) => {
    const userEvent: AnalyticsEvent = {
      name: 'user_set',
      category: 'user',
      action: 'identified',
      value: userId,
      metadata: properties,
      timestamp: new Date(),
    };
    
    eventQueueRef.current.push(userEvent);
  }, []);
  
  // Set session
  const setSession = useCallback((sessionId: string, properties?: Record<string, unknown>) => {
    const sessionEvent: AnalyticsEvent = {
      name: 'session_set',
      category: 'user',
      action: 'started',
      value: sessionId,
      metadata: properties,
      timestamp: new Date(),
    };
    
    eventQueueRef.current.push(sessionEvent);
  }, []);
  
  // Get metrics
  const getMetrics = useCallback((): PerformanceMetrics => {
    return state.metrics;
  }, [state.metrics]);
  
  // Get events
  const getEvents = useCallback((category?: AnalyticsEvent['category'], limit?: number) => {
    let events = eventQueueRef.current;
    
    if (category) {
      events = events.filter(event => event.category === category);
    }
    
    if (limit && limit > 0) {
      events = events.slice(-limit);
    }
    
    return events;
  }, []);
  
  // Enable/disable analytics
  const enable = useCallback(() => {
    setState(prev => ({ ...prev, isEnabled: true }));
  }, []);
  
  const disable = useCallback(() => {
    setState(prev => ({ ...prev, isEnabled: false }));
    
    // Flush remaining events when disabling
    flushEvents();
  }, [flushEvents]);
  
  return {
    track,
    trackPerformance,
    trackError,
    trackFeature,
    setUser,
    setSession,
    flush: flushEvents,
    getMetrics,
    getEvents,
    enable,
    disable,
  };
}
