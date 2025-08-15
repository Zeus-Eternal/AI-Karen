# Path: ui_launchers/web_ui/src/services/__tests__/ai-provider.test.ts

import { 
  AIProviderFactory, 
  OpenAIProvider, 
  CustomProvider,
  AIProviderConfig,
  AIProviderRequest 
} from '../ai-provider';
import { useTelemetry } from '@/hooks/use-telemetry';

// Mock dependencies
jest.mock('@/hooks/use-telemetry');

const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('AIProviderFactory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTelemetry.mockReturnValue({
      track: jest.fn()
    } as any);
  });

  it('should register and create providers', () => {
    const config: AIProviderConfig = {
      name: 'test',
      endpoint: 'https://api.test.com',
      apiKey: 'test-key'
    };

    const provider = AIProviderFactory.createProvider({
      ...config,
      name: 'openai'
    });

    expect(provider).toBeInstanceOf(OpenAIProvider);
  });

  it('should throw error for unknown provider', () => {
    const config: AIProviderConfig = {
      name: 'unknown',
      endpoint: 'https://api.unknown.com'
    };

    expect(() => AIProviderFactory.createProvider(config)).toThrow('Unknown AI provider: unknown');
  });

  it('should list available providers', () => {
    const providers = AIProviderFactory.getAvailableProviders();
    expect(providers).toContain('openai');
    expect(providers).toContain('custom');
  });
});

describe('OpenAIProvider', () => {
  let provider: OpenAIProvider;
  const mockTrack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    const config: AIProviderConfig = {
      name: 'openai',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      apiKey: 'test-key',
      model: 'gpt-4'
    };

    provider = new OpenAIProvider(config);
  });

  it('should return correct capabilities', () => {
    const capabilities = provider.getCapabilities();
    
    expect(capabilities.streaming).toBe(true);
    expect(capabilities.codeGeneration).toBe(true);
    expect(capabilities.functionCalling).toBe(true);
    expect(capabilities.supportedModels).toContain('gpt-4');
  });

  it('should send message successfully', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: 'Hello, how can I help you?'
            }
          }
        ],
        model: 'gpt-4',
        usage: {
          prompt_tokens: 10,
          completion_tokens: 15,
          total_tokens: 25
        }
      })
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ]
    };

    const response = await provider.sendMessage(request);

    expect(response.message.content).toBe('Hello, how can I help you?');
    expect(response.message.role).toBe('assistant');
    expect(response.usage?.totalTokens).toBe(25);
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_request', expect.any(Object));
  });

  it('should handle API errors', async () => {
    const mockResponse = {
      ok: false,
      status: 401,
      statusText: 'Unauthorized'
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ]
    };

    await expect(provider.sendMessage(request)).rejects.toThrow('OpenAI API error: 401 Unauthorized');
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_error', expect.any(Object));
  });

  it('should stream messages', async () => {
    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('data: {"choices":[{"delta":{"content":"Hello"}}]}\n'),
          done: false
        })
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('data: {"choices":[{"delta":{"content":" world"}}]}\n'),
          done: false
        })
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('data: [DONE]\n'),
          done: false
        })
        .mockResolvedValueOnce({
          done: true
        })
    };

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ],
      stream: true
    };

    const chunks: string[] = [];
    const onChunk = jest.fn((chunk) => {
      if (chunk.content) {
        chunks.push(chunk.content);
      }
    });
    const onError = jest.fn();

    await provider.streamMessage(request, onChunk, onError);

    expect(chunks).toEqual(['Hello', ' world']);
    expect(onError).not.toHaveBeenCalled();
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_request', expect.any(Object));
  });

  it('should handle streaming errors', async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error'
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ],
      stream: true
    };

    const onChunk = jest.fn();
    const onError = jest.fn();

    await provider.streamMessage(request, onChunk, onError);

    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_error', expect.any(Object));
  });
});

describe('CustomProvider', () => {
  let provider: CustomProvider;
  const mockTrack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    const config: AIProviderConfig = {
      name: 'custom',
      endpoint: '/api/chat'
    };

    provider = new CustomProvider(config);
  });

  it('should return correct capabilities', () => {
    const capabilities = provider.getCapabilities();
    
    expect(capabilities.streaming).toBe(true);
    expect(capabilities.codeGeneration).toBe(true);
    expect(capabilities.functionCalling).toBe(false);
    expect(capabilities.supportedModels).toContain('custom-model');
  });

  it('should send message successfully', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        answer: 'Custom response',
        meta: {
          confidence: 0.9,
          reasoning: 'Based on context'
        },
        context: ['source1', 'source2']
      })
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ],
      sessionId: 'session-123',
      conversationId: 'conv-456'
    };

    const response = await provider.sendMessage(request);

    expect(response.message.content).toBe('Custom response');
    expect(response.message.metadata?.confidence).toBe(0.9);
    expect(response.message.metadata?.sources).toEqual(['source1', 'source2']);
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_request', expect.any(Object));
  });

  it('should stream messages with custom format', async () => {
    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('data: {"text":"Hello"}\n'),
          done: false
        })
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('data: {"text":" world"}\n'),
          done: false
        })
        .mockResolvedValueOnce({
          done: true
        })
    };

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ],
      stream: true
    };

    const chunks: string[] = [];
    const onChunk = jest.fn((chunk) => {
      if (chunk.content) {
        chunks.push(chunk.content);
      }
    });
    const onError = jest.fn();

    await provider.streamMessage(request, onChunk, onError);

    expect(chunks).toEqual(['Hello', ' world']);
    expect(onError).not.toHaveBeenCalled();
  });

  it('should handle non-JSON streaming data', async () => {
    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({
          value: new TextEncoder().encode('Plain text response\n'),
          done: false
        })
        .mockResolvedValueOnce({
          done: true
        })
    };

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const request: AIProviderRequest = {
      messages: [
        {
          id: 'test-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date()
        }
      ],
      stream: true
    };

    const chunks: string[] = [];
    const onChunk = jest.fn((chunk) => {
      if (chunk.content) {
        chunks.push(chunk.content);
      }
    });
    const onError = jest.fn();

    await provider.streamMessage(request, onChunk, onError);

    expect(chunks).toEqual(['Plain text response']);
  });
});