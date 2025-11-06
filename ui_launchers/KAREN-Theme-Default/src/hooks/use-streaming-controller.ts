'use client';

import { useCallback, useRef, useState, useEffect } from 'react';
import { getTelemetryService } from '@/lib/telemetry';
import { safeWarn } from '@/lib/safe-console';

export interface StreamOptions {
  url: string;
  method?: 'GET' | 'POST';
  headers?: Record<string, string>;
  body?: any;
  signal?: AbortSignal;
  onToken?: (token: string) => void;
  onComplete?: (fullText: string) => void;
  onError?: (error: Error) => void;
  maxRetries?: number;
  retryDelay?: number;
  backpressureThreshold?: number; // Max buffer size before applying backpressure
  correlationId?: string;
  streamId?: string;
}

export interface StreamingController {
  start: (options: StreamOptions) => Promise<void>;
  append: (token: string) => void;
  flush: () => void;
  abort: () => void;
  retry: () => Promise<void>;
  isStreaming: boolean;
  isAborted: boolean;
  error: Error | null;
  buffer: string;
  retryCount: number;
  bufferSize: number;
  isBackpressureActive: boolean;
  streamMetrics: StreamMetrics;
}

export interface StreamMetrics {
  startTime: number;
  firstTokenTime?: number;
  endTime?: number;
  tokenCount: number;
  bytesReceived: number;
  averageLatency: number;
  throughput: number; // tokens per second
}

export interface StreamState {
  isStreaming: boolean;
  isAborted: boolean;
  error: Error | null;
  buffer: string;
  retryCount: number;
  fullText: string;
  bufferSize: number;
  isBackpressureActive: boolean;
  metrics: StreamMetrics;
}

const INITIAL_METRICS: StreamMetrics = {
  startTime: 0,
  tokenCount: 0,
  bytesReceived: 0,
  averageLatency: 0,
  throughput: 0,
};

const INITIAL_STATE: StreamState = {
  isStreaming: false,
  isAborted: false,
  error: null,
  buffer: '',
  retryCount: 0,
  fullText: '',
  bufferSize: 0,
  isBackpressureActive: false,
  metrics: INITIAL_METRICS,
};

const DEFAULT_BACKPRESSURE_THRESHOLD = 50000; // 50KB
const BACKPRESSURE_DELAY = 10; // ms

