import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useStreamingController } from '../use-streaming-controller';
import { telemetryService } from '../../lib/telemetry';

// Mock telemetry service
vi.mock('../../lib/telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock ReadableStream
class MockReadableStream {
  private chunks: Uint8Array[];
  private index = 0;

  constructor(chunks: string[]) {
    this.chunks = chunks.map(chunk => new TextEncoder().encode(chunk));
  }

  getReader() {
    return {
      read: async () => {
        if (this.index >= this.chunks.length) {
          return { done: true, value: undefined };
        }
        const value = this.chunks[this.index++];
        return { done: false, value };
      },
    };
  }
}

describe('useStreamingController', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useStreamingController());

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.isAborted).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.buffer).toBe('');
    expect(result.current.retryCount).toBe(0);
    expect(result.current.bufferSize).toBe(0);
    expect(result.current.isBackpressureActive).toBe(false);
    expect(result.current.streamMetrics.tokenCount).toBe(0);
  });

  it('starts streaming successfully', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['data: {"token": "Hello"}\n', 'data: {"token": " World"}\n']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const onToken = vi.fn();
    const onComplete = vi.fn();

    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onToken,
        onComplete,
        correlationId: 'test-correlation',
        streamId: 'test-stream',
      });
    });

    expect(mockFetch).toHaveBeenCalledWith('http://test.com/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: undefined,
      signal: expect.any(AbortSignal),
    });

    expect(onToken).toHaveBeenCalledWith('Hello');
    expect(onToken).toHaveBeenCalledWith(' World');
    expect(onComplete).toHaveBeenCalledWith('Hello World');
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.buffer).toBe('Hello World');
  });

  it('tracks telemetry events during streaming', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['data: {"token": "test"}\n']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        correlationId: 'test-correlation',
        streamId: 'test-stream',
      });
    });

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.started',
      expect.objectContaining({
        url: 'http://test.com/stream',
        correlationId: 'test-correlation',
        streamId: 'test-stream',
      }),
      'test-correlation'
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.first_token',
      expect.objectContaining({
        correlationId: 'test-correlation',
        streamId: 'test-stream',
      }),
      'test-correlation'
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.completed',
      expect.objectContaining({
        correlationId: 'test-correlation',
        streamId: 'test-stream',
      }),
      'test-correlation'
    );
  });

  it('handles HTTP errors correctly', async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: () => Promise.resolve('Server error details'),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const onError = vi.fn();
    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onError,
      });
    });

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining('HTTP 500'),
      })
    );
    expect(result.current.error).toBeTruthy();
    expect(result.current.isStreaming).toBe(false);
  });

  it('handles network errors correctly', async () => {
    mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

    const onError = vi.fn();
    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onError,
      });
    });

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Failed to fetch',
      })
    );

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.error',
      expect.objectContaining({
        errorType: 'network_error',
      }),
      undefined
    );
  });

  it('aborts streaming correctly', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['data: {"token": "test"}\n']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useStreamingController());

    act(() => {
      result.current.start({
        url: 'http://test.com/stream',
      });
    });

    act(() => {
      result.current.abort();
    });

    expect(result.current.isAborted).toBe(true);
    expect(result.current.isStreaming).toBe(false);
    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.abort_requested',
      expect.any(Object),
      undefined
    );
  });

  it('retries with exponential backoff', async () => {
    mockFetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        body: new MockReadableStream(['data: {"token": "success"}\n']),
      });

    const { result } = renderHook(() => useStreamingController());

    // First attempt fails
    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        maxRetries: 3,
        retryDelay: 1000,
      });
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.retryCount).toBe(0);

    // Retry
    await act(async () => {
      await result.current.retry();
      vi.advanceTimersByTime(2000); // Wait for retry delay
    });

    expect(result.current.retryCount).toBe(1);
    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.retry_scheduled',
      expect.objectContaining({
        retryCount: 1,
        delay: expect.any(Number),
      }),
      undefined
    );
  });

  it('fails after max retries', async () => {
    const { result } = renderHook(() => useStreamingController());

    // Simulate reaching max retries
    act(() => {
      result.current.start({
        url: 'http://test.com/stream',
        maxRetries: 2,
      });
    });

    // Manually set retry count to max
    for (let i = 0; i < 3; i++) {
      try {
        await act(async () => {
          await result.current.retry();
        });
      } catch (error) {
        // Expected to throw on max retries
      }
    }

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.retry_max_exceeded',
      expect.objectContaining({
        maxRetries: 2,
      }),
      undefined
    );
  });

  it('applies backpressure when buffer is large', async () => {
    const largeToken = 'x'.repeat(60000); // Larger than default threshold
    const mockResponse = {
      ok: true,
      body: new MockReadableStream([`data: {"token": "${largeToken}"}\n`]),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        backpressureThreshold: 50000,
      });
      vi.advanceTimersByTime(100); // Allow backpressure to activate
    });

    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.backpressure.activated',
      expect.objectContaining({
        threshold: 50000,
      }),
      undefined
    );
  });

  it('appends tokens manually', () => {
    const { result } = renderHook(() => useStreamingController());

    act(() => {
      result.current.append('Hello');
    });

    act(() => {
      result.current.append(' World');
    });

    expect(result.current.buffer).toBe('Hello World');
    expect(result.current.bufferSize).toBe(11);
    expect(result.current.streamMetrics.tokenCount).toBe(2);
  });

  it('flushes buffer correctly', () => {
    const { result } = renderHook(() => useStreamingController());

    act(() => {
      result.current.append('Hello World');
    });

    expect(result.current.buffer).toBe('Hello World');

    act(() => {
      result.current.flush();
    });

    expect(result.current.buffer).toBe('');
    expect(telemetryService.track).toHaveBeenCalledWith(
      'stream.buffer_flushed',
      expect.any(Object),
      undefined
    );
  });

  it('handles plain text streaming', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['Hello', ' World', '!']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const onToken = vi.fn();
    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onToken,
      });
    });

    expect(onToken).toHaveBeenCalledWith('Hello');
    expect(onToken).toHaveBeenCalledWith(' World');
    expect(onToken).toHaveBeenCalledWith('!');
    expect(result.current.buffer).toBe('Hello World!');
  });

  it('handles Server-Sent Events format', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream([
        'data: {"token": "Hello"}\n\n',
        'data: {"token": " World"}\n\n',
        'data: [DONE]\n\n',
      ]),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const onToken = vi.fn();
    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onToken,
      });
    });

    expect(onToken).toHaveBeenCalledWith('Hello');
    expect(onToken).toHaveBeenCalledWith(' World');
    expect(onToken).not.toHaveBeenCalledWith('[DONE]');
  });

  it('updates metrics during streaming', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['data: {"token": "test"}\n']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
      });
      vi.advanceTimersByTime(1000); // Advance time for metrics update
    });

    expect(result.current.streamMetrics.tokenCount).toBe(1);
    expect(result.current.streamMetrics.startTime).toBeGreaterThan(0);
    expect(result.current.streamMetrics.firstTokenTime).toBeGreaterThan(0);
    expect(result.current.streamMetrics.bytesReceived).toBeGreaterThan(0);
  });

  it('handles callback errors gracefully', async () => {
    const mockResponse = {
      ok: true,
      body: new MockReadableStream(['data: {"token": "test"}\n']),
    };
    mockFetch.mockResolvedValue(mockResponse);

    const onToken = vi.fn().mockImplementation(() => {
      throw new Error('Callback error');
    });
    const onComplete = vi.fn().mockImplementation(() => {
      throw new Error('Complete callback error');
    });

    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useStreamingController());

    await act(async () => {
      await result.current.start({
        url: 'http://test.com/stream',
        onToken,
        onComplete,
      });
    });

    expect(consoleSpy).toHaveBeenCalledWith('Error in onToken callback:', expect.any(Error));
    expect(consoleSpy).toHaveBeenCalledWith('Error in onComplete callback:', expect.any(Error));
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBe(null); // Callback errors don't break streaming

    consoleSpy.mockRestore();
  });

  it('cleans up resources on unmount', () => {
    const { result, unmount } = renderHook(() => useStreamingController());

    act(() => {
      result.current.start({
        url: 'http://test.com/stream',
      });
    });

    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
    expect(clearIntervalSpy).toHaveBeenCalled();

    clearTimeoutSpy.mockRestore();
    clearIntervalSpy.mockRestore();
  });
});