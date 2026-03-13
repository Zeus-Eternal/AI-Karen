import { useState, useEffect, useRef, useCallback } from 'react';
import { ResponseStream, StreamingResponse, StreamOptions } from '../utils/streaming-utils';

export interface UseStreamResponse {
  response: StreamingResponse | null;
  isLoading: boolean;
  error: Error | null;
  startStream: (text: string, options?: StreamOptions) => void;
  startStreamFromGenerator: (generator: AsyncGenerator<string, void, unknown>) => void;
  startStreamFromFetch: (url: string, options?: RequestInit) => void;
  cancelStream: () => void;
  resetStream: () => void;
}

export function useStreamResponse(): UseStreamResponse {
  const [response, setResponse] = useState<StreamingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const streamRef = useRef<ResponseStream | null>(null);

  const resetStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.removeAllListeners();
    }
    setResponse(null);
    setIsLoading(false);
    setError(null);
    streamRef.current = null;
  }, []);

  const cancelStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.removeAllListeners();
      setIsLoading(false);
    }
  }, []);

  const startStream = useCallback((text: string, options: StreamOptions = {}) => {
    resetStream();
    setIsLoading(true);
    setError(null);

    const streamId = `stream-${Date.now()}`;
    const stream = new ResponseStream(streamId, options);

    streamRef.current = stream;

    stream.on('chunk', (chunk) => {
      setResponse(stream.getResponse());
    });

    stream.on('complete', () => {
      setIsLoading(false);
      setResponse(stream.getResponse());
    });

    stream.on('error', (err: Error) => {
      setError(err);
      setIsLoading(false);
    });

    // Start streaming the text
    stream.streamText(text, options).catch(err => {
      setError(err instanceof Error ? err : new Error(String(err)));
      setIsLoading(false);
    });
  }, [resetStream]);

  const startStreamFromGenerator = useCallback((generator: AsyncGenerator<string, void, unknown>) => {
    resetStream();
    setIsLoading(true);
    setError(null);

    const streamId = `stream-${Date.now()}`;
    const stream = new ResponseStream(streamId);

    streamRef.current = stream;

    stream.on('chunk', (chunk) => {
      setResponse(stream.getResponse());
    });

    stream.on('complete', () => {
      setIsLoading(false);
      setResponse(stream.getResponse());
    });

    stream.on('error', (err: Error) => {
      setError(err);
      setIsLoading(false);
    });

    // Start streaming from generator
    stream.streamFromGenerator(generator).catch(err => {
      setError(err instanceof Error ? err : new Error(String(err)));
      setIsLoading(false);
    });
  }, [resetStream]);

  const startStreamFromFetch = useCallback((url: string, options?: RequestInit) => {
    resetStream();
    setIsLoading(true);
    setError(null);

    const streamId = `stream-${Date.now()}`;
    const stream = new ResponseStream(streamId);

    streamRef.current = stream;

    stream.on('chunk', (chunk) => {
      setResponse(stream.getResponse());
    });

    stream.on('complete', () => {
      setIsLoading(false);
      setResponse(stream.getResponse());
    });

    stream.on('error', (err: Error) => {
      setError(err);
      setIsLoading(false);
    });

    // Start streaming from fetch
    stream.streamFromFetch(url, options).catch(err => {
      setError(err instanceof Error ? err : new Error(String(err)));
      setIsLoading(false);
    });
  }, [resetStream]);

  return {
    response,
    isLoading,
    error,
    startStream,
    startStreamFromGenerator,
    startStreamFromFetch,
    cancelStream,
    resetStream
  };
}