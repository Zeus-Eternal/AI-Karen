import { EventEmitter } from 'events';

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
export class ResponseStream extends EventEmitter {
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
   * Add a chunk to stream
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
   * Mark stream as complete
   */
  complete(): void {
    if (this.isComplete) {
      return;
    }

    this.isComplete = true;
    this.emit('complete', this.getResponse());

    if (this.options.onComplete) {
      const finalChunk = this.chunks[this.chunks.length - 1];
      if (finalChunk) {
        this.options.onComplete(finalChunk);
      }
    }
  }

  /**
   * Handle an error in stream
   */
  handleError(error: Error): void {
    this.error = error;
    this.emit('error', error);
    
    if (this.options.onError) {
      this.options.onError(error);
    }
  }

  /**
   * Get current response state
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
