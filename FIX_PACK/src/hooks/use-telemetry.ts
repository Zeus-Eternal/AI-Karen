'use client';

import { useCallback } from 'react';

export interface TelemetryEvent {
  event: string;
  payload: any;
  correlationId?: string;
  timestamp?: string;
}

export interface TelemetryHook {
  track: (event: string, payload: any, correlationId?: string) => void;
  startSpan: (name: string) => { end: () => void };
  setCorrelationId: (id: string) => void;
  flush: () => Promise<void>;
}

export const useTelemetry = (): TelemetryHook => {
  const track = useCallback((event: string, payload: any, correlationId?: string) => {
    // In a real implementation, this would send to analytics service
    if (process.env.NODE_ENV === 'development') {
      console.log('Telemetry:', { event, payload, correlationId });
    }
  }, []);

  const startSpan = useCallback((name: string) => {
    const startTime = performance.now();
    
    return {
      end: () => {
        const duration = performance.now() - startTime;
        track('span_completed', { name, duration });
      }
    };
  }, [track]);

  const setCorrelationId = useCallback((id: string) => {
    // Store correlation ID for subsequent events
    if (typeof window !== 'undefined') {
      (window as any).__correlationId = id;
    }
  }, []);

  const flush = useCallback(async () => {
    // In a real implementation, this would flush pending events
    return Promise.resolve();
  }, []);

  return {
    track,
    startSpan,
    setCorrelationId,
    flush
  };
};