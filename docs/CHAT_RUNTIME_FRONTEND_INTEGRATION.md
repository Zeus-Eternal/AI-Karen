# Chat Runtime Frontend Integration Guide

## Overview

This document provides complete integration guidance for connecting frontends (Web UI, Desktop) to Kari's production chat runtime API.

## Base Configuration

### Environment Variables

```env
# .env.local or .env.production
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
```

## API Endpoints

### 1. Non-Streaming Chat

**Endpoint:** `POST /api/chat/runtime`

**Request:**
```typescript
interface ChatRequest {
  message: string;                    // User message (required)
  context?: Record<string, any>;      // Optional chat context
  tools?: string[];                   // Available tools
  memory_context?: string;            // Memory context identifier
  user_preferences?: Record<string, any>;  // User preferences
  platform?: string;                  // Platform identifier (default: "web")
  conversation_id?: string;           // Conversation ID
  stream?: boolean;                   // Enable streaming (default: true)
  model?: string;                     // Explicit model (optional)
  provider?: string;                  // Explicit provider (optional)
  temperature?: number;               // Sampling temperature (0.0-2.0)
  max_tokens?: number;                // Maximum tokens (optional)
}
```

**Response:**
```typescript
interface ChatResponse {
  content: string;                    // AI response
  tool_calls: ToolCall[];             // Tool calls made
  memory_operations: MemoryOperation[];  // Memory operations
  metadata: {
    platform: string;
    correlation_id: string;
    user_id: string;
    processing_time: number;
    latency_ms: number;
    used_fallback: boolean;
    // ... additional metadata
  };
  conversation_id: string;
  timestamp: string;
}
```

**Example (React/TypeScript):**
```typescript
const sendMessage = async (message: string) => {
  const response = await fetch(`${API_BASE_URL}/api/chat/runtime`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      stream: false,
      platform: 'web',
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  const data: ChatResponse = await response.json();
  return data;
};
```

### 2. Streaming Chat (SSE)

**Endpoint:** `POST /api/chat/runtime/stream`

**Request:** Same as non-streaming

**Response (Server-Sent Events):**

The API streams events in SSE format. Each event is a JSON object with a `type` field.

**Event Types:**

1. **metadata** - Initial metadata
```json
{
  "type": "metadata",
  "data": {
    "conversation_id": "...",
    "correlation_id": "...",
    "platform": "web"
  }
}
```

2. **token** - Individual tokens
```json
{
  "type": "token",
  "data": {
    "token": "Hello"
  }
}
```

3. **complete** - Completion metadata
```json
{
  "type": "complete",
  "data": {
    "total_tokens": 150,
    "latency_ms": 2345,
    "first_token_latency_ms": 234,
    "processing_time": 2.345,
    "used_fallback": false
  }
}
```

4. **error** - Error occurred
```json
{
  "type": "error",
  "data": {
    "message": "Error description"
  }
}
```

**Example (React/TypeScript with EventSource):**

```typescript
const streamMessage = async (message: string, onToken: (token: string) => void) => {
  const response = await fetch(`${API_BASE_URL}/api/chat/runtime/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      stream: true,
      platform: 'web',
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        switch (data.type) {
          case 'metadata':
            console.log('Stream metadata:', data.data);
            break;

          case 'token':
            onToken(data.data.token);
            break;

          case 'complete':
            console.log('Stream complete:', data.data);
            break;

          case 'error':
            console.error('Stream error:', data.data.message);
            break;
        }
      }
    }
  }
};
```

**Example (React Hook):**

```typescript
import { useState, useCallback } from 'react';

interface UseStreamingChatOptions {
  apiBaseUrl: string;
  conversationId: string;
}

