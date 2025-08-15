# Path: ui_launchers/web_ui/src/services/__tests__/ai-client.test.ts

import { AIClient, AIClientConfig } from '../ai-client';
import { AIProvider, AIProviderFactory } from '../ai-provider';
import { useTelemetry } from '@/hooks/use-telemetry';

// Mock dependencies
jest.mock('@/hooks/use-telemetry');
jest.mock('../ai-provider');

const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;
const mockAIProviderFactory = AIProviderFactory as jest.Mocked<typeof AIProviderFactory>;

// Mock provider class
class MockProvider extends AIProvider {
  getCapabilities() {
    return {
      streaming: true,
      codeGeneration: true,
      imageGeneration: false,
      functionCalling: false,
      contextWindow: 4096,
      supportedModels: ['mock-model']
    };
  }

  async sendMessage(request: any) {
    return {
      message: {
        id: 'mock-response',
        role: 'assistant' as const,
        content: 'Mock response',
        timestamp: new Date(),
        type: 'text' as const,
        metadata: {
          model: 'mock-model',
          latencyMs: 100
        }
      },
      metadata: {
        model: 'mock-model',
        latencyMs: 100
      }
    };
  }

  async streamMessage(request: any, onChunk: any, onError: any, signal?: AbortSignal) {
    onChunk({ content: 'Mock ', done: false });
    onChunk({ content: 'streaming ', done: false });
    onChunk({ content: 'response', done: false });
    onChunk({ content: '', done: true });
  }
}