export const useStreamingController = (): StreamingController => {
  const [state, setState] = useState<StreamState>(INITIAL_STATE);
  const abortControllerRef = useRef<AbortController | null>(null);
  const optionsRef = useRef<StreamOptions | null>(null);
  const backpressureTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const telemetryService = getTelemetryService();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (backpressureTimeoutRef.current) {
        clearTimeout(backpressureTimeoutRef.current);
      }
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current);
      }
    };
  }, []);

  // Apply backpressure when buffer gets too large
  const applyBackpressure = useCallback(async (threshold: number) => {
    if (state.bufferSize > threshold && !state.isBackpressureActive) {
      setState(prev => ({ ...prev, isBackpressureActive: true }));
      
      telemetryService.track('stream.backpressure.activated', {
        bufferSize: state.bufferSize,
        threshold,
        correlationId: optionsRef.current?.correlationId,
        streamId: optionsRef.current?.streamId,
      }, optionsRef.current?.correlationId);

      return new Promise<void>(resolve => {
        backpressureTimeoutRef.current = setTimeout(() => {
          setState(prev => ({ ...prev, isBackpressureActive: false }));
          resolve();
        }, BACKPRESSURE_DELAY);

    }
  }, [state.bufferSize, state.isBackpressureActive, telemetryService]);

  // Update metrics periodically during streaming
  const updateMetrics = useCallback(() => {
    setState(prev => {
      const now = performance.now();
      const duration = now - prev.metrics.startTime;
      const throughput = duration > 0 ? (prev.metrics.tokenCount / duration) * 1000 : 0;
      
      return {
        ...prev,
        metrics: {
          ...prev.metrics,
          throughput,
          averageLatency: prev.metrics.firstTokenTime 
            ? prev.metrics.firstTokenTime - prev.metrics.startTime 
            : 0,
        },
      };

  }, []);

  // Start streaming
  const start = useCallback(async (options: StreamOptions) => {
    // Abort any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear any existing timeouts
    if (backpressureTimeoutRef.current) {
      clearTimeout(backpressureTimeoutRef.current);
    }
    if (metricsIntervalRef.current) {
      clearInterval(metricsIntervalRef.current);
    }

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;
    optionsRef.current = options;

    const startTime = performance.now();
    const backpressureThreshold = options.backpressureThreshold || DEFAULT_BACKPRESSURE_THRESHOLD;

    // Reset state
    setState(prev => ({
      ...INITIAL_STATE,
      isStreaming: true,
      retryCount: prev.retryCount,
      metrics: {
        ...INITIAL_METRICS,
        startTime,
      },
    }));

    // Start metrics tracking
    metricsIntervalRef.current = setInterval(updateMetrics, 1000);

    let firstTokenReceived = false;

    try {
      telemetryService.track('stream.started', {
        url: options.url,
        method: options.method || 'POST',
        retryCount: state.retryCount,
        backpressureThreshold,
        correlationId: options.correlationId,
        streamId: options.streamId,
      }, options.correlationId);

      // Make the request with timeout
      const timeoutController = new AbortController();
      const timeoutId = setTimeout(() => timeoutController.abort(), 30000); // 30s timeout

      const combinedSignal = AbortSignal.any ? 
        AbortSignal.any([controller.signal, timeoutController.signal]) :
        controller.signal;

      const response = await fetch(options.url, {
        method: options.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: combinedSignal

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      if (!response.body) {
        throw new Error('No response body available for streaming');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullText = '';
      let bytesReceived = 0;

      while (true) {
        // Check for abort before reading
        if (controller.signal.aborted) {
          break;
        }

        // Apply backpressure if needed
        await applyBackpressure(backpressureThreshold);

        const { value, done } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        bytesReceived += value.byteLength;
        
        // Update bytes received metric
        setState(prev => ({
          ...prev,
          metrics: {
            ...prev.metrics,
            bytesReceived,
          },
        }));

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          // Handle Server-Sent Events format
          let data = trimmed;
          if (trimmed.startsWith('data: ')) {
            data = trimmed.slice(6);
            if (data === '[DONE]') continue;
          }

          let token = '';
          try {
            // Try to parse as JSON
            const parsed = JSON.parse(data);
            token = parsed.token || parsed.text || parsed.content || parsed.delta?.content || '';
          } catch {
            // If not JSON, treat as plain text token
            if (data && !data.startsWith('{')) {
              token = data;
            }
          }

          if (token) {
            const now = performance.now();
            
            if (!firstTokenReceived) {
              firstTokenReceived = true;
              setState(prev => ({
                ...prev,
                metrics: {
                  ...prev.metrics,
                  firstTokenTime: now,
                },
              }));
              
              telemetryService.track('stream.first_token', {
                latency: now - startTime,
                correlationId: options.correlationId,
                streamId: options.streamId,
              }, options.correlationId);
            }

            fullText += token;
            const newBufferSize = fullText.length;
            
            setState(prev => ({
              ...prev,
              buffer: prev.buffer + token,
              fullText,
              bufferSize: newBufferSize,
              metrics: {
                ...prev.metrics,
                tokenCount: prev.metrics.tokenCount + 1,
              },
            }));

            try {
              options.onToken?.(token);
            } catch (tokenError) {
              safeWarn('Error in onToken callback:', tokenError);
              // Don't break streaming for callback errors
            }
          }
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        const trimmed = buffer.trim();
        let data = trimmed;
        if (trimmed.startsWith('data: ')) {
          data = trimmed.slice(6);
        }

        let token = '';
        try {
          const parsed = JSON.parse(data);
          token = parsed.token || parsed.text || parsed.content || parsed.delta?.content || '';
        } catch {
          if (data && !data.startsWith('{')) {
            token = data;
          }
        }

        if (token) {
          fullText += token;
          setState(prev => ({
            ...prev,
            buffer: prev.buffer + token,
            fullText,
            bufferSize: fullText.length,
            metrics: {
              ...prev.metrics,
              tokenCount: prev.metrics.tokenCount + 1,
            },
          }));
          
          try {
            options.onToken?.(token);
          } catch (tokenError) {
            safeWarn('Error in onToken callback:', tokenError);
          }
        }
      }

      // Stream completed successfully
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      setState(prev => ({
        ...prev,
        isStreaming: false,
        fullText,
        metrics: {
          ...prev.metrics,
          endTime,
        },
      }));

      // Clear intervals
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current);
      }

      telemetryService.track('stream.completed', {
        duration,
        tokenCount: state.metrics.tokenCount,
        bytesReceived,
        throughput: duration > 0 ? (state.metrics.tokenCount / duration) * 1000 : 0,
        retryCount: state.retryCount,
        correlationId: options.correlationId,
        streamId: options.streamId,
      }, options.correlationId);

      try {
        options.onComplete?.(fullText);
      } catch (completeError) {
        safeWarn('Error in onComplete callback:', completeError);
      }

    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown streaming error');
      const duration = performance.now() - startTime;
      
      // Clear intervals on error
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current);
      }
      
      if (err.name === 'AbortError') {
        setState(prev => ({
          ...prev,
          isStreaming: false,
          isAborted: true,
          metrics: {
            ...prev.metrics,
            endTime: performance.now(),
          },
        }));
        
        telemetryService.track('stream.aborted', {
          duration,
          tokenCount: state.metrics.tokenCount,
          retryCount: state.retryCount,
          correlationId: options.correlationId,
          streamId: options.streamId,
        }, options.correlationId);
        
        return; // Don't treat abort as an error
      }

      // Categorize error types for better handling
      const errorType = err.name === 'TypeError' && err.message.includes('fetch') 
        ? 'network_error'
        : err.message.includes('timeout')
        ? 'timeout_error'
        : err.message.includes('HTTP')
        ? 'http_error'
        : 'unknown_error';

      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: err,
        metrics: {
          ...prev.metrics,
          endTime: performance.now(),
        },
      }));

      telemetryService.track('stream.error', {
        error: err.message,
        errorType,
        errorStack: err.stack,
        duration,
        tokenCount: state.metrics.tokenCount,
        retryCount: state.retryCount,
        correlationId: options.correlationId,
        streamId: options.streamId,
      }, options.correlationId);

      try {
        options.onError?.(err);
      } catch (errorCallbackError) {
        safeWarn('Error in onError callback:', errorCallbackError);
      }
    }
  }, [state.retryCount, state.metrics.tokenCount, applyBackpressure, updateMetrics, telemetryService]);

  // Append token manually (for non-streaming scenarios)
  const append = useCallback((token: string) => {
    setState(prev => ({
      ...prev,
      buffer: prev.buffer + token,
      fullText: prev.fullText + token,
      bufferSize: prev.fullText.length + token.length,
      metrics: {
        ...prev.metrics,
        tokenCount: prev.metrics.tokenCount + 1,
      },
    }));
  }, []);

  // Flush buffer (clear accumulated tokens)
  const flush = useCallback(() => {
    setState(prev => ({
      ...prev,
      buffer: '',
      bufferSize: prev.fullText.length, // Keep fullText size as buffer size
    }));
    
    telemetryService.track('stream.buffer_flushed', {
      correlationId: optionsRef.current?.correlationId,
      streamId: optionsRef.current?.streamId,
    }, optionsRef.current?.correlationId);
  }, [telemetryService]);

  // Abort current stream
  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Clear timeouts and intervals
    if (backpressureTimeoutRef.current) {
      clearTimeout(backpressureTimeoutRef.current);
    }
    if (metricsIntervalRef.current) {
      clearInterval(metricsIntervalRef.current);
    }
    
    setState(prev => ({
      ...prev,
      isStreaming: false,
      isAborted: true,
      isBackpressureActive: false,
      metrics: {
        ...prev.metrics,
        endTime: performance.now(),
      },
    }));

    telemetryService.track('stream.abort_requested', {
      retryCount: state.retryCount,
      correlationId: optionsRef.current?.correlationId,
      streamId: optionsRef.current?.streamId,
    }, optionsRef.current?.correlationId);
  }, [state.retryCount, telemetryService]);

  // Retry with exponential backoff and jitter
  const retry = useCallback(async () => {
    if (!optionsRef.current) {
      const error = new Error('No previous stream options available for retry');
      setState(prev => ({ ...prev, error }));
      throw error;
    }

    const maxRetries = optionsRef.current.maxRetries || 3;
    const baseDelay = optionsRef.current.retryDelay || 1000;

    if (state.retryCount >= maxRetries) {
      const error = new Error(`Max retries (${maxRetries}) exceeded`);
      setState(prev => ({ ...prev, error }));
      
      telemetryService.track('stream.retry_max_exceeded', {
        maxRetries,
        correlationId: optionsRef.current?.correlationId,
        streamId: optionsRef.current?.streamId,
      }, optionsRef.current?.correlationId);
      
      throw error;
    }

    // Calculate delay with exponential backoff and jitter
    const exponentialDelay = baseDelay * Math.pow(2, state.retryCount);
    const jitter = Math.random() * 1000; // Add up to 1s jitter
    const delay = exponentialDelay + jitter;
    
    telemetryService.track('stream.retry_scheduled', {
      retryCount: state.retryCount + 1,
      delay,
      exponentialDelay,
      jitter,
      correlationId: optionsRef.current?.correlationId,
      streamId: optionsRef.current?.streamId,
    }, optionsRef.current?.correlationId);

    await new Promise(resolve => setTimeout(resolve, delay));

    setState(prev => ({
      ...prev,
      retryCount: prev.retryCount + 1,
      error: null,
      isAborted: false,
      isBackpressureActive: false,
      // Reset metrics but keep retry count
      metrics: {
        ...INITIAL_METRICS,
        startTime: performance.now(),
      },
    }));

    await start(optionsRef.current);
  }, [state.retryCount, start, telemetryService]);

  return {
    start,
    append,
    flush,
    abort,
    retry,
    isStreaming: state.isStreaming,
    isAborted: state.isAborted,
    error: state.error,
    buffer: state.buffer,
    retryCount: state.retryCount,
    bufferSize: state.bufferSize,
    isBackpressureActive: state.isBackpressureActive,
    streamMetrics: state.metrics,
  };
};

export default useStreamingController;