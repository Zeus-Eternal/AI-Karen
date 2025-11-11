"use client";

import { useCallback, useEffect } from "react";
import { getTelemetryService, type Span } from "@/lib/telemetry";

export interface TelemetryEvent {
  event: string;
  payload: unknown;
  correlationId?: string;
  timestamp?: string;
}

export interface TelemetryHook {
  track: (event: string, payload: unknown, correlationId?: string) => void;
  startSpan: (name: string) => Span;
  setCorrelationId: (id: string) => void;
  flush: () => Promise<void>;
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
      
      telemetryService.track(event, validPayload, correlationId);
    },
    [telemetryService]
  );

  const startSpan = useCallback(
    (name: string): Span => {
      return telemetryService.startSpan(name);
    },
    [telemetryService]
  );

  const setCorrelationId = useCallback(
    (id: string) => {
      telemetryService.setCorrelationId(id);
    },
    [telemetryService]
  );

  const flush = useCallback(async () => {
    return telemetryService.flush();
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
