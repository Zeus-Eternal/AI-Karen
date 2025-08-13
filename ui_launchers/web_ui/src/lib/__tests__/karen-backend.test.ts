import { describe, it, expect, beforeEach, vi } from 'vitest';
import { KarenBackendService } from '../karen-backend';

vi.mock('../config', () => ({
  webUIConfig: {
    backendUrl: 'http://localhost:8000',
    apiKey: '',
    apiTimeout: 5000,
    cacheTtl: 1000,
    debugLogging: false,
    requestLogging: false,
    performanceMonitoring: false,
    logLevel: 'info',
    maxRetries: 3,
    retryDelay: 100,
  },
}));

vi.mock('../performance-monitor', () => ({
  getPerformanceMonitor: () => ({
    trackRequest: vi.fn(),
    trackError: vi.fn(),
  }),
}));

const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

describe('KarenBackendService', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('retrieves plugin list from cache after first fetch', async () => {
    const service = new KarenBackendService();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ plugins: [{ name: 'test', description: '', category: '', enabled: true, version: '1.0' }] }),
    } as any);

    const first = await service.getAvailablePlugins();
    expect(first.length).toBe(1);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const second = await service.getAvailablePlugins();
    expect(second.length).toBe(1);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});