describe('AIClient', () => {
  const mockTrack = jest.fn();
  let client: AIClient;
  let config: AIClientConfig;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    mockAIProviderFactory.createProvider.mockImplementation(() => new MockProvider({
      name: 'mock',
      endpoint: 'https://api.mock.com'
    }));

    config = {
      defaultProvider: 'mock',
      providers: [
        {
          name: 'mock',
          endpoint: 'https://api.mock.com'
        },
        {
          name: 'fallback',
          endpoint: 'https://api.fallback.com'
        }
      ],
      fallbackProviders: ['fallback'],
      timeout: 5000
    };

    client = new AIClient(config);
  });

  it('should initialize with providers', () => {
    expect(mockAIProviderFactory.createProvider).toHaveBeenCalledTimes(2);
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_initialized', expect.any(Object));
  });

  it('should send message successfully', async () => {
    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    const response = await client.sendMessage(messages, 'session-123', 'conv-456');

    expect(response.message.content).toBe('Mock response');
    expect(mockTrack).toHaveBeenCalledWith('ai_client_message_sent', expect.any(Object));
  });

  it('should handle provider not found error', async () => {
    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    await expect(
      client.sendMessage(messages, 'session-123', 'conv-456', { provider: 'nonexistent' })
    ).rejects.toThrow('Provider nonexistent not found or not initialized');
  });

  it('should stream message successfully', async () => {
    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    const chunks: string[] = [];
    const onChunk = jest.fn((chunk) => {
      if (chunk.content) {
        chunks.push(chunk.content);
      }
    });

    await client.streamMessage(messages, 'session-123', 'conv-456', { onChunk });

    expect(chunks).toEqual(['Mock ', 'streaming ', 'response']);
    expect(mockTrack).toHaveBeenCalledWith('ai_client_stream_completed', expect.any(Object));
  });

  it('should handle streaming errors', async () => {
    // Mock provider that throws error
    const errorProvider = new MockProvider({
      name: 'error',
      endpoint: 'https://api.error.com'
    });

    errorProvider.streamMessage = jest.fn().mockImplementation((request, onChunk, onError) => {
      onError(new Error('Streaming failed'));
    });

    mockAIProviderFactory.createProvider.mockReturnValueOnce(errorProvider);

    const errorClient = new AIClient({
      defaultProvider: 'error',
      providers: [{ name: 'error', endpoint: 'https://api.error.com' }]
    });

    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    const onError = jest.fn();
    await errorClient.streamMessage(messages, 'session-123', 'conv-456', { onError });

    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it('should try fallback providers on error', async () => {
    // Mock primary provider that fails
    const failingProvider = new MockProvider({
      name: 'failing',
      endpoint: 'https://api.failing.com'
    });

    failingProvider.sendMessage = jest.fn().mockRejectedValue(new Error('Primary failed'));

    // Mock fallback provider that succeeds
    const fallbackProvider = new MockProvider({
      name: 'fallback',
      endpoint: 'https://api.fallback.com'
    });

    mockAIProviderFactory.createProvider
      .mockReturnValueOnce(failingProvider)
      .mockReturnValueOnce(fallbackProvider);

    const fallbackClient = new AIClient({
      defaultProvider: 'failing',
      providers: [
        { name: 'failing', endpoint: 'https://api.failing.com' },
        { name: 'fallback', endpoint: 'https://api.fallback.com' }
      ],
      fallbackProviders: ['fallback']
    });

    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    const response = await fallbackClient.sendMessage(messages);

    expect(response.message.content).toBe('Mock response');
    expect(mockTrack).toHaveBeenCalledWith('ai_client_fallback_attempt', expect.any(Object));
    expect(mockTrack).toHaveBeenCalledWith('ai_client_fallback_success', expect.any(Object));
  });

  it('should handle timeout', async () => {
    // Mock provider with slow response
    const slowProvider = new MockProvider({
      name: 'slow',
      endpoint: 'https://api.slow.com'
    });

    slowProvider.sendMessage = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 10000))
    );

    mockAIProviderFactory.createProvider.mockReturnValueOnce(slowProvider);

    const timeoutClient = new AIClient({
      defaultProvider: 'slow',
      providers: [{ name: 'slow', endpoint: 'https://api.slow.com' }],
      timeout: 100
    });

    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    await expect(timeoutClient.sendMessage(messages)).rejects.toThrow('Operation timed out after 100ms');
  });

  it('should get provider capabilities', () => {
    const capabilities = client.getProviderCapabilities('mock');
    
    expect(capabilities.streaming).toBe(true);
    expect(capabilities.supportedModels).toContain('mock-model');
  });

  it('should list available providers', () => {
    const providers = client.getAvailableProviders();
    
    expect(providers).toContain('mock');
    expect(providers).toContain('fallback');
  });

  it('should check provider availability', () => {
    expect(client.isProviderAvailable('mock')).toBe(true);
    expect(client.isProviderAvailable('nonexistent')).toBe(false);
  });

  it('should add new provider', () => {
    const newProviderConfig = {
      name: 'new',
      endpoint: 'https://api.new.com'
    };

    client.addProvider(newProviderConfig);

    expect(mockAIProviderFactory.createProvider).toHaveBeenCalledWith(newProviderConfig);
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_added', expect.any(Object));
  });

  it('should remove provider', () => {
    const removed = client.removeProvider('mock');
    
    expect(removed).toBe(true);
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_removed', { provider: 'mock' });
  });

  it('should update provider config', () => {
    const updates = { temperature: 0.8 };
    
    client.updateProviderConfig('mock', updates);
    
    expect(mockTrack).toHaveBeenCalledWith('ai_provider_config_updated', {
      provider: 'mock',
      updatedFields: ['temperature']
    });
  });

  it('should handle provider initialization errors', () => {
    mockAIProviderFactory.createProvider.mockImplementation(() => {
      throw new Error('Provider init failed');
    });

    // Should not throw, but log error
    const errorConfig = {
      defaultProvider: 'error',
      providers: [{ name: 'error', endpoint: 'https://api.error.com' }]
    };

    expect(() => new AIClient(errorConfig)).not.toThrow();
  });

  it('should handle non-streaming provider for streaming request', async () => {
    // Mock provider without streaming capability
    const nonStreamingProvider = new MockProvider({
      name: 'non-streaming',
      endpoint: 'https://api.non-streaming.com'
    });

    nonStreamingProvider.getCapabilities = jest.fn().mockReturnValue({
      streaming: false,
      codeGeneration: true,
      imageGeneration: false,
      functionCalling: false,
      contextWindow: 4096,
      supportedModels: ['non-streaming-model']
    });

    mockAIProviderFactory.createProvider.mockReturnValueOnce(nonStreamingProvider);

    const nonStreamingClient = new AIClient({
      defaultProvider: 'non-streaming',
      providers: [{ name: 'non-streaming', endpoint: 'https://api.non-streaming.com' }]
    });

    const messages = [
      {
        id: 'test-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date()
      }
    ];

    await expect(
      nonStreamingClient.streamMessage(messages)
    ).rejects.toThrow('Provider non-streaming does not support streaming');
  });
});