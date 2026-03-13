import React, { useState, useRef, useCallback } from 'react';

// Simple event emitter implementation for browser
type StreamListener = (...args: unknown[]) => void;

class SimpleEventEmitter {
  private listeners: Record<string, StreamListener[]> = {};

  on(event: string, callback: StreamListener): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event: string, ...args: unknown[]): void {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(...args));
    }
  }

  removeAllListeners(): void {
    this.listeners = {};
  }
}

export interface StreamChunk {
  id: string;
  content: string;
  isFinal: boolean;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

export interface StreamOptions {
  chunkSize?: number;
  delay?: number;
  onChunk?: (chunk: StreamChunk) => void;
  onError?: (error: Error) => void;
  onComplete?: (finalChunk: StreamChunk) => void;
}

export interface StreamingResponse {
  id: string;
  content: string;
  chunks: StreamChunk[];
  isComplete: boolean;
  error?: Error;
}

/**
 * Streaming utility for handling real-time response streaming
 */
export class ResponseStream extends SimpleEventEmitter {
  private id: string;
  private content: string = '';
  private chunks: StreamChunk[] = [];
  private isComplete: boolean = false;
  private error: Error | null = null;
  private options: StreamOptions;

  constructor(id: string, options: StreamOptions = {}) {
    super();
    this.id = id;
    this.options = {
      chunkSize: 100,
      delay: 10,
      ...options
    };
  }

  /**
   * Add a chunk to the stream
   */
  addChunk(content: string, isFinal = false, metadata?: Record<string, unknown>): void {
    if (this.isComplete) {
      throw new Error('Stream is already complete');
    }

    const chunk: StreamChunk = {
      id: `${this.id}-${this.chunks.length}`,
      content,
      isFinal,
      timestamp: new Date(),
      metadata
    };

    this.content += content;
    this.chunks.push(chunk);

    this.emit('chunk', chunk);
    
    if (this.options.onChunk) {
      this.options.onChunk(chunk);
    }

    if (isFinal) {
      this.complete();
    }
  }

  /**
   * Mark the stream as complete
   */
  complete(): void {
    if (this.isComplete) {
      return;
    }

    this.isComplete = true;
    this.emit('complete', this.getResponse());
    
    if (this.options.onComplete && this.chunks.length > 0) {
      const finalChunk = this.chunks[this.chunks.length - 1];
      if (finalChunk) {
        this.options.onComplete(finalChunk);
      }
    }
  }

  /**
   * Handle an error in the stream
   */
  handleError(error: Error): void {
    this.error = error;
    this.emit('error', error);
    
    if (this.options.onError) {
      this.options.onError(error);
    }
  }

  /**
   * Get the current response state
   */
  getResponse(): StreamingResponse {
    return {
      id: this.id,
      content: this.content,
      chunks: [...this.chunks],
      isComplete: this.isComplete,
      error: this.error || undefined
    };
  }

  /**
   * Stream text content with optional delay between chunks
   */
  async streamText(text: string, options: { delay?: number; chunkSize?: number } = {}): Promise<void> {
    const { delay = this.options.delay || 10, chunkSize = this.options.chunkSize || 100 } = options;
    
    for (let i = 0; i < text.length; i += chunkSize) {
      const chunk = text.substring(i, i + chunkSize);
      const isFinal = i + chunkSize >= text.length;
      
      this.addChunk(chunk, isFinal);
      
      if (!isFinal && delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  /**
   * Stream a response from an async generator
   */
  async streamFromGenerator(generator: AsyncGenerator<string, void, unknown>): Promise<void> {
    try {
      let result = await generator.next();
      while (!result.done) {
        this.addChunk(result.value);
        result = await generator.next();
      }
      this.complete();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * Stream a response from a fetch request with streaming support
   */
  async streamFromFetch(url: string, options?: RequestInit): Promise<void> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options?.headers,
          'Accept': 'text/plain',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let done = false;
      while (!done) {
        const { done: readerDone, value } = await reader.read();
        done = readerDone;
        
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          this.addChunk(chunk);
        }
      }

      this.complete();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error(String(error)));
    }
  }
}

/**
 * React hook for managing streaming responses
 */
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

    stream.on('chunk', () => {
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

    stream.on('chunk', () => {
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

    stream.on('chunk', () => {
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

/**
 * Component for displaying streamed content
 */

interface StreamedContentProps {
  response: StreamingResponse | null;
  isLoading?: boolean;
  error?: Error | null;
  theme?: {
    colors?: {
      error?: string;
      primary?: string;
    };
  };
  className?: string;
  showTypingIndicator?: boolean;
  typingIndicator?: React.ReactNode;
}

export const StreamedContent: React.FC<StreamedContentProps> = ({
  response,
  isLoading = false,
  error,
  theme,
  className = '',
  showTypingIndicator = true,
  typingIndicator
}) => {
  const contentRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when content updates
  React.useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [response?.content]);

  if (error) {
    return (
      <div className={`copilot-streamed-error ${className}`} style={{ color: theme?.colors?.error }}>
        Error: {error.message}
      </div>
    );
  }

  return (
    <div className={`copilot-streamed-content ${className}`} style={{ position: 'relative' }}>
      <div
        ref={contentRef}
        className="copilot-streamed-text"
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: '1.5'
        }}
      >
        {response?.content || ''}
      </div>
      
      {isLoading && showTypingIndicator && (
        <div className="copilot-typing-indicator" style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}>
          {typingIndicator || (
            <>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, marginRight: '4px', animation: 'pulse 1.4s infinite' }}></span>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, marginRight: '4px', animation: 'pulse 1.4s infinite 0.2s' }}></span>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, animation: 'pulse 1.4s infinite 0.4s' }}></span>
            </>
          )}
        </div>
      )}
      
      <style>{`
        @keyframes pulse {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
};
