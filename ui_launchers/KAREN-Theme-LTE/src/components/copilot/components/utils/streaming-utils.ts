/**
 * Streaming utilities for copilot components
 */

export interface StreamingResponse {
  content: string;
  isComplete?: boolean;
  metadata?: {
    tokens?: number;
    timestamp?: number;
    model?: string;
  };
}

export interface StreamingChunk {
  content: string;
  isComplete: boolean;
  metadata?: StreamingResponse['metadata'];
}

export function createStreamingResponse(initialContent = ''): StreamingResponse {
  return {
    content: initialContent,
    isComplete: false,
    metadata: {
      tokens: 0,
      timestamp: Date.now()
    }
  };
}

export function appendToStreamingResponse(
  response: StreamingResponse,
  chunk: string
): StreamingResponse {
  return {
    ...response,
    content: response.content + chunk,
    metadata: {
      ...response.metadata,
      tokens: (response.metadata?.tokens || 0) + chunk.length
    }
  };
}

export function completeStreamingResponse(
  response: StreamingResponse
): StreamingResponse {
  return {
    ...response,
    isComplete: true
  };
}