export function useStreamingChat({ apiBaseUrl, conversationId }: UseStreamingChatOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentMessage, setCurrentMessage] = useState('');

  const sendStreamingMessage = useCallback(async (message: string) => {
    setIsStreaming(true);
    setCurrentMessage('');

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/runtime/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          stream: true,
          platform: 'web',
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'token') {
              setCurrentMessage(prev => prev + data.data.token);
            }
          }
        }
      }
    } finally {
      setIsStreaming(false);
    }
  }, [apiBaseUrl, conversationId]);

  return { sendStreamingMessage, isStreaming, currentMessage };
}
```

### 3. Stop Generation

**Endpoint:** `POST /api/chat/runtime/stop`

**Request:**
```typescript
interface StopRequest {
  conversation_id: string;      // Required
  correlation_id?: string;      // Optional - specific request to stop
}
```

**Response:**
```typescript
interface StopResponse {
  status: "stopped";
  conversation_id: string;
  correlation_ids: string[];
  stopped_at: string;
}
```

**Example:**
```typescript
const stopGeneration = async (conversationId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/chat/runtime/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId }),
  });

  return response.json();
};
```

### 4. Chat Configuration

**Endpoint:** `GET /api/chat/runtime/config`

**Response:**
```typescript
interface ChatConfig {
  user: {
    id: string;
    tenant_id: string;
    roles: string[];
  };
  environment: {
    name: string;
    debug: boolean;
  };
  llm: {
    default_provider: string;
    default_model: string;
    fallback_chain: string[];
    streaming_enabled: boolean;
  };
  tools: {
    available: Tool[];
  };
  memory: {
    enabled: boolean;
    provider: string;
  };
  limits: {
    max_message_length: number;
    max_tokens: number;
    temperature: number;
  };
}
```

### 5. Health Check

**Endpoint:** `GET /api/chat/runtime/health`

**Response:**
```typescript
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  service: "chat-runtime";
  version: string;
  environment: string;
  services: Record<string, ServiceStatus>;
  config: {
    max_message_length: number;
    stream_timeout: number;
    fallback_enabled: boolean;
  };
}
```

## Complete Chat Component Example

```typescript
// components/Chat.tsx
import React, { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId] = useState(() => `conv_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleStreamingChat = async (userMessage: string) => {
    setIsLoading(true);
    setIsStreaming(true);

    // Add user message
    const userMsg: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);

    // Create assistant message placeholder
    const assistantMsgId = `assistant_${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMsg]);

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/runtime/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          stream: true,
          platform: 'web',
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let buffer = '';
      let assistantContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'token') {
                assistantContent += data.data.token;

                // Update message in place
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: assistantContent }
                      : msg
                  )
                );
              } else if (data.type === 'complete') {
                // Store metadata
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMsgId
                      ? { ...msg, metadata: data.data }
                      : msg
                  )
                );
              } else if (data.type === 'error') {
                console.error('Stream error:', data.data.message);
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: `Error: ${data.data.message}` }
                      : msg
                  )
                );
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMsgId
            ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    await handleStreamingChat(userMessage);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b p-4">
        <h1 className="text-xl font-semibold">Kari AI Chat</h1>
        <p className="text-sm text-gray-500">Conversation ID: {conversationId}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.metadata && (
                <div className="mt-2 text-xs opacity-70">
                  Provider: {msg.metadata.preferred_llm_provider || 'unknown'} |
                  Latency: {msg.metadata.latency_ms?.toFixed(0)}ms
                </div>
              )}
            </div>
          </div>
        ))}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="bg-white border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
}
```

## Error Handling

Always implement proper error handling:

```typescript
try {
  const response = await fetch(url, options);

  if (!response.ok) {
    if (response.status === 400) {
      // Validation error
      const error = await response.json();
      console.error('Validation error:', error);
    } else if (response.status === 503) {
      // Service unavailable
      console.error('Service temporarily unavailable');
    } else {
      console.error(`HTTP ${response.status}`);
    }
    return;
  }

  // Process successful response
} catch (error) {
  console.error('Network error:', error);
}
```

## Best Practices

1. **Use Streaming for Better UX** - Streaming provides immediate feedback
2. **Handle Disconnections** - Implement retry logic for network failures
3. **Display Metadata** - Show provider, model, and latency information
4. **Implement Stop Functionality** - Allow users to cancel long-running requests
5. **Cache Configuration** - Fetch chat config once and reuse
6. **Handle Fallback Mode** - Display appropriate messages when in degraded mode
7. **Use Correlation IDs** - Track requests for debugging
8. **Implement Rate Limiting** - Respect API rate limits
9. **Validate Input** - Check message length before sending

## Testing

Use the provided validation script:

```bash
python scripts/validate_chat_runtime_production.py
```

This will verify:
- ✅ Health endpoints
- ✅ Non-streaming chat
- ✅ Streaming (SSE)
- ✅ Prometheus metrics
- ✅ Degraded mode status
- ✅ Configuration endpoints

## Support

For issues or questions, please refer to:
- API Documentation: `/docs`
- Health Check: `/health`
- Chat Runtime Health: `/api/chat/runtime/health`
