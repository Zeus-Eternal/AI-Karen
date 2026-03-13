"use client";

import React from 'react';
const { useCallback, useEffect } = React;
import { getTelemetryService } from "@/lib/telemetry";

export interface TelemetryEvent {
  event: string;
  payload: unknown;
  correlationId?: string;
  timestamp?: string;
}

export interface TelemetryHook {
  track: (event: string, payload: unknown, correlationId?: string) => void;
  startSpan: (name: string) => string;
  setCorrelationId: (id: string) => void;
  flush: () => void;
}

export const useTelemetry = (): TelemetryHook => {
  const telemetryService = getTelemetryService();

  const track = useCallback(
    (event: string, payload: unknown = {}, correlationId?: string) => {
      // Ensure payload is a valid object or undefined
      const validPayload: Record<string, unknown> | undefined =
        payload && typeof payload === 'object' && !Array.isArray(payload)
          ? payload as Record<string, unknown>
          : payload === undefined || payload === null
          ? undefined
          : { value: payload };
      
      telemetryService.trackEvent({
        type: 'user_action',
        category: 'telemetry',
        action: event,
        metadata: validPayload,
        ...(correlationId && { sessionId: correlationId })
      });
    },
    [telemetryService]
  );

  const startSpan = useCallback(
    (name: string): string => {
      void name;
      return telemetryService.generateId();
    },
    [telemetryService]
  );

  const setCorrelationId = useCallback(
    (id: string) => {
      telemetryService.setSessionId(id);
    },
    [telemetryService]
  );

  const flush = useCallback(() => {
    telemetryService.flush();
  }, [telemetryService]);

  // Track component mount/unmount
  useEffect(() => {
    track("component_mounted", { component: "useTelemetry" });

    return () => {
      track("component_unmounted", { component: "useTelemetry" });
    };
  }, [track]);

  return {
    track,
    startSpan,
    setCorrelationId,
    flush,
  };
};
